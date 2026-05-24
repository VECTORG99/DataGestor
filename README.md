# Sistema de Inteligencia Territorial para la Seguridad Pública en Londres

---
**Proyecto limpio y automatizado. Frontend React + Material UI leyendo directamente de Supabase.**
- Deploy preparado para Docker Compose (local/producción) y Github Pages (estático, solo frontend).
- Acceso seguro: nunca necesitas exponer credenciales privadas en el frontend.
- Arquitectura clara: backend Python opcional, frontend desacoplado, datos en Supabase.
---

## Etapas del Pipeline

### 1. Ingesta y Limpieza de Datos
- Origen: Dataset público `london_crime` (BigQuery)
- Pipeline backend Python:
  - Descarga del dataset bruto, limpieza de datos nulos/inconsistentes.
  - Transformaciones: agregaciones por año, categoría, municipio.
  - Generación del dataset limpio `london_crime_aggregated`.
- Herramienta: Scripts en Python, ejecutables vía Docker (“london_crime_app”)
- Output: Archivo/tablas limpias y listas para carga a base de datos analítica.

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
  - Consulta Supabase con `@supabase/supabase-js` y muestra tabla “inteligente”.
  - Opción para agregar más features (filtros, paginación, charts).
- Docker Compose: Orquestación automática de frontend + backend (pipeline) + db.
- Deploy:
  - Local: Nginx sirve la build de React.
  - Producción: Opcional despliegue estático en Github Pages (consume Supabase directamente, no requiere backend ni db propios).

### 5. Automatización y Ciclo DevOps
- Docker Compose: Reproduce y automatiza todo el stack localmente.
- Limpieza y mantenimiento: Scripts/indicaciones para limpiar nodos, dependencias y mantener el entorno reproducible.
- (Opcional) CI/CD: Configurable para autodeploy en Github Pages (frontend), con secrets seguros y setup reproducible.

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

1. Copia tus credenciales públicas de Supabase (URL y ANON_KEY) en `apps/frontend/.env.local`.
2. (Opcional) Coloca credenciales GCP en `config/credentials.json` si ejecutas pipeline backend DataOps.
3. Levanta todo con Docker Compose:
   ```bash
   docker-compose -f infra/docker-compose.yml up --build -d
   ```
4. Accede a http://localhost:5173 en tu navegador para ver tus datos limpios.

5. (Opcional, backend/pipeline):
   ```bash
   docker exec -it london_crime_app python apps/backend/cli/pipeline_dataops.py
   ```

## 4. Estructura del Proyecto (Actualizada)

```
DataGestor/
├── docs/                  # Documentación técnica 
├── apps/                  # Apps (backend + frontend)
│    ├── backend/          # Código Python: pipeline, limpieza, carga, tests
│    └── frontend/         # Frontend React para Supabase
├── config/                # Configuración local (no subir a git)
│    └── credentials.json
├── data/                  # Logs y outputs locales
│    ├── logs/
│    └── outputs/
├── infra/                 # Infraestructura (Dockerfiles/Compose)
│    ├── backend.Dockerfile
│    ├── frontend.Dockerfile
│    └── docker-compose.yml
├── requirements.txt
└── README.md
```

## ¿Cómo desplegar el frontend en Github Pages? ️

1. Construye el frontend localmente:
    ```bash
    cd apps/frontend
    npm install
    npm run build
    ```
    Esto deja `/apps/frontend/dist/` listo para deploy.

2. Sube a la rama `gh-pages`. Lo más fácil: usa [peaceiris/actions-gh-pages](https://github.com/peaceiris/actions-gh-pages) en Github Actions:

    *Ejemplo de workflow Github Actions (en .github/workflows/deploy-pages.yml):*
    ```yaml
    name: Deploy React Frontend to Github Pages
    on:
      push:
        branches:
          - main
    jobs:
      build-and-deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout code
            uses: actions/checkout@v4
          - name: Setup Node.js
            uses: actions/setup-node@v4
            with:
              node-version: 20
          - name: Install dependencies
            run: |
              cd apps/frontend
              npm ci
          - name: Build
            run: |
              cd apps/frontend
              npm run build
          - name: Deploy to Github Pages
            uses: peaceiris/actions-gh-pages@v4
            with:
              personal_token: ${{ secrets.GITHUB_TOKEN }}
              publish_dir: ./apps/frontend/dist
    ```
3. Configura Pages en el repo para servir desde la rama gh-pages.

- El backend sólo es necesario para procesamiento, el frontend funciona 100% estático con acceso seguro solo lectura.
- En producción: basta la URL y ANON_KEY de Supabase en el frontend (sin backend ni DB local).

---

## Limpieza de residuos

No quedan archivos basura/patrones demo de frameworks. Si ejecutas local y deseas limpiar espacio:
Ve a /apps/frontend y ejecuta:
```
rm -rf node_modules
```
Siempre puedes restaurar dependencias con:
```
npm install
```

---

## 5. Casos de Análisis SQL

En la carpeta `/sql/` se encuentran los scripts detallados. A continuación, ejemplos principales:

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
