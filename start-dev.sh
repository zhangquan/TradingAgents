#!/bin/bash

echo "🚀 Starting TradingAgents Development Environment"
echo "================================================"

# Check if ports are available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 8000 is already in use. Please stop the service and try again."
    exit 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null ; then
    echo "❌ Port 3000 is already in use. Please stop the service and try again."
    exit 1
fi

# Start backend in background
echo "🔧 Starting Backend API Server..."
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

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
    echo "❌ Backend failed to start after 30 seconds. Check the logs above."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend API Server running on http://localhost:8000"

# Start frontend
echo "🎨 Starting Frontend Development Server..."
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "⚙️ Creating environment configuration..."
    echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local
fi

npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "⏳ Waiting for frontend to initialize..."
sleep 10

echo ""
echo "🎉 TradingAgents Development Environment Started!"
echo "================================================"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Wait for user to press Ctrl+C
wait
