# London Crime Data Platform

Dashboard de crimen de Londres + estimador histórico basado en ML.

> El modelo **no predice el futuro**. Estima perfiles históricos aprendidos del dataset 2008-2016. La limitación está documentada porque el split actual es aleatorio 70/30 y puede inflar métricas.

## Qué incluye

| Área | Qué hay |
|---|---|
| Dashboard | React + Vite + MUI + Chart.js |
| Datos | Supabase/PostgreSQL con tabla `london_crime_aggregated` |
| DataOps | BigQuery → limpieza → carga Supabase → métricas |
| ML | LogisticRegression + RandomForestRegressor |
| API | FastAPI en Render, endpoint `POST /predict` |
| CI | GitHub Actions backend: black + flake8 + pytest |
| Infra | Render Docker deploy + Docker Compose local en `infra/` |

## Arquitectura rápida

```text
BigQuery london_crime
        │
        ▼
apps/backend/cli/pipeline_dataops.py
        │
        ├── pipeline/ingestion.py
        ├── pipeline/cleaning.py
        ├── pipeline/loading.py
        └── pipeline/metrics.py
        │
        ▼
data/processed/london_crime_aggregated.csv ──→ ML pipeline → data/models/*.joblib
        │
        └── Supabase: london_crime_aggregated ──→ Frontend React/Vercel
```

## ML actual

El estimador usa dos modelos entrenados por `apps/backend/cli/ml_pipeline.py` desde `data/processed/london_crime_aggregated.csv`:

| Modelo | Archivo | Salida |
|---|---|---|
| `LogisticRegression` | `data/models/logistic_regression.joblib` | incidencia alta/baja |
| `RandomForestRegressor` | `data/models/crime_regressor.joblib` | delitos estimados |
| Preprocessor sklearn | `data/models/preprocessor.joblib` | one-hot + escalado |

Inputs del modelo: `borough`, `major_category`, `minor_category`, `year`, `month_sin`, `month_cos`.

Limitación clave: el entrenamiento usa split aleatorio, no temporal. Por eso las métricas actuales describen desempeño histórico interno, no capacidad real de predecir años futuros.

## DevOps / DataOps real

| Componente | Ruta/config real |
|---|---|
| Render | `render.yaml` (`env: docker`, `healthCheckPath: /health`) |
| Docker API | `Dockerfile` |
| Docker local | `infra/docker-compose.yml` |
| Docker backend dev | `infra/backend.Dockerfile` |
| Docker frontend | `infra/frontend.Dockerfile` + `infra/nginx.conf` |
| CI backend | `.github/workflows/ci-backend.yml` |
| Requirements | `requirements.txt` en la raíz |
| Env ejemplo | `config/.env.example` |

Variables importantes:

| Variable | Uso |
|---|---|
| `VITE_SUPABASE_URL` | Frontend |
| `VITE_SUPABASE_ANON_KEY` | Frontend |
| `VITE_ML_API_URL` | Frontend → FastAPI |
| `SUPABASE_DB_URL` | Pipeline backend/DataOps |
| `GOOGLE_APPLICATION_CREDENTIALS` | BigQuery |

## Ejecutar local

Desde la raíz del repo:

```bash
# Dependencias Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# API ML
uvicorn apps.backend.api.predict:app --reload
```

Frontend:

```bash
cd apps/frontend
npm install
npm run dev
```

Pipeline/DataOps:

```bash
# ETL demo sin BigQuery
python -m apps.backend.cli.pipeline_dataops --demo

# ETL real BigQuery → Supabase
python -m apps.backend.cli.pipeline_dataops

# Entrenar modelos ML
python -m apps.backend.cli.ml_pipeline
```

Docker local:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "borough": "westminster",
    "major_category": "theft and handling",
    "minor_category": "theft from shop",
    "year": 2016,
    "month": 6
  }'
```

Respuesta real:

```json
{
  "prediction": 1,
  "probability_high": 0.8234,
  "probability_low": 0.1766,
  "predicted_crimes": 42,
  "predicted_crimes_raw": 42.37,
  "threshold": 0.5,
  "features_used": 120
}
```

## Mejoras futuras

### Opción B — split temporal correcto

Entrenar con años antiguos y evaluar en años posteriores:

```python
train = df[df["year"] <= 2014]
test = df[df["year"] >= 2015]
```

Añadir `lag_1`, `lag_12`, rolling averages y evaluación walk-forward.

### Opción C — predicción real

Migrar a Prophet, SARIMA o LSTM para predecir 2017+ con series temporales reales por distrito/categoría.

## Documentación

- [`docs/API.md`](docs/API.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/ML_PIPELINE.md`](docs/ML_PIPELINE.md)
- [`docs/PRESENTATION.md`](docs/PRESENTATION.md)
- [`SECURITY.md`](SECURITY.md)

## Tests

```bash
PYTHONPATH=. python -m pytest apps/backend/tests/ -v
```

## Licencia

MIT
