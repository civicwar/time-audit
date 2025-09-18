#!/usr/bin/env bash
set -euo pipefail

DOMAIN="time-audit.just4u.app"
EMAIL="admin@just4u.app"
SERVICE_NAME="time-audit.service"
SITE_FILE="/etc/nginx/sites-available/time-audit.conf"

# Must run as root (or with sudo)
if [[ $EUID -ne 0 ]]; then
  echo "Run as root (sudo)." >&2
  exit 1
fi

echo "[1] Install required packages" 
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python3-certbot-nginx

# Adjust backend to bind localhost if not already
SERVICE_UNIT="/etc/systemd/system/${SERVICE_NAME}"
if grep -q -- "--host 0.0.0.0" "$SERVICE_UNIT"; then
  echo "[2] Updating service host binding to 127.0.0.1" 
  sed -i "s/--host 0.0.0.0/--host 127.0.0.1/" "$SERVICE_UNIT"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME" || true
fi

# Create Nginx site if missing
if [[ ! -f "$SITE_FILE" ]]; then
  echo "[3] Creating nginx site config" 
  cat > "$SITE_FILE" <<'EOF'
server {
    listen 80;
    server_name ${DOMAIN};

    root /var/www/html; # fallback
    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
  rm -f /etc/nginx/sites-enabled/default
  ln -sf "$SITE_FILE" /etc/nginx/sites-enabled/time-audit.conf
  nginx -t
  systemctl reload nginx
else
  echo "[3] Nginx site already exists, skipping creation" 
fi

# Obtain cert if not present
if [[ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]]; then
  echo "[4] Obtaining certificate with certbot" 
  certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${EMAIL}" --redirect
else
  echo "[4] Certificate already exists, attempting renew" 
  certbot renew --dry-run || true
fi

echo "[5] Add security headers (idempotent)" 
if ! grep -q "X-Content-Type-Options" "$SITE_FILE"; then
  sed -i "/proxy_set_header X-Forwarded-Proto/a \\tadd_header X-Content-Type-Options nosniff;\n\tadd_header X-Frame-Options DENY;\n\tadd_header Referrer-Policy no-referrer;\n\tadd_header X-XSS-Protection '1; mode=block';" "$SITE_FILE"
  nginx -t && systemctl reload nginx || echo "Header injection failed; manual review needed" >&2
fi

echo "[DONE] TLS setup complete for https://${DOMAIN}" 
