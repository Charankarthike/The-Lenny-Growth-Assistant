# Architecture Documentation: The Lenny Growth Assistant

## System Overview

The Lenny Growth Assistant is a full-stack AI-powered conversational application built on a modern RAG (Retrieval-Augmented Generation) architecture. The system consists of four primary layers:

1. **Frontend Layer:** React-based chat interface with artifact viewer
2. **API Layer:** FastAPI backend with RESTful endpoints
3. **Agent Layer:** Skill-based routing using Anthropic Claude Agent SDK
4. **Data Layer:** PostgreSQL for persistence, vector store for retrieval

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  ┌──────────────────┐         ┌──────────────────┐         │
│  │  Chat Interface  │         │ Artifact Viewer  │         │
│  └──────────────────┘         └──────────────────┘         │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  ┌──────────────┬───────────────┬──────────────────────┐   │
│  │   Session    │   Message     │   Configuration      │   │
│  │   Manager    │   Handler     │   Manager            │   │
│  └──────────────┴───────────────┴──────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Agent     │  │  Retrieval  │  │  Database   │
│   Layer     │  │   Engine    │  │ PostgreSQL  │
│  (Claude)   │  │   (RAG)     │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
         │               │
         ▼               ▼
┌─────────────┐  ┌─────────────┐
│ LLM Provider│  │   Vector    │
│ Cloud/Local │  │   Store     │
└─────────────┘  └─────────────┘
```

---

## Database Schema

### PostgreSQL Tables

#### 1. `sessions` Table
Stores conversation session metadata.

```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    title VARCHAR(255),
    model_provider VARCHAR(50) NOT NULL,  -- 'anthropic', 'openai', 'ollama'
    model_name VARCHAR(100) NOT NULL,     -- e.g., 'claude-3-5-sonnet-20241022'
    metadata JSONB DEFAULT '{}'::jsonb,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_sessions_created_at ON sessions(created_at DESC);
CREATE INDEX idx_sessions_is_active ON sessions(is_active);
```

**Design Rationale:**
- UUID for globally unique identifiers (supports distributed systems)
- Separate `model_provider` and `model_name` for flexible LLM configuration
- JSONB metadata for extensibility (user tags, categories, etc.)
- `is_active` flag for soft deletion and archival

#### 2. `messages` Table
Stores individual messages within sessions.

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    token_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,  -- sources, artifacts, tool_calls
    
    CONSTRAINT valid_role CHECK (role IN ('user', 'assistant', 'system'))
);

CREATE INDEX idx_messages_session_id ON messages(session_id, created_at);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

**Design Rationale:**
- Foreign key with CASCADE delete ensures orphan cleanup
- `role` field follows OpenAI/Anthropic message format conventions
- `token_count` for usage tracking and cost estimation
- JSONB metadata stores:
  - `sources`: Array of transcript citations
  - `artifacts`: Generated content metadata (type, title, content)
  - `tool_calls`: Agent actions for debugging

#### 3. `transcripts` Table
Stores Lenny's Podcast episode metadata and content.

```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    episode_number INTEGER UNIQUE,
    title VARCHAR(500) NOT NULL,
    guest_name VARCHAR(200),
    publish_date DATE,
    duration_minutes INTEGER,
    full_text TEXT NOT NULL,
    summary TEXT,
    topics TEXT[],  -- Array of topic tags
    url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transcripts_episode_number ON transcripts(episode_number);
CREATE INDEX idx_transcripts_publish_date ON transcripts(publish_date DESC);
CREATE INDEX idx_transcripts_guest_name ON transcripts(guest_name);
CREATE INDEX idx_transcripts_topics ON transcripts USING GIN(topics);
CREATE INDEX idx_transcripts_full_text_search ON transcripts USING GIN(to_tsvector('english', full_text));
```

**Design Rationale:**
- Full-text search index for keyword matching
- GIN index on topics array for efficient filtering
- Separate summary field for quick preview (generated via LLM)
- URL field for source attribution and verification

#### 4. `transcript_chunks` Table
Stores chunked and embedded transcript segments for retrieval.

```sql
CREATE TABLE transcript_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding vector(1536),  -- Assumes OpenAI ada-002 or similar
    metadata JSONB DEFAULT '{}'::jsonb,  -- speaker, timestamp, context_before, context_after
    
    UNIQUE(transcript_id, chunk_index)
);

CREATE INDEX idx_chunks_transcript_id ON transcript_chunks(transcript_id);
CREATE INDEX idx_chunks_embedding ON transcript_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Design Rationale:**
- Uses `pgvector` extension for native vector similarity search
- `chunk_index` maintains order within transcripts
- JSONB metadata stores:
  - `speaker`: Who said this (host vs. guest)
  - `timestamp`: Position in episode (for audio linkage)
  - `context_before`/`context_after`: Adjacent chunks for overlap
- IVFFlat index for fast approximate nearest neighbor search

#### 5. `artifacts` Table (Optional)
Explicitly tracks generated artifacts for history and caching.

```sql
CREATE TABLE artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    artifact_type VARCHAR(50) NOT NULL,  -- 'markdown', 'html', 'json'
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- SHA-256 for deduplication
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_artifact_type CHECK (artifact_type IN ('markdown', 'html', 'json', 'mermaid'))
);

CREATE INDEX idx_artifacts_session_id ON artifacts(session_id, created_at DESC);
CREATE INDEX idx_artifacts_content_hash ON artifacts(content_hash);
```

**Design Rationale:**
- Separate table allows querying artifact history independently
- `content_hash` enables deduplication and caching
- Foreign key to `message_id` links artifacts to conversation context

---

## API Endpoints

### Base URL
- Local Development: `http://localhost:8000`
- API Prefix: `/api/v1`

### Health & Status

#### `GET /health`
Returns system health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-09-16T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "vector_store": "healthy",
    "llm_provider": "healthy",
    "ollama": "healthy"
  }
}
```

#### `GET /api/v1/config`
Returns current configuration (model provider, available models).

**Response:**
```json
{
  "model_provider": "ollama",
  "model_name": "llama3.1:8b",
  "available_providers": ["anthropic", "openai", "ollama"],
  "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
  "features": {
    "ship_30_for_30": true,
    "artifact_viewer": true
  }
}
```

### Session Management

#### `POST /api/v1/sessions`
Creates a new conversation session.

**Request Body:**
```json
{
  "title": "Product Strategy Questions",  // Optional
  "model_provider": "ollama",  // Optional, defaults to env config
  "model_name": "llama3.1:8b"  // Optional
}
```

**Response (201 Created):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-09-16T10:30:00Z",
  "title": "Product Strategy Questions",
  "model_provider": "ollama",
  "model_name": "llama3.1:8b"
}
```

#### `GET /api/v1/sessions`
Lists all sessions (most recent first).

**Query Parameters:**
- `limit` (int, default 20): Number of sessions to return
- `offset` (int, default 0): Pagination offset
- `is_active` (bool, optional): Filter by active status

**Response (200 OK):**
```json
{
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-09-16T10:30:00Z",
      "updated_at": "2026-09-16T10:35:00Z",
      "title": "Product Strategy Questions",
      "message_count": 8,
      "model_provider": "ollama"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

#### `GET /api/v1/sessions/{session_id}`
Retrieves a single session with full message history.

**Response (200 OK):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-09-16T10:30:00Z",
  "updated_at": "2026-09-16T10:35:00Z",
  "title": "Product Strategy Questions",
  "model_provider": "ollama",
  "model_name": "llama3.1:8b",
  "messages": [
    {
      "message_id": "660e8400-e29b-41d4-a716-446655440001",
      "role": "user",
      "content": "What does Lenny say about pricing strategy?",
      "created_at": "2026-09-16T10:30:15Z"
    },
    {
      "message_id": "660e8400-e29b-41d4-a716-446655440002",
      "role": "assistant",
      "content": "Based on the transcripts...",
      "created_at": "2026-09-16T10:30:18Z",
      "metadata": {
        "sources": [
          {
            "episode_number": 42,
            "guest_name": "Elena Verna",
            "title": "Mastering pricing and packaging",
            "excerpt": "..."
          }
        ],
        "token_count": 450
      }
    }
  ]
}
```

#### `DELETE /api/v1/sessions/{session_id}`
Soft-deletes a session (sets `is_active = false`).

**Response (204 No Content)**

### Message Handling

#### `POST /api/v1/sessions/{session_id}/messages`
Sends a message and receives assistant response.

**Request Body:**
```json
{
  "content": "What does Lenny say about pricing strategy?",
  "stream": false  // Optional, enables SSE streaming
}
```

**Response (200 OK):**
```json
{
  "message_id": "660e8400-e29b-41d4-a716-446655440002",
  "role": "assistant",
  "content": "Based on the transcripts from Episode 42 with Elena Verna...",
  "created_at": "2026-09-16T10:30:18Z",
  "metadata": {
    "sources": [
      {
        "transcript_id": "abc123",
        "episode_number": 42,
        "guest_name": "Elena Verna",
        "title": "Mastering pricing and packaging",
        "excerpt": "You have to understand your value metric...",
        "relevance_score": 0.89
      }
    ],
    "artifacts": [],
    "token_count": 450,
    "processing_time_ms": 3200
  }
}
```

**Streaming Response (SSE):**
When `stream: true`, returns Server-Sent Events:
```
event: message_start
data: {"message_id": "660e8400..."}

event: content_delta
data: {"delta": "Based on"}

event: content_delta
data: {"delta": " the transcripts"}

event: message_complete
data: {"metadata": {...}}
```

### Artifact Management

#### `GET /api/v1/sessions/{session_id}/artifacts`
Lists all artifacts generated in a session.

**Response (200 OK):**
```json
{
  "artifacts": [
    {
      "artifact_id": "770e8400-e29b-41d4-a716-446655440003",
      "artifact_type": "markdown",
      "title": "Ship 30 for 30: Pricing Strategy Insights",
      "created_at": "2026-09-16T10:32:00Z",
      "preview": "# The Hidden Psychology of Pricing...\n\n"
    }
  ]
}
```

#### `GET /api/v1/artifacts/{artifact_id}`
Retrieves full artifact content.

**Response (200 OK):**
```json
{
  "artifact_id": "770e8400-e29b-41d4-a716-446655440003",
  "artifact_type": "markdown",
  "title": "Ship 30 for 30: Pricing Strategy Insights",
  "content": "# The Hidden Psychology of Pricing\n\n...",
  "created_at": "2026-09-16T10:32:00Z",
  "metadata": {
    "word_count": 1248,
    "sources": ["episode_42", "episode_67"]
  }
}
```

### Retrieval Testing (Development Only)

#### `POST /api/v1/retrieval/search`
Direct access to retrieval engine for testing.

**Request Body:**
```json
{
  "query": "pricing strategy for B2B SaaS",
  "top_k": 5,
  "min_score": 0.7
}
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "chunk_id": "880e8400...",
      "transcript_id": "abc123",
      "episode_number": 42,
      "guest_name": "Elena Verna",
      "content": "You have to understand your value metric...",
      "score": 0.89,
      "metadata": {
        "speaker": "guest",
        "timestamp_seconds": 1450
      }
    }
  ],
  "query_time_ms": 120
}
```

---

## Component Architecture

### Backend Components

#### 1. API Layer (`backend/app/api/`)
- **`routes/`**: FastAPI routers for each resource (sessions, messages, artifacts)
- **`dependencies.py`**: Shared dependencies (DB connections, auth)
- **`middleware.py`**: Logging, CORS, error handling
- **`schemas.py`**: Pydantic models for request/response validation

#### 2. Agent Layer (`backend/app/agent/`)
- **`agent.py`**: Main agent orchestrator using Claude Agent SDK
- **`skills/`**: Modular skill implementations
  - `conversational_assistant.py`: Q&A with retrieval
  - `ship_30_content_generator.py`: Structured content creation
- **`prompts.py`**: System prompts and templates
- **`routing.py`**: Intent classification and skill routing logic

#### 3. Retrieval Engine (`backend/app/retrieval/`)
- **`embedder.py`**: Embedding model wrapper (local or API)
- **`vector_store.py`**: Vector database interface (pgvector or FAISS)
- **`retriever.py`**: Main RAG logic (query → embed → search → rerank)
- **`reranker.py`**: Cross-encoder or LLM-based reranking

#### 4. LLM Provider Layer (`backend/app/llm/`)
- **`base_provider.py`**: Abstract base class for LLM providers
- **`anthropic_provider.py`**: Anthropic Claude integration
- **`openai_provider.py`**: OpenAI GPT integration
- **`ollama_provider.py`**: Local Ollama integration
- **`config.py`**: Provider selection and configuration management

#### 5. Database Layer (`backend/app/db/`)
- **`models.py`**: SQLAlchemy ORM models
- **`session.py`**: Database session management
- **`repositories/`**: Data access layer (repository pattern)
  - `session_repository.py`
  - `message_repository.py`
  - `transcript_repository.py`

#### 6. Ingestion Pipeline (`backend/app/ingestion/`)
- **`loader.py`**: Transcript file loading (JSON, Markdown, HTML)
- **`chunker.py`**: Text chunking with overlap strategy
- **`embedder.py`**: Batch embedding generation
- **`indexer.py`**: Vector index creation and management

### Frontend Components

#### 1. Pages (`frontend/src/pages/`)
- **`ChatPage.tsx`**: Main application page

#### 2. Components (`frontend/src/components/`)
- **`ChatInterface/`**: Message display, input, and session list
  - `MessageList.tsx`: Scrollable conversation view
  - `MessageInput.tsx`: Text input with send button
  - `SessionSidebar.tsx`: Session switching and creation
- **`ArtifactViewer/`**: Rendering panel for generated content
  - `ArtifactViewer.tsx`: Main container with type detection
  - `MarkdownRenderer.tsx`: Markdown display with syntax highlighting
  - `HTMLSandbox.tsx`: Sandboxed HTML rendering
- **`ModelSelector.tsx`**: UI for switching LLM providers

#### 3. Services (`frontend/src/services/`)
- **`api.ts`**: Axios-based API client with typed methods
- **`websocket.ts`**: SSE connection for streaming responses

#### 4. State Management (`frontend/src/store/`)
- **`sessionStore.ts`**: Zustand store for session state
- **`configStore.ts`**: Application configuration state

---

## Ingestion and Retrieval Flow

### Ingestion Pipeline

```
Raw Transcript Files
        ↓
  1. Load & Parse
        ↓
  2. Extract Metadata (episode, guest, date)
        ↓
  3. Chunk Text (512 tokens, 50 token overlap)
        ↓
  4. Generate Embeddings (batch processing)
        ↓
  5. Store in Database (transcripts + chunks tables)
        ↓
  6. Build Vector Index (pgvector or FAISS)
```

**Chunking Strategy:**
- **Chunk Size:** 512 tokens (~380 words)
- **Overlap:** 50 tokens (~38 words)
- **Rationale:** 
  - 512 tokens fits comfortably in LLM context with query
  - Overlap preserves context across boundaries
  - Avoids mid-sentence splits using sentence boundary detection

**Metadata Preservation:**
Each chunk stores:
- `transcript_id`: Link back to full episode
- `chunk_index`: Position in transcript
- `speaker`: Host or guest attribution
- `context_before`/`context_after`: Adjacent chunk previews

### Retrieval Pipeline

```
User Query
    ↓
1. Query Understanding (extract intent, entities)
    ↓
2. Embedding Generation (same model as ingestion)
    ↓
3. Vector Search (top 20 candidates, cosine similarity)
    ↓
4. Keyword Filter (optional: guest name, topic)
    ↓
5. Reranking (cross-encoder or LLM, narrow to top 5)
    ↓
6. Context Assembly (merge adjacent chunks if from same transcript)
    ↓
7. Source Attribution (attach episode metadata)
    ↓
Retrieved Context → Agent
```

**Retrieval Optimizations:**
- **Hybrid Search:** Combine vector similarity with BM25 keyword matching
- **Metadata Filtering:** Pre-filter by guest name or date range if specified
- **Chunk Merging:** If top chunks are adjacent, merge for fuller context
- **Score Thresholding:** Minimum similarity of 0.7 to avoid irrelevant results

---

## Agent Routing Logic

### Intent Classification

The agent uses a two-stage routing system:

1. **Primary Classification:**
   - **Conversational Q&A:** General questions about product/growth
   - **Content Generation:** Explicit request for Ship 30 for 30 essay
   - **Artifact Manipulation:** Edit, regenerate, or export existing artifacts

2. **Skill Invocation:**
   - Each skill is a self-contained function with its own system prompt
   - Skills receive conversation history and retrieved context
   - Skills return structured outputs (text + metadata)

### Routing Decision Tree

```
User Message
     ↓
Intent Classifier (LLM or regex patterns)
     ↓
     ├─ Contains "Ship 30 for 30" / "write essay" / "generate content"
     │       → Ship30ContentGenerator Skill
     │
     ├─ Contains "create diagram" / "build mockup" / "HTML"
     │       → HTMLArtifactGenerator Skill
     │
     ├─ Refers to previous artifact ("edit that", "regenerate")
     │       → ArtifactEditor Skill
     │
     └─ Default: Question or conversation
             → ConversationalAssistant Skill
```

### Skill: Conversational Assistant

**Inputs:**
- User query
- Conversation history (last 10 messages)
- Retrieved context (top 5 chunks)

**System Prompt:**
```
You are an expert assistant specializing in product management and growth,
trained on Lenny Rachitsky's podcast interviews.

Guidelines:
1. Answer ONLY based on the provided transcript context
2. Always cite the episode and guest name
3. If information is not in the transcripts, say "I don't have information about that"
4. Use specific quotes when possible
5. Maintain conversational tone
```

**Output:**
- Answer text
- Source citations (episode, guest, excerpt)
- Confidence score

### Skill: Ship 30 for 30 Content Generator

**Inputs:**
- Topic or question
- Retrieved context (top 10 chunks for more material)
- Writing principles (encoded in skill)

**Writing Principles (Ship 30 for 30):**
1. **Hook:** First 2 sentences must grab attention (question, stat, or bold claim)
2. **Structure:** Clear H2 headings every 200-300 words
3. **Skimmability:** Bullet points, numbered lists, bold key phrases
4. **Length:** 1,200-1,300 words (strict)
5. **Takeaway:** End with a concrete, actionable insight
6. **Grounding:** Every claim cites a source

**Output:**
- Markdown-formatted essay
- Title suggestion
- Source bibliography
- Metadata (word count, reading time)

---

## Model Configuration System

### Configuration File (`backend/app/config.py`)

```python
class LLMConfig:
    provider: str = "ollama"  # 'anthropic', 'openai', 'ollama'
    
    # Cloud models
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    openai_model: str = "gpt-4o-mini"
    
    # Local models
    ollama_model: str = "llama3.1:8b"
    ollama_base_url: str = "http://localhost:11434"
    
    # Embedding models
    embedding_provider: str = "local"  # 'openai', 'local'
    local_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Fallback behavior
    fallback_enabled: bool = True
    fallback_order: list = ["ollama", "anthropic", "openai"]
```

### Provider Selection Logic

```python
def get_llm_provider(config: LLMConfig) -> BaseLLMProvider:
    """
    Returns the configured LLM provider with fallback handling.
    """
    try:
        if config.provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise MissingAPIKeyError("Anthropic API key not found")
            return AnthropicProvider(config)
        
        elif config.provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise MissingAPIKeyError("OpenAI API key not found")
            return OpenAIProvider(config)
        
        elif config.provider == "ollama":
            # Check if Ollama is running
            try:
                requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
            except requests.exceptions.RequestException:
                raise OllamaUnavailableError("Ollama server not responding")
            return OllamaProvider(config)
    
    except Exception as e:
        if config.fallback_enabled:
            logger.warning(f"Primary provider failed: {e}. Trying fallback...")
            for fallback_provider in config.fallback_order:
                if fallback_provider != config.provider:
                    try:
                        config.provider = fallback_provider
                        return get_llm_provider(config)
                    except:
                        continue
        
        raise ProviderInitializationError("All LLM providers failed")
```

---

## Security Architecture

### Artifact Rendering Security

**Threat Model:**
- Malicious HTML generated by LLM (XSS, code injection)
- External resource loading (tracking pixels, malicious scripts)
- Iframe breakout attempts

**Mitigation Layers:**

#### 1. HTML Sanitization (DOMPurify)
```typescript
import DOMPurify from 'dompurify';

const ALLOWED_TAGS = [
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
  'p', 'br', 'strong', 'em', 'u', 'code', 'pre',
  'ul', 'ol', 'li', 'blockquote',
  'table', 'thead', 'tbody', 'tr', 'th', 'td',
  'div', 'span', 'a', 'img'
];

const ALLOWED_ATTR = [
  'href', 'src', 'alt', 'title', 'class', 'id', 'style'
];

function sanitizeHTML(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS,
    ALLOWED_ATTR,
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['script', 'iframe', 'object', 'embed'],
    FORBID_ATTR: ['onerror', 'onload', 'onclick']
  });
}
```

#### 2. Content Security Policy (CSP)
```typescript
const sandbox = "allow-same-origin";  // No scripts, no forms
<iframe
  srcDoc={sanitizedHTML}
  sandbox={sandbox}
  style={{border: 'none', width: '100%', height: '100%'}}
/>
```

#### 3. Sandboxed Iframe
- `sandbox="allow-same-origin"`: No JavaScript execution
- No `allow-scripts`, `allow-forms`, or `allow-popups`
- Blocks navigation and top-level access

#### 4. URL Filtering
```typescript
function sanitizeURL(url: string): string | null {
  try {
    const parsed = new URL(url);
    // Only allow HTTPS URLs to trusted domains
    if (parsed.protocol === 'https:') {
      return url;
    }
  } catch {
    return null;  // Invalid URL
  }
  return null;
}
```

**Security Boundaries:**
- No inline JavaScript allowed
- No external resource loading (images, scripts, fonts)
- Styles are scoped and sanitized
- Links open in new tab with `rel="noopener noreferrer"`

---

## Deployment Topology

### Local Development (Docker Compose)

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/lenny_assistant
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  db:
    image: pgvector/pgvector:pg16
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=lenny_assistant
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Design Rationale:**
- `host.docker.internal` allows backend container to access Ollama running on host
- pgvector extension pre-installed in official image
- Volume mounts for database persistence
- Environment variables for configuration

### Production Considerations (Not Implemented)

For a production deployment, the following would be added:

1. **Authentication Layer:**
   - JWT-based auth or OAuth2
   - Role-based access control
   - API rate limiting

2. **Scalability:**
   - Horizontal scaling of backend (stateless design)
   - Load balancer (nginx or cloud LB)
   - Redis for session caching
   - Separate vector database (Qdrant, Pinecone)

3. **Monitoring:**
   - Prometheus metrics export
   - Grafana dashboards
   - Sentry error tracking
   - Log aggregation (ELK or Datadog)

4. **Infrastructure:**
   - Kubernetes manifests or Terraform
   - CI/CD pipeline (GitHub Actions)
   - Automated backups and disaster recovery

---

## Observability and Logging

### Structured Logging Format

```json
{
  "timestamp": "2026-09-16T10:30:18.234Z",
  "level": "INFO",
  "service": "backend-api",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "event": "retrieval_completed",
  "details": {
    "query": "pricing strategy",
    "num_results": 5,
    "top_score": 0.89,
    "latency_ms": 120
  }
}
```

### Key Events Logged

1. **API Requests:**
   - Endpoint, method, status code, latency
   - Request ID for tracing

2. **Agent Execution:**
   - Skill invoked, input summary, output summary
   - Token usage, processing time

3. **Retrieval Operations:**
   - Query text (truncated), number of results, top scores
   - Embedding time, search time, reranking time

4. **Database Operations:**
   - Query type (INSERT, SELECT), table, duration
   - Connection pool stats

5. **Errors:**
   - Exception type, message, stack trace
   - Context (session ID, user input)

### Health Check Implementation

```python
@app.get("/health")
async def health_check():
    """
    Returns system health status with component checks.
    """
    components = {}
    
    # Database check
    try:
        db.execute("SELECT 1")
        components["database"] = "healthy"
    except Exception as e:
        components["database"] = f"unhealthy: {str(e)}"
    
    # Vector store check
    try:
        vector_store.ping()
        components["vector_store"] = "healthy"
    except Exception as e:
        components["vector_store"] = f"unhealthy: {str(e)}"
    
    # LLM provider check
    try:
        llm_provider.health_check()
        components["llm_provider"] = "healthy"
    except Exception as e:
        components["llm_provider"] = f"unhealthy: {str(e)}"
    
    # Ollama check (if configured)
    if config.provider == "ollama":
        try:
            requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
            components["ollama"] = "healthy"
        except:
            components["ollama"] = "unavailable"
    
    overall_status = "healthy" if all(
        v == "healthy" for v in components.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": components
    }
```

---

## Error Handling and Resilience

### Error Categories and Responses

| Error Type | HTTP Status | User Message | Recovery Action |
|-----------|-------------|--------------|-----------------|
| Missing API Key | 503 Service Unavailable | "Cloud LLM unavailable. Falling back to local model." | Attempt fallback provider |
| Ollama Unavailable | 503 Service Unavailable | "Local model server not running. Please start Ollama." | Return clear setup instructions |
| Retrieval Timeout | 504 Gateway Timeout | "Search taking longer than expected. Please try again." | Retry with reduced top_k |
| No Relevant Results | 200 OK | "I don't have information about that in the available transcripts." | Graceful response, no error |
| Database Connection Failed | 503 Service Unavailable | "System temporarily unavailable. Please try again shortly." | Retry with exponential backoff |
| Invalid Input | 400 Bad Request | "Your message is too long. Please keep it under 2000 characters." | Validation error with guidance |
| Rate Limit Exceeded | 429 Too Many Requests | "You're asking questions too quickly. Please wait a moment." | Retry-After header |

### Graceful Degradation

1. **LLM Provider Failure:**
   - Fallback to alternative provider
   - If all fail, return cached/template responses

2. **Retrieval Failure:**
   - Agent operates without grounding (clearly disclosed)
   - Reduces confidence in response

3. **Database Write Failure:**
   - Log error but return LLM response
   - Queue for retry in background

4. **Embedding Model Unavailable:**
   - Fall back to keyword search only
   - Reduced quality but functional

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| API Response Time (p95) | <5s | Conversational queries |
| Content Generation Time (p95) | <15s | Ship 30 for 30 essays |
| Retrieval Latency (p95) | <500ms | Vector search + rerank |
| Database Query Time (p95) | <100ms | Session/message CRUD |
| Frontend Initial Load | <2s | Time to interactive |
| Streaming Response TTFB | <1s | Time to first token |

---

**Document Version:** 1.0  
**Last Updated:** 2026-09-16  
**Author:** Forward Deployed Engineer Candidate
