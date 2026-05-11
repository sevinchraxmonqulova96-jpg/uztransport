from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    # JWT Auth
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Apps
    path('api/', include('transport.urls')),
    path('api/auth/', include('accounts.urls')),
    # Frontend pages
    path('', include('transport.web_urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
