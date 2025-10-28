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

export DEBIAN_FRONTEND=noninteractive

PROJECT_DIR="${PROJECT_DIR:-/opt/heshmatbot}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SERVICE_NAME="${SERVICE_NAME:-heshmatbot}"
DB_NAME="${DB_NAME:-heshmatbot}"

# Take input from env if provided, otherwise prompt interactively
BOT_TOKEN="${BOT_TOKEN:-}"
if [[ -z "${BOT_TOKEN}" ]]; then
  read -rp "Enter Telegram BOT_TOKEN: " BOT_TOKEN
fi

ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin123}"
read -rp "Enter ADMIN_PASSWORD [${ADMIN_PASSWORD}]: " _ADMIN_PASSWORD || true
ADMIN_PASSWORD=${_ADMIN_PASSWORD:-${ADMIN_PASSWORD}}

MYSQL_ROOT_PWD="${MYSQL_ROOT_PWD:-}"
if [[ -z "${MYSQL_ROOT_PWD}" ]]; then
  read -rp "Enter MySQL root password (leave empty if using socket auth): " MYSQL_ROOT_PWD || true
fi

DB_USER_DEFAULT="${DB_USER:-heshmat}"
read -rp "Create DB user (non-root) [${DB_USER_DEFAULT}]: " _DB_USER || true
DB_USER="${_DB_USER:-${DB_USER_DEFAULT}}"

DB_PASSWORD="${DB_PASSWORD:-}"
if [[ -z "${DB_PASSWORD}" ]]; then
  read -srp "Password for DB user ${DB_USER}: " DB_PASSWORD
  echo
fi

echo "Updating apt cache..."
apt-get update -y

echo "Installing dependencies..."
apt-get install -y \
  curl ca-certificates git rsync python3 python3-venv python3-pip \
  mysql-server

echo "Ensuring MySQL is running..."
systemctl enable --now mysql

# Determine root authentication method and build a reusable mysql command
MYSQL_CMD_ROOT=(mysql -uroot)
if ! "${MYSQL_CMD_ROOT[@]}" -e "SELECT 1" >/dev/null 2>&1; then
  # If password provided, try password auth
  if [[ -n "${MYSQL_ROOT_PWD}" ]]; then
    MYSQL_CMD_ROOT=(mysql -uroot -p"${MYSQL_ROOT_PWD}")
    if ! "${MYSQL_CMD_ROOT[@]}" -e "SELECT 1" >/dev/null 2>&1; then
      echo "Cannot authenticate to MySQL as root with provided password." >&2
      exit 1
    fi
  else
    echo "Cannot authenticate to MySQL as root. Provide MYSQL_ROOT_PWD if socket auth is not enabled." >&2
    exit 1
  fi
fi

echo "Creating database and user..."
"${MYSQL_CMD_ROOT[@]}" <<SQL
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
SQL

echo "Deploying project to ${PROJECT_DIR}..."
mkdir -p "${PROJECT_DIR}"
# Copy from current directory to target (excluding VCS and virtualenv)
rsync -a --delete --exclude ".git" --exclude "venv" "$(pwd)/" "${PROJECT_DIR}/"
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

