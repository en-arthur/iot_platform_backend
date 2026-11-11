#!/bin/sh
# Render entrypoint: generate passwd + acl files, then start broker

set -e

PASSWD_FILE=/mosquitto/config/passwd
ACL_FILE=/mosquitto/config/acl

mkdir -p /mosquitto/data /mosquitto/log /mosquitto/config

# ── Admin credentials (backend service) ─────────────────────────────────
if [ -z "$MQTT_ADMIN_USER" ] || [ -z "$MQTT_ADMIN_PASSWORD" ]; then
    echo "ERROR: MQTT_ADMIN_USER and MQTT_ADMIN_PASSWORD must be set."
    exit 1
fi

echo "Creating MQTT password file..."
mosquitto_passwd -c -b "$PASSWD_FILE" "$MQTT_ADMIN_USER" "$MQTT_ADMIN_PASSWORD"

# Make files readable by the mosquitto process (runs as mosquitto user uid=1883)
chmod 0640 "$PASSWD_FILE"
chown root:$(id -g mosquitto 2>/dev/null || echo 0) "$PASSWD_FILE" 2>/dev/null || chmod 0644 "$PASSWD_FILE"

# ── Admin ACL: full access to all topics ────────────────────────────────
cat > "$ACL_FILE" << EOF
# Admin user — full access (used by backend)
user ${MQTT_ADMIN_USER}
topic readwrite #

# Pattern ACL — devices restricted to their own topic namespace.
# A device authenticated as "device:<device_id>" can only:
#   publish  to: devices/<device_id>/telemetry
#   subscribe to: devices/<device_id>/cmd
pattern publish devices/%u/telemetry
pattern subscribe devices/%u/cmd
EOF

chmod 0644 "$ACL_FILE"

echo "MQTT ACL file created."
ls -la /mosquitto/config/

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
