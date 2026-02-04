#!/bin/bash

# Cron Job Setup & Testing Utility
# Interactive tool to configure and test scheduled maintenance

set -e

API_URL="${API_URL:-http://127.0.0.1:5000}"
PROJECT_DIR="/home/hunter/Projekty/ddospot"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log_info() { echo -e "${BLUE}[INFO]${NC} $@"; }
log_success() { echo -e "${GREEN}[✓]${NC} $@"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $@"; }
log_error() { echo -e "${RED}[✗]${NC} $@"; }

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     DDoSPot Cron Jobs Setup & Maintenance Manager${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

# Check prerequisites
log_info "Checking prerequisites..."
cd "$PROJECT_DIR" || exit 1

# Python 3
if ! command -v python3 &> /dev/null; then
    log_error "Python3 not found"
    exit 1
fi
python_path=$(which python3)
log_success "Python3 found: $python_path"

# Cron service
if ! command -v crontab &> /dev/null; then
    log_error "Crontab not found. Install with: sudo apt install cron"
    exit 1
fi
log_success "Crontab available"

echo

# Main menu
show_menu() {
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Cron Management Options:${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo "  1. Install cron jobs (automatic)"
    echo "  2. View installed cron jobs"
    echo "  3. Test log rotation"
    echo "  4. Test database cleanup"
    echo "  5. Test full maintenance"
    echo "  6. Schedule daily backups"
    echo "  7. Setup backup retention"
    echo "  8. Add health check job"
    echo "  9. View maintenance logs"
    echo "  10. Edit crontab manually"
    echo "  11. Remove all DDoSPot cron jobs"
    echo "  0. Exit"
    echo
}

# Test maintenance tasks
test_log_rotation() {
    log_info "Testing log rotation..."
    
    if $python_path app/maintenance.py rotate; then
        log_success "Log rotation test passed"
    else
        log_error "Log rotation test failed"
        return 1
    fi
    echo
}

test_database_cleanup() {
    log_info "Testing database cleanup (30 days)..."
    
    # Show before state
    log_info "Database before cleanup:"
    $python_path -c "
from core.database import HoneypotDatabase
db = HoneypotDatabase('logs/honeypot.db')
info = db.get_database_size()
print(f'  Events: {info[\"event_count\"]}')
print(f'  Size: {info[\"size_mb\"]:.2f} MB')
"
    echo
    
    # Run cleanup
    if $python_path app/maintenance.py cleanup --days 30; then
        log_success "Database cleanup test passed"
        
        # Show after state
        log_info "Database after cleanup:"
        $python_path -c "
from core.database import HoneypotDatabase
db = HoneypotDatabase('logs/honeypot.db')
info = db.get_database_size()
print(f'  Events: {info[\"event_count\"]}')
print(f'  Size: {info[\"size_mb\"]:.2f} MB')
"
    else
        log_error "Database cleanup test failed"
        return 1
    fi
    echo
}

test_full_maintenance() {
    log_info "Testing full maintenance..."
    
    if $python_path app/maintenance.py full --days 30; then
        log_success "Full maintenance test passed"
    else
        log_error "Full maintenance test failed"
        return 1
    fi
    echo
}

# Install cron jobs
install_cron_jobs() {
    log_info "Installing cron jobs..."
    
    if bash scripts/install-cron.sh; then
        log_success "Cron jobs installed"
        echo
        log_info "Installed jobs:"
        crontab -l 2>/dev/null | grep -E "DDoSPoT|maintenance" || log_warning "No cron jobs found"
    else
        log_error "Failed to install cron jobs"
        return 1
    fi
    echo
}

# View cron jobs
view_cron_jobs() {
    log_info "Installed cron jobs:"
    echo
    if crontab -l 2>/dev/null | grep -q "maintenance"; then
        crontab -l | grep -E "DDoSPoT|maintenance" | sed 's/^/  /'
    else
        log_warning "No DDoSPot cron jobs found"
    fi
    echo
}

# Schedule daily backups
schedule_daily_backups() {
    log_info "Setting up daily backups..."
    echo
    
    # Get current crontab
    CRONTAB_BACKUP="/tmp/crontab-$(date +%s)"
    crontab -l > "$CRONTAB_BACKUP" 2>/dev/null || true
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "backup-local.sh"; then
        log_warning "Daily backup already scheduled"
        echo
        return 0
    fi
    
    # Add daily backup at 2 AM
    {
        crontab -l 2>/dev/null || true
        echo ""
        echo "# DDoSPot Daily Backups"
        echo "0 2 * * * bash $PROJECT_DIR/backup-local.sh >> /var/log/ddospot-backup.log 2>&1"
    } | crontab -
    
    log_success "Daily backups scheduled at 2:00 AM"
    echo
}

# Setup backup retention
setup_backup_retention() {
    log_info "Setting up backup retention policy..."
    echo
    
    read -p "Days to keep backups [30]: " days
    days=${days:-30}
    
    # Get current crontab
    CRONTAB_BACKUP="/tmp/crontab-$(date +%s)"
    crontab -l > "$CRONTAB_BACKUP" 2>/dev/null || true
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "find.*backup"; then
        log_warning "Backup cleanup already scheduled"
        echo
        return 0
    fi
    
    # Add backup cleanup job
    {
        crontab -l 2>/dev/null || true
        echo ""
        echo "# DDoSPot Backup Retention (keep $days days)"
        echo "30 2 * * * find $PROJECT_DIR/backups -name '*.tar.gz' -mtime +$days -delete"
    } | crontab -
    
    log_success "Backup retention set to $days days"
    echo "  Old backups will be deleted at 2:30 AM daily"
    echo
}

# Add health check job
add_health_check() {
    log_info "Setting up health check job..."
    echo
    
    # Check if already exists
    if crontab -l 2>/dev/null | grep -q "health"; then
        log_warning "Health check already scheduled"
        echo
        return 0
    fi
    
    # Add health check job (hourly)
    {
        crontab -l 2>/dev/null || true
        echo ""
        echo "# DDoSPot Health Check"
        echo "0 * * * * curl -s http://127.0.0.1:5000/health >> /var/log/ddospot-health.log 2>&1"
    } | crontab -
    
    log_success "Health check scheduled hourly"
    echo
}

# View maintenance logs
view_maintenance_logs() {
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Maintenance Logs:${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    
    if [ -f "/var/log/ddospot-maintenance.log" ]; then
        log_info "Last 20 lines from /var/log/ddospot-maintenance.log:"
        tail -20 /var/log/ddospot-maintenance.log | sed 's/^/  /'
    else
        log_warning "No maintenance log found yet"
    fi
    
    echo
}

# Edit crontab
edit_crontab() {
    log_info "Opening crontab editor..."
    crontab -e
    echo
    log_info "Updated cron jobs:"
    crontab -l | head -20 | sed 's/^/  /'
    echo
}

# Remove cron jobs
remove_cron_jobs() {
    log_warning "This will remove all DDoSPot cron jobs"
    read -p "Are you sure? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        echo
        return 0
    fi
    
    # Backup current crontab
    BACKUP="/tmp/crontab-backup-$(date +%s)"
    crontab -l > "$BACKUP"
    log_success "Crontab backed up to: $BACKUP"
    
    # Remove DDoSPot jobs
    if bash scripts/uninstall-cron.sh; then
        log_success "Cron jobs removed"
    else
        log_error "Failed to remove cron jobs"
    fi
    echo
}

# Main loop
while true; do
    show_menu
    read -p "Select option: " choice
    echo
    
    case $choice in
        1) install_cron_jobs ;;
        2) view_cron_jobs ;;
        3) test_log_rotation ;;
        4) test_database_cleanup ;;
        5) test_full_maintenance ;;
        6) schedule_daily_backups ;;
        7) setup_backup_retention ;;
        8) add_health_check ;;
        9) view_maintenance_logs ;;
        10) edit_crontab ;;
        11) remove_cron_jobs ;;
        0)
            log_success "Goodbye!"
            exit 0
            ;;
        *)
            log_error "Invalid option"
            echo
            ;;
    esac
done
