# 🚀 Wealth Advisor - Production Deployment Guide

This guide walks you through deploying Wealth Advisor to production using **Supabase** (database), **Railway/Render** (backend), and **Firebase Hosting** (frontend).

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Firebase       │────▶│  Railway/Render │────▶│   Supabase     │
│  Hosting        │     │  (FastAPI)      │     │  (PostgreSQL)   │
│  (React App)    │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
     Frontend              Backend API            Database
```

---

## Step 1: Set Up Supabase (Database)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click **"New Project"**
3. Choose your organization and set:
   - **Project name**: `wealth-advisor`
   - **Database password**: Generate a strong password (save it!)
   - **Region**: Choose closest to your users
4. Click **"Create new project"** and wait for setup

### 1.2 Get Database Connection String

1. Go to **Project Settings** → **Database**
2. Scroll to **Connection String** section
3. Select **URI** tab
4. Copy the connection string, it looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual database password

### 1.3 Get API Keys (Optional - for future Supabase Auth)

1. Go to **Project Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://[PROJECT-REF].supabase.co`
   - **anon public key**: For client-side auth
   - **service_role key**: For server-side (keep secret!)

---

## Step 2: Deploy Backend to Railway

### 2.1 Create Railway Account & Project

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository or click **"Configure GitHub App"** to grant access
4. Select the repository containing your wealth-advisor code

### 2.2 Configure Environment Variables

1. In your Railway project, go to **Variables** tab
2. Add these environment variables:

```bash
# Required
SECRET_KEY=<generate-a-long-random-string-32-chars>
DATABASE_URL=<your-supabase-connection-string>
CORS_ORIGINS=https://your-app.web.app,http://localhost:5173

# Optional
DEMO_MODE=false
DEBUG=false
```

**Tip**: Generate a secret key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2.3 Configure Build Settings

Railway should auto-detect Python. If not, set:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 2.4 Set Root Directory (if needed)

If your backend is in a subdirectory:
1. Go to **Settings** → **Root Directory**
2. Set it to `wealth advisor/backend`

### 2.5 Deploy & Get URL

1. Click **Deploy** or it auto-deploys on push
2. Once deployed, click on your service
3. Go to **Settings** → **Domain**
4. Click **Generate Domain** to get your URL like `https://wealth-advisor-api-production.up.railway.app`

---

## Alternative: Deploy Backend to Render

### 3.1 Create Render Account & Service

1. Go to [render.com](https://render.com) and sign up
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repo

### 3.2 Configure Service

- **Name**: `wealth-advisor-api`
- **Root Directory**: `wealth advisor/backend`
- **Runtime**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3.3 Add Environment Variables

Same as Railway - add in the Environment section:
- `SECRET_KEY`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `DEMO_MODE=false`

### 3.4 Deploy

Click **"Create Web Service"** and wait for deployment.

---

## Step 4: Deploy Frontend to Firebase

### 4.1 Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### 4.2 Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add project"**
3. Name it `wealth-advisor` (or similar)
4. Disable Google Analytics (optional)
5. Click **"Create project"**

### 4.3 Initialize Firebase in Frontend

```bash
cd "wealth advisor/frontend"
firebase init hosting
```

When prompted:
- **Select project**: Choose your Firebase project
- **Public directory**: `dist`
- **Single-page app**: Yes
- **Automatic builds**: No

### 4.4 Update Frontend Configuration

1. Edit `.firebaserc`:
```json
{
  "projects": {
    "default": "your-firebase-project-id"
  }
}
```

2. Create `.env` file (copy from `env.template`):
```bash
VITE_API_URL=https://your-backend-url.railway.app
```

### 4.5 Build and Deploy

```bash
# Build the app
npm run build

# Deploy to Firebase
npm run deploy
# or
firebase deploy --only hosting
```

Your app will be live at: `https://your-project-id.web.app`

---

## Step 5: Update CORS Origins

After getting your Firebase URL, update the backend's `CORS_ORIGINS`:

**Railway/Render Dashboard:**
```
CORS_ORIGINS=https://your-project.web.app,https://your-custom-domain.com
```

---

## Step 6: Enable New User Registration

To allow any user to sign up (not just the demo account):

### Option A: Keep Demo Mode (Simple)

Set `DEMO_MODE=true` in backend. Users can:
1. Enter any phone number
2. Receive OTP in the response (for testing)

### Option B: Real SMS OTP (Production)

1. Sign up for [Twilio](https://twilio.com) or [MSG91](https://msg91.com)
2. Add SMS provider credentials to backend env vars
3. Update `auth.py` to send real SMS
4. Set `DEMO_MODE=false`

---

## Custom Domain Setup

### Firebase Hosting
1. Go to Firebase Console → Hosting
2. Click **"Add custom domain"**
3. Follow the DNS verification steps

### Railway
1. Go to your Railway service → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed

---

## Database Migrations

When you need to update the database schema:

```bash
# Connect to your local environment first
cd "wealth advisor/backend"
source venv/bin/activate

# Run the app once to create tables
DATABASE_URL="your-supabase-url" python -c "from app.database import init_db; init_db()"
```

---

## Monitoring & Logs

### Railway
- Dashboard shows real-time logs
- Click your service → **"Logs"** tab

### Render
- Dashboard → Your service → **"Logs"**

### Firebase
- Firebase Console → Hosting → **"Usage"**

---

## Cost Estimates (Free Tiers)

| Service | Free Tier |
|---------|-----------|
| Supabase | 500MB database, 2GB bandwidth |
| Railway | $5 free credits/month |
| Render | 750 hours/month |
| Firebase | 10GB hosting, 360MB storage |

**Total estimated cost**: $0/month for small to medium usage!

---

## Troubleshooting

### CORS Errors
- Make sure `CORS_ORIGINS` includes your frontend URL
- Check there are no trailing slashes in URLs

### Database Connection Failed
- Verify `DATABASE_URL` has correct password
- Check Supabase project is active (not paused)
- Ensure IP is not blocked in Supabase settings

### 502/503 Errors
- Check Railway/Render logs for startup errors
- Verify all environment variables are set
- Make sure `PORT` is being used from env var

### Frontend Can't Connect to Backend
- Verify `VITE_API_URL` is set correctly in `.env`
- Rebuild frontend after env changes: `npm run build`
- Check backend is running and responding at `/api/health`

---

## Quick Commands Reference

```bash
# Backend (Railway CLI)
railway login
railway link
railway up

# Frontend (Firebase CLI)
firebase login
firebase init hosting
npm run build
firebase deploy --only hosting

# Preview deployment (Firebase)
npm run deploy:preview
```

---

## Security Checklist

- [ ] Changed `SECRET_KEY` from default
- [ ] Set `DEMO_MODE=false` for production
- [ ] Set `DEBUG=false` for production
- [ ] CORS origins are restricted to your domains
- [ ] Database password is strong and secret
- [ ] HTTPS is enabled (automatic on Railway/Render/Firebase)

---

Happy deploying! 🎉

