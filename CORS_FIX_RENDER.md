# CORS Fix for Render Deployment

How to fix the CORS error when connecting Vercel frontend to Render backend.

---

## ❌ **Error You're Seeing**

```
Access to XMLHttpRequest at 'https://job-adventure.onrender.com/api/v1/auth/login' 
from origin 'https://job-adventure.vercel.app' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

---

## 🔍 **Root Cause**

Your backend on Render is not configured to allow requests from your Vercel frontend.

The CORS middleware in `backend/app/main.py` now uses **both**:
1. `allow_origins` - Reads from `ALLOWED_HOSTS` environment variable
2. `allow_origin_regex` - Regex pattern to match Vercel and Render URLs

---

## ✅ **Solution: Deploy Updated Code to Render**

### **Step 1: Commit and Push Changes**

```bash
# Check what changed
git status

# Add the changes
git add backend/app/main.py .env.example

# Commit
git commit -m "Fix CORS: Add allow_origin_regex for Vercel and Render"

# Push to GitHub
git push origin main
```

### **Step 2: Redeploy on Render**

**Option A: Automatic Deployment (if enabled)**
- Render will automatically detect the push and redeploy
- Wait 2-3 minutes for deployment to complete

**Option B: Manual Deployment**
1. Go to https://dashboard.render.com
2. Click on your **job-adventure** service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**
4. Wait for deployment to complete

### **Step 3: Verify CORS is Fixed**

After deployment completes:

1. Go to https://job-adventure.vercel.app/auth/login
2. Try to log in
3. Check browser console (F12) - no more CORS errors!

---

## 🎯 **What Was Changed**

### **File: `backend/app/main.py` (Line 153)**

**Added `allow_origin_regex`:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$|https://.*\.vercel\.app$|https://.*\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=600,
)
```

---

## 📊 **What This Regex Allows**

### ✅ **Local Development:**
- `http://localhost:3000`
- `http://localhost:8000`
- `https://localhost:3000`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8000`

### ✅ **Vercel (Production + Previews):**
- `https://job-adventure.vercel.app` ← Your production frontend
- `https://job-adventure-git-main.vercel.app` ← Preview deployments
- `https://job-adventure-pr-123.vercel.app` ← PR previews
- Any subdomain of `vercel.app`

### ✅ **Render (Backend):**
- `https://job-adventure.onrender.com` ← Your backend
- Any subdomain of `onrender.com`

---

## 🔧 **Alternative: Set Environment Variable (Optional)**

If you prefer to use environment variables instead of regex, you can set this on Render:

### **On Render Dashboard:**

1. Go to your service → **Environment**
2. Add variable:
   - **Key:** `ALLOWED_HOSTS`
   - **Value:** `https://job-adventure.vercel.app,https://job-adventure.onrender.com,http://localhost:3000`
3. Click **"Save Changes"**

**Note:** The regex approach is better because it automatically allows all Vercel preview deployments!

---

## 🧪 **Testing**

### **Test 1: Login from Vercel**
1. Go to https://job-adventure.vercel.app/auth/login
2. Enter credentials
3. Click "Login"
4. ✅ Should work without CORS errors

### **Test 2: Check Browser Console**
1. Open browser DevTools (F12)
2. Go to "Console" tab
3. Try logging in
4. ✅ No CORS errors should appear

### **Test 3: Check Network Tab**
1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Try logging in
4. Click on the login request
5. Check "Response Headers"
6. ✅ Should see: `Access-Control-Allow-Origin: https://job-adventure.vercel.app`

---

## 📝 **Regex Pattern Breakdown**

```regex
https?://(localhost|127\.0\.0\.1)(:\d+)?$
│      │                          │
│      │                          └─ Optional port (:3000, :8000)
│      └─ localhost OR 127.0.0.1
└─ http or https

|  ← OR operator

https://.*\.vercel\.app$
│       │              │
│       │              └─ Must end with .vercel.app
│       └─ Any subdomain (wildcard)
└─ HTTPS only

|  ← OR operator

https://.*\.onrender\.com$
│       │                │
│       │                └─ Must end with .onrender.com
│       └─ Any subdomain (wildcard)
└─ HTTPS only
```

---

## ✅ **Checklist**

- [x] Updated `backend/app/main.py` with `allow_origin_regex`
- [ ] Commit changes to Git
- [ ] Push to GitHub
- [ ] Wait for Render to redeploy (or trigger manual deploy)
- [ ] Test login from Vercel frontend
- [ ] Verify no CORS errors in browser console

---

## 🎉 **Expected Result**

After deploying:
- ✅ Vercel frontend can call Render backend
- ✅ No CORS errors
- ✅ Login works
- ✅ All API calls work
- ✅ Preview deployments also work

---

## 🚨 **Troubleshooting**

### **Still Getting CORS Errors?**

1. **Check Render deployment status:**
   - Make sure deployment completed successfully
   - Check logs for any errors

2. **Clear browser cache:**
   ```
   Ctrl+Shift+R (Windows/Linux)
   Cmd+Shift+R (Mac)
   ```

3. **Check Render logs:**
   - Go to Render dashboard → Your service → Logs
   - Look for CORS-related messages

4. **Verify the code is deployed:**
   - Go to https://job-adventure.onrender.com/docs
   - Check if the API is responding

5. **Check frontend environment variable:**
   - On Vercel dashboard → Your project → Settings → Environment Variables
   - Make sure `NEXT_PUBLIC_API_URL` is set to `https://job-adventure.onrender.com`

---

## 📚 **Additional Resources**

- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [MDN CORS Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Render Deployment Guide](https://render.com/docs/deploy-fastapi)

---

## ✅ **Status: Ready to Deploy**

Your code is now ready! Just commit, push, and let Render redeploy. 🚀

