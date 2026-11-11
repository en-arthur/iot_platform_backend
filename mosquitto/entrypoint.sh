#!/bin/sh
# Render entrypoint: generate passwd + acl files, then start broker

set -e

PASSWD_FILE=/mosquitto/config/passwd
ACL_FILE=/mosquitto/config/acl

mkdir -p /mosquitto/data /mosquitto/log /mosquitto/config

# ── Admin credentials ────────────────────────────────────────────────────
if [ -z "$MQTT_ADMIN_USER" ] || [ -z "$MQTT_ADMIN_PASSWORD" ]; then
    echo "ERROR: MQTT_ADMIN_USER and MQTT_ADMIN_PASSWORD must be set."
    exit 1
fi

echo "Creating MQTT password file..."
mosquitto_passwd -c -b "$PASSWD_FILE" "$MQTT_ADMIN_USER" "$MQTT_ADMIN_PASSWORD"

# ── Admin ACL: full access to all topics ─────────────────────────────────
# Mosquitto ACL keywords: read (subscribe), write (publish), readwrite (both)
cat > "$ACL_FILE" << EOF
# Admin user — full readwrite access
user ${MQTT_ADMIN_USER}
topic readwrite #

# Pattern ACL — applied to ALL authenticated users dynamically.
# A device authenticated as "device:<device_id>" (%u = "device:<device_id>") can only:
#   write (publish)  → devices/<device_id>/telemetry
#   read (subscribe) → devices/<device_id>/cmd
pattern write devices/%u/telemetry
pattern read devices/%u/cmd
EOF

# ── Fix ownership & permissions so mosquitto process can read them ───────
chown mosquitto:mosquitto "$PASSWD_FILE" "$ACL_FILE"
chmod 0700 "$PASSWD_FILE"
chmod 0700 "$ACL_FILE"

echo "MQTT ACL file created."
ls -la /mosquitto/config/

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
