#!/bin/bash
# DDoSPoT Restore Script
# Usage: ./restore.sh <backup_file>
# Example: ./restore.sh /opt/ddospot/backups/ddospot_backup_20240115_020000.tar.gz

set -e

# Configuration
LOG_DIR="/var/log/ddospot"
LOG_FILE="$LOG_DIR/restore.log"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $*"
    exit 1
}

# Verify parameters
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 /opt/ddospot/backups/ddospot_backup_20240115_020000.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Backup file not found: $BACKUP_FILE"
fi

log "Starting DDoSPoT restore from: $BACKUP_FILE"
log "Backup file size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Confirmation prompt
echo ""
echo "⚠️  WARNING: This will OVERWRITE current data!"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Type 'RESTORE' to confirm: " confirmation

if [ "$confirmation" != "RESTORE" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# Stop services
log "Stopping services..."
sudo systemctl stop ddospot-dashboard.service 2>/dev/null || log "Dashboard not running"
sudo systemctl stop ddospot-honeypot.service 2>/dev/null || log "Honeypot not running"
sudo docker compose down 2>/dev/null || log "Docker containers not running"

# Create restore backup (safety measure)
SAFETY_BACKUP="/opt/ddospot/backups/pre_restore_backup_$(date +%s).tar.gz"
log "Creating safety backup at: $SAFETY_BACKUP"
if [ -d /var/lib/ddospot ]; then
    tar -czf "$SAFETY_BACKUP" /var/lib/ddospot 2>/dev/null || log "Warning: Could not create safety backup"
fi

# Restore data
log "Restoring from backup..."
tar -xzf "$BACKUP_FILE" -C / 2>/dev/null || {
    error_exit "Failed to extract backup. Attempting to restore from safety backup..."
    if [ -f "$SAFETY_BACKUP" ]; then
        log "Restoring safety backup..."
        tar -xzf "$SAFETY_BACKUP" -C / || error_exit "Safety backup restore failed"
    fi
}

# Fix permissions
log "Fixing permissions..."
sudo chown -R ddospot:ddospot /var/lib/ddospot 2>/dev/null || true
sudo chown -R ddospot:ddospot /opt/ddospot 2>/dev/null || true
sudo chmod 750 /var/lib/ddospot 2>/dev/null || true
sudo chmod 750 /opt/ddospot 2>/dev/null || true
sudo chmod 600 /opt/ddospot/.env.prod 2>/dev/null || true

# Restart services
log "Restarting services..."
sudo docker compose up -d 2>/dev/null || log "Docker services failed to start"
sudo systemctl start ddospot-honeypot.service 2>/dev/null || log "Honeypot failed to start"
sudo systemctl start ddospot-dashboard.service 2>/dev/null || log "Dashboard failed to start"

# Wait for services to stabilize
sleep 5

# Verify restoration
log "Verifying restoration..."
RESTORE_SUCCESS=true

# Check database
if [ -f /var/lib/ddospot/honeypot.db ]; then
    EVENT_COUNT=$(sqlite3 /var/lib/ddospot/honeypot.db "SELECT COUNT(*) FROM honeypot_events;" 2>/dev/null || echo "0")
    log "Database restored. Events: $EVENT_COUNT"
else
    log "WARNING: Database not found after restore"
    RESTORE_SUCCESS=false
fi

# Check service status
if sudo systemctl is-active --quiet ddospot-dashboard.service; then
    log "✓ Dashboard service running"
else
    log "✗ Dashboard service not running"
    RESTORE_SUCCESS=false
fi

if sudo systemctl is-active --quiet ddospot-honeypot.service; then
    log "✓ Honeypot service running"
else
    log "✗ Honeypot service not running"
    RESTORE_SUCCESS=false
fi

# Final status
echo ""
if [ "$RESTORE_SUCCESS" = true ]; then
    log "=========================================="
    log "Restore completed successfully!"
    log "Services are running and data has been restored."
    log "=========================================="
    exit 0
else
    log "=========================================="
    log "Restore completed with warnings. Check services manually."
    log "Safety backup available at: $SAFETY_BACKUP"
    log "=========================================="
    exit 1
fi
