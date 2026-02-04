#!/bin/bash
# Data Export Script - Export honeypot data in multiple formats

echo "=================================================="
echo "🍯 DDoSPot Data Export Tool"
echo "=================================================="

EXPORT_DIR="exports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create exports directory
mkdir -p "$EXPORT_DIR"

echo -e "\n📊 Exporting data in multiple formats...\n"

# 1. Export Events as CSV
echo "1️⃣  Exporting events as CSV..."
CSV_FILE="$EXPORT_DIR/events_$TIMESTAMP.csv"
curl -s "http://127.0.0.1:5000/api/export/events/csv" > "$CSV_FILE"
if [ -f "$CSV_FILE" ] && [ -s "$CSV_FILE" ]; then
    LINES=$(wc -l < "$CSV_FILE")
    echo "   ✓ Saved to: $CSV_FILE ($LINES lines)"
else
    echo "   ✗ Failed to export CSV"
fi

# 2. Export Events as JSON
echo "2️⃣  Exporting events as JSON..."
JSON_EVENTS="$EXPORT_DIR/events_$TIMESTAMP.json"
curl -s "http://127.0.0.1:5000/api/export/events/json" > "$JSON_EVENTS"
if [ -f "$JSON_EVENTS" ] && [ -s "$JSON_EVENTS" ]; then
    SIZE=$(du -h "$JSON_EVENTS" | cut -f1)
    echo "   ✓ Saved to: $JSON_EVENTS ($SIZE)"
else
    echo "   ✗ Failed to export events JSON"
fi

# 3. Export Statistics as JSON
echo "3️⃣  Exporting statistics as JSON..."
JSON_STATS="$EXPORT_DIR/statistics_$TIMESTAMP.json"
curl -s "http://127.0.0.1:5000/api/export/stats/json" > "$JSON_STATS"
if [ -f "$JSON_STATS" ] && [ -s "$JSON_STATS" ]; then
    SIZE=$(du -h "$JSON_STATS" | cut -f1)
    echo "   ✓ Saved to: $JSON_STATS ($SIZE)"
else
    echo "   ✗ Failed to export stats JSON"
fi

# 4. Export Full Report
echo "4️⃣  Exporting comprehensive report..."
JSON_REPORT="$EXPORT_DIR/report_$TIMESTAMP.json"
curl -s "http://127.0.0.1:5000/api/export/report/json" > "$JSON_REPORT"
if [ -f "$JSON_REPORT" ] && [ -s "$JSON_REPORT" ]; then
    SIZE=$(du -h "$JSON_REPORT" | cut -f1)
    echo "   ✓ Saved to: $JSON_REPORT ($SIZE)"
else
    echo "   ✗ Failed to export report JSON"
fi

# 5. Export IP Profiles
echo "5️⃣  Exporting IP profiles as JSON..."
JSON_PROFILES="$EXPORT_DIR/profiles_$TIMESTAMP.json"
curl -s "http://127.0.0.1:5000/api/export/profiles/json" > "$JSON_PROFILES"
if [ -f "$JSON_PROFILES" ] && [ -s "$JSON_PROFILES" ]; then
    SIZE=$(du -h "$JSON_PROFILES" | cut -f1)
    echo "   ✓ Saved to: $JSON_PROFILES ($SIZE)"
else
    echo "   ✗ Failed to export profiles JSON"
fi

# Summary
echo -e "\n=================================================="
echo "📁 Export Summary"
echo "=================================================="
echo "Location: $(pwd)/$EXPORT_DIR/"
echo ""
ls -lh "$EXPORT_DIR/" | tail -n +2 | awk '{print "   " $9 " (" $5 ")"}'

echo -e "\n✓ Data export complete!"
echo ""
echo "You can now:"
echo "  • Open CSV files in Excel/Sheets"
echo "  • Parse JSON files for analysis"
echo "  • Import into SIEM systems"
echo "  • Share with security teams"
echo ""
