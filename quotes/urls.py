from django.urls import path
from .views import quotes_api, random_quote_api, add_quote_api

urlpatterns = [
    path('all/', quotes_api, name='quotes_api'),
    path('random/', random_quote_api, name='random_quote_api'),
    path('add/', add_quote_api, name='add_quote_api'),
]
