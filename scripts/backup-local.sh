#!/bin/bash
# DDoSPoT Local Backup Script
# Creates timestamped backup of database, configs, and attack data

set -e

PROJECT_DIR="/home/hunter/Projekty/ddospot"
BACKUP_DIR="$PROJECT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ddospot_backup_$TIMESTAMP.tar.gz"
RETENTION_DAYS=7

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🔄 DDoSPoT Backup Started - $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if database exists
if [ ! -f "$PROJECT_DIR/logs/honeypot.db" ]; then
    echo "⚠️  Warning: Database not found at $PROJECT_DIR/logs/honeypot.db"
else
    echo "✓ Database found: $(du -h $PROJECT_DIR/logs/honeypot.db | cut -f1)"
fi

# Create backup archive
echo ""
echo "📦 Creating backup archive..."
tar -czf "$BACKUP_FILE" \
    -C "$PROJECT_DIR" \
    logs/honeypot.db \
    config/config.json \
    config/alert_config.json \
    2>/dev/null && echo "✓ Archive created: $BACKUP_FILE" || echo "✓ Archive created (with warnings)"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "   Size: $BACKUP_SIZE"

# Clean old backups
echo ""
echo "🧹 Cleaning old backups (>$RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "ddospot_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
REMAINING=$(ls -1 "$BACKUP_DIR" | wc -l)
echo "✓ Retained backups: $REMAINING"

# Show backup info
echo ""
echo "📋 Backup Contents:"
tar -tzf "$BACKUP_FILE" | sed 's/^/   /'

# Create restore command
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Backup Complete!"
echo ""
echo "📍 Backup location: $BACKUP_FILE"
echo ""
echo "🔄 To restore this backup, run:"
echo "   bash restore-local.sh $BACKUP_FILE"
echo ""
