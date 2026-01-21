#!/bin/bash
# DDoSPoT Production Deployment Setup Script
# Usage: sudo ./setup-production.sh

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DDOSPOT_USER="ddospot"
DDOSPOT_HOME="/opt/ddospot"
DDOSPOT_DATA="/var/lib/ddospot"
BACKUP_DIR="${DDOSPOT_HOME}/backups"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run as root"
    fi
}

check_requirements() {
    log_info "Checking system requirements..."

    # Check OS
    if ! grep -qi ubuntu /etc/os-release && ! grep -qi rocky /etc/os-release; then
        log_warn "This script is optimized for Ubuntu/Rocky Linux"
    fi

    # Check required commands
    local required_tools=("docker" "docker-compose" "nginx" "git" "python3" "pip3")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
        fi
    done

    log_info "✓ All requirements met"
}

create_user() {
    log_info "Creating system user..."

    if id "$DDOSPOT_USER" &>/dev/null; then
        log_warn "User $DDOSPOT_USER already exists"
    else
        sudo useradd -m -d "$DDOSPOT_HOME" -s /bin/bash "$DDOSPOT_USER"
        log_info "✓ User $DDOSPOT_USER created"
    fi
}

setup_directories() {
    log_info "Setting up directory structure..."

    mkdir -p "$DDOSPOT_DATA"/{prometheus,grafana,alertmanager}
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$DDOSPOT_HOME"/{logs,config,scripts}

    chown -R "$DDOSPOT_USER:$DDOSPOT_USER" "$DDOSPOT_HOME" "$DDOSPOT_DATA"
    chmod 750 "$DDOSPOT_HOME" "$DDOSPOT_DATA"

    log_info "✓ Directory structure created"
}

setup_environment() {
    log_info "Setting up environment configuration..."

    if [ ! -f "$DDOSPOT_HOME/.env.prod" ]; then
        if [ -f "$DDOSPOT_HOME/.env.prod.template" ]; then
            cp "$DDOSPOT_HOME/.env.prod.template" "$DDOSPOT_HOME/.env.prod"
            chown "$DDOSPOT_USER:$DDOSPOT_USER" "$DDOSPOT_HOME/.env.prod"
            chmod 600 "$DDOSPOT_HOME/.env.prod"
            log_warn "Created .env.prod from template. Please configure it!"
        else
            log_error ".env.prod.template not found"
        fi
    fi

    # Generate API token if not present
    if grep -q "DDOSPOT_API_TOKEN=$" "$DDOSPOT_HOME/.env.prod"; then
        TOKEN=$(openssl rand -hex 32)
        sed -i "s/DDOSPOT_API_TOKEN=.*/DDOSPOT_API_TOKEN=$TOKEN/" "$DDOSPOT_HOME/.env.prod"
        log_info "✓ Generated API token"
    fi

    log_info "✓ Environment configured"
}

setup_scripts() {
    log_info "Setting up helper scripts..."

    # Make scripts executable
    chmod +x "$DDOSPOT_HOME"/backup.sh "$DDOSPOT_HOME"/restore.sh 2>/dev/null || true

    # Copy scripts to bin
    mkdir -p "$DDOSPOT_HOME/scripts"
    chmod +x "$DDOSPOT_HOME/scripts"/*.sh 2>/dev/null || true

    log_info "✓ Scripts configured"
}

setup_docker() {
    log_info "Setting up Docker..."

    # Enable Docker service
    systemctl enable docker
    systemctl start docker

    # Create Docker Compose override for production
    cat > "$DDOSPOT_HOME/docker-compose.override.yml" << 'EOF'
version: '3.8'

services:
  ddospot-dashboard:
    volumes:
      - /var/lib/ddospot:/data
    environment:
      - PYTHONUNBUFFERED=1

  prometheus:
    volumes:
      - /var/lib/ddospot/prometheus:/prometheus

  grafana:
    volumes:
      - /var/lib/ddospot/grafana:/var/lib/grafana

  alertmanager:
    volumes:
      - /var/lib/ddospot/alertmanager:/alertmanager
EOF

    chown "$DDOSPOT_USER:$DDOSPOT_USER" "$DDOSPOT_HOME/docker-compose.override.yml"

    log_info "✓ Docker configured"
}

setup_nginx() {
    log_info "Setting up Nginx..."

    # Create Nginx config directory
    mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled

    # Copy configuration if exists
    if [ -f "$DDOSPOT_HOME/nginx/ddospot.conf" ]; then
        cp "$DDOSPOT_HOME/nginx/ddospot.conf" /etc/nginx/sites-available/ddospot
        ln -sf /etc/nginx/sites-available/ddospot /etc/nginx/sites-enabled/ddospot
    fi

    # Test configuration
    if ! nginx -t &>/dev/null; then
        log_warn "Nginx configuration test failed. Please review /etc/nginx/sites-available/ddospot"
    fi

    systemctl enable nginx
    systemctl reload nginx

    log_info "✓ Nginx configured"
}

setup_systemd() {
    log_info "Setting up Systemd services..."

    if [ -f "$DDOSPOT_HOME/systemd/ddospot-honeypot.service" ]; then
        cp "$DDOSPOT_HOME/systemd/ddospot-honeypot.service" /etc/systemd/system/
        log_info "✓ Honeypot service installed"
    fi

    if [ -f "$DDOSPOT_HOME/systemd/ddospot-dashboard.service" ]; then
        cp "$DDOSPOT_HOME/systemd/ddospot-dashboard.service" /etc/systemd/system/
        log_info "✓ Dashboard service installed"
    fi

    systemctl daemon-reload
    systemctl enable ddospot-honeypot.service
    systemctl enable ddospot-dashboard.service

    log_info "✓ Systemd services configured"
}

setup_backup_cron() {
    log_info "Setting up automated backups..."

    # Create cron job
    CRON_CMD="0 2 * * * $DDOSPOT_HOME/backup.sh"
    
    # Check if cron job exists
    if sudo -u "$DDOSPOT_USER" crontab -l 2>/dev/null | grep -q backup.sh; then
        log_warn "Backup cron job already exists"
    else
        (sudo -u "$DDOSPOT_USER" crontab -l 2>/dev/null; echo "$CRON_CMD") | \
            sudo -u "$DDOSPOT_USER" crontab -
        log_info "✓ Backup cron job scheduled (daily at 2 AM)"
    fi
}

setup_firewall() {
    log_info "Configuring firewall..."

    # Check if UFW is available
    if command -v ufw &> /dev/null; then
        ufw default deny incoming 2>/dev/null || true
        ufw default allow outgoing 2>/dev/null || true
        ufw allow 22/tcp 2>/dev/null || true
        ufw allow 80/tcp 2>/dev/null || true
        ufw allow 443/tcp 2>/dev/null || true
        ufw enable 2>/dev/null || true
        log_info "✓ Firewall configured"
    else
        log_warn "UFW not available, configure firewall manually"
    fi
}

start_services() {
    log_info "Starting services..."

    cd "$DDOSPOT_HOME"

    # Build and start Docker containers
    docker-compose build
    docker-compose up -d

    # Start systemd services
    systemctl start ddospot-honeypot.service
    systemctl start ddospot-dashboard.service

    sleep 3

    log_info "✓ Services started"
}

verify_deployment() {
    log_info "Verifying deployment..."

    # Check Docker services
    if ! docker-compose ps | grep -q "Up"; then
        log_warn "Some Docker services not running"
    fi

    # Check systemd services
    if systemctl is-active --quiet ddospot-dashboard.service; then
        log_info "✓ Dashboard service running"
    else
        log_warn "Dashboard service not running"
    fi

    # Test connectivity
    if curl -f http://127.0.0.1:5000/health &>/dev/null; then
        log_info "✓ Dashboard API responding"
    else
        log_warn "Dashboard API not responding"
    fi

    log_info "✓ Deployment verification complete"
}

cleanup_interactive() {
    log_info "Cleaning up..."

    # Remove this script's execution permissions
    chmod -x "$0" 2>/dev/null || true
}

# Main execution
main() {
    clear
    echo "╔════════════════════════════════════════════╗"
    echo "║  DDoSPoT Production Deployment Setup       ║"
    echo "║  Version 1.0                               ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""

    check_root
    check_requirements
    create_user
    setup_directories
    setup_environment
    setup_scripts
    setup_docker
    setup_nginx
    setup_systemd
    setup_backup_cron
    setup_firewall
    start_services
    verify_deployment
    cleanup_interactive

    echo ""
    echo "╔════════════════════════════════════════════╗"
    echo "║  Deployment Completed Successfully!        ║"
    echo "╚════════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "1. Configure .env.prod with your settings"
    echo "2. Setup SSL certificate (certbot)"
    echo "3. Update Nginx configuration for your domain"
    echo "4. Verify services are running"
    echo "5. Check monitoring dashboards"
    echo ""
    echo "For more information, see: $DDOSPOT_HOME/DEPLOYMENT_GUIDE.md"
    echo ""
}

# Run main
main "$@"
