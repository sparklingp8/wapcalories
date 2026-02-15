from django.contrib import admin
from .models import Quote


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "created_at")
    search_fields = ("text",)
    ordering = ("-created_at",)
