from django.urls import path
from .web_views import IndexView, DriverView, AdminDashView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('driver/', DriverView.as_view(), name='driver'),
    path('dashboard/', AdminDashView.as_view(), name='dashboard'),
]
