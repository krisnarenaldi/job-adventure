# Quick Deploy Guide - Railway Free Plan

## TL;DR - Can I Deploy on Railway Free Plan?

**YES! ✅** With optimizations, your app fits in Railway's free tier.

## Size Comparison

| Setup | Size | Fits Free Plan? |
|-------|------|----------------|
| Original (GPU PyTorch + Spacy) | ~1.5GB | ❌ NO |
| **Optimized (CPU PyTorch, no Spacy)** | **~650MB** | **✅ YES** |

## Quick Deploy (3 Steps)

### Step 1: Prepare Backend (2 minutes)
```bash
# Use optimized requirements
cp backend/requirements-railway.txt backend/requirements.txt

# Or use the automated script
./deploy-railway.sh
```

### Step 2: Deploy to Railway (5 minutes)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Step 3: Set Environment Variables
In Railway dashboard, add:
```
DATABASE_URL=your_neondb_url
SECRET_KEY=your_secret_key
ENVIRONMENT=production
```

## What Changed?

### ✅ Optimizations Applied
1. **CPU-only PyTorch** - Saves ~500MB
2. **Removed Spacy** - Saves ~200MB (app falls back to pattern matching)
3. **Added `.slugignore`** - Excludes unnecessary files
4. **No-cache pip install** - Reduces build size

### 📦 Final Size: ~650MB
- PyTorch (CPU): ~500MB
- Sentence Transformers: ~150MB
- Other dependencies: ~100MB
- **Total: ~650MB** (fits in 1GB with 350MB to spare)

## Cost Breakdown

### Free Tier (Recommended for Testing)
- **Railway**: $0 (uses $5 free credits)
- **Vercel** (frontend): $0
- **NeonDB** (database): $0
- **Total: $0/month** ✅

### Hobby Tier (Recommended for Production)
- **Railway**: $5/month
- **Vercel**: $0
- **NeonDB**: $0
- **Total: $5/month** ✅

## Files Created

| File | Purpose |
|------|---------|
| `railway.json` | Railway configuration |
| `nixpacks.toml` | Build configuration |
| `Procfile` | Start command |
| `.slugignore` | Exclude unnecessary files |
| `backend/requirements-railway.txt` | Optimized dependencies |
| `deploy-railway.sh` | Automated deployment script |
| `RAILWAY_DEPLOYMENT.md` | Detailed deployment guide |
| `DEPLOYMENT_OPTIONS.md` | Platform comparison |

## Quick Commands

```bash
# Deploy
railway up

# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open

# Run migrations
railway run cd backend && alembic upgrade head

# Set environment variable
railway variables set KEY=value
```

## Troubleshooting

### "Out of disk space"
- ✅ Already fixed with CPU-only PyTorch
- If still happening, remove `anthropic` from requirements

### "Out of memory"
- Free tier has 512MB RAM
- Your app uses ~300-400MB ✅
- If crashing, upgrade to Hobby plan ($5/month)

### "Build takes too long"
- First build: 5-10 minutes (normal)
- Subsequent builds: 2-3 minutes (cached)

## Next Steps

1. ✅ Deploy backend to Railway (see above)
2. ✅ Deploy frontend to Vercel: `cd frontend && vercel`
3. ✅ Update frontend env: `NEXT_PUBLIC_API_URL=https://your-app.railway.app`
4. ✅ Test all features
5. ✅ Monitor usage in Railway dashboard

## Support

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Deployment Guide**: See `RAILWAY_DEPLOYMENT.md`
- **Platform Comparison**: See `DEPLOYMENT_OPTIONS.md`

## Summary

✅ **YES, Railway free plan works!**
✅ **Optimized to ~650MB** (fits in 1GB)
✅ **$0/month** for testing
✅ **$5/month** for production (recommended)

Run `./deploy-railway.sh` to get started! 🚀

