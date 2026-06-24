# ⚙️ Environment Variables Guide

The `.env` file is crucial for the AgriCrop application. It contains secrets, configuration paths, and Firebase credentials.

**⚠️ NEVER commit the `.env` file or `serviceAccountKey.json` to version control.**

## Variable Breakdown

### Application
- `APP_NAME`: Name of the application (e.g., AgriCrop)
- `APP_ENV`: Environment mode (`development` or `production`)
- `APP_PORT`: Port for the FastAPI backend (e.g., `8000`)
- `SECRET_KEY`: A strong, random 32+ character string used for signing JWTs.
- `ALGORITHM`: JWT algorithm (e.g., `HS256`)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: How long JWTs remain valid (e.g., `60`).

### Firebase Admin SDK (Backend)
These variables are used by the FastAPI backend to verify tokens and interact with Firebase securely.
- `FIREBASE_PROJECT_ID`: Your Firebase Project ID (e.g., `agricrop-a8352`)
- `FIREBASE_PRIVATE_KEY_ID`: From `serviceAccountKey.json`
- `FIREBASE_PRIVATE_KEY`: From `serviceAccountKey.json` (Ensure line breaks are preserved as `\n`)
- `FIREBASE_CLIENT_EMAIL`: The service account email
- `FIREBASE_CLIENT_ID`: Service account client ID
- `FIREBASE_SERVICE_ACCOUNT_PATH`: Path to the local JSON file (e.g., `./serviceAccountKey.json`). *Note: In production, it's safer to use the individual environment variables instead of the file.*

### Firebase Client (Frontend)
These variables configure the public-facing Firebase Web SDK.
- `FIREBASE_API_KEY`: Web API Key
- `FIREBASE_AUTH_DOMAIN`: e.g., `agricrop-a8352.firebaseapp.com`
- `FIREBASE_STORAGE_BUCKET`: e.g., `agricrop-a8352.firebasestorage.app`
- `FIREBASE_MESSAGING_SENDER_ID`: Sender ID
- `FIREBASE_APP_ID`: Web App ID
- `FIREBASE_MEASUREMENT_ID`: Google Analytics ID

### File Uploads & Storage
- `MAX_UPLOAD_SIZE_MB`: Max size in MB (e.g., `10`)
- `UPLOAD_TEMP_DIR`: Local path to temporarily store uploads before processing (e.g., `./tmp/agricrop_uploads`)
- `FIREBASE_STORAGE_URL`: e.g., `gs://agricrop-a8352.firebasestorage.app`

### AI Models
- `DISEASE_MODEL_PATH`: Path to the disease `.h5` model (e.g., `./ai_models/saved_models/disease_model.h5`)
- `SOIL_MODEL_PATH`: Path to the soil `.h5` model
- `MODEL_CONFIDENCE_THRESHOLD`: Minimum confidence to accept a prediction (e.g., `0.65`)

### Security
- `ALLOWED_ORIGINS`: Comma-separated list of CORS origins allowed to hit the backend.
- `RATE_LIMIT_REQUESTS`: Max requests per window.
- `RATE_LIMIT_WINDOW_SECONDS`: Time window for rate limiting.
