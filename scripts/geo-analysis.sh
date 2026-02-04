#!/bin/bash
# geo-analysis.sh - Geographic attack analysis report

API="http://127.0.0.1:5000"

echo "🌍 Geographic Attack Analysis Report"
echo "════════════════════════════════════════════════════════════════"
echo "Generated: $(date)"
echo ""

# Test connection
if ! curl -s "$API/health" > /dev/null 2>&1; then
    echo "❌ Error: Dashboard not running at $API"
    echo "Start it with: bash START_DASHBOARD.sh"
    exit 1
fi

# Get map data
echo "📊 Fetching attack data..."
MAP_DATA=$(curl -s "$API/api/map-data" 2>/dev/null)

if [ -z "$MAP_DATA" ]; then
    echo "❌ Error: Could not fetch map data"
    exit 1
fi

# Extract data
TOTAL_POINTS=$(echo "$MAP_DATA" | grep -o '"ip"' | wc -l)
echo "✓ Found $TOTAL_POINTS attack origins"
echo ""

# Attack origins by country
echo "🗺️  Top Attack Origins:"
echo "────────────────────────────────────────────────────────────────"
printf "%-25s %10s %10s %15s\n" "Country" "Events" "IPs" "Top Protocol"
echo "────────────────────────────────────────────────────────────────"

echo "$MAP_DATA" | jq -r '.[] | "\(.country)|\(.events)|\(.ip)"' | sort | awk -F'|' '{
    country[$1]++;
    events[$1]+=$2;
}
END {
    for (c in country) {
        printf "%-25s %10s %10s\n", c, events[c], country[c]
    }
}' | sort -k3 -rn | head -10

echo ""

# Geographic distribution
echo "📈 Geographic Distribution:"
echo "────────────────────────────────────────────────────────────────"

NORTH_AMERICA=$(echo "$MAP_DATA" | grep -i '"country":".*\(United States\|Canada\|Mexico\)"' | wc -l)
EUROPE=$(echo "$MAP_DATA" | grep -i '"country":".*\(Russia\|Germany\|France\|UK\|United Kingdom\)"' | wc -l)
ASIA=$(echo "$MAP_DATA" | grep -i '"country":".*\(China\|Japan\|India\|Singapore\)"' | wc -l)
OTHER=$(echo "$MAP_DATA" | jq -r '.[].country' | sort -u | wc -l)

echo "  🇺🇸 North America:    $NORTH_AMERICA origins"
echo "  🇪🇺 Europe:          $EUROPE origins"
echo "  🌏 Asia:            $ASIA origins"
echo "  🌐 Other regions:   $((OTHER - NORTH_AMERICA - EUROPE - ASIA)) origins"
echo ""

# Attack intensity by location
echo "🎯 Most Active Attack Origins:"
echo "────────────────────────────────────────────────────────────────"
printf "%-18s %-20s %10s %12s\n" "IP" "Country/City" "Events" "Protocols"
echo "────────────────────────────────────────────────────────────────"

echo "$MAP_DATA" | jq -r '.[] | "\(.ip)|\(.country)|\(.city)|\(.events)|\(.protocols)"' | 
sort -t'|' -k4 -rn | head -5 | while IFS='|' read ip country city events protocols; do
    city_str="$country"
    if [ ! -z "$city" ] && [ "$city" != "null" ]; then
        city_str="$city, $country"
    fi
    # Remove JSON array formatting from protocols
    proto_str=$(echo "$protocols" | tr -d '[]"' | tr ',' ' ' | cut -d' ' -f1,2,3)
    printf "%-18s %-20s %10s %12s\n" "$ip" "$city_str" "$events" "$proto_str"
done

echo ""

# Coordinate analysis
echo "📍 Geographic Bounding Box:"
echo "────────────────────────────────────────────────────────────────"

MIN_LAT=$(echo "$MAP_DATA" | jq -r '.[].latitude' | sort -n | head -1)
MAX_LAT=$(echo "$MAP_DATA" | jq -r '.[].latitude' | sort -n | tail -1)
MIN_LON=$(echo "$MAP_DATA" | jq -r '.[].longitude' | sort -n | head -1)
MAX_LON=$(echo "$MAP_DATA" | jq -r '.[].longitude' | sort -n | tail -1)

echo "  North-South span: ${MIN_LAT}° to ${MAX_LAT}° ($(echo "$MAX_LAT - $MIN_LAT" | bc)° range)"
echo "  East-West span:   ${MIN_LON}° to ${MAX_LON}° ($(echo "$MAX_LON - $MIN_LON" | bc)° range)"
echo ""

# Statistics
echo "📊 Statistics:"
echo "────────────────────────────────────────────────────────────────"

TOTAL_EVENTS=$(echo "$MAP_DATA" | jq -r '.[].events' | awk '{sum+=$1} END {print sum}')
AVG_EVENTS=$(echo "scale=2; $TOTAL_EVENTS / $TOTAL_POINTS" | bc)

echo "  Total Events:     $TOTAL_EVENTS"
echo "  Unique Origins:   $TOTAL_POINTS"
echo "  Avg Events/IP:    $AVG_EVENTS"
echo ""

# Protocol breakdown
echo "🔀 Protocols Used Globally:"
echo "────────────────────────────────────────────────────────────────"

echo "$MAP_DATA" | jq -r '.[].protocols[]' | sort | uniq -c | sort -rn | while read count proto; do
    pct=$(echo "scale=1; $count * 100 / $TOTAL_EVENTS" | bc 2>/dev/null || echo "?")
    printf "  %-15s %4s events (%s%%)\n" "$proto" "$count" "$pct"
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Analysis Complete!"
echo ""
echo "💡 Tips:"
echo "  • View interactive map: http://127.0.0.1:5000/advanced"
echo "  • Export as GeoJSON: curl http://127.0.0.1:5000/api/map-data | jq ."
echo "  • Get country stats: curl http://127.0.0.1:5000/api/country-stats"
echo ""
