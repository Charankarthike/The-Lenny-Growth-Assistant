# Deployment Guide

## Option 1: Render (Recommended)

### Step 1: Create PostgreSQL Database

1. Go to https://dashboard.render.com/
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `lenny-db`
   - **Database**: `lenny_assistant`
   - **User**: `lenny_user`
   - **Region**: Oregon (or closest to you)
   - **Plan**: Free
4. Click **"Create Database"**
5. Wait for database to provision (~2 minutes)
6. Copy the **"Internal Database URL"** (starts with `postgresql://`)

### Step 2: Deploy Backend API

1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `lenny-api`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

4. Add Environment Variables:
   ```
   DATABASE_URL = [paste Internal Database URL]
   OPENAI_API_KEY = [your OpenAI API key]
   ENVIRONMENT = production
   PORT = 10000
   CORS_ORIGINS = *
   EMBEDDING_MODEL = text-embedding-3-small
   LLM_MODEL = gpt-4o-mini
   TOP_K_RESULTS = 5
   ```

5. Click **"Create Web Service"**
6. Wait for build to complete (~3-5 minutes)

### Step 3: Initialize Database

Once deployed, use Render Shell:

1. Go to your service → **"Shell"** tab
2. Run:
   ```bash
   python scripts/init_database.py
   python scripts/load_sample_data.py
   ```

### Step 4: Test Your API

Your API will be live at: `https://lenny-api-[random].onrender.com`

Test endpoints:
- Health: `GET https://your-api.onrender.com/health`
- Chat: `POST https://your-api.onrender.com/api/chat`

---

## Option 2: Railway

### Step 1: Create PostgreSQL Database

1. Go to https://railway.app/
2. Create new project
3. Click **"+ New"** → **"Database"** → **"PostgreSQL"**
4. Copy the **"DATABASE_URL"** from Variables tab

### Step 2: Deploy Backend

1. Click **"+ New"** → **"GitHub Repo"**
2. Select your repository
3. Configure:
   - **Root Directory**: `/backend`
   - Railway will auto-detect Python and use `railway.toml`

4. Add Environment Variables:
   ```
   DATABASE_URL = [from PostgreSQL service]
   OPENAI_API_KEY = [your key]
   ENVIRONMENT = production
   CORS_ORIGINS = *
   ```

5. Deploy will start automatically

### Step 3: Initialize Database

Use Railway CLI or web shell:
```bash
python scripts/init_database.py
python scripts/load_sample_data.py
```

---

## Option 3: Docker (Self-hosted)

### Build and Run

```bash
cd backend

# Build image
docker build -t lenny-api .

# Run container
docker run -d \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:password@host:5432/db \
  -e OPENAI_API_KEY=your-key \
  -e ENVIRONMENT=production \
  --name lenny-api \
  lenny-api
```

### With Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_DB: lenny_assistant
      POSTGRES_USER: lenny_user
      POSTGRES_PASSWORD: lenny_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://lenny_user:lenny_password@db:5432/lenny_assistant
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ENVIRONMENT: production
    depends_on:
      - db

volumes:
  postgres_data:
```

Run:
```bash
docker-compose up -d
```

---

## Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | PostgreSQL connection URL | - |
| `OPENAI_API_KEY` | ✅ | OpenAI API key | - |
| `ENVIRONMENT` | ❌ | Environment (production/development) | production |
| `PORT` | ❌ | Server port | 8000 |
| `CORS_ORIGINS` | ❌ | Allowed CORS origins (comma-separated) | * |
| `EMBEDDING_MODEL` | ❌ | OpenAI embedding model | text-embedding-3-small |
| `LLM_MODEL` | ❌ | OpenAI chat model | gpt-4o-mini |
| `TOP_K_RESULTS` | ❌ | Number of RAG results | 5 |

---

## Post-Deployment Checklist

- [ ] Backend API is accessible
- [ ] `/health` endpoint returns `{"status": "healthy"}`
- [ ] Database connection works (check `/health` → `"database": "connected"`)
- [ ] Database initialized (`python scripts/init_database.py`)
- [ ] Sample data loaded (`python scripts/load_sample_data.py`)
- [ ] Chat endpoint works (`POST /api/chat`)
- [ ] RAG retrieval returns sources
- [ ] Update frontend `VITE_API_URL` to backend URL

---

## Troubleshooting

### Build fails with pydantic-core error
✅ **Fixed!** We use pydantic 2.5.0 with pre-built wheels.

### Database connection fails
- Check `DATABASE_URL` is set correctly
- Ensure pgvector extension is enabled (done by `init_database.py`)
- Verify database is in same region as API (for Render)

### OpenAI API errors
- Verify `OPENAI_API_KEY` is set
- Check API key has credits
- Test with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`

### CORS errors
- Set `CORS_ORIGINS` to your frontend URL (not `*`)
- Or use `*` for testing (not recommended for production)

---

## Monitoring

### Render
- View logs in dashboard
- Set up log drains for long-term storage
- Monitor resource usage

### Railway
- Built-in metrics and logging
- Set up webhooks for alerts

### Docker
- Use `docker logs lenny-api`
- Set up logging driver for centralized logs
