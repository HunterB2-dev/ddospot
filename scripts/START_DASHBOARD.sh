#!/bin/bash
# DDoSPot Dashboard & Honeypot Startup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🍯 DDoSPot - Starting Services"
echo "======================================"

# Kill any existing processes
echo "Stopping any existing services..."
pkill -f "start-dashboard.py" || true
pkill -f "start-honeypot.py" || true
sleep 2

# Check if virtual environment exists
if [ ! -f "myenv/bin/activate" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv myenv && source myenv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source myenv/bin/activate

# Verify dependencies
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo "❌ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
}

# Clean up old database file if it exists
if [ -f "honeypot.db" ]; then
    echo "Removing old database file..."
    rm honeypot.db
fi

# Ensure logs directory exists
mkdir -p logs

# Start honeypot in background
echo ""
echo "Starting honeypot service..."
nohup python start-honeypot.py > logs/honeypot.log 2>&1 &
HONEYPOT_PID=$!
echo "✓ Honeypot started (PID: $HONEYPOT_PID)"

# Wait for honeypot to initialize
sleep 3

# Start dashboard in background
echo "Starting dashboard service..."
nohup python start-dashboard.py > logs/dashboard.log 2>&1 &
DASHBOARD_PID=$!
echo "✓ Dashboard started (PID: $DASHBOARD_PID)"

# Wait for dashboard to initialize
sleep 3

# Verify services are running
echo ""
echo "======================================"
echo "✓ Services started successfully!"
echo "======================================"

# Get machine IP
MACHINE_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "🌐 DASHBOARD ACCESS:"
echo "   Local:   http://127.0.0.1:5000"
echo "   Network: http://$MACHINE_IP:5000"
echo ""

# Test health endpoint
echo "Testing API health..."
if curl -s http://127.0.0.1:5000/health > /dev/null 2>&1; then
    echo "✓ Dashboard API is responding"
else
    echo "⚠ Dashboard not responding yet, check logs..."
fi

echo ""
echo "📝 LOGS:"
echo "   Dashboard: tail -f logs/dashboard.log"
echo "   Honeypot:  tail -f logs/honeypot.log"
echo ""
echo "🛑 To stop services:"
echo "   pkill -f start-dashboard.py"
echo "   pkill -f start-honeypot.py"
echo "======================================"
