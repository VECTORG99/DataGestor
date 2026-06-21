"""Preprocessing module: feature engineering, encoding, targets, split."""

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline


def load_clean_data(path: str) -> pd.DataFrame:
    """Load cleaned dataset from CSV or Parquet."""
    if path.endswith(".parquet"):
        return pd.read_parquet(path)
    return pd.read_csv(path)


def create_classification_target(df: pd.DataFrame, method: str = "median") -> np.ndarray:
    """Create binary target: 1 if total_crimes > threshold, else 0."""
    threshold = df["total_crimes"].median() if method == "median" else df["total_crimes"].mean()
    return (df["total_crimes"] > threshold).astype(int).values


def create_regression_target(df: pd.DataFrame) -> np.ndarray:
    """Regression target: total_crimes."""
    return df["total_crimes"].values


def cyclical_encode_month(df: pd.DataFrame) -> pd.DataFrame:
    """Cyclical encoding for month (sin + cos)."""
    df = df.copy()
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def build_preprocessor(categorical_cols: list, numeric_cols: list):
    """Build ColumnTransformer: one-hot encoder + StandardScaler."""
    cat_pipeline = Pipeline(
        [
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            )
        ]
    )
    num_pipeline = Pipeline([("scaler", StandardScaler())])
    preprocessor = ColumnTransformer(
        [
            ("cat", cat_pipeline, categorical_cols),
            ("num", num_pipeline, numeric_cols),
        ]
    )
    return preprocessor


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare features: cyclical month encoding + select columns."""
    df = cyclical_encode_month(df)
    feature_cols = [
        "borough",
        "major_category",
        "minor_category",
        "year",
        "month_sin",
        "month_cos",
    ]
    return df[feature_cols]


def split_data(X, y, test_size=0.3, random_state=42, stratify=None):
    """Train/test split with optional stratification."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=stratify)


def preprocess_and_split(
    df: pd.DataFrame,
    target_type: str = "regression",
    test_size: float = 0.3,
    random_state: int = 42,
):
    """Full preprocessing pipeline: features -> preprocessor -> split."""
    if target_type == "regression":
        y = create_regression_target(df)
        stratify = None
    else:
        y = create_classification_target(df)
        stratify = y

    X = prepare_features(df)
    categorical_cols = ["borough", "major_category", "minor_category"]
    numeric_cols = ["year", "month_sin", "month_cos"]

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)
    X_train, X_test, y_train, y_test = split_data(X, y, test_size, random_state, stratify)

    return X_train, X_test, y_train, y_test, preprocessor
