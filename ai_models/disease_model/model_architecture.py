"""
AgriCrop – Disease Model Architecture
MobileNetV2 Transfer Learning for Plant Disease Detection.
38 classes (PlantVillage dataset).
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.applications import MobileNetV2


def build_disease_model(
    num_classes: int = 38,
    input_shape: tuple = (224, 224, 3),
    dropout_rate: float = 0.3,
    fine_tune_layers: int = 20,
) -> keras.Model:
    """
    Build the MobileNetV2 transfer learning model for disease detection.

    Architecture:
    - Base: MobileNetV2 (pretrained on ImageNet, weights frozen initially)
    - Global Average Pooling
    - Dropout
    - Dense 512 (ReLU)
    - Dropout
    - Dense num_classes (Softmax)

    Args:
        num_classes: Number of output disease classes (default 38).
        input_shape: Input image dimensions (H, W, C).
        dropout_rate: Dropout probability for regularization.
        fine_tune_layers: Number of top base model layers to unfreeze for fine-tuning.

    Returns:
        Compiled Keras model.
    """
    # ── Base Model ────────────────────────────────────────────────────────────
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base_model.trainable = False  # Freeze initially for feature extraction

    # ── Custom Classification Head ────────────────────────────────────────────
    inputs = keras.Input(shape=input_shape, name="leaf_input")

    # MobileNetV2 preprocess: scale pixel values to [-1, 1]
    x = tf.keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D(name="gap")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(dropout_rate, name="dropout_1")(x)
    x = layers.Dense(512, activation="relu", name="dense_512")(x)
    x = layers.Dropout(dropout_rate / 2, name="dropout_2")(x)
    outputs = layers.Dense(num_classes, activation="softmax", name="predictions")(x)

    model = keras.Model(inputs, outputs, name="AgriCrop_DiseaseDetector")

    # ── Compile ────────────────────────────────────────────────────────────────
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy", keras.metrics.TopKCategoricalAccuracy(k=3, name="top3_accuracy")],
    )

    return model


def unfreeze_for_fine_tuning(model: keras.Model, fine_tune_layers: int = 20) -> keras.Model:
    """
    Unfreeze the top N layers of the base MobileNetV2 model for fine-tuning.
    Call this AFTER initial training has converged.

    Args:
        model: The compiled disease detection model.
        fine_tune_layers: Number of top base model layers to unfreeze.

    Returns:
        Re-compiled model ready for fine-tuning.
    """
    # The base model is the 3rd layer (index 2) of the model
    base_model = model.layers[3]  # MobileNetV2 layer
    base_model.trainable = True

    # Freeze all layers except the top fine_tune_layers
    for layer in base_model.layers[:-fine_tune_layers]:
        layer.trainable = False

    # Re-compile with lower learning rate for fine-tuning
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-5),
        loss="categorical_crossentropy",
        metrics=["accuracy", keras.metrics.TopKCategoricalAccuracy(k=3, name="top3_accuracy")],
    )

    print(f"✅ Unfroze top {fine_tune_layers} layers for fine-tuning")
    print(f"   Trainable params: {sum(tf.size(w).numpy() for w in model.trainable_weights):,}")
    return model


def get_model_summary(model: keras.Model) -> str:
    """Return the model summary as a string."""
    summary_lines = []
    model.summary(print_fn=lambda x: summary_lines.append(x))
    return "\n".join(summary_lines)


if __name__ == "__main__":
    model = build_disease_model()
    model.summary()
    print(f"\nTotal parameters: {model.count_params():,}")
