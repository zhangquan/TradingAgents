#!/bin/bash

echo "🚀 Starting TradingAgents Production Environment"
echo "==============================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Create production environment file for frontend
echo "⚙️ Creating production configuration..."
cat > frontend/.env.production.local <<EOF
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
EOF

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Check if services are running
echo "🔍 Checking service health..."

if ! curl -s http://localhost:8000/health >/dev/null; then
    echo "❌ Backend service is not responding. Check logs with: docker-compose logs backend"
    exit 1
fi

if ! curl -s http://localhost:3000 >/dev/null; then
    echo "❌ Frontend service is not responding. Check logs with: docker-compose logs frontend"
    exit 1
fi

echo ""
echo "🎉 TradingAgents Production Environment Started!"
echo "==============================================="
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🛠️  Management Commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart:       docker-compose restart"
echo "  Update:        docker-compose pull && docker-compose up -d"
