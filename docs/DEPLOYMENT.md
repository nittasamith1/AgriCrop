# 🚀 Deployment Guide

AgriCrop uses a decoupled architecture:
1. **Frontend**: Hosted on Firebase Hosting (Static HTML/JS/CSS).
2. **Backend**: FastAPI app hosted on Google Cloud Run or Render.com.

## 1. Firebase Setup (Required)

1. Create a project at [Firebase Console](https://console.firebase.google.com/).
2. Enable the following services:
   - **Authentication** (Enable Email/Password provider)
   - **Firestore Database** (Create database in production mode)
   - **Storage** (Create default bucket)
   - **Hosting**
3. Generate a new private key for the Admin SDK:
   - Go to Project Settings > Service Accounts.
   - Click "Generate new private key".
   - Save the downloaded file as `serviceAccountKey.json` in the root of this project.

## 2. Deploying the Frontend (Firebase Hosting)

Make sure you have the Firebase CLI installed:
```bash
npm install -g firebase-tools
```

Login to Firebase:
```bash
firebase login
```

Set your active project (replace `agricrop-a8352` with your actual project ID):
```bash
firebase use agricrop-a8352
```

Deploy the application (Hosting, Firestore rules/indexes, Storage rules):
```bash
firebase deploy --only hosting,firestore:rules,firestore:indexes,storage
```
Your frontend is now live at `https://<YOUR-PROJECT-ID>.web.app`.

## 3. Deploying the Backend (Cloud Run / Render)

Because the backend requires Python, TensorFlow, and other heavy dependencies, it must be deployed to a container-native service like Google Cloud Run or Render.

### Option A: Render.com (Easier)
1. Push your repository to GitHub.
2. Create a new "Web Service" on Render.
3. Connect your GitHub repository.
4. Set the Build Command to `pip install -r requirements.txt`.
5. Set the Start Command to `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
6. Add all Environment Variables from your `.env` file to the Render dashboard.
7. **Important:** Copy the base64 encoded contents of your `serviceAccountKey.json` or paste the raw JSON into an environment variable and configure the backend to parse it.

### Option B: Google Cloud Run (Recommended for Firebase integration)
1. Make sure Docker is installed.
2. Build the container:
   ```bash
   gcloud builds submit --tag gcr.io/<YOUR-PROJECT-ID>/agricrop-backend
   ```
3. Deploy to Cloud Run:
   ```bash
   gcloud run deploy agricrop-backend --image gcr.io/<YOUR-PROJECT-ID>/agricrop-backend --platform managed --allow-unauthenticated
   ```
4. Update `firebase.json` rewrites to point to your new Cloud Run service.

## 4. Connecting Frontend to Backend

Update the `window.API_BASE` in `frontend/js/api.js`.
- If using Firebase Cloud Run Rewrites, keep it as `""` (empty string).
- If using Render, set it to `https://your-render-app.onrender.com`.
