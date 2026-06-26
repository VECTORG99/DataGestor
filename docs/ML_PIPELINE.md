# ML Pipeline — London Crime Historical Estimator

## TL;DR

**Esto NO es un predictor del futuro.** El modelo aprende el perfil histórico del dataset 2008-2016 y estima criminalidad para una combinación `(borough, major_category, minor_category, year, month)` dentro del rango histórico. Usa un **split temporal correcto** (train ≤ 2014, test ≥ 2015) — sin fuga temporal. Para predicción real 2017+ ver [Opciones de evolución](#opciones-de-evolución).

> **Auditoría 2026-06:** se eliminaron las lag features (`crimes_last_month`, `avg_last_3_months`) que (1) derivaban del target y por tanto inflaban métricas con autocorrelación mes-a-mes, y (2) rompían la inferencia single-row de la API (el preprocessor esperaba 8 columnas, la API mandaba 6 → `ValueError` en todo `/predict`). El modelo ahora entrena con exactamente las 6 features disponibles en inferencia.

---

## Auditoría de calidad (hallazgos resueltos)

| # | Hallazgo | Severidad | Estado |
|---|----------|-----------|--------|
| 1 | `/predict` crasheaba: preprocessor esperaba `crimes_last_month`, `avg_last_3_months` que la API no provee | **Crítico (producción rota)** | ✅ removidas |
| 2 | Lag features derivadas del target inflaban métricas vía autocorrelación | **Fuga de datos** | ✅ removidas |
| 3 | Métricas previas (acc 0.93 / R² 0.97) eran trampa del item 2 | **Desinformación** | ✅ métricas honestas |
| 4 | Split random 70/30 mezclaba años (fuga temporal) | Medio | ✅ split temporal corregido antes |
| 5 | Demo data usaba años 2016-2019 → split temporal daba 0 train rows | Bloqueo CI | ✅ `SAMPLE_YEARS` = 2008-2016 |

### Métricas honestas (post-fix, temporal split 2008-2014 / 2015-2016)

| Métrica | Valor | Nota |
|---------|-------|------|
| Accuracy | 0.8913 | Sin fuga lag, solo 6 features |
| Precision | 0.9057 | |
| Recall | 0.8657 | |
| F1 Score | 0.8852 | |
| ROC AUC | 0.9677 | |
| Gini | 0.9355 | |
| R² (regresión) | 0.9097 | |
| MAE (regresión) | 5.7645 | |

---

## Arquitectura del ML

```
data/processed/london_crime_aggregated.csv
    │
    ▼
apps/backend/cli/ml_pipeline.py
    │
    ├── Carga CSV procesado
    ├── apps/backend/ml/preprocessing.py
    │     ├── cyclical_encode_month → month_sin, month_cos
    │     ├── prepare_features → 6 cols (borough, major_category,
    │     │                        minor_category, year, month_sin, month_cos)
    │     ├── create_classification_target: 1 si total_crimes > mediana, 0 si no
    │     └── temporal split: train year ≤ 2014, test year ≥ 2015
    │        (fallback a random split si el train queda vacío)
    ├── OneHotEncoder + StandardScaler (ColumnTransformer)
    ├── Entrena LogisticRegression (clasificación)
    ├── Entrena RandomForestRegressor (regresión sobre total_crimes)
    └── Guarda modelos en data/models/
         ├── logistic_regression.joblib
         ├── crime_regressor.joblib
         └── preprocessor.joblib
```

## Features (consistencia train ↔ inferencia)

El modelo usa **exactamente** las 6 features que la API puede proveer:

```
borough, major_category, minor_category, year, month_sin, month_cos
```

Sin lag features. Sin features derivadas del target. Train e inferencia son idénticos en columnas.

## Files

| Archivo | Propósito |
|---------|-----------|
| `apps/backend/cli/ml_pipeline.py` | Orquestador (carga, entrena, guarda, métricas) |
| `apps/backend/ml/classification.py` | LogisticRegression + RandomForestRegressor + métricas |
| `apps/backend/ml/preprocessing.py` | Feature engineering + split + ColumnTransformer |
| `apps/backend/api/predict.py` | FastAPI `/predict` (envía las 6 cols al preprocessor) |
| `data/models/*.joblib` | Modelos serializados |
| `apps/frontend/public/ml/ml_metrics.json` | Métricas para el dashboard |

### Código eliminado en la auditoría

- `add_lag_features()` — lag features derivadas del target, rotas para inferencia
- `preprocess_and_split()` (random split) — reemplazado por `temporal_preprocess_and_split`; solo subsiste como fallback interno ante split temporal vacío
- Lag features de los tests (`crimes_last_month`, `avg_last_3_months`)

---

## Modelo de Clasificación (LogisticRegression)

### Target
```python
median_crimes = df["total_crimes"].median()
df["target_binary"] = (df["total_crimes"] > median_crimes).astype(int)
```
- **1** = incidencia alta (por encima de la mediana)
- **0** = incidencia baja

### Features (one-hot encoded, ~67 columnas tras encoding)
- `borough` (32 distritos)
- `major_category` (9 categorías)
- `minor_category` (~65 subcategorías)
- `year` (escalado)
- `month_sin`, `month_cos` (mes cíclico)

---

## Modelo de Regresión (RandomForestRegressor)

### Target
- `total_crimes` — número de crímenes para ese grupo (borough, category, year, month)

### Features
- Mismas 6 que clasificación

> ⚠️ **RandomForest no extrapola.** Si pedís un `year` fuera del rango de entrenamiento (2008-2014), el regresor devuelve el promedio del leaf más cercano, no una extrapolación. Predicciones para años > 2014 ya son menos confiables; para 2017+ son básicamente el promedio histórico.

---

## Limitaciones (honestas)

### 1. RandomForest no extrapola fuera del rango de entrenamiento
Train = 2008-2014. El regresor no puede producir valores razonables para años fuera de ese rango — devuelve el promedio de un leaf. Esto afecta `predicted_crimes` en el endpoint. El clasificador (LogisticRegression) sí responde razonablemente porque los one-hot de borough/category capturan estructura estable.

### 2. Sin features temporales reales (lag/rolling)
Se removieron porque no son providables en inferencia single-row. Para usarlos correctamente, la API debería consultar Supabase por el mes anterior. Queda como [Opción B](#opciones-de-evolución).

### 3. Threshold global (mediana)
La mediana de `total_crimes` define "alto vs bajo". El 75% de los grupos tienen ≤3 crímenes/mes, entonces "alto" significa >3. Un clasificador naive "siempre bajo" ya da ~75% accuracy. Nuestro 89% supera eso pero sigue siendo condicionado por el threshold global.

### 4. Rango fijo 2008-2016
El modelo estima dentro del rango histórico. Para predicción 2017+ real, migrar a modelo de series temporales (ver Opción C).

### 5. El split temporal sigue sin ser walk-forward
El split actual es un corte único en 2014. Un walk-forward (entrenar en 2008-2013, validar 2014, reentrenar 2008-2015, validar 2016) daría estimaciones de generalización más robustas, pero acá solo reportamos una ventana.

---

## Entrenamiento Automatizado

El entrenamiento ML corre **automáticamente** en GitHub Actions:

| Workflow | Trigger | Data source |
|----------|---------|-------------|
| `etl-pipeline.yml` (job `ml-training`) | 1ro de cada mes (post-ETL) | CSV fresco del job ETL |
| `ml-training.yml` (standalone) | cada 3 días | CSV commiteado en repo |

Ambos entrenan, commitean `ml_metrics.json` y suben `.joblib` al release `ml-models-latest` (consumido por el Dockerfile de Render).

## Entrenamiento Local

```bash
python -m apps.backend.cli.ml_pipeline

# Probar endpoint (requiere API corriendo)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"borough": "Westminster", "major_category": "Theft and Handling",
       "minor_category": "Theft From Shop", "year": 2016, "month": 6}'
```

---

## Opciones de evolución

### Opción B — Lag features reales con DBlookup en inferencia
Hacer que `/predict` consulte Supabase por el mes anterior del mismo (borough, category) y compute `crimes_last_month` server-side. Reentrenar con lag. Más trabajo, pero captura autocorrelación sin fuga.

### Opción C — Modelo predictivo real (2017+)
Migrar a Prophet / SARIMA / LSTM por serie `(borough, category)`. Reestructura el pipeline (un modelo por serie o jerárquico). El estimador actual pasa a ser solo descriptivo histórico.