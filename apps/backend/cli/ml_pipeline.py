#!/usr/bin/env python
"""
Machine Learning Pipeline for London Crime.
Usage: python apps/backend/cli/ml_pipeline.py

Trains Logistic Regression to classify high/low crime.
"""

import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.backend.ml.preprocessing import load_clean_data, preprocess_and_split
from apps.backend.ml.classification import (
    evaluate_classification,
    plot_confusion_matrix,
    plot_roc_curve,
    save_classification_model,
    train_logistic_regression,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "london_crime_aggregated.csv"
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
MODELS_DIR = PROJECT_ROOT / "data" / "models"


def main():
    logging.info("=" * 60)
    logging.info("LOGISTIC REGRESSION - LONDON CRIME")
    logging.info("=" * 60)

    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # ---- 1. Load data ----
    logging.info("[1/4] Cargando datos limpios...")
    df = load_clean_data(str(DATA_PATH))
    logging.info(f"  Registros cargados: {len(df)}")

    # ---- 2. Preprocess ----
    logging.info("[2/4] Preprocesando...")
    X_train, X_test, y_train, y_test, pre = preprocess_and_split(df, random_state=42)
    X_train_t = pre.fit_transform(X_train)
    X_test_t = pre.transform(X_test)

    # ---- 3. Train & evaluate ----
    logging.info("-" * 40)
    logging.info("ENTRENANDO LOGISTIC REGRESSION")
    logging.info("-" * 40)

    logreg = train_logistic_regression(X_train_t, y_train)
    metrics = evaluate_classification(logreg, X_test_t, y_test, "LogisticRegression")
    y_proba = logreg.predict_proba(X_test_t)[:, 1]
    plot_confusion_matrix(y_test, logreg.predict(X_test_t),
                          save_path=str(METRICS_DIR / "confusion_matrix.png"))
    plot_roc_curve(y_test, y_proba,
                   save_path=str(METRICS_DIR / "roc_curve.png"))
    save_classification_model(logreg, path=str(MODELS_DIR / "logistic_regression.joblib"))

    # ---- Save metrics ----
    with open(METRICS_DIR / "ml_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    logging.info("[3/4] Metricas guardadas")

    # ---- Summary ----
    logging.info("=" * 60)
    logging.info("RESUMEN")
    logging.info("=" * 60)
    for k in ("accuracy", "precision", "recall", "f1_score", "roc_auc", "gini"):
        logging.info(f"  {k}: {metrics.get(k, 'N/A')}")
    logging.info("=" * 60)
    logging.info("[4/4] PIPELINE ML FINALIZADO")


if __name__ == "__main__":
    main()
