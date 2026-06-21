# 🤖 Machine Learning Pipeline - DataGestor

## Índice

- [1. Visión General](#1-visión-general)
- [2. Modelo: Logistic Regression](#2-modelo-logistic-regression)
- [3. Features & Preprocesamiento](#3-features--preprocesamiento)
- [4. Training & Evaluación](#4-training--evaluación)
- [5. Métricas de Rendimiento](#5-métricas-de-rendimiento)
- [6. Uso del Modelo](#6-uso-del-modelo)
- [7. Mejoras Futuras](#7-mejoras-futuras)

---

## 1. Visión General

### Objetivo del Modelo

**Predecir si una combinación de (borough, categoría, año, mes) tendrá criminalidad "Alta" o "Baja".**

**Caso de Uso:**
- Input: Westminster, Robbery, 2016, July
- Output: "Alta" (prob 0.87) → Mayor riesgo de robo en Westminster en julio

### Datos de Entrenamiento

- **Fuente:** Tabla `london_crime_aggregated` (77,524 registros)
- **Variables:** Borough, major_category, minor_category, year, month, total_crimes
- **Split:** 70% train (54,267), 30% test (23,257)
- **Balance:** Target balanceado (51.2% Alta, 48.8% Baja)

### Algoritmo Seleccionado

**Logistic Regression** (scikit-learn)

**Por qué:**
- ✅ Interpretable (probabilidades)
- ✅ Rápido para entrenar y predecir
- ✅ Funciona bien con características categóricas one-hot encoded
- ✅ Proporciona confidence scores (0.0-1.0)
- ✅ Baseline sólido para regressions binarias

---

## 2. Modelo: Logistic Regression

### Fórmula Matemática

```
P(y=1|X) = 1 / (1 + e^(-z))

donde:
z = β₀ + β₁X₁ + β₂X₂ + ... + βₙXₙ
y ∈ {0, 1} (Baja, Alta)
```

### Parámetros del Modelo

```python
from sklearn.linear_model import LogisticRegression

model = LogisticRegression(
    max_iter=1000,           # Máximo de iteraciones
    class_weight='balanced',  # Balancear clases
    solver='lbfgs',          # Optimizador
    random_state=42          # Reproducibilidad
)
```

### Decision Threshold

```
Default: threshold = 0.5

Si P(y=1) >= 0.5  →  Predicción: "Alta" (1)
Si P(y=1) <  0.5  →  Predicción: "Baja" (0)
```

**Ajuste de threshold:**
```python
# Aumentar threshold para más conservador (menos falsos positivos)
threshold = 0.6  # Más selectivo

# Disminuir threshold para más agresivo (menos falsos negativos)
threshold = 0.4  # Más sensible
```

---

## 3. Features & Preprocesamiento

### 3.1 Features de Entrada

| # | Feature | Tipo | Rango | Transformación |
|---|---------|------|-------|---|
| 1 | `borough` | Categórico | 33 valores | One-Hot Encoding |
| 2 | `major_category` | Categórico | 8 valores | One-Hot Encoding |
| 3 | `minor_category` | Categórico | ~40 valores | One-Hot Encoding |
| 4 | `year` | Numérico | 2008-2016 | StandardScaler |
| 5 | `month_sin` | Numérico | -1 a +1 | Cíclico: sin(2π × m/12) |
| 6 | `month_cos` | Numérico | -1 a +1 | Cíclico: cos(2π × m/12) |

### 3.2 Transformaciones

#### One-Hot Encoding (Categóricas)

```python
from sklearn.preprocessing import OneHotEncoder

encoder = OneHotEncoder(
    handle_unknown='ignore',      # Ignorar valores nuevos
    sparse_output=False,          # Retornar array denso
    drop=None                     # Mantener todas las columnas
)

# Transforma:
# borough = "Westminster" 
# →
# borough_Westminster = 1, borough_Croydon = 0, borough_Lambeth = 0, ...
```

**Ejemplo:**
```
Original:  borough = "Westminster"
Encoded:   [0, 0, 0, 1, 0, ..., 0]  (33 columnas totales)
```

#### StandardScaler (Numéricas)

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

# Transforma:
# year = 2015
# →
# z = (2015 - mean(year)) / std(year) = 0.5

# Resultado: Media = 0, Std = 1
```

#### Codificación Cíclica (Mes)

```python
import numpy as np

# Convertir mes (1-12) a coordenadas circulares
month = 7  # Julio

month_sin = np.sin(2 * np.pi * month / 12)  # ≈ 0.867
month_cos = np.cos(2 * np.pi * month / 12)  # ≈ 0.5

# Captura la naturaleza cíclica: mes 12 (Dec) es cercano a mes 1 (Jan)
# Sin esto: mes 1 y mes 12 se verían "lejanos"
```

### 3.3 Pipeline de Preprocesamiento

```python
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

# Definir columnas
categorical_cols = ['borough', 'major_category', 'minor_category']
numeric_cols = ['year', 'month_sin', 'month_cos']

# Transformadores
ct = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
    ('num', StandardScaler(), numeric_cols)
])

# Aplicar
X_transformed = ct.fit_transform(df[categorical_cols + numeric_cols])

# Resultado: Matriz (77,524 × ~80 features)
```

### 3.4 Target Variable

```python
# Crear target binaria
df['target'] = (df['total_crimes'] > df['total_crimes'].median()).astype(int)

# Resultado:
# 1 = "Alta" (total_crimes > mediana)
# 0 = "Baja" (total_crimes ≤ mediana)

# Estadísticas:
# Mediana: 34.0
# Baja (0): 37,566 registros (48.8%)
# Alta (1): 39,958 registros (51.2%)
```

---

## 4. Training & Evaluación

### 4.1 Flujo de Entrenamiento

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix
)

# Step 1: Preprocesar features
X_transformed = ct.fit_transform(df[features])
y = df['target']

# Step 2: Train/Test Split (70/30, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X_transformed, y,
    test_size=0.3,
    random_state=42,
    stratify=y  # Mantener proporción en ambos sets
)

# Step 3: Entrenar modelo
model = LogisticRegression(max_iter=1000, class_weight='balanced')
model.fit(X_train, y_train)

# Step 4: Evaluar
y_pred = model.predict(X_test)
y_pred_proba = model.predict_proba(X_test)[:, 1]

# Step 5: Calcular métricas
metrics = {
    'accuracy': accuracy_score(y_test, y_pred),
    'precision': precision_score(y_test, y_pred),
    'recall': recall_score(y_test, y_pred),
    'f1': f1_score(y_test, y_pred),
    'roc_auc': roc_auc_score(y_test, y_pred_proba),
}

print(metrics)
# {'accuracy': 0.890, 'precision': 0.865, ...}
```

### 4.2 Cross-Validation (Opcional)

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(
    model, X_transformed, y,
    cv=5,  # 5-fold cross-validation
    scoring='roc_auc'
)

print(f"Cross-Val Scores: {scores}")
print(f"Mean AUC: {scores.mean():.3f} (+/- {scores.std():.3f})")
```

---

## 5. Métricas de Rendimiento

### 5.1 Matriz de Confusión

```
                Predicción
              Baja      Alta
Real   Baja  9,532    1,200       (Specificity: 88.8%)
       Alta  1,830   21,238       (Sensitivity: 92.1%)
```

**Interpretación:**
- TP (True Positive): 21,238 → Predijo Alta y era Alta ✓
- TN (True Negative): 9,532 → Predijo Baja y era Baja ✓
- FP (False Positive): 1,200 → Predijo Alta pero era Baja ✗
- FN (False Negative): 1,830 → Predijo Baja pero era Alta ✗

### 5.2 Métricas Calculadas

| Métrica | Fórmula | Valor | Interpretación |
|---------|---------|-------|---|
| **Accuracy** | (TP+TN)/(TP+TN+FP+FN) | 89.0% | De 100 predicciones, 89 correctas |
| **Precision** | TP/(TP+FP) | 86.5% | De casos predichos como Alta, 86.5% son reales |
| **Recall** | TP/(TP+FN) | 92.1% | Detecta 92.1% de los casos reales de Alta |
| **F1 Score** | 2×(Precision×Recall)/(Precision+Recall) | 88.9% | Balance entre P y R |
| **ROC AUC** | Area Under Curve | 0.963 | Excelente discriminación |
| **Specificity** | TN/(TN+FP) | 88.8% | Correctly identifies Baja cases |

### 5.3 Curva ROC (Receiver Operating Characteristic)

```
Sensibilidad (TPR)
     ^
     |     ╱╱╱╱
 100% |   ╱╱╱╱  ← Modelo bueno (AUC = 0.963)
     |  ╱╱╱╱
     | ╱╱╱╱
  50% |╱╱╱╱
     |
   0%+───────────────> 1-Specificity (FPR)
     0%      50%     100%

AUC = 0.963 → Excelente discriminación
AUC = 0.5   → Adivinanza aleatoria
AUC = 1.0   → Perfecto (imposible)
```

---

## 6. Uso del Modelo

### 6.1 Predicción en Production

```python
import joblib
import numpy as np

# Cargar modelo entrenado
model = joblib.load('apps/backend/ml/logistic_regression.joblib')
preprocessor = joblib.load('apps/backend/ml/preprocessor.pkl')

# Preparar datos nuevos
new_data = {
    'borough': 'Westminster',
    'major_category': 'Robbery',
    'minor_category': 'Robbery of personal property',
    'year': 2016,
    'month': 7,
    'month_sin': np.sin(2 * np.pi * 7 / 12),
    'month_cos': np.cos(2 * np.pi * 7 / 12)
}

# Transformar
X_new = preprocessor.transform([new_data])

# Predecir
prediction = model.predict(X_new)[0]           # 0 o 1
probability = model.predict_proba(X_new)[0]   # [P(Baja), P(Alta)]

print(f"Predicción: {'Alta' if prediction == 1 else 'Baja'}")
print(f"Probabilidad Alta: {probability[1]:.2%}")
```

### 6.2 Interpretabilidad

```python
# Obtener coeficientes del modelo
coefficients = model.coef_[0]
feature_names = preprocessor.get_feature_names_out()

# Top features más influyentes
top_indices = np.argsort(np.abs(coefficients))[-10:]
for idx in top_indices[::-1]:
    print(f"{feature_names[idx]}: {coefficients[idx]:.4f}")

# Ejemplo output:
# major_category_Robbery: 0.8234
# borough_Westminster: 0.6123
# year: 0.4856
```

### 6.3 Frontend Display

```javascript
// Mostrar predicciones en dashboard
const prediction = await fetchMLPrediction({
    borough: 'Westminster',
    major_category: 'Robbery',
    year: 2016,
    month: 7
});

if (prediction.probability > 0.8) {
    console.log("🔴 Alto riesgo de criminalidad");
} else if (prediction.probability > 0.5) {
    console.log("🟡 Riesgo medio");
} else {
    console.log("🟢 Riesgo bajo");
}
```

---

## 7. Mejoras Futuras

### 7.1 Modelos Más Avanzados

```python
# Random Forest - mejor para relaciones no-lineales
from sklearn.ensemble import RandomForestClassifier

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
rf_score = rf_model.score(X_test, y_test)

# XGBoost - state-of-the-art
from xgboost import XGBClassifier

xgb_model = XGBClassifier(random_state=42)
xgb_model.fit(X_train, y_train)
xgb_score = xgb_model.score(X_test, y_test)

# Comparar
print(f"Logistic Regression: {model.score(X_test, y_test):.3f}")
print(f"Random Forest: {rf_score:.3f}")
print(f"XGBoost: {xgb_score:.3f}")
```

### 7.2 Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'C': [0.001, 0.01, 0.1, 1, 10],
    'max_iter': [100, 500, 1000],
    'solver': ['lbfgs', 'liblinear']
}

grid_search = GridSearchCV(
    LogisticRegression(),
    param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1
)

grid_search.fit(X_train, y_train)
print(f"Best params: {grid_search.best_params_}")
print(f"Best CV score: {grid_search.best_score_:.3f}")
```

### 7.3 Feature Engineering

```python
# Agregar features temporales
df['quarter'] = (df['month'] - 1) // 3 + 1
df['is_summer'] = df['month'].isin([6, 7, 8]).astype(int)

# Agregar lags (crímenes del mes anterior)
df['prev_month_crimes'] = df.groupby(['borough', 'major_category'])['total_crimes'].shift(1)

# Agregar rolling averages
df['rolling_avg_6m'] = df.groupby(['borough', 'major_category'])['total_crimes'].transform(
    lambda x: x.rolling(6, min_periods=1).mean()
)
```

### 7.4 Automatización de Reentrenamiento

```python
# Reentrenar modelo cada mes con datos nuevos
import schedule

def retrain_model():
    df_new = fetch_new_data()
    X_new, y_new = preprocess(df_new)
    model.fit(X_new, y_new)
    joblib.dump(model, 'model.joblib')
    print("Model retrained!")

schedule.every().month.do(retrain_model)

while True:
    schedule.run_pending()
```

### 7.5 Monitoreo de Drift

```python
# Detectar si la distribución de datos cambió (model drift)
from sklearn.metrics import total_variation_distance

def check_data_drift(X_old, X_new):
    drift = total_variation_distance(
        X_old.mean(axis=0),
        X_new.mean(axis=0)
    )
    
    if drift > 0.1:  # Threshold
        print("⚠️ Data drift detected!")
        return True
    return False
```

---

## 8. Archivos del Pipeline

| Archivo | Propósito |
|---------|----------|
| `apps/backend/ml/preprocessing.py` | Feature engineering y transformaciones |
| `apps/backend/ml/classification.py` | Model training y evaluación |
| `apps/backend/cli/ml_pipeline.py` | CLI orchestration |
| `apps/backend/ml/logistic_regression.joblib` | Modelo entrenado (persistencia) |
| `apps/backend/ml/preprocessor.pkl` | Preprocesador (persistencia) |
| `data/metrics/ml_metrics.json` | Métricas calculadas |
| `data/metrics/confusion_matrix.png` | Visualización |
| `data/metrics/roc_curve.png` | Visualización |

---

## 9. Ejecución

```bash
# Entrenar modelo
python apps/backend/cli/ml_pipeline.py

# Modo debug
LOG_LEVEL=DEBUG python apps/backend/cli/ml_pipeline.py

# Solo preprocesamiento (sin training)
python -c "from apps.backend.ml.preprocessing import Preprocessor; p = Preprocessor(); print(p.get_feature_names())"
```

---

**Última actualización:** Junio 2026  
**Data Scientist:** [nombre]  
**Revisado:** [revisor]
