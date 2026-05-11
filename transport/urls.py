from django.urls import path
from .views import (
    RegionListView, RegionRoutesView,
    RouteDetailView, RouteVehiclesView, RouteStopsView,
    VehicleLocationView, NearbyVehiclesView,
    DriverUpdateLocationView, StatsView,
)

urlpatterns = [
    # Regions
    path('regions/', RegionListView.as_view()),
    path('regions/<str:region_code>/routes/', RegionRoutesView.as_view()),
    # Routes
    path('routes/<int:pk>/', RouteDetailView.as_view()),
    path('routes/<int:route_id>/vehicles/', RouteVehiclesView.as_view()),
    path('routes/<int:route_id>/stops/', RouteStopsView.as_view()),
    # Vehicles
    path('vehicles/<int:vehicle_id>/location/', VehicleLocationView.as_view()),
    path('vehicles/nearby/', NearbyVehiclesView.as_view()),
    # Driver
    path('driver/update-location/', DriverUpdateLocationView.as_view()),
    # Stats
    path('stats/', StatsView.as_view()),
]
