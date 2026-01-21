#!/bin/bash
# DDoSPoT Backup and Recovery Script
# Location: /opt/ddospot/backup.sh
# Schedule: 0 2 * * * /opt/ddospot/backup.sh (daily at 2 AM)
# Log: /var/log/ddospot/backup.log

set -e

# Configuration
BACKUP_DIR="/opt/ddospot/backups"
LOG_DIR="/var/log/ddospot"
LOG_FILE="$LOG_DIR/backup.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ddospot_backup_$TIMESTAMP.tar.gz"
RETENTION_DAYS=30
DB_PATH="/var/lib/ddospot/honeypot.db"
PROM_PATH="/var/lib/ddospot/prometheus"
ALERT_PATH="/var/lib/ddospot/alertmanager"
GRAFANA_PATH="/var/lib/ddospot/grafana"

# Create directories
mkdir -p "$BACKUP_DIR" "$LOG_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Error handler
error_exit() {
    log "ERROR: $*"
    exit 1
}

# Start backup
log "Starting DDoSPoT backup at $(date)"

# Check if database is accessible
if [ ! -f "$DB_PATH" ]; then
    error_exit "Database not found at $DB_PATH"
fi

# Create backup archive
log "Creating backup archive: $BACKUP_FILE"
{
    tar -czf "$BACKUP_FILE" \
        -C /var/lib/ddospot honeypot.db 2>/dev/null || log "Warning: Could not backup database"
    tar -czf "$BACKUP_FILE" \
        -C /var/lib/ddospot prometheus 2>/dev/null || log "Warning: Could not backup Prometheus data"
    tar -czf "$BACKUP_FILE" \
        -C /var/lib/ddospot alertmanager 2>/dev/null || log "Warning: Could not backup Alertmanager data"
    tar -czf "$BACKUP_FILE" \
        -C /var/lib/ddospot grafana 2>/dev/null || log "Warning: Could not backup Grafana data"
    tar -czf "$BACKUP_FILE" \
        /opt/ddospot/.env.prod 2>/dev/null || log "Warning: Could not backup .env.prod"
    tar -czf "$BACKUP_FILE" \
        /opt/ddospot/alert_config.json 2>/dev/null || log "Warning: Could not backup alert config"
} || {
    log "Error during archive creation, but continuing..."
}

# Verify backup file
if [ ! -f "$BACKUP_FILE" ]; then
    error_exit "Backup file was not created: $BACKUP_FILE"
fi

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
log "Backup completed successfully. Size: $BACKUP_SIZE"

# Clean old backups (keep last 30 days)
log "Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \;
OLD_BACKUPS=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f | wc -l)
log "Active backups in retention: $OLD_BACKUPS"

# Optional: Upload to remote storage
# Uncomment and configure if using cloud storage
if [ -n "$BACKUP_S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://$BACKUP_S3_BUCKET/" || log "Warning: S3 upload failed"
fi

if [ -n "$BACKUP_NAS_PATH" ] && [ -d "$BACKUP_NAS_PATH" ]; then
    log "Uploading backup to NAS..."
    cp "$BACKUP_FILE" "$BACKUP_NAS_PATH/" || log "Warning: NAS backup failed"
fi

# List recent backups
log "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -5

log "Backup completed successfully at $(date)"
log "=========================================="
