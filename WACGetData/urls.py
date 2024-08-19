from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("hi", views.get_msg),
    path("msg",views.bot),
    path("getData/<int:pid>",views.get_data),
    path("getData/<int:pid>/<int:cal>",views.get_data),

]
