# Deploy to Vercel - The Lenny Growth Assistant

## Important: Two-Part Deployment

Vercel hosts **frontend only**. You need:
1. **Frontend on Vercel** (React app)
2. **Backend on Render/Railway** (FastAPI + Database)

---

## Part 1: Deploy Backend (Render - Free)

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Connect your repository

### Step 2: Deploy PostgreSQL Database
1. Click "New +" → "PostgreSQL"
2. Settings:
   - **Name:** lenny-assistant-db
   - **Plan:** Free
3. Click "Create Database"
4. **Important:** After creation, click "Connect" → "PSQL Command"
5. Run in database shell:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

### Step 3: Deploy Backend API
1. Click "New +" → "Web Service"
2. Connect GitHub repo: **The-Lenny-Growth-Assistant**
3. Settings:
   - **Name:** lenny-assistant-api
   - **Root Directory:** `backend`
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free

4. Environment Variables (click "Advanced" → "Add Environment Variable"):
   ```
   DATABASE_URL=<copy from Render PostgreSQL Internal Connection String>
   ANTHROPIC_API_KEY=your_anthropic_key_here
   MODEL_PROVIDER=anthropic
   MODEL_NAME=claude-3-5-sonnet-20241022
   EMBEDDING_PROVIDER=local
   CORS_ORIGINS=https://your-frontend.vercel.app
   LOG_LEVEL=INFO
   PORT=10000
   ```

5. Click "Create Web Service"

### Step 4: Initialize Data
Once backend is deployed:
1. Go to backend service page
2. Click "Shell" tab (or use "Connect" dropdown)
3. Run:
   ```bash
   python scripts/ingest_transcripts.py
   python scripts/generate_embeddings.py
   ```

### Step 5: Get Backend URL
Copy your backend URL (looks like):
```
https://lenny-assistant-api.onrender.com
```

**Keep this URL - you'll need it for Vercel!**

---

## Part 2: Deploy Frontend (Vercel)

### Option A: Via Vercel Dashboard (Easiest)

1. **Go to Vercel:**
   - Visit: https://vercel.com
   - Click "Sign Up" or "Login"
   - Sign in with GitHub

2. **Import Project:**
   - Click "Add New..." → "Project"
   - Find **The-Lenny-Growth-Assistant**
   - Click "Import"

3. **Configure Project:**
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

4. **Add Environment Variable:**
   - Click "Environment Variables"
   - Add:
     - **Name:** `VITE_API_URL`
     - **Value:** `https://lenny-assistant-api.onrender.com` (your backend URL)

5. **Deploy:**
   - Click "Deploy"
   - Wait 2-3 minutes
   - Get your URL: `https://your-app.vercel.app`

### Option B: Via Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project
cd "The Lenny Growth Assistant"

# Update environment
echo "VITE_API_URL=https://lenny-assistant-api.onrender.com" > frontend/.env.production

# Deploy
cd frontend
vercel --prod

# Follow prompts:
# - Set up and deploy? Y
# - Which scope? (choose your account)
# - Link to existing project? N
# - Project name? lenny-assistant
# - Directory? ./
# - Override settings? N
```

---

## Part 3: Update CORS

After frontend is deployed:

1. Go back to **Render backend service**
2. Click "Environment"
3. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:5173
   ```
4. Save (backend will redeploy automatically)

---

## Verification Steps

### Test Backend
```bash
# Health check
curl https://lenny-assistant-api.onrender.com/health

# Expected: {"status":"healthy"}
```

### Test Frontend
1. Open `https://your-app.vercel.app`
2. Should see the chat interface
3. Click "+ New" to create session
4. Try sending a message

---

## Full Deployment URLs

After deployment, you'll have:

| Service | URL |
|---------|-----|
| **Frontend (Vercel)** | https://your-app.vercel.app |
| **Backend (Render)** | https://lenny-assistant-api.onrender.com |
| **API Docs** | https://lenny-assistant-api.onrender.com/docs |
| **Database** | Internal (Render PostgreSQL) |

---

## Environment Variables Summary

### Backend (Render)
```bash
DATABASE_URL=<from Render PostgreSQL>
ANTHROPIC_API_KEY=your_key
MODEL_PROVIDER=anthropic
MODEL_NAME=claude-3-5-sonnet-20241022
EMBEDDING_PROVIDER=local
CORS_ORIGINS=https://your-app.vercel.app
LOG_LEVEL=INFO
PORT=10000
```

### Frontend (Vercel)
```bash
VITE_API_URL=https://lenny-assistant-api.onrender.com
```

---

## Troubleshooting

### Issue: Frontend can't connect to backend
**Solution:**
1. Check backend URL in Vercel environment variables
2. Verify CORS_ORIGINS includes your Vercel URL
3. Test backend health: `curl https://your-backend.onrender.com/health`

### Issue: "Module not found" on Vercel
**Solution:**
1. Verify Root Directory is set to `frontend`
2. Check Build Command is `npm run build`
3. Check Output Directory is `dist`

### Issue: Backend takes long to respond
**Solution:**
- Render free tier has cold starts (takes 30s to wake up)
- First request may be slow, subsequent ones are fast
- Consider upgrading to paid plan for always-on

### Issue: Database connection errors
**Solution:**
1. Verify DATABASE_URL in backend environment
2. Check pgvector extension: `CREATE EXTENSION vector;`
3. Ensure internal connection string is used (not external)

### Issue: No data returned
**Solution:**
Run initialization in backend shell:
```bash
python scripts/ingest_transcripts.py
python scripts/generate_embeddings.py
```

---

## Cost Breakdown

| Service | Free Tier | Paid |
|---------|-----------|------|
| **Vercel** | Unlimited deploys | $20/month (Pro) |
| **Render (Backend)** | 750 hours/month | $7/month |
| **Render (Database)** | Free | $7/month |
| **Total** | **$0** | $14-27/month |

**Free tier is sufficient for demo/portfolio!**

---

## Quick Commands Reference

### Vercel CLI Commands
```bash
# Deploy
vercel --prod

# Check deployment status
vercel ls

# View logs
vercel logs

# Remove deployment
vercel rm project-name
```

### Update Deployment
```bash
# Make changes, commit to GitHub
git add .
git commit -m "Update"
git push

# Vercel auto-deploys from GitHub
# Or manually:
cd frontend
vercel --prod
```

---

## Performance Tips

### Vercel (Frontend)
- ✅ Automatic HTTPS
- ✅ Global CDN
- ✅ Instant cache invalidation
- ✅ Auto-scaling

### Render (Backend)
- ⚠️ Cold starts on free tier (~30s)
- ✅ Persistent storage
- ✅ Auto-deploy from GitHub
- ✅ Free SSL

---

## Next Steps After Deployment

1. ✅ Test end-to-end functionality
2. ✅ Add custom domain (optional)
3. ✅ Monitor usage in dashboards
4. ✅ Share your URL!
5. ✅ Add to portfolio/resume

---

## Custom Domain (Optional)

### Vercel
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records as shown
4. Wait for verification

### Render
1. Go to Service Settings → Custom Domain
2. Add your domain
3. Update DNS CNAME to Render

---

## Monitoring

### Vercel Dashboard
- Deployment logs
- Analytics
- Performance metrics
- Error tracking

### Render Dashboard
- Service logs
- Metrics
- Database usage
- Uptime monitoring

---

## Important Notes

⚠️ **Render Free Tier Limitations:**
- Services spin down after 15 min of inactivity
- First request after inactivity takes ~30s (cold start)
- 750 hours/month limit (enough for most demos)

✅ **Vercel Free Tier:**
- No cold starts
- Unlimited bandwidth (100GB/month fair use)
- Unlimited deployments

---

## Success Checklist

- [ ] Backend deployed on Render
- [ ] Database created with pgvector
- [ ] Data ingested and embeddings generated
- [ ] Backend health check returns healthy
- [ ] Frontend deployed on Vercel
- [ ] VITE_API_URL set correctly
- [ ] CORS configured with Vercel URL
- [ ] Can create session in frontend
- [ ] Can send message and get response
- [ ] Sources are displayed
- [ ] Ship 30 generation works

---

## Get API Key

Don't have Anthropic API key?

1. Go to: https://console.anthropic.com
2. Sign up (free credits available)
3. Navigate to "API Keys"
4. Create new key
5. Copy and add to Render environment

---

## Support Links

- **Vercel Docs:** https://vercel.com/docs
- **Render Docs:** https://render.com/docs
- **Vite Docs:** https://vitejs.dev
- **FastAPI Docs:** https://fastapi.tiangolo.com

---

## Estimated Time

- **Backend Setup (Render):** 10 minutes
- **Frontend Setup (Vercel):** 5 minutes
- **Testing & Configuration:** 5 minutes
- **Total:** ~20 minutes

---

🎉 **You're ready to deploy!**

Start with Part 1 (Backend on Render), then Part 2 (Frontend on Vercel).
