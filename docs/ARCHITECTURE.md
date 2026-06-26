# Arquitectura — London Crime Data Platform

## Diagrama General

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  React + Vite + MUI + Chart.js                              │   │
│  │                                                              │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────┐      │   │
│  │  │Dashboard │  │  Filtros     │  │ Estimador        │      │   │
│  │  │Visual    │  │  (borough,   │  │ Histórico        │      │   │
│  │  │(charts)  │  │   category,  │  │ (ML POST)        │      │   │
│  │  │          │  │   year)      │  │                  │      │   │
│  │  └──────────┘  └──────┬───────┘  └────────┬─────────┘      │   │
│  │                       │                    │                │   │
│  │              ┌────────▼────┐      ┌────────▼────────┐      │   │
│  │              │  Supabase   │      │  ML API URL     │      │   │
│  │              │  (JS SDK)   │      │  (fetch /predict)│      │   │
│  │              └─────────────┘      └─────────────────┘      │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │                    │
                              ▼                    ▼
┌──────────────────────────────────┐   ┌──────────────────────────────┐
│     SUPABASE (PostgreSQL)        │   │  BACKEND ML API (Render)    │
│  ┌────────────────────────────┐  │   │  ┌───────────────────────┐  │
│  │ london_crime_aggregated   │  │   │  │ FastAPI               │  │
│  │ ┌──────────────────────┐  │  │   │  │ ┌─────────────────┐  │  │
│  │ │ borough: varchar    │  │  │   │  │ │ POST /predict   │  │  │
│  │ │ major_category      │  │  │   │  │ └────────┬────────┘  │  │
│  │ │ minor_category      │  │  │   │  │          │           │  │
│  │ │ year: int           │  │  │   │  │ ┌────────▼────────┐  │  │
│  │ │ month: int          │  │  │   │  │ │ ML Models       │  │  │
│  │ │ total_crimes: int   │  │  │   │  │ │ (scikit-learn)  │  │  │
│  │ │ date: date          │  │  │   │  │ │ ┌────────────┐  │  │  │
│  │ └──────────────────────┘  │  │   │  │ │ │ Logistic   │  │  │  │
│  └────────────────────────────┘  │   │  │ │ │ Regression │  │  │  │
└──────────────────────────────────┘   │  │ │ ├────────────┤  │  │  │
                                       │  │ │ │ Random     │  │  │  │
┌──────────────────────────────────┐   │  │ │ │ Forest     │  │  │  │
│  PIPELINE ETL (GitHub Actions)    │   │  │ │ │ Regressor  │  │  │  │
│  ┌────────────────────────────┐  │   │  │ │ ├────────────┤  │  │  │
│  │ etl-pipeline.yml (mensual) │  │   │  │ │ │ Encoders   │  │  │  │
│  │  BigQuery → Supabase       │  │   │  │ │ └────────────┘  │  │  │
│  │  + frontend JSONs + commit │  │   │  │ └─────────────────┘  │  │
│  └──────────┬─────────────────┘  │   │  └───────────────────────┘  │
│             ▼                    │   │                              │
│  ┌────────────────────────────┐  │   │                              │
│  │ ml-training.yml (job ML)   │  │   │                              │
│  │  Train → commit métricas   │  │   │                              │
│  │  └── release ml-models     │  │   │                              │
│  └────────────────────────────┘  │   │                              │
└──────────────────────────────────┘   └──────────────────────────────┘
```

## Flujo de Datos

### 1. ETL (GitHub Actions → Supabase)

> El pipeline ETL corre **automáticamente** cada mes via GitHub Actions (`etl-pipeline.yml`). También puede ejecutarse localmente con `python -m apps.backend.cli.pipeline_dataops`.

```
BigQuery (3M LSOA records)
   │
   ▼  google-cloud-bigquery client (GCP service account desde secret)
Raw Data (~3M filas)
   │
   ▼  apps/backend/cli/pipeline_dataops.py
Limpieza:
  ├── Eliminar nulos → ~200K eliminados
  ├── Meses inválidos (0 o >12) → ~5K
  ├── Años fuera de rango (≠2008-2016) → ~50K
  ├── Valores negativos → ~2K
  ├── Duplicados → ~10K
  └── Normalizar mayúsculas
   │
   ▼  GROUP BY (borough, major_category, minor_category, year, month)
Agregación (~23K filas agregadas)
   │
   ├── save CSV/Parquet en data/processed/
   └── upsert a Supabase (london_crime_aggregated)
```

### 2. Frontend → Datos (lectura)

```
Browser → Supabase JS SDK → SELECT * FROM london_crime_aggregated
  ├── Paginación automática (1000 rows/page)
  ├── Retry en rate limits (3 intentos)
  └── Datos cacheados en React state

Filtros (client-side):
  borough, major_category, year → filter(), reduce()
```

### 3. Frontend → ML API (estimación)

```
Browser → fetch(ML_API_URL + /predict) → FastAPI en Render
  ├── Carga modelos .joblib al iniciar (data/models/)
  ├── One-hot encode de features
  ├── LogisticRegression → prediction + probabilities
  ├── RandomForestRegressor → predicted_crimes
  └── Response JSON → UI
```

## CI/CD Automation

El proyecto tiene **tres workflows** en GitHub Actions:

```
.github/workflows/
├── ci-backend.yml         # lint + test en push/PR
├── etl-pipeline.yml       # ETL mensual + ML training encadenado
└── ml-training.yml        # retrain standalone cada 3 días
```

**Flujo ETL + ML (etl-pipeline.yml):**
```
Schedule (1ro de mes) → Job ETL → BigQuery → Clean → Supabase
                                  → frontend JSONs → commit
                                  └── CSV artifact ──→ Job ML Training
                                                         → train models
                                                         → commit ml_metrics.json
                                                         └── release ml-models-latest
```

**Flujo standalone (ml-training.yml):**
```
Schedule (cada 3 días) → checkout → train → commit metrics → release models
```

**Render deploy:** el Dockerfile descarga los `.joblib` del release `ml-models-latest` en vez de entrenar en cada build. Si el release no existe, entrena en build time como fallback.

## Stack por Capa

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React + Vite | Vite 8 |
| UI | MUI (Material-UI) | v9 |
| Charts | Chart.js + react-chartjs-2 | v4 |
| Backend | FastAPI | Python 3.11 |
| ML | scikit-learn | 1.3+ |
| DB | Supabase (PostgreSQL) | Hosted |
| ETL | pandas, numpy, google-cloud-bigquery | |
| CI | GitHub Actions | |
| Deploy | Vercel (FE) + Render (BE) | |

## Seguridad

- **CORS:** La API ML tiene `allow_origins=["*"]` (abierto — aceptable para un proyecto demo con datos públicos no sensibles).
- **Autenticación:** Supabase usa anon key del lado del cliente con Row Level Security (RLS) si está configurado.
- **Secretos:** Variables de entorno en Vercel / Render / GitHub Secrets. No hay secretos en el código.
- **Modelos:** Archivos .joblib en `data/models/` (regenerables localmente).

## Consideraciones de Escalabilidad

- **Frontend:** Vercel escala automáticamente (estático + edge).
- **API ML:** Render Free Tier se duerme tras 15 min de inactividad. Primer request tras inactividad tarda ~30s (cold start). Upgrade a Starter ($7/mes) elimina esto.
- **Base de datos:** Supabase Free Tier (500 MB, 100 conexiones simultáneas). Suficiente para ~23K filas.
- **ML:** Modelos en memoria (~50MB cada uno). Una instancia Render Free (512MB RAM) es suficiente.
