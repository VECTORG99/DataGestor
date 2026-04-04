# Sistema de Inteligencia Territorial para la Seguridad Pública en Londres

## 1. Descripción del Proyecto
Este repositorio contiene el diseño de arquitectura y la planificación para un sistema de gestión de datos basado en el dataset público `london_crime` de Google BigQuery. El objetivo es proporcionar una plataforma escalable para identificar focos de alta incidencia delictiva y analizar tendencias históricas en la ciudad de Londres desde el año 2008.

## 2. Arquitectura Seleccionada (IL 1.2)
Se ha implementado una arquitectura **Lakehouse** sobre la plataforma Google Cloud (GCP).
*   **Justificación:** Combina la flexibilidad de un Data Lake (Cloud Storage) con el rendimiento analítico de un Data Warehouse (BigQuery). Ideal para integrar visualización (Looker) y analítica avanzada (IA/ML) sin redundancia.
*   **Capas de Datos:** Siguiendo el patrón Medallion (Bronce, Plata, Oro).

## 3. Configuración del Entorno Virtual (IL 1.3)
Para garantizar la reproductibilidad del entorno, el proyecto utiliza **Docker** y **Docker Compose**.

### Requisitos Técnicos
*   Docker Desktop (Windows/Mac) o Docker Engine (Linux).
*   Docker Compose V2+.
*   Cuenta de Google Cloud con acceso a BigQuery.

### Instrucciones de Instalación
Siga estos pasos para levantar el entorno de desarrollo:

1.  **Construir la imagen:**
    ```bash
    docker-compose build
    ```
2.  **Levantar los servicios:**
    ```bash
    docker-compose up -d
    ```
3.  **Acceder al contenedor de la aplicación:**
    ```bash
    docker exec -it london_crime_app /bin/bash
    ```
    *Aquí dentro podrá ejecutar el Google Cloud SDK y scripts de Python.*

4.  **Autenticación en GCP:** (Dentro del contenedor)
    ```bash
    gcloud auth application-default login
    ```

## 4. Estructura del Repositorio (IL 1.3)
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

## 5. Casos de Análisis SQL (Bonus)
En la carpeta `/sql/` se encuentran scripts adaptados para analizar:
*   Rangos históricos de datos.
*   Distribución de crímenes por categoría y año.
*   Top 10 distritos con mayor tasa de incidentes.
