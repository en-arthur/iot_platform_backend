#!/bin/sh
# Render entrypoint: generate passwd file from env vars, then start broker

set -e

PASSWD_FILE=/mosquitto/config/passwd

# Create password file from environment variables
# MQTT_ADMIN_USER and MQTT_ADMIN_PASSWORD must be set in Render dashboard
if [ -n "$MQTT_ADMIN_USER" ] && [ -n "$MQTT_ADMIN_PASSWORD" ]; then
    echo "Creating MQTT password file for user: $MQTT_ADMIN_USER"
    mosquitto_passwd -c -b "$PASSWD_FILE" "$MQTT_ADMIN_USER" "$MQTT_ADMIN_PASSWORD"
else
    echo "WARNING: MQTT_ADMIN_USER or MQTT_ADMIN_PASSWORD not set. Falling back to anonymous access."
    # Patch config to allow anonymous if no credentials set
    sed -i 's/allow_anonymous false/allow_anonymous true/' /mosquitto/config/mosquitto.conf
    sed -i '/password_file/d' /mosquitto/config/mosquitto.conf
fi

exec /usr/sbin/mosquitto -c /mosquitto/config/mosquitto.conf
