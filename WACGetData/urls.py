from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("hi", views.get_msg),
    path("msg",views.bot),
    path("getData/<int:pid>", views.add_get_cal_data),
    path("getData/<int:pid>/<int:cal>", views.add_get_cal_data),
    path("addUser/<int:uid>", views.add_user)

]
