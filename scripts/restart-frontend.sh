#!/bin/bash

# Quick frontend restart — no image rebuild needed.
# Python source is bind-mounted, so code changes only need a container restart.

set -e

COMPOSE_FILE="docker-compose.dev.yml"

if docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "❌ Docker Compose not found."
    exit 1
fi

echo "🔄 Restarting Reflex frontend..."
$COMPOSE_CMD -f $COMPOSE_FILE restart reflex

echo "📋 Watching logs (Ctrl+C to stop)..."
$COMPOSE_CMD -f $COMPOSE_FILE logs -f reflex
