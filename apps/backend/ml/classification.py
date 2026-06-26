"""Classification module: Logistic Regression training and evaluation."""

import logging
import os

import joblib
import matplotlib
from config import settings

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    r2_score,
    precision_score,
    recall_score,
    roc_curve,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
)


def train_logistic_regression(X_train, y_train, max_iter=None):
    """Train Logistic Regression classifier."""
    model = LogisticRegression(
        max_iter=max_iter or settings.ML_LOGREG_MAX_ITER,
        random_state=settings.ML_RANDOM_STATE,
    )
    model.fit(X_train, y_train)
    logging.info("[ML] Logistic Regression entrenada.")
    return model


def train_crime_regressor(X_train, y_train):
    """Train a small regressor to estimate monthly crime count."""
    model = RandomForestRegressor(
        n_estimators=settings.ML_RF_N_ESTIMATORS,
        min_samples_leaf=settings.ML_RF_MIN_SAMPLES_LEAF,
        random_state=settings.ML_RANDOM_STATE,
        n_jobs=settings.ML_N_JOBS,
    )
    model.fit(X_train, y_train)
    logging.info("[ML] Crime count regressor entrenado.")
    return model


def evaluate_regression(model, X_test, y_test) -> dict:
    """Evaluate count regression."""
    y_pred = model.predict(X_test)
    return {
        "mae": round(mean_absolute_error(y_test, y_pred), 4),
        "r2": round(r2_score(y_test, y_pred), 4),
    }


def evaluate_classification(model, X_test, y_test, model_name: str = "model") -> dict:
    """Evaluate classifier. Returns all metrics."""
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else None

    metrics = {
        "model": model_name,
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
    }

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    metrics["confusion_matrix"] = cm.tolist()
    tn, fp, fn, tp = cm.ravel()
    metrics["true_negatives"] = int(tn)
    metrics["false_positives"] = int(fp)
    metrics["false_negatives"] = int(fn)
    metrics["true_positives"] = int(tp)

    # ROC AUC + Gini + full curve data
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_auc = auc(fpr, tpr)
        metrics["roc_auc"] = round(roc_auc, 4)
        metrics["gini"] = round(2 * roc_auc - 1, 4)
        metrics["roc_curve"] = {
            "fpr": [round(float(x), 6) for x in fpr],
            "tpr": [round(float(x), 6) for x in tpr],
        }

    return metrics


def plot_confusion_matrix(
    y_test,
    y_pred,
    save_path: str = None,
):
    """Save confusion matrix plot."""
    save_path = save_path or str(settings.METRICS_DIR / settings.ML_CONFUSION_MATRIX_FILENAME)
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax, cmap="Blues", values_format="d")
    ax.set_title("Matriz de Confusion")
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    logging.info(f"[ML] Matriz de confusion guardada en {save_path}")


def plot_roc_curve(
    y_test,
    y_proba,
    save_path: str = None,
):
    """Save ROC curve plot."""
    save_path = save_path or str(settings.METRICS_DIR / settings.ML_ROC_CURVE_FILENAME)
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)

    fig, ax = plt.subplots(figsize=(7, 5))
    RocCurveDisplay(fpr=fpr, tpr=tpr, roc_auc=roc_auc).plot(ax=ax)
    ax.plot([0, 1], [0, 1], "k--", label="Aleatorio")
    ax.set_title(f"Curva ROC (AUC = {roc_auc:.3f})")
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    logging.info(f"[ML] Curva ROC guardada en {save_path}")


def save_classification_model(model, path: str):
    """Save classifier model."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    logging.info(f"[ML] Modelo guardado en {path}")
