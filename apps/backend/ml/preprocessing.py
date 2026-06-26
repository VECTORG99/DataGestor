"""Preprocessing module: feature engineering, encoding, targets, split.

Uses ONLY features available at inference time (borough, major_category,
minor_category, year, month_sin, month_cos). No lag features: they derive
from the target and are not providable by the single-row predict API.
"""

import logging

import logging

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Features used at inference (must match predict.py feature_cols)
CATEGORICAL_COLS = ["borough", "major_category", "minor_category"]
NUMERIC_COLS = ["year", "month_sin", "month_cos"]


def load_clean_data(path: str) -> pd.DataFrame:
    """Load cleaned dataset from CSV or Parquet."""
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def create_classification_target(df: pd.DataFrame, method: str = "median") -> np.ndarray:
    """Create binary target: 1 if total_crimes > threshold, else 0."""
    threshold = df["total_crimes"].median() if method == "median" else df["total_crimes"].mean()
    return (df["total_crimes"] > threshold).astype(int).values


def cyclical_encode_month(df: pd.DataFrame) -> pd.DataFrame:
    """Cyclical encoding for month (sin + cos)."""
    df = df.copy()
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def build_preprocessor(categorical_cols: list, numeric_cols: list):
    """Build ColumnTransformer: one-hot encoder + StandardScaler."""
    cat_pipeline = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]
    )
    num_pipeline = Pipeline([("scaler", StandardScaler())])
    return ColumnTransformer(
        [
            ("cat", cat_pipeline, categorical_cols),
            ("num", num_pipeline, numeric_cols),
        ]
    )


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the 6 inference-consistent features: borough, major_category,
    minor_category, year, month_sin, month_cos."""
    df = cyclical_encode_month(df)
    return df[CATEGORICAL_COLS + NUMERIC_COLS]


def temporal_preprocess_and_split(
    df: pd.DataFrame,
    train_until_year: int = 2014,
):
    """Temporal split: train on years <= train_until_year, test on later years.

    Falls back to random split if temporal split yields < 1 training sample
    (e.g. demo data that doesn't span the boundary).
    """
    y = create_classification_target(df)
    X = prepare_features(df)
    preprocessor = build_preprocessor(CATEGORICAL_COLS, NUMERIC_COLS)

    train_mask = df["year"] <= train_until_year
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]

    if len(X_train) < 1:
        logging.warning(
            "Temporal split: 0 registros de entrenamiento (todos los datos son > %s). "
            "Usando random split como fallback.",
            train_until_year,
        )
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.3, random_state=42, stratify=y
        )

    return X_train, X_test, y_train, y_test, preprocessor, df
