from django.urls import path
from jarvis import views

urlpatterns=[
   path('login',views.login,name='login'),
   path('logout',views.logout,name='logout'),
   path('register',views.register,name='createuser'),
   path('analysis',views.analysis,name='analysis'),
   path('display',views.display_analysis,name='list analysis'),
   path('result',views.result,name='display result')
   # path('result',views.result,name='result')
]
