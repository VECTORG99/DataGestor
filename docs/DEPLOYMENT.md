# Despliegue — London Crime Data Platform

## Arquitectura de Despliegue

```
[GitHub] ──push──→ [GitHub Actions] ──tests──→ [Vercel / Render]
                        │
                        ├── tests.yml: pytest + lint
                        └── checks.yml: build
```

| Componente | Plataforma | URL | Build |
|-----------|-----------|-----|-------|
| Frontend (React) | Vercel | `https://london-crime-dashboard.vercel.app` | `npm run build` → `dist/` |
| Backend ML API | Render | `https://london-crime-api.onrender.com` | `uvicorn api.predict:app` |
| Base de Datos | Supabase | (cloud) | Pre-cargada |

No hay despliegue automático por GitHub Actions. Vercel y Render detectan cambios en `main` mediante sus integraciones nativas.

---

## Frontend — Vercel

### Configuración
- **Root directory:** `apps/frontend/`
- **Build command:** `npm run build`
- **Output directory:** `dist/`
- **Node version:** 18.x

### Variables de Entorno (Vercel dashboard)
```
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxx
VITE_ML_API_URL=https://london-crime-api.onrender.com
```

### Despliegue manual
```bash
cd apps/frontend
npx vercel --prod
```

---

## Backend ML API — Render

### Configuración
- **Type:** Web Service
- **Root directory:** `apps/backend/`
- **Runtime:** Python 3.11
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn api.predict:app --host 0.0.0.0 --port $PORT`

### Variables de Entorno (Render dashboard)
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJxxx
PYTHON_VERSION=3.11.0
```

### Health Check
Render puede configurar un health check en `GET /health`:
```json
{"status": "ok", "model_loaded": true}
```

---

## Base de Datos — Supabase

### Tabla: `london_crime_aggregated`
```sql
CREATE TABLE london_crime_aggregated (
  id SERIAL PRIMARY KEY,
  borough VARCHAR(100),
  major_category VARCHAR(100),
  minor_category VARCHAR(100),
  year INTEGER,
  month INTEGER,
  total_crimes INTEGER,
  date DATE
);

CREATE INDEX idx_london_crime_aggregated_borough ON london_crime_aggregated(borough);
CREATE INDEX idx_london_crime_aggregated_year ON london_crime_aggregated(year);
```

Los datos se cargan mediante el pipeline ETL con upsert. El dataset completo tiene ~23,000 registros agregados.

---

## CI/CD — GitHub Actions

### `tests.yml`
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backend tests
        working-directory: apps/backend
        run: |
          pip install -r requirements.txt
          pytest tests/ -v
      - name: Frontend lint
        working-directory: apps/frontend
        run: |
          npm install
          npm run lint
```

### `checks.yml`
```yaml
name: Build Check
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Frontend build
        working-directory: apps/frontend
        run: |
          npm install
          npm run build
```

### Secrets requeridos en GitHub
Los tests del backend requieren credenciales de Supabase:
```
SUPABASE_URL=***
SUPABASE_KEY=***
```

---

## Pipeline ETL

El pipeline ETL se ejecuta **localmente** (no en producción):

```bash
cd apps/backend

# Modo normal (usa datos existentes en Supabase si hay)
python scripts/etl_pipeline.py

# Forzar recarga completa desde BigQuery
python scripts/etl_pipeline.py --mode production

# Solo ML (si la tabla ya tiene datos)
python ml/train.py
```

### Requisitos del pipeline ETL
1. Credenciales GCP (`google-cloud-bigquery`) — archivo JSON de service account.
2. Credenciales Supabase — variables de entorno.
3. Dataset público `london_crime` en BigQuery.

### Flujo ETL
```
BigQuery (3M registros LSOA)
    │
    ▼
Limpieza (nulos, meses inválidos, años fuera de rango, negativos, duplicados, normalización)
    │
    ▼
Agregación (GROUP BY borough, major_category, minor_category, year, month)
    │
    ▼
Supabase (upsert ~23K registros agregados)
    │
    ▼
Entrenamiento ML (train.py)
```

---

## Docker (Alternativa Local)

### Frontend
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```
Se sirve con nginx (config en `nginx.conf`).

### Backend
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.predict:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker-compose up -d  # Levanta frontend + backend localmente
```
