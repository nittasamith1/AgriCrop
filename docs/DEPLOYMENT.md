# AgriCrop Deployment Guide

## Stack

| Layer | Service | Cost |
|---|---|---|
| Backend API | [Render](https://render.com) Web Service | Free |
| Database | [MongoDB Atlas](https://cloud.mongodb.com) M0 Cluster | Free |
| Frontend | [Vercel](https://vercel.com) | Free |
| File Storage | MongoDB GridFS (same Atlas cluster) | Free |

---

## 1. MongoDB Atlas Setup

You already have a cluster at `cluster0.xdax7ct.mongodb.net`. Make sure:

1. **Network Access** → Add `0.0.0.0/0` to allow access from Render's IPs
2. **Database Access** → Your user `db_user` has `readWrite` on `agricrop` DB
3. The connection string format should be:
   ```
   mongodb+srv://db_user:<password>@cluster0.xdax7ct.mongodb.net/?appName=Cluster0
   ```

---

## 2. Deploy Backend to Render

### Option A: render.yaml (recommended)
1. Push your code to GitHub
2. Go to [render.com/dashboard](https://dashboard.render.com) → **New → Blueprint**
3. Connect your GitHub repo — Render reads `render.yaml` automatically
4. Set these **environment variables** in the Render dashboard:
   - `MONGODB_URI` → your Atlas URI
   - `SECRET_KEY` → a random 32+ character string (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
5. Deploy → your API will be live at `https://agricrop-backend.onrender.com`

### Option B: Manual
1. **New Web Service** → Connect GitHub repo
2. **Build Command:** `pip install -r requirements.txt`
3. **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Python Version:** 3.11
5. Add all env vars from `.env.example`

### Verify Backend
```bash
curl https://agricrop-backend.onrender.com/api/health
# → {"status":"healthy","database":"connected",...}
```

---

## 3. Deploy Frontend to Vercel

### Step 1: Update API URL
Edit `frontend/assets/js/api.js` line ~10:
```js
const API_BASE_URL = "https://agricrop-backend.onrender.com/api/v1";
```

### Step 2: Update vercel.json
Edit `vercel.json` to point the API proxy to your real Render URL:
```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://agricrop-backend.onrender.com/api/$1"
    }
  ]
}
```

### Step 3: Deploy
1. Go to [vercel.com](https://vercel.com) → **New Project** → Import GitHub repo
2. **Root Directory** → Set to `frontend/`
3. **Framework Preset** → Other
4. Deploy → your frontend is live at `https://agricrop.vercel.app`

---

## 4. Docker (Self-hosted / VPS)

For deploying on a VPS (DigitalOcean, AWS EC2, etc.):

```bash
# Clone repo
git clone https://github.com/youruser/agricrop.git
cd agricrop

# Create .env from example
cp .env.example .env
# Edit .env with your real MongoDB Atlas URI and SECRET_KEY

# Build and run
docker compose up -d --build

# Check logs
docker compose logs -f backend
```

The backend will be at `http://your-server-ip:8000`

---

## 5. Adding AI Models

The app runs in **stub mode** until real models are provided.

### Disease Model
Place your trained MobileNetV2 Keras model at:
```
ai_models/saved_models/disease_model.h5
```
Expected input shape: `(1, 224, 224, 3)`, output: 38 softmax classes.

### Soil Model
Place your trained model at:
```
ai_models/saved_models/soil_model.pkl
```
Expected: sklearn-compatible model with `predict([[temp, humidity, rainfall, wind_speed, soil_idx, prev_moisture]])`.

---

## 6. Email (SMTP) Setup

To enable password-reset and verification emails, set in `.env`:
```
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-gmail@gmail.com
SMTP_PASSWORD=your-app-password    # Gmail App Password (not regular password)
EMAIL_FROM=noreply@agricrop.ai
```

> **Tip:** For Gmail, enable 2FA and generate an App Password at https://myaccount.google.com/apppasswords

---

## 7. Environment Variables Reference

Copy `.env.example` and fill in:

```env
# Core
APP_NAME=AgriCrop
APP_ENV=production
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">

# MongoDB Atlas
MONGODB_URI=mongodb+srv://db_user:PASSWORD@cluster0.xdax7ct.mongodb.net/?appName=Cluster0
MONGODB_DB_NAME=agricrop

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMTP (optional)
EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# CORS (comma-separated; * for dev only)
ALLOWED_ORIGINS=https://agricrop.vercel.app,http://localhost:8080

# Logging
LOG_LEVEL=INFO
```
