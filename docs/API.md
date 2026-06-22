# API Reference — London Crime Historical Estimator

Base URL: `https://london-crime-api.onrender.com` (producción) o `http://localhost:8000` (local)

---

## `GET /health`

Verifica que el servicio y los modelos estén cargados.

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

---

## `POST /predict`

Estima el perfil histórico de criminalidad para una combinación de distrito, categoría, mes y año.

**Importante:** Esto NO es una predicción del futuro. El modelo se entrenó con datos de 2008-2016 y solo puede estimar dentro de ese rango. Ver `/docs/ML_PIPELINE.md` para limitaciones detalladas.

### Request

```json
{
  "borough": "westminster",
  "major_category": "theft and handling",
  "minor_category": "theft from shop",
  "year": 2016,
  "month": 6
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `borough` | string | Distrito londinense (ej: "westminster", "camden") |
| `major_category` | string | Categoría principal (ej: "theft and handling", "violence against the person") |
| `minor_category` | string | Subcategoría (ej: "theft from shop", "common assault") |
| `year` | integer | Año (2008-2016) |
| `month` | integer | Mes (1-12) |

### Response

```json
{
  "borough": "westminster",
  "major_category": "theft and handling",
  "minor_category": "theft from shop",
  "year": 2016,
  "month": 6,
  "prediction": 1,
  "probability_high": 0.8234,
  "probability_low": 0.1766,
  "predicted_crimes": 42,
  "predicted_crimes_raw": 42.37,
  "features_used": 120
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `prediction` | integer | 1 = alta incidencia, 0 = baja incidencia |
| `probability_high` | float | Probabilidad de alta incidencia (0-1) |
| `probability_low` | float | Probabilidad de baja incidencia (0-1) |
| `predicted_crimes` | integer | Número estimado de crímenes (redondeado) |
| `predicted_crimes_raw` | float | Número estimado de crímenes (sin redondear) |
| `features_used` | integer | Dimensiones de feature vector |

### Códigos de Error

| Código | Significado |
|--------|-------------|
| 400 | Missing required field o invalid value |
| 422 | Validation error (formato incorrecto) |
| 500 | Model not loaded o internal error |

### Ejemplo con curl

```bash
curl -X POST https://london-crime-api.onrender.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "borough": "westminster",
    "major_category": "theft and handling",
    "minor_category": "theft from shop",
    "year": 2016,
    "month": 6
  }'
```

### Ejemplo con Python

```python
import requests

resp = requests.post("https://london-crime-api.onrender.com/predict", json={
    "borough": "westminster",
    "major_category": "theft and handling",
    "minor_category": "theft from shop",
    "year": 2016,
    "month": 6,
})
print(resp.json())
# {'prediction': 1, 'predicted_crimes': 42, 'probability_high': 0.8234, ...}
```

---

## `GET /docs` (Swagger UI)

Documentación interactiva generada por FastAPI. Disponible en `/docs` en el mismo host.

---

## Notas Técnicas

- **Latencia típica:** ~50-100ms por request (modelos livianos de scikit-learn).
- **Concurrencia:** FastAPI con Uvicorn maneja ~100 requests simultáneos (limitado por instancia Render gratuita).
- **Rate limiting:** No implementado (aplicar a nivel de Render si es necesario).
- **CORS:** Habilitado para todos los orígenes (`allow_origins=["*"]`).
