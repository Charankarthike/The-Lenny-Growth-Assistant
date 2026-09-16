# Deployment & Verification Guide

## Pre-Deployment Checklist

### Required Setup
- [ ] Docker and Docker Compose installed
- [ ] Anthropic API key obtained (or Ollama installed for local LLM)
- [ ] `.env` file created from `.env.example`
- [ ] API keys added to `.env` file

### Environment Configuration

```bash
# Required for Anthropic (recommended)
ANTHROPIC_API_KEY=sk-ant-...

# OR for local Ollama
# Install: brew install ollama && ollama pull llama2
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2

# Database (defaults work for Docker)
POSTGRES_USER=lenny_user
POSTGRES_PASSWORD=lenny_password
POSTGRES_DB=lenny_assistant

# Embeddings (local is default, no API key needed)
EMBEDDING_PROVIDER=local
```

## Quick Start Deployment

### Option 1: Automated Setup (Recommended)

```bash
cd "The Lenny Growth Assistant"

# 1. Create environment file
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# 2. Run initialization script
chmod +x scripts/init.sh
./scripts/init.sh
```

The script will:
1. Start PostgreSQL
2. Run database migrations
3. Ingest sample transcripts
4. Generate embeddings
5. Start all services

**Expected Output:**
```
✅ The Lenny Growth Assistant is ready!
🌐 Frontend: http://localhost:5173
🔧 Backend API: http://localhost:8000
📚 API Docs: http://localhost:8000/docs
```

### Option 2: Manual Step-by-Step

```bash
# 1. Start PostgreSQL only
docker-compose up -d postgres

# 2. Wait for database to be ready
sleep 10

# 3. Run migrations
docker-compose run --rm backend alembic upgrade head

# 4. Ingest data
docker-compose run --rm backend python scripts/ingest_transcripts.py

# 5. Generate embeddings
docker-compose run --rm backend python scripts/generate_embeddings.py

# 6. Start all services
docker-compose up -d
```

## Verification Steps

### 1. Backend Health Check

```bash
# Check backend is running
curl http://localhost:8000/health

# Expected: {"status":"healthy"}
```

### 2. Database Verification

```bash
# Access database
docker-compose exec postgres psql -U lenny_user -d lenny_assistant

# Check tables exist
\dt

# Expected tables:
# - sessions
# - messages  
# - transcripts
# - transcript_chunks
# - artifacts
# - alembic_version

# Check data was ingested
SELECT COUNT(*) FROM transcripts;
# Expected: 2

SELECT COUNT(*) FROM transcript_chunks;
# Expected: ~50-100 chunks

# Exit psql
\q
```

### 3. API Endpoints Test

```bash
# Test configuration endpoint
curl http://localhost:8000/api/v1/config | jq

# Test retrieval search
curl -X POST http://localhost:8000/api/v1/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "product market fit", "top_k": 3}' | jq

# Test session creation
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Session"}' | jq
```

### 4. Frontend Verification

1. Open http://localhost:5173 in browser
2. Verify UI loads without errors
3. Click "+ New" to create a session
4. Type a test message: "What is product-market fit?"
5. Verify assistant responds with sources
6. Try Ship 30 request: "Generate a Ship 30 essay about retention"
7. Verify artifact is displayed

### 5. End-to-End Test

**Conversational Q&A:**
```
User: "What are the key strategies for achieving product-market fit?"
Expected: Assistant responds with insights from transcripts, shows 3-5 sources
```

**Ship 30 for 30:**
```
User: "Write a Ship 30 for 30 essay about pricing strategy"
Expected: Assistant generates ~250-word atomic essay with hook, body, conclusion
```

## Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Check Container Status

```bash
docker-compose ps

# Expected output shows all services as "Up"
```

## Troubleshooting

### Issue: Backend won't start

```bash
# Check logs
docker-compose logs backend

# Common causes:
# 1. Database not ready - wait 10s and retry
# 2. Missing API key - check .env file
# 3. Port conflict - check if 8000 is in use

# Fix: Restart services
docker-compose restart backend
```

### Issue: No embeddings generated

```bash
# Regenerate embeddings
docker-compose exec backend python scripts/generate_embeddings.py

# Check progress
docker-compose exec backend python -c "
from app.db.database import get_db
from app.db.models import TranscriptChunk
from sqlalchemy import select, func

with next(get_db()) as db:
    result = db.execute(
        select(
            func.count(TranscriptChunk.chunk_id),
            func.count(TranscriptChunk.embedding)
        )
    ).first()
    print(f'Total chunks: {result[0]}, With embeddings: {result[1]}')
"
```

### Issue: Frontend can't connect to backend

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in `backend/app/main.py`
3. Verify `VITE_API_URL` in frontend `.env` or `vite.config.ts`
4. Check browser console for errors

### Issue: "Module not found" errors

```bash
# Backend
docker-compose exec backend pip install -r requirements.txt

# Frontend
docker-compose exec frontend npm install

# Or rebuild containers
docker-compose up -d --build
```

### Issue: Database connection errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check DATABASE_URL in .env matches postgres container
# Should be: postgresql://lenny_user:lenny_password@postgres:5432/lenny_assistant

# Restart database
docker-compose restart postgres
sleep 10
docker-compose restart backend
```

## Performance Checks

### Embedding Generation Time
```bash
# Should complete in 30-60 seconds for sample data
time docker-compose exec backend python scripts/generate_embeddings.py
```

### Retrieval Speed
```bash
# Should return in <1 second
time curl -X POST http://localhost:8000/api/v1/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "retention tactics", "top_k": 5}'
```

### Agent Response Time
- First message: 3-5 seconds (includes retrieval + LLM)
- Subsequent messages: 2-4 seconds
- Ship 30 generation: 5-10 seconds (longer content)

## Cleanup & Reset

### Stop Services
```bash
docker-compose down
```

### Reset Everything (WARNING: Deletes all data)
```bash
docker-compose down -v
rm -rf backend/alembic/versions/*.py  # Keep .gitkeep
./scripts/init.sh  # Start fresh
```

### Remove Docker Images
```bash
docker-compose down --rmi all
```

## Production Considerations

### Not Included (Demo Scope)
- [ ] Authentication/Authorization
- [ ] Rate limiting
- [ ] HTTPS/SSL certificates
- [ ] Production database tuning
- [ ] CDN for frontend
- [ ] Monitoring/alerting
- [ ] Backup strategy
- [ ] Load balancing
- [ ] CI/CD pipeline

### Security Notes
- API keys in `.env` (not committed to git)
- No authentication (single-user demo)
- CORS configured for localhost only
- pgvector extension runs with database privileges

## Success Criteria

✅ **Deployment is successful when:**
1. All Docker containers are running (green status)
2. Backend health check returns `{"status":"healthy"}`
3. Frontend loads at http://localhost:5173
4. Can create new session
5. Can send message and receive response with sources
6. Can generate Ship 30 essay artifact
7. Database contains transcripts and embeddings
8. No errors in `docker-compose logs`

## Support

If issues persist:
1. Check logs: `docker-compose logs -f`
2. Review README.md troubleshooting section
3. Verify all environment variables in `.env`
4. Ensure Docker has sufficient resources (4GB+ RAM)
5. Try clean restart: `docker-compose down && docker-compose up -d`

---

**Last Updated:** 2026-09-16  
**Version:** 1.0  
**Status:** Ready for deployment
