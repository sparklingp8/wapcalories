from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("hi", views.get_msg),
    path("msg", views.bot),
    path('get_message_api/', views.get_message_api, name='get_message_api'),
    path("msg/<int:pid>", views.get_data_mobile),
    path("getData/<int:pid>", views.add_get_cal_data),
    path("getData/<int:pid>/<int:cal>", views.add_get_cal_data),
    path("addUser/<int:uid>", views.add_user)

]
