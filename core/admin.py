from django.contrib import admin

from .models import RoomType


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "capacity", "display_order", "is_active", "is_sample")