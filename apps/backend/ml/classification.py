"""Classification module: Logistic Regression training and evaluation."""

import logging
import os

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_curve,
    ConfusionMatrixDisplay,
    RocCurveDisplay,
)


def train_logistic_regression(X_train, y_train, max_iter=1000):
    """Train Logistic Regression classifier."""
    model = LogisticRegression(max_iter=max_iter, random_state=42)
    model.fit(X_train, y_train)
    logging.info("[ML] Logistic Regression entrenada.")
    return model


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

    # ROC AUC + Gini
    if y_proba is not None:
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_auc = auc(fpr, tpr)
        metrics["roc_auc"] = round(roc_auc, 4)
        metrics["gini"] = round(2 * roc_auc - 1, 4)

    return metrics


def plot_confusion_matrix(
    y_test,
    y_pred,
    save_path: str = "/app/data/metrics/confusion_matrix.png",
):
    """Save confusion matrix plot."""
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(y_test, y_pred, ax=ax, cmap="Blues", values_format="d")
    ax.set_title("Matriz de Confusion")
    plt.savefig(save_path, dpi=100, bbox_inches="tight")
    plt.close()
    logging.info(f"[ML] Matriz de confusion guardada en {save_path}")


def plot_roc_curve(
    y_test,
    y_proba,
    save_path: str = "/app/data/metrics/roc_curve.png",
):
    """Save ROC curve plot."""
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
