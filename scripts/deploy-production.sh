#!/bin/bash
# DDoSPot Production Deployment Script

set -e

PROJECT_NAME="ddospot"
REGISTRY="${REGISTRY:-localhost:5000}"
COMPOSE_FILE="docker-compose-prod.yml"
LOG_DIR="./logs"
BACKUP_DIR="./backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DDoSPot Production Deployment${NC}"
echo -e "${BLUE}========================================${NC}"

# Function to print colored output
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

log_info "Docker version: $(docker --version)"

# Create necessary directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR"
log_info "Created log and backup directories"

# Backup existing database if it exists
if [ -f "honeypot.db" ]; then
    BACKUP_FILE="$BACKUP_DIR/honeypot_$(date +%Y%m%d_%H%M%S).db.bak"
    cp honeypot.db "$BACKUP_FILE"
    log_info "Database backed up to $BACKUP_FILE"
fi

# Build images
log_info "Building Docker images..."
docker-compose -f "$COMPOSE_FILE" build

# Pull external images
log_info "Pulling external service images..."
docker-compose -f "$COMPOSE_FILE" pull

# Start services
log_info "Starting services..."
docker-compose -f "$COMPOSE_FILE" up -d

# Wait for services to be ready
log_info "Waiting for services to become healthy..."
sleep 10

# Check service status
log_info "Checking service status..."
docker-compose -f "$COMPOSE_FILE" ps

# Display endpoints
echo ""
log_info "=========================================="
log_info "Deployment Complete!"
log_info "=========================================="
echo -e "${GREEN}"
echo "Services are now running at:"
echo "  Dashboard:       http://localhost:5000"
echo "  Prometheus:      http://localhost:9090"
echo "  Grafana:         http://localhost:3000 (admin/admin)"
echo "  AlertManager:    http://localhost:9093"
echo ""
echo "Useful Commands:"
echo "  View logs:       docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services:   docker-compose -f $COMPOSE_FILE down"
echo "  Restart service: docker-compose -f $COMPOSE_FILE restart <service>"
echo -e "${NC}"

# Log display
log_info "View logs with: docker-compose -f $COMPOSE_FILE logs -f"
