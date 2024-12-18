from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("age", views.getAge, name="get_age"),
    path("<str:userID>", views.user_countdown, name="user_countdowns" ),    
    path("addCountdown/<str:userID>", views.user_add_countdown, name="user_add_countdowns" ),
    path("countdowns/delCountdown/<str:userID>/<str:count_name>", views.user_delete_countdown, name="user_delete_countdowns" ),
    path("try",views.tryy, name="tryy"),
    path("countdowns/<str:userID>/<str:message>", views.user_countdown, name="user_countdowns" ),
    path("countdowns/<str:userID>", views.user_countdown, name="user_countdowns" ),
]