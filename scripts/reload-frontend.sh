#!/bin/bash
# Quick frontend reload — clears .web cache and restarts reflex with current source.
# No full image rebuild needed. Takes ~1-2 minutes.

set -e

COMPOSE_FILE="docker-compose.dev.yml"

if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "Docker Compose not found."
    exit 1
fi

echo "Stopping reflex..."
$COMPOSE_CMD -f $COMPOSE_FILE rm -f reflex

echo "Clearing .web cache..."
docker volume rm benchhubplus_reflex_dev_web 2>/dev/null || true

echo "Starting reflex (recompiling from source)..."
$COMPOSE_CMD -f $COMPOSE_FILE up -d reflex

echo "Waiting for app to be ready..."
for i in $(seq 1 24); do
    if curl -sf http://localhost:3000 > /dev/null 2>&1; then
        echo "Ready! Open http://localhost:3000"
        exit 0
    fi
    echo "  [$i/24] Still starting..."
    sleep 5
done

echo "Timeout — check logs: $COMPOSE_CMD -f $COMPOSE_FILE logs -f reflex"
