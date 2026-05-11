from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/transport/(?P<region_code>\w+)/$', consumers.TransportConsumer.as_asgi()),
    re_path(r'ws/driver/(?P<vehicle_id>\d+)/$', consumers.DriverConsumer.as_asgi()),
]
