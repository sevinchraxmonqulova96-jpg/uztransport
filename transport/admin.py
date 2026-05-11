from django.contrib import admin
from .models import Route, Stop, Vehicle, VehicleLocation


class StopInline(admin.TabularInline):
    model = Stop
    extra = 0


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['route_number', 'route_name', 'transport_type', 'region', 'is_active']
    list_filter = ['transport_type', 'is_active', 'region']
    search_fields = ['route_number', 'route_name']
    inlines = [StopInline]


@admin.register(Stop)
class StopAdmin(admin.ModelAdmin):
    list_display = ['name', 'route', 'order', 'average_wait_time']
    list_filter = ['route__region']
    search_fields = ['name']


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['plate_number', 'driver_name', 'route', 'current_passengers', 'capacity', 'is_online', 'is_active']
    list_filter = ['is_active', 'is_online', 'route__region']
    search_fields = ['plate_number', 'driver_name']


@admin.register(VehicleLocation)
class VehicleLocationAdmin(admin.ModelAdmin):
    list_display = ['vehicle', 'latitude', 'longitude', 'speed', 'timestamp']
    list_filter = ['vehicle__route__region']
    readonly_fields = ['timestamp']
