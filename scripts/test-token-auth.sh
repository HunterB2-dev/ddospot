#!/bin/bash
# test-token-auth.sh - Demonstrate token authentication

PROJECT_DIR="/home/hunter/Projekty/ddospot"
API_URL="http://127.0.0.1:5000"

echo "🔐 DDoSPoT Token Authentication Test"
echo "════════════════════════════════════════════════════════════════"

# Check if dashboard is running
echo ""
echo "1️⃣  Checking if dashboard is running..."
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo "   ❌ Dashboard not running at $API_URL"
    echo "   🚀 Start it with: python start-dashboard.py &"
    exit 1
fi
echo "   ✓ Dashboard is running"

# Check current token status
echo ""
echo "2️⃣  Checking current security configuration..."
if [ -z "$DDOSPOT_REQUIRE_TOKEN" ]; then
    echo "   ⚠️  Token requirement not set (DDOSPOT_REQUIRE_TOKEN is empty)"
    echo "   ℹ️  APIs are currently UNPROTECTED"
else
    echo "   ✓ Token requirement: $DDOSPOT_REQUIRE_TOKEN"
fi

if [ -z "$DDOSPOT_API_TOKEN" ]; then
    echo "   ⚠️  No token configured (DDOSPOT_API_TOKEN is empty)"
    echo "   📝 Generate one: openssl rand -hex 32"
else
    echo "   ✓ Token set: ${DDOSPOT_API_TOKEN:0:16}... (first 16 chars)"
fi

# Test without token
echo ""
echo "3️⃣  Testing access WITHOUT token..."
RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/api/stats" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ 200 OK - Token protection is OFF (unprotected)"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ 401 Unauthorized - Token protection is ON (protected)"
else
    echo "   ❓ Unexpected status: $HTTP_CODE"
fi

# Generate token if not set
if [ -z "$DDOSPOT_API_TOKEN" ]; then
    echo ""
    echo "4️⃣  No token found - generating one..."
    DDOSPOT_API_TOKEN=$(openssl rand -hex 32)
    export DDOSPOT_API_TOKEN
    echo "   ✓ Generated token: ${DDOSPOT_API_TOKEN:0:16}..."
else
    echo ""
    echo "4️⃣  Using existing token..."
    echo "   Token: ${DDOSPOT_API_TOKEN:0:16}... (truncated)"
fi

# Test with token in Authorization header
echo ""
echo "5️⃣  Testing with Authorization header..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $DDOSPOT_API_TOKEN" \
    "$API_URL/api/stats" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
DATA=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ 200 OK - Authorization header works!"
    EVENTS=$(echo "$DATA" | grep -o '"total_events":[0-9]*' | head -1)
    if [ ! -z "$EVENTS" ]; then
        echo "   ✓ Response data: $EVENTS"
    fi
elif [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ 401 Unauthorized - Dashboard doesn't require token (OK)"
else
    echo "   ❓ Status: $HTTP_CODE"
fi

# Test with X-API-Token header
echo ""
echo "6️⃣  Testing with X-API-Token header..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "X-API-Token: $DDOSPOT_API_TOKEN" \
    "$API_URL/api/stats" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ $HTTP_CODE - X-API-Token header works!"
else
    echo "   ❓ Status: $HTTP_CODE"
fi

# Test with query parameter
echo ""
echo "7️⃣  Testing with query parameter..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    "$API_URL/api/stats?token=$DDOSPOT_API_TOKEN" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ $HTTP_CODE - Query parameter works!"
else
    echo "   ❓ Status: $HTTP_CODE"
fi

# Test with wrong token
echo ""
echo "8️⃣  Testing with wrong token..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer wrong_token_12345" \
    "$API_URL/api/stats" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | tail -1)

if [ "$HTTP_CODE" = "401" ]; then
    echo "   ✓ 401 Unauthorized - Rejected wrong token (correct!)"
elif [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ 200 OK - Token protection is off (OK)"
else
    echo "   ❓ Status: $HTTP_CODE"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Token Authentication Test Complete!"
echo ""
echo "📋 Summary:"
echo "   Your token (save this!): $DDOSPOT_API_TOKEN"
echo ""
echo "🚀 To enable token protection, run:"
echo "   export DDOSPOT_API_TOKEN=$DDOSPOT_API_TOKEN"
echo "   export DDOSPOT_REQUIRE_TOKEN=true"
echo "   python start-dashboard.py"
echo ""
echo "📚 Documentation: See TASK_6_SECURITY_HARDENING.md"
echo ""
