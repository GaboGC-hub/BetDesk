# 🔄 FLUJO COMPLETO DEL SISTEMA BETDESK

## 📊 ARQUITECTURA GENERAL

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO COMPLETO DEL SISTEMA                    │
└─────────────────────────────────────────────────────────────────┘

1. INGESTIÓN (Scraping)
   ↓
2. ALMACENAMIENTO (Base de Datos)
   ↓
3. MODELOS ESTADÍSTICOS (Cálculo de Probabilidades)
   ↓
4. DECISIÓN (Cálculo de EV y Detección de Anomalías)
   ↓
5. FILTRADO (Picks con EV+ o Z-score alto)
   ↓
6. ALERTAS (Telegram + Dashboard)
```

---

## 1️⃣ INGESTIÓN (Scraping de Flashscore)

### 📁 Archivos Involucrados:

- `app/ingest/event_discovery.py` - Descubre eventos
- `app/ingest/provider_flashscore.py` - Scraping de odds
- `app/scheduler.py` - Jobs automatizados

### 🔄 Proceso:

#### Paso 1.1: Descubrimiento de Eventos

**Archivo:** `app/ingest/event_discovery.py`
**Funciones:**

- `discover_basketball_events()` - NBA, CBA
- `discover_football_events()` - Premier League, La Liga, Champions
- `discover_tennis_events()` - ATP, WTA

**Qué hace:**

```python
# Ejemplo Basketball
1. Accede a: https://www.flashscore.com/basketball/usa/nba/fixtures/
2. Usa Playwright para cargar JavaScript
3. Busca divs con clase "event__match"
4. Extrae: home, away, start_time, league
5. Filtra eventos en vivo (solo futuros)
6. Retorna lista de eventos
```

**Salida:**

```python
{
    "sport": "basketball",
    "league": "NBA",
    "home": "Lakers",
    "away": "Celtics",
    "start_time_utc": datetime(...),
    "flashscore_url": "https://..."
}
```

#### Paso 1.2: Scraping de Odds

**Archivo:** `app/ingest/provider_flashscore.py`
**Función:** `scrape_event_odds(event)`

**Qué hace:**

```python
1. Accede a la URL del evento
2. Busca sección de odds
3. Extrae mercados: TOTAL, SPREAD, MONEYLINE
4. Para cada mercado:
   - Extrae línea (ej: 228.5)
   - Extrae odds (ej: 1.90)
   - Extrae bookmaker (ej: Bwin)
5. Retorna lista de odds
```

**Salida:**

```python
{
    "sport": "basketball",
    "league": "NBA",
    "home": "Lakers",
    "away": "Celtics",
    "market": "TOTAL",
    "line": 228.5,
    "selection": "OVER",
    "odds": 1.90,
    "bookmaker": "Bwin",
    "start_time_utc": datetime(...)
}
```

#### Paso 1.3: Jobs Automatizados

**Archivo:** `app/scheduler.py`
**Jobs de Scraping:**

- `job_scrape_basketball()` - Cada 15 minutos
- `job_scrape_football()` - Cada 20 minutos
- `job_scrape_tennis()` - Cada 20 minutos

**Qué hace:**

```python
def job_scrape_basketball():
    # 1. Descubrir eventos
    events = discover_basketball_events(max_events=20)

    # 2. Para cada evento, scrapear odds
    for event in events:
        odds_list = scrape_event_odds(event)

        # 3. Guardar en BD
        for odd in odds_list:
            insert_odd(odd)  # app/crud.py
```

---

## 2️⃣ ALMACENAMIENTO (PostgreSQL)

### 📁 Archivos Involucrados:

- `app/crud.py` - Operaciones CRUD
- `app/db.py` - Conexión a BD
- `sql/schema.sql` - Esquema de tablas

### 🗄️ Tablas:

#### Tabla: `events`

```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    home VARCHAR(200),
    away VARCHAR(200),
    start_time_utc TIMESTAMP,
    flashscore_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tabla: `odds`

```sql
CREATE TABLE odds (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    event VARCHAR(500),  -- "Lakers vs Celtics"
    market VARCHAR(50),  -- "TOTAL", "SPREAD", "MONEYLINE"
    line DECIMAL(10,2),  -- 228.5
    selection VARCHAR(50), -- "OVER", "UNDER", "HOME", "AWAY"
    odds DECIMAL(10,2),  -- 1.90
    bookmaker VARCHAR(100),
    start_time_utc TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Tabla: `alerts`

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    event VARCHAR(500),
    market VARCHAR(50),
    line DECIMAL(10,2),
    selection VARCHAR(50),
    odds DECIMAL(10,2),
    bookmaker VARCHAR(100),
    message TEXT,  -- Mensaje formateado para Telegram
    start_time_utc TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 3️⃣ MODELOS ESTADÍSTICOS (Cálculo de Probabilidades)

### 📁 Archivos Involucrados:

- `app/decision/football_models.py` - Modelo Poisson
- `app/decision/tennis_models.py` - Modelo ELO
- `app/decision/utils.py` - Modelo Normal (Basketball)

### 🎯 Por Deporte:

#### Basketball: Distribución Normal

**Archivo:** `app/decision/utils.py`
**Función:** `calculate_normal_probabilities()`

**Qué hace:**

```python
def calculate_normal_probabilities(mean: float, std: float, line: float):
    """
    Calcula probabilidades usando distribución normal

    Args:
        mean: Promedio histórico de puntos totales (ej: 225.0)
        std: Desviación estándar (ej: 12.0)
        line: Línea del mercado (ej: 228.5)

    Returns:
        {
            "over": 0.387,  # 38.7% probabilidad de OVER
            "under": 0.613  # 61.3% probabilidad de UNDER
        }
    """
    from scipy.stats import norm

    # Probabilidad de que X > line
    prob_over = 1 - norm.cdf(line, loc=mean, scale=std)
    prob_under = norm.cdf(line, loc=mean, scale=std)

    return {"over": prob_over, "under": prob_under}
```

**Ejemplo:**

```python
# Lakers vs Celtics
# Promedio histórico: 225 puntos
# Desviación: 12 puntos
# Línea: 228.5

probs = calculate_normal_probabilities(225, 12, 228.5)
# Resultado:
# over: 0.387 (38.7%)
# under: 0.613 (61.3%)
```

#### Football: Modelo Poisson

**Archivo:** `app/decision/football_models.py`
**Función:** `calculate_poisson_probabilities()`

**Qué hace:**

```python
def calculate_poisson_probabilities(home_lambda: float, away_lambda: float):
    """
    Calcula probabilidades usando distribución de Poisson

    Args:
        home_lambda: Goles esperados del local (ej: 1.8)
        away_lambda: Goles esperados del visitante (ej: 1.2)

    Returns:
        {
            "home_win": 0.52,  # 52% probabilidad de victoria local
            "draw": 0.25,      # 25% probabilidad de empate
            "away_win": 0.23   # 23% probabilidad de victoria visitante
        }
    """
    from scipy.stats import poisson

    # Simular 10,000 partidos
    max_goals = 10
    prob_matrix = np.zeros((max_goals, max_goals))

    for i in range(max_goals):
        for j in range(max_goals):
            prob_matrix[i, j] = (
                poisson.pmf(i, home_lambda) *
                poisson.pmf(j, away_lambda)
            )

    # Sumar probabilidades
    home_win = np.sum(np.tril(prob_matrix, -1))  # Local > Visitante
    draw = np.sum(np.diag(prob_matrix))          # Local = Visitante
    away_win = np.sum(np.triu(prob_matrix, 1))   # Local < Visitante

    return {
        "home_win": home_win,
        "draw": draw,
        "away_win": away_win
    }
```

#### Tennis: Modelo ELO

**Archivo:** `app/decision/tennis_models.py`
**Función:** `calculate_elo_probabilities()`

**Qué hace:**

```python
def calculate_elo_probabilities(elo_home: float, elo_away: float):
    """
    Calcula probabilidades usando sistema ELO

    Args:
        elo_home: Rating ELO del jugador 1 (ej: 2100)
        elo_away: Rating ELO del jugador 2 (ej: 1950)

    Returns:
        {
            "home_win": 0.76,  # 76% probabilidad jugador 1
            "away_win": 0.24   # 24% probabilidad jugador 2
        }
    """
    # Fórmula ELO
    expected_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
    expected_away = 1 - expected_home

    return {
        "home_win": expected_home,
        "away_win": expected_away
    }
```

---

## 4️⃣ DECISIÓN (Cálculo de EV y Detección de Anomalías)

### 📁 Archivos Involucrados:

- `app/decision/ev.py` - **AQUÍ SE CALCULA EV**
- `app/decision/anomaly.py` - Detección de anomalías
- `app/scheduler.py` - Jobs de análisis

### 💰 CÁLCULO DE EV (Expected Value)

**Archivo:** `app/decision/ev.py`
**Función:** `calculate_ev_for_odd()`

**⭐ AQUÍ SE CALCULA EL EV:**

```python
def calculate_ev_for_odd(odd: dict, model_prob: float) -> float:
    """
    Calcula Expected Value (EV) de una apuesta

    Args:
        odd: {
            "odds": 1.90,
            "selection": "OVER",
            ...
        }
        model_prob: Probabilidad calculada por el modelo (ej: 0.45 = 45%)

    Returns:
        EV en decimal (ej: 0.05 = 5% de EV positivo)

    Fórmula:
        EV = (Probabilidad × Ganancia) - (1 - Probabilidad) × Pérdida
        EV = (model_prob × (odds - 1)) - ((1 - model_prob) × 1)
    """
    odds_decimal = odd["odds"]

    # Ganancia si gana: (odds - 1) × apuesta
    # Pérdida si pierde: 1 × apuesta

    ev = (model_prob * (odds_decimal - 1)) - ((1 - model_prob) * 1)

    return ev

# EJEMPLO REAL:
# Odd: Over 228.5 @ 1.90
# Probabilidad del modelo: 45% (0.45)
#
# EV = (0.45 × (1.90 - 1)) - ((1 - 0.45) × 1)
# EV = (0.45 × 0.90) - (0.55 × 1)
# EV = 0.405 - 0.55
# EV = -0.145 (EV negativo, NO apostar)
#
# Si la probabilidad fuera 60%:
# EV = (0.60 × 0.90) - (0.40 × 1)
# EV = 0.54 - 0.40
# EV = 0.14 (14% de EV positivo, ¡APOSTAR!)
```

### 📊 Detección de Anomalías

**Archivo:** `app/decision/anomaly.py`
**Función:** `detect_anomalies()`

**Qué hace:**

```python
def detect_anomalies(odds_snapshot: List[dict]) -> List[dict]:
    """
    Detecta odds anómalas usando Z-score

    Args:
        odds_snapshot: Lista de odds del mismo mercado

    Returns:
        Lista de odds con Z-score > 2.0

    Proceso:
        1. Agrupar odds por mercado (ej: TOTAL Over 228.5)
        2. Calcular media y desviación estándar
        3. Calcular Z-score para cada odd
        4. Filtrar Z-score > 2.0 (anomalías)
    """
    import numpy as np

    # Agrupar por mercado
    grouped = {}
    for odd in odds_snapshot:
        key = f"{odd['market']}_{odd['line']}_{odd['selection']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(odd['odds'])

    anomalies = []

    for key, odds_list in grouped.items():
        if len(odds_list) < 3:
            continue

        mean = np.mean(odds_list)
        std = np.std(odds_list)

        for odd in odds_snapshot:
            odd_key = f"{odd['market']}_{odd['line']}_{odd['selection']}"
            if odd_key == key:
                z_score = abs((odd['odds'] - mean) / std) if std > 0 else 0

                if z_score > 2.0:  # Anomalía
                    anomalies.append({
                        **odd,
                        "z_score": z_score
                    })

    return anomalies
```

---

## 5️⃣ FILTRADO (Picks con EV+ o Z-score alto)

### 📁 Archivo: `app/scheduler.py`

### 🎯 **AQUÍ SE FILTRAN LOS PICKS:**

#### Job 1: EV Positivo (Basketball)

**Función:** `job_ev_baseline()`

```python
def job_ev_baseline():
    """
    Job que filtra picks con EV positivo para basketball

    Ejecuta cada 2 minutos
    """
    logger.info("🎯 Running EV baseline job (basketball)...")

    # 1. Obtener odds recientes (últimos 60 minutos)
    rows = fetch_latest_odds_snapshot(minutes=60, sport="basketball")

    if not rows:
        logger.info("No basketball odds found")
        return

    # 2. Para cada odd, calcular EV
    for row in rows:
        # 2.1 Calcular probabilidad con modelo
        mean = 225.0  # Promedio histórico (simplificado)
        std = 12.0    # Desviación estándar
        line = row['line']

        probs = calculate_normal_probabilities(mean, std, line)

        # 2.2 Obtener probabilidad según selección
        if row['selection'] == 'OVER':
            model_prob = probs['over']
        else:
            model_prob = probs['under']

        # 2.3 Calcular EV
        ev = calculate_ev_for_odd(row, model_prob)

        # ⭐ FILTRO: Solo picks con EV > 3%
        if ev > 0.03:  # EV positivo mayor a 3%
            # 3. Crear alerta
            message = format_alert_basketball_ev(row, ev, model_prob)

            # 4. Guardar en BD
            insert_alert({
                **row,
                "message": message
            })

            # 5. Enviar a Telegram
            send_telegram_alert(message)

            logger.info(f"✅ EV+ pick: {row['event']} - EV: {ev*100:.1f}%")
```

#### Job 2: Anomalías (Basketball)

**Función:** `job_anomalies()`

```python
def job_anomalies():
    """
    Job que filtra picks con anomalías (Z-score alto)

    Ejecuta cada 2 minutos
    """
    logger.info("📊 Running anomaly detection (basketball)...")

    # 1. Obtener odds recientes
    rows = fetch_latest_odds_snapshot(minutes=30, sport="basketball")

    if not rows:
        return

    # 2. Detectar anomalías
    anomalies = detect_anomalies(rows)

    # ⭐ FILTRO: Solo Z-score > 2.0
    for anomaly in anomalies:
        if anomaly['z_score'] > 2.0:
            # 3. Crear alerta
            message = format_alert_basketball_anomaly(
                anomaly,
                anomaly['z_score']
            )

            # 4. Guardar en BD
            insert_alert({
                **anomaly,
                "message": message
            })

            # 5. Enviar a Telegram
            send_telegram_alert(message)

            logger.info(f"⚠️ Anomaly: {anomaly['event']} - Z: {anomaly['z_score']:.2f}")
```

---

## 6️⃣ ALERTAS (Telegram + Dashboard)

### 📁 Archivos Involucrados:

- `app/telegram.py` - Envío a Telegram
- `app/formatters.py` - Formato de mensajes
- `app/main.py` - API para dashboard

### 📱 Telegram

**Archivo:** `app/telegram.py`
**Función:** `send_telegram_alert()`

```python
def send_telegram_alert(message: str):
    """
    Envía alerta a Telegram

    Args:
        message: Mensaje HTML formateado
    """
    import requests

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }

    response = requests.post(url, json=payload)

    if response.status_code == 200:
        logger.info("✅ Telegram alert sent")
    else:
        logger.error(f"❌ Telegram error: {response.text}")
```

### 🖥️ Dashboard

**Archivo:** `app/main.py`
**Endpoints:**

```python
@app.get("/api/alerts")
async def get_alerts_api(
    sport: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 50
):
    """
    Obtiene alertas para el dashboard

    Query params:
        - sport: basketball, football, tennis
        - alert_type: ev+, anomalia
        - limit: número máximo

    Returns:
        {
            "alerts": [...],
            "total": 10
        }
    """
    # Consultar BD
    alerts = fetch_alerts_from_db(sport, alert_type, limit)

    return {
        "alerts": alerts,
        "total": len(alerts)
    }
```

---

## 📊 RESUMEN DEL FLUJO

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO PASO A PASO                             │
└─────────────────────────────────────────────────────────────────┘

1. SCRAPING (cada 15-20 min)
   ├─ discover_basketball_events() → Lista de eventos
   ├─ scrape_event_odds(event) → Lista de odds
   └─ insert_odd(odd) → Guardar en BD

2. MODELOS (cuando se ejecutan jobs de análisis)
   ├─ Basketball: calculate_normal_probabilities()
   ├─ Football: calculate_poisson_probabilities()
   └─ Tennis: calculate_elo_probabilities()

3. CÁLCULO DE EV (cada 2 min) ⭐ AQUÍ SE CALCULA EV
   ├─ fetch_latest_odds_snapshot() → Obtener odds
   ├─ calculate_ev_for_odd(odd, prob) → Calcular EV
   └─ if EV > 3%: crear alerta

4. DETECCIÓN DE ANOMALÍAS (cada 2-3 min)
   ├─ fetch_latest_odds_snapshot() → Obtener odds
   ├─ detect_anomalies(odds) → Calcular Z-scores
   └─ if Z-score > 2.0: crear alerta

5. FILTRADO ⭐ AQUÍ SE FILTRAN PICKS
   ├─ EV > 3% → Pick EV+
   └─ Z-score > 2.0 → Pick Anomalía

6. ALERTAS
   ├─ insert_alert() → Guardar en BD
   ├─ send_telegram_alert() → Enviar a Telegram
   └─ API /api/alerts → Mostrar en dashboard
```

---

## 🎯 PUNTOS CLAVE

### ¿Dónde se calcula EV?

**Archivo:** `app/decision/ev.py`
**Función:** `calculate_ev_for_odd()`
**Fórmula:** `EV = (prob × (odds - 1)) - ((1 - prob) × 1)`

### ¿Dónde se filtran picks?

**Archivo:** `app/scheduler.py`
**Jobs:**

- `job_ev_baseline()` - Filtra EV > 3%
- `job_anomalies()` - Filtra Z-score > 2.0

### ¿Cada cuánto se ejecuta?

- Scraping: 15-20 minutos
- Análisis EV: 2 minutos
- Análisis Anomalías: 2-3 minutos

---

**¡Este es el flujo completo del sistema BetDesk!** 🚀
