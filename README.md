# Sistema de Inteligencia Territorial para la Seguridad Publica en Londres

[![CI Backend](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml)
[![Vercel](https://img.shields.io/badge/deploy-Vercel-black)](https://data-gestor.vercel.app/)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/react-19-61DAFB)](https://react.dev/)

**Dashboard interactivo** de criminalidad en Londres (2008-2016) con pipeline ETL desde BigQuery, almacenamiento en Supabase, y visualizacion con React + Material UI + Chart.js. Incluye un modelo de Machine Learning (Regresion Logistica) para clasificacion binaria de alta/baja incidencia delictiva.

**Demo en vivo:** [data-gestor.vercel.app](https://data-gestor.vercel.app/)

---

## Tabla de Contenidos

- [Arquitectura General](#arquitectura-general)
- [Dashboard](#dashboard)
- [Pipeline de Datos](#pipeline-de-datos)
- [Machine Learning](#machine-learning)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Inicio Rapido](#inicio-rapido)
- [Despliegue](#despliegue)
- [CI/CD](#cicd)
- [Tests](#tests)
- [Seguridad](#seguridad)
- [KPIs y Monitoreo](#kpis-y-monitoreo)

---

## Arquitectura General

```
BigQuery Public Dataset               Google Cloud
(london_crime, 3M rows)               Service Account
        |                                     |
        v                                     |
  Pipeline Python (ETL)  <-------------------+
  - 10 etapas de limpieza
  - Agregacion: 3M -> 77,524 filas
  - Validacion y deteccion de outliers
        |
        v
  Supabase (PostgreSQL)              Pipeline ML
  tabla: london_crime_aggregated      Logistic Regression
        |                             Accuracy: 89%
        |                             ROC AUC: 0.963
        v                                     |
  Frontend React (Vercel)  <------------------+
  - 77,524 filas via paginacion paralela
  - Filtros por distrito/categoria/anio
  - Charts + Heatmap + ML Insights
```

### Componentes clave

| Componente | Tecnologia | Proposito |
|---|---|---|
| **Fuente de datos** | Google BigQuery | Dataset publico `london_crime` (~3M registros crudos) |
| **Pipeline ETL** | Python (pandas, SQLAlchemy) | Ingesta, limpieza, agregacion, carga a Supabase |
| **Base de datos** | Supabase (PostgreSQL) | Almacenamiento de 77,524 registros agregados |
| **Frontend** | React 19 + Vite 8 + MUI 9 | Dashboard interactivo desplegado en Vercel |
| **Excel Export** | SheetJS (xlsx) + Material-UI Icons | Exportación de datos a Excel en 3 formatos |
| **ML** | scikit-learn (LogisticRegression) | Clasificacion binaria de criminalidad |
| **CI/CD** | GitHub Actions | Lint + tests automaticos en cada push |

### Nota sobre paginacion en Supabase

El API REST de Supabase (PostgREST) limita las respuestas a **1,000 filas por request**. El frontend maneja esto con paginacion paralela en batches:

- Primero obtiene el total de filas via `count=exact`
- Luego descarga las 77,524 filas en ~78 requests paralelos (10 concurrentes)
- Los datos se agregan en el cliente para los charts

---

## Dashboard

https://data-gestor.vercel.app/

### Vistas

| Seccion | Descripcion |
|---|---|
| **KPIs** | Total crimenes (1.3M+), distrito lider, categoria principal, registros filtrados |
| **Filtros** | Selectores de distrito (33), categoria (8), ano (2008-2016) + 3 botones de exportacion |
| **Exportacion a Excel** | Descargar datos filtrados, datos agregados (3 hojas), o dataset completo (77k+ registros) |
| **Crimenes por Distrito** | Grafico de barras con totales por borough |
| **Proporcion por Categoria** | Grafico donut con distribucion por tipo de crimen |
| **Tendencia Temporal** | Linea temporal mes a mes (96 puntos) |
| **Top 10 Subcategorias** | Barras horizontales con las subcategorias mas frecuentes |
| **Crimenes por Distrito y Ano** | Tabla heatmap (33 boroughs x 9 anos) |
| **Datos Detallados** | Tabla con los primeros 100 registros filtrados + boton de exportacion |
| **ML Insights** | Metricas del modelo, matriz de confusion, curva ROC |

### Exportacion de Datos

Se agregó funcionalidad de exportación a Excel con tres opciones:

#### 1. **Exportar Datos Filtrados** 📥
- Descarga solo los registros que coinciden con los filtros activos
- Respeta: Borough, Categoría, Año
- Columnas: Borough, Major Category, Minor Category, Year, Month, Total Crimes, Date
- Archivo: `london_crime_filtered_YYYY-MM-DD.xlsx`

#### 2. **Exportar Datos Agregados** 📊
- Descarga un Excel con 3 hojas:
  - **Crímenes por Distrito**: Totales por borough
  - **Top 10 Subcategorías**: Las 10 categorías menores más frecuentes
  - **Tendencia Temporal**: Datos mes a mes
- Archivo: `london_crime_aggregated_YYYY-MM-DD.xlsx`

#### 3. **Exportar Dataset Completo** 📦
- Descarga todos los 77,524 registros
- Ignora los filtros aplicados
- Archivo: `london_crime_complete_YYYY-MM-DD.xlsx` (~5-7 MB)

**Dependencias:**
- `xlsx` (SheetJS Community Edition) — Exportación a Excel
- `@mui/icons-material` — Icono de descarga

---

## Pipeline de Datos

### 1. Ingesta

Origen: `bigquery-public-data.london_crime.crime_by_lsoa` (Google BigQuery).
Modo produccion: hasta **3M filas**. Modo demo: **150 filas sinteticas** (Poisson, seed 42).

### 2. Limpieza (10 etapas)

| # | Etapa | Descripcion |
|---|-------|-------------|
| 1 | Estandarizar columnas | snake_case, nombres consistentes |
| 2 | Manejo de nulos | Elimina filas con nulos en columnas criticas |
| 3 | Validar tipos | `year`/`month` -> Int64, `value` -> float64 |
| 4 | Validar rangos | Mes [1,12], ano >= 2000, valor >= 0 |
| 5 | Normalizar texto | Strip, title(), correccion ortografica de boroughs |
| 6 | Eliminar duplicados | Filas identicas (todas las columnas) |
| 7 | **Agregar** | `GROUP BY (borough, major_category, minor_category, year, month)` + `SUM(value)` |
| 8 | Crear fecha | Columna `date` desde year + month |
| 9 | Detectar outliers | IQR + Z-score (solo reporte, no elimina) |
| 10 | Eliminar columnas | Conserva solo columnas relevantes |

**Reduccion**: 3M filas crudas -> **77,524 filas agregadas** (97.4%).

### 3. Carga a Supabase

```bash
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py
```

Tabla: `london_crime_aggregated` con columnas `borough, major_category, minor_category, year, month, total_crimes, date`.

---

## Machine Learning

Pipeline de clasificacion binaria con **Logistic Regression**.

**Target**: `1` si `total_crimes > mediana` (alta incidencia), `0` si no.

**Features** (6):
- `borough`, `major_category`, `minor_category` (OneHotEncoding)
- `year` (numerico)
- `month_sin`, `month_cos` (codificacion ciclica)

**Metricas** (77,524 registros, train/test 70/30):

| Metrica | Valor |
|---------|-------|
| Accuracy | 89.0% |
| Precision | 86.5% |
| Recall | 91.4% |
| F1 Score | 88.9% |
| ROC AUC | **0.9634** |
| Gini | **0.9267** |

El modelo se entrena offline y las metricas se muestran en la seccion **ML Insights** del dashboard.

```bash
docker exec london_crime_app python apps/backend/cli/ml_pipeline.py
```

---

## Estructura del Proyecto

```
DataGestor/
├── apps/
│   ├── backend/
│   │   ├── pipeline/        # ETL: ingestion, cleaning, loading, metrics
│   │   ├── ml/              # ML: preprocessing, classification
│   │   ├── cli/             # CLI: pipeline_dataops.py, ml_pipeline.py
│   │   └── tests/           # 33 tests (cleaning, loading, ml, pipeline)
│   └── frontend/
│       ├── src/App.jsx       # Dashboard principal
│       ├── public/ml/        # Artefactos ML (metricas, graficos)
│       ├── vercel.json       # Config Vercel
│       └── package.json
├── config/
│   ├── settings.py           # Config centralizada del pipeline
│   ├── .env.example          # Plantilla de variables de entorno
│   ├── boroughs.json         # 33 London boroughs
│   └── categories.json       # Categorias de crimen
├── data/
│   ├── raw/                  # Datos crudos (Parquet)
│   ├── validated/            # Datos validados
│   ├── processed/            # Datos agregados (CSV + Parquet)
│   ├── logs/                 # pipeline.log
│   ├── metrics/              # pipeline_metrics.jsonl, ml_metrics.json, *.png
│   └── models/               # logistic_regression.joblib
├── infra/
│   ├── docker-compose.yml    # Orquestacion local
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── docs/
│   └── ml_pipeline.md
├── .github/workflows/
│   └── ci-backend.yml        # GitHub Actions
├── SECURITY.md
└── requirements.txt
```

---

## Inicio Rapido

### Requisitos

- Node.js 20+
- Python 3.11+ (para pipeline local)
- Docker + Docker Compose (opcional, para stack completo)
- Cuenta de Supabase con tabla `london_crime_aggregated`

### Instalacion

```bash
# 1. Clonar
git clone https://github.com/VECTORG99/DataGestor.git
cd DataGestor

# 2. Configurar credenciales
cp config/.env.example .env
# Editar .env con tus credenciales de Supabase y GCP

cp config/.env.example apps/frontend/.env.local
# Editar con VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY

# 3. Frontend (desarrollo local)
cd apps/frontend
npm install
npm run dev
# Abrir http://localhost:5173
# Los botones de exportacion a Excel estarán disponibles en:
#   - Seccion de filtros (3 opciones)
#   - Seccion de Datos Detallados (exportar filtrados)

# 4. Pipeline ETL (via Docker)
cd ../..
docker compose -f infra/docker-compose.yml up --build -d
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py
```

---

## Despliegue

### Vercel (produccion)

El frontend se despliega en Vercel con integracion Git:

1. Conecta el repo `VECTORG99/DataGestor` en [vercel.com](https://vercel.com)
2. Rama: `master`
3. Framework: Vite
4. Variables de entorno requeridas:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_SUPABASE_TABLE_NAME` (opcional, default: `london_crime_aggregated`)

Cada push a `master` depliega automaticamente.

---

## CI/CD

| Workflow | Archivo | Disparo |
|---|---|---|
| Backend CI | `.github/workflows/ci-backend.yml` | Push/PR a `master` |

Ejecuta:
- `black --check apps/backend/` (formato)
- `flake8 apps/backend/` (lint)
- `python -m pytest apps/backend/tests/ -v` (tests)

---

## Tests

33 tests que cubren el pipeline ETL y ML:

| Archivo | Cobertura | Tests |
|---------|-----------|-------|
| `tests/test_cleaning.py` | Estandarizacion, nulos, tipos, rangos, texto, duplicados, fecha, outliers | 21 |
| `tests/test_loading.py` | Guardado CSV + Parquet | 2 |
| `tests/test_ml.py` | Preprocessing, clasificacion | 7 |
| `tests/test_pipeline_dataops.py` | Importacion, entorno | 2 |

```bash
# Local
PYTHONPATH=. python -m pytest apps/backend/tests/ -v

# Docker
docker exec london_crime_app python -m pytest apps/backend/tests/ -v
```

---

## Seguridad

Ver [`SECURITY.md`](SECURITY.md) para el plan completo.

**Resumen:**
- **GDPR + Ley 19.628** (Chile): datos anonimos y agregados, sin PII
- **TLS 1.3** en todas las conexiones externas
- **AES-256** en reposo (Supabase, BigQuery)
- **RLS en Supabase**: `anon_key` solo lectura, `service_role` escritura
- **Secretos**: `.env`, `credentials.json`, `*.local` en `.gitignore`

---

## KPIs y Monitoreo

El pipeline registra metricas de cada ejecucion:

| KPI | Descripcion | Ejemplo |
|-----|-------------|---------|
| Latencia | Duracion por etapa | `limpieza: 6.85s` |
| Volumen | Reduction 3M -> 77k | `97.4%` |
| Completitud | % datos no nulos | `100.0%` |
| Outliers | Valores atipicos (IQR) | `11,133` |

Persistido en `data/metrics/pipeline_metrics.jsonl` (una linea por ejecucion).

```bash
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py --demo
# RESUMEN DE KPIs - PIPELINE DATAOPS
#   Duracion total:  7.27 seg
#   Registros:        150 -> 146 (2.7% reduccion)
#   Completitud:      100.0%
```

---

## Licencia

Proyecto academico — Duoc UC.
