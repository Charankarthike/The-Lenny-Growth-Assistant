# Final Step: Connect Frontend to Backend

## 🎯 Once Backend Build Completes

After your Render backend shows "Live" status, follow these steps to connect your frontend:

### Step 1: Update Vercel Environment Variable

1. Go to: https://vercel.com/dashboard
2. Click on your project: **the-lenny-growth-assistant**
3. Click **"Settings"** tab
4. Click **"Environment Variables"** in the left sidebar
5. Find the `VITE_API_URL` variable
6. Click the **three dots (⋮)** → **"Edit"**
7. Change the value to:
   ```
   https://lenny-api-gpj1.onrender.com
   ```
8. Click **"Save"**

### Step 2: Redeploy Frontend

1. Go to the **"Deployments"** tab
2. Click the **three dots (⋮)** on the latest deployment
3. Click **"Redeploy"**
4. Wait 1-2 minutes for redeployment

### Step 3: Update Backend CORS

1. Go back to Render: https://dashboard.render.com/
2. Click your backend service: **lenny-api-gpj1**
3. Click **"Environment"**
4. Find the `CORS_ORIGINS` variable
5. Click **"Edit"**
6. Change from `*` to:
   ```
   https://the-lenny-growth-assistant-green.vercel.app
   ```
7. Click **"Save Changes"**

## ✅ Test Your Application

After both deployments complete:

1. **Open your app**: https://the-lenny-growth-assistant-green.vercel.app/
2. **Test the chat**:
   - Type a message like "What is Ship 30 for 30?"
   - You should get a response from the AI

## 🔍 If It Doesn't Work

Check:
1. Backend is "Live" in Render (green dot)
2. Backend health check works: https://lenny-api-gpj1.onrender.com/health
3. Frontend deployed successfully in Vercel
4. Browser console (F12) for any error messages

## 📊 Initial Data Load (Optional - Do Later)

Once everything works, you can load the transcript data:

1. In Render, click your backend service
2. Click **"Shell"** tab
3. Run these commands one by one:
   ```bash
   python -c "from app.db.database import engine; from sqlalchemy import text; with engine.connect() as conn: conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector')); conn.commit()"
   
   python scripts/ingest_transcripts.py
   
   python scripts/generate_embeddings.py
   ```

This will enable the full RAG functionality with Lenny's podcast transcripts!

## 🎉 You're Done!

Your full-stack application will be live and accessible to anyone!
