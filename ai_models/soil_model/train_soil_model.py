"""
AgriCrop – Soil Moisture Model Training Script
Full training pipeline using the synthetic soil moisture dataset.

Dataset: datasets/soil/soil_moisture_data.csv
Features: temperature, humidity, rainfall, wind_speed, soil_type, previous_moisture
Target: soil_moisture (%)

Usage:
    python -m ai_models.soil_model.train_soil_model
    (Run from the AgriCrop project root)
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from ai_models.soil_model.model_architecture import build_soil_model

# ── Configuration ─────────────────────────────────────────────────────────────
DATASET_PATH = "datasets/soil/soil_moisture_data.csv"
OUTPUT_DIR   = "ai_models/saved_models"
SCALER_PATH  = os.path.join(OUTPUT_DIR, "soil_scaler.pkl")
BATCH_SIZE   = 32
EPOCHS       = 100
RANDOM_SEED  = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)
np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)

SOIL_TYPE_MAP = {"sandy": 0, "loamy": 1, "clay": 2, "silt": 3, "peaty": 4}


def load_and_preprocess(csv_path: str):
    """Load CSV, encode categoricals, and split into train/val/test."""
    df = pd.read_csv(csv_path)

    # Encode soil type
    df["soil_type_idx"] = df["soil_type"].str.lower().map(SOIL_TYPE_MAP).fillna(1)

    feature_cols = ["temperature", "humidity", "rainfall", "wind_speed", "soil_type_idx", "previous_moisture"]
    target_col = "soil_moisture"

    X = df[feature_cols].values.astype(np.float32)
    y = (df[target_col].values / 100.0).astype(np.float32)  # Normalize to [0,1]

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, random_state=RANDOM_SEED)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=RANDOM_SEED)

    print(f"  Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")
    return X_train, X_val, X_test, y_train, y_val, y_test


def plot_training_history(history):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(history.history["mae"], label="Train MAE")
    ax1.plot(history.history["val_mae"], label="Val MAE")
    ax1.set_title("Mean Absolute Error"); ax1.set_xlabel("Epoch"); ax1.set_ylabel("MAE")
    ax1.legend(); ax1.grid(True, alpha=0.3)

    ax2.plot(history.history["loss"], label="Train Loss (MSE)")
    ax2.plot(history.history["val_loss"], label="Val Loss (MSE)")
    ax2.set_title("Loss (MSE)"); ax2.set_xlabel("Epoch"); ax2.set_ylabel("MSE")
    ax2.legend(); ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, "soil_training_history.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✅ Training history plot saved to {plot_path}")


def plot_predictions(y_true, y_pred):
    """Scatter plot of true vs predicted moisture values."""
    y_true_pct = y_true * 100
    y_pred_pct = y_pred * 100

    plt.figure(figsize=(6, 6))
    plt.scatter(y_true_pct, y_pred_pct, alpha=0.4, s=15, color="#1a7c3e")
    plt.plot([0, 100], [0, 100], "r--", label="Perfect Prediction")
    plt.xlabel("True Moisture (%)"); plt.ylabel("Predicted Moisture (%)")
    plt.title("Soil Moisture: True vs Predicted")
    plt.legend(); plt.grid(True, alpha=0.3)

    plot_path = os.path.join(OUTPUT_DIR, "soil_predictions_scatter.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✅ Predictions scatter plot saved to {plot_path}")


def train():
    print("=" * 60)
    print("  AgriCrop – Soil Moisture Model Training")
    print("=" * 60)
    print(f"  TensorFlow: {tf.__version__}")
    print(f"  Dataset: {DATASET_PATH}")

    if not os.path.exists(DATASET_PATH):
        print(f"\n❌ Dataset not found at '{DATASET_PATH}'")
        print("   Run the dataset generation script first or create:")
        print("   datasets/soil/soil_moisture_data.csv")
        sys.exit(1)

    # ── Load Data ──────────────────────────────────────────────────────────────
    print("\n📂 Loading dataset...")
    X_train, X_val, X_test, y_train, y_val, y_test = load_and_preprocess(DATASET_PATH)

    # ── Build & Train ──────────────────────────────────────────────────────────
    print("\n🏋️ Training Dense NN soil model...")
    model = build_soil_model(input_dim=X_train.shape[1])
    model.summary()

    callbacks = [
        keras.callbacks.EarlyStopping(patience=15, restore_best_weights=True, monitor="val_mae"),
        keras.callbacks.ReduceLROnPlateau(factor=0.5, patience=7, min_lr=1e-6, verbose=1),
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(OUTPUT_DIR, "soil_model_best.h5"),
            save_best_only=True, monitor="val_mae", verbose=1,
        ),
    ]

    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1,
    )

    # ── Save Final Model ───────────────────────────────────────────────────────
    final_path = os.path.join(OUTPUT_DIR, "soil_model.h5")
    model.save(final_path)
    print(f"\n✅ Final model saved to: {final_path}")

    # ── Evaluate ───────────────────────────────────────────────────────────────
    print("\n📊 Evaluation on test set:")
    y_pred = model.predict(X_test, verbose=0).flatten()

    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"   MAE:  {mae * 100:.2f}% moisture")
    print(f"   R²:   {r2:.4f}")

    # ── Plots ──────────────────────────────────────────────────────────────────
    plot_training_history(history)
    plot_predictions(y_test, y_pred)

    print("\n🎉 Training complete!")


if __name__ == "__main__":
    train()
