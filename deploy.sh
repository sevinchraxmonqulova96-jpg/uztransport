#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# UzTransport Live — Deploy skripti (Ubuntu 22.04)
# Ishlatish: chmod +x deploy.sh && sudo ./deploy.sh
# ═══════════════════════════════════════════════════════════════
set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }

PROJECT_DIR="/home/ubuntu/uztransport"
VENV="$PROJECT_DIR/venv"
DOMAIN=${DOMAIN:-"yourdomain.uz"}

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════╗"
echo "║   UzTransport Live — Deploy             ║"
echo "║   Ubuntu 22.04 + Daphne + Nginx         ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# 1. System packages
info "Tizim paketlari o'rnatilmoqda..."
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv \
    nginx supervisor redis-server git curl \
    gcc libpq-dev python3-dev

log "Tizim paketlari o'rnatildi"

# 2. Redis
info "Redis ishga tushirilmoqda..."
systemctl enable redis-server
systemctl start redis-server
redis-cli ping | grep -q PONG && log "Redis ishlayapti" || warn "Redis muammo"

# 3. Project dir
mkdir -p "$PROJECT_DIR"
mkdir -p /var/log/uztransport
chown ubuntu:ubuntu /var/log/uztransport

# 4. Virtual environment
info "Python virtual environment yaratilmoqda..."
python3 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --upgrade pip -q
pip install -r "$PROJECT_DIR/requirements.txt" -q
log "Python paketlari o'rnatildi"

# 5. .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
    info ".env fayli yaratilmoqda..."
    SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
    cat > "$PROJECT_DIR/.env" << EOF
SECRET_KEY=$SECRET
DEBUG=False
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
USE_POSTGRES=False
CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN
EOF
    log ".env fayli yaratildi"
fi

# 6. Django setup
info "Django sozlanmoqda..."
cd "$PROJECT_DIR"
source "$VENV/bin/activate"
python manage.py migrate --noinput
python manage.py collectstatic --noinput -v 0

# Load fixtures
python manage.py loaddata fixtures/regions.json || warn "Fixtures allaqachon yuklangan"
python manage.py seed_demo || warn "Demo data allaqachon mavjud"
log "Django sozlandi"

# 7. Supervisor
info "Supervisor sozlanmoqda..."
cp "$PROJECT_DIR/supervisor/uztransport.conf" /etc/supervisor/conf.d/
supervisorctl reread
supervisorctl update
supervisorctl restart uztransport-all || supervisorctl start uztransport-all
log "Supervisor sozlandi"

# 8. Nginx
info "Nginx sozlanmoqda..."
cp "$PROJECT_DIR/nginx/uztransport.conf" /etc/nginx/sites-available/uztransport
ln -sf /etc/nginx/sites-available/uztransport /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
log "Nginx sozlandi"

# 9. SSL (ixtiyoriy)
if command -v certbot &>/dev/null; then
    info "SSL sertifikat olinmoqda..."
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos -m "admin@$DOMAIN" || warn "SSL olishda muammo (domenni tekshiring)"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   🎉 Deploy muvaffaqiyatli yakunlandi!  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  🌐 Xarita:      ${BLUE}http://$DOMAIN/${NC}"
echo -e "  🚌 Haydovchi:   ${BLUE}http://$DOMAIN/driver/${NC}"
echo -e "  📊 Dashboard:   ${BLUE}http://$DOMAIN/dashboard/${NC}"
echo -e "  ⚙️  Admin:       ${BLUE}http://$DOMAIN/admin/${NC}  (admin/admin123)"
echo ""
