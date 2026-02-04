#!/bin/bash

# Alert Configuration Script for DDoSPot
# Interactive setup for Email and Discord alerts

set -e

API_URL="${API_URL:-http://127.0.0.1:5000}"
TOKEN_FILE=".api_token"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     DDoSPot Alert Configuration Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo

# Check if dashboard is running
echo -e "${YELLOW}1. Checking dashboard...${NC}"
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}✗ Dashboard not accessible at $API_URL${NC}"
    echo "  Start dashboard with: python start-dashboard.py"
    exit 1
fi
echo -e "${GREEN}✓ Dashboard is running${NC}"
echo

# Check for API token
echo -e "${YELLOW}2. Checking API token...${NC}"
if [ ! -f "$TOKEN_FILE" ]; then
    echo -e "${RED}✗ API token file not found (.api_token)${NC}"
    echo "  Generate token with: python app/cli.py"
    echo "  Then save to .api_token file"
    exit 1
fi
TOKEN=$(cat "$TOKEN_FILE")
echo -e "${GREEN}✓ API token loaded${NC}"
echo

# Get current configuration
echo -e "${YELLOW}3. Current Configuration:${NC}"
CURRENT=$(curl -s "$API_URL/api/alerts/config")
echo "$CURRENT" | jq '.' | sed 's/^/   /'
echo

# Main menu
show_menu() {
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Alert Configuration Options:${NC}"
    echo -e "${BLUE}═════════════════════════════════════════════════════════════${NC}"
    echo "  1. Enable Email Alerts (Gmail)"
    echo "  2. Enable Discord Webhooks"
    echo "  3. Enable Both (Email + Discord)"
    echo "  4. Configure Throttling"
    echo "  5. Configure Thresholds"
    echo "  6. Select Alert Types"
    echo "  7. Test Email"
    echo "  8. Test Discord"
    echo "  9. View Configuration"
    echo "  10. View Alert History"
    echo "  0. Exit"
    echo
}

# Email setup
setup_email() {
    echo -e "${YELLOW}Gmail Alert Setup${NC}"
    echo
    
    read -p "Gmail address (example@gmail.com): " gmail_address
    echo -e "${YELLOW}Getting app password from${NC} ${BLUE}myaccount.google.com/security${NC}"
    read -sp "Gmail app password (16 chars, no spaces): " app_password
    echo
    
    read -p "Recipient emails (comma-separated): " recipients
    
    # Convert comma-separated to JSON array
    recipients_json=$(echo "$recipients" | tr ',' '\n' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | jq -R '.' | jq -s '.')
    
    # Get current config and update
    curl -s -X POST "$API_URL/api/alerts/config" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"enabled\": true,
            \"email\": {
                \"enabled\": true,
                \"smtp_server\": \"smtp.gmail.com\",
                \"smtp_port\": 587,
                \"sender_email\": \"$gmail_address\",
                \"sender_password\": \"$app_password\",
                \"recipients\": $recipients_json
            }
        }" > /dev/null
    
    echo -e "${GREEN}✓ Email configuration saved${NC}"
    echo
}

# Discord setup
setup_discord() {
    echo -e "${YELLOW}Discord Webhook Setup${NC}"
    echo
    
    echo "Creating Discord webhook:"
    echo "  1. Open your Discord server"
    echo "  2. Server Settings → Integrations → Webhooks"
    echo "  3. Click 'New Webhook', name it 'DDoSPot'"
    echo "  4. Copy the webhook URL"
    echo
    
    read -p "Webhook URL (paste here): " webhook_url
    
    curl -s -X POST "$API_URL/api/alerts/config" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"enabled\": true,
            \"discord\": {
                \"enabled\": true,
                \"webhook_url\": \"$webhook_url\"
            }
        }" > /dev/null
    
    echo -e "${GREEN}✓ Discord configuration saved${NC}"
    echo
}

# Throttle setup
setup_throttle() {
    echo -e "${YELLOW}Throttling Configuration${NC}"
    echo "Prevents alert fatigue by limiting alert frequency"
    echo
    
    echo "Preset options:"
    echo "  1. Aggressive (60 seconds)"
    echo "  2. Balanced (300 seconds) [Default]"
    echo "  3. Conservative (3600 seconds)"
    echo "  4. Custom"
    echo
    
    read -p "Select (1-4): " throttle_choice
    
    case $throttle_choice in
        1) interval=60 ;;
        2) interval=300 ;;
        3) interval=3600 ;;
        4)
            read -p "Enter interval in seconds: " interval
            ;;
        *) 
            echo -e "${RED}Invalid choice${NC}"
            return
            ;;
    esac
    
    curl -s -X POST "$API_URL/api/alerts/config" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"throttle\": {
                \"enabled\": true,
                \"min_interval_seconds\": $interval
            }
        }" > /dev/null
    
    echo -e "${GREEN}✓ Throttling set to $interval seconds${NC}"
    echo
}

# Threshold setup
setup_threshold() {
    echo -e "${YELLOW}Alert Threshold Configuration${NC}"
    echo "Minimum event count to trigger alert"
    echo
    
    echo "Preset options:"
    echo "  1. High sensitivity (10 events)"
    echo "  2. Medium sensitivity (50 events)"
    echo "  3. Low sensitivity (100 events) [Default]"
    echo "  4. Custom"
    echo
    
    read -p "Select (1-4): " threshold_choice
    
    case $threshold_choice in
        1) threshold=10 ;;
        2) threshold=50 ;;
        3) threshold=100 ;;
        4)
            read -p "Enter threshold (events): " threshold
            ;;
        *) 
            echo -e "${RED}Invalid choice${NC}"
            return
            ;;
    esac
    
    curl -s -X POST "$API_URL/api/alerts/config" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"threshold\": $threshold
        }" > /dev/null
    
    echo -e "${GREEN}✓ Threshold set to $threshold events${NC}"
    echo
}

# Alert types setup
setup_alert_types() {
    echo -e "${YELLOW}Select Alert Types${NC}"
    echo
    
    current_config=$(curl -s "$API_URL/api/alerts/config")
    
    echo "Current alert types:"
    echo "$current_config" | jq '.alerts[] as {$key: $value} | "\($key): \($value)"' -r 2>/dev/null || echo "Could not read current config"
    echo
    
    echo "Enable which alert types? (comma-separated numbers)"
    echo "  1. Critical Attack"
    echo "  2. IP Blacklisted"
    echo "  3. Sustained Attack"
    echo "  4. Multi-Protocol"
    echo "  [default: all enabled]"
    echo
    
    read -p "Select (1-4 or leave blank for all): " alert_selection
    
    # Set all to true by default
    critical=true
    blacklist=true
    sustained=true
    multi=true
    
    # Parse selection
    if [ ! -z "$alert_selection" ]; then
        critical=false
        blacklist=false
        sustained=false
        multi=false
        
        IFS=',' read -ra selected <<< "$alert_selection"
        for num in "${selected[@]}"; do
            case $num in
                1) critical=true ;;
                2) blacklist=true ;;
                3) sustained=true ;;
                4) multi=true ;;
            esac
        done
    fi
    
    curl -s -X POST "$API_URL/api/alerts/config" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{
            \"alerts\": {
                \"critical_attack\": $critical,
                \"ip_blacklisted\": $blacklist,
                \"sustained_attack\": $sustained,
                \"multi_protocol\": $multi
            }
        }" > /dev/null
    
    echo -e "${GREEN}✓ Alert types configured${NC}"
    echo
}

# Test email
test_email() {
    echo -e "${YELLOW}Sending test email...${NC}"
    
    response=$(curl -s -X POST "$API_URL/api/alerts/test" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "type": "test",
            "message": "Test alert from DDoSPot configuration"
        }')
    
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Test alert sent${NC}"
        echo "Check your email in the next 30 seconds"
    else
        echo -e "${RED}✗ Failed to send test alert${NC}"
        echo "Error: $response"
    fi
    echo
}

# Test Discord
test_discord() {
    echo -e "${YELLOW}Sending test Discord message...${NC}"
    
    response=$(curl -s -X POST "$API_URL/api/alerts/test" \
        -H "X-API-Token: $TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "type": "test",
            "message": "🧪 Test alert from DDoSPot configuration"
        }')
    
    if echo "$response" | jq . > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Test message sent${NC}"
        echo "Check your Discord channel now"
    else
        echo -e "${RED}✗ Failed to send test message${NC}"
        echo "Error: $response"
    fi
    echo
}

# View configuration
view_config() {
    echo -e "${YELLOW}Current Configuration:${NC}"
    echo
    curl -s "$API_URL/api/alerts/config" | jq '.' | sed 's/^/   /'
    echo
}

# View history
view_history() {
    echo -e "${YELLOW}Alert History:${NC}"
    echo
    
    history=$(curl -s "$API_URL/api/alerts/history")
    
    if [ $(echo "$history" | jq 'length') -eq 0 ]; then
        echo "   No alerts yet"
    else
        echo "$history" | jq -r '.[] | "\(.timestamp) - \(.type): \(.message)"' | sed 's/^/   /'
    fi
    echo
}

# Main loop
while true; do
    show_menu
    read -p "Select option: " choice
    echo
    
    case $choice in
        1) setup_email ;;
        2) setup_discord ;;
        3) setup_email; setup_discord ;;
        4) setup_throttle ;;
        5) setup_threshold ;;
        6) setup_alert_types ;;
        7) test_email ;;
        8) test_discord ;;
        9) view_config ;;
        10) view_history ;;
        0) 
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            echo
            ;;
    esac
done
