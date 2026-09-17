# Update Render Backend Environment Variables

## ✅ Changes Made
- Removed `sentence-transformers` and `torch` (caused build failures)
- Downgraded to `pydantic 2.5.3` with pre-built wheels (avoids pydantic-core compilation)
- Backend will now use **OpenAI embeddings** instead of local models

## 🔧 Required Action: Update Environment Variables

### Step 1: Go to Your Render Dashboard
1. Open: https://dashboard.render.com/
2. Click on your backend service: **lenny-api-gpj1**

### Step 2: Add New Environment Variable
1. Click **"Environment"** in the left sidebar
2. Scroll down to the **Environment Variables** section
3. Click **"Add Environment Variable"**
4. Add this new variable:
   ```
   Key: EMBEDDING_PROVIDER
   Value: openai
   ```

### Step 3: Verify All Required Variables
Make sure you have these 7 environment variables set:

```
DATABASE_URL = [your internal database URL from Render PostgreSQL]
OPENAI_API_KEY = [your OpenAI API key]
MODEL_PROVIDER = openai
MODEL_NAME = gpt-4o-mini
EMBEDDING_PROVIDER = openai    ← NEW! Add this
CORS_ORIGINS = *
PORT = 10000
```

### Step 4: Save and Redeploy
1. Click **"Save Changes"** at the bottom
2. Render will automatically trigger a new deployment
3. Wait 3-5 minutes for the build to complete

## ✅ Why This Will Work Now
- **No more compilation**: Using only packages with pre-built wheels
- **pydantic 2.5.3**: Stable version that installs without building from source
- **OpenAI embeddings**: No need for torch or sentence-transformers
- **Faster build**: Should complete in 3-5 minutes instead of timing out

## 📝 What Changed in Code
1. `backend/requirements.txt` - Simplified to essential packages only
2. `backend/app/retrieval/embedder.py` - Better error message if sentence-transformers missing
3. Backend will automatically use OpenAI embeddings when `EMBEDDING_PROVIDER=openai`

## 🔍 After Deployment
Once the build succeeds, you should see:
- ✅ Build completed successfully
- ✅ Service is live at: https://lenny-api-gpj1.onrender.com
- ✅ Health check endpoint: https://lenny-api-gpj1.onrender.com/health

## 🚨 If Build Still Fails
Let me know the error message and we'll troubleshoot further.
