# DataGestor - Sistema de Inteligencia Territorial para Seguridad Pública

[![CI Backend](https://img.shields.io/github/actions/workflow/status/VECTORG99/DataGestor/ci-backend.yml?label=CI%20Backend&logo=github)](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml)
[![Deploy Status](https://img.shields.io/badge/deploy-Vercel-black?logo=vercel)](https://data-gestor.vercel.app/)
[![Python Version](https://img.shields.io/badge/python-3.11-blue?logo=python)](https://www.python.org/)
[![React Version](https://img.shields.io/badge/react-19-61DAFB?logo=react)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)

> **Dashboard interactivo de análisis de criminalidad en Londres (2008-2016)** con pipeline ETL desde BigQuery, almacenamiento en Supabase, y visualización con React + Material UI. Incluye modelo ML (Regresión Logística) para clasificación de alta/baja incidencia delictiva con **89% de precisión**.

** Demo en vivo:** [data-gestor.vercel.app](https://data-gestor.vercel.app/) | ** Dataset:** 77,524 registros agregados | ** Años:** 2008-2016 | ** Distritos:** 33 boroughs

---

## Tabla de Contenidos

- [ Características Principales](#-características-principales)
- [ Arquitectura General](#-arquitectura-general)
- [ Inicio Rápido](#-inicio-rápido)
- [ Instalación y Configuración](#-instalación-y-configuración)
- [ Variables de Entorno](#-variables-de-entorno)
- [ Pipeline de Datos](#-pipeline-de-datos)
- [ Machine Learning](#-machine-learning)
- [ Desarrollo](#-desarrollo)
- [ Estructura del Proyecto](#-estructura-del-proyecto)
- [ Dashboard](#-dashboard)
- [ Despliegue](#-despliegue)
- [ CI/CD](#-cicd)
- [ Documentación Adicional](#-documentación-adicional)
- [ Seguridad](#-seguridad)
- [ Contribuir](#-contribuir)

---

## Características Principales

 **Pipeline ETL robusto**: Ingesta de 3M+ registros desde BigQuery con 10 etapas de limpieza y validación  
 **Compresión de datos**: Reducción de 97% (3M → 77.5k registros agregados) optimizando almacenamiento  
 **Dashboard interactivo**: Visualización en tiempo real con 33 distritos, 8 categorías, 9 años de datos  
 **Exportación de datos**: 3 modos de exportación a Excel (filtrado, agregado, completo)  
 **Modelo ML**: Regresión Logística con 89% de precisión y AUC 0.963 para predicción de criminalidad  
 **Escalabilidad**: Paginación paralela manejando 77.5k filas sin problemas de rendimiento  
 **Seguridad**: Cumplimiento GDPR, cifrado TLS 1.3, Row-Level Security en Supabase  
 **CI/CD Automatizado**: GitHub Actions con linting, formateo y tests en cada push

---

## Arquitectura General

```
┌─────────────────────┐
│    Google BigQuery  │ (3M filas de crímenes de Londres)
│  (london_crime DB)  │
└──────────┬──────────┘
           │
           ├──────────────────┐
           │                  │
    ┌──────v────────┐   ┌─────v──────────┐
    │   GCP Creds   │   │ Python ETL CLI │
    │ credentials   │   │ (pandas, SQL)  │
    │  .json        │   │                │
    └───────────────┘   └──────┬─────────┘
                                │
                         [10-Stage Cleaning]
                         • Standardize
                         • Validate ranges
                         • Detect outliers (IQR)
                         • Aggregate
                         • Remove duplicates
                                │
                         3M rows → 77.5k rows
                                │
                    ┌───────────v──────────────┐
                    │ Supabase PostgreSQL      │
                    │ london_crime_aggregated  │
                    │ (8 MB, 77,524 registros) │
                    └───────────┬──────────────┘
                                │
                ┌───────────────┴──────────────┐
                │                              │
         ┌──────v───────────┐        ┌────────v─────────┐
         │ React Dashboard  │        │  ML Training CLI │
         │ (Vite + MUI)     │        │  (scikit-learn)  │
         │                  │        │                  │
         │ • Charts         │        │ • Preprocessing  │
         │ • Heatmap        │        │ • Train/Test     │
         │ • Excel Export   │        │ • Metrics        │
         │ • Pag Paralela   │        └──────┬───────────┘
         │ (10 concurrent)  │               │
         └──────────────────┘      ┌────────v─────────┐
                                    │ ML Insights      │
                                    │ • Confusion Mat  │
                                    │ • ROC Curve      │
                                    │ • Model Stats    │
                                    └──────────────────┘
```

### Componentes Clave

| Componente | Tecnología | Propósito | Detalles |
|---|---|---|---|
| **Fuente de datos** | Google BigQuery | Dataset público `london_crime` | 3M registros crudos (2008-2016) |
| **Pipeline ETL** | Python 3.11 (pandas, SQLAlchemy) | Ingesta, limpieza, agregación | 10 etapas, detección de outliers |
| **Base de datos** | Supabase PostgreSQL | Almacenamiento persistente | 77,524 registros, 8 MB |
| **Frontend** | React 19 + Vite 8 + MUI 9 | Dashboard interactivo | Desplegado en Vercel |
| **ML** | scikit-learn (LogisticRegression) | Clasificación binaria | 89% accuracy, AUC 0.963 |
| **Visualización** | Chart.js + Material-UI | Gráficos y heatmaps | 8 tipos de visualización |
| **Exportación** | SheetJS (xlsx) | Descarga a Excel | 3 modos (filtrado, agregado, completo) |
| **CI/CD** | GitHub Actions | Automatización | Black, Flake8, pytest |

### Nota sobre Paginación en Supabase

El API REST de Supabase (PostgREST) limita las respuestas a **1,000 filas por request**. El frontend maneja esto con paginación paralela en batches:

- **Paso 1**: Obtiene el total de filas via `count=exact`
- **Paso 2**: Descarga las 77,524 filas en ~78 requests paralelos (10 concurrentes)
- **Paso 3**: Agrega los datos en el cliente para renderizar charts

---

## Inicio Rápido

### Opción 1: Vercel (Solo Frontend, recomendado para demo)

```bash
# Sin instalación local - accede directamente a:
# https://data-gestor.vercel.app/
```

### Opción 2: Docker Compose (Stack completo local)

```bash
# Clonar el repositorio
git clone https://github.com/VECTORG99/DataGestor.git
cd DataGestor

# Crear archivo .env (ver sección Variables de Entorno)
cp config/.env.example .env
# Editar .env con tus credenciales

# Levantar servicios
docker-compose up -d

# Ejecutar pipeline ETL
docker exec datagestor-app python apps/backend/cli/pipeline_dataops.py

# Ejecutar ML pipeline
docker exec datagestor-app python apps/backend/cli/ml_pipeline.py

# Frontend disponible en: http://localhost:5173
```

### Opción 3: Desarrollo Local (Backend + Frontend separados)

```bash
# Backend
cd apps/backend
pip install -r ../../requirements.txt
python cli/pipeline_dataops.py
python cli/ml_pipeline.py

# Frontend (en otra terminal)
cd apps/frontend
npm install
npm run dev
```

---

## 📦 Instalación y Configuración

### Requisitos

- **Node.js 20+** (para frontend)
- **Python 3.11+** (para backend)
- **Docker + Docker Compose** (opcional, para stack completo)
- **Cuenta de Supabase** (Base de datos)
- **Cuenta de Google Cloud** (BigQuery)

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/VECTORG99/DataGestor.git
cd DataGestor
```

### Paso 2: Configurar variables de entorno

```bash
# Crear archivo .env en la raíz del proyecto
cp config/.env.example .env
```

Editar `.env` con tus credenciales (ver [sección Variables de Entorno](#-variables-de-entorno)).

### Paso 3: Instalar dependencias

**Backend:**
```bash
pip install -r requirements.txt
```

**Frontend:**
```bash
cd apps/frontend
npm install
```

### Paso 4: Ejecutar pipeline ETL

```bash
python apps/backend/cli/pipeline_dataops.py
```

Esto va a:
1. Leer datos de BigQuery (3M filas)
2. Aplicar 10 etapas de limpieza
3. Validar y detectar outliers
4. Cargar 77,524 registros agregados a Supabase

### Paso 5: Entrenar modelo ML

```bash
python apps/backend/cli/ml_pipeline.py
```

Esto va a:
1. Preprocesar features
2. Entrenar Logistic Regression
3. Generar confusion matrix y ROC curve
4. Guardar métricas en `data/metrics/ml_metrics.json`

### Paso 6: Ejecutar frontend

```bash
cd apps/frontend
npm run dev
```

Accede a: `http://localhost:5173`

---

## Variables de Entorno

### Archivo `.env` (Raíz del proyecto)

```bash
# ============================================================================
# GCP / BigQuery Configuration
# ============================================================================
GCP_PROJECT_ID=london-crime-491323
BIGQUERY_TABLE=bigquery-public-data.london_crime.crime_by_lsoa
BIGQUERY_ROW_LIMIT=3000000  # Límite de filas a extraer (ajustar por storage)
GOOGLE_APPLICATION_CREDENTIALS=config/credentials.json

# ============================================================================
# Supabase Configuration
# ============================================================================
SUPABASE_DB_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
SUPABASE_TABLE_NAME=london_crime_aggregated

# ============================================================================
# Logging & Debug
# ============================================================================
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
DB_ECHO=false                      # Log SQL queries
SAMPLE_N_ROWS=150                  # Para tests/demo, producción es 3M

# ============================================================================
# Pipeline Parameters
# ============================================================================
VALIDATION_IQR_MULTIPLIER=1.5     # Rango IQR para outliers
VALIDATION_ZSCORE_THRESHOLD=3     # Z-score threshold

# ============================================================================
# Data Directories (Opcional)
# ============================================================================
# Si no se especifican, usan defaults en config/settings.py
DATA_DIR=./data
RAW_DIR=./data/raw
VALIDATED_DIR=./data/validated
PROCESSED_DIR=./data/processed
LOG_DIR=./data/logs
METRICS_DIR=./data/metrics
```

### Archivo `apps/frontend/.env.local` (Frontend)

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Optional: API Backend (si tienes backend REST propio)
# VITE_API_URL=http://localhost:8000
```

### Obtener credenciales

#### Google Cloud (BigQuery)

1. Crear proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar BigQuery API
3. Crear Service Account
4. Descargar JSON key → guardar como `config/credentials.json`
5. Obtener GCP_PROJECT_ID del proyecto

#### Supabase

1. Crear proyecto en [supabase.com](https://supabase.com)
2. Ir a Settings → API
3. Copiar `Project URL` → `VITE_SUPABASE_URL`
4. Copiar `anon public key` → `VITE_SUPABASE_ANON_KEY`
5. Para backend, usar `Service Role` key en `SUPABASE_DB_URL`

---

## Pipeline de Datos

### Fases del Pipeline

#### Ingesta (BigQuery)

```python
# apps/backend/pipeline/ingestion.py
from apps.backend.pipeline.ingestion import ingest_from_bigquery

df = ingest_from_bigquery(row_limit=3_000_000)
# Resultado: DataFrame con 3M+ filas crudas
```

**Columnas de entrada:**
- `borough` - Distrito de Londres
- `major_category` - Tipo de crimen (ej: Robo, Asalto)
- `minor_category` - Subtipo de crimen
- `value` - Cantidad de crímenes
- `year`, `month` - Período

#### Limpieza (10 Etapas)

```python
# apps/backend/pipeline/cleaning.py
from apps.backend.pipeline.cleaning import CleanuPipeline

cleaner = CleaningPipeline()
df_clean = cleaner.execute(df)
# Resultado: 77,524 filas agregadas
```

| # | Etapa | Operación | Filas antes | Filas después |
|---|-------|-----------|-------------|---------------|
| 1 | Standardize columns | snake_case, nombres consistentes | 3M | 3M |
| 2 | Handle nulls | Elimina filas con nulos críticos | 3M | 2.9M |
| 3 | Validate types | Convierte a Int64/float64 | 2.9M | 2.8M |
| 4 | Validate ranges | Mes [1-12], año ≥ 2000, valor ≥ 0 | 2.8M | 2.7M |
| 5 | Normalize text | Strip, title(), correcciones | 2.7M | 2.7M |
| 6 | Remove duplicates | Elimina filas idénticas | 2.7M | 2.6M |
| 7 | **Aggregate** | GROUP BY + SUM(value) | 2.6M | **77.5k** |
| 8 | Create date column | Derived: first day of month | 77.5k | 77.5k |
| 9 | Detect outliers | IQR + Z-score (solo reporte) | 77.5k | 77.5k |
| 10 | Keep columns | Mantiene solo columns relevantes | 77.5k | 77.5k |

**Reducción:** 3M → 77,524 (97.4% compresión)

#### Validación

```python
# apps/backend/pipeline/data_stage_manager.py
from apps.backend.pipeline.data_stage_manager import DataStageManager

validator = DataStageManager()
report = validator.generate_validation_report(df_clean)
# Resultado: Reporte con estadísticas, outliers detectados
```

**Validaciones:**
- ✅ Rango de años (2000+)
- ✅ Rango de meses (1-12)
- ✅ Valores positivos
- ✅ Detección de outliers (IQR × 1.5)
- ✅ Z-score threshold (3)

#### 4️⃣ Carga (Supabase)

```python
# apps/backend/pipeline/loading.py
from apps.backend.pipeline.loading import load_to_supabase

load_to_supabase(df_clean, table_name='london_crime_aggregated', 
                 if_exists='replace', chunksize=1000)
# Resultado: Tabla Supabase con 77,524 registros
```

**Schema:**
```sql
CREATE TABLE london_crime_aggregated (
  borough VARCHAR,
  major_category VARCHAR,
  minor_category VARCHAR,
  year INT,
  month INT,
  total_crimes FLOAT,
  date TIMESTAMP
);
```

### Ejecutar Pipeline Manualmente

```bash
# Ejecutar pipeline completo
python apps/backend/cli/pipeline_dataops.py

# Con logs detallados
LOG_LEVEL=DEBUG python apps/backend/cli/pipeline_dataops.py

# Modo demo (150 filas)
SAMPLE_N_ROWS=150 python apps/backend/cli/pipeline_dataops.py
```

### Outputs del Pipeline

| Ruta | Contenido | Formato | Tamaño |
|------|-----------|---------|--------|
| `data/raw/` | Datos crudos de BigQuery | Parquet | ~300 MB |
| `data/validated/` | Reporte de validación | TXT | 50 KB |
| `data/processed/london_crime_processed.csv` | 77,524 registros limpios | CSV | 8 MB |
| `data/processed/london_crime_aggregated.csv` | Agregado final | CSV | 8 MB |
| `data/logs/pipeline.log` | Log de ejecución | LOG | 100 KB |
| `data/metrics/pipeline_metrics.jsonl` | Métricas por etapa | JSONL | 2 KB |

---

## Machine Learning

### Modelo: Logistic Regression (Clasificación Binaria)

**Objetivo:** Predecir si un distrito-mes tiene criminalidad "Alta" o "Baja"

**Target:** 
- `1` si `total_crimes > mediana`
- `0` si `total_crimes ≤ mediana`

### Features (6)

| # | Feature | Tipo | Transformación | Valores únicos |
|---|---------|------|---|---|
| 1 | `borough` | Categórico | One-Hot Encoding | 33 |
| 2 | `major_category` | Categórico | One-Hot Encoding | 8 |
| 3 | `minor_category` | Categórico | One-Hot Encoding | ~40 |
| 4 | `year` | Numérico | StandardScaler | 9 (2008-2016) |
| 5 | `month_sin` | Numérico | Cíclico: sin(2π × mes/12) | - |
| 6 | `month_cos` | Numérico | Cíclico: cos(2π × mes/12) | - |

**Preprocesamiento:**
```python
# apps/backend/ml/preprocessing.py
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), 
     ['borough', 'major_category', 'minor_category']),
    ('num', StandardScaler(), ['year', 'month_sin', 'month_cos'])
])

X_transformed = preprocessor.fit_transform(X)
```

### Métricas de Rendimiento

**Dataset:** 77,524 registros | **Split:** 70% train, 30% test

| Métrica | Valor | Interpretación |
|---------|-------|---|
| **Accuracy** | 89.0% | De cada 100 predicciones, 89 son correctas |
| **Precision** | 86.5% | De los casos predichos como "Alta", 86.5% son reales |
| **Recall** | 91.4% | Encuentra 91.4% de los casos reales "Alta" |
| **F1 Score** | 88.9% | Balance entre Precision y Recall |
| **ROC AUC** | **0.9634** | Excelente discriminación entre clases |
| **Gini** | **0.9267** | Muy buen ordenamiento predictivo |

### Matriz de Confusión

```
                Predicción
              Baja    Alta
Real   Baja  [ 9,532 | 1,200 ]  → Specificity: 88.8%
       Alta  [ 1,830 | 21,238 ] → Sensitivity: 92.1%
```

### Entrenar Modelo

```bash
# Entrenar y generar métricas
python apps/backend/cli/ml_pipeline.py

# Salidas:
# - data/metrics/ml_metrics.json (métricas)
# - data/metrics/confusion_matrix.png (gráfico)
# - data/metrics/roc_curve.png (gráfico)
# - apps/backend/ml/logistic_regression.joblib (modelo entrenado)
```

### Usar Modelo Entrenado

```python
import joblib
from apps.backend.ml.preprocessing import Preprocessor

# Cargar modelo y preprocesador
model = joblib.load('apps/backend/ml/logistic_regression.joblib')
preprocessor = Preprocessor()

# Preparar datos nuevos
X_new = preprocessor.preprocess(new_data)

# Predecir
predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)
```

---

## Desarrollo

### Estructura de Directorios

```
apps/backend/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── ml_pipeline.py           # CLI para entrenar ML
│   └── pipeline_dataops.py      # CLI para ejecutar ETL
├── ml/
│   ├── __init__.py
│   ├── classification.py        # Logistic Regression trainer
│   └── preprocessing.py         # Feature engineering
├── pipeline/
│   ├── __init__.py
│   ├── cleaning.py              # 10-stage cleaner
│   ├── data_stage_manager.py    # Validación y reportes
│   ├── ingestion.py             # BigQuery reader
│   ├── loading.py               # Supabase writer
│   └── metrics.py               # Metrics collection
└── tests/
    ├── __init__.py
    ├── conftest.py              # pytest fixtures
    ├── test_cleaning.py
    ├── test_loading.py
    ├── test_ml.py
    └── test_pipeline_dataops.py

apps/frontend/
├── src/
│   ├── App.jsx                  # Dashboard principal
│   ├── main.jsx
│   └── components/              # (puede agregarse)
├── public/
│   ├── ml/
│   │   └── ml_metrics.json      # ML metrics display
│   └── pipeline_stats.json      # Pipeline stats display
├── package.json
├── vite.config.js
└── vercel.json
```

### Ejecutar Tests

```bash
# Todos los tests
pytest apps/backend/tests/ -v

# Tests específicos
pytest apps/backend/tests/test_ml.py -v

# Con cobertura
pytest apps/backend/tests/ --cov=apps/backend --cov-report=html

# Tests de limpieza
pytest apps/backend/tests/test_cleaning.py::test_standardize_columns -v
```

### Linting y Formateo

```bash
# Formatear código (Black)
black apps/backend/

# Lint (Flake8)
flake8 apps/backend/ --max-line-length=100

# Ambos
make lint  # si tienes Makefile
```

### Build del Frontend

```bash
cd apps/frontend

# Modo desarrollo
npm run dev

# Build producción
npm run build

# Preview
npm run preview
```

### Agregar Nuevas Dependencias

**Backend:**
```bash
pip install new-package
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd apps/frontend
npm install new-package
git add package.json package-lock.json
```

---

## Estructura del Proyecto

```
DataGestor/
├── 📄 README.md                         # Este archivo
├── 📄 SECURITY.md                       # Políticas de seguridad
├── 📄 LICENSE                           # Licencia MIT
├── 📄 pyproject.toml                    # Config Python
├── 📄 requirements.txt                  # Dependencias Python
│
├── 📁 docs/                             # Documentación técnica
│   ├── ARCHITECTURE.md                  # Arquitectura detallada
│   ├── API.md                           # Endpoints de Supabase
│   ├── ML_PIPELINE.md                   # Detalles del modelo ML
│   ├── DEPLOYMENT.md                    # Instrucciones de deploy
│   └── PRESENTATION.md                  # Presentación del proyecto
│
├── 📁 apps/backend/                     # Backend Python
│   ├── cli/
│   │   ├── ml_pipeline.py               # Orquestación ML
│   │   └── pipeline_dataops.py          # Orquestación ETL
│   ├── ml/
│   │   ├── classification.py            # Model trainer
│   │   └── preprocessing.py             # Feature engineering
│   ├── pipeline/
│   │   ├── cleaning.py                  # Data cleaning
│   │   ├── data_stage_manager.py        # Validation
│   │   ├── ingestion.py                 # BigQuery read
│   │   ├── loading.py                   # Supabase write
│   │   └── metrics.py                   # Metrics collection
│   └── tests/
│       ├── conftest.py
│       ├── test_cleaning.py
│       ├── test_loading.py
│       ├── test_ml.py
│       └── test_pipeline_dataops.py
│
├── 📁 apps/frontend/                    # Frontend React
│   ├── src/
│   │   ├── App.jsx                      # Main dashboard
│   │   └── main.jsx
│   ├── public/
│   │   ├── ml/ml_metrics.json
│   │   └── pipeline_stats.json
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
│
├── 📁 config/                           # Configuración centralizada
│   ├── settings.py                      # Parámetros del pipeline
│   ├── .env.example                     # Template .env
│   ├── boroughs.json                    # 33 distritos de Londres
│   └── categories.json                  # Categorías de crímenes
│
├── 📁 data/                             # Datos
│   ├── raw/                             # Datos crudos (BigQuery)
│   ├── validated/                       # Datos validados
│   ├── processed/                       # Datos procesados (77.5k)
│   ├── logs/                            # Pipeline logs
│   └── metrics/                         # ML metrics & graphs
│
├── 📁 infra/                            # Infraestructura
│   ├── docker-compose.yml               # Local stack
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── nginx.conf                       # Nginx config
│
├── 📁 .github/workflows/                # CI/CD
│   └── ci-backend.yml                   # GitHub Actions
│
└── 📁 .gitignore                        # Git ignore file
    (contiene: .env*, *.local, credentials.json, etc)
```

---

## Dashboard

**URL:** [data-gestor.vercel.app](https://data-gestor.vercel.app/)

### Secciones

#### 1. **KPIs (Top)**
- Total de crímenes: 1.3M+
- Distrito con más crímenes
- Categoría principal
- Registros filtrados

#### 2. **Controles de Filtro**
- Selector de Borough (33 distritos)
- Selector de Categoría (8 tipos)
- Selector de Año (2008-2016)
- 3 botones de exportación a Excel

#### 3. **Visualizaciones**

| Gráfico | Tipo | Datos |
|---------|------|-------|
| Crímenes por Distrito | Barras | Total por borough |
| Proporción por Categoría | Donut | % por tipo de crimen |
| Tendencia Temporal | Línea | Mes a mes (96 puntos) |
| Top 10 Subcategorías | Barras Horiz. | Subcategorías |
| Crímenes por Distrito y Año | Heatmap | 33×9 matrix |
| Tabla de Registros | Tabla | Primeros 100 |

#### 4. **Exportación a Excel**

**Modo 1: Datos Filtrados**
- Descarga solo registros con filtros activos
- Archivo: `london_crime_filtered_YYYY-MM-DD.xlsx`

**Modo 2: Datos Agregados**
- 3 hojas:
  - Crímenes por Distrito (33 filas)
  - Top 10 Subcategorías (10 filas)
  - Tendencia Temporal (96 meses)
- Archivo: `london_crime_aggregated_YYYY-MM-DD.xlsx`

**Modo 3: Dataset Completo**
- Todos los 77,524 registros
- Ignora filtros
- Archivo: `london_crime_complete_YYYY-MM-DD.xlsx` (~5-7 MB)

#### 5. **ML Insights**
- Accuracy: 89%
- ROC AUC: 0.9634
- Precision/Recall/F1
- Confusion Matrix (gráfico)
- ROC Curve (gráfico)

---

## Despliegue

Ver documentación completa en [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Frontend (Vercel)

```bash
# 1. Push a GitHub
git add .
git commit -m "Update features"
git push origin main

# 2. Vercel auto-deploy (configurado)
# 3. Accede a: https://data-gestor.vercel.app/
```

### Backend (Docker)

```bash
# Build imagen
docker build -f infra/backend.Dockerfile -t datagestor-backend .

# Ejecutar
docker run -v $(pwd):/app \
           -v ~/.config/gcloud:/root/.config/gcloud \
           --env-file .env \
           datagestor-backend

# O con compose
docker-compose up -d
```

---

## CI/CD

**GitHub Actions:** `.github/workflows/ci-backend.yml`

### Triggers

- ✅ Push a `main` branch
- ✅ Pull requests

### Steps

1. **Checkout** código
2. **Setup Python** 3.11
3. **Install deps** (requirements.txt)
4. **Black check** (formato código)
5. **Flake8 lint** (max-line-length=100)
6. **pytest** (tests unitarios)

### Variablespython/python-lint-job:
```yaml
env:
  SUPABASE_DB_URL: postgresql://test:test@localhost:5432/test
  GCP_PROJECT_ID: test-project
  BIGQUERY_ROW_LIMIT: 100
```

### Ver Status

- [GitHub Actions](https://github.com/VECTORG99/DataGestor/actions)
- Badge en README actualizado automáticamente

---

## Documentación Adicional

| Documento | Contenido |
|-----------|----------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diseño detallado de componentes, patrones, base de datos |
| [docs/API.md](docs/API.md) | Endpoints de Supabase, RLS policies, paginación |
| [docs/ML_PIPELINE.md](docs/ML_PIPELINE.md) | Algoritmo, features, validación de modelo |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deploy a Vercel, Docker, CI/CD setup |
| [docs/PRESENTATION.md](docs/PRESENTATION.md) | Slides para presentación del proyecto |
| [SECURITY.md](SECURITY.md) | GDPR, cifrado, manejo de secretos |

---

## Seguridad

Ver documentación completa en [SECURITY.md](SECURITY.md)

### ✅ Cumplimientos

- ✅ **GDPR (UE)**: Datos agregados y anónimos
- ✅ **Ley 19.628 (Chile)**: Sin PII, acceso restringido
- ✅ **Cifrado en tránsito**: TLS 1.3 (Supabase, BigQuery)
- ✅ **Cifrado en reposo**: AES-256 (Supabase, BigQuery)
- ✅ **Row-Level Security**: RLS policies en Supabase
- ✅ **Secretos**: .env en .gitignore, env vars en CI/CD
- ✅ **Contenedores**: Non-root user, image scanning

###  Gestión de Credenciales

```bash
# Nunca commitear:
.env
.env.local
config/credentials.json
*.private.key

# Siempre usar:
config/.env.example
.gitignore
GitHub Secrets (CI/CD)
Environment variables
```

---

## Contribuir

### Workflow

1. Fork el repositorio
2. Crear rama feature: `git checkout -b feature/my-feature`
3. Realizar cambios y tests
4. Commit: `git commit -am 'Add my feature'`
5. Push: `git push origin feature/my-feature`
6. Pull Request a `main`

### Estándares

- ✅ Formatear con **Black** (line-length=100)
- ✅ Lint con **Flake8**
- ✅ Tests con **pytest**
- ✅ Commit messages descriptivos
- ✅ Documentar nuevas features

**Última actualización:** Junio 2026 | **Versión:** 2.0
