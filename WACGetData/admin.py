from django.contrib import admin
from .models import UserProfile, DailyEntry, PhoneNumberMapping


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id",)   # Add your fields here


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("id",)   # Add your fields here

 
@admin.register(PhoneNumberMapping)   
class PhoneNumberMappingAdmin(admin.ModelAdmin):
    list_display = ("id",)   # Add your fields here

