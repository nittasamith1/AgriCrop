"""
AgriCrop – Soil Moisture Predictor
Dense Neural Network inference for soil moisture prediction.
Falls back to a physics-informed stub when the model is absent.
"""

import math
import random
import numpy as np
from typing import Dict, Any
from loguru import logger

from backend.ai.model_loader import load_soil_model
from backend.models.prediction import SoilPredictionRequest

# Soil type feature encoding
SOIL_TYPE_MAP = {
    "sandy": 0, "loamy": 1, "clay": 2, "silt": 3, "peaty": 4,
}

# Water retention coefficients per soil type (field capacity %)
SOIL_WATER_RETENTION = {
    "sandy": 0.10, "loamy": 0.25, "clay": 0.40, "silt": 0.30, "peaty": 0.50,
}


class SoilPredictor:
    """
    Predicts soil moisture percentage from environmental features.
    Uses Dense NN model if available; otherwise uses a physics-informed stub.
    """

    def predict(self, req: SoilPredictionRequest) -> Dict[str, Any]:
        """
        Predict soil moisture and generate irrigation recommendation.
        """
        model = load_soil_model()
        features = self._build_features(req)

        if model is not None:
            return self._predict_with_model(model, features, req)
        else:
            logger.info("Soil model not loaded — using physics-informed stub")
            return self._stub_prediction(features, req)

    def _build_features(self, req: SoilPredictionRequest) -> np.ndarray:
        """
        Encode request into a normalized feature vector:
        [temperature, humidity, rainfall, wind_speed, soil_type_idx, previous_moisture]
        """
        soil_idx = SOIL_TYPE_MAP.get(req.soil_type.lower(), 1)
        features = np.array([
            req.temperature / 60.0,          # Normalize 0–60°C
            req.humidity / 100.0,             # Already 0–100%
            req.rainfall / 500.0,             # Normalize 0–500mm
            req.wind_speed / 150.0,           # Normalize 0–150 km/h
            soil_idx / 4.0,                   # Normalize 0–4
            req.previous_moisture / 100.0,    # Already 0–100%
        ], dtype=np.float32)
        return features

    def _predict_with_model(
        self, model, features: np.ndarray, req: SoilPredictionRequest
    ) -> Dict[str, Any]:
        """Run actual TF inference."""
        try:
            batch = np.expand_dims(features, axis=0)
            raw = model.predict(batch, verbose=0)
            predicted_moisture = float(np.clip(raw[0][0] * 100, 0, 100))
            return self._build_result(predicted_moisture, req, stub=False)
        except Exception as e:
            logger.error(f"Soil model inference failed: {e}. Falling back to stub.")
            return self._stub_prediction(features, req)

    def _stub_prediction(self, features: np.ndarray, req: SoilPredictionRequest) -> Dict[str, Any]:
        """
        Physics-informed stub using:
        - Soil water retention capacity
        - Rainfall contribution
        - Evapotranspiration approximation (Penman-Monteith simplified)
        - Previous moisture carry-over
        """
        soil_type = req.soil_type.lower()
        retention = SOIL_WATER_RETENTION.get(soil_type, 0.25)

        # Evapotranspiration proxy (higher temp + wind = more drying)
        eto = (0.0023 * (req.temperature + 17.8) * math.sqrt(max(0, req.humidity))
               * (0.408 * req.temperature + req.wind_speed * 0.01))
        eto = max(0, min(eto, 15))  # Cap at 15mm/day

        # Effective rainfall (some runs off)
        effective_rain = req.rainfall * retention

        # Predicted moisture
        moisture = (
            req.previous_moisture * 0.5
            + effective_rain * 0.3
            + req.humidity * 0.1
            - eto * 0.5
            + random.uniform(-2, 2)
        )
        predicted_moisture = float(np.clip(moisture, 5, 95))
        return self._build_result(predicted_moisture, req, stub=True)

    def _build_result(
        self, predicted_moisture: float, req: SoilPredictionRequest, stub: bool
    ) -> Dict[str, Any]:
        """Build the full structured prediction result."""
        soil_type = req.soil_type.lower()

        # Field capacity thresholds per soil type
        field_capacity = {
            "sandy": 25, "loamy": 40, "clay": 55, "silt": 45, "peaty": 65,
        }.get(soil_type, 40)

        wilting_point = {
            "sandy": 10, "loamy": 18, "clay": 25, "silt": 20, "peaty": 30,
        }.get(soil_type, 18)

        # Available water content
        awc = max(0, predicted_moisture - wilting_point)

        # Irrigation decision
        irrigation_recommended = predicted_moisture < (field_capacity * 0.6)
        water_requirement = max(0, (field_capacity - predicted_moisture) * 5)  # mm/hectare simplified

        if not irrigation_recommended:
            irrigation_type = "none"
            next_irrigation_hours = None
        elif water_requirement < 15:
            irrigation_type = "drip"
            next_irrigation_hours = 24
        elif water_requirement < 30:
            irrigation_type = "sprinkler"
            next_irrigation_hours = 12
        else:
            irrigation_type = "flood"
            next_irrigation_hours = 6

        return {
            "predicted_moisture": round(predicted_moisture, 2),
            "field_capacity": field_capacity,
            "wilting_point": wilting_point,
            "available_water_content": round(awc, 2),
            "water_requirement_mm": round(water_requirement, 2),
            "irrigation_recommended": irrigation_recommended,
            "irrigation_type": irrigation_type,
            "next_irrigation_hours": next_irrigation_hours,
            "soil_type": soil_type,
            "input_features": {
                "temperature": req.temperature,
                "humidity": req.humidity,
                "rainfall": req.rainfall,
                "wind_speed": req.wind_speed,
                "soil_type": req.soil_type,
                "previous_moisture": req.previous_moisture,
            },
            "model_version": "DenseNN-v1",
            "stub_mode": stub,
        }


# Module-level singleton
soil_predictor = SoilPredictor()
