# 🎨 INTEGRACIÓN FRONTEND NEXT.JS - COMPLETADA

## ✅ Cambios Realizados

### 1. **Backend FastAPI - Endpoints API** ✅

**Archivo:** `app/main.py`

**Endpoints agregados:**

```python
# Health check
GET /api/health

# Estadísticas generales
GET /api/stats

# Alertas con filtros
GET /api/alerts?sport=basketball&alert_type=ev+&limit=50

# Lista de deportes
GET /api/sports
```

**CORS configurado:**

```python
allow_origins=[
    "http://localhost:3000",  # Next.js dev
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # FastAPI
    "http://127.0.0.1:8000"
]
```

---

### 2. **Frontend Next.js - Servicio API** ✅

**Archivo:** `betting-dashboard-frontend/lib/api.ts`

**Funciones creadas:**

- `getStats()` - Obtiene estadísticas
- `getAlerts(sport?, type?, limit?)` - Obtiene alertas con filtros
- `getSports()` - Obtiene lista de deportes
- `healthCheck()` - Verifica estado del API

---

### 3. **Frontend Next.js - Dashboard Actualizado** ✅

**Archivo:** `betting-dashboard-frontend/app/page.tsx`

**Características:**

- ✅ Conectado con API real
- ✅ Auto-refresh cada 30 segundos
- ✅ Filtros por deporte y tipo de alerta
- ✅ Estadísticas en tiempo real
- ✅ Formato de fechas en español
- ✅ Loading states
- ✅ Error handling

---

### 4. **Configuración** ✅

**Archivo:** `betting-dashboard-frontend/.env.local`

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Cómo Ejecutar

### Paso 1: Instalar Dependencias del Frontend

```bash
cd betting-dashboard-frontend
npm install
```

### Paso 2: Iniciar Backend FastAPI

```bash
# Desde la raíz del proyecto
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Verificar:**

- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Paso 3: Iniciar Frontend Next.js

```bash
# En otra terminal
cd betting-dashboard-frontend
npm run dev
```

**Verificar:**

- Frontend: http://localhost:3000

---

## 📊 Arquitectura Final

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA BETDESK                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│  Next.js Frontend    │  HTTP   │  FastAPI Backend     │
│  Port: 3000          │ ──────> │  Port: 8000          │
│                      │         │                      │
│  - Dashboard         │         │  - API Endpoints     │
│  - Filtros           │         │  - CORS              │
│  - Auto-refresh      │         │  - Scheduler         │
│  - Real-time data    │         │  - Scrapers          │
└──────────────────────┘         └──────────────────────┘
                                          │
                                          ▼
                                 ┌──────────────────┐
                                 │  PostgreSQL DB   │
                                 │  Port: 5432      │
                                 │                  │
                                 │  - alerts        │
                                 │  - events        │
                                 │  - odds          │
                                 └──────────────────┘
```

---

## 🔧 Endpoints API Disponibles

### 1. Health Check

```bash
GET http://localhost:8000/api/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-30T12:00:00",
  "version": "1.0.0"
}
```

### 2. Estadísticas

```bash
GET http://localhost:8000/api/stats

Response:
{
  "totalAlertas": 150,
  "alertasEV": 45,
  "anomalias": 105,
  "enviadas": 150,
  "lastUpdate": "2024-01-30T12:00:00"
}
```

### 3. Alertas

```bash
GET http://localhost:8000/api/alerts?sport=basketball&alert_type=ev+&limit=10

Response:
{
  "alerts": [
    {
      "id": "123",
      "sport": "basketball",
      "league": "NBA",
      "match": "Lakers vs Celtics",
      "market": "TOTAL",
      "line": 228.5,
      "selection": "OVER",
      "odds": 1.90,
      "bookmaker": "Bwin.co",
      "message": "...",
      "type": "ev+",
      "ev": 8.5,
      "timestamp": "2024-01-30T12:00:00",
      "startTime": "2024-01-30T19:30:00"
    }
  ],
  "total": 1,
  "filters": {
    "sport": "basketball",
    "type": "ev+",
    "limit": 10
  }
}
```

### 4. Deportes

```bash
GET http://localhost:8000/api/sports

Response:
{
  "sports": [
    {"name": "basketball", "count": 50},
    {"name": "football", "count": 30},
    {"name": "tennis", "count": 20}
  ]
}
```

---

## 🧪 Testing

### Test Backend API

```bash
# Health check
curl http://localhost:8000/api/health

# Stats
curl http://localhost:8000/api/stats

# Alerts
curl "http://localhost:8000/api/alerts?limit=5"

# Sports
curl http://localhost:8000/api/sports
```

### Test Frontend

1. Abrir http://localhost:3000
2. Verificar que las estadísticas se cargan
3. Probar filtros de deporte
4. Probar filtros de tipo de alerta
5. Verificar auto-refresh (30 segundos)
6. Verificar botón de refresh manual

---

## 📝 Notas Importantes

### CORS

- El backend está configurado para aceptar requests desde `localhost:3000`
- Si cambias el puerto del frontend, actualiza CORS en `app/main.py`

### Variables de Entorno

- Frontend usa `NEXT_PUBLIC_API_URL` para conectarse al backend
- Por defecto: `http://localhost:8000`
- Cambiar en `.env.local` si es necesario

### Auto-refresh

- El dashboard se actualiza automáticamente cada 30 segundos
- Puedes cambiar el intervalo en `app/page.tsx` (línea 48)

### Filtros

- Los filtros se aplican en el backend
- El frontend solo envía los parámetros de query
- Cambios en filtros recargan las alertas automáticamente

---

## 🎯 Próximos Pasos

### Opcional - Mejoras Futuras:

1. **Autenticación en Frontend**
   - Agregar login page
   - JWT tokens
   - Protected routes

2. **Más Páginas**
   - Historial de alertas
   - Estadísticas detalladas por deporte
   - Configuración de notificaciones

3. **WebSockets**
   - Alertas en tiempo real
   - Sin necesidad de polling

4. **Gráficos**
   - Charts con estadísticas
   - Tendencias históricas
   - Performance de alertas

---

## ✅ Checklist de Verificación

- [x] Backend con endpoints API
- [x] CORS configurado
- [x] Frontend con servicio API
- [x] Dashboard conectado a datos reales
- [x] Filtros funcionando
- [x] Auto-refresh implementado
- [x] Variables de entorno configuradas
- [x] Documentación completa

---

## 🐛 Troubleshooting

### Error: CORS

**Problema:** Frontend no puede conectarse al backend

**Solución:**

1. Verificar que el backend esté corriendo en puerto 8000
2. Verificar CORS en `app/main.py`
3. Verificar `NEXT_PUBLIC_API_URL` en `.env.local`

### Error: No hay datos

**Problema:** Dashboard muestra 0 alertas

**Solución:**

1. Verificar que el backend tenga datos en la BD
2. Ejecutar: `curl http://localhost:8000/api/alerts`
3. Verificar que el scheduler esté corriendo

### Error: TypeScript

**Problema:** Errores de TypeScript en el frontend

**Solución:**

1. Instalar dependencias: `npm install`
2. Los errores desaparecerán después de la instalación

---

**Autor:** BLACKBOXAI  
**Fecha:** 2024-01-30  
**Versión:** 1.0.0
