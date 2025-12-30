FROM homeassistant/home-assistant:latest

# Install additional dependencies if needed
RUN apk add --no-cache \
    curl \
    jq \
    bash

# Copy custom configuration
# COPY configuration.yaml /config/configuration.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -f http://localhost:8123/api/ || exit 1

# Expose port
EXPOSE 8123
