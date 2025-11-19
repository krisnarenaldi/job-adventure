# 🚀 Quick Deployment Guide

Deploy your Resume Match AI app in **15 minutes**!

---

## 📦 What You're Deploying

- **Frontend** (Next.js) → Vercel
- **Backend** (FastAPI) → Railway
- **Database** (PostgreSQL) → Railway

---

## ⚡ Quick Steps

### 1️⃣ Deploy Backend to Railway (5 min)

```bash
# 1. Go to https://railway.app
# 2. New Project → Deploy from GitHub → Select "job-match"
# 3. Settings → Root Directory → "backend"
# 4. Add PostgreSQL: + New → Database → PostgreSQL
# 5. Add Variables (see below)
```

**Required Variables:**
```bash
SECRET_KEY=<generate-random-string>
ALLOWED_HOSTS=["http://localhost:3000"]
PROJECT_NAME=Resume Match AI
API_V1_STR=/api/v1
ENVIRONMENT=production
MAX_FILE_SIZE=10485760
UPLOAD_DIR=/tmp/uploads
```

**Generate SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Get Backend URL:**
- Settings → Generate Domain
- Copy: `https://your-backend.up.railway.app`

---

### 2️⃣ Deploy Frontend to Vercel (5 min)

```bash
# 1. Go to https://vercel.com
# 2. New Project → Import "job-match"
# 3. Root Directory → "frontend"
# 4. Add Environment Variable:
#    NEXT_PUBLIC_API_URL = https://your-backend.up.railway.app
# 5. Deploy
```

**Get Frontend URL:**
- Copy: `https://your-app.vercel.app`

---

### 3️⃣ Update CORS (2 min)

```bash
# 1. Go back to Railway
# 2. Backend service → Variables
# 3. Update ALLOWED_HOSTS:
```

```json
["https://your-app.vercel.app","http://localhost:3000"]
```

---

### 4️⃣ Test (3 min)

Visit: `https://your-app.vercel.app`

- ✅ Register account
- ✅ Login
- ✅ Upload resume
- ✅ Create job
- ✅ See matches

---

## 📁 Files Created

All configuration files are ready:

```
✅ backend/Procfile
✅ backend/railway.json
✅ backend/nixpacks.toml
✅ backend/requirements.txt (CPU-optimized)
✅ frontend/vercel.json
✅ frontend/.env.production.example
```

---

## 🐛 Troubleshooting

### Backend won't start
- Check Root Directory = `backend`
- Verify SECRET_KEY is set
- Check logs in Railway

### Frontend can't connect
- Verify NEXT_PUBLIC_API_URL is set
- Check CORS in backend ALLOWED_HOSTS
- Redeploy frontend after adding variables

### Database errors
- Make sure PostgreSQL is running
- Check DATABASE_URL is linked

---

## 📚 Detailed Guides

- **Full Guide**: `DEPLOYMENT_GUIDE.md`
- **Railway Details**: `RAILWAY_DEPLOYMENT.md`
- **Vercel Details**: `VERCEL_DEPLOYMENT.md`

---

## 🎯 Your URLs

After deployment, save these:

```
Frontend: https://your-app.vercel.app
Backend:  https://your-backend.up.railway.app
API Docs: https://your-backend.up.railway.app/docs
```

---

## 💰 Costs

**Free Tier:**
- Railway: 500 hours/month (enough for 24/7)
- Vercel: 100GB bandwidth/month
- **Total: $0/month** ✅

**Paid Tier (Optional):**
- Railway Hobby: $5/month (always-on, no sleep)
- Vercel Pro: $20/month (more bandwidth)

---

## ✅ Checklist

- [ ] Backend deployed to Railway
- [ ] PostgreSQL database created
- [ ] Backend environment variables set
- [ ] Backend URL obtained
- [ ] Frontend deployed to Vercel
- [ ] Frontend environment variable set
- [ ] CORS updated in backend
- [ ] Can register and login
- [ ] Can upload and match

---

## 🎉 Done!

Your app is live! Share it with the world! 🚀

**Need help?** Check the detailed guides or Railway/Vercel documentation.

