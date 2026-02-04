#!/bin/bash
# START_DASHBOARD_SECURE.sh - Start dashboard with token authentication enabled

set -e

PROJECT_DIR="/home/hunter/Projekty/ddospot"
cd "$PROJECT_DIR"

echo "🔐 DDoSPoT Dashboard - Secure Mode"
echo "════════════════════════════════════════════════════════════════"

# Check if token is already set
if [ -z "$DDOSPOT_API_TOKEN" ]; then
    echo ""
    echo "📝 Generating secure API token..."
    DDOSPOT_API_TOKEN=$(openssl rand -hex 32)
    echo "✓ Token: $DDOSPOT_API_TOKEN"
else
    echo ""
    echo "✓ Using existing token: ${DDOSPOT_API_TOKEN:0:16}..."
fi

# Enable token requirement
export DDOSPOT_API_TOKEN
export DDOSPOT_REQUIRE_TOKEN=true

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🚀 Starting Dashboard with Security Enabled"
echo ""
echo "📋 Configuration:"
echo "   Token: ${DDOSPOT_API_TOKEN:0:32}..."
echo "   Token required: YES"
echo "   Dashboard URL: http://127.0.0.1:5000"
echo ""
echo "🔑 To access APIs, use:"
echo "   curl -H \"Authorization: Bearer $DDOSPOT_API_TOKEN\" http://127.0.0.1:5000/api/stats"
echo ""
echo "✋ Press Ctrl+C to stop"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Start dashboard
python start-dashboard.py
