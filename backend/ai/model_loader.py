"""
AgriCrop – AI Model Loader
Thread-safe singleton loader for TensorFlow/Keras models.
Provides lazy loading with fallback to stub mode when .h5 files are absent.
"""

import os
import threading
from typing import Optional, Any
from loguru import logger

from backend.config import settings

# ── Thread Safety ──────────────────────────────────────────────────────────────
_disease_model: Optional[Any] = None
_soil_model: Optional[Any] = None
_disease_lock = threading.Lock()
_soil_lock = threading.Lock()

# ── Disease Class Labels ───────────────────────────────────────────────────────
# 38 PlantVillage classes (matches training order)
DISEASE_CLASSES = [
    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",
    "Blueberry___healthy",
    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",
    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",
    "Orange___Haunglongbing_(Citrus_greening)",
    "Peach___Bacterial_spot",
    "Peach___healthy",
    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",
    "Raspberry___healthy",
    "Soybean___healthy",
    "Squash___Powdery_mildew",
    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",
    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy",
]

DISEASE_CLASSES_DISPLAY = {cls: cls.replace("___", " – ").replace("_", " ") for cls in DISEASE_CLASSES}


def load_disease_model():
    """
    Load the MobileNetV2 disease detection model (thread-safe singleton).
    Returns the Keras model or None if the file is not found (stub mode).
    """
    global _disease_model
    if _disease_model is not None:
        return _disease_model

    with _disease_lock:
        if _disease_model is not None:
            return _disease_model

        model_path = settings.DISEASE_MODEL_PATH
        if not os.path.exists(model_path):
            logger.warning(
                f"Disease model not found at '{model_path}'. "
                "Running in STUB MODE — predictions will be simulated."
            )
            return None

        try:
            import tensorflow as tf
            logger.info(f"Loading disease model from: {model_path}")
            _disease_model = tf.keras.models.load_model(model_path)
            logger.success(f"✅ Disease model loaded ({model_path})")
            return _disease_model
        except Exception as e:
            logger.error(f"Failed to load disease model: {e}")
            return None


def load_soil_model():
    """
    Load the Dense NN soil moisture prediction model (thread-safe singleton).
    Returns the Keras model or None if the file is not found (stub mode).
    """
    global _soil_model
    if _soil_model is not None:
        return _soil_model

    with _soil_lock:
        if _soil_model is not None:
            return _soil_model

        model_path = settings.SOIL_MODEL_PATH
        if not os.path.exists(model_path):
            logger.warning(
                f"Soil model not found at '{model_path}'. "
                "Running in STUB MODE — predictions will be simulated."
            )
            return None

        try:
            import tensorflow as tf
            logger.info(f"Loading soil model from: {model_path}")
            _soil_model = tf.keras.models.load_model(model_path)
            logger.success(f"✅ Soil model loaded ({model_path})")
            return _soil_model
        except Exception as e:
            logger.error(f"Failed to load soil model: {e}")
            return None


def is_disease_model_loaded() -> bool:
    return _disease_model is not None or os.path.exists(settings.DISEASE_MODEL_PATH)


def is_soil_model_loaded() -> bool:
    return _soil_model is not None or os.path.exists(settings.SOIL_MODEL_PATH)
