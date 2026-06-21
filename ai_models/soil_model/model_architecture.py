"""
AgriCrop – Soil Moisture Model Architecture
Dense Sequential Neural Network for Soil Moisture Prediction.

Input features (6):
  temperature, humidity, rainfall, wind_speed, soil_type_idx, previous_moisture

Output (1):
  predicted_moisture (normalized 0–1, multiply by 100 for %)
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, regularizers


def build_soil_model(
    input_dim: int = 6,
    dropout_rate: float = 0.2,
    l2_reg: float = 1e-4,
) -> keras.Model:
    """
    Build a Dense NN for soil moisture regression.

    Architecture:
    Input(6) → Dense(128, ReLU) → BN → Dropout
             → Dense(64, ReLU)  → BN → Dropout
             → Dense(32, ReLU)  → BN
             → Dense(1, Sigmoid)   ← output: moisture in [0,1]

    Args:
        input_dim: Number of input features (default 6).
        dropout_rate: Dropout probability.
        l2_reg: L2 regularization weight.

    Returns:
        Compiled Keras model.
    """
    reg = regularizers.l2(l2_reg)

    model = keras.Sequential([
        layers.Input(shape=(input_dim,), name="soil_features"),

        # Block 1
        layers.Dense(128, activation="relu", kernel_regularizer=reg, name="dense_128"),
        layers.BatchNormalization(),
        layers.Dropout(dropout_rate),

        # Block 2
        layers.Dense(64, activation="relu", kernel_regularizer=reg, name="dense_64"),
        layers.BatchNormalization(),
        layers.Dropout(dropout_rate),

        # Block 3
        layers.Dense(32, activation="relu", kernel_regularizer=reg, name="dense_32"),
        layers.BatchNormalization(),

        # Output: sigmoid gives [0,1]; multiply by 100 for moisture %
        layers.Dense(1, activation="sigmoid", name="moisture_output"),
    ], name="AgriCrop_SoilPredictor")

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="mse",
        metrics=["mae", tf.keras.metrics.RootMeanSquaredError(name="rmse")],
    )

    return model


if __name__ == "__main__":
    model = build_soil_model()
    model.summary()
    print(f"\nTotal parameters: {model.count_params():,}")
