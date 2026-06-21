# Installation & Local Setup

Follow these instructions to set up the AgriCrop development environment.

## Prerequisites

1. **Python 3.11** or higher.
2. **Node.js** (optional, for custom static file server configuration).
3. **Firebase Project**:
   - Create a Firebase project at [Firebase Console](https://console.firebase.google.com).
   - Enable **Authentication** (Email/Password).
   - Create a **Firestore Database**.
   - Create a **Firebase Storage** bucket.
   - Download the service account JSON key and place it locally or copy credentials.

---

## Installation Steps

### 1. Clone & Navigate
```bash
git clone <repository_url> AgriCrop
cd AgriCrop
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate  # On Linux/macOS
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory and populate it according to the template in `.env.example`:
```env
APP_NAME=AgriCrop
APP_ENV=development
FIREBASE_PROJECT_ID=your-project-id
# Add Firebase config details
```

### 5. Running the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
Visit `http://127.0.0.1:8000/api/docs` to inspect the Swagger UI.

### 6. Serving the Frontend
You can serve the `frontend/` directory using any local static server. For instance, using Python:
```bash
python -m http.server 3000 --directory frontend
```
Visit `http://localhost:3000` in your web browser.
