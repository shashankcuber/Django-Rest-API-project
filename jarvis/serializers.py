from rest_framework import serializers
from jarvis.models import User,Analysis
from django.utils import timezone

class UserSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=10)
    email=serializers.EmailField()
    password=serializers.CharField(max_length=10,required=True)
    is_active=serializers.BooleanField(default=False)

class AnalysisSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=10)
    name=serializers.CharField(max_length=10)
    created=serializers.DateField()
    date_start=serializers.DateField()
    date_end=serializers.DateField()
    tlx=serializers.FloatField()
    tly=serializers.FloatField()
    brx=serializers.FloatField()
    bry=serializers.FloatField()

class DisplaySerializer(serializers.Serializer):
    username=serializers.CharField(max_length=10)    

#Model based serializer define krne ki ninja technique
class ListSerializer(serializers.ModelSerializer):

    class Meta:
        #model lelo jise verify krna hai
        model=Analysis
        #saare fields ko apne aap dekh lega ye
        fields=['name','created','date_start','date_end','tlx','tly','brx','bry']


class ResultSerializer(serializers.Serializer):
    username=serializers.CharField(max_length=10)
    name=serializers.CharField(max_length=10)

    
    
 