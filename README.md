# 🌱 AgriCrop — AI-Powered Smart Agriculture Platform

> **Production-ready** enterprise AI application for crop disease detection, soil moisture prediction, GIS farm monitoring, and precision irrigation recommendations.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-7.0-47A248?logo=mongodb)](https://www.mongodb.com/atlas)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🦠 **Disease Detection** | MobileNetV2 AI model for leaf disease diagnosis (38 classes) |
| 💧 **Soil Prediction** | DenseNN predicts moisture % from env inputs |
| 🗺️ **GIS Monitoring** | Leaflet.js interactive map with severity markers |
| 📊 **Analytics Dashboard** | Chart.js visualisations of farm health trends |
| 📄 **PDF Reports** | Auto-generated disease/soil/combined farm reports |
| 🔔 **Notifications** | Real-time alerts for high-severity detections |
| 👤 **Admin Dashboard** | User management, system stats, activity logs |
| 🔐 **JWT Auth** | Secure login, refresh tokens, password reset via email |
| 📦 **GridFS Storage** | Leaf images and PDFs stored in MongoDB GridFS |

---

## 🏗️ Architecture

```
AgriCrop/
├── backend/                    # FastAPI Python Backend
│   ├── main.py                 # App entry point, middleware, routers
│   ├── config.py               # Pydantic settings (env vars)
│   ├── database.py             # Motor (async MongoDB) + GridFS
│   ├── dependencies.py         # JWT guards (get_current_user, require_admin)
│   ├── routers/
│   │   ├── auth.py             # Register, login, refresh, reset, farms
│   │   ├── disease.py          # Leaf image upload + AI prediction
│   │   ├── soil.py             # Soil moisture prediction
│   │   ├── map_router.py       # GIS markers and farm boundaries
│   │   ├── history.py          # Prediction history + pagination
│   │   ├── notifications.py    # User notifications
│   │   ├── reports.py          # PDF report generation
│   │   ├── admin.py            # Admin-only management
│   │   └── files.py            # GridFS file streaming
│   ├── services/
│   │   ├── auth_service.py     # JWT issue/verify, bcrypt hash
│   │   ├── mongodb_service.py  # Generic async CRUD
│   │   ├── gridfs_service.py   # GridFS upload/download
│   │   ├── email_service.py    # SMTP / token links
│   │   ├── notification_service.py
│   │   └── report_service.py
│   ├── ai/
│   │   ├── disease_predictor.py   # TF/Keras MobileNetV2 inference
│   │   ├── soil_predictor.py      # DenseNN soil moisture
│   │   └── recommendation_engine.py  # Irrigation recommendations
│   ├── models/                 # Pydantic schemas
│   └── utils/                  # helpers, validators
├── frontend/                   # Vanilla JS / Bootstrap 5 SPA
│   ├── index.html
│   ├── pages/                  # login, register, dashboard, upload, map…
│   └── assets/
│       ├── css/
│       └── js/
│           ├── auth.js         # JWT session management (auto-refresh)
│           └── api.js          # Axios-like fetch wrapper with 401 retry
├── ai_models/saved_models/     # .h5 / .keras model files (gitignored)
├── datasets/                   # Training data (gitignored)
├── docker-compose.yml          # Local dev with mongo container
├── Dockerfile.backend          # Multi-stage production build
├── render.yaml                 # One-click Render deploy
└── vercel.json                 # Vercel frontend deploy + API proxy
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- Python 3.11+
- MongoDB Atlas account (free tier works)

### 1. Clone & Install
```bash
git clone https://github.com/youruser/agricrop.git
cd agricrop
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and set:
#   MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
#   SECRET_KEY=<any 32+ char random string>
```

### 3. Run Backend
```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Open Frontend
Open `frontend/index.html` in your browser, or serve it with:
```bash
python -m http.server 8080 --directory frontend
```

Then visit `http://localhost:8080`

### 3. Training AI Models Locally

If you wish to retrain the models with your own data:

```bash
# Generate synthetic soil data (optional)
python3 -c "import pandas as pd; ..." # see scripts

# Train Soil model
python3 -m ai_models.soil_model.train_soil_model

# Train Disease model (requires PlantVillage dataset)
python3 -m ai_models.disease_model.train_disease_model
```

---

## 🌐 Production Deployment

### Backend → Render
1. Push code to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Connect your repo — Render auto-detects `render.yaml`
4. Set `MONGODB_URI` and `SECRET_KEY` in the Render dashboard

### Frontend → Vercel
1. Import the repo on [vercel.com](https://vercel.com)
2. Set **Root Directory** to `frontend/`
3. Update `vercel.json` → replace `agricrop-backend.onrender.com` with your Render URL
4. Deploy

### Docker (Self-hosted)
```bash
docker compose up -d
```

---

## 🔑 API Reference

Interactive docs available at: `http://localhost:8000/api/docs`

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/auth/me` | Get profile |
| `POST` | `/api/v1/auth/change-password` | Change password |
| `POST` | `/api/v1/disease/detect` | Upload leaf + detect disease |
| `POST` | `/api/v1/soil/predict` | Predict soil moisture |
| `GET` | `/api/v1/history` | Prediction history |
| `GET` | `/api/v1/map/markers` | GIS map markers |
| `GET` | `/api/v1/notifications` | User notifications |
| `POST` | `/api/v1/reports/generate` | Generate PDF report |
| `GET` | `/api/health` | Health check |

---

## 🤖 AI Models

| Model | Architecture | Classes | Status |
|---|---|---|---|
| Disease Detection | MobileNetV2 (TF/Keras) | 38 crop diseases | Stub mode until `.h5` placed in `ai_models/saved_models/` |
| Soil Moisture | DenseNN (sklearn) | Regression | Stub mode until `.pkl` placed in `ai_models/saved_models/` |

Place trained model files at:
```
ai_models/saved_models/disease_model.h5
ai_models/saved_models/soil_model.pkl
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URI` | ✅ | MongoDB Atlas connection string |
| `MONGODB_DB_NAME` | ✅ | Database name (default: `agricrop`) |
| `SECRET_KEY` | ✅ | JWT signing secret (32+ chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | Default: `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | — | Default: `30` |
| `EMAIL_ENABLED` | — | `true` to enable SMTP |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | — | SMTP port (default: `587`) |
| `SMTP_USER` | — | SMTP username / email |
| `SMTP_PASSWORD` | — | SMTP password |
| `ALLOWED_ORIGINS` | — | Comma-separated CORS origins |
| `LOG_LEVEL` | — | `DEBUG`/`INFO`/`WARNING` |

---

## 🔒 Security

- Passwords hashed with **bcrypt** (12 rounds)
- JWT **access tokens** (60 min) + **refresh tokens** (30 days)
- Rate limiting via **slowapi** on all mutation endpoints
- CORS restricted to configured origins in production
- `.env` and `serviceAccountKey.json` excluded from git

