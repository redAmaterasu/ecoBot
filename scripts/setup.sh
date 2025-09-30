#!/usr/bin/env bash
set -euo pipefail

# HeshmatBot one-click setup (Ubuntu/Debian)
# - Installs system packages, Python, MySQL
# - Creates DB/user/schema, .env
# - Creates systemd service and enables it

if [[ $(id -u) -ne 0 ]]; then
  echo "Please run as root (use sudo)." >&2
  exit 1
fi

PROJECT_DIR="/opt/heshmatbot"
PYTHON_BIN="python3"
SERVICE_NAME="heshmatbot"
DB_NAME="heshmatbot"

read -rp "Enter Telegram BOT_TOKEN: " BOT_TOKEN
read -rp "Enter ADMIN_PASSWORD [admin123]: " ADMIN_PASSWORD
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
read -rp "Enter MySQL root password (will be set if empty currently): " MYSQL_ROOT_PWD
read -rp "Create DB user (non-root) [heshmat]: " DB_USER
DB_USER=${DB_USER:-heshmat}
read -srp "Password for DB user ${DB_USER}: " DB_PASSWORD
echo

echo "Updating apt cache..."
apt-get update -y

echo "Installing dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  curl ca-certificates git python3 python3-venv python3-pip \
  mysql-server

echo "Securing MySQL and setting root password if needed..."
systemctl enable --now mysql

# Try to set root password and switch to native password auth
mysql -uroot -e "SELECT 1" >/dev/null 2>&1 || true
if ! mysql -uroot -e "SELECT 1" >/dev/null 2>&1; then
  echo "Configuring MySQL root account..."
  mysql --user=root <<SQL
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PWD}';
FLUSH PRIVILEGES;
SQL
fi

echo "Creating database and user..."
mysql -uroot -p"${MYSQL_ROOT_PWD}" <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

echo "Deploying project to ${PROJECT_DIR}..."
mkdir -p "${PROJECT_DIR}"
rsync -a --delete --exclude ".git" --exclude "venv" /workspace/ "${PROJECT_DIR}/"
cd "${PROJECT_DIR}"

echo "Creating virtual environment..."
${PYTHON_BIN} -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Writing .env file..."
cat > .env <<ENV
BOT_TOKEN=${BOT_TOKEN}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
DB_HOST=localhost
DB_PORT=3306
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=${DB_NAME}
ENV

echo "Initializing database schema..."
mysql -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" < mysql_setup.sql || true

echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<SERVICE
[Unit]
Description=HeshmatBot Telegram Bot
After=network.target mysql.service

[Service]
Type=simple
WorkingDirectory=${PROJECT_DIR}
Environment="PYTHONUNBUFFERED=1"
ExecStart=${PROJECT_DIR}/venv/bin/python ${PROJECT_DIR}/bot.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

echo "Reloading systemd and enabling service..."
systemctl daemon-reload
systemctl enable --now ${SERVICE_NAME}

echo "Setup complete. Service status:"
systemctl --no-pager status ${SERVICE_NAME} || true

echo "Logs (tail -n 50):"
journalctl -u ${SERVICE_NAME} -n 50 --no-pager || true

echo "Done."

