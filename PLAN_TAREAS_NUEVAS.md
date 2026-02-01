# 📋 PLAN DE TAREAS NUEVAS

## 🎯 Tareas Solicitadas

### 1. ✅ Corregir URL de La Liga

**Estado:** COMPLETADO

**Cambios realizados:**

```python
# app/ingest/event_discovery.py
leagues = [
    {
        "name": "Premier League",
        "url": "https://www.flashscore.co/futbol/inglaterra/premier-league/resultados/"
    },
    {
        "name": "La Liga",
        "url": "https://www.flashscore.co/futbol/espana/laliga-ea-sports/resultados/"  # ✅ CORREGIDO
    },
    {
        "name": "Champions League",
        "url": "https://www.flashscore.co/futbol/europa/champions-league/resultados/"
    }
]
```

---

### 2. ⏳ Sistema de Estadísticas Robusto

**Estado:** PLANIFICADO (NO IMPLEMENTADO)

**Situación actual:**

- ✅ Existe documento `PLAN_ESTADISTICAS_ROBUSTAS.md` con plan detallado
- ❌ NO está implementado el código
- ❌ NO existen las tablas de BD necesarias
- ❌ NO existe el módulo `app/stats/`

**Plan de implementación:**

#### Fase 1: Infraestructura Base (2-3 horas)

```bash
# Crear estructura de módulos
app/stats/
├── __init__.py
├── collector.py      # Recolector principal
├── h2h.py           # Head-to-Head
├── form.py          # Forma reciente
├── trends.py        # Tendencias
└── cache.py         # Sistema de caché
```

#### Fase 2: Tablas de BD (30 min)

```sql
-- sql/stats_schema.sql
CREATE TABLE team_stats (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    team VARCHAR(200),
    season VARCHAR(20),
    games_played INT,
    wins INT,
    losses INT,
    points_avg FLOAT,
    points_against_avg FLOAT,
    home_record VARCHAR(20),
    away_record VARCHAR(20),
    last_updated TIMESTAMP
);

CREATE TABLE h2h_history (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    team_home VARCHAR(200),
    team_away VARCHAR(200),
    date DATE,
    score_home INT,
    score_away INT,
    total_points INT,
    metadata JSONB
);
```

#### Fase 3: Integración con modelos existentes (2-3 horas)

- Modificar `app/decision/anomaly.py` para usar estadísticas
- Modificar `app/decision/ev.py` para usar estadísticas
- Actualizar formatters con información adicional

**Tiempo estimado total:** 5-7 horas

**¿Quieres que implemente esto ahora?**

---

### 3. ⏳ Integrar Frontend Next.js como Principal

**Estado:** FRONTEND EXISTE (NO INTEGRADO)

**Situación actual:**

- ✅ Existe `betting-dashboard-frontend/` con Next.js + TypeScript + Tailwind
- ✅ Tiene componentes UI profesionales
- ❌ NO está conectado al backend FastAPI
- ❌ NO tiene endpoints API configurados
- ❌ Usa datos mock (no reales)

**Arquitectura actual:**

```
Backend (FastAPI):
- Puerto: 8000
- Templates: templates/*.html (Jinja2)
- Endpoints: /api/alerts, /api/stats

Frontend (Next.js):
- Puerto: 3000 (no configurado)
- Componentes: React + TypeScript
- Datos: Mock (hardcoded)
```

**Plan de integración:**

#### Opción A: Frontend Separado (Recomendado)

```
┌─────────────────────┐         ┌─────────────────────┐
│  Next.js Frontend   │  HTTP   │  FastAPI Backend    │
│  Port: 3000         │ ──────> │  Port: 8000         │
│  betting-dashboard- │         │  app/               │
│  frontend/          │         │                     │
└─────────────────────┘         └─────────────────────┘
```

**Pasos:**

1. Agregar endpoints API en FastAPI para el frontend
2. Configurar CORS en FastAPI
3. Crear servicio de API en Next.js
4. Conectar componentes con datos reales
5. Configurar proxy en Next.js

#### Opción B: Frontend Integrado

```
┌─────────────────────────────────────┐
│  FastAPI Backend (Port: 8000)       │
│  ├── /api/*  → API endpoints        │
│  └── /*      → Next.js build        │
└─────────────────────────────────────┘
```

**Pasos:**

1. Build de Next.js (`npm run build`)
2. Servir build desde FastAPI
3. Configurar rutas en FastAPI

**Tiempo estimado:** 3-4 horas

---

## 🚀 Plan de Acción Recomendado

### Prioridad 1: Integrar Frontend (3-4 horas)

**Razón:** El frontend ya está hecho, solo necesita conectarse

**Pasos:**

1. ✅ Agregar endpoints API en FastAPI
2. ✅ Configurar CORS
3. ✅ Crear servicio API en Next.js
4. ✅ Conectar componentes
5. ✅ Documentar setup

### Prioridad 2: Sistema de Estadísticas (5-7 horas)

**Razón:** Mejorará significativamente la calidad de las alertas

**Pasos:**

1. ⏳ Crear módulo `app/stats/`
2. ⏳ Crear tablas de BD
3. ⏳ Implementar scrapers de estadísticas
4. ⏳ Integrar con modelos existentes
5. ⏳ Actualizar formatters

---

## 📊 Resumen de Estado

| Tarea                        | Estado       | Tiempo | Prioridad |
| ---------------------------- | ------------ | ------ | --------- |
| 1. Corregir URL La Liga      | ✅ HECHO     | 5 min  | ALTA      |
| 2. Sistema Estadísticas      | ⏳ PENDIENTE | 5-7h   | MEDIA     |
| 3. Integrar Frontend Next.js | ⏳ PENDIENTE | 3-4h   | ALTA      |

---

## ❓ Preguntas para el Usuario

1. **¿Quieres que implemente el sistema de estadísticas robusto ahora?**
   - Tomará 5-7 horas
   - Mejorará significativamente las alertas
   - Requiere crear nuevas tablas en BD

2. **¿Qué opción prefieres para el frontend?**
   - **Opción A:** Frontend separado (Next.js en puerto 3000)
   - **Opción B:** Frontend integrado (servido desde FastAPI)

3. **¿En qué orden quieres que trabaje?**
   - **Opción 1:** Primero frontend, luego estadísticas
   - **Opción 2:** Primero estadísticas, luego frontend
   - **Opción 3:** Solo frontend (estadísticas después)

---

## 🎯 Próximos Pasos Inmediatos

**Esperando tu respuesta para:**

1. Confirmar si implemento sistema de estadísticas
2. Elegir opción de integración de frontend
3. Definir orden de implementación

**Mientras tanto, puedo:**

- Crear endpoints API básicos para el frontend
- Preparar estructura de módulo de estadísticas
- Documentar arquitectura propuesta
