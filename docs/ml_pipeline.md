# ML Pipeline - London Crime DataGestor

## Resumen

Pipeline de Machine Learning que entrena un modelo de **regresion lineal** como modelo principal y modelos de **clasificacion binaria** (Logistic Regression + Random Forest) como complemento, sobre el dataset `london_crime_aggregated` procesado por el pipeline ETL.

Los modelos predictivos permiten analizar y anticipar patrones delictivos en los 33 distritos de Londres, utilizando datos historicos de BigQuery (~100k registros originales, ~16k agregados).

---

## 1. Problema de Negocio

### Preguntas que responde el modelo

| Tipo | Pregunta | Aplicacion |
|---|---|---|
| **Regresion** | ¿Cuantos crimenes de un tipo especifico ocurriran en un distrito en un mes determinado? | Asignacion de recursos policiales |
| **Clasificacion** | ¿Este periodo (distrito, categoria, mes) tendra alta incidencia delictiva? | Alertas tempranas, planificacion preventiva |

### Target

- **Regresion**: `total_crimes` (numero de crimenes, continuo)
- **Clasificacion**: `is_high_crime` (binario: 1 si `total_crimes > mediana`, 0 en otro caso)

### Features

| Feature | Tipo | Procesamiento |
|---|---|---|
| `borough` | Categorica (33 valores) | One-hot encoding |
| `major_category` | Categorica (9 valores) | One-hot encoding |
| `minor_category` | Categorica (~20 valores) | One-hot encoding |
| `year` | Numerica | StandardScaler |
| `month` | Ciclica (1-12) | Seno + Coseno |

---

## 2. Pipeline de Preprocesamiento

Ubicacion: `apps/backend/ml/preprocessing.py`

```
Dataset limpio (CSV/Parquet)
    │
    ▼
prepare_features()
    ├── cyclical_encode_month()  → month_sin, month_cos
    └── Seleccionar columnas     → borough, major_category, minor_category, year
    │
    ▼
create_regression_target()  → total_crimes (regresion)
create_classification_target() → is_high_crime (clasificacion)
    │
    ▼
build_preprocessor()
    ├── OneHotEncoder          → columnas categoricas
    └── StandardScaler         → columnas numericas
    │
    ▼
train_test_split (70/30, estratificado para clasificacion)
    │
    ▼
X_train, X_test, y_train, y_test, preprocessor
```

---

## 3. Modelos

### 3.1 Regresion Lineal

**Algoritmo**: `sklearn.linear_model.LinearRegression`

**Metricas**:

| Metrica | Descripcion |
|---|---|
| **R²** | Proporcion de varianza explicada por el modelo |
| **RMSE** | Raiz del error cuadratico medio (en crimenes) |
| **MAE** | Error absoluto medio (en crimenes) |
| **Residuales** | Diferencia entre valor real y predicho |

**Resultados** (sobre 16,609 registros, BigQuery):

| Metrica | Valor |
|---|---|
| R² | 0.3945 |
| RMSE | 11.29 crimenes |
| MAE | 4.92 crimenes |

### 3.2 Logistic Regression (Clasificacion)

**Algoritmo**: `sklearn.linear_model.LogisticRegression` (max_iter=1000)

| Metrica | Valor |
|---|---|
| Accuracy | 0.9743 |
| Precision | 0.9888 |
| Recall | 0.9510 |
| F1-Score | 0.9696 |
| ROC AUC | 0.9850 |
| **Gini** | **0.9701** |

### 3.3 Random Forest (Clasificacion)

**Algoritmo**: `sklearn.ensemble.RandomForestClassifier` (100 arboles)

| Metrica | Valor |
|---|---|
| Accuracy | 0.9739 |
| Precision | 0.9846 |
| Recall | 0.9543 |
| F1-Score | 0.9692 |
| ROC AUC | 0.9867 |
| **Gini** | **0.9735** |

---

## 4. Interpretacion de Metricas

### Regresion Lineal (R² = 0.39)

El modelo explica el ~39% de la variabilidad en el numero de crimenes. Es un valor moderado, esperable porque los crimenes dependen de muchos factores socioeconomicos no capturados en este dataset limitado a ubicacion, categoria y tiempo. Sin embargo, los coeficientes del modelo revelan que distritos y categorias especificas tienen pesos predictivos significativos.

### Matriz de Confusion

La matriz de confusion muestra verdaderos positivos (alta incidencia correctamente identificada), falsos positivos (alarma falsa), verdaderos negativos y falsos negativos (alta incidencia no detectada). Estos ultimos son los mas peligrosos porque representan periodos de alta criminalidad no anticipados.

### Curva ROC y Gini

- **ROC AUC ~0.985**: El modelo tiene excelente capacidad discriminativa. En un grafico ROC, la curva se aproxima muy cerca de la esquina superior izquierda.
- **Gini ~0.97**: Indice derivado del ROC (Gini = 2×AUC - 1). Un valor cercano a 1 indica poder predictivo muy alto. La banca utiliza este mismo indicador para evaluar modelos de riesgo crediticio.

### Feature Importance (Random Forest)

El grafico de importancia de variables revela que:
- `major_category` (especialmente "Violence Against the Person" y "Theft and Handling") tiene el mayor peso predictivo
- `borough` tambien contribuye significativamente (distritos con mayor poblacion tienen mas crimenes)
- `year` y `month` tienen menor peso, indicando que la estacionalidad es secundaria frente a la categoria del delito

---

## 5. Archivos Generados

### Modelos (`data/models/`)

| Archivo | Descripcion |
|---|---|
| `linear_regression.joblib` | Modelo de regresion lineal entrenado |
| `logistic_regression.joblib` | Clasificador Logistic Regression |
| `random_forest.joblib` | Clasificador Random Forest (100 arboles, ~12MB) |

### Graficos (`data/metrics/`)

| Archivo | Descripcion |
|---|---|
| `residuals.png` | Residuales vs Predicho + histograma |
| `confusion_matrix_logreg.png` | Matriz de confusion (Logistic Regression) |
| `roc_curve_logreg.png` | Curva ROC (Logistic Regression) |
| `confusion_matrix_rf.png` | Matriz de confusion (Random Forest) |
| `roc_curve_rf.png` | Curva ROC (Random Forest) |
| `feature_importance_rf.png` | Top 15 features (Random Forest) |

### Metricas (`data/metrics/ml_metrics.json`)

JSON completo con todas las metricas de regresion y clasificacion.

---

## 6. Como Ejecutar

```bash
# 1. Asegurar datos limpios (desde BigQuery o demo)
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py

# 2. Ejecutar pipeline ML
docker exec london_crime_app python apps/backend/cli/ml_pipeline.py

# 3. Ejecutar tests
docker exec london_crime_app python -m pytest apps/backend/tests/ -v
```

### Modo demo (sin BigQuery)

```bash
# Generar datos sinteticos (5000+ registros)
docker exec london_crime_app python apps/backend/cli/pipeline_dataops.py --demo

# Ejecutar ML
docker exec london_crime_app python apps/backend/cli/ml_pipeline.py
```

---

## 7. Dependencias

Agregadas a `requirements.txt`:

```
scikit-learn>=1.3,<2
xgboost>=2.0,<3
matplotlib>=3.7,<4
seaborn>=0.12,<1
joblib>=1.3,<2
```

---

## 8. Tests

12 tests unitarios especificos del modulo ML (`apps/backend/tests/test_ml.py`):

| Clase | Tests | Cobertura |
|---|---|---|
| `TestPreprocessing` | 7 | Carga, targets, encoding ciclico, ColumnTransformer, split |
| `TestRegression` | 2 | Entrenamiento, evaluacion de metricas |
| `TestClassification` | 3 | LR, RF, evaluacion completa de metricas |
