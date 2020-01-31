from django.db import models
from django.conf import settings
from django.utils import timezone
from django import forms
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField
# from json_field import JSONField

# Create your models here.

class User(AbstractUser):

    pass

    def __str__(self):
        return self.username
    # REQUIRED_FIELDS=[]
    # USERNAME_FIELD ='username'
    # is_anonymous=[]
    # is_authenticated=[]

class Analysis(models.Model):
    name=models.CharField(max_length=10,null=True)
    #object type field jo analysis table mai nhi  aur M:M bnaane mai madad krega
    users = models.ManyToManyField(User)
    #auto_now_add useful for creating timestamp
    created=models.DateField(auto_now_add=True)
    date_start=models.DateField()
    date_end=models.DateField()
    #area of interest
    tlx=models.FloatField()
    tly=models.FloatField()
    brx=models.FloatField()
    bry=models.FloatField()
    result=JSONField()
    


# class Result(models.Model):
#      result=JSONField()
#      task=models.OneToOneField(Analysis,on_delete=models.CASCADE)
   
    

        


