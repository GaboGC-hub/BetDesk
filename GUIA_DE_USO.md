# 📖 GUÍA DE USO - BetDesk

## 🎯 ¿Qué es BetDesk?

BetDesk es un **sistema automatizado de análisis de apuestas deportivas** que:

1. 🔍 **Scrapea** eventos y cuotas desde Flashscore
2. 📊 **Analiza** las cuotas usando modelos matemáticos
3. 🚨 **Detecta** anomalías y oportunidades de valor (EV+)
4. 📱 **Envía alertas** a Telegram cuando encuentra oportunidades
5. 🌐 **Muestra** todas las alertas en un dashboard web

---

## 🚀 Cómo Funciona (Paso a Paso)

### 1️⃣ Configuración Inicial

**Requisitos:**

- Python 3.10+
- Docker Desktop (para PostgreSQL)
- Cuenta de Telegram (para recibir alertas)

**Instalación Rápida:**

```bash
# 1. Navegar al proyecto
cd Betplay

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar script de setup automático
python setup.py
```

El script `setup.py` hará automáticamente:

- ✅ Verificar dependencias
- ✅ Crear archivo .env
- ✅ Iniciar Docker (si está instalado)
- ✅ Crear tablas en PostgreSQL

**Instalación Manual (si setup.py falla):**

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Crear archivo .env manualmente
# Copiar este contenido en un archivo llamado .env:
DATABASE_URL=postgresql://betdesk:betdesk@localhost:5432/betdesk
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# 3. Iniciar Docker Desktop manualmente
# Abrir Docker Desktop desde el menú de Windows

# 4. Iniciar base de datos
docker-compose up -d

# 5. Crear tablas
python -c "from app.db import create_tables; create_tables()"
```

**⚠️ Problema Común: Docker no está corriendo**

Si ves este error:

```
unable to get image 'postgres:16': error during connect:
open //./pipe/dockerDesktopLinuxEngine: El sistema no puede encontrar el archivo
```

**Solución:**

1. Abre **Docker Desktop** desde el menú de Windows
2. Espera a que Docker inicie completamente (ícono verde)
3. Ejecuta de nuevo: `docker-compose up -d`

---

### 2️⃣ Iniciar el Sistema

```bash
# Iniciar servidor FastAPI
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**¿Qué pasa al iniciar?**

```
1. ✅ FastAPI se inicia en http://127.0.0.1:8000
2. ✅ Scheduler arranca automáticamente
3. ✅ 10 jobs comienzan a ejecutarse:

   Basketball:
   - job_ingest_basketball (cada 30 min)
   - job_anomalies_basketball (cada 2 min)
   - job_ev_basketball (cada 2 min)

   Football:
   - job_ingest_football (cada 45 min)
   - job_anomalies_football (cada 3 min)
   - job_ev_football (cada 5 min)

   Tennis:
   - job_ingest_tennis (cada 60 min)
   - job_anomalies_tennis (cada 3 min)
   - job_ev_tennis (cada 5 min)

   Utilidades:
   - job_flashscore_smoke (cada 60 min)
```

---

### 3️⃣ Flujo de Trabajo Automático

#### **Cada X Minutos (según el job):**

```
┌─────────────────────────────────────────────────────────┐
│ 1. JOB DE INGESTA (Scraping)                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ a) Scraper descubre eventos próximos:                   │
│    - Basketball: NBA, CBA, Euroleague                   │
│    - Football: Premier League, La Liga, etc.            │
│    - Tennis: ATP, WTA, Grand Slam                       │
│                                                          │
│ b) Para cada evento:                                    │
│    - Extrae: equipos, liga, hora de inicio              │
│    - Guarda en tabla 'events'                           │
│                                                          │
│ c) Extrae cuotas de cada evento:                        │
│    - Basketball: TOTAL, SPREAD, MONEYLINE               │
│    - Football: 1X2, TOTAL, BTTS                         │
│    - Tennis: MONEYLINE, TOTAL_GAMES                     │
│                                                          │
│ d) Guarda cuotas en tabla 'odds'                        │
│                                                          │
│ Ejemplo de log:                                         │
│ ✅ Ingest OK. Events: 13, Odds: 156                     │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 2. JOB DE ANOMALÍAS (Detección)                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ a) Lee últimas cuotas (últimos 60 min)                 │
│                                                          │
│ b) Para cada mercado:                                   │
│    - Agrupa cuotas por evento/mercado/línea             │
│    - Calcula probabilidad implícita de cada bookmaker   │
│    - Calcula media y desviación estándar                │
│    - Identifica outliers (z-score > umbral)             │
│                                                          │
│ c) Si encuentra anomalía:                               │
│    - Crea alerta en tabla 'alerts'                      │
│    - Formatea mensaje con emoji y detalles              │
│    - Envía a Telegram                                   │
│    - Marca como enviada                                 │
│                                                          │
│ Ejemplo de alerta:                                      │
│ 🚨 ANOMALÍA                                             │
│ NBA - Lakers vs Celtics                                 │
│ TOTAL 228.5 OVER @ 2.10 (Bet365)                        │
│ z=2.3                                                   │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 3. JOB DE EV (Expected Value)                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ a) Lee últimas cuotas (últimos 60 min)                 │
│                                                          │
│ b) Para cada cuota:                                     │
│    - Aplica modelo matemático según deporte:           │
│      * Basketball: Distribución Normal                  │
│      * Football: Distribución de Poisson                │
│      * Tennis: Sistema ELO                              │
│                                                          │
│    - Calcula probabilidad "real" del evento             │
│    - Compara con probabilidad implícita de la cuota     │
│    - Calcula EV = p_real * (odds - 1) - (1 - p_real)   │
│                                                          │
│ c) Si EV > umbral (ej. 2%):                             │
│    - Crea alerta en tabla 'alerts'                      │
│    - Formatea mensaje                                   │
│    - Envía a Telegram                                   │
│    - Marca como enviada                                 │
│                                                          │
│ Ejemplo de alerta:                                      │
│ 💰 EV+                                                  │
│ NBA - Lakers vs Celtics                                 │
│ TOTAL 228.5 OVER @ 2.10 (Bet365)                        │
│ EV=0.035  p=0.52                                        │
└─────────────────────────────────────────────────────────┘
```

---

### 4️⃣ Ver las Alertas

#### **Opción 1: Telegram (Tiempo Real)**

Las alertas llegan automáticamente a tu Telegram:

```
📱 Telegram Bot
   ↓
🚨 ANOMALÍA
NBA - Lakers vs Celtics
TOTAL 228.5 OVER @ 2.10 (Bet365)
z=2.3

💰 EV+
Premier League - Man City vs Liverpool
1X2 HOME @ 1.85 (Pinnacle)
EV=0.042  p=0.58
```

#### **Opción 2: Dashboard Web**

Abre tu navegador en: **http://127.0.0.1:8000/alerts**

Verás una tabla con todas las alertas:

| ID  | Sport      | League         | Event                 | Start            | Market | Line  | Sel  | Book     | Odds | Reason  | Score | Sent |
| --- | ---------- | -------------- | --------------------- | ---------------- | ------ | ----- | ---- | -------- | ---- | ------- | ----- | ---- |
| 1   | basketball | NBA            | Lakers vs Celtics     | 2025-01-25 19:30 | TOTAL  | 228.5 | OVER | Bet365   | 2.10 | ANOMALY | 2.3   | ✅   |
| 2   | football   | Premier League | Man City vs Liverpool | 2025-01-25 20:00 | 1X2    | -     | HOME | Pinnacle | 1.85 | EV      | 0.042 | ✅   |

---

## 🔧 Configuración Avanzada

### Ajustar Umbrales

**Archivo:** `app/config/sport_configs.py`

```python
SPORT_CONFIGS = {
    "basketball": {
        "NBA": {
            "anomaly_z_threshold": 1.2,  # Más bajo = más alertas
            "ev_threshold": 0.02,         # 2% EV mínimo
            "min_bookmakers": 2,
        }
    },
    "football": {
        "Premier League": {
            "anomaly_z_threshold": 1.5,
            "ev_threshold": 0.03,         # 3% EV mínimo
            "min_bookmakers": 3,
        }
    }
}
```

### Ajustar Frecuencia de Jobs

**Archivo:** `app/scheduler.py`

```python
# Cambiar minutos aquí:
sched.add_job(job_ingest_basketball, "interval",
              minutes=30,  # <-- Cambiar a 15, 60, etc.
              next_run_time=datetime.now(timezone.utc))
```

### Cambiar Modelos Matemáticos

**Basketball - Archivo:** `app/decision/ev.py`

```python
# Ajustar parámetros de la distribución normal
mu_total = 228.0      # Media de puntos totales NBA
sigma_total = 12.0    # Desviación estándar
```

**Football - Archivo:** `app/decision/football_models.py`

```python
# Ajustar parámetros de Poisson
lambda_home = 1.5     # Goles esperados local
lambda_away = 1.2     # Goles esperados visitante
```

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Monitoreo Pasivo

```bash
# 1. Iniciar sistema
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Dejar corriendo
# El sistema automáticamente:
# - Scrapea eventos cada 30-60 min
# - Analiza cuotas cada 2-5 min
# - Envía alertas a Telegram cuando encuentra oportunidades

# 3. Revisar alertas en:
# - Telegram (tiempo real)
# - http://127.0.0.1:8000/alerts (histórico)
```

### Ejemplo 2: Análisis Manual

```python
# Abrir Python REPL
python

# Importar funciones
from app.ingest.provider_flashscore import upcoming_basketball_events, odds_for_event
from app.decision.ev import prob_over, expected_value

# 1. Ver eventos próximos
events = upcoming_basketball_events(max_events=5)
for e in events:
    print(f"{e['league']}: {e['home']} vs {e['away']}")

# 2. Extraer cuotas de un evento
url = events[0]['flashscore_url']
odds = odds_for_event(url)
for o in odds:
    print(f"{o['market']} {o['line']} {o['selection']} @ {o['odds']} ({o['bookmaker']})")

# 3. Calcular EV manualmente
# Ejemplo: TOTAL 228.5 OVER @ 2.10
mu = 228.0
sigma = 12.0
line = 228.5
odds = 2.10

p = prob_over(mu, sigma, line)
ev = expected_value(p, odds)
print(f"Probabilidad: {p:.3f}")
print(f"EV: {ev:.3f}")
```

### Ejemplo 3: Testing del Scraper

```bash
# Ejecutar tests
python test_scraper_fase3.py

# Ver si el scraper funciona
python -c "from app.ingest.provider_flashscore import test_scraper_connection; test_scraper_connection()"
```

---

## 🎯 Casos de Uso Reales

### Caso 1: Arbitraje de Cuotas

**Escenario:** Diferentes bookmakers tienen cuotas muy diferentes para el mismo evento.

**Cómo BetDesk lo detecta:**

1. Job de anomalías compara cuotas de múltiples bookmakers
2. Calcula z-score de cada cuota
3. Si z > 1.2 (configurable), envía alerta

**Ejemplo de alerta:**

```
🚨 ANOMALÍA
NBA - Lakers vs Celtics
TOTAL 228.5 OVER @ 2.10 (Bet365)
z=2.3

Interpretación:
- La cuota 2.10 es significativamente más alta que el promedio
- Otros bookmakers ofrecen ~1.85
- Posible oportunidad de arbitraje
```

### Caso 2: Value Betting (EV+)

**Escenario:** El modelo matemático estima que un evento tiene más probabilidad de ocurrir que lo que implican las cuotas.

**Cómo BetDesk lo detecta:**

1. Job de EV calcula probabilidad "real" usando modelos
2. Compara con probabilidad implícita de las cuotas
3. Si EV > 2% (configurable), envía alerta

**Ejemplo de alerta:**

```
💰 EV+
NBA - Lakers vs Celtics
TOTAL 228.5 OVER @ 2.10 (Bet365)
EV=0.035  p=0.52

Interpretación:
- Modelo estima 52% de probabilidad de OVER
- Cuota 2.10 implica 47.6% de probabilidad
- EV positivo de 3.5%
- Apuesta con valor esperado positivo
```

### Caso 3: Monitoreo de Ligas Específicas

**Escenario:** Solo te interesan partidos de la NBA.

**Configuración:**

```python
# En app/scheduler.py, comentar jobs que no quieres:

# sched.add_job(job_ingest_football, ...)  # Comentar
# sched.add_job(job_ingest_tennis, ...)    # Comentar

# Dejar solo basketball
sched.add_job(job_ingest_basketball, "interval", minutes=10)
sched.add_job(job_anomalies_basketball, "interval", minutes=2)
sched.add_job(job_ev_basketball, "interval", minutes=2)
```

---

## 🐛 Troubleshooting

### Problema 1: No recibo alertas en Telegram

**Solución:**

```bash
# 1. Verificar variables de entorno
cat .env
# Debe tener:
# TELEGRAM_BOT_TOKEN=...
# TELEGRAM_CHAT_ID=...

# 2. Probar manualmente
python -c "from app.telegram import send_telegram; send_telegram('Test')"

# 3. Verificar que el bot esté iniciado en Telegram
# Buscar tu bot y enviar /start
```

### Problema 2: El scraper no encuentra eventos

**Solución:**

```bash
# 1. Verificar conexión a Flashscore
python -c "from app.ingest.provider_flashscore import test_scraper_connection; test_scraper_connection()"

# 2. El sistema usa fallback a datos mock automáticamente
# Revisar logs:
# ⚠️  No events found for basketball, using fallback

# 3. Ajustar selectores CSS si Flashscore cambió su HTML
# Ver: app/ingest/event_discovery.py
```

### Problema 3: Base de datos no conecta

**Solución:**

```bash
# 1. Verificar que PostgreSQL esté corriendo
docker-compose ps

# 2. Si no está corriendo:
docker-compose up -d

# 3. Crear tablas si no existen:
python -c "from app.db import create_tables; create_tables()"
```

### Problema 4: Demasiadas alertas

**Solución:**

```python
# Ajustar umbrales en app/config/sport_configs.py

# Hacer más estricto (menos alertas):
"anomaly_z_threshold": 2.0,  # Era 1.2
"ev_threshold": 0.05,         # Era 0.02 (5% en vez de 2%)
"min_bookmakers": 5,          # Era 2
```

---

## 📈 Monitoreo del Sistema

### Ver Logs en Tiempo Real

```bash
# Logs del servidor
# Se muestran automáticamente en la terminal donde corriste uvicorn

# Buscar por tipo de log:
# ✅ = Éxito
# ⚠️  = Advertencia
# ❌ = Error
# 🔍 = Scraping
# 📊 = Análisis
# 🚨 = Alerta
```

### Ver Estadísticas

```python
# En Python REPL
from app.ingest.scraper_errors import error_stats

print(error_stats)
# ErrorStats(total=5, types=2, urls=3)

print(error_stats.get_error_rate(100))
# 5.0  (5% de error rate)

print(error_stats.get_most_common_error())
# 'NetworkError'
```

---

## 🎓 Mejores Prácticas

### 1. Empezar con Datos Mock

```python
# Primero probar con datos mock (sin scraping real)
# Los jobs ya tienen fallback automático

# Ver datos mock en:
# app/ingest/provider_mock.py
```

### 2. Ajustar Umbrales Gradualmente

```
Inicio:
- anomaly_z_threshold: 2.0 (conservador)
- ev_threshold: 0.05 (5%)

Después de 1 semana:
- Revisar alertas recibidas
- Si muy pocas: bajar umbrales
- Si demasiadas: subir umbrales

Óptimo (depende de tu estrategia):
- anomaly_z_threshold: 1.2-1.8
- ev_threshold: 0.02-0.04 (2-4%)
```

### 3. Monitorear Rate Limits

```python
# El sistema tiene rate limiting automático
# Pero si Flashscore bloquea tu IP:

# 1. Aumentar delays en app/ingest/scraper_config.py:
SCRAPER_CONFIG = {
    "delay_between_requests": 5.0,  # Era 2.0
    "delay_variance": 2.0,           # Era 1.0
}

# 2. Reducir frecuencia de jobs en app/scheduler.py:
minutes=60  # En vez de 30
```

### 4. Backup de Datos

```bash
# Hacer backup de la base de datos regularmente
docker exec betdesk_db pg_dump -U betdesk betdesk > backup.sql

# Restaurar:
docker exec -i betdesk_db psql -U betdesk betdesk < backup.sql
```

---

## 🎯 Resumen Rápido

**Para empezar en 5 minutos:**

```bash
# 1. Instalar
pip install -r requirements.txt

# 2. Configurar .env
echo "TELEGRAM_BOT_TOKEN=tu_token" > .env
echo "TELEGRAM_CHAT_ID=tu_chat_id" >> .env

# 3. Iniciar BD
docker-compose up -d

# 4. Crear tablas
python -c "from app.db import create_tables; create_tables()"

# 5. Iniciar sistema
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. Ver alertas
# - Telegram: automático
# - Web: http://127.0.0.1:8000/alerts
```

**¡Listo! El sistema está funcionando y enviando alertas automáticamente.**

---

## 📞 Soporte

Si tienes dudas:

1. Revisa esta guía
2. Lee FASE3_COMPLETADO.md para detalles técnicos
3. Ejecuta los tests: `python test_scraper_fase3.py`
4. Revisa los logs del servidor

---

**Versión:** 1.0
**Última actualización:** Enero 2025
