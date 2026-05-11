# 🚌 UzTransport Live

**O'zbekiston uchun real-vaqt jamoat transporti monitoring tizimi**

> Django 4.2 + Django Channels + WebSocket + Leaflet.js + OpenStreetMap

---

## 🖥 Sahifalar

| Sahifa | URL | Tavsif |
|--------|-----|--------|
| 🗺 Xarita | `/` | Yo'lovchilar uchun real-vaqt xarita |
| 🚌 Haydovchi | `/driver/` | Haydovchi GPS paneli |
| 📊 Dashboard | `/dashboard/` | Boshqaruv statistikasi |
| ⚙️ Admin | `/admin/` | Django admin paneli |

---

## ⚡ Tez boshlash (lokal)

### 1. Talablar
```
Python 3.10+
Redis (lokal yoki Docker)
```

### 2. O'rnatish
```bash
git clone <repo>
cd uztransport

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # .env ni tahrirlang
```

### 3. Redis ishga tushirish
```bash
# Docker orqali (oson):
docker run -d -p 6379:6379 redis:alpine

# Yoki lokal o'rnatish (Ubuntu):
sudo apt install redis-server && sudo systemctl start redis
```

### 4. Bazani sozlash
```bash
python manage.py migrate
python manage.py loaddata fixtures/regions.json
python manage.py seed_demo
```

### 5. Ishga tushirish
```bash
python manage.py runserver
```

Brauzerda oching: **http://127.0.0.1:8000/**

---

## 🔑 Demo kirish

| Rol | Login | Parol |
|-----|-------|-------|
| Admin | `admin` | `admin123` |
| Haydovchi 1 | `driver1` | `driver123` |
| Haydovchi 2 | `driver2` | `driver123` |
| Haydovchi 3 | `driver3` | `driver123` |

---

## 🌐 API Endpointlar

```
GET  /api/regions/                       → 14 viloyat ro'yxati
GET  /api/regions/{code}/routes/         → Viloyat yo'nalishlari
GET  /api/routes/{id}/vehicles/          → Yo'nalishdagi transport
GET  /api/routes/{id}/stops/             → Bekatlar
GET  /api/vehicles/{id}/location/        → Oxirgi joylashuv
GET  /api/vehicles/nearby/?lat=&lng=     → Yaqin transport
POST /api/driver/update-location/        → GPS yuborish (REST)
GET  /api/stats/                         → Umumiy statistika
POST /api/token/                         → JWT token olish
POST /api/token/refresh/                 → Tokenni yangilash
POST /api/auth/register/                 → Ro'yxatdan o'tish
```

---

## 🔌 WebSocket Endpointlar

```
ws://domain/ws/transport/{region_code}/   → Yo'lovchi monitoring
ws://domain/ws/driver/{vehicle_id}/       → Haydovchi GPS yuborish
```

### Yo'lovchi WebSocket xabarlari

```javascript
// Yo'nalishga obuna bo'lish
ws.send(JSON.stringify({ type: 'subscribe_route', route_id: 1 }))

// Yaqin transport topish
ws.send(JSON.stringify({ type: 'find_nearby', lat: 41.29, lng: 69.24, radius: 1000 }))
```

### Server → Client xabarlar

```javascript
// Boshlang'ich holat
{ type: 'initial_state', vehicles: [...], routes: [...], stops: [...] }

// Transport yangilanishi
{
  type: 'vehicle_update',
  vehicle_id: 1,
  lat: 41.299, lng: 69.240,
  speed: 45.5, heading: 180,
  route_id: 1, route_number: '7',
  passengers: 23, occupancy: 46,
  occupancy_color: '#22c55e',
  eta_stops: [{ stop_id: 1, stop_name: 'Bozor', eta_minutes: 3, distance_km: 0.8 }]
}

// Transport offline ketdi
{ type: 'vehicle_offline', vehicle_id: 1 }

// Yaqin transport
{ type: 'nearby_vehicles', vehicles: [...] }
```

---

## 🖥 Serverga deploy (Ubuntu 22.04)

### Bepul serverlar
- **Railway.app** — `railway up` (Redis ham bor)
- **Render.com** — Web Service + Redis
- **Fly.io** — `fly deploy`
- **Oracle Cloud Free Tier** — 4 vCPU, 24GB RAM bepul!

### VPS ga deploy
```bash
# Loyihani serverga ko'chirish
scp -r uztransport/ ubuntu@YOUR_SERVER_IP:/home/ubuntu/

# Serverga kirish
ssh ubuntu@YOUR_SERVER_IP

# Deploy skriptini ishga tushirish
cd /home/ubuntu/uztransport
chmod +x deploy.sh
sudo DOMAIN=yourdomain.uz ./deploy.sh
```

### Railway.app (eng oson)
```bash
npm install -g @railway/cli
railway login
railway init
railway add redis
railway up
```

`Procfile` yaratish kerak:
```
web: daphne -b 0.0.0.0 -p $PORT core.asgi:application
```

### Render.com
1. GitHub ga push qiling
2. render.com da "New Web Service"
3. Build command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
4. Start command: `daphne -b 0.0.0.0 -p $PORT core.asgi:application`
5. Redis qo'shing (Environment → Add Redis)

---

## 🗂 Loyiha tuzilishi

```
uztransport/
├── core/               # Django sozlamalari
│   ├── settings.py
│   ├── asgi.py         # Daphne/Channels ASGI
│   ├── urls.py
│   └── celery.py
├── transport/          # Asosiy app
│   ├── models.py       # Route, Stop, Vehicle, VehicleLocation
│   ├── consumers.py    # WebSocket consumers
│   ├── views.py        # REST API
│   ├── serializers.py
│   ├── routing.py      # WS URL routing
│   ├── middleware.py   # JWT auth middleware
│   ├── tasks.py        # Celery tasks
│   ├── web_views.py    # HTML pages
│   ├── urls.py         # API URLs
│   └── web_urls.py     # Page URLs
├── accounts/           # Foydalanuvchilar
├── regions/            # Viloyatlar
├── analytics/          # Statistika (kelajakda)
├── templates/
│   └── transport/
│       ├── index.html      # 🗺 Xarita
│       ├── driver.html     # 🚌 Haydovchi paneli
│       └── dashboard.html  # 📊 Dashboard
├── fixtures/
│   └── regions.json    # 14 viloyat ma'lumotlari
├── nginx/
│   └── uztransport.conf
├── supervisor/
│   └── uztransport.conf
├── deploy.sh           # Avtomatik deploy
├── requirements.txt
└── .env.example
```

---

## 🔧 Muhim sozlamalar

### PostgreSQL + PostGIS (production uchun)
```bash
sudo apt install postgresql postgis
sudo -u postgres createdb uztransport
sudo -u postgres psql -c "CREATE EXTENSION postgis;" uztransport
```

`.env` da:
```
USE_POSTGRES=True
DB_NAME=uztransport
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### SSL (HTTPS/WSS) — Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.uz -d www.yourdomain.uz
```

---

## 📋 Management commands

```bash
# Demo ma'lumotlar yaratish
python manage.py seed_demo

# Viloyatlarni yuklash
python manage.py loaddata fixtures/regions.json

# Eski joylashuvlarni tozalash
python manage.py shell -c "from transport.tasks import cleanup_old_locations; cleanup_old_locations()"
```

---

## 🔒 Xavfsizlik

- **JWT auth** — Haydovchi WebSocket ulanishida token tekshiriladi
- **CORS** — Ruxsat etilgan domenlar `.env` da sozlanadi
- **Rate limiting** — Nginx darajasida sozlash mumkin
- **Redis** — Channel layer va kesh uchun

---

## 📞 Qo'llab-quvvatlash

Muammolar uchun `admin` panelidan yoki log fayllardan foydalaning:
```bash
tail -f /var/log/uztransport/app.log
supervisorctl status
```
