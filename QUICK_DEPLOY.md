# 🚀 Quick Deploy - The Lenny Growth Assistant

## Fastest Method: Railway (5 minutes)

### Step 1: Push to GitHub
```bash
cd "The Lenny Growth Assistant"

# Initialize git if not already
git init
git add .
git commit -m "Initial commit - The Lenny Growth Assistant"

# Create GitHub repo and push
# Go to github.com, create new repo, then:
git remote add origin https://github.com/YOUR_USERNAME/lenny-assistant.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Railway

1. **Go to:** https://railway.app
2. **Click:** "Start a New Project"
3. **Select:** "Deploy from GitHub repo"
4. **Choose:** your lenny-assistant repository
5. **Railway will:**
   - Auto-detect docker-compose.yml
   - Create PostgreSQL database
   - Deploy backend and frontend
   - Generate public URLs

### Step 3: Add Environment Variables

In Railway dashboard:
1. Click on your backend service
2. Go to "Variables" tab
3. Add:
   ```
   ANTHROPIC_API_KEY=your_key_here
   MODEL_PROVIDER=anthropic
   ```

### Step 4: Enable pgvector Extension

1. Click on PostgreSQL service
2. Go to "Data" tab
3. Click "Query"
4. Run: `CREATE EXTENSION IF NOT EXISTS vector;`

### Step 5: Initialize Data

1. Click on backend service
2. Go to "Settings" → "Run Command"
3. Run:
   ```bash
   python scripts/ingest_transcripts.py && python scripts/generate_embeddings.py
   ```

### Step 6: Get Your URL! 🎉

Railway will provide URLs like:
- **Frontend:** `https://your-app.up.railway.app`
- **Backend:** `https://your-api.up.railway.app`

---

## Alternative: Render (10 minutes)

### Step 1: Push to GitHub (same as above)

### Step 2: Deploy Database

1. Go to https://render.com
2. Click "New +" → "PostgreSQL"
3. Name: `lenny-db`
4. Plan: Free
5. Create Database
6. In database shell, run: `CREATE EXTENSION vector;`

### Step 3: Deploy Backend

1. Click "New +" → "Web Service"
2. Connect GitHub repo
3. Settings:
   - Root: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Environment variables:
   ```
   DATABASE_URL=[from Render PostgreSQL]
   ANTHROPIC_API_KEY=your_key
   CORS_ORIGINS=*
   ```
5. Deploy

### Step 4: Deploy Frontend

1. Click "New +" → "Static Site"
2. Connect GitHub repo
3. Settings:
   - Root: `frontend`
   - Build: `npm install && npm run build`
   - Publish: `dist`
4. Environment:
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```
5. Deploy

---

## Without GitHub (Local Deploy to Vercel)

If you don't want to use GitHub:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
echo "VITE_API_URL=http://localhost:8000" > .env.production
npm run build
vercel --prod

# You'll need to run backend locally or use a cloud provider
```

---

## Need ANTHROPIC_API_KEY?

1. Go to: https://console.anthropic.com
2. Sign up / Log in
3. Go to "API Keys"
4. Create new key
5. Copy and use in deployment

---

## Expected Result

Once deployed, you'll have:
- ✅ Public URL (e.g., `https://lenny-assistant.railway.app`)
- ✅ Working chat interface
- ✅ RAG-powered Q&A
- ✅ Ship 30 for 30 generation
- ✅ Persistent sessions

---

## Troubleshooting

**Issue: "Module not found"**
- Railway: Wait for build to complete
- Render: Check build logs

**Issue: "Database connection failed"**
- Verify DATABASE_URL is set
- Check pgvector extension is installed

**Issue: "CORS error"**
- Update CORS_ORIGINS to include frontend URL
- Or temporarily set to `*` for testing

**Issue: "No data returned"**
- Run ingestion scripts in backend service
- Check database has transcripts and embeddings

---

## What I Recommend

**For Demo/Testing:** Railway (easiest, free tier)
**For Production:** Render or Fly.io (more control)
**For Enterprise:** AWS/GCP with proper infrastructure

---

**Total Time:** 5-10 minutes
**Cost:** Free tier sufficient for demo
**Result:** Public URL you can share!

🎉 **You're ready to deploy!**
