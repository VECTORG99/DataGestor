# 🏗️ Arquitectura del Sistema - DataGestor

## Índice

- [1. Visión General](#1-visión-general)
- [2. Componentes del Sistema](#2-componentes-del-sistema)
- [3. Flujo de Datos](#3-flujo-de-datos)
- [4. Patrones de Diseño](#4-patrones-de-diseño)
- [5. Base de Datos](#5-base-de-datos)
- [6. Backend Python](#6-backend-python)
- [7. Frontend React](#7-frontend-react)
- [8. Despliegue](#8-despliegue)
- [9. Escalabilidad](#9-escalabilidad)

---

## 1. Visión General

### Propósito
DataGestor es un sistema ETL + Analytics que procesa datos de crímenes en Londres desde Google BigQuery, realiza análisis estadístico con ML, y proporciona un dashboard interactivo para visualización.

### Stack Tecnológico

```
Data Layer:        Google BigQuery → Supabase PostgreSQL
Processing:        Python 3.11 (pandas, scikit-learn, SQLAlchemy)
Presentation:      React 19 + Vite 8 + Material-UI 9
Deployment:        Vercel (Frontend), Docker (Backend)
Orchestration:     CLI Commands (python-based)
```

### Principios de Arquitectura

1. **Separación de Capas**: ETL, ML, y Frontend desacoplados
2. **Escalabilidad Horizontal**: Paginación paralela en frontend
3. **Automatización**: CI/CD con GitHub Actions
4. **Observabilidad**: Logs, métricas, reportes de validación
5. **Seguridad**: GDPR-compliant, TLS 1.3, RLS policies

---

## 2. Componentes del Sistema

### 2.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Google BigQuery - london_crime dataset (3M+ rows)        │   │
│  │ • 2008-2016 data                                          │   │
│  │ • 33 boroughs, 8+ categories                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ (GCP Service Account)
                         │
┌────────────────────────v────────────────────────────────────────┐
│                    BATCH PROCESSING LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ETL Pipeline (Python)                                    │   │
│  │ ├── Ingestion: BigQuery → DataFrame                      │   │
│  │ ├── Cleaning: 10-stage pipeline                          │   │
│  │ ├── Validation: Outlier detection                        │   │
│  │ └── Loading: DataFrame → Supabase                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ML Training (Python)                                     │   │
│  │ ├── Preprocessing: Feature engineering                   │   │
│  │ ├── Training: Logistic Regression                        │   │
│  │ └── Evaluation: Metrics, confusion matrix                │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ (SQLAlchemy ORM, psycopg2)
                         │
┌────────────────────────v────────────────────────────────────────┐
│                    DATA LAYER                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Supabase PostgreSQL (Free Tier)                          │   │
│  │ ├── london_crime_aggregated (77.5k rows, 8 MB)          │   │
│  │ └── Row-Level Security Policies                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │ (PostgREST JSON API)
                         │
        ┌────────────────┴────────────────┐
        │                                  │
┌───────v──────────┐          ┌───────────v──────┐
│  PRESENTATION    │          │  ML ARTIFACTS    │
│  LAYER           │          │  LAYER           │
│                  │          │                  │
│ React Dashboard  │          │ • Metrics JSON   │
│ • Charts         │          │ • ROC Curve PNG  │
│ • Heatmaps       │          │ • Confusion Mat  │
│ • Tables         │          │ • Model joblib   │
│ • Exports        │          │                  │
└──────────────────┘          └──────────────────┘
        │
        │ (Vercel CDN)
        │
        v
    USERS
```

### 2.2 Tabla de Componentes

| Componente | Responsabilidad | Tecnología | Entrada | Salida |
|---|---|---|---|---|
| **BigQuery** | Almacén de datos crudos | Google Cloud | N/A | 3M registros |
| **ETL Pipeline** | Ingesta, limpieza, carga | Python, pandas | BigQuery | 77.5k registros |
| **ML Pipeline** | Entrenamiento, evaluación | scikit-learn | Datos limpios | Métricas, modelo |
| **Supabase** | Persistencia y API | PostgreSQL, PostgREST | DataFrames | JSON API |
| **Frontend** | Visualización e interacción | React, Vite, MUI | JSON API | HTML/CSS/JS |
| **Vercel** | Hosting de frontend | CDN, serverless | React build | HTTPS |

---

## 3. Flujo de Datos

### 3.1 Orquestación ETL

```
Step 1: INGEST
├─ Conectar a BigQuery
├─ Query: SELECT * FROM london_crime_by_lsoa LIMIT 3M
├─ Descargar a Parquet (~300 MB)
└─ Output: data/raw/london_crime_raw.parquet

Step 2: CLEAN
├─ 10 etapas de limpieza:
│  1. Standardize columns
│  2. Handle nulls
│  3. Validate types
│  4. Validate ranges
│  5. Normalize text
│  6. Remove duplicates
│  7. AGGREGATE (3M → 77.5k)
│  8. Create date column
│  9. Detect outliers
│  10. Keep columns
└─ Output: data/processed/london_crime_processed.csv

Step 3: VALIDATE
├─ Verificar rangos
├─ Detectar outliers (IQR, Z-score)
└─ Output: data/validated/validation_report.txt

Step 4: LOAD
├─ Leer CSV limpio
├─ Conectar a Supabase
├─ INSERT/UPSERT en london_crime_aggregated
└─ Output: Supabase DB (77.5k rows)
```

**Duración total**: ~5-10 minutos (dependiendo de conectividad)

### 3.2 Orquestación ML

```
Step 1: PREPROCESS
├─ One-Hot Encode: borough, major_category, minor_category
├─ StandardScale: year
├─ Cyclical encode: month (sin/cos)
└─ Output: Feature matrix (77.5k × ~80 columns)

Step 2: SPLIT
├─ Train/Test: 70/30 (stratified)
├─ Train set: 54.3k records
└─ Test set: 23.2k records

Step 3: TRAIN
├─ Fit LogisticRegression(max_iter=1000)
├─ Class weight: balanced
└─ Output: Trained model

Step 4: EVALUATE
├─ Predict on test set
├─ Calculate: Accuracy, Precision, Recall, F1, ROC AUC
├─ Generate: Confusion matrix, ROC curve
└─ Output: metrics.json, *.png

Step 5: SAVE
├─ Serialize model → logistic_regression.joblib
└─ Copy metrics to frontend/public/ml/
```

**Duración total**: ~2 minutos

### 3.3 Flujo de Usuario Frontend

```
User opens dashboard
    │
    ├─ 1. Load initial data (first 1,000 rows)
    ├─ 2. Get total count (count=exact)
    ├─ 3. Render KPIs
    ├─ 4. Render charts (aggregated)
    │
    └─ On filter change:
       ├─ 1. Query Supabase with filters
       ├─ 2. Paginate results (10 concurrent)
       ├─ 3. Aggregate in-memory
       ├─ 4. Re-render charts
       └─ 5. Show table excerpt
```

---

## 4. Patrones de Diseño

### 4.1 ETL Pattern

**Pipeline stages:**

```python
@dataclass
class PipelineStage:
    name: str
    input: DataFrame
    process: Callable
    output: DataFrame
    metrics: Dict

# Ejecutar en secuencia
stages = [
    PipelineStage("ingest", ..., ingest_from_bigquery, ...),
    PipelineStage("clean", ..., clean_data, ...),
    PipelineStage("validate", ..., validate_data, ...),
    PipelineStage("load", ..., load_to_supabase, ...),
]

for stage in stages:
    stage.output = stage.process(stage.input)
    log(f"{stage.name}: {len(stage.output)} rows")
```

### 4.2 Dependency Injection

**En CLI commands:**

```python
# config/settings.py - centralized config
class Settings:
    bigquery_table: str = "..."
    supabase_url: str = env("SUPABASE_DB_URL")
    row_limit: int = 3_000_000

# apps/backend/cli/pipeline_dataops.py
def main(settings: Settings = Settings()):
    pipeline = ETLPipeline(settings)
    pipeline.execute()
```

### 4.3 Repository Pattern

```python
# apps/backend/pipeline/loading.py
class DataRepository:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
    
    def save(self, df: DataFrame, table: str):
        df.to_sql(table, self.engine, if_exists="replace")
    
    def load(self, table: str) -> DataFrame:
        return pd.read_sql(f"SELECT * FROM {table}", self.engine)

# Usage
repo = DataRepository(SUPABASE_DB_URL)
repo.save(df_clean, "london_crime_aggregated")
```

### 4.4 Chain of Responsibility

```python
# Data validation chain
class Validator:
    def __init__(self, next_validator=None):
        self.next = next_validator
    
    def validate(self, df):
        df = self._validate(df)
        if self.next:
            return self.next.validate(df)
        return df

# Build chain
chain = (
    RangeValidator(
        TextValidator(
            TypeValidator(NullValidator())
        )
    )
)

df_validated = chain.validate(df_raw)
```

---

## 5. Base de Datos

### 5.1 Schema

```sql
CREATE TABLE london_crime_aggregated (
    id SERIAL PRIMARY KEY,
    
    -- Geographic
    borough VARCHAR(50) NOT NULL,          -- e.g., "Westminster"
    
    -- Crime Classification
    major_category VARCHAR(50) NOT NULL,   -- e.g., "Robbery"
    minor_category VARCHAR(100) NOT NULL,  -- e.g., "Robbery of personal property"
    
    -- Temporal
    year INT NOT NULL,                     -- 2008-2016
    month INT NOT NULL,                    -- 1-12
    date TIMESTAMP NOT NULL,               -- First day of month
    
    -- Metric
    total_crimes FLOAT NOT NULL,           -- Aggregated count
    
    -- Indexes for query performance
    INDEX idx_borough (borough),
    INDEX idx_year_month (year, month),
    INDEX idx_date (date)
);

-- Enable Row-Level Security
ALTER TABLE london_crime_aggregated ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "anon_read" ON london_crime_aggregated
    FOR SELECT TO anon USING (true);

CREATE POLICY "service_role_all" ON london_crime_aggregated
    FOR ALL TO service_role USING (true);
```

### 5.2 Índices

| Índice | Columnas | Propósito | Query Time |
|--------|----------|----------|-----------|
| `idx_borough` | borough | Filtrar por distrito | O(log n) |
| `idx_year_month` | year, month | Filtrar por período | O(log n) |
| `idx_date` | date | Ordenar temporal | O(log n) |
| PRIMARY KEY | id | Identify rows | O(log n) |

**Sin índices**: SELECT * FROM london_crime_aggregated WHERE borough='Westminster' → Full table scan (O(n))  
**Con índices**: Mismo query → Index lookup (O(log n)) → 100x más rápido

### 5.3 Performance

| Metrica | Valor |
|---------|-------|
| **Tabla Size** | 8 MB |
| **Rows** | 77,524 |
| **Storage Usage** | 1.6% del Free Tier (500 MB) |
| **Avg Query Time** | < 100 ms |
| **Concurrent Users** | Unlimited (Supabase manages) |

---

## 6. Backend Python

### 6.1 Modularidad

```
apps/backend/
├── pipeline/              # ETL operations
│   ├── ingestion.py      # Read from BigQuery
│   ├── cleaning.py       # 10-stage cleaning
│   ├── validation.py     # Outlier detection
│   ├── loading.py        # Write to Supabase
│   └── metrics.py        # Collect statistics
├── ml/                    # Machine learning
│   ├── preprocessing.py   # Feature engineering
│   └── classification.py  # Model training
├── cli/                   # Command-line interfaces
│   ├── pipeline_dataops.py  # Orchestrate ETL
│   └── ml_pipeline.py       # Orchestrate ML
└── tests/                 # Unit tests
```

### 6.2 Importancia de Dependencias

```python
# Tight coupling (❌ BAD)
class MyClass:
    def __init__(self):
        self.db = Supabase(SUPABASE_URL)  # Hard-coded dependency

# Loose coupling (✅ GOOD)
class MyClass:
    def __init__(self, db: Repository):  # Injected dependency
        self.db = db
```

### 6.3 Error Handling

```python
try:
    df = ingest_from_bigquery()
except BigQueryException as e:
    logger.error(f"BigQuery error: {e}")
    df = load_sample_data()  # Fallback
except Exception as e:
    logger.critical(f"Unexpected error: {e}")
    sys.exit(1)
```

---

## 7. Frontend React

### 7.1 Component Hierarchy

```
App.jsx (root)
├─ Header
├─ KPIs (cards)
├─ Filters (borough, category, year)
├─ Charts Container
│  ├─ BarChart (crimes/borough)
│  ├─ PieChart (category distribution)
│  ├─ LineChart (temporal trend)
│  ├─ HorizontalBarChart (top 10)
│  ├─ Heatmap (borough × year)
│  └─ MLInsights (confusion matrix, ROC)
├─ DataTable
└─ ExportButtons
```

### 7.2 State Management

```javascript
// Simple state: useState
const [filters, setFilters] = useState({
    borough: null,
    category: null,
    year: null
});

// Effect: Fetch data on filter change
useEffect(() => {
    fetchData(filters);
}, [filters]);
```

### 7.3 Data Fetching (Paginación Paralela)

```javascript
async function fetchAllData() {
    // Step 1: Get total count
    const { count } = await supabase
        .from('london_crime_aggregated')
        .select('*', { count: 'exact', head: true });
    
    // Step 2: Paginate in parallel (10 concurrent)
    const batches = [];
    for (let i = 0; i < count; i += 1000) {
        batches.push(
            supabase
                .from('london_crime_aggregated')
                .select('*')
                .range(i, i + 999)
        );
    }
    
    // Step 3: Aggregate results
    const results = await Promise.all(batches);
    return results.flatMap(r => r.data);
}
```

---

## 8. Despliegue

### 8.1 Entornos

| Entorno | Frontend | Backend | Database | Deploy |
|---------|----------|---------|----------|--------|
| **Development** | localhost:5173 | localhost:8000 | Supabase Free | git push to branch |
| **Staging** | Vercel preview | N/A | Supabase Free | PR preview |
| **Production** | Vercel | Docker | Supabase Prod | git push to main |

### 8.2 Pipeline CI/CD

```yaml
GitHub Push → Actions Runner
├─ Checkout code
├─ Setup Python 3.11
├─ Install dependencies
├─ Run Black (format check)
├─ Run Flake8 (lint)
├─ Run pytest
└─ Deploy to Vercel (if main branch)
```

---

## 9. Escalabilidad

### 9.1 Horizontal Scaling

**Frontend:**
- ✅ Stateless React app → Infinita instancias
- ✅ Vercel CDN → Global distribution
- ✅ Paginación paralela → Maneja 1M+ rows

**Backend:**
- ✅ Batch processing → No necesita scaling
- ✅ Scheduled jobs → Ejecutar off-peak
- ✅ Docker containers → Multi-instance deployment

**Database:**
- ✅ Supabase managed → Auto-scaling
- ✅ Read replicas → Para heavy queries
- ✅ Connection pooling → PgBouncer

### 9.2 Performance Optimizations

| Nivel | Técnica | Impacto |
|-------|---------|--------|
| **Database** | Indexing | 10-100x |
| **API** | Paginación | 5-10x |
| **Frontend** | Lazy loading | 2-5x |
| **Network** | CDN, compression | 2-5x |
| **Cache** | Redis (optional) | 5-50x |

### 9.3 Límites Actuales

| Métrica | Límite | Porcentaje Usado |
|--------|--------|-----------------|
| Database Storage (Supabase Free) | 500 MB | 1.6% |
| Row Limit | 2 GB | ~0.4% |
| API Requests | Unlimited | <0.1% |
| Concurrent Users | Unlimited | <0.1% |

**Conclusión**: Escala actual soporta 10x+ de usuarios sin cambios.

---

## 10. Monitoreo y Observabilidad

### 10.1 Logs

```
data/logs/pipeline.log
├─ Start time, end time
├─ Rows processed per stage
├─ Errors/warnings
└─ Execution time per stage
```

### 10.2 Métricas

```
data/metrics/pipeline_metrics.jsonl
{
    "stage": "ingest",
    "rows_before": 0,
    "rows_after": 3000000,
    "duration_seconds": 120,
    "timestamp": "2026-06-21T10:30:00Z"
}
```

### 10.3 Alertas

```bash
# Si ejecución > 30 minutos
# Si rows < 70,000 (anomalía de datos)
# Si error en pipeline
```

---

## 11. Seguridad en Arquitectura

- ✅ **Defense in depth**: Múltiples capas (TLS, RLS, env vars)
- ✅ **Least privilege**: Credenciales restringidas
- ✅ **Separation of concerns**: Anon vs service_role
- ✅ **Audit trail**: Logs de todas las operaciones

---

**Última actualización:** Junio 2026  
**Diseñador de arquitectura:** [nombre]
