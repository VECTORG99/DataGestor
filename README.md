# Sistema de Inteligencia Territorial para la Seguridad Pública en Londres

## 1. Descripción del Proyecto
Este repositorio contiene el diseño de arquitectura y la planificación para un sistema de gestión de datos basado en el dataset público `london_crime` de Google BigQuery. El objetivo es proporcionar una plataforma escalable para identificar focos de alta incidencia delictiva y analizar tendencias históricas en la ciudad de Londres desde el año 2008.

## 2. Arquitectura Seleccionada 
Se ha implementado una arquitectura **Lakehouse** sobre la plataforma Google Cloud (GCP).
*   **Justificación:** Combina la flexibilidad de un Data Lake (Cloud Storage) con el rendimiento analítico de un Data Warehouse (BigQuery). Ideal para integrar visualización (Looker) y analítica avanzada (IA/ML) sin redundancia.
*   **Capas de Datos:** Siguiendo el patrón Medallion (Bronce, Plata, Oro).

## 3. Configuración del Entorno Virtual 
Para garantizar la reproductibilidad del entorno, el proyecto utiliza **Docker** y **Docker Compose**.

### Requisitos Técnicos
*   Docker Desktop (Windows/Mac) o Docker Engine (Linux).
*   Docker Compose V2+.
*   Cuenta de Google Cloud con acceso a BigQuery.

### Instrucciones de Instalación
Siga estos pasos para levantar el entorno de desarrollo optimizado para DataOps:

1.  **Autenticación en GCP (En tu máquina local):**
    Antes de levantar el entorno Docker, asegúrate de estar autenticado en Google Cloud desde la terminal de tu computador (Windows/Mac/Linux):
    ```bash
    gcloud auth application-default login
    ```
    *Nota: Docker Compose está configurado para tomar estas credenciales locales (`~/.config/gcloud`) y montarlas en el contenedor, por lo que ya no es necesario instalar el SDK de Google pesado dentro de la imagen.*

2.  **Configuración de Supabase:**
    Asegúrate de haber creado tu archivo `.env` en la raíz del proyecto basándote en el archivo `.env.example`.

3.  **Construir la imagen:**
    ```bash
    docker-compose build
    ```
4.  **Levantar los servicios:**
    ```bash
    docker-compose up -d
    ```
5.  **Ejecutar el Pipeline DataOps:**
    ```bash
    docker exec -it london_crime_app python src/pipeline_dataops.py
    ```

## 4. Estructura del Repositorio 
```text
├── docs/                 # Documentación de diseño y justificación.
│   ├── arquitectura_y_tecnologia.md
│   └── diseño_tecnico.md
├── sql/                  # Scripts de procesamiento Medallion.
│   └── analisis_london_crime.sql
├── plan_gestion/         # Archivos de planificación PMBOK/WBS.
│   └── plan_gestion_y_seguimiento.md
├── Dockerfile            # Configuración del entorno Python + GCloud SDK.
├── docker-compose.yml    # Orquestación de App y PostgreSQL.
├── requirements.txt      # Dependencias de Python.
└── README.md             # Documento principal.
```

## 5. Casos de Análisis SQL
En la carpeta `/sql/` se encuentran los scripts detallados. A continuación, se muestran los ejemplos principales:

### A. Rango de Fechas
Identifica el periodo histórico cubierto por el dataset.
```sql
SELECT 
    MIN(year) as primer_año, 
    MAX(year) as ultimo_año 
FROM `bigquery-public-data.london_crime.crime_by_lsoa`;
```

### B. Crímenes por Año y Categoría
Clasifica los crímenes en violencia vs robo/otros.
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
Identifica los distritos con mayor incidencia delictiva.
```sql
SELECT 
    borough, 
    SUM(value) as total_crimenes
FROM `bigquery-public-data.london_crime.crime_by_lsoa`
GROUP BY borough
ORDER BY total_crimenes DESC
LIMIT 10;
```
