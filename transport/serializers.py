from rest_framework import serializers
from .models import Route, Stop, Vehicle, VehicleLocation


class StopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stop
        fields = ['id', 'name', 'latitude', 'longitude', 'order', 'average_wait_time', 'is_terminal']


class RouteListSerializer(serializers.ModelSerializer):
    stop_count = serializers.SerializerMethodField()
    online_vehicles = serializers.SerializerMethodField()

    class Meta:
        model = Route
        fields = ['id', 'route_number', 'route_name', 'transport_type', 'color', 'is_active', 'stop_count', 'online_vehicles']

    def get_stop_count(self, obj):
        return obj.stops.count()

    def get_online_vehicles(self, obj):
        return obj.vehicles.filter(is_active=True, is_online=True).count()


class RouteDetailSerializer(serializers.ModelSerializer):
    stops = StopSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = ['id', 'route_number', 'route_name', 'transport_type', 'color', 'polyline', 'description', 'stops']


class VehicleSerializer(serializers.ModelSerializer):
    occupancy_percent = serializers.ReadOnlyField()
    occupancy_color = serializers.ReadOnlyField()
    route_number = serializers.CharField(source='route.route_number', read_only=True)
    route_color = serializers.CharField(source='route.color', read_only=True)
    latest_location = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ['id', 'plate_number', 'driver_name', 'capacity', 'current_passengers',
                  'occupancy_percent', 'occupancy_color', 'is_online', 'route_number', 'route_color',
                  'vehicle_model', 'latest_location']

    def get_latest_location(self, obj):
        try:
            loc = obj.locations.latest()
            return {'lat': loc.latitude, 'lng': loc.longitude, 'speed': loc.speed, 'heading': loc.heading, 'timestamp': loc.timestamp}
        except VehicleLocation.DoesNotExist:
            return None
