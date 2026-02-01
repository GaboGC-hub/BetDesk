# 🔍 ANÁLISIS DE ERRORES DEL SCRAPER

## Fecha: 2026-01-29

---

## ✅ Lo que Funciona

1. **Imports del Scheduler** ✅
   - `app.scheduler` se importa correctamente
   - Todas las funciones de jobs están definidas
   - No hay errores de sintaxis

2. **Estructura del Código** ✅
   - `app/ingest/provider_flashscore.py` tiene todas las funciones necesarias:
     - `upcoming_basketball_events()`
     - `upcoming_football_events()`
     - `upcoming_tennis_events()`
     - `odds_for_event()`
     - `scrape_flashscore_odds()`
3. **Event Discovery** ✅
   - `app/ingest/event_discovery.py` tiene:
     - `discover_events_with_fallback()`
     - `discover_basketball_events()`
     - `discover_football_events()`
     - `discover_tennis_events()`
   - Sistema de fallback a mock implementado

---

## ❌ Errores Encontrados

### 1. Error de SQLAlchemy (MENOR)

**Ubicación:** `test_scraper_simple.py` línea 98

**Error:**

```
sqlalchemy.exc.ArgumentError: Textual SQL expression 'SELECT COUNT(*) FROM even...'
should be explicitly declared as text('SELECT COUNT(*) FROM even...')
```

**Causa:**
SQLAlchemy 2.0 requiere que las queries SQL en texto se envuelvan en `text()`

**Solución:**

```python
from sqlalchemy import text
result = session.execute(text("SELECT COUNT(*) FROM events"))
```

**Impacto:** BAJO - Solo afecta al test, no al código de producción

---

### 2. Scraper Lento (ESPERADO)

**Observación:**
El test de `discover_basketball_events()` está tardando porque:

- Usa Playwright (navegador headless)
- Hace scraping real de Flashscore
- Espera 5 segundos para que cargue el contenido dinámico
- Hace scroll para activar lazy loading

**Esto es NORMAL y ESPERADO**

**Tiempos estimados:**

- Event Discovery: 10-15 segundos
- Odds Scraping: 5-10 segundos por mercado

---

## 🔄 Estado Actual del Test

**Test en ejecución:**

```
🏀 TEST: Basketball Event Discovery
📍 Buscando eventos de basketball...
2026-01-29 22:03:35 - betdesk.scraper - INFO - 🏀 Fetching upcoming basketball events...
2026-01-29 22:03:35 - betdesk.scraper - INFO - 🏀 Discovering basketball events...
```

**Esperando:** Que Playwright termine de scrapear Flashscore

---

## 🎯 Posibles Problemas del Scraper

### 1. Flashscore Bloqueando el Scraper

**Síntomas:**

- Timeout después de 30 segundos
- HTML vacío o incompleto
- Captcha o página de error

**Causas:**

- Anti-bot de Flashscore detectando Playwright
- Rate limiting (demasiadas requests)
- IP bloqueada temporalmente

**Soluciones:**

- ✅ Ya implementado: User-Agent realista
- ✅ Ya implementado: Ocultar webdriver
- ✅ Ya implementado: Rate limiting (5 segundos entre requests)
- ⏳ Pendiente: Rotar User-Agents
- ⏳ Pendiente: Usar proxies

### 2. Estructura HTML de Flashscore Cambió

**Síntomas:**

- Scraper retorna 0 eventos
- Logs muestran "No se encontraron links"

**Causas:**

- Flashscore actualizó su HTML
- Clases CSS cambiaron
- Estructura de la página cambió

**Soluciones:**

- Revisar HTML actual con `fetch_event_page_html()`
- Actualizar selectores en `event_discovery.py`
- Usar selectores más robustos (múltiples opciones)

### 3. Eventos en Vivo No Filtrados

**Síntomas:**

- Alertas de partidos que ya empezaron
- Duplicados de Lakers vs Celtics

**Causas:**

- Filtro de eventos en vivo no funciona correctamente
- Marcadores no detectados

**Soluciones:**

- ✅ Ya implementado: Filtro de clases "live", "inprogress", "started"
- ✅ Ya implementado: Detección de marcadores numéricos
- ⏳ Verificar que funciona en producción

---

## 📊 Diagnóstico Recomendado

### Paso 1: Esperar Resultado del Test Actual

- Ver si `discover_basketball_events()` retorna eventos
- Verificar si hay errores de Playwright
- Revisar logs para detectar problemas

### Paso 2: Si el Test Falla

```bash
# Probar manualmente el scraper
python -c "from app.ingest.event_discovery import discover_basketball_events; events = discover_basketball_events(5); print(f'Eventos: {len(events)}')"
```

### Paso 3: Revisar Logs del Servidor

```bash
# Ver logs del servidor en tiempo real
# Buscar errores de scraping
# Verificar si los jobs se ejecutan
```

### Paso 4: Probar con Mock Data

```bash
# Si el scraping falla, verificar que el fallback funciona
python -c "from app.ingest.provider_mock import upcoming_nba_cba_events; events = upcoming_nba_cba_events(); print(f'Mock events: {len(events)}')"
```

---

## 🚀 Próximos Pasos

### Si el Scraper Funciona ✅

1. Dejar que el servidor corra por 10-15 minutos
2. Verificar que se crean eventos en la BD
3. Verificar que se detectan anomalías
4. Verificar que se envían alertas a Telegram

### Si el Scraper Falla ❌

1. Revisar logs detallados
2. Guardar HTML de Flashscore para análisis
3. Actualizar selectores si es necesario
4. Considerar usar API alternativa

---

## 📝 Notas Importantes

1. **El scraper usa fallback automático**
   - Si falla el scraping real, usa datos mock
   - El sistema sigue funcionando
   - No hay downtime

2. **Rate Limiting está implementado**
   - 5 segundos entre requests
   - Evita ser bloqueado por Flashscore
   - Puede hacer el scraping más lento

3. **Playwright es necesario**
   - Flashscore usa JavaScript para cargar contenido
   - `requests` o `BeautifulSoup` solos no funcionan
   - Playwright simula un navegador real

4. **El sistema es robusto**
   - Maneja errores gracefully
   - Logs detallados para debugging
   - Fallback a mock si falla

---

## 🎯 Conclusión Preliminar

**Estado:** 🔄 EN PRUEBA

**Esperando:** Resultado del test de `discover_basketball_events()`

**Próxima acción:** Analizar resultado del test y decidir si:

- ✅ El scraper funciona → Monitorear en producción
- ❌ El scraper falla → Investigar causa y corregir
- ⚠️ El scraper es lento → Optimizar o aceptar tiempos

---

**Última actualización:** 2026-01-29 22:03:35
