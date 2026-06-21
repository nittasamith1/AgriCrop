"""
AgriCrop – Image Preprocessor
Handles all image loading, resizing, normalization, and augmentation
for the MobileNetV2 disease detection pipeline.
"""

import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ExifTags
from typing import Tuple, Optional
from loguru import logger

# MobileNetV2 input requirements
TARGET_SIZE = (224, 224)
CHANNELS = 3


def load_image_from_bytes(content: bytes) -> np.ndarray:
    """
    Load an image from raw bytes (uploaded file) into a NumPy array (BGR).
    """
    arr = np.frombuffer(content, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image. The file may be corrupt or unsupported.")
    return img


def fix_image_orientation(pil_img: Image.Image) -> Image.Image:
    """
    Correct EXIF orientation for images from mobile cameras.
    """
    try:
        exif = pil_img._getexif()
        if exif is None:
            return pil_img
        orient_key = next(
            (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
        )
        if orient_key and orient_key in exif:
            orientation = exif[orient_key]
            rotations = {3: 180, 6: 270, 8: 90}
            if orientation in rotations:
                pil_img = pil_img.rotate(rotations[orientation], expand=True)
    except Exception:
        pass  # If EXIF reading fails, return as-is
    return pil_img


def preprocess_for_model(
    content: bytes,
    target_size: Tuple[int, int] = TARGET_SIZE,
    normalize: bool = True,
) -> np.ndarray:
    """
    Full preprocessing pipeline for the disease detection model:
      1. Load image from bytes
      2. Fix EXIF orientation
      3. Convert to RGB (OpenCV uses BGR)
      4. Resize to target_size
      5. Normalize pixel values to [0, 1] (MobileNetV2 preprocess_input style)
    Returns shape: (1, H, W, 3) — batch of 1 ready for model.predict()
    """
    # Load via PIL for better format support and EXIF handling
    try:
        pil_img = Image.open(io.BytesIO(content)).convert("RGB")
        pil_img = fix_image_orientation(pil_img)
    except Exception as e:
        raise ValueError(f"Cannot open image: {e}")

    # Resize
    pil_img = pil_img.resize(target_size, Image.LANCZOS)

    # Convert to numpy
    img_array = np.array(pil_img, dtype=np.float32)

    # MobileNetV2 preprocess_input: scale to [-1, 1]
    if normalize:
        img_array = (img_array / 127.5) - 1.0

    # Add batch dimension
    img_batch = np.expand_dims(img_array, axis=0)
    return img_batch


def extract_image_metadata(content: bytes) -> dict:
    """
    Extract basic metadata from an image:
    - Format, mode, dimensions, file size, dominant colors.
    """
    meta = {
        "file_size_bytes": len(content),
        "format": None,
        "mode": None,
        "width": None,
        "height": None,
        "dominant_colors": [],
    }
    try:
        pil_img = Image.open(io.BytesIO(content))
        meta["format"] = pil_img.format
        meta["mode"] = pil_img.mode
        meta["width"], meta["height"] = pil_img.size

        # Compute 3 dominant colors via k-means on small resized version
        small = pil_img.resize((50, 50)).convert("RGB")
        arr = np.array(small).reshape(-1, 3).astype(np.float32)
        _, labels, centers = cv2.kmeans(
            arr, 3, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
            3, cv2.KMEANS_RANDOM_CENTERS,
        )
        meta["dominant_colors"] = [
            f"#{int(c[0]):02x}{int(c[1]):02x}{int(c[2]):02x}" for c in centers
        ]
    except Exception as e:
        logger.warning(f"Image metadata extraction failed: {e}")
    return meta


def compute_green_ratio(content: bytes) -> float:
    """
    Estimate the green pixel ratio of the image (proxy for leaf coverage).
    Green ratio > 0.3 suggests a valid leaf image.
    """
    try:
        pil_img = Image.open(io.BytesIO(content)).convert("RGB").resize((100, 100))
        arr = np.array(pil_img)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        green_mask = (g.astype(int) - r.astype(int) > 10) & (g.astype(int) - b.astype(int) > 10)
        return float(np.sum(green_mask)) / (100 * 100)
    except Exception:
        return 0.0
