"""Tests for the ML pipeline module."""

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def sample_df():
    """Mini dataset for tests."""
    np.random.seed(42)
    n = 50
    return pd.DataFrame(
        {
            "borough": np.random.choice(["Camden", "Westminster", "Brent"], n),
            "major_category": np.random.choice(
                ["Violence Against the Person", "Theft and Handling", "Burglary"], n
            ),
            "minor_category": np.random.choice(
                ["Assault with injury", "Shoplifting", "Burglary in a dwelling"], n
            ),
            "year": np.random.choice([2016, 2017, 2018, 2019], n),
            "month": np.random.randint(1, 13, n),
            "total_crimes": np.random.poisson(15, n).astype(float),
            "date": pd.date_range("2016-01-01", periods=n, freq="ME"),
        }
    )


class TestPreprocessing:
    def test_load_clean_data_csv(self, tmp_path, sample_df):
        from apps.backend.ml.preprocessing import load_clean_data

        path = tmp_path / "test.csv"
        sample_df.to_csv(path, index=False)
        df = load_clean_data(str(path))
        assert len(df) == 50
        assert "total_crimes" in df.columns

    def test_create_classification_target(self, sample_df):
        from apps.backend.ml.preprocessing import create_classification_target

        y = create_classification_target(sample_df, method="median")
        assert y.dtype == np.int64 or y.dtype == int
        assert set(np.unique(y)).issubset({0, 1})
        ratio = y.mean()
        assert 0.3 <= ratio <= 0.7

    def test_cyclical_encode_month(self, sample_df):
        from apps.backend.ml.preprocessing import cyclical_encode_month

        df = cyclical_encode_month(sample_df.copy())
        assert "month_sin" in df.columns
        assert "month_cos" in df.columns
        sums = (df["month_sin"] ** 2 + df["month_cos"] ** 2).values
        assert np.allclose(sums, 1.0, atol=1e-10)

    def test_build_preprocessor(self, sample_df):
        from apps.backend.ml.preprocessing import build_preprocessor

        preprocessor = build_preprocessor(["borough", "major_category"], ["year"])
        X = sample_df[["borough", "major_category", "year"]]
        X_t = preprocessor.fit_transform(X)
        assert X_t.shape[0] == 50
        assert X_t.shape[1] > 3

    def test_preprocess_and_split_classification(self, sample_df):
        from apps.backend.ml.preprocessing import preprocess_and_split

        X_train, X_test, y_train, y_test, preprocessor = preprocess_and_split(
            sample_df, test_size=0.3, random_state=42
        )
        assert set(np.unique(y_train)).issubset({0, 1})
        assert set(np.unique(y_test)).issubset({0, 1})


class TestClassification:
    def test_train_logistic_regression(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            create_classification_target,
            prepare_features,
        )
        from apps.backend.ml.classification import train_logistic_regression

        X = prepare_features(sample_df)
        y = create_classification_target(sample_df)
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        X_t = preprocessor.fit_transform(X)
        model = train_logistic_regression(X_t[:40], y[:40])
        assert hasattr(model, "coef_")
        assert hasattr(model, "predict_proba")

    def test_evaluate_classification_returns_all_metrics(self, sample_df):
        from apps.backend.ml.preprocessing import (
            build_preprocessor,
            create_classification_target,
            prepare_features,
        )
        from apps.backend.ml.classification import (
            evaluate_classification,
            train_logistic_regression,
        )

        X = prepare_features(sample_df)
        y = create_classification_target(sample_df)
        preprocessor = build_preprocessor(
            ["borough", "major_category", "minor_category"],
            ["year", "month_sin", "month_cos"],
        )
        X_t = preprocessor.fit_transform(X)
        model = train_logistic_regression(X_t[:40], y[:40])
        metrics = evaluate_classification(model, X_t[40:], y[40:], "LogReg")
        for key in ["accuracy", "precision", "recall", "f1_score", "confusion_matrix"]:
            assert key in metrics, f"Missing metric: {key}"
        assert len(metrics["confusion_matrix"]) == 2
        assert len(metrics["confusion_matrix"][0]) == 2
