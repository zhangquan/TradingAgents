#!/bin/bash

echo "🛑 Stopping TradingAgents Production Environment"
echo "================================================"

# Function to stop service by PID file
stop_service() {
    local service_name=$1
    local pid_file="logs/$service_name.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            echo "🛑 Stopping $service_name (PID: $pid)..."
            kill $pid
            
            # Wait up to 10 seconds for graceful shutdown
            for i in {1..10}; do
                if ! ps -p $pid > /dev/null 2>&1; then
                    echo "✅ $service_name stopped successfully"
                    rm -f "$pid_file"
                    return 0
                fi
                sleep 1
            done
            
            # Force kill if still running
            echo "⚠️ Force stopping $service_name..."
            kill -9 $pid 2>/dev/null
            rm -f "$pid_file"
            echo "✅ $service_name force stopped"
        else
            echo "⚠️ $service_name PID file exists but process not running"
            rm -f "$pid_file"
        fi
    else
        echo "ℹ️ No $service_name PID file found"
    fi
}

# Stop services
stop_service "backend" "Backend API Server"
stop_service "frontend" "Frontend Server"

# Also kill any remaining processes on the ports
echo "🧹 Cleaning up any remaining processes..."

# Kill processes on port 8000 (backend)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "🔧 Killing remaining processes on port 8000..."
    lsof -Pi :8000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
fi

# Kill processes on port 3000 (frontend)
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "🌐 Killing remaining processes on port 3000..."
    lsof -Pi :3000 -sTCP:LISTEN -t | xargs kill -9 2>/dev/null
fi

echo ""
echo "✅ All TradingAgents services stopped"
echo "📊 To verify, run: lsof -i :8000,3000"
