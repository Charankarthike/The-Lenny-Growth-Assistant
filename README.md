# 🚀 The Lenny Growth Assistant

An AI-powered conversational assistant built on Lenny Rachitsky's podcast transcripts, featuring RAG (Retrieval-Augmented Generation) for accurate, source-grounded answers about product growth, strategy, and entrepreneurship.

## ✨ Features

- **💬 Conversational Q&A**: Ask questions about growth strategies, product-market fit, retention tactics, and more from Lenny's podcast content
- **✍️ Ship 30 for 30 Content Generation**: Generate atomic essays (250 words) from episode insights
- **🔍 RAG-Powered Retrieval**: Answers grounded in actual transcript data with source citations
- **🎯 Multi-LLM Support**: Works with Anthropic Claude, Ollama (local), and OpenAI
- **📊 Vector Search**: PostgreSQL with pgvector for semantic similarity search
- **💾 Session Management**: Save and resume conversations
- **🎨 Modern React UI**: Clean, responsive interface with artifact viewer

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   React     │◄────►│   FastAPI    │◄────►│ PostgreSQL  │
│  Frontend   │      │   Backend    │      │  +pgvector  │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  LLM Layer   │
                     │ (Anthropic/  │
                     │  Ollama)     │
                     └──────────────┘
```

**Key Components**:
- **Backend**: FastAPI with async/await, SQLAlchemy, Alembic migrations
- **Database**: PostgreSQL 16 with pgvector extension for embeddings
- **Agent Layer**: Skill-based routing (conversational Q&A, Ship 30 for 30)
- **RAG System**: sentence-transformers embeddings, vector similarity search
- **Frontend**: React 18 + TypeScript + Vite + Zustand

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key (or Ollama for local LLM)

### One-Command Setup

```bash
# 1. Clone and navigate to the project
cd "The Lenny Growth Assistant"

# 2. Create .env file
cp .env.example .env

# 3. Edit .env and add your API keys
# Required: ANTHROPIC_API_KEY=your_key_here
nano .env

# 4. Run initialization script
./scripts/init.sh
```

The init script will:
1. Start PostgreSQL with pgvector
2. Run database migrations
3. Ingest sample transcript data
4. Generate embeddings
5. Start all services

**Access the application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📖 Manual Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example ../.env
# Edit .env with your settings

# Start PostgreSQL (must have pgvector extension)
# Update DATABASE_URL in .env to point to your PostgreSQL

# Run migrations
alembic upgrade head

# Ingest data
python scripts/ingest_transcripts.py
python scripts/generate_embeddings.py

# Start server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## 🎯 Usage

### Starting a Conversation

1. Open http://localhost:5173
2. Click "+ New" to create a session
3. Ask questions or request content generation

### Example Queries

**Conversational Q&A**:
- "What are the key growth strategies discussed?"
- "Tell me about product-market fit"
- "How do successful companies improve retention?"

**Ship 30 for 30 Generation**:
- "Generate a Ship 30 for 30 essay about viral loops"
- "Write an atomic essay on network effects"
- "Create a 250-word essay about customer acquisition"

## 🔧 Configuration

### Environment Variables

Key settings in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/lenny_assistant

# LLM Configuration
MODEL_PROVIDER=anthropic  # anthropic, ollama, or openai
MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_key_here

# Embeddings
EMBEDDING_PROVIDER=local  # local or openai
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Retrieval
TOP_K_RESULTS=5
SIMILARITY_THRESHOLD=0.3

# Optional: Ollama (for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

### Switching LLM Providers

**Use Anthropic Claude** (recommended):
```bash
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=your_key
```

**Use Ollama** (local, no API key needed):
```bash
MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
# Install: brew install ollama && ollama pull llama2
```

**Use OpenAI**:
```bash
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4
OPENAI_API_KEY=your_key
```

## 📁 Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Configuration
│   │   ├── api/v1/              # API endpoints
│   │   ├── db/                  # Database models & repos
│   │   ├── agent/               # Agent orchestration
│   │   ├── llm/                 # LLM providers
│   │   ├── retrieval/           # RAG & embeddings
│   │   └── ingestion/           # Data loading
│   ├── scripts/                 # CLI tools
│   ├── tests/                   # Test suite
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── api.ts               # API client
│   │   ├── store.ts             # State management
│   │   └── types.ts             # TypeScript types
│   ├── package.json
│   └── vite.config.ts
├── data/transcripts/            # Sample transcript data
├── docs/                        # Design documentation
├── agent-transcripts/           # Agent execution logs
├── docker-compose.yml
└── README.md
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Manual Testing

```bash
# Test retrieval
python scripts/test_retrieval.py "product market fit"

# Test ingestion
python -m pytest tests/test_ingestion.py

# Test API
curl http://localhost:8000/api/v1/config
```

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose up -d --build

# Access backend shell
docker-compose exec backend bash

# Run migrations
docker-compose exec backend alembic upgrade head

# Reset database (WARNING: deletes all data)
docker-compose down -v
./scripts/init.sh
```

## 📊 Database Schema

**Core Tables**:
- `sessions` - Chat sessions
- `messages` - User and assistant messages
- `transcripts` - Episode metadata
- `transcript_chunks` - Text chunks with embeddings (pgvector)
- `artifacts` - Generated content (essays, analyses)

**Vector Search**:
```sql
-- Find similar chunks
SELECT content, metadata, 
       1 - (embedding <=> query_embedding) as similarity
FROM transcript_chunks
WHERE 1 - (embedding <=> query_embedding) > 0.3
ORDER BY embedding <=> query_embedding
LIMIT 5;
```

## 🎨 Frontend Components

- **Layout**: Main app layout with sidebar
- **SessionList**: Session management sidebar
- **ChatInterface**: Main chat area
- **MessageBubble**: Individual message display
- **MessageInput**: Text input with auto-resize
- **SourceDisplay**: Show retrieval sources
- **ArtifactViewer**: Expandable artifact renderer

## 🔍 API Endpoints

```
GET  /api/v1/config              # Get configuration
GET  /api/v1/sessions            # List sessions
POST /api/v1/sessions            # Create session
GET  /api/v1/sessions/{id}/messages  # Get messages
POST /api/v1/sessions/{id}/messages  # Send message
POST /api/v1/retrieval/search    # Search transcripts
```

See full API documentation at http://localhost:8000/docs

## 🤖 Agent Skills

### Conversational Q&A Skill
- Retrieves relevant transcript chunks
- Generates natural, source-grounded answers
- Includes citations with similarity scores

### Ship 30 for 30 Skill
- Generates atomic essays (~250 words)
- Hook → Body → Conclusion structure
- Based on episode insights
- Stored as artifacts for reuse

## 📈 Performance & Optimization

- **Embeddings**: Cached in database, batch generation
- **Vector Search**: pgvector HNSW index for fast similarity
- **Connection Pooling**: SQLAlchemy async engine
- **Streaming**: Supports LLM streaming (not yet in UI)
- **Pagination**: API supports offset/limit for large result sets

## 🔐 Security Considerations

- API keys stored in environment variables
- Database credentials not committed to git
- CORS configured for frontend origin
- Input validation on all endpoints
- SQL injection prevented via SQLAlchemy ORM

## 🚧 Known Limitations

- Sample data includes only 2 mock transcripts
- Frontend markdown rendering is basic
- No authentication/authorization
- Single-user focused (no multi-tenancy)
- Embeddings are local model (small, fast, but less accurate than OpenAI)

## 🛠️ Troubleshooting

**Backend won't start**:
```bash
# Check logs
docker-compose logs backend

# Verify database connection
docker-compose exec backend python -c "from app.db.database import engine; print('OK')"
```

**No embeddings generated**:
```bash
# Regenerate embeddings
docker-compose exec backend python scripts/generate_embeddings.py
```

**Frontend can't connect to backend**:
- Verify backend is running: http://localhost:8000/health
- Check VITE_API_URL in .env matches backend URL
- Verify CORS settings in backend/app/main.py

**Docker disk space issues**:
```bash
# Clean up unused images/volumes
docker system prune -a
```

## 📚 Documentation

- **[PRD.md](docs/PRD.md)**: Product requirements
- **[architecture.md](docs/architecture.md)**: System design
- **[design.md](docs/design.md)**: Technical design decisions
- **[agent-transcripts/](agent-transcripts/)**: Agent execution logs

## 🤝 Contributing

This is a take-home assignment project. For production use:
1. Add authentication/authorization
2. Implement real transcript ingestion pipeline
3. Add comprehensive test coverage
4. Set up CI/CD
5. Add monitoring and observability
6. Implement rate limiting

## 📝 License

This project was created as a take-home assignment for a Forward Deployed Engineer role.

## 🙏 Acknowledgments

- Built for analysis of Lenny Rachitsky's podcast content
- Powered by Anthropic Claude, pgvector, FastAPI, and React
- Ship 30 for 30 format inspired by Dickie Bush and Nicolas Cole

---

**Built with ❤️ for the Forward Deployed Engineer take-home assignment**

For questions or issues, please refer to the documentation in the `docs/` directory.
