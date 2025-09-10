#!/bin/bash

echo "🚀 Starting TradingAgents Production Environment (Native)"
echo "======================================================="

# Set production environment variables
export NODE_ENV=production
export PYTHON_ENV=production
export UV_CACHE_DIR=~/.cache/uv

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=60
    local attempt=1

    print_info "Waiting for $service_name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            print_status "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    print_error "$service_name failed to start after $max_attempts seconds"
    return 1
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_info "Stopping services..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        print_status "Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        print_status "Frontend stopped"
    fi
    exit 0
}

# Trap Ctrl+C and other signals
trap cleanup INT TERM

# Check prerequisites
print_info "Checking prerequisites..."

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
    print_error "uv is not installed. Please install uv first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node >/dev/null 2>&1; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm >/dev/null 2>&1; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

print_status "All prerequisites are installed"

# Check if ports are available
print_info "Checking port availability..."

if check_port 8000; then
    print_error "Port 8000 is already in use. Please stop the service and try again."
    echo "You can find what's using the port with: lsof -i :8000"
    exit 1
fi

if check_port 3000; then
    print_error "Port 3000 is already in use. Please stop the service and try again."
    echo "You can find what's using the port with: lsof -i :3000"
    exit 1
fi

print_status "Ports 8000 and 3000 are available"

# Create logs directory
mkdir -p logs
mkdir -p data

# Create production environment configuration
print_info "Setting up production environment configuration..."

# Create backend .env file for production if it doesn't exist
if [ ! -f ".env" ]; then
    cat > .env <<EOF
# Production Environment Configuration
PYTHON_ENV=production
NODE_ENV=production

# Database Configuration
DATABASE_URL=sqlite:///./data/tradingagents.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/tradingagents.log

# Cache Configuration
CACHE_TTL=3600

# Security Configuration
SECRET_KEY=your-secret-key-change-in-production
CORS_ORIGINS=http://localhost:3000

# External APIs (configure as needed)
# POLYGON_API_KEY=your_polygon_api_key
# FINNHUB_API_KEY=your_finnhub_api_key
# REDDIT_CLIENT_ID=your_reddit_client_id
# REDDIT_CLIENT_SECRET=your_reddit_client_secret
EOF
    print_warning "Created .env file with default configuration. Please update with your actual API keys."
fi

# Install/Update Python dependencies
print_info "Installing Python dependencies with uv..."
if ! uv sync; then
    print_error "Failed to install Python dependencies"
    exit 1
fi
print_status "Python dependencies installed"

# Install/Update Node.js dependencies
print_info "Installing Node.js dependencies..."
cd frontend

if [ ! -d "node_modules" ] || [ ! -f "package-lock.json" ]; then
    if ! npm ci; then
        print_error "Failed to install Node.js dependencies"
        exit 1
    fi
else
    print_info "Node.js dependencies already installed"
fi

# Create frontend production environment file
cat > .env.production.local <<EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=production
EOF

print_status "Frontend environment configured"

# Build frontend for production
print_info "Building frontend for production..."
if ! npm run build; then
    print_error "Frontend build failed"
    exit 1
fi
print_status "Frontend build completed"

cd ..

# Initialize database if needed
print_info "Initializing database..."
uv run python -c "
from backend.database.init_db import init_database
init_database()
print('Database initialized')
" 2>/dev/null || print_warning "Database initialization may have failed (this might be normal if already initialized)"

# Start backend service
print_info "Starting backend API server..."
uv run uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --access-log \
    --log-level info \
    --no-server-header \
    > logs/backend.log 2>&1 &

BACKEND_PID=$!
print_status "Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8000/health" "Backend API"; then
    print_error "Backend failed to start. Check logs/backend.log for details."
    cleanup
    exit 1
fi

# Start frontend service
print_info "Starting frontend server..."
cd frontend
npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

print_status "Frontend started with PID: $FRONTEND_PID"

# Wait for frontend to be ready
if ! wait_for_service "http://localhost:3000" "Frontend"; then
    print_error "Frontend failed to start. Check logs/frontend.log for details."
    cleanup
    exit 1
fi

# Display startup summary
echo ""
echo "🎉 TradingAgents Production Environment Started Successfully!"
echo "==========================================================="
echo -e "${GREEN}🌐 Frontend:     http://localhost:3000${NC}"
echo -e "${GREEN}🔧 Backend API:  http://localhost:8000${NC}"
echo -e "${GREEN}📚 API Docs:     http://localhost:8000/docs${NC}"
echo -e "${GREEN}📊 Health Check: http://localhost:8000/health${NC}"
echo ""
echo -e "${BLUE}📁 Log Files:${NC}"
echo -e "   Backend:  logs/backend.log"
echo -e "   Frontend: logs/frontend.log"
echo ""
echo -e "${BLUE}🛠️  Management Commands:${NC}"
echo -e "   View backend logs:  tail -f logs/backend.log"
echo -e "   View frontend logs: tail -f logs/frontend.log"
echo -e "   Monitor processes:  ps aux | grep -E '(uvicorn|node)'"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Monitor services and wait for interrupt
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        print_error "Backend process died unexpectedly!"
        cleanup
        exit 1
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        print_error "Frontend process died unexpectedly!"
        cleanup
        exit 1
    fi
    
    sleep 5
done
