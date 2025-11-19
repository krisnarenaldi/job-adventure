# Deployment Guide - Vercel (Frontend) + Railway (Backend)

This guide will help you deploy your Resume Match AI application with:
- **Frontend (Next.js)** → Vercel
- **Backend (FastAPI)** → Railway

---

## 📋 Prerequisites

Before you start, make sure you have:

1. ✅ GitHub account (to push your code)
2. ✅ Vercel account (sign up at https://vercel.com)
3. ✅ Railway account (sign up at https://railway.app)
4. ✅ Your code pushed to a GitHub repository

---

## 🚀 Part 1: Deploy Backend to Railway

### Step 1: Prepare Backend for Railway

Your backend is already optimized for Railway! The following files are ready:

✅ `backend/requirements.txt` - CPU-optimized dependencies (~650MB)
✅ `backend/Procfile` - Railway startup command
✅ `backend/railway.json` - Railway configuration
✅ `backend/.env.example` - Environment variables template

### Step 2: Create Railway Project

1. **Go to Railway**: https://railway.app
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Connect your GitHub account** (if not already connected)
5. **Select your repository**: `job-match`
6. **Railway will detect your app automatically**

### Step 3: Configure Root Directory

Since your backend is in a subfolder, you need to tell Railway:

1. In Railway dashboard, click on your service
2. Go to **Settings** tab
3. Find **"Root Directory"** setting
4. Set it to: `backend`
5. Click **Save**

### Step 4: Set Environment Variables

In Railway dashboard, go to **Variables** tab and add these:

```bash
# Database (Railway provides PostgreSQL)
DATABASE_URL=<Railway will provide this - see Step 5>

# Security
SECRET_KEY=<generate-a-random-secret-key-here>
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services (Optional - for explanations)
ANTHROPIC_API_KEY=<your-anthropic-api-key-if-you-have-one>

# CORS - Add your Vercel domain after deployment
ALLOWED_HOSTS=["https://your-app.vercel.app","http://localhost:3000"]

# Application
PROJECT_NAME=Resume Match AI
VERSION=1.0.0
API_V1_STR=/api/v1
ENVIRONMENT=production
LOG_LEVEL=INFO

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/tmp/uploads
```

**To generate SECRET_KEY**, run this in your terminal:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 5: Add PostgreSQL Database

1. In Railway dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create a database and provide `DATABASE_URL`
4. The `DATABASE_URL` will be automatically available to your backend service
5. **Copy the DATABASE_URL** and add it to your backend variables (or Railway links it automatically)

### Step 6: Deploy Backend

1. Railway will automatically deploy when you push to GitHub
2. Or click **"Deploy"** button in Railway dashboard
3. Wait for deployment to complete (~3-5 minutes)
4. You'll get a URL like: `https://your-backend.up.railway.app`

### Step 7: Test Backend

Visit: `https://your-backend.up.railway.app/docs`

You should see the FastAPI Swagger documentation! ✅

---

## 🎨 Part 2: Deploy Frontend to Vercel

### Step 1: Prepare Frontend for Vercel

Create a `vercel.json` file in the `frontend` folder to configure the deployment.

### Step 2: Create Environment Variable File

In your `frontend` folder, you need to set the backend API URL.

Create `frontend/.env.production` (I'll create this for you in the next step).

### Step 3: Deploy to Vercel

**Option A: Deploy via Vercel Dashboard (Recommended)**

1. **Go to Vercel**: https://vercel.com
2. **Click "Add New Project"**
3. **Import your GitHub repository**: `job-match`
4. **Configure Project**:
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: Click "Edit" and set to `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)
   - **Install Command**: `npm install` (default)

5. **Add Environment Variables**:
   - Click "Environment Variables"
   - Add: `NEXT_PUBLIC_API_URL` = `https://your-backend.up.railway.app`
   - (Replace with your actual Railway backend URL)

6. **Click "Deploy"**
7. Wait for deployment (~2-3 minutes)
8. You'll get a URL like: `https://your-app.vercel.app`

**Option B: Deploy via Vercel CLI**

```bash
# Install Vercel CLI
npm i -g vercel

# Go to frontend folder
cd frontend

# Login to Vercel
vercel login

# Deploy
vercel

# Follow the prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? job-match-frontend
# - Directory? ./ (current directory)
# - Override settings? No

# For production deployment
vercel --prod
```

### Step 4: Update CORS in Backend

Now that you have your Vercel URL, update the backend CORS settings:

1. Go to **Railway dashboard**
2. Go to your backend service → **Variables**
3. Update `ALLOWED_HOSTS`:
   ```
   ["https://your-app.vercel.app","http://localhost:3000"]
   ```
4. Replace `your-app.vercel.app` with your actual Vercel domain
5. Click **Save** (Railway will redeploy automatically)

---

## 🔧 Part 3: Final Configuration

### Update Frontend API URL

If you didn't set it during deployment:

1. Go to **Vercel dashboard**
2. Select your project
3. Go to **Settings** → **Environment Variables**
4. Add or update:
   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://your-backend.up.railway.app`
   - **Environment**: Production, Preview, Development (select all)
5. Click **Save**
6. Go to **Deployments** tab
7. Click **"Redeploy"** on the latest deployment

### Test the Full Application

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Try to register a new account
3. Try to login
4. Upload a resume and job description
5. Check if matching works

---

## 📝 Important Notes

### Backend (Railway)

✅ **Free Tier Limits**:
- 500 hours/month (enough for 24/7 if you have one service)
- 1GB RAM
- 1GB Disk
- Sleeps after 30 minutes of inactivity (wakes up on first request)

✅ **Database**:
- Railway PostgreSQL is separate from your backend
- Free tier: 1GB storage
- Automatically backed up

✅ **File Uploads**:
- Railway uses ephemeral storage
- Files in `/tmp` are deleted on restart
- For production, use S3 or Cloudinary for file storage

### Frontend (Vercel)

✅ **Free Tier Limits**:
- Unlimited deployments
- 100GB bandwidth/month
- Automatic HTTPS
- Global CDN

✅ **Environment Variables**:
- Must start with `NEXT_PUBLIC_` to be accessible in browser
- Changes require redeployment

✅ **Custom Domain** (Optional):
- Go to Vercel → Settings → Domains
- Add your custom domain
- Update DNS records as instructed

---

## 🐛 Troubleshooting

### Backend Issues

**Problem**: Backend won't start
- Check Railway logs: Dashboard → Deployments → View Logs
- Verify `DATABASE_URL` is set
- Verify `SECRET_KEY` is set

**Problem**: Database connection error
- Make sure PostgreSQL service is running
- Check if `DATABASE_URL` is correct
- Railway should auto-link the database

**Problem**: CORS errors
- Update `ALLOWED_HOSTS` in Railway variables
- Include your Vercel domain with `https://`

### Frontend Issues

**Problem**: Can't connect to backend
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Make sure it includes `https://` and no trailing slash
- Redeploy after changing environment variables

**Problem**: 404 errors on refresh
- Vercel handles this automatically for Next.js
- Check if `vercel.json` is configured correctly

---

## 🎉 Success Checklist

- [ ] Backend deployed to Railway
- [ ] PostgreSQL database created and linked
- [ ] Backend environment variables set
- [ ] Backend API docs accessible at `/docs`
- [ ] Frontend deployed to Vercel
- [ ] Frontend environment variable `NEXT_PUBLIC_API_URL` set
- [ ] CORS configured in backend with Vercel URL
- [ ] Can register and login
- [ ] Can upload files and see matches

---

## 📚 Next Steps

1. **Custom Domain**: Add your own domain to Vercel
2. **Monitoring**: Set up error tracking (Sentry, LogRocket)
3. **Analytics**: Add Google Analytics or Vercel Analytics
4. **File Storage**: Migrate to S3/Cloudinary for persistent file storage
5. **Email**: Add email service for notifications (SendGrid, Resend)

---

**Need help?** Check the detailed guides I'll create next:
- `VERCEL_DEPLOYMENT.md` - Detailed Vercel guide
- `RAILWAY_DEPLOYMENT.md` - Detailed Railway guide

