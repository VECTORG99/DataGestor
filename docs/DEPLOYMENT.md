# Despliegue — London Crime Data Platform

## Arquitectura de Despliegue

```
[GitHub] ──push──→ [GitHub Actions]
                        │
                        └── ci-backend.yml: black + flake8 + pytest
                        │
                        ▼
                  [Vercel] auto-deploy desde main
                  [Render] auto-deploy desde main
```

| Componente | Plataforma | URL | Build |
|-----------|-----------|-----|-------|
| Frontend (React) | Vercel | `https://london-crime-dashboard.vercel.app` | `npm run build` → `dist/` |
| Backend ML API | Render | `https://london-crime-api.onrender.com` | `uvicorn api.predict:app` |
| Base de Datos | Supabase | (cloud) | Pre-cargada |

No hay despliegue automático por GitHub Actions. Vercel y Render detectan cambios en `main` mediante sus integraciones nativas.

---

## Frontend — Vercel

### Configuración
- **Root directory:** `apps/frontend/`
- **Build command:** `npm run build`
- **Output directory:** `dist/`
- **Node version:** 18.x

### Variables de Entorno (Vercel dashboard)
```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx
VITE_ML_API_URL=https://london-crime-api.onrender.com
```

### Despliegue manual
```bash
cd apps/frontend
npx vercel --prod
```

---

## Backend ML API — Render

### Configuración
- **Type:** Web Service
- **Root directory:** `apps/backend/`
- **Runtime:** Python 3.11
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn api.predict:app --host 0.0.0.0 --port $PORT`

### Variables de Entorno (Render dashboard)
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJxxx
PYTHON_VERSION=3.11.0
```

### Health Check
Render puede configurar un health check en `GET /health`:
```json
{"status": "ok", "model_loaded": true}
```

---

## Base de Datos — Supabase

### Tabla: `london_crime_aggregated`
```sql
CREATE TABLE london_crime_aggregated (
  id SERIAL PRIMARY KEY,
  borough VARCHAR(100),
  major_category VARCHAR(100),
  minor_category VARCHAR(100),
  year INTEGER,
  month INTEGER,
  total_crimes INTEGER,
  date DATE
);

CREATE INDEX idx_london_crime_aggregated_borough ON london_crime_aggregated(borough);
CREATE INDEX idx_london_crime_aggregated_year ON london_crime_aggregated(year);
```

Los datos se cargan mediante el pipeline ETL con upsert. El dataset completo tiene ~23,000 registros agregados.

---

## CI/CD — GitHub Actions

### `ci-backend.yml` (único workflow)
```yaml
name: CI Backend
on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
jobs:
  test-lint-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install 'black>=25.0,<26' flake8
          pip install -r apps/backend/requirements.txt
      - name: Black format check
        run: black --check apps/backend/
      - name: Flake8 lint
        run: flake8 apps/backend/ --max-line-length=100 --exclude=.venv,__pycache__
      - name: Pytest
        run: python -m pytest apps/backend/tests/ -v
        env:
          SUPABASE_DB_URL: dummy
          GOOGLE_APPLICATION_CREDENTIALS: dummy
```

**Nota:** El CI solo cubre el backend. No hay workflow de frontend — Vercel hace build propio al desplegar.

### Secrets requeridos en GitHub
Los tests usan valores dummy (`SUPABASE_DB_URL: dummy`, `GOOGLE_APPLICATION_CREDENTIALS: dummy`) y solo prueban lógica sin conexión real a BD. No se requieren secrets reales para CI.

---

## Pipeline ETL

El pipeline ETL se ejecuta **localmente** (no en producción):

```bash
cd apps/backend

# ETL completo (BigQuery → limpia → Supabase)
python -m apps.backend.cli.pipeline_dataops

# Modo demo (datos sintéticos, sin BigQuery)
python -m apps.backend.cli.pipeline_dataops --demo

# Solo ML (entrenar modelos desde Supabase)
python -m apps.backend.cli.ml_pipeline
```

### Requisitos del pipeline ETL
1. Credenciales GCP (`google-cloud-bigquery`) — archivo JSON de service account (solo para modo no-demo).
2. Credenciales Supabase — variables de entorno `SUPABASE_URL` y `SUPABASE_KEY`.
3. Dataset público `bigquery-public-data.london_crime.crime_by_lsoa` en BigQuery.

### Flujo ETL (detalle por módulo)
```
apps/backend/pipeline/ingestion.py
    BigQuery → ~3M filas LSOA
        │
        ▼
apps/backend/pipeline/cleaning.py  (clean_and_transform_data)
    ├── standardize_column_names()   → snake_case
    ├── handle_null_values()         → elimina filas con nulos críticos
    ├── validate_data_types()        → int64, float64, string
    ├── validate_value_ranges()      → meses 1-12, años 2008-2016
    ├── normalize_text_fields()      → title case, corrige boroughs
    ├── detect_and_remove_duplicates() → exactos + subset
    ├── create_date_column()         → year+month → date
    └── detect_outliers()            → IQR (solo reporta, no elimina)
        │
        ▼
apps/backend/pipeline/loading.py
    ├── save_clean_data()            → CSV + Parquet local
    └── load_to_supabase()           → upsert a Supabase
        │
        ▼
apps/backend/cli/ml_pipeline.py
    ├── apps/backend/ml/preprocessing.py  → features + preprocessor
    ├── apps/backend/ml/classification.py → LogisticRegression + RandomForestRegressor
    └── data/models/*.joblib              → modelos serializados
```

## Nota sobre contenedores

El proyecto no usa Docker ni docker-compose. El frontend se despliega en Vercel (serverless) y el backend como servicio web en Render. Para desarrollo local, se ejecutan directamente con `npm run dev` y `uvicorn`.
