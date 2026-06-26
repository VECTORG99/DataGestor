# London Crime Data Platform

> **Dashboard analítico + estimador histórico de criminalidad para Londres (2008-2016).**  
> No es un predictor del futuro. Es un sistema de análisis que estima perfiles históricos de crimen basados en datos reales.

---

## ¿Qué hace este proyecto?

Procesa ~3 millones de registros de crimen a nivel LSOA del dataset público de la Policía Metropolitana de Londres y los transforma en:

1. **Dashboard interactivo** — visualizaciones por distrito, categoría, tendencia temporal, exportación a Excel.
2. **Pipeline DataOps/ETL** — extracción desde BigQuery, limpieza, validación, agregación, snapshots, métricas y carga a Supabase.
3. **Estimador ML histórico** — dado un distrito, categoría, mes y año, estima cuántos crímenes cabría esperar según el perfil histórico aprendido.

**Importante:** Este sistema **NO predice el futuro**. El modelo ML actual se entrena con un split aleatorio 70/30 sobre datos históricos, lo que puede introducir fuga temporal e inflar métricas. Para predicción real, ver [Opciones de evolución](#opciones-de-evolución).

---

## Stack tecnológico

| Capa | Tecnología | Configuración real |
|---|---|---|
| Frontend | React + Vite + MUI + Chart.js | `apps/frontend`, deploy en Vercel |
| Backend API | FastAPI + Uvicorn | `apps/backend/api/predict.py`, deploy en Render |
| Base de datos | Supabase/PostgreSQL | tabla `london_crime_aggregated` |
| DataOps | Python + pandas + BigQuery + SQLAlchemy | `apps/backend/cli/pipeline_dataops.py` |
| ML | scikit-learn | `apps/backend/cli/ml_pipeline.py` |
| Modelos | joblib | `data/models/*.joblib` |
| CI | GitHub Actions | `ci-backend.yml` (lint+test), `etl-pipeline.yml` (ETL+ML automático), `ml-training.yml` (retrain standalone) |
| Infra | Docker + Compose + nginx | `Dockerfile`, `render.yaml`, `infra/` |

---

## Arquitectura general

```text
BigQuery: bigquery-public-data.london_crime.crime_by_lsoa
        │
        ▼
apps/backend/cli/pipeline_dataops.py
        │
        ├── pipeline/ingestion.py
        ├── pipeline/cleaning.py
        ├── pipeline/loading.py
        ├── pipeline/data_stage_manager.py
        └── pipeline/metrics.py
        │
        ├── data/processed/london_crime_aggregated.csv
        ├── Supabase: london_crime_aggregated
        └── data/metrics/pipeline_metrics.jsonl
                │
                ▼
apps/backend/cli/ml_pipeline.py
        │
        ├── data/models/logistic_regression.joblib
        ├── data/models/crime_regressor.joblib
        └── data/models/preprocessor.joblib
                │
                ▼
apps/backend/api/predict.py  ──→  Frontend React/Vercel
```

---

## ML — Estimador histórico

### Qué hace realmente

El modelo aprende el perfil histórico del dataset 2008-2016. Con los inputs `borough`, `major_category`, `minor_category`, `year` y `month`, devuelve:

- clasificación de incidencia alta/baja;
- probabilidad de alta/baja;
- estimación numérica de crímenes mensuales.

No extrapola de forma confiable fuera del rango histórico.

### Archivos ML reales

| Archivo | Rol |
|---|---|
| `apps/backend/cli/ml_pipeline.py` | Orquesta entrenamiento y guardado de modelos |
| `apps/backend/ml/preprocessing.py` | Carga CSV procesado, crea target y preprocessor sklearn |
| `apps/backend/ml/classification.py` | Entrena/evalúa LogisticRegression y RandomForestRegressor |
| `apps/backend/api/predict.py` | Carga modelos y sirve `POST /predict` |
| `data/models/logistic_regression.joblib` | Clasificador alta/baja |
| `data/models/crime_regressor.joblib` | Regresor de número de crímenes |
| `data/models/preprocessor.joblib` | Transformación de features para inferencia |

### Modelo de clasificación

- **Algoritmo:** `LogisticRegression`
- **Objetivo:** clasificar incidencia alta (`1`) o baja (`0`).
- **Target:** `target_binary = total_crimes > median(total_crimes)`.
- **Features:** `borough`, `major_category`, `minor_category`, `year`, `month_sin`, `month_cos`.
- **Limitación:** split aleatorio 70/30, no split temporal.

### Modelo de regresión

- **Algoritmo:** `RandomForestRegressor`
- **Objetivo:** estimar `predicted_crimes`.
- **Mismas features** que el clasificador.
- **Salida API:** `predicted_crimes` redondeado y `predicted_crimes_raw` sin redondear.

### Limitación fundamental

```python
# Simplificado: split aleatorio, no temporal
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
```

Esto significa que el modelo puede evaluar datos antiguos habiendo aprendido patrones de años posteriores. Las métricas describen desempeño histórico interno, no predicción futura real.

---

## DataOps / ETL

### Entrypoint

```bash
python -m apps.backend.cli.pipeline_dataops
```

### Modo demo

```bash
python -m apps.backend.cli.pipeline_dataops --demo
```

### Flujo DataOps

| Etapa | Módulo | Qué hace |
|---|---|---|
| Ingesta | `pipeline/ingestion.py` | Lee BigQuery o genera muestra demo |
| Limpieza | `pipeline/cleaning.py` | Estandariza columnas, valida tipos/rangos, elimina nulos/duplicados, normaliza texto |
| Validación | `pipeline/data_stage_manager.py` | Guarda snapshots y reportes por etapa |
| Persistencia local | `pipeline/loading.py` | Guarda CSV/Parquet en `data/processed/` |
| Carga Supabase | `pipeline/loading.py` | `load_to_supabase()` usa `SUPABASE_DB_URL` |
| Métricas | `pipeline/metrics.py` | Exporta `pipeline_metrics.jsonl` |

### Variables DataOps

| Variable | Uso |
|---|---|
| `SUPABASE_DB_URL` | Conexión PostgreSQL/Supabase para carga de datos |
| `GOOGLE_APPLICATION_CREDENTIALS` | Credenciales GCP para BigQuery |
| `BIGQUERY_ROW_LIMIT` | Límite de registros a leer |
| `SUPABASE_TABLE_NAME` | Tabla destino, por defecto `london_crime_aggregated` |

> El ETL también corre automáticamente cada mes via GitHub Actions (`etl-pipeline.yml`), usando `GCP_SERVICE_ACCOUNT_JSON` y `SUPABASE_DB_URL` como secrets del repositorio.

---

## DevOps / CI/CD

### Render

Render usa `render.yaml`:

```yaml
services:
  - type: web
    name: datagestor-ml-api
    env: docker
    healthCheckPath: /health
```

La imagen de producción se construye con el `Dockerfile` de la raíz. Ese Dockerfile instala `requirements.txt`, copia el proyecto, descarga modelos pre-entrenados del release `ml-models-latest` (con fallback a entrenamiento en build), y levanta:

```bash
uvicorn apps.backend.api.predict:app --host 0.0.0.0 --port 8000
```

### Vercel

Frontend React/Vite desde `apps/frontend`:

```bash
npm install
npm run build
```

Variables frontend:

| Variable | Uso |
|---|---|
| `VITE_SUPABASE_URL` | URL pública de Supabase |
| `VITE_SUPABASE_ANON_KEY` | anon key de Supabase |
| `VITE_ML_API_URL` | URL de FastAPI/Render |

### GitHub Actions

Tres workflows:

| Workflow | Trigger | Qué hace |
|----------|---------|----------|
| `ci-backend.yml` | push/PR a `main` | lint + test backend |
| `etl-pipeline.yml` | 1ro de cada mes + manual | ETL (BigQuery → Supabase), genera JSONs frontend, entrena ML con datos frescos, sube modelos a release |
| `ml-training.yml` | cada 3 días + manual | Retrain standalone con CSV commiteado, actualiza métricas, sube modelos |

**`ci-backend.yml`** — lint + test en push/PR:

```yaml
# Python 3.11 → pip install → black --check → flake8 → pytest
```

**`etl-pipeline.yml`** — ETL + ML automatizado:
```
Job 1 (etl):
  BigQuery → clean → Supabase → frontend JSONs
  └── sube CSV procesado como artifact
Job 2 (ml-training, depende de etl):
  descarga artifact → entrena modelos → commitea ml_metrics.json
  └── sube .joblib a release ml-models-latest
```

**`ml-training.yml`** — standalone (usa el CSV ya commiteado):
```
checkout → entrena → commitea métricas → sube modelos a ml-models-latest
```

**Secrets requeridos en GitHub:**

| Secret | Uso |
|--------|-----|
| `GCP_SERVICE_ACCOUNT_JSON` | Credenciales BigQuery para ETL (solo `etl-pipeline.yml`) |
| `SUPABASE_DB_URL` | Conexión a Supabase para carga de datos |

### Docker local

| Archivo | Uso |
|---|---|
| `Dockerfile` | Producción API en Render |
| `infra/docker-compose.yml` | Backend + frontend local |
| `infra/backend.Dockerfile` | Contenedor backend/dev |
| `infra/frontend.Dockerfile` | Build React + nginx |
| `infra/nginx.conf` | SPA fallback + gzip + headers básicos |

```bash
docker compose -f infra/docker-compose.yml up --build
```

---

## API

### Health

```http
GET /health
```

Respuesta real:

```json
{"status": "ok"}
```

### Estimación

```http
POST /predict
```

Request:

```json
{
  "borough": "westminster",
  "major_category": "theft and handling",
  "minor_category": "theft from shop",
  "year": 2016,
  "month": 6
}
```

Response:

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

---

## Ejecutar localmente

### Backend/API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn apps.backend.api.predict:app --reload
```

### Frontend

```bash
cd apps/frontend
npm install
npm run dev
```

### Pipeline y ML

```bash
# Desde la raíz del repo
python -m apps.backend.cli.pipeline_dataops --demo
python -m apps.backend.cli.pipeline_dataops
python -m apps.backend.cli.ml_pipeline
```

---

## Estructura del proyecto

```text
DataGestor/
├── apps/
│   ├── frontend/                 # React + Vite
│   │   ├── src/App.jsx           # Dashboard + estimador
│   │   └── public/               # métricas/logs para dashboard
│   └── backend/
│       ├── api/predict.py        # FastAPI /health y /predict
│       ├── cli/                  # entrypoints DataOps/ML
│       ├── pipeline/             # ingestion, cleaning, loading, metrics
│       ├── ml/                   # preprocessing + modelos sklearn
│       └── tests/                # pytest
├── config/.env.example           # variables ejemplo
├── data/
│   ├── processed/                # CSV/Parquet procesados
│   ├── metrics/                  # métricas DataOps/ML
│   └── models/                   # modelos joblib
├── infra/                        # Docker Compose, Dockerfiles dev, nginx
├── .github/workflows/ci-backend.yml
├── .github/workflows/etl-pipeline.yml
├── .github/workflows/ml-training.yml
├── render.yaml
├── Dockerfile
├── requirements.txt
├── docs/
└── README.md
```

---

## Opciones de evolución

### Opción A — actual

Mantener el estimador histórico, documentando que no predice futuro.

### Opción B — split temporal correcto

Cambiar evaluación a entrenamiento histórico y test futuro:

```python
train = df[df["year"] <= 2014]
test = df[df["year"] >= 2015]
```

Añadir `lag_1`, `lag_12`, rolling averages y walk-forward validation.

### Opción C — predicción real

Migrar a Prophet, SARIMA o LSTM para series temporales y predicción 2017+ por distrito/categoría.

---

## Documentación

- [`docs/API.md`](docs/API.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`docs/ML_PIPELINE.md`](docs/ML_PIPELINE.md)
- [`docs/PRESENTATION.md`](docs/PRESENTATION.md)
- [`SECURITY.md`](SECURITY.md)

---

## Tests

```bash
PYTHONPATH=. python -m pytest apps/backend/tests/ -v
```

---

## Licencia

MIT
