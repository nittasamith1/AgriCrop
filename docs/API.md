# AgriCrop API Documentation

The AgriCrop backend exposes a REST API via FastAPI. The base path for all endpoints is `/api/v1`.

## Authentication

### 1. Register User
- **URL**: `/api/v1/auth/register`
- **Method**: `POST`
- **Payload**:
  ```json
  {
    "email": "farmer@example.com",
    "password": "securepassword123",
    "name": "Samith Nitta",
    "role": "farmer",
    "phone": "+919876543210",
    "state": "Andhra Pradesh",
    "district": "Chittoor"
  }
  ```
- **Response**: `201 Created`

### 2. Forgot Password
- **URL**: `/api/v1/auth/forgot-password`
- **Method**: `POST`
- **Params**: `email` (string)
- **Response**: `200 OK`

### 3. Get Profile
- **URL**: `/api/v1/auth/me`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ID_TOKEN>`
- **Response**: `200 OK`

---

## Disease Detection

### 1. Predict Crop Disease
- **URL**: `/api/v1/disease/predict`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <ID_TOKEN>`
- **Payload**: `multipart/form-data`
  - `file`: Image binary
  - `farm_id`: Optional (string)
  - `crop_type`: Optional (string)
  - `latitude`: Optional (float)
  - `longitude`: Optional (float)
- **Response**: `201 Created`

### 2. Get Disease Scan History
- **URL**: `/api/v1/disease/history`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ID_TOKEN>`
- **Response**: `200 OK`

---

## Soil Moisture Prediction

### 1. Predict Soil Moisture
- **URL**: `/api/v1/soil/predict`
- **Method**: `POST`
- **Headers**: `Authorization: Bearer <ID_TOKEN>`
- **Payload**:
  ```json
  {
    "temperature": 28.5,
    "humidity": 55.0,
    "soil_temperature": 24.2,
    "wind_speed": 4.1,
    "soil_type": "loamy",
    "crop_type": "Tomato",
    "farm_id": "farm_123",
    "latitude": 13.52,
    "longitude": 79.98
  }
  ```
- **Response**: `201 Created`

---

## Admin Analytics & Management

### 1. Get Analytics Dashboard Data
- **URL**: `/api/v1/admin/analytics`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ADMIN_TOKEN>`
- **Response**: `200 OK`

### 2. Get Users List
- **URL**: `/api/v1/admin/users`
- **Method**: `GET`
- **Headers**: `Authorization: Bearer <ADMIN_TOKEN>`
- **Response**: `200 OK`
