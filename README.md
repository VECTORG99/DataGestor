# London Crime Data Platform

> **Dashboard analítico + estimador histórico de criminalidad para Londres (2008-2016).**  
> No es un predictor del futuro. Es un sistema de análisis que estima perfiles históricos de crimen basados en datos reales.

---

## ¿Qué hace este proyecto?

Procesa ~3 millones de registros de crimen a nivel LSOA del dataset público de la Policía Metropolitana de Londres y los transforma en:

1. **Dashboard interactivo** — visualizaciones por distrito, categoría, tendencia temporal, exportación a Excel.
2. **Pipeline ETL** — extracción desde BigQuery, limpieza (nulos, duplicados, valores inválidos), agregación por (borough, major_category, minor_category, year, month).
3. **Estimador ML histórico** — dado un distrito, categoría, mes y año, estima cuántos crímenes cabría esperar según el perfil histórico aprendido.

**Importante:** Este sistema NO predice el futuro. El modelo ML se entrena con un split aleatorio 70/30 de datos históricos (2008-2016), lo que introduce fuga temporal — aprende de datos "futuros" para estimar datos "pasados". Las métricas reportadas (~89% accuracy, R²~0.94) están infladas artificialmente por esta fuga. Para predicción real, consulta las Opciones B y C en la sección de ML.

---

## Stack Tecnológico

| Capa | Tecnología | Despliegue |
|------|-----------|-----------|
| Frontend | React + Vite + MUI + Chart.js | Vercel |
| Backend API | FastAPI (Python) | Render |
| Base de datos | Supabase (PostgreSQL) | Supabase Cloud |
| ML | scikit-learn (LogisticRegression + RandomForestRegressor) | Render (mismo servicio) |
| ETL | Python (google-cloud-bigquery, pandas, numpy) | Local → CLI |
| CI/CD | GitHub Actions | `ci-backend.yml` (lint + test) |

---

## ML — Estimador Histórico

### ¿Qué hace realmente el modelo?

**No predice el futuro.** El modelo aprende el perfil histórico de criminalidad del dataset (2008-2016) y, dados los inputs (borough, major_category, minor_category, year, month), **estima el valor que estadísticamente corresponde** según el patrón aprendido.

### Arquitectura del ML

```
apps/backend/
├── cli/
│   ├── ml_pipeline.py       ← Entrenamiento ML (carga Supabase, entrena, guarda modelos)
│   └── pipeline_dataops.py  ← ETL completo (BigQuery → limpia → agrega → Supabase → ML)
├── pipeline/
│   ├── ingestion.py         ← Lectura desde BigQuery
│   ├── cleaning.py          ← Limpieza y transformación
│   ├── loading.py           ← Carga a Supabase + archivos locales
│   ├── data_stage_manager.py ← Snapshots por etapa
│   └── metrics.py           ← Colección de métricas del pipeline
├── ml/
│   ├── classification.py    ← LogisticRegression (alta/baja)
│   ├── preprocessing.py     ← Feature engineering + pipeline sklearn
│   └── ...
├── api/
│   └── predict.py           ← Endpoint FastAPI /predict (carga modelos y sirve)
└── data/models/
    ├── logistic_regression.joblib    ← LogisticRegression (~1KB)
    ├── crime_regressor.joblib        ← RandomForestRegressor (~79MB)
    └── preprocessor.joblib           ← Pipeline de preprocesamiento
```

### Modelo de Clasificación (LogisticRegression)

- **Objetivo:** Clasificar un caso como "alta incidencia" (1) o "baja incidencia" (0).
- **Threshold:** La mediana global de `total_crimes` en el dataset — **3 crímenes por mes**.
- **Features:** borough, major_category, minor_category, year, month (one-hot encoded, ~120 dimensiones).
- **Split:** Aleatorio 70/30. Esto causa **fuga temporal**: datos de 2015 pueden estar en train y datos de 2009 en test.

| Métrica | Valor |
|---------|-------|
| Accuracy | ~89% |
| Precision | ~85% |
| Recall | ~86% |
| F1 Score | ~85% |
| ROC AUC | ~0.94 |
| Gini | ~0.89 |

### Modelo de Regresión (RandomForestRegressor)

- **Objetivo:** Estimar el número exacto de crímenes (`predicted_crimes`).
- **Mismas features** que el clasificador.
- **Mismo split aleatorio** con fuga temporal.

| Métrica | Valor |
|---------|-------|
| R² | ~0.94 |
| MAE | ~4.37 |
| RMSE | ~11.89 |
| Mediana error | ~2.05 |

### Limitación Fundamental

```python
# apps/backend/cli/ml_pipeline.py (simplificado)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
# ↑ NO respeta el orden temporal. Datos de 2015-2016 aparecen en train,
#   y datos de 2008-2009 aparecen en test.
```

Esto significa que el modelo:
- Aprende patrones de años recientes para "estimar" años tempranos.
- Reporta métricas artificialmente altas (en un escenario real de predecir 2016 entrenando con 2008-2015, accuracy caería significativamente).
- NO es adecuado para predecir criminalidad futura fuera del rango del dataset.

**¿Por qué se hizo así?** Era un MVP técnico para demostrar el pipeline completo. La fuga temporal es conocida y documentada.

---

## DevOps / CI/CD

### Arquitectura de Despliegue

```
[GitHub] → push a main
    ↓
[GitHub Actions]
    └── ci-backend.yml   → black + flake8 + pytest (backend)
    ↓
[Vercel]                          [Render]                     [Supabase]
 ┌──────────────┐               ┌──────────────┐              ┌──────────┐
 │ React + Vite │  ←───────→   │ FastAPI ML   │  ←───────→   │ Postgres │
 │  (frontend)  │  /predict    │  (backend)   │              │ (datos)  │
 └──────────────┘               └──────────────┘              └──────────┘
```

### Frontend — Vercel
- Framework: Vite + React
- Build: `npm run build` → `dist/`
- Variables de entorno: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_ML_API_URL`
- Despliegue automático desde `apps/frontend/`

### Backend ML API — Render
- Servicio Web desde `apps/backend/`
- Comando: `uvicorn api.predict:app --host 0.0.0.0 --port $PORT`
- Variables de entorno: `SUPABASE_URL`, `SUPABASE_KEY`, `PYTHON_VERSION=3.11`
- Los modelos ML (`.joblib`) se generan localmente y se guardan en `apps/backend/data/models/` (incluidos en `.gitignore` — regenerar localmente tras cambios)

### Base de Datos — Supabase
- Tabla: `london_crime_aggregated`
- Columnas: borough, major_category, minor_category, year, month, total_crimes, date
- Datos precargados (2008-2016)

### CI/CD — GitHub Actions
- `.github/workflows/ci-backend.yml`: Corre `black --check`, `flake8` y `pytest` en el backend con cada push/PR a main/master.
- **No hay CI para frontend** — solo Vercel build automático desde la rama main.
- **No hay despliegue automático por Actions** — Vercel y Render detectan cambios en `main` por sí mismos.

### Pipeline ETL + ML

```bash
# ETL completo: BigQuery → limpia → agrega → Supabase
python -m apps.backend.cli.pipeline_dataops

# Modo demo (sin BigQuery, usa datos de muestra)
python -m apps.backend.cli.pipeline_dataops --demo

# Solo ML (entrenar modelos desde Supabase)
python -m apps.backend.cli.ml_pipeline
```

<details>
<summary><strong>Detalle del ETL (DataOps)</strong></summary>

**Módulos** en `apps/backend/pipeline/`:

| Módulo | Archivo | Responsabilidad |
|--------|---------|---------------|
| Ingestion | `pipeline/ingestion.py` | Lee ~3M registros desde BigQuery o genera datos de muestra en modo demo |
| Cleaning | `pipeline/cleaning.py` | Estandariza columnas, elimina nulos, valida tipos y rangos, normaliza texto, elimina duplicados, detecta outliers |
| Loading | `pipeline/loading.py` | Guarda datos limpios como CSV/Parquet local y hace upsert a Supabase |
| Stage Manager | `pipeline/data_stage_manager.py` | Guarda snapshots de los datos en cada etapa del pipeline (sin modificar el flujo) |
| Metrics | `pipeline/metrics.py` | Recolecta y exporta métricas de cada etapa a `pipeline_metrics.jsonl` |

**Flujo:**
1. `Ingestion` → lee desde BigQuery (tabla `bigquery-public-data.london_crime.crime_by_lsoa`, ~3M filas)
2. `Cleaning` → `clean_and_transform_data()` aplica: snake_case, elimina nulos en columnas críticas, convierte tipos, valida meses (1-12) y años (2008-2016), elimina valores negativos, normaliza mayúsculas/title case, elimina duplicados exactos y por subset, crea columna `date`, opcionalmente remueve outliers vía IQR
3. `Loading` → `load_to_supabase()` hace upsert de los datos agregados a Supabase; `save_clean_data()` guarda CSV/Parquet localmente
4. `Metrics` → cada etapa registra duración, registros in/out, reducción %
5. `ML Pipeline` → `cli.ml_pipeline.py` entrena modelos sobre los datos en Supabase

</details>

---

## Opciones de Evolución

### Opción A (Actual) — Estimador Histórico  ✅

El modelo actual entrenado con split aleatorio. Sirve como demo del pipeline completo pero **no debe usarse para predicción real**. La documentación y UI son honestas sobre esta limitación.

**Archivos clave:**
- `apps/backend/cli/ml_pipeline.py` — entrenamiento de modelos
- `apps/backend/ml/classification.py` — LogisticRegression + RandomForestRegressor
- `apps/backend/ml/preprocessing.py` — feature engineering
- `apps/backend/data/models/*.joblib` — modelos serializados
- `apps/backend/api/predict.py` — API endpoint
- `apps/frontend/src/App.jsx` — UI del estimador
- `apps/frontend/public/ml/ml_metrics.json` — métricas para dashboard

### Opción B (Recomendada para mejora inmediata) — Split Temporal Correcto

Cambiar el split aleatorio por un split temporal que respete el orden cronológico:

```python
# En lugar de train_test_split aleatorio:
train = df[df["year"] <= 2014]   # 2008-2014 → entrenamiento
test  = df[df["year"] >= 2015]   # 2015-2016  → evaluación
```

**Mejoras adicionales:**
- Features de temporalidad explícitas: month-of-year como sinusoidal, lag-1 y lag-12 del mismo (borough, category).
- Rolling averages de los últimos 3 y 6 meses (como features, no como target).
- Evaluación walk-forward: entrenar con 2008-2013, test 2014; luego 2008-2014, test 2015; luego 2008-2015, test 2016.
- Threshold dinámico por (borough, category) en lugar de mediana global de 3.

**Métricas esperadas (reales, no infladas):** Accuracy ~75-80%, R² ~0.70-0.80.

### Opción C (Meta) — Modelo Predictivo Real

Reemplazar scikit-learn con modelos de series temporales:

- **Prophet (Meta):** Maneja estacionalidad anual, mensual. No requiere features manuales. Bueno para contar crímenes por (borough, category) como serie independiente.
- **LSTM / GRU:** Red recurrente para capturar dependencias temporales largas. Requiere mucho más dato y preprocesamiento.
- **SARIMA:** Modelo estadístico clásico. Funciona bien si la serie es relativamente estable.

**Arquitectura propuesta:**
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Supabase    │───→│  Feature     │───→│  Prophet /   │
│  (histórico) │    │  Engineering │    │  LSTM        │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               ↓
                                        ┌──────────────┐
                                        │  /predict    │
                                        │  (futuro)    │
                                        └──────────────┘
```

**Resultado:** Podría predecir crímenes para 2017+ en lugar de solo estimar dentro del rango histórico.

---

## Estructura del Proyecto

```
```
DataGestor/
├── apps/
│   ├── frontend/                     # React + Vite + MUI
│   │   ├── src/
│   │   │   ├── App.jsx              # Dashboard + Estimador
│   │   │   └── ...
│   │   ├── public/
│   │   │   ├── ml/
│   │   │   │   ├── ml_metrics.json  # Métricas de clasificación
│   │   │   │   ├── confusion_matrix.png
│   │   │   │   └── roc_curve.png
│   │   │   ├── pipeline_stats.json  # Estadísticas del pipeline ETL
│   │   │   └── pipeline_logs.json   # Logs de ejecuciones
│   │   └── package.json
│   │
│   └── backend/                      # FastAPI + ML + Pipeline
│       ├── api/
│       │   └── predict.py           # Endpoint /predict
│       ├── cli/
│       │   ├── pipeline_dataops.py  # ETL BigQuery → Supabase
│       │   └── ml_pipeline.py       # Entrenamiento de modelos
│       ├── pipeline/
│       │   ├── ingestion.py         # Lectura BigQuery
│       │   ├── cleaning.py          # Limpieza de datos
│       │   ├── loading.py           # Carga a Supabase
│       │   ├── data_stage_manager.py # Snapshots por etapa
│       │   └── metrics.py           # Métricas del pipeline
│       ├── ml/
│       │   ├── classification.py    # LogisticRegression + RandomForest
│       │   ├── preprocessing.py     # Feature engineering
│       │   └── __init__.py
│       ├── data/models/             # Modelos .joblib (gitignored)
│       │   ├── logistic_regression.joblib
│       │   ├── crime_regressor.joblib
│       │   └── preprocessor.joblib
│       ├── tests/
│       │   ├── test_cleaning.py
│       │   ├── test_loading.py
│       │   ├── test_ml.py
│       │   ├── test_pipeline_dataops.py
│       │   └── conftest.py
│       └── requirements.txt
│
├── .github/workflows/
│   └── ci-backend.yml           # black + flake8 + pytest
│
├── docs/
│   ├── ML_PIPELINE.md       ← ML detallado
│   ├── DEPLOYMENT.md        ← Guía de despliegue
│   ├── ARCHITECTURE.md      ← Diagrama de arquitectura
│   ├── API.md               ← Referencia de la API
│   └── PRESENTATION.md      ← Narrativa del proyecto
│
├── README.md                ← Este archivo
└── SECURITY.md              ← Política de seguridad
```
```

---

## Inicio Rápido

```bash
# 1. Clonar
git clone <repo>
cd DataGestor

# 2. Frontend
cd apps/frontend
npm install
cp .env.example .env   # Configurar VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_ML_API_URL
npm run dev

# 3. Backend (Python)
cd apps/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Configurar SUPABASE_URL, SUPABASE_KEY
uvicorn api.predict:app --reload

# 4. Visitar
# Frontend: http://localhost:5173
# API:      http://localhost:8000/docs
```

---

## Licencia

MIT
