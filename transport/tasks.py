from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_old_locations():
    """
    Eski joylashuv ma'lumotlarini tozalash (1 kundan eski).
    Kunlik ishga tushadi.
    """
    from transport.models import VehicleLocation
    cutoff = timezone.now() - timedelta(days=1)
    deleted, _ = VehicleLocation.objects.filter(timestamp__lt=cutoff).delete()
    logger.info(f"cleanup_old_locations: {deleted} ta yozuv o'chirildi")
    return deleted


@shared_task
def mark_inactive_vehicles():
    """
    5 daqiqadan ko'proq yangilanmagan transport vositalarini offline qilish.
    """
    from transport.models import Vehicle
    cutoff = timezone.now() - timedelta(minutes=5)
    count = Vehicle.objects.filter(is_online=True, last_seen__lt=cutoff).update(is_online=False)
    logger.info(f"mark_inactive_vehicles: {count} ta transport offline qilindi")
    return count


@shared_task
def update_region_stats():
    """
    Viloyat statistikasini yangilash (kesh).
    """
    from django.core.cache import cache
    from regions.models import Region
    from transport.models import Vehicle, Route

    for region in Region.objects.filter(is_active=True):
        stats = {
            'online_vehicles': Vehicle.objects.filter(
                route__region=region, is_online=True, is_active=True
            ).count(),
            'total_routes': Route.objects.filter(region=region, is_active=True).count(),
        }
        cache.set(f'region_stats_{region.code}', stats, 60)

    logger.info("update_region_stats: statistikalar yangilandi")
