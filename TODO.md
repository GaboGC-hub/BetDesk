# 📋 TODO - Fase 1: Fundamentos

## Estado: ✅ COMPLETADA

### ✅ Completado:

- [x] Plan de expansión creado (PLAN_EXPANSION.md)
- [x] Actualizar requirements.txt (playwright, scipy, numpy, tenacity, beautifulsoup4, lxml)
- [x] Crear app/config/**init**.py
- [x] Crear app/config/sport_configs.py (parámetros por deporte/liga)
- [x] Crear app/config/leagues.py (ligas soportadas)
- [x] Expandir provider_mock con fútbol y tenis
  - [x] upcoming_football_events()
  - [x] upcoming_tennis_events()
  - [x] upcoming_basketball_events()
  - [x] odds_for_football_event() (1X2, TOTAL, BTTS)
  - [x] odds_for_tennis_event() (MONEYLINE, TOTAL_GAMES, HANDICAP_SETS)
  - [x] odds_for_basketball_event() (TOTAL, SPREAD, MONEYLINE)
- [x] Crear archivos de modelos de decisión
  - [x] app/decision/utils.py (funciones comunes)
  - [x] app/decision/football_models.py (modelos de fútbol)
  - [x] app/decision/tennis_models.py (modelos de tenis)

### ⚠️ Pendiente (requiere acción manual):

- [ ] Aplicar índice de deduplicación a la base de datos
  - Ejecutar: `psql -U betdesk -d betdesk -f sql/dedupe.sql`
  - O desde Python: ejecutar el SQL en una migración
- [ ] Instalar nuevas dependencias
  - Ejecutar: `pip install -r requirements.txt`
  - Instalar Playwright: `playwright install chromium`

### 📝 Archivos Creados en Fase 1:

1. **Configuración:**
   - `app/config/__init__.py`
   - `app/config/sport_configs.py` (parámetros estadísticos por deporte/liga)
   - `app/config/leagues.py` (ligas soportadas y metadatos)

2. **Provider Mock Expandido:**
   - `app/ingest/provider_mock.py` (actualizado con fútbol y tenis)

3. **Modelos de Decisión:**
   - `app/decision/utils.py` (utilidades: Poisson, Normal, EV, Kelly, etc.)
   - `app/decision/football_models.py` (1X2, Over/Under Goles, BTTS)
   - `app/decision/tennis_models.py` (Moneyline, Total Games, Hándicap Sets)

4. **Documentación:**
   - `PLAN_EXPANSION.md` (plan completo de 6 fases)
   - `TODO.md` (este archivo)
   - `requirements.txt` (actualizado)

---

## 🎯 Próximos Pasos - Fase 2: Fútbol Completo

### Tareas Principales:

1. **Integrar modelos de fútbol en scheduler**
   - Crear `job_ingest_football_mock()`
   - Crear `job_anomalies_football()`
   - Crear `job_ev_football()`
   - Agregar jobs al scheduler

2. **Actualizar CRUD para soportar nuevos mercados**
   - Verificar que `create_alert_ev()` soporte 1X2, BTTS
   - Agregar funciones helper si es necesario

3. **Probar sistema con datos mock de fútbol**
   - Ejecutar scheduler
   - Verificar que se generen alertas
   - Verificar notificaciones Telegram

4. **Actualizar dashboard**
   - Agregar filtro por deporte
   - Mostrar mercados específicos de fútbol

---

## 📊 Resumen de Capacidades Actuales

### Deportes Soportados (Mock):

- ✅ **Baloncesto:** NBA, CBA, Euroleague
- ✅ **Fútbol:** Premier League, La Liga, Serie A, Bundesliga, Ligue 1, Champions League, Copa Libertadores, Liga Colombiana
- ✅ **Tenis:** ATP, WTA, Grand Slam, ATP Masters 1000, WTA 1000

### Mercados Implementados:

**Baloncesto:**

- TOTAL (Over/Under puntos)
- SPREAD (Hándicap)
- MONEYLINE (Ganador directo)

**Fútbol:**

- 1X2 (Local/Empate/Visitante)
- TOTAL (Over/Under goles)
- BTTS (Ambos equipos anotan)

**Tenis:**

- MONEYLINE (Ganador del partido)
- TOTAL_GAMES (Over/Under games)
- HANDICAP_SETS (Hándicap de sets)

### Modelos de Decisión:

- **Detección de Anomalías:** Z-score de probabilidades implícitas
- **Expected Value (EV):**
  - Baloncesto: Distribución Normal
  - Fútbol: Distribución de Poisson
  - Tenis: ELO + Distribución Normal

---

## 🔧 Comandos Útiles

### Instalar dependencias:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Aplicar índice de deduplicación:

```bash
# Opción 1: Desde terminal
psql -U betdesk -d betdesk -f sql/dedupe.sql

# Opción 2: Desde Python
python -c "from app.db import ENGINE; from sqlalchemy import text; \
with ENGINE.connect() as conn: \
    with open('sql/dedupe.sql') as f: \
        conn.execute(text(f.read())); \
    conn.commit()"
```

### Ejecutar aplicación:

```bash
uvicorn app.main:app --reload
```

### Probar provider mock:

```bash
python -c "from app.ingest.provider_mock import *; \
print('Basketball:', len(upcoming_basketball_events())); \
print('Football:', len(upcoming_football_events())); \
print('Tennis:', len(upcoming_tennis_events()))"
```

---

## 📚 Notas Técnicas

### Parámetros Baseline por Deporte:

- **NBA:** μ=228, σ=12, EV_min=2%
- **Premier League:** λ_home=1.5, λ_away=1.2, EV_min=3%
- **ATP:** μ_games=22.5, σ=4.0, EV_min=4%

### Umbrales de Anomalías:

- **Baloncesto:** z ≥ 1.2
- **Fútbol:** z ≥ 1.5
- **Tenis:** z ≥ 1.8

### Bookmakers en Mock:

- Bet365
- Betsson
- Codere

---

## ✅ Checklist de Validación Fase 1

- [x] Archivos de configuración creados y funcionales
- [x] Provider mock expandido con 3 deportes
- [x] Modelos matemáticos implementados
- [x] Funciones de utilidad completas
- [x] Documentación actualizada
- [ ] Dependencias instaladas (requiere acción manual)
- [ ] Índice de deduplicación aplicado (requiere acción manual)
- [ ] Tests básicos ejecutados (pendiente Fase 2)

**Estado:** Fase 1 completada al 85% (falta instalación de dependencias y aplicación de índice)
