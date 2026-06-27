# 🌾 AgriCrop – AI-Powered Precision Agriculture Platform

## 📖 Overview

AgriCrop is an AI-powered smart agriculture platform designed to assist farmers in monitoring crop health, detecting plant diseases, predicting soil moisture, and visualizing agricultural data using geospatial technologies.

The platform integrates Artificial Intelligence (TensorFlow), Firebase Cloud Services, satellite-based mapping (Leaflet), and a FastAPI backend to provide actionable insights that improve crop productivity.

---

## ✨ Features

- 🌱 **AI Disease Detection:** MobileNetV2 identifies 38 plant diseases from a single leaf photo.
- 💧 **Soil Moisture AI:** Dense Neural Network predicts soil moisture based on temperature, humidity, and rainfall.
- 📍 **GIS Disease Maps:** Interactive Leaflet.js maps with disease markers and heatmaps.
- 📊 **Real-Time Analytics:** Chart.js powered dashboard for crop health and severity breakdowns.
- ☁️ **Cloud Infrastructure:** Firebase Authentication, Firestore Database, and Firebase Storage.
- 🔐 **Role-based Access:** Secure farmer and admin dashboards.
- 📄 **PDF Reports:** Generate and download professional PDF reports.

---

## 🛠 Tech Stack

### Frontend
- **HTML5, CSS3, JavaScript (ES6+)**
- **Bootstrap 5** (Styling framework)
- **Chart.js** (Analytics)
- **Leaflet.js** (Geospatial Mapping)
- **Firebase Web SDK** (Auth, Storage, Firestore)

### Backend
- **Python 3.10+**
- **FastAPI** (REST API Framework)
- **Uvicorn** (ASGI server)
- **Firebase Admin SDK** (Backend security & verification)

### AI & ML
- **TensorFlow & Keras** (Model training and inference)
- **MobileNetV2** (Image classification)
- **Scikit-learn** (Data preprocessing)
- **OpenCV & Pillow** (Image processing)

---

## 📂 Project Structure

```text
AgriCrop/
├── ai_models/         # Pre-trained TensorFlow models (.h5)
├── backend/           # FastAPI backend application
│   ├── routers/       # API endpoints (auth, disease, soil, map)
│   ├── services/      # Business logic & Firebase integration
│   ├── config.py      # Environment configuration
│   └── main.py        # FastAPI entry point
├── datasets/          # Raw data and labels for AI models
├── docs/              # Additional documentation
├── frontend/          # Vanilla HTML/JS/CSS frontend
│   ├── css/           # Stylesheets (Bootstrap overrides)
│   ├── js/            # Client-side logic and API wrappers
│   ├── assets/        # Images, fonts, icons
│   └── *.html         # Pages (index, login, dashboard, etc.)
├── logs/              # Backend logs
├── tests/             # Pytest test suite
├── .env               # Environment variables
├── firebase.json      # Firebase Hosting and Rules configuration
└── requirements.txt   # Python dependencies
```

---

## 🚀 Local Development

### 1. Backend Setup

```bash
# Clone repository
git clone https://github.com/nittasamith1/AgriCrop.git
cd AgriCrop

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```
API Documentation will be available at: `http://localhost:8000/api/docs`

### 2. Frontend Setup

The frontend is built with plain HTML/JS and doesn't require a build step. You can use any static server to serve the `frontend/` directory.
For example, using Python:

```bash
cd frontend
python -m http.server 3000
```
Open `http://localhost:3000` in your browser.

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

## ☁️ Deployment & Configuration

For detailed deployment instructions (Firebase Hosting, Cloud Run/Render) and environment variable setup, please refer to the documentation:

- [Deployment Guide](docs/DEPLOYMENT.md)
- [Environment Variables](docs/ENVIRONMENT.md)

---

## 👨‍💻 Author

**Nitta Samith**
- B.Tech Artificial Intelligence & Machine Learning

## ⭐ Support

If you found this project helpful, please ⭐ Star the repository!
