from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date
from datetime import datetime
import os
import zipfile 
import glob
from osgeo import ogr
import osr
import gdal
from gdal import GetDriverByName
import cv2
import numpy as np
from tqdm import tqdm
from celery import shared_task
from jarvis.models import Analysis,User
# import matplotlib.pyplot as plt
def create_vector(name,bbox):

    driver = ogr.GetDriverByName("geojson")
    data_source = driver.CreateDataSource("/home/pegasus/Desktop/shashank/bootcamp/Results/temp.geojson")
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)
    layer = data_source.CreateLayer("sentinelapidata", srs, ogr.wkbMultiPolygon)
    nameField = ogr.FieldDefn("name", ogr.OFTString)
    layer.CreateField(nameField)
    feature = ogr.Feature(layer.GetLayerDefn())
    feature.SetField("name",name)
    multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
    ring1 = ogr.Geometry(ogr.wkbLinearRing)
    ring1.AddPoint_2D(bbox[0], bbox[1])
    ring1.AddPoint_2D(bbox[0], bbox[3])
    ring1.AddPoint_2D(bbox[2], bbox[3])
    ring1.AddPoint_2D(bbox[2], bbox[1])
    ring1.AddPoint_2D(bbox[0], bbox[1])
    poly1 = ogr.Geometry(ogr.wkbPolygon)
    poly1.AddGeometry(ring1)
    multipolygon.AddGeometry(poly1)
    feature.SetGeometry(multipolygon)
    layer.CreateFeature(feature)
    feature = None
    data_source = None

def area(array):
    cnt = np.sum(array)
    return float(cnt*100/1000000)

@shared_task
def phase_1(name,DateStart,DateEnd,bbox,username,created):
    
    # print(DateStart)
    cloud_thresh = 1500
    awei_thresh = -1000
    #Bbox to geojson
    create_vector(name,bbox) 
    #change_directory
    os.chdir(r"/home/pegasus/Desktop/shashank/bootcamp/Results/")
    Given_AOI = '/home/pegasus/Desktop/shashank/bootcamp/Results/temp.geojson'
    #running pyhton api
    api = SentinelAPI('sanchit2843', 'popo0909')
    footprint = geojson_to_wkt(read_geojson(Given_AOI))
    products = api.query(footprint,
                      date = (DateStart,DateEnd),
                     platformname='Sentinel-2',producttype='S2MSI2A')
    api.download_all(products) 

    #unzipping the files
    files = glob.glob('/home/pegasus/Desktop/shashank/bootcamp/Results/*.zip')
    for file in files:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall("/home/pegasus/Desktop/shashank/bootcamp/Results/Sentinel_Data")
    #reading the files
    required_bands = ['B01','B02','B04','B08','B8A','B09','B11','B12']
    resolutions = ['R10m','R20m','R60m']
    required_bands1 = required_bands.copy()
    bands = {}
    base = '/home/pegasus/Desktop/shashank/bootcamp/Results/Sentinel_Data'
    os.makedirs(base,exist_ok = True)
    result_dict = {}
    for id,input_file in enumerate(os.listdir(base)):
        input_path = os.path.join(base,input_file,'GRANULE')
        input_path = os.path.join(input_path,os.listdir(input_path)[0],'IMG_DATA')
        date = input_file.split('_')[2][:8]
        date = date[:4] + '-' + date[4:6] + '-' + date[6:]
        for res in resolutions:
            path_file = os.path.join(input_path,res)
            for file in os.listdir(path_file):
                if(file.split('_')[-2] in required_bands1):
                    if(os.path.exists('/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff')):
                        os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff')
                    if(os.path.exists('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')):
                        os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')
                    gdal.Translate("/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff",os.path.join(path_file,file))
                    outtile = gdal.Warp("/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff", 
                                        "/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff", 
                                        cutlineDSName ='/home/pegasus/Desktop/shashank/bootcamp/Results/temp.geojson',
                                        dstNodata = 0 , cropToCutline = True)
                    outtile = None
                    bands.update({file.split('_')[-2]:gdal.Open('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')})
                    required_bands1.remove(file.split('_')[-2]) 

        #Cloud
        if(os.path.exists('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')):
            os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')
        if(os.path.exists('/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff')):
            os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/out.tiff')
        sh2,sh1 = bands['B02'].ReadAsArray().shape
        clouds = cv2.resize(bands['B01'].ReadAsArray().astype(np.float32()),(sh1,sh2))
        clouds[clouds<=cloud_thresh] = 0
        clouds[clouds>cloud_thresh] = 1
        geotiff = GetDriverByName('GTiff')
        output = geotiff.Create('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff', sh1,sh2, 1, gdal.GDT_Float32)
        output.SetGeoTransform(bands['B02'].GetGeoTransform())
        output.SetProjection(bands['B02'].GetProjection())
        output_band = output.GetRasterBand(1)
        output_band.WriteArray(clouds)
        output = None
        temp = gdal.Open('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff').ReadAsArray().astype(int)
        temp[temp>1] = 1
        temp[temp<0] = 0
        clouds_area = area(temp)
        os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')
        if(id == 0):
            date_dict = {date:clouds_area}
        else:
            date_dict = result_dict['clouds']
            date_dict.update({date:clouds_area})
        result_dict.update({'clouds':date_dict})
        #awei
        #AWEI= 4*(GREEN-SWIR2)- (0.25*NIR+2.75*SWIR1)
        awei = 4*(bands['B02'].ReadAsArray().astype(np.float32()) - cv2.resize(bands['B12'].ReadAsArray().astype(np.float32()),(sh1,sh2))) - (0.25*(cv2.resize(bands['B8A'].ReadAsArray().astype(np.float32()),(sh1,sh2)))+2.75*cv2.resize(bands['B11'].ReadAsArray().astype(np.float32()),(sh1,sh2)))
        awei[awei>=awei_thresh] = 1
        awei[awei<awei_thresh] = 0
        geotiff = GetDriverByName('GTiff')
        output = geotiff.Create('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff', sh1, sh2, 1, gdal.GDT_Float32)
        output.SetGeoTransform(bands['B02'].GetGeoTransform())
        output.SetProjection(bands['B02'].GetProjection())
        output_band = output.GetRasterBand(1)
        output_band.WriteArray(awei)
        output = None
        temp = gdal.Open('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff').ReadAsArray().astype(int)
        temp[temp>1] = 1
        temp[temp<0] = 0

        water_area = area(temp)
        os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')
        if(id == 0):
            date_dict = {date:water_area}
        else:
            date_dict = result_dict['awei']
            date_dict.update({date:water_area})

        result_dict.update({'awei':date_dict})
        #ndvi
        #ndvi = (NIR-RED)/(NIR+RED)
        ndvi = (bands['B08'].ReadAsArray().astype(np.float32()) - bands['B04'].ReadAsArray().astype(np.float32()) )/(bands['B08'].ReadAsArray().astype(np.float32()) + bands['B04'].ReadAsArray().astype(np.float32()) ) 
        #ndvi = np.nan_to_num(ndvi)
        ndvi[ndvi>= 0.2] = 1
        ndvi[ndvi< 0.2] = 0
        geotiff = GetDriverByName('GTiff')
        output = geotiff.Create('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff', sh1, sh2, 1, gdal.GDT_Float32)
        output.SetGeoTransform(bands['B02'].GetGeoTransform())
        output.SetProjection(bands['B02'].GetProjection())
        output_band = output.GetRasterBand(1)
        output_band.WriteArray(ndvi)
        output = None
        temp = gdal.Open('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff').ReadAsArray().astype(int)
        temp[temp>1] = 1
        temp[temp<0] = 0
        veg_area = area(temp)
        os.remove('/home/pegasus/Desktop/shashank/bootcamp/Results/temp.tiff')
        if(id == 0):
            date_dict = {date:veg_area}
        else:
            date_dict = result_dict['ndvi']
            date_dict.update({date:veg_area})

        result_dict.update({'ndvi':date_dict})
    
    format_str='%Y%m%d'    
    date_start=datetime.strptime(DateStart,format_str)
    date_end=datetime.strptime(DateEnd,format_str)
    obj1=Analysis.objects.create(name=name,created=created,date_start=date_start,date_end=date_end,tlx=bbox[0],tly=bbox[1],brx=bbox[2],bry=bbox[3],result=result_dict)
    #M:M field mai value assign krne ka tarika
    user_object=User.objects.get(username=username)
    obj1.users.add(user_object)
                
    obj1.save()
# phase_1('sanchit','2019-02-05','20190220',[76.526789413595196, 10.245776787828065, 76.664012284079703, 9.995835130874156 ])