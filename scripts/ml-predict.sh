#!/bin/bash
# ml-predict.sh - Predict attack types for all attacking IPs

API="http://127.0.0.1:5000"

echo "🤖 Attack Classification Report"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Get all attacking IPs
echo "📊 Fetching attack data..."
TOP_IPS=$(curl -s "$API/api/top-attackers" 2>/dev/null | grep -o '"ip":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOP_IPS" ]; then
    echo "❌ Error: Could not fetch top attackers"
    echo "   Make sure dashboard is running at $API"
    exit 1
fi

# Count IPs
IP_COUNT=$(echo "$TOP_IPS" | wc -l)
echo "✓ Found $IP_COUNT attacking IPs"
echo ""

# Prediction summary
NORMAL_COUNT=0
VOLUMETRIC_COUNT=0
AMPLIFICATION_COUNT=0
SUSTAINED_COUNT=0
MULTI_COUNT=0

echo "Attack Predictions:"
echo "────────────────────────────────────────────────────────────────"
printf "%-20s %-20s %-12s %-8s\n" "IP Address" "Attack Type" "Confidence" "Events"
echo "────────────────────────────────────────────────────────────────"

for ip in $TOP_IPS; do
    # Get prediction
    PRED=$(curl -s "$API/api/ml/predict/$ip" 2>/dev/null)
    
    if [ -z "$PRED" ]; then
        echo "❌ Error predicting for $ip"
        continue
    fi
    
    TYPE=$(echo "$PRED" | grep -o '"prediction":"[^"]*"' | cut -d'"' -f4)
    CONF=$(echo "$PRED" | grep -o '"confidence":[0-9.]*' | cut -d':' -f2)
    EVENTS=$(echo "$PRED" | grep -o '"event_count":[0-9]*' | cut -d':' -f2)
    
    if [ -z "$TYPE" ]; then
        TYPE="unknown"
        CONF=0
    fi
    
    # Format confidence as percentage
    CONF_PCT=$(printf "%.1f" $(echo "$CONF * 100" | bc 2>/dev/null || echo "0"))%
    
    # Count by type
    case "$TYPE" in
        "volumetric") VOLUMETRIC_COUNT=$((VOLUMETRIC_COUNT+1)) ;;
        "amplification") AMPLIFICATION_COUNT=$((AMPLIFICATION_COUNT+1)) ;;
        "sustained") SUSTAINED_COUNT=$((SUSTAINED_COUNT+1)) ;;
        "multi_protocol") MULTI_COUNT=$((MULTI_COUNT+1)) ;;
        *) NORMAL_COUNT=$((NORMAL_COUNT+1)) ;;
    esac
    
    # Display with color coding
    if [ "$TYPE" = "volumetric" ]; then
        ICON="🔴"
    elif [ "$TYPE" = "amplification" ]; then
        ICON="🟠"
    elif [ "$TYPE" = "sustained" ]; then
        ICON="🟡"
    elif [ "$TYPE" = "multi_protocol" ]; then
        ICON="🟣"
    else
        ICON="🟢"
    fi
    
    printf "%s %-18s %-20s %-12s %-8s\n" "$ICON" "$ip" "$TYPE" "$CONF_PCT" "$EVENTS"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📈 Summary:"
echo ""
echo "  🟢 Normal/Benign:           $NORMAL_COUNT"
echo "  🔴 Volumetric:              $VOLUMETRIC_COUNT"
echo "  🟠 Amplification:           $AMPLIFICATION_COUNT"
echo "  🟡 Sustained:               $SUSTAINED_COUNT"
echo "  🟣 Multi-Protocol:          $MULTI_COUNT"
echo ""
echo "  Total IPs analyzed:         $IP_COUNT"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "ℹ️  Classifications:"
echo "  🟢 Normal:            Benign or single probes"
echo "  🔴 Volumetric:        High-volume floods"
echo "  🟠 Amplification:      Reflection/amplification attacks"
echo "  🟡 Sustained:          Continuous/slow-rate attacks"
echo "  🟣 Multi-Protocol:     Multiple protocol attacks"
echo ""
