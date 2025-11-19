# Vercel Deployment Guide - Frontend (Next.js)

Complete step-by-step guide to deploy your Next.js frontend to Vercel.

---

## 📋 What You'll Deploy

- **Frontend**: Next.js 14 application with React
- **Framework**: Next.js with App Router
- **Styling**: Tailwind CSS with custom design system
- **Features**: Authentication, file uploads, job matching UI

---

## 🚀 Quick Start (4 Steps)

1. **Sign up**: https://vercel.com (use GitHub login)
2. **New Project** → Import `job-match` repo
3. **Configure** → Root Directory: `frontend`
4. **Add Variable** → `NEXT_PUBLIC_API_URL` = Your Railway backend URL

---

## 📝 Detailed Step-by-Step

### Step 1: Get Your Backend URL

Before deploying frontend, you need your Railway backend URL:

```
https://your-backend.up.railway.app
```

If you haven't deployed the backend yet, see `DEPLOYMENT_GUIDE.md` first.

---

### Step 2: Sign Up for Vercel

1. Go to https://vercel.com
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Vercel to access your repositories

---

### Step 3: Import Your Project

1. In Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find your repository: **`job-match`**
3. Click **"Import"**

---

### Step 4: Configure Project Settings

Vercel will show a configuration screen:

#### Framework Preset
- **Auto-detected**: Next.js ✅
- Leave as is

#### Root Directory
- Click **"Edit"** next to Root Directory
- Enter: `frontend`
- Click **"Continue"**

#### Build Settings
- **Build Command**: `npm run build` (default)
- **Output Directory**: `.next` (default)
- **Install Command**: `npm install` (default)
- Leave these as default ✅

#### Environment Variables
Click **"Environment Variables"** and add:

**Variable 1:**
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: `https://your-backend.up.railway.app`
- **Environment**: Production, Preview, Development (select all)

Replace `your-backend.up.railway.app` with your actual Railway URL!

---

### Step 5: Deploy

1. Click **"Deploy"**
2. Wait for deployment (~2-3 minutes)
3. Watch the build logs
4. You'll see "Congratulations!" when done ✅

---

### Step 6: Get Your Frontend URL

After deployment:

1. You'll get a URL like: `https://your-app.vercel.app`
2. Click **"Visit"** to open your app
3. **Copy this URL** - you'll need it for CORS configuration

---

### Step 7: Update Backend CORS

Now update your Railway backend to allow requests from Vercel:

1. Go to **Railway dashboard**
2. Click on your **backend service**
3. Go to **"Variables"** tab
4. Find `ALLOWED_HOSTS` variable
5. Update it to:

```json
["https://your-app.vercel.app","http://localhost:3000"]
```

6. Replace `your-app.vercel.app` with your actual Vercel domain
7. Click **"Save"** (Railway will auto-redeploy)

---

### Step 8: Test Your Application

Visit your Vercel URL and test:

1. ✅ Home page loads
2. ✅ Navigation works
3. ✅ Can register a new account
4. ✅ Can login
5. ✅ Can access dashboard
6. ✅ Can upload files

---

## 🔧 Configuration Files

These files are already created for you:

### `frontend/vercel.json`
```json
{
  "buildCommand": "npm run build",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

### `frontend/.env.production.example`
Template for environment variables (for reference only).

---

## 🎨 Custom Domain (Optional)

### Add Your Own Domain

1. Go to Vercel dashboard → Your project
2. Click **"Settings"** → **"Domains"**
3. Click **"Add"**
4. Enter your domain: `yourdomain.com`
5. Follow DNS configuration instructions
6. Wait for DNS propagation (~5-60 minutes)

### Update Backend CORS

After adding custom domain, update Railway CORS:

```json
["https://yourdomain.com","https://your-app.vercel.app","http://localhost:3000"]
```

---

## 🐛 Common Issues

### Can't Connect to Backend

**Error**: `Failed to fetch` or `Network Error`

**Solution**:
1. Check `NEXT_PUBLIC_API_URL` is set correctly
2. Make sure it includes `https://` and NO trailing slash
3. Verify backend is running on Railway
4. Check CORS is configured in backend

### Environment Variable Not Working

**Error**: `NEXT_PUBLIC_API_URL is undefined`

**Solution**:
1. Make sure variable name starts with `NEXT_PUBLIC_`
2. Redeploy after adding variables
3. Go to **Deployments** → Click **"..."** → **"Redeploy"**

### 404 on Page Refresh

**Error**: Page works on navigation but 404 on refresh

**Solution**:
- Vercel handles this automatically for Next.js
- If issue persists, check `vercel.json` configuration

### Build Fails

**Error**: `Module not found` or `Cannot find module`

**Solution**:
1. Check `package.json` has all dependencies
2. Try deleting `node_modules` and `package-lock.json` locally
3. Run `npm install` and test locally
4. Push changes and redeploy

---

## 📊 Vercel Free Tier Limits

✅ **What You Get:**
- **Deployments**: Unlimited
- **Bandwidth**: 100GB/month
- **Build Time**: 6000 minutes/month
- **Serverless Functions**: 100GB-hours
- **Edge Functions**: 500,000 invocations
- **Custom Domains**: Unlimited
- **HTTPS**: Automatic
- **CDN**: Global

⚠️ **Limits:**
- 100GB bandwidth/month (plenty for most apps)
- Upgrade to Pro ($20/month) for more

---

## ✅ Success Checklist

- [ ] Frontend deployed to Vercel
- [ ] Environment variable `NEXT_PUBLIC_API_URL` set
- [ ] Can access frontend URL
- [ ] Backend CORS updated with Vercel URL
- [ ] Can register and login
- [ ] Can upload files and see matches
- [ ] All pages load correctly

---

## 🎯 Post-Deployment

### Automatic Deployments

Vercel automatically deploys when you push to GitHub:

- **Push to `main`** → Production deployment
- **Push to other branches** → Preview deployment
- **Pull requests** → Preview deployment with unique URL

### View Deployments

1. Go to Vercel dashboard → Your project
2. Click **"Deployments"** tab
3. See all deployments with logs and previews

### Rollback

If something breaks:

1. Go to **"Deployments"**
2. Find a working deployment
3. Click **"..."** → **"Promote to Production"**

---

## 💡 Pro Tips

### Preview Deployments

Every branch and PR gets a unique URL:
- `https://your-app-git-feature-branch.vercel.app`
- Perfect for testing before merging!

### Environment Variables per Environment

You can set different values for:
- **Production**: Live site
- **Preview**: Branch deployments
- **Development**: Local development

### Analytics

Enable Vercel Analytics:
1. Go to **"Analytics"** tab
2. Click **"Enable"**
3. Get insights on page views, performance, etc.

### Speed Insights

Enable Web Vitals monitoring:
1. Go to **"Speed Insights"** tab
2. Click **"Enable"**
3. Monitor Core Web Vitals

---

## 🔗 Useful Links

- **Vercel Dashboard**: https://vercel.com/dashboard
- **Vercel Docs**: https://vercel.com/docs
- **Next.js Docs**: https://nextjs.org/docs
- **Support**: https://vercel.com/support

---

## 🎉 You're Live!

**Your application is now deployed!**

- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-backend.up.railway.app`

### Share Your App

Your app is now accessible to anyone with the URL!

### Next Steps

1. 📧 Set up email notifications (SendGrid, Resend)
2. 📊 Add analytics (Google Analytics, Vercel Analytics)
3. 🔒 Add custom domain
4. 💾 Set up file storage (S3, Cloudinary)
5. 🔔 Set up error tracking (Sentry)

---

**Congratulations! Your app is live! 🚀**

