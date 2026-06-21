"""
AgriCrop – Disease Model Training Script
Full training pipeline for MobileNetV2 plant disease detection.

Dataset: PlantVillage (https://www.kaggle.com/datasets/emmarex/plantdisease)
Expected structure:
  datasets/PlantVillage/
      Apple___Apple_scab/
      Apple___Black_rot/
      ...
      Tomato___healthy/

Usage:
    python -m ai_models.disease_model.train_disease_model
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
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import classification_report, confusion_matrix

from ai_models.disease_model.model_architecture import build_disease_model, unfreeze_for_fine_tuning

# ── Configuration ─────────────────────────────────────────────────────────────
DATASET_DIR   = "datasets/PlantVillage"
OUTPUT_DIR    = "ai_models/saved_models"
LABELS_PATH   = "datasets/disease/disease_labels.csv"
IMG_SIZE      = (224, 224)
BATCH_SIZE    = 32
EPOCHS_HEAD   = 15      # Phase 1: train head only
EPOCHS_FINE   = 10      # Phase 2: fine-tune top layers
NUM_CLASSES   = 38
RANDOM_SEED   = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)
tf.random.set_seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def create_data_generators():
    """Create train, validation, and test data generators with augmentation."""

    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=0.2,
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        brightness_range=[0.7, 1.3],
        fill_mode="nearest",
    )

    val_datagen = ImageDataGenerator(
        rescale=1.0 / 255.0,
        validation_split=0.2,
    )

    train_gen = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="training",
        shuffle=True,
        seed=RANDOM_SEED,
    )

    val_gen = val_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMG_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        subset="validation",
        shuffle=False,
        seed=RANDOM_SEED,
    )

    return train_gen, val_gen


def save_class_labels(class_indices: dict):
    """Save class index → label mapping to CSV for inference use."""
    df = pd.DataFrame([
        {"index": v, "class_key": k, "display_name": k.replace("___", " – ").replace("_", " ")}
        for k, v in sorted(class_indices.items(), key=lambda x: x[1])
    ])
    df.to_csv(LABELS_PATH, index=False)
    print(f"✅ Class labels saved to {LABELS_PATH}")


def plot_training_history(history_head, history_fine):
    """Save training accuracy and loss plots."""
    epochs_head = range(1, len(history_head.history["accuracy"]) + 1)
    epochs_fine = range(
        len(history_head.history["accuracy"]) + 1,
        len(history_head.history["accuracy"]) + len(history_fine.history["accuracy"]) + 1,
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Accuracy
    ax1.plot(epochs_head, history_head.history["accuracy"], "b-o", label="Train (head)", markersize=4)
    ax1.plot(epochs_head, history_head.history["val_accuracy"], "r-o", label="Val (head)", markersize=4)
    ax1.plot(epochs_fine, history_fine.history["accuracy"], "b--s", label="Train (fine-tune)", markersize=4)
    ax1.plot(epochs_fine, history_fine.history["val_accuracy"], "r--s", label="Val (fine-tune)", markersize=4)
    ax1.set_title("Model Accuracy", fontsize=14)
    ax1.set_xlabel("Epoch"); ax1.set_ylabel("Accuracy")
    ax1.legend(); ax1.grid(True, alpha=0.3)

    # Loss
    ax2.plot(epochs_head, history_head.history["loss"], "b-o", label="Train loss (head)", markersize=4)
    ax2.plot(epochs_head, history_head.history["val_loss"], "r-o", label="Val loss (head)", markersize=4)
    ax2.plot(epochs_fine, history_fine.history["loss"], "b--s", label="Train loss (fine-tune)", markersize=4)
    ax2.plot(epochs_fine, history_fine.history["val_loss"], "r--s", label="Val loss (fine-tune)", markersize=4)
    ax2.set_title("Model Loss", fontsize=14)
    ax2.set_xlabel("Epoch"); ax2.set_ylabel("Loss")
    ax2.legend(); ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(OUTPUT_DIR, "disease_training_history.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✅ Training history plot saved to {plot_path}")


def train():
    print("=" * 60)
    print("  AgriCrop – Disease Model Training")
    print("=" * 60)
    print(f"  TensorFlow version: {tf.__version__}")
    print(f"  Dataset: {DATASET_DIR}")
    print(f"  Output: {OUTPUT_DIR}")

    if not os.path.exists(DATASET_DIR):
        print(f"\n❌ Dataset not found at '{DATASET_DIR}'")
        print("   Download PlantVillage from: https://www.kaggle.com/datasets/emmarex/plantdisease")
        print("   Extract to: datasets/PlantVillage/")
        sys.exit(1)

    # ── Data ──────────────────────────────────────────────────────────────────
    print("\n📂 Loading dataset...")
    train_gen, val_gen = create_data_generators()
    num_classes = len(train_gen.class_indices)
    print(f"   Classes found: {num_classes}")
    print(f"   Training samples: {train_gen.samples}")
    print(f"   Validation samples: {val_gen.samples}")

    save_class_labels(train_gen.class_indices)

    # ── Phase 1: Train Classification Head ────────────────────────────────────
    print(f"\n🏋️ Phase 1: Training classification head ({EPOCHS_HEAD} epochs)...")
    model = build_disease_model(num_classes=num_classes)

    callbacks_head = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
        keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-7, verbose=1),
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(OUTPUT_DIR, "disease_model_head_best.h5"),
            save_best_only=True, monitor="val_accuracy", verbose=1,
        ),
    ]

    history_head = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_HEAD,
        callbacks=callbacks_head,
        verbose=1,
    )

    # ── Phase 2: Fine-Tune Top Layers ─────────────────────────────────────────
    print(f"\n🔧 Phase 2: Fine-tuning top 20 base model layers ({EPOCHS_FINE} epochs)...")
    model = unfreeze_for_fine_tuning(model, fine_tune_layers=20)

    callbacks_fine = [
        keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True, monitor="val_accuracy"),
        keras.callbacks.ReduceLROnPlateau(factor=0.3, patience=3, min_lr=1e-8, verbose=1),
        keras.callbacks.ModelCheckpoint(
            filepath=os.path.join(OUTPUT_DIR, "disease_model_fine_best.h5"),
            save_best_only=True, monitor="val_accuracy", verbose=1,
        ),
    ]

    history_fine = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=EPOCHS_FINE,
        callbacks=callbacks_fine,
        verbose=1,
    )

    # ── Save Final Model ───────────────────────────────────────────────────────
    final_path = os.path.join(OUTPUT_DIR, "disease_model.h5")
    model.save(final_path)
    print(f"\n✅ Final model saved to: {final_path}")

    # ── Evaluation ─────────────────────────────────────────────────────────────
    print("\n📊 Evaluating on validation set...")
    results = model.evaluate(val_gen, verbose=1)
    print(f"   Val Loss: {results[0]:.4f}")
    print(f"   Val Accuracy: {results[1]:.4f} ({results[1]*100:.2f}%)")

    # ── Plot History ───────────────────────────────────────────────────────────
    plot_training_history(history_head, history_fine)

    print("\n🎉 Training complete!")
    print(f"   Model path: {final_path}")


if __name__ == "__main__":
    train()
