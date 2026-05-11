from rest_framework import generics, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from geopy.distance import geodesic

from .models import Route, Stop, Vehicle, VehicleLocation
from .serializers import RouteListSerializer, RouteDetailSerializer, StopSerializer, VehicleSerializer
from regions.models import Region
from regions.serializers import RegionSerializer


class RegionListView(generics.ListAPIView):
    queryset = Region.objects.filter(is_active=True)
    serializer_class = RegionSerializer


class RegionRoutesView(generics.ListAPIView):
    serializer_class = RouteListSerializer

    def get_queryset(self):
        region = get_object_or_404(Region, code=self.kwargs['region_code'])
        return Route.objects.filter(region=region, is_active=True)


class RouteDetailView(generics.RetrieveAPIView):
    queryset = Route.objects.all()
    serializer_class = RouteDetailSerializer


class RouteVehiclesView(generics.ListAPIView):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(route_id=self.kwargs['route_id'], is_active=True).select_related('route')


class RouteStopsView(generics.ListAPIView):
    serializer_class = StopSerializer

    def get_queryset(self):
        return Stop.objects.filter(route_id=self.kwargs['route_id']).order_by('order')


class VehicleLocationView(views.APIView):
    def get(self, request, vehicle_id):
        v = get_object_or_404(Vehicle, id=vehicle_id)
        try:
            loc = v.locations.latest()
            return Response({
                'vehicle': VehicleSerializer(v).data,
                'lat': loc.latitude, 'lng': loc.longitude,
                'speed': loc.speed, 'heading': loc.heading,
                'timestamp': loc.timestamp,
            })
        except VehicleLocation.DoesNotExist:
            return Response({'detail': 'Joylashuv topilmadi'}, status=404)


class NearbyVehiclesView(views.APIView):
    def get(self, request):
        try:
            lat = float(request.query_params['lat'])
            lng = float(request.query_params['lng'])
        except (KeyError, ValueError):
            return Response({'error': 'lat va lng kerak'}, status=400)

        radius = float(request.query_params.get('radius', 2000))
        region_code = request.query_params.get('region')

        qs = Vehicle.objects.filter(is_active=True, is_online=True).select_related('route', 'route__region')
        if region_code:
            qs = qs.filter(route__region__code=region_code)

        nearby = []
        for v in qs:
            try:
                loc = v.locations.latest()
                dist = geodesic((lat, lng), (loc.latitude, loc.longitude)).meters
                if dist <= radius:
                    nearby.append({
                        'id': v.id,
                        'plate': v.plate_number,
                        'route_number': v.route.route_number,
                        'route_color': v.route.color,
                        'transport_type': v.route.transport_type,
                        'lat': loc.latitude, 'lng': loc.longitude,
                        'speed': loc.speed, 'heading': loc.heading,
                        'distance_m': round(dist),
                        'occupancy': v.occupancy_percent,
                        'occupancy_color': v.occupancy_color,
                    })
            except VehicleLocation.DoesNotExist:
                pass

        nearby.sort(key=lambda x: x['distance_m'])
        return Response(nearby[:15])


class DriverUpdateLocationView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            v = Vehicle.objects.get(id=data['vehicle_id'])
        except (Vehicle.DoesNotExist, KeyError):
            return Response({'error': 'Transport topilmadi'}, status=404)

        VehicleLocation.objects.create(
            vehicle=v,
            latitude=data['lat'],
            longitude=data['lng'],
            speed=data.get('speed', 0),
            heading=data.get('heading', 0),
            accuracy=data.get('accuracy', 0),
        )
        v.is_online = True
        v.save(update_fields=['is_online', 'last_seen'])
        return Response({'status': 'ok'})


class StatsView(views.APIView):
    def get(self, request):
        total_vehicles = Vehicle.objects.filter(is_active=True).count()
        online_vehicles = Vehicle.objects.filter(is_active=True, is_online=True).count()
        total_routes = Route.objects.filter(is_active=True).count()
        total_regions = Region.objects.filter(is_active=True).count()
        return Response({
            'total_vehicles': total_vehicles,
            'online_vehicles': online_vehicles,
            'total_routes': total_routes,
            'total_regions': total_regions,
        })
