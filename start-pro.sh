#!/bin/bash

echo "🚀 Starting TradingAgents Production Environment"
echo "================================================"

# Create logs directory if it doesn't exist
mkdir -p logs

# Function to write PID files
write_pid() {
    echo $1 > "logs/$2.pid"
}

# Function to check if service is running
check_service() {
    if [ -f "logs/$1.pid" ]; then
        local pid=$(cat "logs/$1.pid")
        if ps -p $pid > /dev/null 2>&1; then
            echo "❌ $2 is already running (PID: $pid). Please stop it first."
            exit 1
        else
            rm -f "logs/$1.pid"
        fi
    fi
}

# Check if backend service is already running
check_service "backend" "Backend API Server"

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 8000 is already in use. Please stop the service and try again."
    exit 1
fi

# Start backend in background
echo "🔧 Starting Backend API Server..."
nohup uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
write_pid $BACKEND_PID "backend"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."

# Wait up to 30 seconds for backend to be ready
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null; then
        break
    fi
    echo "⏳ Backend starting... ($i/30)"
    sleep 1
done

# Final check if backend started successfully
if ! curl -s http://localhost:8000/health >/dev/null; then
    echo "❌ Backend failed to start after 30 seconds. Check logs/backend.log for details."
    kill $BACKEND_PID 2>/dev/null
    rm -f logs/backend.pid
    exit 1
fi

echo "✅ Backend API Server running on http://localhost:8000 (PID: $BACKEND_PID)"

echo ""
echo "🎉 TradingAgents Production Environment Started!"
echo "================================================"
echo "🌐 Web Interface: http://localhost:8000 (Frontend integrated in backend)"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📋 Process Information:"
echo "   Backend PID: $BACKEND_PID (logs/backend.log)"
echo ""
echo "🛑 To stop services, run: ./stop-pro.sh"
echo "📊 To check status, run: ps -p $BACKEND_PID"
