# AgriCrop – Geospatial Plant Disease & Soil Moisture Intelligence Network

AgriCrop is an AI-powered Precision Agriculture platform developed to support farmers with real-time geospatial plant disease detection, soil moisture prediction, and custom irrigation recommendations.

## Core Features

- **Leaf Disease Detection**: Detect plant disease and receive treatment recommendations from leaf images using a fine-tuned MobileNetV2.
- **Soil Moisture Prediction**: Input local temperature, humidity, wind speed, and soil temperature to predict soil moisture and get tailored irrigation suggestions.
- **Interactive GIS Map**: Track disease hotspots and moisture gradients with an interactive heat map.
- **Farm Profiles**: Save farm locations, surface areas, and crop types.
- **Admin Dashboard**: Manage user profiles, active disease outbreaks, and platform-wide analytics.
- **Automated Reporting**: Export CSV and PDF reports containing history scans and crop recommendations.

## Tech Stack

- **Backend**: FastAPI, Python 3.11, Uvicorn, TensorFlow, Scikit-Learn
- **Frontend**: Vanilla JS (ES6+), CSS Grid/Flexbox, Bootstrap 5, Chart.js, Leaflet.js
- **Database / Auth**: Firebase Authentication, Firestore Database, Firebase Storage
- **Deployment**: Docker, Docker Compose, GitHub Actions (CI/CD)

## Repository Structure

- `backend/`: FastAPI application code (routers, models, utilities, and services)
- `frontend/`: Single Page Application files (HTML, CSS, JS)
- `ai_models/`: ML Model structures, preprocessing pipelines, and offline training scripts
- `datasets/`: Dataset CSVs used for training and test references
- `docs/`: In-depth developer, installer, API, and architectural documentations
- `tests/`: Automated unit and integration test suite
