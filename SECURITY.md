# Plan de Seguridad - DataGestor

## 1. Marco Legal Aplicable

### 1.1 Reglamento General de Protección de Datos (GDPR) - UE
- **Aplica porque**: Los datos procesados incluyen información de crímenes en Londres (Reino Unido).
- **Cumplimiento**:
  - Minimización de datos: solo se almacenan campos necesarios para el análisis (borough, categorías, fechas, valores agregados).
  - Limitación de finalidad: los datos se usan exclusivamente para análisis estadístico de seguridad pública.
  - Transparencia: el pipeline documenta cada transformación aplicada.

### 1.2 Ley 19.628 sobre Protección de la Vida Privada - Chile
- **Aplica porque**: El proyecto es desarrollado y presentado en Chile (Duoc UC).
- **Cumplimiento**:
  - Los datos son anónimos y agregados (no incluyen información personal identificable).
  - No se almacenan nombres, direcciones, ni identificadores personales.
  - El acceso está restringido al equipo del proyecto.

## 2. Cifrado

### 2.1 Cifrado en Tránsito (TLS)
| Capa | Método | Estado |
|------|--------|--------|
| Frontend -> Supabase | TLS 1.3 | [OK] Supabase fuerza HTTPS por defecto |
| Pipeline -> Supabase | TLS 1.3 | [OK] SQLAlchemy + `psycopg2-binary` usan TLS |
| Pipeline -> BigQuery | TLS 1.3 | [OK] Cliente de Google Cloud usa HTTPS |
| Navegador -> Frontend | HTTP (puerto 5173) | [!] Produccion requiere TLS (ver seccion 2.3) |

### 2.2 Cifrado en Reposo
| Componente | Método | Estado |
|------------|--------|--------|
| Supabase (PostgreSQL) | Cifrado AES-256 | [OK] Activado por defecto |
| BigQuery | Cifrado AES-256 | [OK] Activado por defecto |
| Archivos CSV/Parquet locales | Sin cifrar | [!] Almacenamiento local temporal |

### 2.3 Configuración de TLS en Producción
Para entornos productivos, agregar un proxy reverso con certificado TLS:

```nginx
# infra/nginx.conf
server {
    listen 80;
    server_name tudominio.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name tudominio.com;

    ssl_certificate     /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        root   /usr/share/nginx/html;
        index  index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

## 3. Control de Acceso

### 3.1 Supabase Row-Level Security (RLS)
```sql
-- Política de solo lectura para anon_key
CREATE POLICY "anon_read_london_crime"
ON public.london_crime_aggregated
FOR SELECT
TO anon
USING (true);

-- Solo el service_role puede insertar/actualizar/eliminar
CREATE POLICY "service_write_london_crime"
ON public.london_crime_aggregated
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

### 3.2 Principio de Mínimo Privilegio
| Recurso | Credencial | Permisos |
|---------|-----------|----------|
| Frontend | `VITE_SUPABASE_ANON_KEY` | Solo SELECT en `london_crime_aggregated` |
| Backend | `SUPABASE_DB_URL` (service_role) | INSERT, SELECT, UPDATE, DELETE |
| Backend | `credentials.json` (GCP service account) | Solo lectura en `bigquery-public-data` |
| Repositorio | Ninguna secreto expuesto | Todos los secretos en `.gitignore` |

## 4. Prácticas DataOps Seguras

### 4.1 Gestión de Secretos
- `.env` y `*.local` están en `.gitignore` - nunca se suben al repositorio.
- `config/credentials.json` está en `.gitignore`.
- Variables de entorno inyectadas vía Docker Compose o archivo `.env`.
- En CI/CD, las credenciales se pasan como variables de entorno (`secrets`).

### 4.2 Aislamiento de Contenedores
- Cada servicio corre en su propio contenedor Docker.
- El frontend (Nginx) solo sirve archivos estáticos - no ejecuta lógica sensible.
- El backend (Python) tiene acceso solo a los volúmenes necesarios.

### 4.3 Logging Seguro
- Los logs (`pipeline.log`) no registran credenciales ni tokens.
- Los errores de conexión registran el tipo de error, no la contraseña.

## 5. Matriz de Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Exposición de anon_key | Alta | Bajo | RLS restringe a solo SELECT |
| Fuga de service_role URL | Baja | Alto | Solo en `.env` local, no en repo |
| Intercepción de tráfico | Baja | Medio | TLS en todas las conexiones externas |
| Acceso no autorizado a datos | Baja | Medio | RLS + mínimo privilegio |
| Pérdida de datos en reposo | Baja | Alto | Supabase backups automáticos |

## 6. Checklist de Seguridad

- [x] Secretos en `.gitignore`
- [x] RLS configurado en Supabase (solo lectura para anon)
- [x] TLS en conexiones externas (Supabase, BigQuery)
- [x] Principio de mínimo privilegio aplicado
- [ ] Certificado TLS para frontend en producción
- [ ] Auditoría periódica de accesos a Supabase
- [ ] Rotación de credenciales cada 90 días
