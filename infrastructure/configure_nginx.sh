#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-time-audit.just4u.app}"
EMAIL="${EMAIL:-admin@just4u.app}"
MODE="${MODE:-proxy}"  # proxy | static
SERVICE_NAME="time-audit.service"
SITE_FILE="/etc/nginx/sites-available/time-audit.conf"
STATIC_ROOT="/var/www/time-audit"
FRONTEND_DIST="/opt/time-audit/frontend/dist"

if [[ $EUID -ne 0 ]]; then
  echo "Run as root" >&2
  exit 1
fi

echo "[1] Installing packages (nginx certbot)" 
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python3-certbot-nginx

SERVICE_UNIT="/etc/systemd/system/${SERVICE_NAME}"
if grep -q -- "--host 0.0.0.0" "$SERVICE_UNIT"; then
  echo "[2] Rebinding backend to 127.0.0.1" 
  sed -i 's/--host 0.0.0.0/--host 127.0.0.1/' "$SERVICE_UNIT"
  systemctl daemon-reload
  systemctl restart "$SERVICE_NAME" || true
fi

if [[ "$MODE" == "static" ]]; then
  echo "[3] Preparing static root" 
  mkdir -p "$STATIC_ROOT"
  if [[ -d "$FRONTEND_DIST" ]]; then
    rsync -a --delete "$FRONTEND_DIST/" "$STATIC_ROOT/"
  else
    echo "Frontend dist not found: $FRONTEND_DIST (continuing)" >&2
  fi
fi

echo "[4] Writing nginx config (mode=$MODE)" 
cat > "$SITE_FILE" <<EOF
map \$http_upgrade \$connection_upgrade { default upgrade; '' close; }

server {
  listen 80;
  server_name ${DOMAIN};
  return 301 https://\$host\$request_uri;
}

server {
  listen 443 ssl http2;
  server_name ${DOMAIN};
  ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
  ssl_session_timeout 1d;
  ssl_session_cache shared:SSL:50m;
  ssl_session_tickets off;
  ssl_protocols TLSv1.2 TLSv1.3;
  ssl_prefer_server_ciphers off;
  add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
  add_header X-Content-Type-Options nosniff;
  add_header X-Frame-Options DENY;
  add_header Referrer-Policy no-referrer;
  add_header X-XSS-Protection "1; mode=block";
  client_max_body_size 25M;
EOF

if [[ "$MODE" == "static" ]]; then
  cat >> "$SITE_FILE" <<'EOF'
  root /var/www/time-audit;
  index index.html;
  location /api/ {
    proxy_pass http://127.0.0.1:8000/api/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
  }
  location /reports/ {
    proxy_pass http://127.0.0.1:8000/reports/;
    proxy_set_header Host $host;
  }
  location / {
    try_files $uri $uri/ /index.html;
  }
EOF
else
  cat >> "$SITE_FILE" <<'EOF'
  location / {
    proxy_pass http://127.0.0.1:8000/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
  }
EOF
fi

echo "}" >> "$SITE_FILE"

rm -f /etc/nginx/sites-enabled/default
ln -sf "$SITE_FILE" /etc/nginx/sites-enabled/time-audit.conf
nginx -t && systemctl reload nginx

if [[ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]]; then
  echo "[5] Obtaining certificate" 
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect
else
  echo "[5] Renew check (dry-run)" 
  certbot renew --dry-run || true
fi

echo "[DONE] Nginx configured (mode=$MODE) for https://${DOMAIN}" 
