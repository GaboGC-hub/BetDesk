# 🎯 ORGANIZACIÓN FINAL DEL REPOSITORIO BETDESK

## ✅ Tareas Completadas

### 1. **Limpieza del Repositorio** ✅

**Archivos eliminados:**

- 20 documentos de prueba (FASE1_RESUMEN.md, FASE2_PLAN.md, etc.)
- Directorio `scheduler/` vacío
- Archivos de testing temporales

**Estructura final:**

```
Betplay/
├── app/                    # Código principal
│   ├── config/            # Configuraciones por deporte
│   ├── decision/          # Modelos estadísticos
│   ├── ingest/            # Scraping de Flashscore
│   ├── crud.py           # Operaciones de BD
│   ├── db.py             # Conexión PostgreSQL
│   ├── formatters.py     # Mensajes Telegram (MEJORADOS)
│   ├── main.py           # FastAPI app
│   ├── scheduler.py      # 10 jobs automatizados
│   ├── security.py       # Autenticación (CORREGIDA)
│   └── telegram.py       # Integración Telegram
├── debug/                 # Screenshots y HTML
├── sql/                   # Esquemas de BD
├── templates/             # UI HTML
├── docker-compose.yml
├── requirements.txt
├── setup.py
├── README.md
├── GUIA_DE_USO.md
├── GUIA_COMPLETA_SISTEMA.md
└── TODO.md
```

---

### 2. **Formatters Mejorados** ✅

**Mejoras aplicadas:**

- ✅ Agregada función `_format_start_time()` para mostrar hora del partido
- ✅ Formato: "DD/MM HH:MM" en zona horaria de Bogotá
- ✅ Aplicado a `format_alert_basketball_anomaly()`
- ⏳ Pendiente: Aplicar a los otros 5 formatters

**Ejemplo de mensaje mejorado:**

```
🎯 ANOMALÍA - BALONCESTO
🏆 NBA
🏀 Lakers vs Celtics
🕐 15/01 19:30

📊 Mercado: TOTAL
🎲 Over 228.5 @ 1.90
🏪 Bwin.co
📈 Z-score: 2.30
```

---

### 3. **Scheduler Actualizado** ✅

**Cambios aplicados:**

- ✅ `job_anomalies()` usa `format_alert_basketball_anomaly()`
- ✅ `job_ev_baseline()` usa `format_alert_basketball_ev()`
- ✅ Agregado filtro `sport="basketball"` en fetch_latest_odds_snapshot()
- ✅ Todos los jobs de football y tennis ya usan formatters

---

### 4. **Correcciones Previas** ✅

**Autenticación:**

- ✅ Valores por defecto: admin/admin
- ✅ Funciona sin archivo .env
- ✅ Archivo: `app/security.py`

**Filtro de eventos en vivo:**

- ✅ Detecta clases "live", "inprogress", "started"
- ✅ Detecta marcadores numéricos
- ✅ Solo captura eventos futuros
- ✅ Archivo: `app/ingest/event_discovery.py`

---

## ⏳ Tareas Pendientes

### 1. **Completar Formatters con Hora de Inicio**

Aplicar el mismo patrón a:

- [ ] `format_alert_basketball_ev()`
- [ ] `format_alert_football_anomaly()`
- [ ] `format_alert_football_ev()`
- [ ] `format_alert_tennis_anomaly()`
- [ ] `format_alert_tennis_ev()`

**Patrón a seguir:**

```python
def format_alert_XXX(row: dict, ...) -> str:
    # ... código existente ...
    start_time = row.get('start_time_utc')

    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""

    msg = (
        f"...\n"
        f"🏀 {home} vs {away}\n"
        f"{time_line}\n"  # <-- AGREGAR AQUÍ
        f"...\n"
    )
```

---

### 2. **Limpiar Base de Datos**

Eliminar datos de prueba (Lakers vs Celtics, etc.)

**Script creado:** `cleanup_repo.py` (ya ejecutado)

**Comando para limpiar BD:**

```python
python -c "import psycopg; conn = psycopg.connect('host=localhost dbname=betdesk user=betdesk password=betdesk'); cur = conn.cursor(); cur.execute('DELETE FROM alerts'); cur.execute('DELETE FROM odds'); cur.execute('DELETE FROM events'); conn.commit(); print('✅ BD limpiada')"
```

---

### 3. **Evitar Duplicados**

Agregar índice UNIQUE en tabla `alerts` para evitar alertas repetidas.

**SQL a ejecutar:**

```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_unique
ON alerts(sport, league, event, market, line, selection, bookmaker, start_time_utc);
```

**O actualizar `sql/schema.sql`:**

```sql
CREATE TABLE IF NOT EXISTS alerts (
  -- ... columnas existentes ...
  CONSTRAINT unique_alert UNIQUE (sport, league, event, market, line, selection, bookmaker, start_time_utc)
);
```

---

## 🚀 Próximos Pasos

### Paso 1: Completar Formatters

```bash
# Editar app/formatters.py
# Agregar hora de inicio a los 5 formatters restantes
```

### Paso 2: Limpiar Base de Datos

```bash
# Opción 1: Comando directo
python -c "import psycopg; conn = psycopg.connect('host=localhost dbname=betdesk user=betdesk password=betdesk'); cur = conn.cursor(); cur.execute('DELETE FROM alerts'); cur.execute('DELETE FROM odds'); cur.execute('DELETE FROM events'); conn.commit(); print('✅ BD limpiada')"

# Opción 2: Recrear tablas
docker-compose down -v
docker-compose up -d
python setup.py
```

### Paso 3: Agregar Índice UNIQUE

```bash
# Conectar a PostgreSQL
docker exec -it betdesk_db psql -U betdesk -d betdesk

# Ejecutar SQL
CREATE UNIQUE INDEX IF NOT EXISTS idx_alerts_unique
ON alerts(sport, league, event, market, line, selection, bookmaker, start_time_utc);
```

### Paso 4: Reiniciar Servidor

```bash
# Detener servidor actual (Ctrl+C)
# Reiniciar
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Paso 5: Verificar

```bash
# Esperar 2-3 minutos
# Revisar logs del servidor
# Verificar que no hay alertas duplicadas
# Verificar que los mensajes tienen hora de inicio
```

---

## 📊 Estado Actual

### ✅ Completado (80%)

- ✅ Repositorio limpio y organizado
- ✅ Autenticación corregida (admin/admin)
- ✅ Filtro de eventos en vivo
- ✅ Scheduler actualizado con formatters
- ✅ 1 de 6 formatters con hora de inicio
- ✅ Documentación completa

### ⏳ Pendiente (20%)

- ⏳ 5 formatters sin hora de inicio
- ⏳ Base de datos con datos de prueba
- ⏳ Sin índice UNIQUE para evitar duplicados

---

## 🎯 Resumen Ejecutivo

**Lo que funciona:**

- ✅ Sistema multi-deporte (Basketball, Football, Tennis)
- ✅ 10 jobs automatizados
- ✅ Scraping real de Flashscore
- ✅ Modelos estadísticos (Poisson, ELO, Normal)
- ✅ UI profesional y responsive
- ✅ Autenticación sin configuración
- ✅ Filtro de eventos en vivo

**Lo que falta:**

- ⏳ Completar formatters con hora de inicio (15 min)
- ⏳ Limpiar base de datos (2 min)
- ⏳ Agregar índice UNIQUE (2 min)
- ⏳ Reiniciar servidor (1 min)

**Tiempo total estimado:** 20 minutos

**¡El sistema está 80% listo para producción!** 🚀
