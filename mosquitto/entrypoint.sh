#!/bin/sh
# Render entrypoint: generate config, passwd + acl files, then start broker

set -e

PASSWD_FILE=/mosquitto/config/passwd
ACL_FILE=/mosquitto/config/acl
CONF_FILE=/mosquitto/config/mosquitto.conf

# Render sets $PORT dynamically (default 10000). Use it for the WebSocket listener
# so Render's health check can reach the service.
RENDER_PORT=${PORT:-10000}

mkdir -p /mosquitto/data /mosquitto/log /mosquitto/config

# ── Admin credentials ────────────────────────────────────────────────────
if [ -z "$MQTT_ADMIN_USER" ] || [ -z "$MQTT_ADMIN_PASSWORD" ]; then
    echo "ERROR: MQTT_ADMIN_USER and MQTT_ADMIN_PASSWORD must be set."
    exit 1
fi

# ── Generate mosquitto.conf dynamically with correct $PORT ───────────────
cat > "$CONF_FILE" << EOF
# Global auth (applies to all listeners)
allow_anonymous false
password_file /mosquitto/config/passwd
acl_file /mosquitto/config/acl

# Standard MQTT listener
listener 1883

# WebSocket listener on Render's dynamic \$PORT (health check port)
listener ${RENDER_PORT}
protocol websockets

# Persistence
persistence true
persistence_location /mosquitto/data/

# Logging
log_dest stdout
log_type all
EOF

echo "Generated mosquitto.conf (WebSocket on port ${RENDER_PORT})."

# ── Create password file ─────────────────────────────────────────────────
echo "Creating MQTT password file..."
mosquitto_passwd -c -b "$PASSWD_FILE" "$MQTT_ADMIN_USER" "$MQTT_ADMIN_PASSWORD"

# ── Create ACL file ──────────────────────────────────────────────────────
# read = subscribe, write = publish (Mosquitto 2.0 keywords)
cat > "$ACL_FILE" << EOF
# Admin user — full readwrite access
user ${MQTT_ADMIN_USER}
topic readwrite #

# Pattern ACL — per-device topic isolation
pattern write devices/%u/telemetry
pattern read devices/%u/cmd
EOF

# Fix ownership & permissions for the mosquitto process
chown mosquitto:mosquitto "$PASSWD_FILE" "$ACL_FILE"
chmod 0700 "$PASSWD_FILE"
chmod 0700 "$ACL_FILE"

echo "MQTT ACL file created."

exec /usr/sbin/mosquitto -c "$CONF_FILE"
