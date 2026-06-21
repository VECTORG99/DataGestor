# 🚀 Deployment Guide - DataGestor

## Índice

- [1. Despliegue Recomendado](#1-despliegue-recomendado)
- [2. Frontend: Vercel](#2-frontend-vercel)
- [3. Backend: Docker Compose (Local)](#3-backend-docker-compose-local)
- [4. Backend: Cloud Deployment (Opcional)](#4-backend-cloud-deployment-opcional)
- [5. Configuración de CI/CD](#5-configuración-de-cicd)
- [6. Monitoreo y Mantenimiento](#6-monitoreo-y-mantenimiento)

---

## 1. Despliegue Recomendado

### Arquitectura de Producción

```
┌─────────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend)                        │
│  ├─ https://data-gestor.vercel.app                         │
│  ├─ Auto-deploy desde GitHub main branch                    │
│  ├─ CDN global, HTTPS, caching                             │
│  └─ Env vars: VITE_SUPABASE_*                              │
└─────────────────────┬───────────────────────────────────────┘
                      │ (JSON REST API)
                      │
┌─────────────────────v───────────────────────────────────────┐
│                SUPABASE (Database)                           │
│  ├─ PostgreSQL managed                                      │
│  ├─ Automated backups                                       │
│  ├─ Row-Level Security enabled                              │
│  └─ 77.5k registros de crímenes                            │
└──────────────────────────────────────────────────────────────┘
                      ↑
                      │ (Batch ETL - Scheduled)
                      │
┌─────────────────────┴───────────────────────────────────────┐
│            BACKEND BATCH JOBS (Docker)                      │
│  ├─ Cloud Run / Scheduled Container                        │
│  ├─ Ejecuta: ETL Pipeline + ML Training                    │
│  ├─ Frecuencia: Diaria (ej: 2 AM UTC)                      │
│  └─ Env vars: GCP_PROJECT_ID, SUPABASE_*                  │
└──────────────────────────────────────────────────────────────┘
```

### Tier Recomendado

| Componente | Tier | Costo | Notas |
|-----------|------|-------|-------|
| **Vercel Frontend** | Hobby (FREE) | $0 | 1 proyecto, deploys ilimitados |
| **Supabase Database** | Free (500 MB) | $0 | Suficiente para 77.5k registros |
| **Backend Container** | GCP Cloud Run | $0-5/mes | Paga solo por tiempo de ejecución |

---

## 2. Frontend: Vercel

### 2.1 Setup Inicial

**Requisitos:**
- Cuenta GitHub con repositorio `VECTORG99/DataGestor`
- Cuenta Vercel (vercel.com)

**Pasos:**

1. **Conectar GitHub a Vercel**
   - Ir a [vercel.com](https://vercel.com)
   - Clickear "Import Project"
   - Seleccionar "GitHub" y autorizar
   - Seleccionar repositorio `DataGestor`

2. **Configurar Variables de Entorno**
   - Settings → Environment Variables
   - Agregar:
     ```
     VITE_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
     VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     ```

3. **Configurar Build**
   - Framework: `Next.js` → cambiar a `Vite`
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`
   - Root Directory: `apps/frontend`

### 2.2 Deploy Manual

```bash
# Instalar Vercel CLI
npm install -g vercel

# Autenticarse
vercel login

# Deploy desde apps/frontend
cd apps/frontend
vercel --prod

# Resultado:
# ✓ Preview: https://data-gestor-xxxxx.vercel.app
# ✓ Production: https://data-gestor.vercel.app
```

### 2.3 Configuración vercel.json

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_SUPABASE_URL": "@supabase_url",
    "VITE_SUPABASE_ANON_KEY": "@supabase_anon_key"
  },
  "redirects": [
    {
      "source": "/",
      "destination": "/",
      "permanent": false
    }
  ]
}
```

### 2.4 Auto-Deploy desde GitHub

**Configurar en Vercel Dashboard:**

```
Settings → Git Connections → GitHub

Deploy Branch: main
Production Branch: main
Preview Branches: All (except main)
```

**Resultado:**
- `git push origin main` → Auto deploy a producción ✅
- `git push origin feature/*` → Auto preview URL ✅

---

## 3. Backend: Docker Compose (Local)

### 3.1 Ejecutar Localmente

```bash
# Desde raíz del proyecto
docker-compose up -d

# Verificar
docker-compose ps
# CONTAINER ID   IMAGE                        STATUS
# xxxxx          datagestor-backend           Up 2 minutes
```

### 3.2 Ejecutar ETL Pipeline

```bash
# Ingesta desde BigQuery + Limpieza + Carga a Supabase
docker exec datagestor-app python apps/backend/cli/pipeline_dataops.py

# Ver logs
docker exec datagestor-app tail -f data/logs/pipeline.log
```

### 3.3 Ejecutar ML Training

```bash
# Entrenar modelo y generar métricas
docker exec datagestor-app python apps/backend/cli/ml_pipeline.py

# Ver salidas
docker exec datagestor-app ls -lah data/metrics/
```

### 3.4 Dockerfile Backend

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Instalar Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Usuario no-root
RUN useradd -m -u 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Entrypoint
CMD ["/bin/bash"]
```

---

## 4. Backend: Cloud Deployment (Opcional)

### 4.1 Google Cloud Run

**Ventajas:**
- Managed service (no mantener infraestructura)
- Paga solo por tiempo de ejecución (ejecuta < 1 min)
- Costo: ~$0.005 por ejecución
- Integración con Cloud Scheduler (cron)

**Pasos:**

1. **Crear Dockerfile optimizado**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN useradd -m -u 1000 appuser
USER appuser

ENTRYPOINT ["python", "apps/backend/cli/pipeline_dataops.py"]
```

2. **Build y push a Container Registry**

```bash
# Autenticarse en GCP
gcloud auth login

# Build imagen
gcloud builds submit --tag gcr.io/PROJECT_ID/datagestor-etl

# Resultado: gcr.io/PROJECT_ID/datagestor-etl:latest
```

3. **Deploy a Cloud Run**

```bash
gcloud run deploy datagestor-etl \
  --image gcr.io/PROJECT_ID/datagestor-etl \
  --region us-central1 \
  --memory 2Gi \
  --timeout 600 \
  --set-env-vars SUPABASE_DB_URL=$SUPABASE_DB_URL,GCP_PROJECT_ID=$GCP_PROJECT_ID \
  --service-account datagestor@PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated
```

4. **Configurar Scheduler (Ejecutar diariamente)**

```bash
gcloud scheduler jobs create pubsub daily-etl \
  --location us-central1 \
  --schedule "0 2 * * *" \  # 2 AM UTC diariamente
  --topic datagestor-etl-topic \
  --message-body '{}'
```

### 4.2 AWS Lambda (Alternativa)

```python
# lambda_handler.py
import json
from apps.backend.cli.pipeline_dataops import main

def lambda_handler(event, context):
    try:
        main()
        return {
            'statusCode': 200,
            'body': json.dumps('ETL executed successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
```

**Configurar en AWS:**
- EventBridge rule → Ejecutar diariamente
- Timeout: 15 minutos
- Memory: 3 GB
- Env vars: Mismo que GCP

---

## 5. Configuración de CI/CD

### 5.1 GitHub Actions Workflow

**`.github/workflows/ci-backend.yml`**

```yaml
name: CI Backend

on:
  push:
    branches: [main, master, develop]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Lint with Black
      run: black --check apps/backend
    
    - name: Lint with Flake8
      run: flake8 apps/backend --max-line-length=100
    
    - name: Run tests
      run: pytest apps/backend/tests -v
      env:
        SUPABASE_DB_URL: ${{ secrets.SUPABASE_DB_URL }}
        GCP_PROJECT_ID: test-project
    
    - name: Upload coverage
      if: always()
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests

  deploy-frontend:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Vercel
      uses: vercel/action@master
      with:
        vercel-token: ${{ secrets.VERCEL_TOKEN }}
        vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
        vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

### 5.2 GitHub Secrets

**Configurar en GitHub (Settings → Secrets and variables → Actions):**

```
SUPABASE_DB_URL           = postgresql://user:pass@host:5432/db
GCP_PROJECT_ID            = london-crime-491323
VERCEL_TOKEN              = (generar en Vercel)
VERCEL_ORG_ID             = (ver en Vercel)
VERCEL_PROJECT_ID         = (ver en Vercel)
```

---

## 6. Monitoreo y Mantenimiento

### 6.1 Logs

**Frontend (Vercel):**
- Dashboard → Deployments → Click deploy → Functions/Logs
- O acceder a `/api/logs` (si está configurado)

**Backend (Local):**
```bash
tail -f data/logs/pipeline.log
```

**Backend (Cloud Run):**
```bash
gcloud run logs read datagestor-etl --limit 100
```

**Backend (CloudWatch/Lambda):**
- AWS Console → Lambda → Monitoring → Logs

### 6.2 Monitoreo de Errores

**Verificar si ETL tuvo éxito:**

```bash
# Revisar última ejecución
tail -5 data/logs/pipeline.log

# Debe contener:
# [INFO] Pipeline completed successfully
# [INFO] Rows loaded: 77524
```

**Alertas:**

```python
# En pipeline_dataops.py
try:
    main()
except Exception as e:
    logger.error(f"Pipeline failed: {e}")
    send_alert_email("DataGestor ETL failed!")  # Implementar
    sys.exit(1)
```

### 6.3 Backups Automáticos

**Supabase (Automático):**
- Free tier: Backups diarios (7 días retención)
- Dashboard → Backups → Restore

**Base de datos local (Manual):**

```bash
# Hacer backup
pg_dump -h localhost -U postgres datagestor > backup.sql

# Restaurar
psql -h localhost -U postgres datagestor < backup.sql
```

### 6.4 Actualizar Dependencias

**Python:**
```bash
pip list --outdated
pip install --upgrade <package-name>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

**Node.js:**
```bash
cd apps/frontend
npm outdated
npm update
git add package.json package-lock.json
git commit -m "Update npm packages"
git push
```

---

## 7. Rollback Procedure

### 7.1 Rollback Frontend (Vercel)

```
Vercel Dashboard → Deployments → Select previous version → "Redeploy"
```

**O manual:**
```bash
cd apps/frontend
git checkout <previous-commit>
git push origin main
# Vercel auto-deploys
```

### 7.2 Rollback Backend

```bash
# Si es en Cloud Run
gcloud run deploy datagestor-etl --image gcr.io/PROJECT_ID/datagestor-etl:previous-tag

# Si es Supabase data
# 1. Ir a Dashboard → Backups
# 2. Seleccionar backup anterior
# 3. Click "Restore"
```

---

## 8. Checklist de Despliegue

- [ ] Verificar variables de entorno (.env)
- [ ] Ejecutar tests locales: `pytest apps/backend/tests -v`
- [ ] Build frontend: `cd apps/frontend && npm run build`
- [ ] Build backend: `docker build -f infra/backend.Dockerfile .`
- [ ] Push a GitHub: `git push origin main`
- [ ] Verificar GitHub Actions: Pasar todos los tests
- [ ] Verificar Vercel: Deploy exitoso
- [ ] Verificar Supabase: Datos correctos en tabla
- [ ] Testing manual: Acceder a URL y probar funcionalidad
- [ ] Monitorear logs: 24 horas tras deploy

---

## 9. URLs Importantes

| Recurso | URL |
|---------|-----|
| **Aplicación** | https://data-gestor.vercel.app |
| **Vercel Dashboard** | https://vercel.com/dashboard |
| **Supabase Dashboard** | https://app.supabase.com |
| **GitHub Repo** | https://github.com/VECTORG99/DataGestor |
| **GitHub Actions** | https://github.com/VECTORG99/DataGestor/actions |

---

**Última actualización:** Junio 2026  
**DevOps Lead:** [nombre]  
**Revisado:** [revisor]
