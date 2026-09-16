# Lenny Growth Assistant - Backend

FastAPI backend for the Lenny Growth Assistant, providing RAG-powered conversational AI with session management, vector search, and LLM integration.

## Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── logging_config.py    # Structured logging setup
│   ├── middleware.py        # Custom middleware
│   ├── api/                 # API endpoints
│   │   └── v1/
│   │       ├── router.py    # Main API router
│   │       ├── config.py    # Config endpoints
│   │       ├── sessions.py  # Session management
│   │       └── messages.py  # Message handling
│   ├── db/                  # Database models and repositories (TBD)
│   ├── agent/               # Agent layer and skills (TBD)
│   ├── retrieval/           # RAG and vector search (TBD)
│   └── llm/                 # LLM provider integrations (TBD)
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container image
├── .env.example            # Environment variable template
└── test_main.py            # Basic tests
```

## Prerequisites

- Python 3.11+
- PostgreSQL 16+ with pgvector extension
- Ollama (for local models) or API keys for Anthropic/OpenAI

## Quick Start

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `LLM_PROVIDER`: Choose "ollama", "anthropic", or "openai"
- `OLLAMA_BASE_URL`: URL for Ollama server (default: http://localhost:11434)
- For cloud providers, set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

### 3. Set Up Database

Make sure PostgreSQL 16+ with pgvector extension is installed and running.

**Create the database:**
```bash
createdb lenny_assistant
```

**Or using psql:**
```sql
CREATE DATABASE lenny_assistant;
```

**Initialize tables:**
```bash
python -m app.db.init_db
```

**Or use Alembic migrations (recommended for production):**
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or using Python directly:

```bash
python -m app.main
```

### 4. Verify Installation

Open your browser to:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Root: http://localhost:8000/

## API Endpoints

### Health & Configuration

- `GET /health` - System health status
- `GET /` - API information
- `GET /api/v1/config` - Current configuration

### Sessions

- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions` - List all sessions
- `GET /api/v1/sessions/{id}` - Get specific session
- `DELETE /api/v1/sessions/{id}` - Delete session

### Messages

- `POST /api/v1/sessions/{id}/messages` - Send message
- `GET /api/v1/sessions/{id}/messages` - Get message history

## Testing

Run tests with pytest:

```bash
pytest test_main.py -v
```

With coverage:

```bash
pytest test_main.py --cov=app --cov-report=html
```

## Development

### Code Style

Format code with Black:

```bash
black app/
```

Lint with Flake8:

```bash
flake8 app/
```

Type check with MyPy:

```bash
mypy app/
```

### Logging

Structured logging is configured using `structlog`. Logs are output in JSON format by default (or console format in development).

Key logged events:
- `request_started` / `request_completed` - HTTP requests
- `application_startup` / `application_shutdown` - Lifecycle events
- `creating_session` / `processing_message` - Business logic

Each log entry includes:
- `timestamp`: ISO 8601 format
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `service`: Application name
- `correlation_id`: Request tracking ID

### Adding New Endpoints

1. Create a new router file in `app/api/v1/`
2. Define request/response models using Pydantic
3. Implement endpoint functions
4. Include router in `app/api/v1/router.py`

Example:

```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class MyRequest(BaseModel):
    data: str

@router.post("/my-endpoint")
async def my_endpoint(request: MyRequest):
    return {"result": f"Processed: {request.data}"}
```

## Configuration

All configuration is managed through environment variables and the `Settings` class in `app/config.py`.

### LLM Provider Configuration

**Ollama (Local):**
```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

**Anthropic Claude:**
```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**OpenAI:**
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### Embedding Configuration

**Local (sentence-transformers):**
```env
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

**OpenAI:**
```env
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
# Uses text-embedding-ada-002 (1536 dimensions)
```

## Troubleshooting

### "Module not found" errors

Ensure you're in the virtual environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "Connection refused" to Ollama

Make sure Ollama is running:
```bash
ollama serve
```

In another terminal:
```bash
ollama pull llama3.1:8b
```

### Database connection errors

Verify PostgreSQL is running and accessible:
```bash
psql -h localhost -U lenny_user -d lenny_assistant
```

Check `DATABASE_URL` format:
```
postgresql://user:password@host:port/database
```

### Import errors in tests

Run tests as a module:
```bash
python -m pytest test_main.py
```

## Next Steps

This is the foundational backend structure. Completed phases:
- [x] Database models and migrations (SQLAlchemy + Alembic)
- [x] Transcript ingestion and chunking
- [x] Vector search with pgvector and embeddings
- [ ] Agent layer with skills
- [ ] Ship 30 for 30 content generation
- [ ] Streaming response support
- [ ] Full test coverage

## Ingesting Transcripts

After setting up the database, ingest Lenny's Podcast transcripts:

```bash
# Place transcript files in data/transcripts/
# Supported formats: .json, .md, .html, .txt

# Run ingestion
python scripts/ingest_transcripts.py

# Or specify custom path
python scripts/ingest_transcripts.py --data-path /path/to/transcripts

# Force re-ingestion
python scripts/ingest_transcripts.py --force
```

Sample transcript files are included in `data/transcripts/` for testing.

## Generating Embeddings

After ingestion, generate vector embeddings for semantic search:

```bash
# Generate embeddings for all chunks
python scripts/generate_embeddings.py

# Use larger batch size for faster processing
python scripts/generate_embeddings.py --batch-size 64

# Regenerate all embeddings (force)
python scripts/generate_embeddings.py --force
```

**Note:** The first run will download the embedding model (~120MB for MiniLM).

## Testing Retrieval

Test the RAG retrieval system:

```bash
# Interactive mode
python scripts/test_retrieval.py

# Test specific query
python scripts/test_retrieval.py "What is product-market fit?"

# Run all sample queries
python scripts/test_retrieval.py --all-samples

# Adjust number of results
python scripts/test_retrieval.py --top-k 5
```

## License

Proprietary - Forward Deployed Engineer Take-Home Assignment
