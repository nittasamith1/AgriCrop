# Deployment Guide

This guide details how to build and deploy AgriCrop to a production environment.

## 1. Containerized Deployment (Recommended)

AgriCrop includes ready-to-use Dockerfiles and a `docker-compose.yml` configuration.

### Prerequisites
- Install **Docker** and **Docker Compose** on the target server.

### Deploy Steps
1. Transfer files to the production server.
2. Edit `.env` file to set `APP_ENV=production` and add your real Firebase API keys and secrets.
3. Run the following command:
   ```bash
   docker compose -f docker-compose.yml up --build -d
   ```
4. Verify the containers are running:
   ```bash
   docker compose ps
   ```

The application will be accessible at `http://localhost` (via Nginx proxying traffic to the backend).

---

## 2. Cloud Platforms Deployment

### Backend (Render/Heroku/Railway)
- Root directory: `backend/` or root
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend (Firebase Hosting / Vercel / Netlify)
- Set static files folder to `frontend/`
- Configure custom API rewrite rules to forward requests to the hosted backend URL.
