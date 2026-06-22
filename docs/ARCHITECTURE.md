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
│  │              │  (JS SDK)   │      │  (fetch /fetch)  │      │   │
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
│  PIPELINE ETL (Local)           │   │  │ │ │ Regressor  │  │  │  │
│  ┌────────────────────────────┐  │   │  │ │ ├────────────┤  │  │  │
│  │ BigQuery → Clean →        │  │   │  │ │ │ Encoders   │  │  │  │
│  │ Aggregate → Supabase       │  │   │  │ │ └────────────┘  │  │  │
│  │ → Train ML                 │  │   │  │ └─────────────────┘  │  │
│  └────────────────────────────┘  │   │  └───────────────────────┘  │
└──────────────────────────────────┘   └──────────────────────────────┘
```

## Flujo de Datos

### 1. ETL (Local → Supabase)

```
BigQuery (3M LSOA records)
   │
   ▼  google-cloud-bigquery client
Raw Data (~3M filas)
   │
   ▼  apps/backend/scripts/etl_pipeline.py
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
   ▼  upsert a Supabase
Supabase (london_crime_aggregated)
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
  ├── Carga modelos .pkl al iniciar
  ├── One-hot encode de features
  ├── LogisticRegression → prediction + probabilities
  ├── RandomForestRegressor → predicted_crimes
  └── Response JSON → UI
```

## Stack por Capa

| Capa | Tecnología | Versión |
|------|-----------|---------|
| Frontend | React + Vite | React 18, Vite 5 |
| UI | MUI (Material-UI) | v5 |
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
- **Modelos:** Archivos .pkl incluidos en el repo (contienen coeficientes entrenados — sin datos de entrenamiento).

## Consideraciones de Escalabilidad

- **Frontend:** Vercel escala automáticamente (estático + edge).
- **API ML:** Render Free Tier se duerme tras 15 min de inactividad. Primer request tras inactividad tarda ~30s (cold start). Upgrade a Starter ($7/mes) elimina esto.
- **Base de datos:** Supabase Free Tier (500 MB, 100 conexiones simultáneas). Suficiente para ~23K filas.
- **ML:** Modelos en memoria (~50MB cada uno). Una instancia Render Free (512MB RAM) es suficiente.
