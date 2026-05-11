# Informe Técnico de Proyecto - Evaluación Parcial N°2
**Asignatura:** Gestión de Datos para IA (ITY1101)  
**Sección:** [SECCIÓN]  
**Integrantes:** [Tus Nombres y Apellidos]  

---

## Índice
1. Resumen Ejecutivo
2. Justificación de la Metodología PMBOK
3. Planificación del Proyecto (Product Backlog y Herramientas)
4. Arquitectura y Explicación del Pipeline DataOps
5. Plan de Seguridad en Entorno DataOps
6. Estrategia de KPIs de Monitoreo
7. Documentación y Evidencias de Implementación
8. Conclusiones y Próximos Pasos

---

## 1. Resumen Ejecutivo
El presente proyecto tiene como objetivo diseñar e implementar una arquitectura DataOps integral basada en el dataset público `london_crime` provisto por Google BigQuery. La solución extrae, limpia, valida y carga datos históricos de incidentes delictivos en la ciudad de Londres hacia un almacén de datos alojado en **Supabase** (PostgreSQL en la nube). Adicionalmente, se ha integrado un flujo CI/CD mediante **GitHub Actions** que automatiza el despliegue de un dashboard interactivo desarrollado en **Svelte**, permitiendo a los tomadores de decisiones visualizar los focos de alta incidencia y tendencias delictivas en tiempo real. Esta solución escalable y segura provee un alto valor estratégico para la asignación de recursos policiales.

## 2. Justificación de la Metodología PMBOK
Para la gestión de este proyecto de datos, se ha adoptado una metodología **Ágil/Adaptativa** basada en los lineamientos del PMBOK. 
* **Justificación en DataOps:** El ciclo de vida de DataOps se basa en la integración y entrega continua (CI/CD), la iteración rápida y la colaboración constante entre ingeniería de datos y negocio. Una metodología en "Cascada" sería demasiado rígida frente a cambios en la estructura de los datos o en las necesidades de visualización. El enfoque Ágil nos permite trabajar con Sprints cortos, entregar valor funcional rápidamente (como el dashboard web) y adaptar el pipeline ante anomalías o variaciones semánticas de la fuente original (BigQuery).

## 3. Planificación del Proyecto
El proyecto se dividió en historias de usuario organizadas en un **Product Backlog** gestionado mediante **Trello**. Esto permite un seguimiento visual de las tareas en formato Kanban (To Do, In Progress, Review, Done).

**Product Backlog / Roadmap Principal:**
- **Epic 1: Ingesta y Limpieza.** Conectar Google Cloud SDK en Python, extraer datos del año 2016 (por volumetría) y aplicar transformaciones (manejo de nulos, agregaciones).
- **Epic 2: Validación y Carga.** Establecer aserciones de calidad (valores positivos, consistencia de esquema) y cargar los datos limpios en Supabase vía SQLAlchemy.
- **Epic 3: Visualización (Frontend).** Construir una aplicación web SPA con Svelte + Vite que consuma el SDK de Supabase.
- **Epic 4: CI/CD y Despliegue.** Configurar GitHub Actions para el build estático y pase a producción en GitHub Pages ante cada `git push`.

## 4. Arquitectura y Explicación del Pipeline DataOps
El pipeline automatizado (`src/pipeline_dataops.py`) se compone de las 4 fases requeridas:
1. **Ingesta:** Utiliza la librería `google-cloud-bigquery` para conectar mediante *Application Default Credentials*. Ejecuta una consulta SQL para consolidar y agrupar los crímenes ocurridos durante el año 2016, extrayendo los datos a un DataFrame de Pandas en memoria.
2. **Limpieza y Transformación:** Se detectan y descartan registros nulos en las columnas críticas (`borough`, `major_category`). Posteriormente, los datos se agrupan calculando la sumatoria de incidentes y se renombran las columnas para estandarizar la nomenclatura de salida.
3. **Validación Estructural y Semántica:** Se establecen bloqueos de calidad de datos mediante `asserts` en Python.
   - *Validación Estructural:* Se verifica que las columnas de salida sean exactamente: `['municipio', 'categoria_delito', 'total_incidentes']`.
   - *Validación Semántica:* Se comprueba matemáticamente que no existan incidentes con valores menores a cero (`df['total_incidentes'] >= 0`).
4. **Carga:** Una vez que los datos pasan las pruebas, se utiliza `sqlalchemy` y `psycopg2` para inyectar los registros limpios en una tabla PostgreSQL alojada en **Supabase**. Si la tabla existe, el modelo la reemplaza para garantizar datos frescos para el dashboard.

## 5. Plan de Seguridad en Entorno DataOps
En un entorno DataOps que maneje datos reales sensibles, se deben aplicar las siguientes normativas y técnicas:
* **Normativas:** Aunque los datos de `london_crime` son públicos, en un contexto real aplicaríamos la normativa vigente de Chile sobre protección a la vida privada (**Ley N° 19.628**) y regulaciones internacionales como GDPR. Esto exige anonimizar registros identificatorios (nombres, direcciones exactas de víctimas).
* **Técnicas de Seguridad Implementadas:**
  - **Uso de Variables de Entorno (`.env`):** Las cadenas de conexión y claves API están excluidas del control de versiones (`.gitignore`), evitando exposición de credenciales en GitHub.
  - **Cifrado en tránsito y reposo:** La conexión con Supabase se realiza a través de SSL/TLS (HTTPS y PostgreSQL seguro), garantizando que los datos no puedan ser interceptados durante la fase de carga ni desde el Frontend Svelte.
  - **Control de Accesos (Row Level Security):** Supabase permite configurar políticas RLS para que solo usuarios autenticados o con el *Anon Key* tengan permisos de solo lectura (`SELECT`) a la tabla, bloqueando inyecciones o borrados externos (`INSERT/DELETE`).

## 6. Estrategia de KPIs de Monitoreo
Para asegurar la salud del pipeline DataOps, se han definido los siguientes Indicadores Clave de Rendimiento (KPIs):
- **Completitud de Datos:** Porcentaje de registros exitosamente transformados frente al total extraído (Meta: >99%).
- **Tasa de Errores de Validación:** Cantidad de veces que el pipeline falla debido a aserciones de esquema o semántica mensual (Meta: 0 fallos semanales).
- **Latencia del Pipeline:** Tiempo total transcurrido desde que el script de Python inicia la ingesta hasta que Supabase confirma el commit de la transacción final.
- **Disponibilidad del Dashboard (Uptime):** Porcentaje de tiempo que la aplicación web responde exitosamente consultas de los usuarios finales (apoyado por el SLA de GitHub Pages y Supabase).

## 7. Documentación y Evidencias
- **Repositorio GitHub:** [INSERTE LINK AL REPOSITORIO]
- **Dashboard en vivo (GitHub Pages):** [INSERTE LINK AL DASHBOARD]
- **Evidencias:** Los logs de ejecución de las 4 fases se almacenan en `logs/pipeline.log`. El archivo `Dockerfile` y `docker-compose.yml` base se mantiene para entornos locales de desarrollo. La herramienta GitHub Actions sirve de evidencia para la integración y despliegue continuo.

## 8. Conclusiones y Próximos Pasos
El enfoque DataOps adoptado garantiza la repetibilidad, trazabilidad y automatización total del ciclo de vida del dato. Al reemplazar la arquitectura de visualización tradicional por un frontend moderno y estático consumiendo APIs de manera asíncrona, se han reducido los costos de infraestructura (Serverless).
**Próximos Pasos:**
- Implementar validaciones más estrictas con herramientas especializadas como `Great Expectations`.
- Ampliar el frontend para incluir filtrado interactivo por rango de fechas (Slicers) consumiendo directamente BigQuery para consultas masivas no agregadas.
- Desarrollar un sistema de alertas proactivas (ej. Slack/Email) que notifique automáticamente si el pipeline de GitHub Actions o la ejecución del script Python arrojan un error crítico.
