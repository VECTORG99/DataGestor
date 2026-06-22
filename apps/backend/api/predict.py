"""FastAPI predict endpoint for Logistic Regression crime classifier."""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MODELS_DIR = PROJECT_ROOT / "data" / "models"

app = FastAPI(title="London Crime Historical Estimator", version="0.1")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Lazy-load model + preprocessor
_model = None
_preprocessor = None
_regressor = None


def _load_artifacts():
    global _model, _preprocessor, _regressor
    model_path = MODELS_DIR / "logistic_regression.joblib"
    regressor_path = MODELS_DIR / "crime_regressor.joblib"
    prep_path = MODELS_DIR / "preprocessor.joblib"
    if not model_path.exists() or not prep_path.exists() or not regressor_path.exists():
        raise RuntimeError(
            "Model artifacts not found. Run `python apps/backend/cli/ml_pipeline.py` first."
        )
    _model = joblib.load(model_path)
    _regressor = joblib.load(regressor_path)
    _preprocessor = joblib.load(prep_path)


class PredictInput(BaseModel):
    borough: str
    major_category: str
    minor_category: str
    year: int
    month: int


class PredictOutput(BaseModel):
    prediction: int  # 0 = bajo, 1 = alto
    probability_high: float
    probability_low: float
    predicted_crimes: int
    predicted_crimes_raw: float
    threshold: float
    features_used: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictOutput)
def predict(input_data: PredictInput):
    try:
        if _model is None or _preprocessor is None or _regressor is None:
            _load_artifacts()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Build single-row DataFrame with cyclical month
    raw = pd.DataFrame(
        [
            {
                "borough": input_data.borough,
                "major_category": input_data.major_category,
                "minor_category": input_data.minor_category,
                "year": input_data.year,
                "month": input_data.month,
                "month_sin": np.sin(2 * np.pi * input_data.month / 12),
                "month_cos": np.cos(2 * np.pi * input_data.month / 12),
            }
        ]
    )

    feature_cols = ["borough", "major_category", "minor_category", "year", "month_sin", "month_cos"]
    X = raw[feature_cols]

    try:
        X_t = _preprocessor.transform(X)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Preprocessing error: {e}")

    pred = int(_model.predict(X_t)[0])
    proba = _model.predict_proba(X_t)[0]
    predicted_crimes_raw = max(0.0, float(_regressor.predict(X_t)[0]))
    prob_low = round(float(proba[0]), 4)
    prob_high = round(float(proba[1]), 4)

    return PredictOutput(
        prediction=pred,
        probability_high=prob_high,
        probability_low=prob_low,
        predicted_crimes=round(predicted_crimes_raw),
        predicted_crimes_raw=round(predicted_crimes_raw, 2),
        threshold=0.5,
        features_used=X_t.shape[1],
    )
