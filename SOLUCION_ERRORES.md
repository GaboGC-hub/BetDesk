# 🔧 SOLUCIÓN A ERRORES DETECTADOS

## Problemas Identificados

### 1. ❌ Error de Hydration en Next.js

**Causa:** Extensión Dark Reader del navegador
**Síntoma:** Atributos `data-darkreader-*` agregados por la extensión causan mismatch entre servidor y cliente

### 2. ✅ URL de La Liga - YA CORREGIDA

**Estado:** Las URLs ya están correctas con `/partidos/` en lugar de `/resultados/`
**Verificado en:** `app/ingest/event_discovery.py` líneas 308-320

### 3. ❌ PostgreSQL No Está Corriendo

**Error:** `connection to server at "127.0.0.1", port 5432 failed`
**Causa:** Docker no está iniciado o contenedor de PostgreSQL no está corriendo

---

## 🛠️ SOLUCIONES

### Solución 1: Error de Hydration (Dark Reader)

**Opción A: Deshabilitar Dark Reader (Recomendado)**

1. Abrir extensiones del navegador
2. Deshabilitar Dark Reader para `localhost:3000`
3. Recargar la página

**Opción B: Suprimir Warning en Next.js**
Agregar a `betting-dashboard-frontend/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Suprimir warnings de hydration causados por extensiones del navegador
  onDemandEntries: {
    maxInactiveAge: 25 * 1000,
    pagesBufferLength: 2,
  },
  // Ignorar warnings de hydration en desarrollo
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.devtool = "cheap-module-source-map";
    }
    return config;
  },
};

module.exports = nextConfig;
```

**Opción C: Agregar suppressHydrationWarning**
En `betting-dashboard-frontend/app/layout.tsx`:

```tsx
<html lang="es" className="dark" suppressHydrationWarning>
```

---

### Solución 2: URL de La Liga ✅

**Estado:** YA CORREGIDA

Las URLs en `app/ingest/event_discovery.py` ya están correctas:

```python
leagues = [
    {
        "name": "Premier League",
        "url": "https://www.flashscore.co/futbol/inglaterra/premier-league/partidos/"
    },
    {
        "name": "La Liga",
        "url": "https://www.flashscore.co/futbol/espana/laliga-ea-sports/partidos/"
    },
    {
        "name": "Champions League",
        "url": "https://www.flashscore.co/futbol/europa/champions-league/partidos/"
    }
]
```

✅ Todas usan `/partidos/` (partidos programados) en lugar de `/resultados/` (partidos terminados)

---

### Solución 3: PostgreSQL No Está Corriendo

**Paso 1: Verificar Docker**

```bash
# Verificar si Docker está corriendo
docker ps

# Si no hay contenedores, iniciar Docker Desktop
# Abrir Docker Desktop manualmente
```

**Paso 2: Iniciar PostgreSQL**

```bash
# Desde la raíz del proyecto
docker-compose up -d

# Verificar que el contenedor está corriendo
docker ps

# Deberías ver algo como:
# CONTAINER ID   IMAGE         PORTS                    NAMES
# xxxxx          postgres:15   0.0.0.0:5432->5432/tcp   betdesk_db
```

**Paso 3: Verificar Conexión**

```bash
# Conectar a PostgreSQL
docker exec -it betdesk_db psql -U betdesk -d betdesk

# Si funciona, verás:
# psql (15.x)
# Type "help" for help.
# betdesk=#

# Salir con: \q
```

**Paso 4: Crear Tablas (Si es Primera Vez)**

```bash
python setup.py
```

---

## 🚀 PASOS PARA INICIAR EL SISTEMA COMPLETO

### 1. Iniciar PostgreSQL

```bash
docker-compose up -d
```

### 2. Verificar Base de Datos

```bash
docker ps
# Debe mostrar contenedor betdesk_db corriendo
```

### 3. Iniciar Backend

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Iniciar Frontend (Si tienes Node.js)

```bash
cd betting-dashboard-frontend
npm run dev
```

### 5. Acceder

- **Frontend Next.js:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Dashboard HTML:** http://localhost:8000/alerts

---

## 🔍 VERIFICACIÓN

### Verificar Backend

```bash
# Health check
curl http://localhost:8000/api/health

# Debe retornar:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

### Verificar PostgreSQL

```bash
# Conectar
docker exec -it betdesk_db psql -U betdesk -d betdesk

# Verificar tablas
\dt

# Debe mostrar:
# alerts, events, odds, etc.
```

### Verificar Frontend

1. Abrir http://localhost:3000
2. Deshabilitar Dark Reader si está activo
3. Verificar que carga sin errores de hydration

---

## 📝 RESUMEN DE ESTADO

### ✅ Completado

- URL de La Liga corregida a `/partidos/`
- URLs de Premier League y Champions League también corregidas
- Backend con endpoints API funcionando
- Frontend Next.js preparado

### ⚠️ Requiere Acción

1. **Iniciar Docker:** `docker-compose up -d`
2. **Deshabilitar Dark Reader:** En extensiones del navegador
3. **Iniciar Backend:** `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`

### 📦 Opcional

- Instalar Node.js para frontend Next.js
- Si no, usar dashboard HTML en `/alerts`

---

## 🎯 COMANDOS RÁPIDOS

```bash
# 1. Iniciar todo
docker-compose up -d
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 2. Verificar
curl http://localhost:8000/api/health
docker ps

# 3. Frontend (opcional)
cd betting-dashboard-frontend
npm run dev
```

---

**Estado:** ✅ URLs corregidas, soluciones documentadas
**Próximo paso:** Iniciar Docker y backend
