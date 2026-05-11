from django.contrib import admin
from .models import Region

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name_uz', 'code', 'center_lat', 'center_lng', 'is_active']
    list_filter = ['is_active']
