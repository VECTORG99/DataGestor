"""Regression module: Linear Regression training and evaluation."""

import logging
import os

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error


def train_linear_regression(X_train, y_train):
    """Train linear regression model."""
    model = LinearRegression()
    model.fit(X_train, y_train)
    logging.info(f"[ML] Regresion Lineal entrenada. Coeficientes: {len(model.coef_)}")
    return model


def evaluate_regression(model, X_test, y_test, feature_names: list = None) -> dict:
    """Evaluate regression model. Returns metrics dict."""
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    residuals = y_test - y_pred

    metrics = {
        "r2_score": round(r2, 4),
        "rmse": round(rmse, 2),
        "mae": round(mae, 2),
        "mean_actual": round(float(y_test.mean()), 2),
        "mean_predicted": round(float(y_pred.mean()), 2),
        "residuals_mean": round(float(residuals.mean()), 2),
        "residuals_std": round(float(residuals.std()), 2),
    }

    if feature_names is not None and hasattr(model, "coef_"):
        coef_df = pd.DataFrame({"feature": feature_names, "coefficient": model.coef_}).sort_values(
            "coefficient", key=abs, ascending=False
        )
        metrics["top_coefficients"] = coef_df.head(10).to_dict("records")

    return metrics


def plot_residuals(y_test, y_pred, save_path: str = "/app/data/metrics/residuals.png"):
    """Generate residual plot."""
    residuals = y_test - y_pred
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].scatter(y_pred, residuals, alpha=0.3)
    axes[0].axhline(y=0, color="r", linestyle="--")
    axes[0].set_xlabel("Predicho")
    axes[0].set_ylabel("Residual")
    axes[0].set_title("Residuales vs Predicho")

    sns.histplot(residuals, kde=True, ax=axes[1])
    axes[1].set_xlabel("Residual")
    axes[1].set_title("Distribucion de Residuales")

    plt.tight_layout()
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    logging.info(f"[ML] Grafico de residuales guardado en {save_path}")


def save_regression_model(model, path: str = "/app/data/models/linear_regression.joblib"):
    """Save trained model."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logging.info(f"[ML] Modelo guardado en {path}")
