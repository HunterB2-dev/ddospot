#!/bin/bash
# DDoSPoT Cron Uninstaller
# Removes DDoSPoT maintenance cron jobs

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      DDoSPoT Scheduled Maintenance Removal                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if DDoSPoT cron jobs exist
if ! crontab -l 2>/dev/null | grep -q "DDoSPoT Automated Maintenance"; then
    echo "No DDoSPoT cron jobs found."
    exit 0
fi

echo "Found DDoSPoT maintenance cron jobs:"
echo ""
crontab -l 2>/dev/null | grep -A 3 "DDoSPoT Automated Maintenance"
echo ""

read -p "Remove these cron jobs? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Removal cancelled."
    exit 0
fi

# Backup current crontab
BACKUP_FILE="/tmp/ddospot-crontab-backup-$(date +%s)"
crontab -l > "$BACKUP_FILE" 2>/dev/null
echo "✓ Current crontab backed up to: $BACKUP_FILE"

# Remove DDoSPoT entries
crontab -l 2>/dev/null | grep -v "DDoSPoT Automated Maintenance" | grep -v "maintenance.py" | crontab -

echo "✓ DDoSPoT cron jobs removed successfully!"
echo ""
echo "To restore backup:  crontab $BACKUP_FILE"
