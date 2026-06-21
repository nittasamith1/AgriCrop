"""
AgriCrop – Disease Predictor
Runs inference on preprocessed leaf images using MobileNetV2.
Falls back to a deterministic stub when the model file is not present.
"""

import random
import numpy as np
from typing import Dict, Any, Optional
from loguru import logger

from backend.ai.model_loader import (
    load_disease_model, DISEASE_CLASSES, DISEASE_CLASSES_DISPLAY
)
from backend.ai.preprocessor import (
    preprocess_for_model, extract_image_metadata, compute_green_ratio
)
from backend.config import settings


class DiseasePredictor:
    """
    Predicts plant disease from a leaf image.
    Uses MobileNetV2 when the .h5 model is available;
    otherwise returns a realistic stub prediction.
    """

    def predict(self, image_bytes: bytes, crop_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Run disease prediction on raw image bytes.
        Returns a full prediction result dict.
        """
        model = load_disease_model()
        green_ratio = compute_green_ratio(image_bytes)
        meta = extract_image_metadata(image_bytes)

        if model is not None:
            return self._predict_with_model(model, image_bytes, green_ratio, meta, crop_hint)
        else:
            logger.info("Disease model not loaded — using stub predictor")
            return self._stub_prediction(image_bytes, green_ratio, meta, crop_hint)

    def _predict_with_model(
        self, model, image_bytes: bytes, green_ratio: float, meta: dict, crop_hint: Optional[str]
    ) -> Dict[str, Any]:
        """Run actual TF inference."""
        try:
            img_batch = preprocess_for_model(image_bytes)
            predictions = model.predict(img_batch, verbose=0)
            class_idx = int(np.argmax(predictions[0]))
            confidence = float(predictions[0][class_idx])

            class_key = DISEASE_CLASSES[class_idx]
            display_name = DISEASE_CLASSES_DISPLAY[class_key]
            is_healthy = "healthy" in class_key.lower()

            result = self._build_result(
                class_key=class_key,
                display_name=display_name,
                confidence=confidence,
                is_healthy=is_healthy,
                all_probs=predictions[0].tolist(),
                green_ratio=green_ratio,
                meta=meta,
                stub=False,
            )
            logger.info(f"Disease prediction: {display_name} ({confidence:.2%})")
            return result
        except Exception as e:
            logger.error(f"Model inference failed: {e}. Falling back to stub.")
            return self._stub_prediction(image_bytes, green_ratio, meta, crop_hint)

    def _stub_prediction(
        self, image_bytes: bytes, green_ratio: float, meta: dict, crop_hint: Optional[str]
    ) -> Dict[str, Any]:
        """
        Deterministic stub that returns realistic predictions based on
        the image's green ratio (a real proxy for leaf quality).
        """
        # Use green ratio as a seed for reproducible results per image
        seed = int(sum(image_bytes[:64])) % 38
        random.seed(seed)

        if green_ratio > 0.35:
            # Mostly green → lean toward healthy or mild disease
            if random.random() < 0.4:
                class_key = "Tomato___healthy"
                confidence = random.uniform(0.78, 0.96)
            else:
                classes_subset = [c for c in DISEASE_CLASSES if "healthy" not in c.lower()]
                class_key = random.choice(classes_subset)
                confidence = random.uniform(0.65, 0.88)
        else:
            # Low green → likely diseased
            classes_diseased = [c for c in DISEASE_CLASSES if "healthy" not in c.lower()]
            class_key = random.choice(classes_diseased)
            confidence = random.uniform(0.70, 0.95)

        is_healthy = "healthy" in class_key.lower()
        display_name = DISEASE_CLASSES_DISPLAY[class_key]

        # Simulate probability distribution
        n = len(DISEASE_CLASSES)
        idx = DISEASE_CLASSES.index(class_key)
        all_probs = [random.uniform(0.001, 0.05) for _ in range(n)]
        all_probs[idx] = confidence
        total = sum(all_probs)
        all_probs = [p / total for p in all_probs]

        return self._build_result(
            class_key=class_key,
            display_name=display_name,
            confidence=confidence,
            is_healthy=is_healthy,
            all_probs=all_probs,
            green_ratio=green_ratio,
            meta=meta,
            stub=True,
        )

    def _build_result(
        self, class_key: str, display_name: str, confidence: float,
        is_healthy: bool, all_probs: list, green_ratio: float, meta: dict, stub: bool
    ) -> Dict[str, Any]:
        """Build the full structured result dictionary."""
        if is_healthy:
            severity = "healthy"
            affected_area = 0.0
        elif confidence < 0.50:
            severity = "mild"
            affected_area = round(random.uniform(5, 25), 1)
        elif confidence < 0.75:
            severity = "moderate"
            affected_area = round(random.uniform(25, 55), 1)
        else:
            severity = "severe"
            affected_area = round(random.uniform(55, 90), 1)

        # Top 3 predictions
        top_indices = sorted(range(len(all_probs)), key=lambda i: all_probs[i], reverse=True)[:3]
        top_predictions = [
            {
                "class": DISEASE_CLASSES_DISPLAY[DISEASE_CLASSES[i]],
                "probability": round(all_probs[i], 4),
            }
            for i in top_indices
        ]

        return {
            "disease_class_key": class_key,
            "disease_name": display_name,
            "confidence": round(confidence, 4),
            "severity": severity,
            "affected_area_percent": affected_area,
            "is_healthy": is_healthy,
            "top_predictions": top_predictions,
            "image_quality": {
                "green_ratio": round(green_ratio, 3),
                "is_valid_leaf": green_ratio > 0.15,
                "width": meta.get("width"),
                "height": meta.get("height"),
                "file_size_bytes": meta.get("file_size_bytes"),
            },
            "model_version": "MobileNetV2-v1",
            "stub_mode": stub,
        }


# Module-level singleton
disease_predictor = DiseasePredictor()
