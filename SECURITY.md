# 🔒 Plan de Seguridad - DataGestor

## Índice

- [1. Marco Legal Aplicable](#1-marco-legal-aplicable)
- [2. Cifrado](#2-cifrado)
- [3. Control de Acceso](#3-control-de-acceso)
- [4. Gestión de Secretos](#4-gestión-de-secretos)
- [5. Aislamiento de Contenedores](#5-aislamiento-de-contenedores)
- [6. Vulnerabilidades Conocidas](#6-vulnerabilidades-conocidas)
- [7. Políticas de RLS en Supabase](#7-políticas-de-rls-en-supabase)
- [8. Respuesta a Incidentes](#8-respuesta-a-incidentes)

---

## 1. Marco Legal Aplicable

### 1.1 Reglamento General de Protección de Datos (GDPR) - UE

**✅ Aplica porque:** Los datos procesados incluyen información de crímenes en Londres (Reino Unido).

**Cumplimiento:**
- ✅ **Minimización de datos**: Solo se almacenan campos necesarios para análisis (borough, categorías, fechas, valores agregados)
- ✅ **Limitación de finalidad**: Datos usados exclusivamente para análisis estadístico de seguridad pública
- ✅ **Transparencia**: Pipeline documenta cada transformación aplicada
- ✅ **Datos agregados**: No se almacenan nombres, direcciones, ni identificadores personales
- ✅ **Derecho al olvido**: Datos agregados no permiten identificación de individuos

**Responsable del Tratamiento:**
- Instituto: Duoc UC
- Contacto: [completar con datos institucionales]
- DPO: Disponible bajo solicitud

### 1.2 Ley 19.628 sobre Protección de la Vida Privada - Chile

**✅ Aplica porque:** Proyecto desarrollado y presentado en Chile (Duoc UC).

**Cumplimiento:**
- ✅ Los datos son anónimos y agregados
- ✅ No se almacenan nombres, direcciones, números de cédula
- ✅ Acceso restringido al equipo del proyecto
- ✅ Datos públicos de BigQuery (dataset de dominio público)
- ✅ Consentimiento: No requerido (datos públicos y agregados)

### 1.3 Data Protection Act 2018 (UK)

**✅ Aplica porque:** Datos relacionados con Reino Unido.

**Cumplimiento:**
- ✅ Datos anónimos y agregados
- ✅ No requiere Data Processing Addendum especial
- ✅ Almacenamiento en Supabase (cumple GDPR/UK DPA)

---

## 2. Cifrado

### 2.1 Cifrado en Tránsito (TLS)

| Conexión | Protocolo | Estado | Notas |
|----------|-----------|--------|-------|
| **Frontend → Supabase** | TLS 1.3 | ✅ OK | Supabase fuerza HTTPS por defecto |
| **Backend → Supabase** | TLS 1.3 | ✅ OK | SQLAlchemy + psycopg2-binary |
| **Backend → BigQuery** | TLS 1.3 | ✅ OK | Google Cloud client |
| **Navegador → Frontend (Local)** | HTTP | ⚠️ DEV ONLY | Producción requiere TLS (Vercel usa HTTPS) |

**Vercel Production:**
- ✅ HTTPS automático (certificado Let's Encrypt)
- ✅ HSTS (Strict-Transport-Security) activado
- ✅ Redirección 301 HTTP → HTTPS

### 2.2 Cifrado en Reposo

| Componente | Método | Estado | Gestión |
|------------|--------|--------|---------|
| **Supabase (PostgreSQL)** | AES-256 | ✅ OK | Automático Supabase |
| **Google BigQuery** | AES-256 | ✅ OK | Automático Google |
| **Archivos CSV/Parquet (local)** | Sin cifrar | ⚠️ CUIDADO | Usar disco cifrado (BitLocker/FileVault) |

**Recomendación:** Para producción, cifrar la carpeta `data/` con BitLocker (Windows) o FileVault (macOS).

```bash
# Linux: usar LUKS
sudo cryptsetup luksFormat /path/to/data
sudo cryptsetup luksOpen /path/to/data data_encrypted
```

### 2.3 Configuración de TLS en Producción (Custom Backend)

Si despliegas backend en servidor propio, agrega HTTPS:

```nginx
# infra/nginx.conf (mejorado)
server {
    listen 80;
    server_name tudominio.com;
    # Redireccionar HTTP a HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name tudominio.com;
    
    # Certificados (Certbot + Let's Encrypt)
    ssl_certificate     /etc/letsencrypt/live/tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tudominio.com/privkey.pem;
    
    # Configuración segura
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

---

## 3. Control de Acceso

### 3.1 Supabase Row-Level Security (RLS)

**Política para Frontend (anon_key - Solo lectura):**

```sql
-- En Supabase Dashboard → SQL Editor, ejecutar:

CREATE POLICY "anon_read_london_crime"
ON public.london_crime_aggregated
FOR SELECT
TO anon
USING (true);

-- Verificar que otras operaciones están bloqueadas para anon
-- INSERT, UPDATE, DELETE automáticamente bloqueados
```

**Política para Backend (service_role - CRUD completo):**

```sql
CREATE POLICY "service_write_london_crime"
ON public.london_crime_aggregated
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

**Verificación:**

```sql
-- Ver todas las políticas RLS
SELECT * FROM pg_policies 
WHERE tablename = 'london_crime_aggregated';

-- Ver estado RLS de la tabla
SELECT relname, relrowsecurity FROM pg_class 
WHERE relname = 'london_crime_aggregated';
```

### 3.2 Modelos de Acceso

| Rol | Credencial | Permisos | Propósito |
|-----|-----------|----------|----------|
| **anon** | `VITE_SUPABASE_ANON_KEY` | SELECT only | Frontend users (lectura pública) |
| **service_role** | `SUPABASE_SERVICE_ROLE_KEY` | INSERT, SELECT, UPDATE, DELETE | Backend (pipeline ETL) |
| **authenticated** | Auth token | Configurable | (No usado en este proyecto) |

### 3.3 Principio de Mínimo Privilegio

```bash
# ❌ NUNCA hacer esto:
SUPABASE_DB_URL=postgresql://root:root@host:5432/db

# ✅ HACER esto:
# Crear usuario con permisos limitados
CREATE USER pipeline_user PASSWORD 'strong_random_password';
GRANT INSERT, SELECT, UPDATE ON london_crime_aggregated TO pipeline_user;
REVOKE DELETE ON london_crime_aggregated FROM pipeline_user;
```

---

## 4. Gestión de Secretos

### 4.1 Orden de Precedencia

**Desarrollo Local:**
1. `.env` (proyecto root) ← **PRIMARY**
2. `.env.local` (overrides)
3. Variables de entorno del sistema

**CI/CD (GitHub Actions):**
1. GitHub Secrets (Settings → Secrets and variables → Actions)
2. Variables de entorno injected
3. ⚠️ Nunca hardcodeadas

**Producción (Vercel):**
1. Vercel Environment Variables (Settings → Environment Variables)
2. Inyectadas en build time
3. Protected (no visibles públicamente)

### 4.2 Archivos en .gitignore

**Verificar que .gitignore contiene:**

```bash
# Environment & Secrets
.env
.env.local
.env.*.local
.env.production.local

# Google Cloud
config/credentials.json
!config/.env.example           # SÓLO EL EXAMPLE
!config/boroughs.json
!config/categories.json

# Node
node_modules/
dist/
build/

# Python
__pycache__/
*.pyc
*.pyo
venv/
.pytest_cache/

# Data
data/raw/
data/processed/
data/validated/
data/logs/
data/metrics/

# Models
*.joblib
```

**Verificar que no hay secretos commiteados:**

```bash
# Antes de cada push
git diff --cached --name-only | xargs grep -l "SUPABASE_\|GCP_\|credentials"

# O usar hook
pre-commit install
pre-commit run --all-files
```

### 4.3 Rotación de Credenciales

**Si alguien obtiene acceso a credenciales:**

1. **Supabase anon_key comprometida:**
   ```
   - Ir a Supabase Dashboard → Settings → API Keys
   - Generar nueva key
   - Actualizar VITE_SUPABASE_ANON_KEY en .env local y Vercel
   - La clave antigua se invalida inmediatamente
   ```

2. **Google Cloud credentials.json comprometida:**
   ```
   - Ir a GCP Console → Service Accounts
   - Revocar clave antigua
   - Crear nueva clave
   - Descargar y reemplazar config/credentials.json
   ```

3. **Database password comprometida:**
   ```
   - Cambiar password en Supabase: Settings → Database → Reset password
   - Actualizar SUPABASE_DB_URL en .env backend
   ```

---

## 5. Aislamiento de Contenedores

### 5.1 Non-Root User

**En backend.Dockerfile:**

```dockerfile
# Crear usuario non-root
RUN useradd -m -u 1000 appuser
USER appuser

# Archivos deben ser propiedad de appuser
COPY --chown=appuser:appuser . .
```

**Beneficios:**
- ✅ Si contenedor es comprometido, atacante no obtiene root
- ✅ Imposible modificar archivos del sistema
- ✅ Restricciones de permisos automáticas

### 5.2 Image Security Scanning

**Escanear imagen antes de push:**

```bash
# Usar Trivy (open source)
trivy image datagestor-backend:latest

# Resulta: Muestra CVEs conocidas de dependencias
```

**En CI/CD:**

```yaml
- name: Scan image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: 'datagestor-backend:latest'
    format: 'sarif'
    output: 'trivy-results.sarif'
```

### 5.3 Volúmenes Seguros

```bash
# ❌ NUNCA hacer esto:
docker run -v /:/data datagestor-backend  # Monta ROOT!

# ✅ HACER esto:
docker run -v $(pwd)/data:/app/data datagestor-backend  # Carpeta específica
```

---

## 6. Vulnerabilidades Conocidas

### 6.1 Dependencias Python

**Verificar vulnerabilidades:**

```bash
# Audit de dependencias
pip install safety
safety check

# O con pip-audit
pip install pip-audit
pip-audit
```

**En CI/CD:**

```yaml
- name: Check Python dependencies
  run: pip-audit
```

### 6.2 Dependencias Node.js

**Verificar vulnerabilidades:**

```bash
cd apps/frontend
npm audit

# Fijar vulnerabilidades automáticamente
npm audit fix
```

**En CI/CD:**

```yaml
- name: Check npm vulnerabilities
  run: |
    cd apps/frontend
    npm audit --audit-level=moderate
```

### 6.3 OWASP Top 10 - Checklist

| Vulnerabilidad | Status | Notas |
|---|---|---|
| **A01:2021 – Broken Access Control** | ✅ OK | RLS policies en Supabase |
| **A02:2021 – Cryptographic Failures** | ✅ OK | TLS 1.3, AES-256 at rest |
| **A03:2021 – Injection** | ✅ OK | SQLAlchemy ORM (no SQL injection) |
| **A04:2021 – Insecure Design** | ✅ OK | Este documento (security-first design) |
| **A05:2021 – Security Misconfiguration** | ✅ OK | Configs centralizadas (settings.py) |
| **A06:2021 – Vulnerable Components** | ✅ MONITORAR | Scans automáticos (Trivy, Safety) |
| **A07:2021 – Authentication** | ✅ OK | Delegado a Supabase (OAuth-ready) |
| **A08:2021 – Data Integrity Failures** | ✅ OK | Validación en pipeline (10 etapas) |
| **A09:2021 – Logging & Monitoring** | ⚠️ PARCIAL | Logs locales (mejorar: enviar a cloud) |
| **A10:2021 – SSRF** | ✅ OK | No hay SSRF attacks vectores |

---

## 7. Políticas de RLS en Supabase

### 7.1 Crear Tabla con RLS Habilitado

```sql
-- En Supabase Dashboard → SQL Editor

-- 1. Crear tabla
CREATE TABLE public.london_crime_aggregated (
    id SERIAL PRIMARY KEY,
    borough VARCHAR NOT NULL,
    major_category VARCHAR NOT NULL,
    minor_category VARCHAR NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    total_crimes FLOAT NOT NULL,
    date TIMESTAMP NOT NULL
);

-- 2. Habilitar RLS
ALTER TABLE public.london_crime_aggregated ENABLE ROW LEVEL SECURITY;

-- 3. Crear políticas
CREATE POLICY "anon_read" 
ON public.london_crime_aggregated 
FOR SELECT 
TO anon 
USING (true);

CREATE POLICY "service_role_all" 
ON public.london_crime_aggregated 
FOR ALL 
TO service_role 
USING (true) 
WITH CHECK (true);
```

### 7.2 Verificar Políticas

```sql
-- Ver políticas activas
SELECT * FROM pg_policies 
WHERE tablename = 'london_crime_aggregated';

-- Ver si RLS está habilitado
SELECT relname, relrowsecurity FROM pg_class 
WHERE relname = 'london_crime_aggregated';
```

### 7.3 Testing de RLS

**Test 1: anon no puede INSERT**

```javascript
// Frontend - debe fallar
const { data, error } = await supabase
  .from('london_crime_aggregated')
  .insert([{ borough: 'Test', ... }]);

// Resultado: error.message = "Policy error"
if (error) console.log("✅ RLS working - INSERT bloqueado");
```

**Test 2: service_role puede INSERT**

```javascript
// Backend - debe funcionar
const client = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
const { data, error } = await client
  .from('london_crime_aggregated')
  .insert([{ borough: 'Test', ... }]);

// Resultado: data = [...] sin errores
if (!error) console.log("✅ Service role working");
```

---

## 8. Respuesta a Incidentes

### 8.1 Flujo de Respuesta

```
┌────────────────────────┐
│ 1. Detectar Incidente  │
│    (anomalía, acceso)  │
└───────────┬────────────┘
            │
            v
┌────────────────────────┐
│ 2. Aislar Sistema      │
│    (stop pipeline)     │
└───────────┬────────────┘
            │
            v
┌────────────────────────┐
│ 3. Investigar          │
│    (logs, audits)      │
└───────────┬────────────┘
            │
            v
┌────────────────────────┐
│ 4. Contener Daño       │
│    (rotate creds)      │
└───────────┬────────────┘
            │
            v
┌────────────────────────┐
│ 5. Recuperar           │
│    (restore from backup)
└───────────┬────────────┘
            │
            v
┌────────────────────────┐
│ 6. Post-Mortem         │
│    (prevenir futuro)   │
└────────────────────────┘
```

### 8.2 Checklist Emergencia

**Si hay acceso no autorizado:**

- [ ] Pausar pipeline ETL inmediatamente
- [ ] Revisar logs: `data/logs/pipeline.log`
- [ ] Revisar Supabase logs: Dashboard → Logs
- [ ] Revocar y regenerar TODAS las credenciales
- [ ] Revisar cambios recientes: `git log --oneline -n 20`
- [ ] Ejecutar `git diff main` para ver cambios uncommitted
- [ ] Contactar al equipo de seguridad
- [ ] Documentar el incidente
- [ ] Actualizar políticas para prevenir

### 8.3 Backups

**Supabase proporciona:**
- ✅ Backups diarios automáticos (Free tier: 7 días)
- ✅ Punto-in-time recovery (Plan Pro: 30 días)

**Recuperar backup:**

```bash
# En Supabase Dashboard → Backups
# 1. Seleccionar backup
# 2. Click "Restore"
# 3. Confirmar (borra datos actuales)
```

---

## 9. Auditoría y Compliance

### 9.1 Logging

**Eventos a loguear:**

| Evento | Ubicación | Propósito |
|--------|-----------|----------|
| Pipeline start/end | `data/logs/pipeline.log` | Auditoría de cambios de datos |
| Errores de validación | `data/logs/pipeline.log` | Detección de anomalías |
| Acceso al dashboard | Supabase logs | Quien accede a datos |
| Failed login attempts | Supabase logs | Detección de ataques |

**Analizar logs:**

```bash
# Ver último pipeline
tail -f data/logs/pipeline.log

# Buscar errores
grep ERROR data/logs/pipeline.log

# Ver en Supabase
Dashboard → SQL Editor → SELECT * FROM pg_stat_statements;
```

### 9.2 Retención de Datos

**Política:**

- Raw data (BigQuery): Mantener 3 años (regulatorio)
- Processed data (Supabase): Mantener indefinido (histórico)
- Logs: Retener 90 días (compliance)
- ML models: Mantener versiones importantes

**Limpieza:**

```bash
# Limpiar logs antiguos (> 90 días)
find data/logs -mtime +90 -delete

# Limpiar data/raw/ (> 30 días)
find data/raw -mtime +30 -delete
```

---

## 10. Security Champions

**Responsables de seguridad:**

- **Lead de Seguridad:** [nombre]
- **DevSecOps:** [nombre]
- **DPO (Data Protection Officer):** [nombre]
- **Reportar vulnerabilidades:** security@duoc.cl

**Bug Bounty:** No aplica (proyecto académico)

---

## 📚 Recursos

- [OWASP Top 10](https://owasp.org/Top10/)
- [GDPR for developers](https://developers.google.com/privacy/dprivacy-eng)
- [Supabase Security](https://supabase.com/docs/guides/auth/auth-deep-dive/auth-policies)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Última actualización:** Junio 2026  
**Versión:** 1.1  
**Revisor:** [nombre]  
**Próxima revisión:** Junio 2027
