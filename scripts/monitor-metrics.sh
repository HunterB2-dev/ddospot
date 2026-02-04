#!/bin/bash
# monitor-metrics.sh - Real-time Prometheus metrics monitoring

API="http://127.0.0.1:5000"
INTERVAL=5

echo "📊 DDoSPoT Prometheus Metrics Monitor"
echo "════════════════════════════════════════════════════════════════"
echo "Updating every $INTERVAL seconds (Press Ctrl+C to stop)"
echo ""

# Check connection
if ! curl -s "$API/health" > /dev/null 2>&1; then
    echo "❌ Error: Dashboard not running at $API"
    exit 1
fi

# Monitoring loop
COUNT=0
while true; do
    # Fetch metrics
    METRICS=$(curl -s "$API/metrics" 2>/dev/null)
    
    if [ -z "$METRICS" ]; then
        echo "❌ Error: Could not fetch metrics"
        sleep $INTERVAL
        continue
    fi
    
    # Clear screen and show header
    clear
    echo "📊 DDoSPoT Prometheus Metrics Monitor"
    echo "════════════════════════════════════════════════════════════════"
    echo "Last updated: $(date '+%Y-%m-%d %H:%M:%S')  |  Update #$COUNT"
    echo ""
    
    # Extract key metrics
    UNIQUE_ATTACKERS=$(echo "$METRICS" | grep 'ddospot_unique_attackers' | grep -v '#' | awk '{print $2}')
    BLACKLISTED=$(echo "$METRICS" | grep 'ddospot_blacklisted_ips' | grep -v '#' | awk '{print $2}')
    TOTAL_EVENTS=$(echo "$METRICS" | grep 'ddospot_database_events_total' | grep -v '#' | awk '{print $2}')
    DB_SIZE=$(echo "$METRICS" | grep 'ddospot_database_size_bytes' | grep -v '#' | awk '{print $2}')
    HTTP_REQUESTS=$(echo "$METRICS" | grep 'ddospot_http_requests_total' | grep -v '#' | head -1 | awk '{print $2}')
    SERVICE_STATUS=$(echo "$METRICS" | grep 'ddospot_service_status{service="dashboard"}' | grep -v '#' | awk '{print $2}')
    CPU_USAGE=$(echo "$METRICS" | grep 'ddospot_cpu_usage_percent' | grep -v '#' | awk '{print $2}')
    
    # Format values
    UNIQUE_ATTACKERS=${UNIQUE_ATTACKERS:-0}
    BLACKLISTED=${BLACKLISTED:-0}
    TOTAL_EVENTS=${TOTAL_EVENTS:-0}
    DB_SIZE_MB=$(echo "scale=1; $DB_SIZE / 1024 / 1024" | bc 2>/dev/null || echo "0")
    HTTP_REQUESTS=${HTTP_REQUESTS:-0}
    CPU_USAGE=$(printf "%.1f" $CPU_USAGE 2>/dev/null || echo "0")
    
    # Format service status
    if [ "$SERVICE_STATUS" = "1" ]; then
        SERVICE_STR="🟢 UP"
    else
        SERVICE_STR="🔴 DOWN"
    fi
    
    # Display metrics in sections
    echo "🎯 Attack Metrics:"
    echo "   Unique Attackers:      $UNIQUE_ATTACKERS"
    echo "   Blacklisted IPs:       $BLACKLISTED"
    echo "   Total Events:          $TOTAL_EVENTS"
    echo ""
    
    echo "💾 Database Metrics:"
    echo "   Database Size:         ${DB_SIZE_MB} MB"
    echo "   Total HTTP Requests:   $HTTP_REQUESTS"
    echo ""
    
    echo "🖥️  System Metrics:"
    echo "   Service Status:        $SERVICE_STR"
    echo "   CPU Usage:             ${CPU_USAGE}%"
    echo ""
    
    # Protocol breakdown
    echo "🔀 Protocol Breakdown:"
    echo "$METRICS" | grep 'ddospot_attack_events_total{' | grep -v '#' | head -5 | while read line; do
        if [ ! -z "$line" ]; then
            PROTOCOL=$(echo "$line" | grep -o 'protocol="[^"]*"' | cut -d'"' -f2)
            COUNT_VAL=$(echo "$line" | awk '{print $NF}')
            printf "   %-20s %10s events\n" "$PROTOCOL" "$COUNT_VAL"
        fi
    done
    echo ""
    
    # ML Model metrics
    PREDICTIONS=$(echo "$METRICS" | grep 'ddospot_ml_predictions_total' | grep -v '#' | awk '{print $2}')
    echo "🤖 ML Model Metrics:"
    echo "   Total Predictions:     ${PREDICTIONS:-0}"
    echo ""
    
    # Footer
    echo "════════════════════════════════════════════════════════════════"
    echo "💡 Tip: View raw metrics with: curl $API/metrics"
    
    # Increment counter and wait
    COUNT=$((COUNT+1))
    sleep $INTERVAL
done
