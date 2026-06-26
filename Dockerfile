FROM python:3.12-slim

WORKDIR /app

# Install system deps (gcc for scikit-learn, curl for model downloads)
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code + data
COPY . .

# Download pre-trained models from GitHub release, fallback to training
RUN mkdir -p data/models && \
    for f in logistic_regression.joblib crime_regressor.joblib preprocessor.joblib; do \
      curl -sfL "https://github.com/VECTORG99/DataGestor/releases/download/ml-models-latest/$f" -o "data/models/$f" || echo "Warning: $f download failed"; \
    done && \
    if [ ! -f data/models/logistic_regression.joblib ] || [ ! -f data/models/crime_regressor.joblib ] || [ ! -f data/models/preprocessor.joblib ]; then \
      echo "No pre-trained models found, training at build time..." && \
      python apps/backend/cli/ml_pipeline.py; \
    else \
      echo "Models downloaded from release ml-models-latest"; \
    fi

# Start FastAPI
CMD ["uvicorn", "apps.backend.api.predict:app", "--host", "0.0.0.0", "--port", "8000"]
