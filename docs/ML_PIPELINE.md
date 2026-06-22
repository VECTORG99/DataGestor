# ML Pipeline — London Crime Historical Estimator

## TL;DR

**Esto NO es un predictor del futuro.** El modelo aprende patrones del dataset histórico (2008-2016) y estima el perfil de criminalidad para una combinación de (borough, category, month, year) dentro del rango de datos. El split de entrenamiento es aleatorio 70/30, lo que introduce **fuga temporal**: el modelo aprende de datos "futuros" para estimar datos "pasados", inflando artificialmente las métricas.

---

## Arquitectura del ML

```
data/processed/london_crime_aggregated.csv
    │
    ▼
apps/backend/cli/ml_pipeline.py
    │
    ├── Carga CSV procesado desde data/processed/
    ├── Usa apps/backend/ml/preprocessing.py → features + preprocessor sklearn Pipeline
    ├── Crea target_binary: 1 si total_crimes > mediana (3), 0 si no
    ├── One-hot encode + StandardScaler
    ├── Split aleatorio 70/30 — ⚠️ fuga temporal
    ├── Entrena LogisticRegression (clasificación) via ml/classification.py
    ├── Entrena RandomForestRegressor (regresión)
    └── Guarda modelos en data/models/
         ├── logistic_regression.joblib
         ├── crime_regressor.joblib
         └── preprocessor.joblib
```

## Files

| Archivo | Propósito |
|---------|-----------|
| `apps/backend/cli/ml_pipeline.py` | Orquestador de entrenamiento (carga datos, entrena, guarda) |
| `apps/backend/ml/classification.py` | LogisticRegression + RandomForestRegressor |
| `apps/backend/ml/preprocessing.py` | Feature engineering + Pipeline sklearn (ColumnTransformer) |
| `apps/backend/api/predict.py` | Endpoint FastAPI `/predict` que sirve los modelos |
| `data/models/*.joblib` | Modelos serializados (regenerables localmente) |
| `apps/frontend/public/ml/ml_metrics.json` | Métricas de clasificación para el dashboard |
| `apps/frontend/public/ml/confusion_matrix.png` | Matriz de confusión (imagen) |
| `apps/frontend/public/ml/roc_curve.png` | Curva ROC (imagen) |

---

## Modelo de Clasificación (LogisticRegression)

### Target
```python
median_crimes = df["total_crimes"].median()  # = 3
df["target_binary"] = (df["total_crimes"] > median_crimes).astype(int)
```
- **1** = Alta incidencia (≥4 crímenes en el mes para ese grupo)
- **0** = Baja incidencia (≤3 crímenes en el mes para ese grupo)

### Features (one-hot encoded, ~120 dimensiones)
- `borough` (32 distritos)
- `major_category` (11 categorías)
- `minor_category` (64 subcategorías)
- `year` (2008-2016)
- `month` (1-12)

### Métricas

| Métrica | Valor | Nota |
|---------|-------|------|
| Accuracy | 0.891 | Inflada por fuga temporal |
| Precision | 0.852 | |
| Recall | 0.862 | |
| F1 Score | 0.857 | |
| ROC AUC | 0.945 | |
| Gini | 0.890 | |

### Matriz de Confusión
```
            Pred Bajo  Pred Alto
Real Bajo    10,923     1,906     ← FP = 1,906
Real Alto     1,693    10,581     ← FN = 1,693
```

---

## Modelo de Regresión (RandomForestRegressor)

### Target
- `total_crimes` — número de crímenes para ese grupo

### Features
- Mismas que clasificación (one-hot encoded)

### Métricas

| Métrica | Valor |
|---------|-------|
| R² | 0.942 |
| MAE | 4.372 |
| RMSE | 11.888 |
| Error Mediana | 2.048 |

---

## Limitaciones (Importante)

### 1. Fuga Temporal (Time Leakage)

```python
# apps/backend/cli/ml_pipeline.py — línea crítica
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
```

El split aleatorio mezcla años: datos de 2015 pueden estar en entrenamiento y datos de 2009 en prueba. El modelo "aprende" el futuro para estimar el pasado, lo que infla todas las métricas.

**¿Qué tan grave es?** En un escenario real (train: 2008-2014, test: 2015-2016), se espera:
- Accuracy: ~70-75% (vs 89% actual)
- R²: ~0.60-0.75 (vs 0.94 actual)

### 2. Threshold Global

La mediana global de `total_crimes` es **3** (75% de los grupos tienen ≤3 crímenes/mes). Esto significa que el 75% de los casos son "baja incidencia" por definición. Un clasificador naive que siempre prediga "baja" tendría 75% de accuracy.

### 3. Sin Features Temporales

No se usan lag features, rolling averages, ni descomposición estacional. El modelo no sabe que enero de 2015 debería parecerse más a enero de 2014 que a julio de 2015.

### 4. Rango Fijo

El modelo solo puede estimar dentro del rango de datos (2008-2016). No puede extrapolar a 2017+ de manera confiable.

---

## Opción B: Split Temporal Correcto (Recomendada)

Cambiar `train_test_split` por:

```python
train = df[df["year"] <= 2014]  # 2008-2014
test  = df[df["year"] >= 2015]  # 2015-2016
```

**Mejoras adicionales:**

```python
# Features temporales
df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
df["lag_1"] = groupby_shift(df, lag=1)    # mes anterior
df["lag_12"] = groupby_shift(df, lag=12)  # año anterior
df["rolling_3"] = groupby_rolling(df, window=3)
df["rolling_6"] = groupby_rolling(df, window=6)
```

## Opción C: Modelo Predictivo Real

Reemplazar con Prophet (Meta), LSTM, o SARIMA para predicción fuera del rango histórico:

```python
from prophet import Prophet

model = Prophet(yearly_seasonality=True, monthly_seasonality=True)
model.fit(historical_df)
future = model.make_future_dataframe(periods=12, freq="M")
forecast = model.predict(future)  # Predice 2017+
```

Requiere reestructurar el pipeline: un modelo por (borough, category) o modelos jerárquicos.

---

## Entrenamiento Local

```bash
# Ejecutar desde la raíz del proyecto
python -m apps.backend.cli.ml_pipeline

# Probar endpoint (requiere API corriendo)
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"borough": "westminster", "major_category": "theft and handling",
       "minor_category": "theft from shop", "year": 2016, "month": 6}'
```
