#!/bin/bash
# enable-security.sh - Easily enable security on running dashboard

PROJECT_DIR="/home/hunter/Projekty/ddospot"
cd "$PROJECT_DIR"

echo "🔐 Enable DDoSPoT Security"
echo "════════════════════════════════════════════════════════════════"

# Generate token if needed
if [ -z "$1" ]; then
    TOKEN=$(openssl rand -hex 32)
    echo "Generating new token..."
else
    TOKEN="$1"
fi

echo ""
echo "✓ Security configuration ready:"
echo ""
echo "Export these in your shell:"
echo "  export DDOSPOT_API_TOKEN='$TOKEN'"
echo "  export DDOSPOT_REQUIRE_TOKEN=true"
echo ""
echo "Or save to .env file:"
echo "  cat > .env << EOF"
echo "  DDOSPOT_API_TOKEN=$TOKEN"
echo "  DDOSPOT_REQUIRE_TOKEN=true"
echo "  EOF"
echo ""
echo "Or run dashboard with security directly:"
echo "  DDOSPOT_API_TOKEN='$TOKEN' DDOSPOT_REQUIRE_TOKEN=true python start-dashboard.py"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "After enabling, test with:"
echo "  TOKEN='$TOKEN'"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" http://127.0.0.1:5000/api/stats"
echo ""
