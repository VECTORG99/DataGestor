#!/usr/bin/env python
"""
Machine Learning Pipeline for London Crime.
Usage: python apps/backend/cli/ml_pipeline.py

Trains:
  1. Linear Regression (predict total_crimes)
  2. Logistic Regression (classify high/low crime)
  3. Random Forest (classify high/low crime)
"""

import json
import logging
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apps.backend.ml.preprocessing import (
    load_clean_data,
    preprocess_and_split,
)
from apps.backend.ml.regression import (
    evaluate_regression,
    plot_residuals,
    save_regression_model,
    train_linear_regression,
)
from apps.backend.ml.classification import (
    evaluate_classification,
    plot_confusion_matrix,
    plot_feature_importance,
    plot_roc_curve,
    save_classification_model,
    train_logistic_regression,
    train_random_forest,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

DATA_PATH = PROJECT_ROOT / "data" / "processed" / "london_crime_aggregated.csv"
METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
MODELS_DIR = PROJECT_ROOT / "data" / "models"
CAT_COLS = ["borough", "major_category", "minor_category"]
NUM_COLS = ["year", "month_sin", "month_cos"]


def get_feature_names(preprocessor):
    """Extract feature names from fitted ColumnTransformer."""
    cat_names = list(
        preprocessor.named_transformers_["cat"]
        .named_steps["onehot"]
        .get_feature_names_out(CAT_COLS)
    )
    return cat_names + NUM_COLS


def main():
    logging.info("=" * 60)
    logging.info("PIPELINE DE MACHINE LEARNING - LONDON CRIME")
    logging.info("=" * 60)

    os.makedirs(METRICS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)

    # ---- 1. Load data ----
    logging.info("[1/6] Cargando datos limpios...")
    df = load_clean_data(str(DATA_PATH))
    logging.info(f"  Registros cargados: {len(df)}")

    # ---- 2. Preprocess for regression ----
    logging.info("[2/6] Preprocesando para regresion...")
    X_train_r, X_test_r, y_train_r, y_test_r, pre_r = preprocess_and_split(
        df, target_type="regression", random_state=42
    )

    # ---- 3. Preprocess for classification ----
    logging.info("[3/6] Preprocesando para clasificacion...")
    X_train_c, X_test_c, y_train_c, y_test_c, pre_c = preprocess_and_split(
        df, target_type="classification", random_state=42
    )

    # ========================
    # REGRESSION
    # ========================
    logging.info("-" * 40)
    logging.info("REGRESION LINEAL")
    logging.info("-" * 40)

    X_train_r_t = pre_r.fit_transform(X_train_r)
    X_test_r_t = pre_r.transform(X_test_r)
    feature_names_r = get_feature_names(pre_r)

    model_lr = train_linear_regression(X_train_r_t, y_train_r)
    metrics_lr = evaluate_regression(model_lr, X_test_r_t, y_test_r, feature_names_r)
    plot_residuals(
        y_test_r,
        model_lr.predict(X_test_r_t),
        save_path=str(METRICS_DIR / "residuals.png"),
    )
    save_regression_model(model_lr, path=str(MODELS_DIR / "linear_regression.joblib"))

    # ========================
    # CLASSIFICATION
    # ========================
    logging.info("-" * 40)
    logging.info("CLASIFICACION")
    logging.info("-" * 40)

    X_train_c_t = pre_c.fit_transform(X_train_c)
    X_test_c_t = pre_c.transform(X_test_c)
    feature_names_c = get_feature_names(pre_c)

    # Logistic Regression
    logreg = train_logistic_regression(X_train_c_t, y_train_c)
    metrics_lr_cls = evaluate_classification(logreg, X_test_c_t, y_test_c, "LogisticRegression")
    y_proba_lr = logreg.predict_proba(X_test_c_t)[:, 1]
    plot_confusion_matrix(
        y_test_c,
        logreg.predict(X_test_c_t),
        save_path=str(METRICS_DIR / "confusion_matrix_logreg.png"),
    )
    plot_roc_curve(
        y_test_c,
        y_proba_lr,
        save_path=str(METRICS_DIR / "roc_curve_logreg.png"),
    )
    save_classification_model(logreg, path=str(MODELS_DIR / "logistic_regression.joblib"))

    # Random Forest
    rf = train_random_forest(X_train_c_t, y_train_c)
    metrics_rf = evaluate_classification(rf, X_test_c_t, y_test_c, "RandomForest")
    y_proba_rf = rf.predict_proba(X_test_c_t)[:, 1]
    plot_confusion_matrix(
        y_test_c,
        rf.predict(X_test_c_t),
        save_path=str(METRICS_DIR / "confusion_matrix_rf.png"),
    )
    plot_roc_curve(
        y_test_c,
        y_proba_rf,
        save_path=str(METRICS_DIR / "roc_curve_rf.png"),
    )
    plot_feature_importance(
        rf,
        feature_names_c,
        save_path=str(METRICS_DIR / "feature_importance_rf.png"),
    )
    save_classification_model(rf, path=str(MODELS_DIR / "random_forest.joblib"))

    # ========================
    # SAVE METRICS
    # ========================
    all_metrics = {
        "regression": metrics_lr,
        "classification": {
            "LogisticRegression": metrics_lr_cls,
            "RandomForest": metrics_rf,
        },
    }
    metrics_path = METRICS_DIR / "ml_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    logging.info(f"[6/6] Metricas ML guardadas en {metrics_path}")

    # ========================
    # SUMMARY
    # ========================
    logging.info("=" * 60)
    logging.info("RESUMEN DE METRICAS - PIPELINE ML")
    logging.info("=" * 60)
    logging.info("REGRESION LINEAL:")
    logging.info(f"  R2    = {metrics_lr['r2_score']}")
    logging.info(f"  RMSE  = {metrics_lr['rmse']}")
    logging.info(f"  MAE   = {metrics_lr['mae']}")
    logging.info("CLASIFICACION:")
    for name, m in [
        ("LogisticRegression", metrics_lr_cls),
        ("RandomForest", metrics_rf),
    ]:
        logging.info(f"  {name}:")
        logging.info(f"    Accuracy  = {m['accuracy']}")
        logging.info(f"    Precision = {m['precision']}")
        logging.info(f"    Recall    = {m['recall']}")
        logging.info(f"    F1        = {m['f1_score']}")
        logging.info(f"    ROC AUC   = {m.get('roc_auc', 'N/A')}")
        logging.info(f"    Gini      = {m.get('gini', 'N/A')}")
    logging.info("=" * 60)
    logging.info("PIPELINE ML FINALIZADO CON EXITO")


if __name__ == "__main__":
    main()
