import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

logger = logging.getLogger(__name__)


def calculate_eta(v_lat, v_lng, s_lat, s_lng, speed):
    try:
        from geopy.distance import geodesic
        dist_km = geodesic((v_lat, v_lng), (s_lat, s_lng)).km
        spd = max(speed, 5)
        return round((dist_km / spd) * 60), round(dist_km, 2)
    except Exception:
        return 0, 0


class TransportConsumer(AsyncWebsocketConsumer):
    """Yo'lovchilar uchun — viloyat bo'yicha real-vaqt monitoring"""

    async def connect(self):
        self.region_code = self.scope['url_route']['kwargs']['region_code']
        self.group_name = f"transport_{self.region_code}"
        self.subscribed_routes = set()

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_initial_state()
        logger.info(f"[WS] Passenger connected: {self.region_code}")

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        for rid in self.subscribed_routes:
            await self.channel_layer.group_discard(f"route_{rid}", self.channel_name)
        logger.info(f"[WS] Passenger disconnected: {self.region_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            t = data.get('type')
            if t == 'subscribe_route':
                rid = str(data['route_id'])
                self.subscribed_routes.add(rid)
                await self.channel_layer.group_add(f"route_{rid}", self.channel_name)
                await self.send(text_data=json.dumps({'type': 'subscribed', 'route_id': rid}))
            elif t == 'unsubscribe_route':
                rid = str(data['route_id'])
                self.subscribed_routes.discard(rid)
                await self.channel_layer.group_discard(f"route_{rid}", self.channel_name)
            elif t == 'find_nearby':
                nearby = await self.get_nearby(data.get('lat'), data.get('lng'), data.get('radius', 1000))
                await self.send(text_data=json.dumps({'type': 'nearby_vehicles', 'vehicles': nearby}))
            elif t == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.error(f"TransportConsumer.receive error: {e}")

    async def send_initial_state(self):
        vehicles, routes, stops = await self.load_initial_data()
        await self.send(text_data=json.dumps({
            'type': 'initial_state',
            'vehicles': vehicles,
            'routes': routes,
            'stops': stops,
        }))

    # ── Channel layer event handlers ──────────────────────────────────────

    async def vehicle_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'vehicle_update',
            'vehicle_id': event['vehicle_id'],
            'lat': event['lat'],
            'lng': event['lng'],
            'speed': event['speed'],
            'heading': event['heading'],
            'route_id': event['route_id'],
            'passengers': event.get('passengers', 0),
            'occupancy': event.get('occupancy', 0),
            'occupancy_color': event.get('occupancy_color', '#22c55e'),
            'eta_stops': event.get('eta_stops', []),
            'timestamp': event.get('timestamp', ''),
            'plate': event.get('plate', ''),
            'route_number': event.get('route_number', ''),
            'route_color': event.get('route_color', '#FF6B35'),
            'transport_type': event.get('transport_type', 'bus'),
        }))

    async def vehicle_offline(self, event):
        await self.send(text_data=json.dumps({
            'type': 'vehicle_offline',
            'vehicle_id': event['vehicle_id'],
        }))

    # ── DB helpers ────────────────────────────────────────────────────────

    @database_sync_to_async
    def load_initial_data(self):
        from transport.models import Vehicle, Route, Stop, VehicleLocation
        from regions.models import Region
        vehicles, routes, stops = [], [], []
        try:
            region = Region.objects.get(code=self.region_code)
            for r in Route.objects.filter(region=region, is_active=True):
                routes.append(r.to_dict())
            for s in Stop.objects.filter(route__region=region, route__is_active=True).select_related('route'):
                stops.append(s.to_dict())
            for v in Vehicle.objects.filter(route__region=region, is_active=True, is_online=True).select_related('route'):
                try:
                    loc = v.locations.latest()
                    d = v.to_dict()
                    d.update({'lat': loc.latitude, 'lng': loc.longitude, 'speed': loc.speed, 'heading': loc.heading})
                    vehicles.append(d)
                except VehicleLocation.DoesNotExist:
                    pass
        except Exception as e:
            logger.error(f"load_initial_data: {e}")
        return vehicles, routes, stops

    @database_sync_to_async
    def get_nearby(self, lat, lng, radius_m):
        from transport.models import Vehicle, VehicleLocation
        from geopy.distance import geodesic
        result = []
        if not lat or not lng:
            return result
        qs = Vehicle.objects.filter(route__region__code=self.region_code, is_active=True, is_online=True).select_related('route')
        for v in qs:
            try:
                loc = v.locations.latest()
                dist = geodesic((lat, lng), (loc.latitude, loc.longitude)).meters
                if dist <= radius_m:
                    d = v.to_dict()
                    d.update({'lat': loc.latitude, 'lng': loc.longitude, 'distance_m': round(dist)})
                    result.append(d)
            except VehicleLocation.DoesNotExist:
                pass
        result.sort(key=lambda x: x.get('distance_m', 9999))
        return result[:10]


class DriverConsumer(AsyncWebsocketConsumer):
    """Haydovchilar uchun — GPS yuborish va broadcast"""

    async def connect(self):
        self.vehicle_id = self.scope['url_route']['kwargs']['vehicle_id']
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return
        self.driver_group = f"driver_{self.vehicle_id}"
        await self.channel_layer.group_add(self.driver_group, self.channel_name)
        await self.accept()
        await self.set_vehicle_online(True)
        logger.info(f"[WS] Driver connected: vehicle {self.vehicle_id}")

    async def disconnect(self, code):
        await self.set_vehicle_online(False)
        await self.broadcast_offline()
        await self.channel_layer.group_discard(self.driver_group, self.channel_name)
        logger.info(f"[WS] Driver disconnected: vehicle {self.vehicle_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            t = data.get('type')
            if t == 'driver_location':
                await self.handle_location(data)
            elif t == 'update_passengers':
                await self.update_passenger_count(data.get('count', 0))
                await self.send(text_data=json.dumps({'type': 'passengers_updated', 'count': data.get('count', 0)}))
            elif t == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception as e:
            logger.error(f"DriverConsumer.receive: {e}")

    async def handle_location(self, data):
        loc = await self.save_location(data)
        if not loc:
            return
        info = await self.get_vehicle_info()
        if not info:
            return
        eta_stops = await self.compute_eta(data['lat'], data['lng'], data.get('speed', 0))

        payload = {
            'type': 'vehicle_update',
            'vehicle_id': int(self.vehicle_id),
            'lat': data['lat'],
            'lng': data['lng'],
            'speed': data.get('speed', 0),
            'heading': data.get('heading', 0),
            'route_id': info['route_id'],
            'passengers': info['passengers'],
            'occupancy': info['occupancy'],
            'occupancy_color': info['occupancy_color'],
            'eta_stops': eta_stops,
            'timestamp': timezone.now().isoformat(),
            'plate': info['plate'],
            'route_number': info['route_number'],
            'route_color': info['route_color'],
            'transport_type': info['transport_type'],
        }
        # Viloyat va yo'nalish group'lariga broadcast
        await self.channel_layer.group_send(f"transport_{info['region_code']}", payload)
        await self.channel_layer.group_send(f"route_{info['route_id']}", payload)
        await self.send(text_data=json.dumps({'type': 'location_received', 'eta_stops': eta_stops}))

    async def broadcast_offline(self):
        info = await self.get_vehicle_info()
        if info:
            await self.channel_layer.group_send(
                f"transport_{info['region_code']}",
                {'type': 'vehicle_offline', 'vehicle_id': int(self.vehicle_id)}
            )

    # ── DB helpers ────────────────────────────────────────────────────────

    @database_sync_to_async
    def set_vehicle_online(self, status):
        from transport.models import Vehicle
        Vehicle.objects.filter(id=self.vehicle_id).update(is_online=status)

    @database_sync_to_async
    def save_location(self, data):
        from transport.models import Vehicle, VehicleLocation
        try:
            v = Vehicle.objects.get(id=self.vehicle_id)
            return VehicleLocation.objects.create(
                vehicle=v,
                latitude=data['lat'],
                longitude=data['lng'],
                speed=data.get('speed', 0),
                heading=data.get('heading', 0),
                accuracy=data.get('accuracy', 0),
            )
        except Exception as e:
            logger.error(f"save_location: {e}")
            return None

    @database_sync_to_async
    def get_vehicle_info(self):
        from transport.models import Vehicle
        try:
            v = Vehicle.objects.select_related('route', 'route__region').get(id=self.vehicle_id)
            return {
                'route_id': v.route_id,
                'region_code': v.route.region.code,
                'passengers': v.current_passengers,
                'occupancy': v.occupancy_percent,
                'occupancy_color': v.occupancy_color,
                'plate': v.plate_number,
                'route_number': v.route.route_number,
                'route_color': v.route.color,
                'transport_type': v.route.transport_type,
            }
        except Exception:
            return None

    @database_sync_to_async
    def compute_eta(self, v_lat, v_lng, speed):
        from transport.models import Vehicle, Stop
        result = []
        try:
            v = Vehicle.objects.get(id=self.vehicle_id)
            for stop in Stop.objects.filter(route=v.route).order_by('order'):
                eta_min, dist_km = calculate_eta(v_lat, v_lng, stop.latitude, stop.longitude, speed)
                result.append({
                    'stop_id': stop.id,
                    'stop_name': stop.name,
                    'eta_minutes': eta_min,
                    'distance_km': dist_km,
                })
        except Exception as e:
            logger.error(f"compute_eta: {e}")
        return result

    @database_sync_to_async
    def update_passenger_count(self, count):
        from transport.models import Vehicle
        Vehicle.objects.filter(id=self.vehicle_id).update(current_passengers=count)
