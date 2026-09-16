#!/bin/bash
set -e

echo "🚀 Initializing The Lenny Growth Assistant..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys before continuing!"
    exit 1
fi

# Source environment variables
set -a
source .env
set +a

# Check required API keys
if [ -z "$ANTHROPIC_API_KEY" ] && [ "$MODEL_PROVIDER" = "anthropic" ]; then
    echo "❌ Error: ANTHROPIC_API_KEY is required when MODEL_PROVIDER=anthropic"
    exit 1
fi

echo "🐳 Starting Docker containers..."
docker-compose up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

echo "📊 Running database migrations..."
docker-compose run --rm backend alembic upgrade head

echo "📥 Ingesting transcript data..."
docker-compose run --rm backend python scripts/ingest_transcripts.py

echo "🔢 Generating embeddings..."
docker-compose run --rm backend python scripts/generate_embeddings.py

echo "✅ Initialization complete!"
echo ""
echo "🎉 Starting all services..."
docker-compose up -d

echo ""
echo "=============================================="
echo "✅ The Lenny Growth Assistant is ready!"
echo "=============================================="
echo ""
echo "🌐 Frontend: http://localhost:5173"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "📝 View logs: docker-compose logs -f"
echo "🛑 Stop services: docker-compose down"
echo ""
