#!/bin/sh

# Chờ Kong sẵn sàng
until curl -s http://kong:8001/status; do
  echo "🕒 Waiting for Kong to be ready..."
  sleep 5
done

# Tạo service
curl -i -X POST http://kong:8001/services \
  --data "name=auth-service" \
  --data "url=http://auth-service:8002"

# Tạo route
curl -i -X POST http://kong:8001/routes \
  --data "service.name=auth-service" \
  --data "paths[]=/auth"

echo "Auth service route created!"
