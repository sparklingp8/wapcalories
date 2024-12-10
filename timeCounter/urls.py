from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("age", views.getAge, name="get_age"),
    path("try",views.tryy, name="tryy")
]