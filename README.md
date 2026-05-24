# Sistema de Inteligencia Territorial para la Seguridad Pública en Londres

[![CI Backend](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml/badge.svg)](https://github.com/VECTORG99/DataGestor/actions/workflows/ci-backend.yml)

---
**Proyecto limpio y automatizado. Frontend React + Material UI leyendo directamente de Supabase.**
- Deploy preparado para Docker Compose (local/producción) y Github Pages (estático, solo frontend).
- Acceso seguro: nunca necesitas exponer credenciales privadas en el frontend.
- Arquitectura clara: backend Python opcional, frontend desacoplado, datos en Supabase.
- Repositorio: https://github.com/VECTORG99/DataGestor
---

## Etapas del Pipeline

### 1. Ingesta y Limpieza de Datos
- Origen: Dataset público `london_crime` (BigQuery)
- Pipeline backend Python con 9 etapas de limpieza:

| # | Etapa | Función | Descripción |
|---|-------|---------|-------------|
| 1 | Estandarizar columnas | `standardize_column_names()` | Convierte nombres a snake_case |
| 2 | Manejo de nulos | `handle_null_values()` | Elimina filas con nulos en columnas críticas; reconoce `NULL`, `Unknown`, `N/A` como nulos |
| 3 | Validar tipos | `validate_data_types()` | Convierte `year`/`month` a `Int64`, `value` a `float64`, texto a `string` |
| 4 | Validar rangos | `validate_value_ranges()` | Elimina meses ∉ [1,12], años < 2000, valores negativos |
| 5 | Normalizar texto | `normalize_text_fields()` | Elimina espacios, título capitalizado, corrige ortografía de boroughs |
| 6 | Eliminar duplicados | `detect_and_remove_duplicates()` | Elimina duplicados exactos y por combinación `(borough, major_category, year, month)` |
| 7 | Crear fecha | `create_date_column()` | Crea columna `date` unificada desde `year` + `month` |
| 8 | Detectar outliers | `detect_outliers()` | Reporta valores atípicos (IQR/Z-score); no elimina por defecto |
| 9 | Eliminar columnas | `remove_unnecessary_columns()` | Conserva solo columnas relevantes |

- Generación del dataset limpio `london_crime_aggregated`.
- Herramienta: Scripts en Python, ejecutables vía Docker (“london_crime_app”)
- Output: Tabla en Supabase + archivos CSV/Parquet en `data/processed/`.

### 2. Carga a la Base de Datos Analítica
- Destino: Supabase (PostgreSQL en la nube)
- Pipeline backend Python: Inserta los datos agregados en la tabla `london_crime_aggregated`.
- Reglas: Solo lectura desde el frontend, escritura protegida.

### 3. Exposición de Datos para Visualización
- En Supabase: Exposición de la información vía REST y SDKs públicos (JS).
- Seguridad: Uso exclusivo de `anon_key` (solo lectura en frontend).

### 4. Visualización & Consumo Frontend
- Frontend React profesional:
  - SPA creada con Vite y Material UI.
  - Consulta Supabase con `@supabase/supabase-js` y muestra tabla dinámica.
  - Opción para agregar más features (filtros, paginación, charts).
- Docker Compose: Orquestación automática de frontend + backend (pipeline) + db.
- Deploy:
  - Local: Nginx sirve la build de React.
  - Producción: Opcional despliegue estático en Github Pages (consume Supabase directamente, no requiere backend ni db propios).

### 5. Automatización y Ciclo DevOps
- Docker Compose: Reproduce y automatiza todo el stack localmente.
- CI/CD: Workflow de backend CI (black + flake8) y workflow para deploy a Github Pages.
- Limpieza y mantenimiento: Scripts/indicaciones para limpiar nodos, dependencias y mantener el entorno reproducible.

---

## Diagrama de Flujo Simplificado

```
Dataset Bruto (BigQuery)
     ↓
Ingesta & Limpieza (Python, Docker)
     ↓
Carga a Supabase
     ↓
Consulta Frontend (React SPA)
     ↓
Visualización Profesional
```
---

## 1. Descripción del Proyecto
Este repositorio contiene el diseño de arquitectura y la planificación para un sistema de gestión de datos basado en el dataset público `london_crime` de Google BigQuery. El objetivo es proporcionar una plataforma escalable para identificar focos de alta incidencia delictiva y analizar tendencias históricas en la ciudad de Londres desde el año 2008.

## 2. Arquitectura Seleccionada 
Se ha implementado una arquitectura **Lakehouse** sobre la plataforma Google Cloud (GCP).
*   **Justificación:** Combina la flexibilidad de un Data Lake (Cloud Storage) con el rendimiento analítico de un Data Warehouse (BigQuery). Ideal para integrar visualización (Looker) y analítica avanzada (IA/ML) sin redundancia.
*   **Capas de Datos:** Siguiendo el patrón Medallion (Bronce, Plata, Oro).

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
├── apps/                   # Aplicaciones
│   ├── backend/            # Código Python (pipeline ETL)
│   │   ├── pipeline/       #   ingestion, cleaning, loading
│   │   ├── cli/            #   pipeline_dataops.py (entrypoint)
│   │   └── tests/          #   test_pipeline_dataops.py
│   └── frontend/           # React SPA (Vite + Material UI)
│       ├── src/            #   App.jsx, main.jsx
│       ├── public/         #   favicon, icons
│       ├── .env.local      #   Credenciales Supabase (no subir)
│       └── package.json
├── config/                 # Configuración sensible (no subir a git)
│   ├── .env.example        # Plantilla de variables de entorno
│   └── credentials.json    # Credenciales GCP
├── data/                   # Datos locales (no subir a git)
│   ├── logs/               # Logs del pipeline
│   ├── outputs/            # Outputs generados
│   └── processed/          # Datos limpios (CSV + Parquet) generados por el pipeline
├── infra/                  # Infraestructura (Docker)
│   ├── backend.Dockerfile
│   ├── frontend.Dockerfile
│   └── docker-compose.yml
├── .github/workflows/      # CI/CD
│   ├── ci-backend.yml      # Lint + test del backend
│   └── deploy.yml          # Deploy a Github Pages
├── requirements.txt
└── README.md
```

## Despliegue en Github Pages

El frontend es una SPA 100% estática que puede funcionar sin backend ni Docker. Para desplegar:

```bash
cd apps/frontend
npm install
npm run build
```

Esto genera `apps/frontend/dist/`. Luego puedes:

1. **Subir manualmente** la carpeta `dist/` a la rama `gh-pages`
2. **Usar el workflow incluido** en `.github/workflows/deploy.yml` — configúralo agregando los secrets `VITE_SUPABASE_URL` y `VITE_SUPABASE_ANON_KEY` en tu repositorio de GitHub.

```yaml
# .github/workflows/deploy.yml (ya incluido en el repo)
name: Deploy React App to GitHub Pages
on:
  push:
    branches: [master]
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: |
          cd apps/frontend
          npm ci
          echo "VITE_SUPABASE_URL=${{ secrets.VITE_SUPABASE_URL }}" >> .env
          echo "VITE_SUPABASE_ANON_KEY=${{ secrets.VITE_SUPABASE_ANON_KEY }}" >> .env
          npm run build
      - uses: peaceiris/actions-gh-pages@v4
        with:
          personal_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./apps/frontend/dist
```

3. Configurar Github Pages en **Settings → Pages** para servir desde `gh-pages`.

> El backend solo es necesario para procesamiento. En producción basta la URL y ANON_KEY de Supabase en el frontend (sin backend ni DB local).

---

## CI/CD en GitHub Actions

| Workflow | Archivo | Disparo |
|---|---|---|
| Backend CI | `.github/workflows/ci-backend.yml` | Push/PR a `master` |
| Deploy Pages | `.github/workflows/deploy.yml` | Push a `master` |

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

## Requisitos

- **Docker** y **Docker Compose** (para el stack completo)
- **Node.js 20+** (solo para build local del frontend)
- **Python 3.9+** (solo para desarrollo del backend fuera de Docker)
- **Cuenta de Supabase** con tabla `london_crime_aggregated`
- **(Opcional) Cuenta de GCP** con acceso a BigQuery

## 5. Casos de Análisis SQL

Ejemplos de consultas sobre el dataset `london_crime` en BigQuery:

### A. Rango de Fechas
```sql
SELECT 
    MIN(year) as primer_año, 
    MAX(year) as ultimo_año 
FROM `bigquery-public-data.london_crime.crime_by_lsoa`;
```

### B. Crímenes por Año y Categoría
```sql
SELECT
year,
COUNT(CASE WHEN major_category = 'Violence Against the Person' THEN 1 END) AS Crimenes_Violentos,
COUNT(CASE WHEN major_category = 'Theft and Handling' THEN 1 END) AS Robos_Hurtos,
SUM(value) as total_incidentes
FROM `bigquery-public-data.london_crime.crime_by_lsoa`
GROUP BY year
ORDER BY year DESC;
```

### C. Top 10 Municipios con Más Crímenes
```sql
SELECT 
    borough, 
    SUM(value) as total_crimenes
FROM `bigquery-public-data.london_crime.crime_by_lsoa`
GROUP BY borough
ORDER BY total_crimenes DESC
LIMIT 10;
```

---

## Notas de Mantenimiento

- **node_modules** no se versiona. Si clonaste el repo y necesitas desarrollo local en frontend:
  ```bash
  cd apps/frontend && npm install
  ```
- **credentials.json** y **.env** están en `.gitignore` — nunca se suben al repo.
- Para limpiar el entorno Docker:
  ```bash
  docker compose -f infra/docker-compose.yml down -v
  ```
