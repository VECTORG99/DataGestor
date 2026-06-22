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
import time
from pathlib import Path

import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.backend.ml.preprocessing import load_clean_data, preprocess_and_split
from apps.backend.pipeline.metrics import configure_logging
from config import settings
from apps.backend.ml.classification import (
    evaluate_classification,
    evaluate_regression,
    plot_confusion_matrix,
    plot_roc_curve,
    save_classification_model,
    train_crime_regressor,
    train_logistic_regression,
)

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "london_crime_aggregated.csv"
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
MODELS_DIR = PROJECT_ROOT / "data" / "models"


def main():
    configure_logging()
    started = time.time()
    hyperparameters = {
        "random_state": settings.ML_RANDOM_STATE,
        "logreg_max_iter": settings.ML_LOGREG_MAX_ITER,
        "rf_n_estimators": settings.ML_RF_N_ESTIMATORS,
        "rf_min_samples_leaf": settings.ML_RF_MIN_SAMPLES_LEAF,
        "n_jobs": settings.ML_N_JOBS,
    }
    logging.info("ml_pipeline_started", extra={"hyperparameters": hyperparameters})
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
    X_train, X_test, y_train, y_test, pre = preprocess_and_split(
        df, random_state=settings.ML_RANDOM_STATE
    )
    X_train_t = pre.fit_transform(X_train)
    X_test_t = pre.transform(X_test)

    # ---- 3. Train & evaluate ----
    logging.info("-" * 40)
    logging.info("ENTRENANDO LOGISTIC REGRESSION")
    logging.info("-" * 40)

    logreg = train_logistic_regression(X_train_t, y_train)
    metrics = evaluate_classification(logreg, X_test_t, y_test, "LogisticRegression")
    y_proba = logreg.predict_proba(X_test_t)[:, 1]
    plot_confusion_matrix(
        y_test,
        logreg.predict(X_test_t),
        save_path=str(METRICS_DIR / settings.ML_CONFUSION_MATRIX_FILENAME),
    )
    plot_roc_curve(y_test, y_proba, save_path=str(METRICS_DIR / settings.ML_ROC_CURVE_FILENAME))
    save_classification_model(logreg, path=str(MODELS_DIR / settings.ML_CLASSIFIER_FILENAME))
    # Save fitted preprocessor for inference API
    joblib.dump(pre, MODELS_DIR / settings.ML_PREPROCESSOR_FILENAME)
    logging.info(f"[ML] Preprocesador guardado en {MODELS_DIR / settings.ML_PREPROCESSOR_FILENAME}")

    y_count_train = df.loc[X_train.index, "total_crimes"].values
    y_count_test = df.loc[X_test.index, "total_crimes"].values
    regressor = train_crime_regressor(X_train_t, y_count_train)
    regression_metrics = evaluate_regression(regressor, X_test_t, y_count_test)
    joblib.dump(regressor, MODELS_DIR / settings.ML_REGRESSOR_FILENAME)
    logging.info(f"[ML] Regresor guardado en {MODELS_DIR / settings.ML_REGRESSOR_FILENAME}")
    metrics["regression"] = regression_metrics

    # ---- Save metrics ----
    metrics["schema_version"] = settings.METRICS_SCHEMA_VERSION
    metrics["hyperparameters"] = hyperparameters
    metrics["duration_seconds"] = round(time.time() - started, 2)
    with open(METRICS_DIR / settings.ML_METRICS_FILENAME, "w") as f:
        json.dump(metrics, f, indent=2)
    logging.info(
        "ml_metrics_saved",
        extra={
            "model": "LogisticRegression+RandomForestRegressor",
            "metrics": metrics,
            "duration_seconds": metrics["duration_seconds"],
            "hyperparameters": hyperparameters,
        },
    )
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
