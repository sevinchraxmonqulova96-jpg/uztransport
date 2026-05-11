from django.db import models
from regions.models import Region


class Route(models.Model):
    TRANSPORT_TYPES = [
        ('bus', 'Avtobus'),
        ('marshrutka', 'Marshrutka'),
        ('trolleybus', 'Trolleybus'),
        ('metro', 'Metro'),
    ]
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='routes')
    route_number = models.CharField(max_length=20)
    route_name = models.CharField(max_length=200)
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_TYPES, default='bus')
    color = models.CharField(max_length=7, default='#FF6B35')
    is_active = models.BooleanField(default=True)
    polyline = models.JSONField(default=list)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Yo'nalish"
        verbose_name_plural = "Yo'nalishlar"
        ordering = ['route_number']

    def __str__(self):
        return f"{self.route_number} — {self.route_name}"

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.route_number,
            'name': self.route_name,
            'type': self.transport_type,
            'color': self.color,
            'polyline': self.polyline,
            'region_code': self.region.code,
        }


class Stop(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='stops')
    name = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    order = models.IntegerField()
    average_wait_time = models.IntegerField(default=5)
    is_terminal = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Bekat'
        verbose_name_plural = 'Bekatlar'
        ordering = ['order']

    def __str__(self):
        return f"{self.name} ({self.route.route_number})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.latitude,
            'lng': self.longitude,
            'order': self.order,
            'avg_wait': self.average_wait_time,
            'is_terminal': self.is_terminal,
        }


class Vehicle(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='vehicles')
    plate_number = models.CharField(max_length=20, unique=True)
    driver_name = models.CharField(max_length=100)
    driver_phone = models.CharField(max_length=20)
    capacity = models.IntegerField(default=50)
    current_passengers = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    vehicle_model = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Transport vositasi'
        verbose_name_plural = 'Transport vositalari'

    def __str__(self):
        return f"{self.plate_number} ({self.route.route_number})"

    @property
    def occupancy_percent(self):
        if self.capacity > 0:
            return min(100, int((self.current_passengers / self.capacity) * 100))
        return 0

    @property
    def occupancy_color(self):
        p = self.occupancy_percent
        if p < 50: return '#22c55e'
        elif p < 80: return '#f59e0b'
        else: return '#ef4444'

    def to_dict(self):
        return {
            'id': self.id,
            'plate': self.plate_number,
            'driver': self.driver_name,
            'capacity': self.capacity,
            'passengers': self.current_passengers,
            'occupancy': self.occupancy_percent,
            'occupancy_color': self.occupancy_color,
            'route_id': self.route_id,
            'route_number': self.route.route_number,
            'route_color': self.route.color,
            'transport_type': self.route.transport_type,
            'is_online': self.is_online,
        }


class VehicleLocation(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(default=0.0)
    heading = models.FloatField(default=0.0)
    accuracy = models.FloatField(default=0.0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Joylashuv'
        verbose_name_plural = 'Joylashuvlar'
        get_latest_by = 'timestamp'
        indexes = [
            models.Index(fields=['vehicle', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.vehicle.plate_number} @ {self.timestamp:%H:%M:%S}"
