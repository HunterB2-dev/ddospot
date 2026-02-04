#!/bin/bash
# DDoSPoT Local Restore Script
# Restores database and configurations from backup

set -e

PROJECT_DIR="/home/hunter/Projekty/ddospot"

# Verify parameters
if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 $PROJECT_DIR/backups/ddospot_backup_20260127_153045.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Verify backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "🔄 DDoSPoT Restore Started"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 Backup file: $BACKUP_FILE"
echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""
echo "📋 Backup contains:"
tar -tzf "$BACKUP_FILE" | sed 's/^/   /'
echo ""

# Confirmation prompt
echo "⚠️  WARNING: This will OVERWRITE current data!"
echo ""
read -p "Type 'RESTORE' to confirm (or Ctrl+C to cancel): " confirmation

if [ "$confirmation" != "RESTORE" ]; then
    echo "❌ Restore cancelled"
    exit 1
fi

# Stop dashboard if running
echo ""
echo "🛑 Stopping dashboard (if running)..."
pkill -f start-dashboard.py 2>/dev/null || true
pkill -f start-honeypot.py 2>/dev/null || true
sleep 2

# Backup current database before overwriting
echo "📦 Creating safety backup of current data..."
mkdir -p "$PROJECT_DIR/backups"
SAFETY_BACKUP="$PROJECT_DIR/backups/safety_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
tar -czf "$SAFETY_BACKUP" \
    -C "$PROJECT_DIR" \
    logs/honeypot.db 2>/dev/null || true
echo "✓ Safety backup saved: $SAFETY_BACKUP"

# Restore from backup
echo ""
echo "📂 Restoring files..."
tar -xzf "$BACKUP_FILE" -C "$PROJECT_DIR"
echo "✓ Restore complete"

# Show what was restored
echo ""
echo "✅ Restored items:"
echo "   ✓ Database (logs/honeypot.db)"
echo "   ✓ Configuration (config/config.json)"
echo "   ✓ Alert config (config/alert_config.json)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Restore Complete!"
echo ""
echo "🚀 To restart services, run:"
echo "   bash START_DASHBOARD.sh"
echo ""
