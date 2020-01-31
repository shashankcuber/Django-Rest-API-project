from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view,permission_classes,authentication_classes
from .models import User,Analysis
import requests
from rest_framework import status
from .phase1_2 import phase_1
from  jarvis.serializers import UserSerializer,AnalysisSerializer,DisplaySerializer,ListSerializer,ResultSerializer
from celery import Celery
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth import get_user,get_user_model
# from django.contrib.auth.models import User,UserManager
# from django
# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    # print(request)
   
    username = request.data.get('username')
    print(username)
    password = request.data.get('password')
   
    users = User.objects.filter(username=username, password=password) # User.objects.get_or_404()
    
    
    # print(users)
    # return Response({"Name": user.username,"Token":token.key}, status=status.HTTP_200_OK)
    if users:
        user = users[0]
        user.is_active = True
        try:
            token_exists = Token.objects.get(user=user)
            token=token_exists
        except:
            token=Token.objects.create(user=user)
            user.save()
        
        return Response({"Name": user.username,"Token":token.key}, status=status.HTTP_200_OK)
    else:
        return Response({" Error in login"} ,status=status.HTTP_400_BAD_REQUEST)    



@api_view(['PUT'])    
def logout(request):
    
    username = request.data.get('username')
    
    users=User.objects.filter(username=username)
    user=users[0]
   
    
    if user and user.is_active:
        user.is_active=False
        user.save()
        return Response({"Username":user.username},status=status.HTTP_200_OK)
    else:
        return Response({"Error" },status=status.HTTP_400_BAD_REQUEST)    


@api_view(['POST']) 
def register(request):
    username =request.data.get('username')
    password=request.data.get('password')
    email=request.data.get('email')
    obj1=User.objects.create(username=username,password=password,email=email,is_active=False)
    # obj1.username =username
    # obj1.password=password
    # obj1.email=email
    # obj1.is_active=False
    obj1.save()
    return Response({"Username":obj1.username},status=status.HTTP_200_OK)



@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def analysis(request):
    # print("hru")
    '''
    bina serializer ke assign krne ki ninja technique
    username=request.data.get('username')
    name=request.data.get('name')
    created=request.data.get('created')
    date_start=request.data.get('date_start')
    date_end=request.data.get('date_end') 
    tlx=request.data.get('tlx')
    tly=request.data.get('tly')
    brx=request.data.get('brx')
    bry=request.data.get('bry')
    aoi=[tlx,tly,brx,bry]
    '''
   
    #serializer ko bhej do 
    serializer=AnalysisSerializer(data=request.data)
    
    if serializer.is_valid():
        username=serializer.validated_data['username']
        # print(username)
        name=serializer.validated_data['name']
        created=serializer.validated_data['created']
        date_start=serializer.validated_data['date_start']
        # print(date_start)
        date_end=serializer.validated_data['date_end']
        tlx=serializer.validated_data['tlx']
        tly=serializer.validated_data['tly']
        brx=serializer.validated_data['brx']
        bry=serializer.validated_data['bry']
        aoi=[tlx,tly,brx,bry]
        
        '''
        # obj1=Analysis.objects.create(name=name,created=created,date_start=date_start,date_end=date_end,tlx=tlx,tly=tly,brx=brx,bry=bry)
        # obj1.username=username
        # obj1.name=name
        # obj1.created=created
        # obj1.date_start=date_start
        # obj1.date_end=date_end
        # obj1.tlx=tlx
        # obj1.tly=tly
        # obj1.brx=brx
        # obj1.bry=bry
        '''
        #user ke object ko laao jo username ho and uske object ko add krna hota hai M:M field mai
        user_object=User.objects.get(username=username)
        if user_object:
            #  #M:M field mai value assign krne ka tarika
            # obj1.users.add(user_object)
            
            # obj1.save()
            # a1=Analysis.objects.get(date_start=date_start,date_end=date_end,tlx=tlx,tly=tly,brx=brx,bry=bry)
            # if(a1):
                # a=a1
                #area type dictionary
            #calling the celry task    
            d=date_start.strftime("%Y%m%d")
            # print(d)
            # print('h')
            # print(d)
            phase_1.delay(name,d,date_end.strftime("%Y%m%d"),aoi,username,created)
            
            return Response({"Analysis started"},status=status.HTTP_200_OK) 
            # else:
                # area={1: 'Geeks', 2: 'For', 3: {'A' : 'Welcome', 'B' : 'To', 'C' : 'Geeks'}}
                
                # return Response({"Answer":area},status=status.HTTP_200_OK) 
            # return Response({"Invalid Analysis"},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"No such username"},status=status.HTTP_400_BAD_REQUEST)
       
    else:
        #serializer.errors likhne se pta chal jaaega ki kaha se error aa rha hai
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST) 



@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def display_analysis(request):
    serializer=DisplaySerializer(data=request.data)

    if serializer.is_valid():
        username=serializer.validated_data['username']
        user=User.objects.get(username=username)
        #ek object ko laane ka tariqa M:M field se 
        list_analysis=Analysis.objects.filter(users=user)
        serialize_final_list=ListSerializer(instance=list_analysis,many=True)
        return Response(serialize_final_list.data,status=status.HTTP_200_OK)
    else:
        return Response({"Invalid"},status=status.HTTP_400_BAD_REQUEST)   



@api_view(['POST'])
# @permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])      
def result(request):
    serializer=ResultSerializer(data=request.data)
    if serializer.is_valid():
        username=serializer.validated_data['username']
        task_name=serializer.validated_data['name']
        user=User.objects.get(username=username)
        if user:
            output=Analysis.objects.get(users=user,name=task_name)
            if output:
                return Response({"Result":output.result},status=status.HTTP_200_OK)
            else:
                return Response({"Invalid"},status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"Invalid"},status=status.HTTP_400_BAD_REQUEST)



        

        
    
      