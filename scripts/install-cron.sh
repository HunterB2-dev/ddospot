#!/bin/bash
# DDoSPoT Cron Helper
# Generates and installs crontab entries for automated maintenance

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
MAINTENANCE_SCRIPT="$SCRIPT_DIR/maintenance.py"
PYTHON_BIN="$(which python3)"

# Ensure maintenance script is executable
chmod +x "$MAINTENANCE_SCRIPT"

cat << 'EOF'
╔═══════════════════════════════════════════════════════════╗
║         DDoSPoT Scheduled Maintenance Setup               ║
╚═══════════════════════════════════════════════════════════╝

This will install automated maintenance tasks via cron:

  • Log Rotation:    Daily at 3:00 AM
  • Database Cleanup: Weekly on Sunday at 4:00 AM (30 day retention)
  • Full Maintenance: Monthly on 1st at 5:00 AM

EOF

# Show example crontab entries
cat << EOF
Suggested crontab entries:

# DDoSPoT Automated Maintenance
# Rotate logs daily at 3 AM
0 3 * * * $PYTHON_BIN $MAINTENANCE_SCRIPT rotate --quiet >> /var/log/ddospot-maintenance.log 2>&1

# Cleanup old events weekly (Sunday 4 AM, keep 30 days)
0 4 * * 0 $PYTHON_BIN $MAINTENANCE_SCRIPT cleanup --days 30 --quiet >> /var/log/ddospot-maintenance.log 2>&1

# Full maintenance monthly (1st day, 5 AM)
0 5 1 * * $PYTHON_BIN $MAINTENANCE_SCRIPT full --days 30 --quiet >> /var/log/ddospot-maintenance.log 2>&1

EOF

read -p "Install these cron jobs now? [y/N]: " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled. You can manually add the entries above to your crontab."
    exit 0
fi

# Backup existing crontab
BACKUP_FILE="/tmp/ddospot-crontab-backup-$(date +%s)"
crontab -l > "$BACKUP_FILE" 2>/dev/null || true
echo "✓ Existing crontab backed up to: $BACKUP_FILE"

# Generate new crontab
{
    crontab -l 2>/dev/null || true
    echo ""
    echo "# DDoSPoT Automated Maintenance"
    echo "0 3 * * * $PYTHON_BIN $MAINTENANCE_SCRIPT rotate --quiet >> /var/log/ddospot-maintenance.log 2>&1"
    echo "0 4 * * 0 $PYTHON_BIN $MAINTENANCE_SCRIPT cleanup --days 30 --quiet >> /var/log/ddospot-maintenance.log 2>&1"
    echo "0 5 1 * * $PYTHON_BIN $MAINTENANCE_SCRIPT full --days 30 --quiet >> /var/log/ddospot-maintenance.log 2>&1"
} | crontab -

echo "✓ Cron jobs installed successfully!"
echo ""
echo "To view installed jobs:    crontab -l"
echo "To edit cron jobs:         crontab -e"
echo "To remove DDoSPoT jobs:    Run: ./uninstall-cron.sh"
echo ""
echo "Maintenance logs will be written to: /var/log/ddospot-maintenance.log"
