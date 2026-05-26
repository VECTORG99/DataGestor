# Sistema de Inteligencia Territorial para la Seguridad Publica en Londres

[![CI Backend](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml)

---
**Proyecto limpio y automatizado. Frontend React + Material UI leyendo directamente de Supabase.**
- Deploy preparado para Docker Compose (local/producción).
- Acceso seguro: nunca necesitas exponer credenciales privadas en el frontend.
- Arquitectura clara: backend Python opcional, frontend desacoplado, datos en Supabase.
- Repositorio: https://github.com/VECTORG99/DataGestor
---

## Seguridad

Ver [`SECURITY.md`](SECURITY.md) para el plan completo.

**Resumen:**
- **Leyes**: GDPR (UE) y Ley 19.628 (Chile) aplicadas al tratamiento de datos.
- **Cifrado en tránsito**: TLS 1.3 en todas las conexiones externas (Supabase, BigQuery).
- **Cifrado en reposo**: AES-256 en Supabase y BigQuery por defecto.
- **Control de acceso**: Row-Level Security (RLS) en Supabase - `anon_key` solo lectura, `service_role` escritura.
- **Secretos**: `.env`, `credentials.json` y `*.local` en `.gitignore`.

## Metodología

### DataOps
El proyecto sigue principios **DataOps**: integración continua (CI/CD con GitHub Actions), automatización del pipeline ETL (Docker Compose), monitoreo de calidad (validación estructural y semántica), y métricas de rendimiento (KPIs por ejecución). Esto permite ciclos cortos de retroalimentación y detección temprana de anomalías.

### PMBOK
Se aplican los 5 grupos de procesos de **PMBOK**:

| Grupo | Aplicación en el proyecto |
|-------|--------------------------|
| Inicio | Identificación del problema: analizar datos de criminalidad en Londres para seguridad pública |
| Planificación | WBS con etapas: ingesta, limpieza, validación, carga, visualización |
| Ejecución | Implementación del pipeline Python + frontend React desplegado con Docker Compose |
| Monitoreo y Control | CI/CD (black, flake8, pytest), KPIs de latencia y calidad, logging estructurado |
| Cierre | Documentación (README, SECURITY.md), repositorio GitHub, informe técnico |

### Por que DataOps + PMBOK?
DataOps aporta agilidad y automatización al ciclo de datos; PMBOK entrega la estructura de gestión de proyectos. La combinación permite un proyecto predecible en plazos, repetible en ejecución y medible en calidad.

## Etapas del Pipeline

### 1. Ingesta y Limpieza de Datos
- Origen: Dataset público `london_crime` (BigQuery)
- Pipeline backend Python con 10 etapas de limpieza:

| # | Etapa | Función | Descripción |
|---|-------|---------|-------------|
| 1 | Estandarizar columnas | `standardize_column_names()` | Convierte nombres a snake_case |
| 2 | Manejo de nulos | `handle_null_values()` | Elimina filas con nulos en columnas críticas; reconoce `NULL`, `Unknown`, `N/A` como nulos |
| 3 | Validar tipos | `validate_data_types()` | Convierte `year`/`month` a `Int64`, `value` a `float64`, texto a `string` |
| 4 | Validar rangos | `validate_value_ranges()` | Elimina meses fuera de [1,12], anyos < 2000, valores negativos |
| 5 | Normalizar texto | `normalize_text_fields()` | Elimina espacios, título capitalizado, corrige ortografía de boroughs |
| 6 | Eliminar duplicados | `detect_and_remove_duplicates()` | Elimina filas completamente idénticas (todas las columnas) |
| 7 | Agregar crímenes | `aggregate_crime_data()` | Agrupa por `(borough, major_category, minor_category, year, month)` y suma valores |
| 8 | Crear fecha | `create_date_column()` | Crea columna `date` unificada desde `year` + `month` |
| 9 | Detectar outliers | `detect_outliers()` | Reporta valores atípicos (IQR/Z-score); no elimina por defecto |
| 10 | Eliminar columnas | `remove_unnecessary_columns()` | Conserva solo columnas relevantes |

- Generación del dataset limpio `london_crime_aggregated`.
- Herramienta: Scripts en Python, ejecutables vía Docker ("london_crime_app")
- Output: Tabla en Supabase + archivos CSV/Parquet en `data/processed/`.

### 2. Carga a la Base de Datos Analítica
- Destino: Supabase (PostgreSQL en la nube)
- Pipeline backend Python: Inserta los datos agregados en la tabla `london_crime_aggregated`.
- Reglas: Solo lectura desde el frontend, escritura protegida.

### 3. Exposición de Datos para Visualización
- En Supabase: Exposición de la información vía REST y SDKs públicos (JS).
- Seguridad: Uso exclusivo de `anon_key` (solo lectura en frontend).

### 4. Visualización & Consumo Frontend

**Tecnologías:**
- **React 19** — UI components y estado
- **Vite 8** (Rolldown) — bundler y dev server
- **Material UI 9** — diseño de componentes (Cards, Grid, Tablas, Selectores)
- **Chart.js 4** + **react-chartjs-2 5** — gráficos (barras, donut, línea)
- **Supabase JS SDK 2** — consultas a la base de datos PostgreSQL
- **Nginx** — servidor de producción del build estático

**Dashboard:**
  - KPIs: total crímenes, distrito líder, categoría principal, registros filtrados.
  - Gráficos: barras por distrito, donut por categoría, línea de tendencia temporal, top 10 subcategorías.
  - Filtros interactivos: distrito, categoría, año (actualizan todos los charts y tablas).
  - Tabla heatmap: crímenes por distrito y año.
  - Tabla detallada con datos crudos (primeros 100 registros).
  - Diseño responsive, centrado y apilado verticalmente.
- Docker Compose: Orquestación automática de frontend + backend (pipeline).
- Deploy:
  - Local: Nginx sirve la build de React.
  - Producción: Solo se necesita la URL y ANON_KEY de Supabase en el frontend (sin backend ni DB local).

### 5. Automatización y Ciclo DevOps
- Docker Compose: Reproduce y automatiza todo el stack localmente.
- CI/CD: Workflow de backend CI (black + flake8 + pytest).
- Limpieza y mantenimiento: Scripts/indicaciones para limpiar nodos, dependencias y mantener el entorno reproducible.

---

## Diagrama de Flujo Simplificado

```
Dataset Bruto (BigQuery)
     |
Ingesta y Limpieza (Python, Docker)
     |
Carga a Supabase
     |
Consulta Frontend (React SPA)
     |
Visualizacion Profesional
```
---

## 1. Descripción del Proyecto
Este repositorio contiene el diseño de arquitectura y la planificación para un sistema de gestión de datos basado en el dataset público `london_crime` de Google BigQuery. El objetivo es proporcionar una plataforma escalable para identificar focos de alta incidencia delictiva y analizar tendencias históricas en la ciudad de Londres desde el año 2008.

## 2. Arquitectura
Los datos se extraen desde **BigQuery** (Google Cloud), se procesan con el pipeline Python, se almacenan en **Supabase** (PostgreSQL) y se visualizan en un **frontend React**. No se implementa Lakehouse ni Medallion; el stack prioriza simplicidad y reproducibilidad con Docker Compose.

## 3. Instrucciones rápidas de Instalación y Uso

```bash
# 1. Clonar el repositorio
git clone https://github.com/VECTORG99/DataGestor.git
cd DataGestor

# 2. Configurar credenciales
#    Copia tus credenciales públicas de Supabase en apps/frontend/.env.local
#    (Opcional) Coloca credenciales GCP en config/credentials.json

# 3. Levantar todo con Docker Compose
docker compose -f infra/docker-compose.yml up --build -d

# 4. Abrir en navegador
#    http://localhost:5173
```

### Ejecutar el pipeline backend (opcional)
```bash
docker exec -it london_crime_app python apps/backend/cli/pipeline_dataops.py
```

## 4. Estructura del Proyecto

```
DataGestor/
|-- apps/                   # Aplicaciones
|   |-- backend/            # Codigo Python (pipeline ETL)
|   |   |-- pipeline/       #   ingestion, cleaning, loading, metrics
|   |   |-- cli/            #   pipeline_dataops.py (entrypoint)
|   |   |-- tests/          #   test_pipeline_dataops.py
|   |-- frontend/           # React SPA (Vite + Material UI + Chart.js)
|       |-- src/            #   App.jsx, main.jsx
|       |-- public/         #   Archivos estaticos
|       |-- .env.local      #   Credenciales Supabase (no subir)
|       |-- package.json
|-- config/                 # Configuracion sensible (no subir a git)
|   |-- .env.example        # Plantilla de variables de entorno
|   |-- credentials.json    # Credenciales GCP
|-- data/                   # Datos locales (no subir a git)
|   |-- raw/                # Datos originales sin procesar
|   |-- validated/          # Datos validados (reporte de calidad)
|   |-- logs/               # Logs del pipeline
|   |-- metrics/            # KPIs del pipeline (JSONL)
|   |-- processed/          # Datos limpios (CSV + Parquet) generados por el pipeline
|-- infra/                  # Infraestructura (Docker)
|   |-- backend.Dockerfile
|   |-- frontend.Dockerfile
|   |-- docker-compose.yml
|-- .github/workflows/      # CI/CD
|   |-- ci-backend.yml      # Lint + test del backend
|-- requirements.txt
|-- README.md
```

## CI/CD en GitHub Actions

| Workflow | Archivo | Disparo |
|---|---|---|
| Backend CI | `.github/workflows/ci-backend.yml` | Push/PR a `master` |

El backend CI ejecuta:
- `black --check apps/backend/` (formato)
- `flake8 apps/backend/` (lint)
- `python -m pytest apps/backend/tests/ -v` (tests unitarios)

---

## Tests

Los tests unitarios cubren cada etapa del pipeline de limpieza:

| Archivo | Tests |
|---------|-------|
| `tests/test_cleaning.py` | `standardize_column_names`, `handle_null_values`, `validate_data_types`, `validate_value_ranges`, `normalize_text_fields`, `detect_and_remove_duplicates`, `create_date_column`, `detect_outliers`, `remove_unnecessary_columns`, `clean_and_transform_data`, `validate_data_quality` |
| `tests/test_loading.py` | `save_clean_data` (CSV + Parquet) |
| `tests/test_pipeline_dataops.py` | Importación y entorno |

### Ejecutar tests localmente

```bash
# Opción 1: Directo (requiere PYTHONPATH)
PYTHONPATH=. python -m pytest apps/backend/tests/ -v

# Opción 2: Docker
docker exec london_crime_app python -m pytest apps/backend/tests/ -v

# Opción 3: Instalar pytest y ejecutar
pip install pytest && python -m pytest apps/backend/tests/ -v
```

---

## Monitoreo y KPIs

El pipeline registra automáticamente métricas de cada ejecución:

| KPI | Descripción | Ejemplo |
|-----|-------------|---------|
| Latencia | Duración por etapa (ingesta, limpieza, validación, guardado, carga) | `limpieza: 0.02s` |
| Volumen | Registros iniciales -> finales con % de reduccion | `150 -> 146 (2.7%)` |
| Completitud | % de datos no nulos en columnas críticas | `100.0%` |
| Outliers | Valores atípicos detectados (IQR) | `7` |

Los KPIs se muestran al final del pipeline y se persisten en `data/metrics/pipeline_metrics.jsonl` (una línea por ejecución).

```bash
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py --demo
# Al final muestra:
# RESUMEN DE KPIs - PIPELINE DATAOPS
#   Duracion total:  7.27 seg
#   Registros:        150 -> 146 (2.7% reduccion)
#   Completitud:      100.0%
```

---

## Escalabilidad

### Pipeline
- **Paralelización**: el pipeline puede dividirse por año o borough usando `concurrent.futures` para procesar lotes en paralelo.
- **Incremental**: los datos nuevos se agregan por fecha sin reprocesar el histórico completo (carga upsert).

### Base de datos (Supabase/PostgreSQL)
- **Índices**: crear índices en `(year, borough)` para acelerar consultas del frontend.
- **Particionamiento**: la tabla `london_crime_aggregated` puede particionarse por año.
- **Connection pooling**: Supabase usa PgBouncer para manejar cientos de conexiones concurrentes.

### Frontend
- **Filtros**: selectores de distrito, categoría y año actualizan todos los gráficos y tablas en tiempo real.
- **Caché**: implementar React Query o SWR para cachear respuestas de Supabase y evitar llamadas repetidas.
- **Paginación**: en lugar de mostrar 100 registros, usar paginación server-side con `range()` de Supabase.
- **CDN**: el build estático de Nginx puede servirse desde Cloudflare o cualquier CDN.

### Infraestructura
- **Réplicas**: Docker Compose soporta `deploy.replicas` para escalar horizontalmente el backend.
- **Orquestación**: para producción, migrar a Kubernetes (GKE) con auto-escalado vertical y horizontal.
- **Health checks**: agregar endpoint `/health` en el backend para que el orquestador monitoree disponibilidad.

### Manejo de anomalías
- **Reintentos**: el pipeline reintenta conexiones fallidas a Supabase/BigQuery con backoff exponencial.
- **Validación**: los outliers se detectan pero no se eliminan automáticamente - se reportan para decisión del analista.
- **Logs**: todos los errores se registran con timestamp y contexto para diagnóstico rápido.
- **Alertas**: integrar con Slack o email cuando el pipeline falle o los KPIs estén fuera de rango esperado.

---

## Requisitos

- **Docker** y **Docker Compose** (para el stack completo)
- **Node.js 20+** (solo para build local del frontend)
- **Python 3.9+** (solo para desarrollo del backend fuera de Docker)
- **Cuenta de Supabase** con tabla `london_crime_aggregated`
- **(Opcional) Cuenta de GCP** con acceso a BigQuery

---

## Notas de Mantenimiento

- **node_modules** no se versiona. Si clonaste el repo y necesitas desarrollo local en frontend:
  ```bash
  cd apps/frontend && npm install
  ```
- **credentials.json** y **.env** están en `.gitignore` - nunca se suben al repo.
- Para limpiar el entorno Docker:
  ```bash
  docker compose -f infra/docker-compose.yml down -v
  ```
