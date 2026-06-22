FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code + data + models
COPY . .

# Verify/train model during build
RUN python apps/backend/cli/ml_pipeline.py

# Start FastAPI
CMD ["uvicorn", "apps.backend.api.predict:app", "--host", "0.0.0.0", "--port", "8000"]
