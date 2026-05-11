"""
Demo ma'lumotlar yaratish:
python manage.py seed_demo
"""
import random
import math
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

ROUTE_COLORS = ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
                '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']

TASHKENT_ROUTES = [
    ('1', 'Yunusobod — Chilonzor', 'bus', [[41.340, 69.284], [41.330, 69.275], [41.320, 69.263], [41.310, 69.252], [41.299, 69.240], [41.288, 69.228]]),
    ('7', 'Sergeli — Bektemir', 'bus', [[41.240, 69.200], [41.255, 69.215], [41.270, 69.230], [41.285, 69.248], [41.299, 69.265]]),
    ('M1', 'Metro: Chorsu — Yunusobod', 'metro', [[41.299, 69.240], [41.308, 69.248], [41.318, 69.257], [41.328, 69.268], [41.338, 69.279]]),
    ('45', 'Mirzo Ulugbek — Shayhontohur', 'marshrutka', [[41.340, 69.310], [41.325, 69.295], [41.310, 69.280], [41.299, 69.270]]),
    ('101', 'Aeroport — Markaziy vokzal', 'bus', [[41.259, 69.281], [41.270, 69.270], [41.280, 69.260], [41.291, 69.249]]),
]

STOP_NAMES = [
    'Markaziy maydon', 'Bozor', 'Maktab', 'Shifoxona', 'Park',
    'Universitet', 'Metro bekati', 'Pochta', 'Do\'kon', 'Stadion',
    'Mehmonxona', 'Zavod', 'Uy-joylar', 'Chorraha', 'Terminal',
]


class Command(BaseCommand):
    help = 'Demo ma\'lumotlar yaratish (viloyatlar, yo\'nalishlar, transport, haydovchilar)'

    def handle(self, *args, **options):
        from regions.models import Region
        from transport.models import Route, Stop, Vehicle, VehicleLocation

        self.stdout.write('🚀 Demo ma\'lumotlar yuklanmoqda...')

        # Viloyatlar fixtures orqali yuklanadi, lekin yo'q bo'lsa yaratamiz
        if not Region.objects.exists():
            self.stdout.write('  📍 Viloyatlar yaratilmoqda...')
            REGIONS = [
                ('Toshkent shahri',   'Toshkent shahri',   'TSH', 41.2995, 69.2401),
                ('Toshkent viloyati', 'Toshkent viloyati', 'TSV', 41.1173, 69.2182),
                ('Samarqand',         'Samarqand',         'SMQ', 39.6542, 66.9597),
                ('Buxoro',            'Buxoro',            'BXR', 39.7747, 64.4286),
                ('Namangan',          'Namangan',           'NMG', 41.0011, 71.6725),
                ('Andijon',           'Andijon',            'ADJ', 40.7829, 72.3442),
                ("Farg'ona",          "Farg'ona",           'FRG', 40.3842, 71.7843),
                ('Qashqadaryo',       'Qashqadaryo',        'QSH', 38.8600, 65.7911),
                ('Surxondaryo',       'Surxondaryo',        'SRX', 37.9400, 67.5700),
                ('Jizzax',            'Jizzax',             'JZX', 40.1158, 67.8422),
                ('Sirdaryo',          'Sirdaryo',           'SRD', 40.8393, 68.6644),
                ('Xorazm',            'Xorazm',             'XRZ', 41.3775, 60.3597),
                ('Navoiy',            'Navoiy',             'NVY', 40.0840, 65.3792),
                ("Qoraqalpog'iston",  "Qoraqalpog'iston",  'QRQ', 43.7687, 59.3678),
            ]
            for name, name_uz, code, lat, lng in REGIONS:
                Region.objects.get_or_create(code=code, defaults={
                    'name': name, 'name_uz': name_uz,
                    'center_lat': lat, 'center_lng': lng, 'is_active': True,
                })
            self.stdout.write(self.style.SUCCESS('  ✅ 14 viloyat yaratildi'))

        tsh = Region.objects.filter(code='TSH').first()
        if not tsh:
            self.stdout.write(self.style.ERROR('❌ Viloyatlar topilmadi.'))
            return

        # Yo'nalishlar
        for num, name, ttype, polyline in TASHKENT_ROUTES:
            route, created = Route.objects.get_or_create(
                region=tsh,
                route_number=num,
                defaults={
                    'route_name': name,
                    'transport_type': ttype,
                    'color': random.choice(ROUTE_COLORS),
                    'polyline': polyline,
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(f'  ✅ Yo\'nalish: {num} — {name}')
                # Bekatlar yaratish
                for i, (lat, lng) in enumerate(polyline):
                    Stop.objects.create(
                        route=route,
                        name=STOP_NAMES[i % len(STOP_NAMES)],
                        latitude=lat + random.uniform(-0.002, 0.002),
                        longitude=lng + random.uniform(-0.002, 0.002),
                        order=i + 1,
                        average_wait_time=random.randint(3, 10),
                        is_terminal=(i == 0 or i == len(polyline) - 1),
                    )

        # Haydovchi foydalanuvchilari
        driver_names = [
            ('Alibek Rahimov', '+998901234567'),
            ('Jasur Karimov', '+998901234568'),
            ('Bobur Toshmatov', '+998901234569'),
            ('Sardor Yusupov', '+998901234570'),
            ('Nodir Hasanov', '+998901234571'),
        ]

        routes = list(Route.objects.filter(region=tsh, is_active=True))

        for i, (dname, phone) in enumerate(driver_names):
            uname = f"driver{i+1}"
            user, _ = User.objects.get_or_create(
                username=uname,
                defaults={'role': 'driver', 'phone': phone, 'first_name': dname.split()[0], 'last_name': dname.split()[1]}
            )
            if _:
                user.set_password('driver123')
                user.save()

            route = routes[i % len(routes)]
            plates = ['01A123BB', '01B456CC', '10C789DD', '15D012EE', '20E345FF']
            models = ['Isuzu NQR', 'MAN Lion\'s City', 'Mercedes Citaro', 'Yutong ZK6118', 'Golden Dragon XML6125']

            vehicle, created = Vehicle.objects.get_or_create(
                plate_number=plates[i],
                defaults={
                    'route': route,
                    'driver_name': dname,
                    'driver_phone': phone,
                    'capacity': random.choice([30, 40, 50, 60, 80]),
                    'current_passengers': random.randint(5, 45),
                    'is_active': True,
                    'is_online': True,
                    'vehicle_model': models[i],
                }
            )

            if created:
                self.stdout.write(f'  🚌 Transport: {plates[i]} — {dname}')
                # Boshlang'ich joylashuv
                start_point = route.polyline[0] if route.polyline else [41.299, 69.240]
                VehicleLocation.objects.create(
                    vehicle=vehicle,
                    latitude=start_point[0] + random.uniform(-0.005, 0.005),
                    longitude=start_point[1] + random.uniform(-0.005, 0.005),
                    speed=random.uniform(20, 60),
                    heading=random.uniform(0, 360),
                )

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@uztransport.uz', 'admin123', role='admin')
            self.stdout.write('  👤 Admin: admin / admin123')

        self.stdout.write(self.style.SUCCESS('\n✅ Demo ma\'lumotlar muvaffaqiyatli yaratildi!'))
        self.stdout.write(self.style.SUCCESS('   Xarita: http://127.0.0.1:8000/'))
        self.stdout.write(self.style.SUCCESS('   Haydovchi: http://127.0.0.1:8000/driver/'))
        self.stdout.write(self.style.SUCCESS('   Admin: http://127.0.0.1:8000/admin/  (admin/admin123)'))
