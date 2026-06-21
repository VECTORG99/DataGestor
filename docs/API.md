# 📡 API Reference - DataGestor

## Índice

- [1. API Supabase (PostgREST)](#1-api-supabase-postgrest)
- [2. Paginación y Filtrado](#2-paginación-y-filtrado)
- [3. Endpoints Principal](#3-endpoints-principal)
- [4. Autenticación](#4-autenticación)
- [5. Row-Level Security (RLS)](#5-row-level-security-rls)
- [6. Ejemplos de Código](#6-ejemplos-de-código)
- [7. Troubleshooting](#7-troubleshooting)

---

## 1. API Supabase (PostgREST)

DataGestor no tiene backend REST personalizado. Todo acceso a datos es a través de la **Supabase PostgREST API**.

### Base URL

```
https://<PROJECT_REF>.supabase.co/rest/v1
```

**Ejemplo:**
```
https://xxxxxxxxxxxx.supabase.co/rest/v1/london_crime_aggregated
```

### Headers Requeridos

```http
Authorization: Bearer <ANON_KEY o SERVICE_ROLE_KEY>
Content-Type: application/json
Accept: application/json
```

### Respuesta Estándar

```json
{
    "id": 1,
    "borough": "Westminster",
    "major_category": "Robbery",
    "minor_category": "Robbery of personal property",
    "year": 2015,
    "month": 6,
    "total_crimes": 125.5,
    "date": "2015-06-01T00:00:00Z"
}
```

---

## 2. Paginación y Filtrado

### Paginación (Range)

**Límite por request**: 1,000 filas máximo

```http
GET /london_crime_aggregated?limit=1000&offset=0
Authorization: Bearer ANON_KEY

# Headers
Range: rows=0-999      # Sintaxis alternativa
Prefer: count=exact    # Obtener total count
```

**JavaScript:**
```javascript
const { data, count } = await supabase
    .from('london_crime_aggregated')
    .select('*', { count: 'exact' })
    .range(0, 999);

console.log(`Total: ${count}, Returned: ${data.length}`);
```

### Filtrado

```http
GET /london_crime_aggregated?borough=eq.Westminster&year=eq.2015
Authorization: Bearer ANON_KEY
```

**Operadores de filtro:**

| Operador | Sintaxis | Ejemplo |
|----------|----------|---------|
| **Equal** | `field=eq.value` | `borough=eq.Westminster` |
| **Not equal** | `field=neq.value` | `borough=neq.Croydon` |
| **Greater than** | `field=gt.value` | `year=gt.2012` |
| **Less than** | `field=lt.value` | `total_crimes=lt.100` |
| **In** | `field=in.(value1,value2)` | `borough=in.(Westminster,Croydon)` |
| **Contains** | `field=like.*pattern*` | `major_category=like.*Robbery*` |
| **Null** | `field=is.null` | `borough=is.null` |

**JavaScript:**
```javascript
const { data } = await supabase
    .from('london_crime_aggregated')
    .select('*')
    .eq('borough', 'Westminster')
    .eq('year', 2015)
    .lt('total_crimes', 100);
```

### Ordenamiento

```http
GET /london_crime_aggregated?order=borough.asc,total_crimes.desc
Authorization: Bearer ANON_KEY
```

**JavaScript:**
```javascript
const { data } = await supabase
    .from('london_crime_aggregated')
    .select('*')
    .order('total_crimes', { ascending: false })
    .order('borough', { ascending: true });
```

---

## 3. Endpoints Principal

### GET /london_crime_aggregated

**Obtener todos los registros (con paginación).**

**Request:**
```http
GET /london_crime_aggregated?limit=10&offset=0
Authorization: Bearer ANON_KEY
```

**Response (200 OK):**
```json
[
    {
        "id": 1,
        "borough": "Westminster",
        "major_category": "Robbery",
        "minor_category": "Robbery of personal property",
        "year": 2015,
        "month": 6,
        "total_crimes": 125.5,
        "date": "2015-06-01T00:00:00Z"
    },
    ...
]
```

**Query Parameters:**

| Param | Tipo | Default | Máximo | Ejemplo |
|-------|------|---------|--------|---------|
| `limit` | integer | 1000 | 1000 | `?limit=100` |
| `offset` | integer | 0 | N/A | `?offset=1000` |
| `order` | string | - | - | `?order=borough.asc` |
| `select` | string | * | - | `?select=borough,year,total_crimes` |

### GET /london_crime_aggregated?count=exact

**Obtener total de registros (para paginación).**

**Request:**
```http
GET /london_crime_aggregated?count=exact&limit=0
Authorization: Bearer ANON_KEY
```

**Response:**
```
Content-Range: 0-0/77524
```

```javascript
const { count } = await supabase
    .from('london_crime_aggregated')
    .select('*', { count: 'exact', head: true });

console.log(`Total records: ${count}`);  // 77524
```

### GET /london_crime_aggregated (con filtros)

**Obtener registros filtrados.**

**Request:**
```http
GET /london_crime_aggregated?borough=eq.Westminster&year=gte.2010&year=lte.2015&major_category=eq.Robbery&limit=100
Authorization: Bearer ANON_KEY
```

**JavaScript:**
```javascript
const { data } = await supabase
    .from('london_crime_aggregated')
    .select('*')
    .eq('borough', 'Westminster')
    .eq('major_category', 'Robbery')
    .gte('year', 2010)
    .lte('year', 2015)
    .limit(100);
```

### GET /london_crime_aggregated (Agregaciones)

**Sumarizaciones:**

```javascript
// Obtener suma total de crímenes por borough
const { data } = await supabase.rpc('get_crimes_by_borough');

// O query manual (si no existe RPC)
const { data } = await supabase
    .from('london_crime_aggregated')
    .select('borough, total_crimes')
    .order('total_crimes', { ascending: false });
```

### POST /london_crime_aggregated (Backend Only)

**Insertar registros (solo service_role).**

**Request:**
```http
POST /london_crime_aggregated
Authorization: Bearer SERVICE_ROLE_KEY
Content-Type: application/json

{
    "borough": "Westminster",
    "major_category": "Robbery",
    "minor_category": "Robbery of personal property",
    "year": 2015,
    "month": 6,
    "total_crimes": 125.5,
    "date": "2015-06-01T00:00:00Z"
}
```

**Response (201 Created):**
```json
{
    "id": 77525,
    "borough": "Westminster",
    "major_category": "Robbery",
    "minor_category": "Robbery of personal property",
    "year": 2015,
    "month": 6,
    "total_crimes": 125.5,
    "date": "2015-06-01T00:00:00Z"
}
```

---

## 4. Autenticación

### Frontend (Anon Key)

**Credenciales públicas - Solo lectura.**

```javascript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
    import.meta.env.VITE_SUPABASE_URL,
    import.meta.env.VITE_SUPABASE_ANON_KEY
);

// Automáticamente incluye el anon_key en Authorization header
const { data } = await supabase
    .from('london_crime_aggregated')
    .select('*')
    .limit(10);
```

### Backend (Service Role Key)

**Credenciales privadas - CRUD completo.**

```python
from supabase import create_client

supabase = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_SERVICE_ROLE_KEY
)

# INSERT con service_role
response = supabase.table('london_crime_aggregated').insert([
    {
        'borough': 'Westminster',
        'major_category': 'Robbery',
        'minor_category': 'Robbery of personal property',
        'year': 2015,
        'month': 6,
        'total_crimes': 125.5,
        'date': '2015-06-01T00:00:00Z'
    }
]).execute()
```

### Errores de Autenticación

```
401 Unauthorized - No Authorization header
403 Forbidden - Token inválido o expirado
```

---

## 5. Row-Level Security (RLS)

### Política: Lectura Pública (anon)

```sql
CREATE POLICY "anon_read_london_crime"
ON public.london_crime_aggregated
FOR SELECT
TO anon
USING (true);
```

**Permitir:** `SELECT * FROM london_crime_aggregated`  
**Bloquear:** `INSERT`, `UPDATE`, `DELETE`

### Política: Full Access (service_role)

```sql
CREATE POLICY "service_role_full_access"
ON public.london_crime_aggregated
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);
```

**Permitir:** `SELECT`, `INSERT`, `UPDATE`, `DELETE`

### Verificar RLS

```sql
-- Ver si RLS está habilitado
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'london_crime_aggregated';

-- Ver políticas activas
SELECT * FROM pg_policies 
WHERE tablename = 'london_crime_aggregated';
```

---

## 6. Ejemplos de Código

### Ejemplo 1: Dashboard Inicial (Frontend)

```javascript
// Cargar KPIs
async function loadDashboard() {
    try {
        // Step 1: Get total count
        const { count } = await supabase
            .from('london_crime_aggregated')
            .select('*', { count: 'exact', head: true });

        // Step 2: Get sample data
        const { data } = await supabase
            .from('london_crime_aggregated')
            .select('borough, major_category, total_crimes')
            .limit(1000)
            .order('total_crimes', { ascending: false });

        // Step 3: Calculate KPIs
        const totalCrimes = data.reduce((sum, row) => sum + row.total_crimes, 0);
        const topBorough = data[0]?.borough;
        const topCategory = [...new Set(data.map(r => r.major_category))][0];

        return {
            totalCount: count,
            totalCrimes: totalCrimes.toFixed(0),
            topBorough,
            topCategory
        };
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}
```

### Ejemplo 2: Filtrado de Datos (Frontend)

```javascript
async function filterData(borough, category, year) {
    let query = supabase
        .from('london_crime_aggregated')
        .select('*');

    if (borough) query = query.eq('borough', borough);
    if (category) query = query.eq('major_category', category);
    if (year) query = query.eq('year', year);

    const { data, error } = await query.limit(1000);

    if (error) {
        console.error('Filter error:', error);
        return [];
    }

    return data;
}
```

### Ejemplo 3: Paginación Paralela (Frontend)

```javascript
async function fetchAllDataParallel() {
    try {
        // Step 1: Get total
        const { count } = await supabase
            .from('london_crime_aggregated')
            .select('*', { count: 'exact', head: true });

        // Step 2: Crear batch queries
        const batchSize = 1000;
        const batches = [];

        for (let i = 0; i < count; i += batchSize) {
            batches.push(
                supabase
                    .from('london_crime_aggregated')
                    .select('*')
                    .range(i, Math.min(i + batchSize - 1, count - 1))
            );
        }

        // Step 3: Ejecutar en paralelo (10 concurrent)
        const results = [];
        for (let i = 0; i < batches.length; i += 10) {
            const batch = batches.slice(i, i + 10);
            const responses = await Promise.all(batch);
            results.push(...responses.map(r => r.data).flat());
        }

        return results;
    } catch (error) {
        console.error('Pagination error:', error);
        return [];
    }
}
```

### Ejemplo 4: Cargar Datos (Backend)

```python
from supabase import create_client
import pandas as pd

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Leer DataFrame limpio
df_clean = pd.read_csv('data/processed/london_crime_processed.csv')

# Convertir a lista de dicts
records = df_clean.to_dict('records')

# Insertar en lotes
batch_size = 1000
for i in range(0, len(records), batch_size):
    batch = records[i:i + batch_size]
    response = supabase.table('london_crime_aggregated').insert(batch).execute()
    print(f"Inserted {len(batch)} rows")
```

---

## 7. Troubleshooting

### Error: 401 Unauthorized

**Causa:** Token inválido o expirado

**Solución:**
```javascript
// Verificar VITE_SUPABASE_ANON_KEY en .env.local
console.log(import.meta.env.VITE_SUPABASE_ANON_KEY);

// Debe empezar con: eyJhbGciOi...
```

### Error: 403 Forbidden

**Causa:** RLS policy bloqueó la operación

**Solución:**
```sql
-- Verificar RLS policies
SELECT * FROM pg_policies WHERE tablename = 'london_crime_aggregated';

-- Si está bloqueado, ejecutar como admin:
ALTER POLICY "anon_read_london_crime" ON london_crime_aggregated
FOR SELECT TO anon USING (true);
```

### Error: 413 Payload Too Large

**Causa:** Intentar insertar demasiadas filas en un request

**Solución:**
```python
# Dividir en lotes
batch_size = 1000
for i in range(0, len(records), batch_size):
    supabase.table('london_crime_aggregated').insert(records[i:i + batch_size]).execute()
```

### Tiempo de Respuesta Lento

**Causa:** Query sin índices

**Solución:**
```sql
-- Crear índices
CREATE INDEX idx_borough ON london_crime_aggregated(borough);
CREATE INDEX idx_year_month ON london_crime_aggregated(year, month);
```

### Limite de Rate (429 Too Many Requests)

**Causa:** Demasiados requests simultáneos

**Solución:**
```javascript
// Limitar concurrencia
const maxConcurrent = 10;
for (let i = 0; i < batches.length; i += maxConcurrent) {
    await Promise.all(batches.slice(i, i + maxConcurrent).map(fetch));
}
```

---

## Rate Limits

| Métrica | Límite | Renovación |
|---------|--------|-----------|
| **API Requests** | Unlimited | N/A (Supabase manages) |
| **Database Connections** | 100 concurrent | Per account |
| **Row Batch Size** | 1,000 rows | Per request |
| **Query Timeout** | 30 segundos | Per query |

---

**Última actualización:** Junio 2026  
**Versión:** 1.0  
**Mantenedor:** [nombre]
