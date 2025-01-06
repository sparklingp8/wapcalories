from django import urls
from django.urls import path

from . import views

urlpatterns = [
    path("age", views.getAge, name="get_age"),
    path("addNewUser",views.add_new_user, name="add_new_user"), 
    path('check-username/<str:username>', views.check_username, name='check-username'),
    path("<str:userID>", views.user_countdown, name="user_countdowns" ),    
    path("addCountdown/<str:userID>", views.user_add_countdown, name="user_add_countdowns" ),
    path("countdowns/delCountdown/<str:userID>/<str:count_name>", views.user_delete_countdown, name="user_delete_countdowns" ),
    
    path("countdowns/<str:userID>/<str:message>", views.user_countdown, name="user_countdowns" ),
    path("countdowns/<str:userID>", views.user_countdown, name="user_countdowns" ),
]