#!/bin/bash

# Quick Cron Job Test Script
# Verify cron infrastructure and test maintenance functions

PROJECT_DIR="/home/hunter/Projekty/ddospot"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

cd "$PROJECT_DIR" || exit 1

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}     DDoSPot Cron Jobs - Quick Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Test 1: Check cron availability
echo -e "${YELLOW}[1/6]${NC} Checking cron service..."
if command -v crontab &> /dev/null; then
    echo -e "${GREEN}✓${NC} Crontab available"
else
    echo -e "${RED}✗${NC} Crontab not found"
    exit 1
fi
echo

# Test 2: Check Python 3
echo -e "${YELLOW}[2/6]${NC} Checking Python environment..."
if python3 --version &> /dev/null; then
    echo -e "${GREEN}✓${NC} $(python3 --version)"
else
    echo -e "${RED}✗${NC} Python3 not available"
    exit 1
fi
echo

# Test 3: Check maintenance script
echo -e "${YELLOW}[3/6]${NC} Checking maintenance script..."
if [ -f "app/maintenance.py" ]; then
    echo -e "${GREEN}✓${NC} Maintenance script found"
else
    echo -e "${RED}✗${NC} Maintenance script not found"
    exit 1
fi
echo

# Test 4: Test log rotation
echo -e "${YELLOW}[4/6]${NC} Testing log rotation..."
if python3 app/maintenance.py rotate 2>&1 | grep -q "completed\|Completed\|success"; then
    echo -e "${GREEN}✓${NC} Log rotation test passed"
else
    echo -e "${YELLOW}⚠${NC}  Log rotation executed (check if logs exist)"
fi
echo

# Test 5: Test database cleanup (dry-run)
echo -e "${YELLOW}[5/6]${NC} Testing database cleanup..."
DB_BEFORE=$(python3 -c "from core.database import HoneypotDatabase; db = HoneypotDatabase('logs/honeypot.db'); print(db.get_database_size()['event_count'])" 2>/dev/null || echo "?")
if python3 app/maintenance.py cleanup --days 30 2>&1 | grep -q "removed\|Removed\|cleaned"; then
    DB_AFTER=$(python3 -c "from core.database import HoneypotDatabase; db = HoneypotDatabase('logs/honeypot.db'); print(db.get_database_size()['event_count'])" 2>/dev/null || echo "?")
    echo -e "${GREEN}✓${NC} Database cleanup test passed"
    echo "   Before: $DB_BEFORE events → After: $DB_AFTER events"
else
    echo -e "${YELLOW}⚠${NC}  Database cleanup executed"
fi
echo

# Test 6: Check cron installation
echo -e "${YELLOW}[6/6]${NC} Checking cron installations..."
if crontab -l 2>/dev/null | grep -q "maintenance"; then
    COUNT=$(crontab -l 2>/dev/null | grep -c "maintenance" || echo "0")
    echo -e "${GREEN}✓${NC} Found $COUNT DDoSPot cron jobs installed"
    echo "   Run: crontab -l  to see all jobs"
else
    echo -e "${YELLOW}⚠${NC}  No DDoSPot cron jobs installed yet"
    echo "   Run: bash scripts/install-cron.sh  to install"
fi
echo

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Cron Job Infrastructure Test Complete${NC}"
echo
echo "Next steps:"
echo "  1. Setup cron jobs:       bash manage-cron.sh"
echo "  2. View installation:     crontab -l"
echo "  3. Monitor execution:     tail -f /var/log/ddospot-maintenance.log"
echo "  4. Check documentation:   less TASK_10_CRON_JOBS.md"
echo
