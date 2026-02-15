from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("hi", views.get_msg),
    path('get_message_api/', views.get_message_api, name='get_message_api'),
   

]
