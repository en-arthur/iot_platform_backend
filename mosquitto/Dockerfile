FROM eclipse-mosquitto:2.0

# Copy production config and entrypoint
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Create required directories
RUN mkdir -p /mosquitto/data /mosquitto/log /mosquitto/config

EXPOSE 1883 9001

ENTRYPOINT ["/entrypoint.sh"]
