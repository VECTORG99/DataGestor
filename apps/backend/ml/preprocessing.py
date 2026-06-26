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


def cyclical_encode_month(df: pd.DataFrame) -> pd.DataFrame:
    """Cyclical encoding for month (sin + cos)."""
    df = df.copy()
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal lag features: crimes_last_month and avg_last_3_months.

    For each (borough, major_category, minor_category) group, computes:
    - crimes_last_month: total crimes in the previous month
    - avg_last_3_months: rolling average of the last 3 months
    """
    df = df.copy()
    df = df.sort_values(["borough", "major_category", "minor_category", "year", "month"])
    group_cols = ["borough", "major_category", "minor_category"]

    df["crimes_last_month"] = df.groupby(group_cols)["total_crimes"].shift(1)
    df["avg_last_3_months"] = df.groupby(group_cols)["total_crimes"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )

    # Fill NaN from first month of each group with 0
    df["crimes_last_month"] = df["crimes_last_month"].fillna(0)
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
        "crimes_last_month",
        "avg_last_3_months",
    ]
    return df[feature_cols]


def temporal_preprocess_and_split(
    df: pd.DataFrame,
    train_until_year: int = 2014,
):
    """Temporal split: train on years ≤ train_until_year, test on later years.

    This avoids data leakage from future data inflating metrics.
    """
    df = add_lag_features(df)
    y = create_classification_target(df)
    X = prepare_features(df)
    categorical_cols = ["borough", "major_category", "minor_category"]
    numeric_cols = [
        "year",
        "month_sin",
        "month_cos",
        "crimes_last_month",
        "avg_last_3_months",
    ]

    train_mask = df["year"] <= train_until_year
    X_train, X_test = X[train_mask], X[~train_mask]
    y_train, y_test = y[train_mask], y[~train_mask]

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)
    return X_train, X_test, y_train, y_test, preprocessor, df


def preprocess_and_split(
    df: pd.DataFrame,
    test_size: float = 0.3,
    random_state: int = 42,
):
    """Full preprocessing pipeline: features -> preprocessor -> split (classification).

    DEPRECATED: Use temporal_preprocess_and_split to avoid data leakage.
    """
    df = add_lag_features(df)
    y = create_classification_target(df)
    X = prepare_features(df)
    categorical_cols = ["borough", "major_category", "minor_category"]
    numeric_cols = [
        "year",
        "month_sin",
        "month_cos",
        "crimes_last_month",
        "avg_last_3_months",
    ]

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    return X_train, X_test, y_train, y_test, preprocessor
