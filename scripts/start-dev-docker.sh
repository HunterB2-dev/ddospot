#!/bin/bash
# DDoSPot Development Startup Script

set -e

COMPOSE_FILE="docker-compose-dev.yml"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DDoSPot Development Environment${NC}"
echo -e "${BLUE}========================================${NC}"

# Create logs directory
mkdir -p logs

# Build images
echo -e "${GREEN}[INFO]${NC} Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build

# Start services
echo -e "${GREEN}[INFO]${NC} Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services
sleep 5

# Display status
echo ""
echo -e "${GREEN}[INFO]${NC} Services started!"
echo ""
echo "Access points:"
echo "  Dashboard:  http://localhost:5000"
echo "  Honeypot SSH: localhost:2222"
echo "  Honeypot HTTP: localhost:8080"
echo ""
echo "Commands:"
echo "  View logs:     docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE down"
echo "  Rebuild:       docker-compose -f $COMPOSE_FILE build --no-cache"
echo ""
