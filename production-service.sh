#!/bin/bash

# TradingAgents Production Service Management Script
# Usage: ./production-service.sh {start|stop|restart|status|logs}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$SCRIPT_DIR/pids"
LOG_DIR="$SCRIPT_DIR/logs"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"

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

# Function to check if a process is running
is_running() {
    local pid_file=$1
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0  # Process is running
        else
            rm -f "$pid_file"  # Remove stale PID file
            return 1  # Process is not running
        fi
    else
        return 1  # PID file doesn't exist
    fi
}

# Function to start backend service
start_backend() {
    if is_running "$BACKEND_PID_FILE"; then
        print_warning "Backend is already running (PID: $(cat $BACKEND_PID_FILE))"
        return 0
    fi
    
    print_info "Starting backend service..."
    
    # Set production environment
    export NODE_ENV=production
    export PYTHON_ENV=production
    
    # Start backend with uv
    cd "$SCRIPT_DIR"
    nohup uv run uvicorn backend.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers 4 \
        --access-log \
        --log-level info \
        --no-server-header \
        > "$LOG_DIR/backend.log" 2>&1 &
    
    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID_FILE"
    
    # Wait for backend to start
    sleep 3
    if is_running "$BACKEND_PID_FILE"; then
        print_status "Backend started successfully (PID: $backend_pid)"
        
        # Wait for health check
        local attempts=0
        while [ $attempts -lt 30 ]; do
            if curl -s http://localhost:8000/health >/dev/null 2>&1; then
                print_status "Backend health check passed"
                return 0
            fi
            sleep 1
            ((attempts++))
        done
        print_warning "Backend started but health check failed"
        return 1
    else
        print_error "Failed to start backend"
        return 1
    fi
}

# Function to start frontend service
start_frontend() {
    if is_running "$FRONTEND_PID_FILE"; then
        print_warning "Frontend is already running (PID: $(cat $FRONTEND_PID_FILE))"
        return 0
    fi
    
    print_info "Starting frontend service..."
    
    cd "$SCRIPT_DIR/frontend"
    
    # Check if build exists
    if [ ! -d ".next" ]; then
        print_info "Building frontend..."
        if ! npm run build; then
            print_error "Frontend build failed"
            return 1
        fi
    fi
    
    # Create production environment file
    cat > .env.production.local <<EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NODE_ENV=production
EOF
    
    # Start frontend
    nohup npm start > "$LOG_DIR/frontend.log" 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$FRONTEND_PID_FILE"
    
    cd "$SCRIPT_DIR"
    
    # Wait for frontend to start
    sleep 5
    if is_running "$FRONTEND_PID_FILE"; then
        print_status "Frontend started successfully (PID: $frontend_pid)"
        
        # Wait for frontend to be ready
        local attempts=0
        while [ $attempts -lt 30 ]; do
            if curl -s http://localhost:3000 >/dev/null 2>&1; then
                print_status "Frontend is ready"
                return 0
            fi
            sleep 1
            ((attempts++))
        done
        print_warning "Frontend started but not responding"
        return 1
    else
        print_error "Failed to start frontend"
        return 1
    fi
}

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if is_running "$pid_file"; then
        local pid=$(cat "$pid_file")
        print_info "Stopping $service_name (PID: $pid)..."
        
        # Try graceful shutdown first
        kill "$pid"
        
        # Wait up to 10 seconds for graceful shutdown
        local attempts=0
        while [ $attempts -lt 10 ] && kill -0 "$pid" 2>/dev/null; do
            sleep 1
            ((attempts++))
        done
        
        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Forcefully stopping $service_name..."
            kill -9 "$pid"
        fi
        
        rm -f "$pid_file"
        print_status "$service_name stopped"
    else
        print_info "$service_name is not running"
    fi
}

# Function to show service status
show_status() {
    echo "TradingAgents Service Status"
    echo "============================"
    
    if is_running "$BACKEND_PID_FILE"; then
        local backend_pid=$(cat "$BACKEND_PID_FILE")
        print_status "Backend: Running (PID: $backend_pid)"
        
        # Check health
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            print_status "Backend Health: OK"
        else
            print_error "Backend Health: FAILED"
        fi
    else
        print_error "Backend: Not running"
    fi
    
    if is_running "$FRONTEND_PID_FILE"; then
        local frontend_pid=$(cat "$FRONTEND_PID_FILE")
        print_status "Frontend: Running (PID: $frontend_pid)"
        
        # Check if frontend is responding
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            print_status "Frontend Health: OK"
        else
            print_error "Frontend Health: FAILED"
        fi
    else
        print_error "Frontend: Not running"
    fi
    
    echo ""
    echo "Service URLs:"
    echo "  Frontend:  http://localhost:3000"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
}

# Function to show logs
show_logs() {
    local service=$1
    
    case $service in
        backend)
            if [ -f "$LOG_DIR/backend.log" ]; then
                tail -f "$LOG_DIR/backend.log"
            else
                print_error "Backend log file not found"
            fi
            ;;
        frontend)
            if [ -f "$LOG_DIR/frontend.log" ]; then
                tail -f "$LOG_DIR/frontend.log"
            else
                print_error "Frontend log file not found"
            fi
            ;;
        *)
            echo "Available logs:"
            echo "  backend  - Show backend logs"
            echo "  frontend - Show frontend logs"
            echo ""
            echo "Usage: $0 logs {backend|frontend}"
            ;;
    esac
}

# Main script logic
case "$1" in
    start)
        print_info "Starting TradingAgents services..."
        
        # Initialize database
        print_info "Initializing database..."
        cd "$SCRIPT_DIR"
        uv run python -c "
from backend.database.init_db import init_database
init_database()
print('Database initialized')
" 2>/dev/null || print_warning "Database initialization may have failed"
        
        if start_backend && start_frontend; then
            print_status "All services started successfully!"
            echo ""
            show_status
        else
            print_error "Failed to start some services"
            exit 1
        fi
        ;;
    stop)
        print_info "Stopping TradingAgents services..."
        stop_service "Frontend" "$FRONTEND_PID_FILE"
        stop_service "Backend" "$BACKEND_PID_FILE"
        print_status "All services stopped"
        ;;
    restart)
        print_info "Restarting TradingAgents services..."
        stop_service "Frontend" "$FRONTEND_PID_FILE"
        stop_service "Backend" "$BACKEND_PID_FILE"
        sleep 2
        
        if start_backend && start_frontend; then
            print_status "All services restarted successfully!"
            echo ""
            show_status
        else
            print_error "Failed to restart some services"
            exit 1
        fi
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    *)
        echo "TradingAgents Production Service Manager"
        echo "======================================="
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Show service logs (backend|frontend)"
        echo ""
        echo "Examples:"
        echo "  $0 start"
        echo "  $0 status"
        echo "  $0 logs backend"
        echo "  $0 restart"
        exit 1
        ;;
esac
