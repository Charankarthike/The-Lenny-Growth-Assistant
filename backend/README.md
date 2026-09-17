# Lenny Growth Assistant - Backend API

Production-ready backend for The Lenny Growth Assistant with RAG capabilities.

## Features

- ✅ FastAPI REST API
- ✅ PostgreSQL with pgvector for vector search
- ✅ OpenAI integration (GPT-4o-mini + embeddings)
- ✅ RAG (Retrieval Augmented Generation)
- ✅ Minimal dependencies (all pre-built wheels)
- ✅ Deployment-ready for Render, Railway, or Vercel

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/lenny_assistant
OPENAI_API_KEY=your-api-key-here
```

### 3. Initialize Database

```bash
python scripts/init_database.py
```

### 4. Load Sample Data (Optional)

```bash
python scripts/load_sample_data.py
```

### 5. Run the Server

```bash
python -m app.main
```

Or with uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Health Check
```
GET /health
```

### Chat (with RAG)
```
POST /api/chat

Request:
{
  "messages": [
    {"role": "user", "content": "What is Ship 30 for 30?"}
  ],
  "use_rag": true,
  "stream": false
}

Response:
{
  "response": "Ship 30 for 30 is a framework for...",
  "sources": [
    {
      "title": "Ship 30 for 30 Framework",
      "content": "...",
      "episode": "002",
      "relevance_score": 0.92
    }
  ],
  "model_used": "gpt-4o-mini"
}
```

## Scripts

- `scripts/init_database.py` - Initialize database tables and enable pgvector
- `scripts/load_sample_data.py` - Load sample transcripts with embeddings
- `scripts/check_data.py` - Check what data exists in database

## Deployment

### Render

1. Create PostgreSQL database on Render
2. Create Web Service connected to this repo
3. Set environment variables:
   - `DATABASE_URL` (from PostgreSQL internal URL)
   - `OPENAI_API_KEY`
   - `PORT=10000`
4. Deploy!

### Railway

1. Create PostgreSQL plugin
2. Create service from GitHub repo
3. Set environment variables
4. Deploy!

## Project Structure

```
backend/
├── app/
│   ├── core/          # Config, database
│   ├── models/        # SQLAlchemy & Pydantic models
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic (OpenAI, RAG)
│   └── main.py        # FastAPI app
├── scripts/           # Data management scripts
├── requirements.txt   # Python dependencies
└── runtime.txt        # Python version
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | Required |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `ENVIRONMENT` | Environment (production/development) | production |
| `PORT` | Server port | 8000 |
| `CORS_ORIGINS` | Allowed CORS origins | * |
| `EMBEDDING_MODEL` | OpenAI embedding model | text-embedding-3-small |
| `LLM_MODEL` | OpenAI chat model | gpt-4o-mini |
| `TOP_K_RESULTS` | Number of RAG results | 5 |

## License

MIT
