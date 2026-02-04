#!/bin/bash

# Quick Alert Testing Script
# Tests all alert functionality with minimal setup

API_URL="${API_URL:-http://127.0.0.1:5000}"
TOKEN_FILE=".api_token"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}     DDoSPot Alert System - Quick Test${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Check dashboard
echo -e "${YELLOW}[1/5]${NC} Checking dashboard..."
if curl -s "$API_URL/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Dashboard running at $API_URL"
else
    echo -e "${RED}✗${NC} Dashboard not accessible at $API_URL"
    exit 1
fi
echo

# Get API token
echo -e "${YELLOW}[2/5]${NC} Loading API token..."
if [ ! -f "$TOKEN_FILE" ]; then
    echo -e "${RED}✗${NC} Token file (.api_token) not found"
    exit 1
fi
TOKEN=$(cat "$TOKEN_FILE" | tr -d '\n')
echo -e "${GREEN}✓${NC} Token loaded"
echo

# Get current configuration
echo -e "${YELLOW}[3/5]${NC} Current Alert Configuration:"
CONFIG=$(curl -s "$API_URL/api/alerts/config")
echo "$CONFIG" | jq '.' | sed 's/^/   /'
echo

# Get alert history
echo -e "${YELLOW}[4/5]${NC} Alert History (last 5 alerts):"
HISTORY=$(curl -s "$API_URL/api/alerts/history")
COUNT=$(echo "$HISTORY" | jq 'length')
echo "   Total alerts: $COUNT"
if [ "$COUNT" -gt 0 ]; then
    echo "$HISTORY" | jq -r '.[:5] | .[] | "   • \(.timestamp) - \(.type)"' 
fi
echo

# Send test alert
echo -e "${YELLOW}[5/5]${NC} Sending test alert..."
TEST_RESULT=$(curl -s -X POST "$API_URL/api/alerts/test" \
    -H "X-API-Token: $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "type": "test",
        "message": "✓ Test alert from DDoSPot"
    }')

if echo "$TEST_RESULT" | jq . > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Test alert sent successfully"
    echo "   Check email/Discord for notification"
else
    echo -e "${RED}✗${NC} Failed to send test alert"
    echo "$TEST_RESULT"
fi
echo

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Alert System Test Complete${NC}"
echo
echo "Next steps:"
echo "  1. Setup email: ./setup-alerts.sh → Option 1"
echo "  2. Setup Discord: ./setup-alerts.sh → Option 2"
echo "  3. View dashboard: http://$API_URL:5000"
echo "  4. Monitor alerts: ./monitor-alerts.sh (if available)"
echo
