# Reporte ML — Sistema de Estimación de Criminalidad (Londres)

## 1. Arquitectura General

```
BigQuery (3M filas LSOA)
    ↓ ingest
Pipeline ETL (limpieza + agregación)
    ↓
44,886 registros agregados (2008-2016)
    ↓ feature engineering
ColumnTransformer (OneHot + StandardScaler)
    ↓
LogisticRegression  ─── clasifica alta/baja incidencia
RandomForestRegressor ── estima número de delitos
    ↓
FastAPI /predict ──── sirve inferencia
    ↓
Frontend React ────── muestra resultados
```

**Stack**: Python + scikit-learn + FastAPI + React (Vite)

---

## 2. Pipeline de Datos

### 2.1 Fuente
- **BigQuery público**: `bigquery-public-data.london_crime.crime_by_lsoa`
- **~3M filas** a nivel LSOA (~1500 hab.), 2008–2016
- **Fallback**: datos sintéticos (Poisson) para demo

### 2.2 Transformaciones (cleaning.py)
| Paso | Acción |
|------|--------|
| Estandarización | columnas a minúsculas/snake_case |
| Nulos | filas con null en columnas críticas eliminadas |
| Tipos | year/month → Int64, value → float64, texto → string |
| Rangos | month 1-12, año ≥ 2000, value ≥ 0 |
| Texto | strip, title case, correcciones ortográficas |
| Duplicados | drop exactos |
| Agregación | groupBy (borough, major/minor_category, year, month) → sum(value) |

**Resultado**: 44,886 registros agregados, **1,427,544 crímenes totales**.

---

## 3. Modelo ML

### 3.1 Feature Engineering

| Feature | Tipo | Encoding |
|---------|------|----------|
| `borough` | categórica (33) | OneHot (handle_unknown="ignore") |
| `major_category` | categórica (9) | OneHot |
| `minor_category` | categórica (~60) | OneHot |
| `year` | numérica | StandardScaler |
| `month_sin` | cíclica | sin(2π·month/12) + StandardScaler |
| `month_cos` | cíclica | cos(2π·month/12) + StandardScaler |

**Total features post-encoding**: ~105 columnas (depende de categorías vistas en train).

### 3.2 Target (clasificación binaria)
- **threshold**: mediana de `total_crimes`
- `1` = delitos > mediana (alta incidencia)
- `0` = delitos ≤ mediana (baja incidencia)

### 3.3 Split
- **70/30 aleatorio estratificado** — sin respetar orden temporal

### 3.4 Modelos

#### Clasificador: LogisticRegression
| Hiperparámetro | Valor |
|----------------|-------|
| `max_iter` | 1000 |
| `random_state` | 42 |

#### Regresor: RandomForestRegressor
| Hiperparámetro | Valor |
|----------------|-------|
| `n_estimators` | 80 |
| `min_samples_leaf` | 3 |
| `n_jobs` | -1 |
| `random_state` | 42 |

### 3.5 Métricas

| Métrica | Valor | Interpretación |
|---------|-------|----------------|
| **Accuracy** | 89.02% | Acierta 89 de cada 100 |
| **Precision** | 86.45% | Cuando dice "alta", acierta 86% |
| **Recall** | 91.44% | Captura 91% de los casos de alta incidencia |
| **F1 Score** | 88.88% | Balance precision-recall |
| **ROC AUC** | 0.9634 | Excelente capacidad discriminativa |
| **Gini** | 0.9267 | Muy alta concentración (correlato de AUC) |
| **R² (regresión)** | 0.9396 | El regresor explica 94% de la varianza |
| **MAE (regresión)** | 4.38 | Error absoluto medio de ~4 delitos |

#### Matriz de Confusión

| | Pred. Bajo | Pred. Alto |
|---|---|---|
| **Real Bajo** | 10,507 (VN) | 1,598 (FP) |
| **Real Alto** | 955 (FN) | 10,198 (VP) |

---

## 4. API de Inferencia

- **Framework**: FastAPI
- **Puerto**: 8000 (configurable vía env)
- **Carga**: lazy-load al primer request

### Endpoint `/predict`
```
POST /predict
{
  "borough": "Camden",
  "major_category": "Violence Against the Person",
  "minor_category": "Assault with injury",
  "year": 2016,
  "month": 6
}
```
**Response**:
```json
{
  "prediction": 1,
  "probability_high": 0.87,
  "probability_low": 0.13,
  "predicted_crimes": 42,
  "predicted_crimes_raw": 42.3,
  "threshold": 0.5,
  "features_used": 105
}
```

---

## 5. Frontend (React)

### Página "ML Insights"
- 6 tarjetas de métricas (Accuracy, Precision, Recall, F1, AUC, Gini)
- Matriz de confusión visual
- Curva ROC en SVG inline con datos del frontend JSON
- Datos servidos desde `/ml/ml_metrics.json` (static file)

### Página "Estimador Histórico"
- 5 selectores (borough, categoría, subcategoría, año, mes)
- Botón "Estimar" → POST a FastAPI
- Resultado: delitos estimados, clasificación ALTA/BAJA, barras de probabilidad
- Alertas de limitación del modelo (data leakage)

---

## 6. Hallazgos y Riesgos Identificados

### 🔴 Críticos

| # | Problema | Impacto | Recomendación |
|---|----------|---------|---------------|
| 1 | **Data leakage por split aleatorio** | Accuracy ~89% y R² ~0.94 inflados artificialmente. El modelo aprende de datos futuros para predecir pasados. | Usar split **temporal** (train: 2008-2014, test: 2015-2016). Las métricas reales serán menores. |
| 2 | **Sin features espacio-temporales** | Borough es OneHot plano; no hay: coordenadas, cluster geográfico, lag de meses anteriores, tendencias, estacionalidad aprendida. | Agregar features derivadas: crímenes del mes anterior por borough, media móvil 3m, coordenadas, día de semana. |

### 🟡 Importantes

| # | Problema | Impacto | Recomendación |
|---|----------|---------|---------------|
| 3 | **Sin validación cruzada** | Las métricas dependen de un solo split 70/30. Alta varianza en la estimación. | Agregar CV estratificada (k=5) y reportar media ± std. |
| 4 | **Sin búsqueda de hiperparámetros** | LogisticRegression con valores por defecto (max_iter=1000). RF con 80 árboles sin tuning. | GridSearchCV o RandomizedSearchCV para RF (n_estimators, max_depth, min_samples_split). |
| 5 | **RandomForestRegressor sobredimensionado** | 80 árboles con 105 features para predecir conteos discretos. Posible sobreajuste a datos de entrenamiento. | Evaluar modelos más simples: Ridge, PoissonRegressor, o GradientBoosting con early stopping. |

### 🟢 Mejoras

| # | Problema | Impacto | Recomendación |
|---|----------|---------|---------------|
| 6 | **Sin experiment tracking** | No hay registro de versiones de modelo, métricas históricas, o comparación entre iteraciones. | MLflow básico o log de métricas con timestamp + hash de features. |
| 7 | **Sin feature importance** | No se sabe qué boroughs/categorías pesan más en la decisión. | SHAP o permutation importance en el reporte. |
| 8 | **Datos 2008-2016 desactualizados** | El dataset termina en 2016. Londres cambió significativamente. | Actualizar con datos más recientes (2016-2024). |
| 9 | **Dos JSON duplicados** | `ml_metrics.json` existe en `data/metrics/` y `frontend/public/ml/` con diferente schema (el frontend agrega roc_curve). | Unificar: el pipeline debería generar el JSON completo incluyendo roc_curve para eliminar la copia manual. |
| 10 | **Sin monitoreo de drift** | No hay detección de concept drift si la distribución de crímenes cambia. | Agregar chequeo periódico de distribución de features vs. entrenamiento. |

---

## 7. Recomendaciones Prioritarias

### Corto plazo (1-2 sprints)
1. **Split temporal**: cambiar `train_test_split(random)` por corte por año (train ≤ 2014, test ≥ 2015). Las métricas bajarán pero serán **reales**.
2. **Agregar lag features**: para cada borough+categoría, incluir `crimes_last_month`, `avg_last_3_months`. Esto capturará autocorrelación temporal.
3. **Unificar JSON de métricas**: que el pipeline genere el JSON completo (con roc_curve) directamente en `frontend/public/ml/`.

### Mediano plazo (3-4 sprints)
4. **Cross-validation + grid search**: evaluar estabilidad del modelo y optimizar hiperparámetros.
5. **SHAP analysis**: generar reporte de importancia de features por borough y categoría.
6. **Endpoint de diagnóstico**: agregar `/model_info` que devuelva hiperparámetros, fecha de entrenamiento, features usadas.

### Largo plazo
7. **Modelos más avanzados**: GradientBoosting (XGBoost/LightGBM) para mejor accuracy, o modelos secuenciales si hay suficientes datos temporales.
8. **Pipeline de reentrenamiento automático**: CI/CD que reentrene con nuevos datos y valide métricas antes de desplegar.

---

## 8. Resumen Técnico

```
Modelos:          LogisticRegression + RandomForestRegressor
Features:         6 → ~105 (post-encoding)
Registros train:  31,420 (70%)
Registros test:   13,466 (30%)
Accuracy:         89.02%
ROC AUC:          0.9634
R² (regresión):   0.9396
API:              FastAPI :8000
Frontend:         React + Vite
Datos:            BigQuery londinense 2008-2016
```

El sistema actual funciona como **estimador histórico** (no predictor futuro) con métricas artificialmente infladas por data leakage temporal. La arquitectura es sólida para un MVP, pero las métricas reportadas no reflejan el rendimiento en producción real.
