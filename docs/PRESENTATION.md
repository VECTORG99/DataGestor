# London Crime Data Platform — Narrativa del Proyecto

## El Problema

Los datasets públicos de criminalidad existen (London DataStore, Police UK), pero:
- Están a nivel LSOA (~1500 habitantes), difíciles de interpretar directamente.
- Requieren SQL o Python para extraer valor.
- No hay una interfaz que permita explorar visualmente tendencias históricas.

## La Solución

Una plataforma web que:
1. **Ingiere** ~3 millones de registros desde BigQuery.
2. **Limpia y agrega** los datos a nivel de borough + categoría + mes.
3. **Visualiza** tendencias, distribuciones y rankings en un dashboard interactivo.
4. **Estima** perfiles históricos de criminalidad usando ML.

## ¿Qué NO hace?

**No predice el crimen futuro.** Usamos "estimador histórico" porque el modelo:
- Se entrena con datos pasados (2008-2016).
- Usa un split aleatorio (no temporal), lo que introduce fuga de datos del futuro.
- Solo puede estimar dentro del rango de datos que conoce.
- Reporta métricas infladas artificialmente.

Esto es intencional y transparente: preferimos documentar la limitación a fingir que el sistema "predice" algo.

## Stack

- **Frontend:** React + Vite + MUI + Chart.js — dashboard responsivo con filtros y exportación a Excel.
- **Backend ML API:** FastAPI + scikit-learn — endpoint para estimaciones históricas.
- **Database:** Supabase (PostgreSQL) — datos agregados listos para consultar.
- **Pipeline ETL:** Python (BigQuery → limpieza → agregación → Supabase → entrenamiento ML).
- **Deploy:** Vercel (frontend) + Render (API) — cloud, sin servidores propios.

## ML: La Historia Real

### Iteración 1: Dashboard básico
Conexión a BigQuery, limpieza básica, primeras visualizaciones en Streamlit.

### Iteración 2: Dashboard completo
Migración a React + MUI, filtros, exportación a Excel, pipeline ETL reproducible.

### Iteración 3: ML (esta iteración)
Se agregó:
- Modelo de clasificación (LogisticRegression) para estimar incidencia alta/baja.
- Modelo de regresión (RandomForestRegressor) para estimar número de crímenes.
- UI interactiva para probar combinaciones.
- Documentación honesta de limitaciones.

### Próximos Pasos (Opciones B y C)

**Opción B — Split temporal correcto:** Reemplazar `train_test_split` aleatorio por split por año. Agregar lag features y rolling averages. Evaluación walk-forward. Esto daría métricas realistas.

**Opción C — Modelo predictivo real:** Usar Prophet, LSTM o SARIMA para predecir fuera del rango histórico (2017+). Requiere reestructurar el pipeline para modelos por serie temporal.

## Demo

1. Dashboard: https://london-crime-dashboard.vercel.app
2. API docs: https://london-crime-api.onrender.com/docs
3. Repo: (este repositorio)

## Comandos Rápidos

```bash
# Frontend local
cd apps/frontend && npm run dev

# API local
cd apps/backend && uvicorn api.predict:app --reload

# Pipeline ETL completo
cd apps/backend && python scripts/etl_pipeline.py

# Solo ML
cd apps/backend && python ml/train.py
```
