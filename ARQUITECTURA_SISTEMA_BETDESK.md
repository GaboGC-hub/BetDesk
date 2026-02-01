# 🏗️ ARQUITECTURA DEL SISTEMA BETDESK

## 📋 Documento para IA de Mejora de Frontend

Este documento explica la arquitectura completa del sistema BetDesk para que puedas mejorar el frontend con conocimiento profundo del backend.

---

## 🎯 VISIÓN GENERAL

BetDesk es un sistema de alertas de apuestas deportivas que:
1. **Scrapea** eventos deportivos de Flashscore (NBA, CBA, Football, Tennis)
2. **Analiza** cuotas usando modelos estadísticos
3. **Detecta** anomalías y oportunidades de valor esperado (EV+)
4. **Envía** alertas automáticas vía Telegram
5. **Muestra** dashboard web con todas las alertas

---

## 📊 FLUJO DE DATOS

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLASHSCORE.COM                                │
│         (Fuente de datos de eventos y cuotas)                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Playwright + BeautifulSoup
                         │ (Web Scraping)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              EVENT DISCOVERY MODULE                              │
│  app/ingest/event_discovery.py                                   │
│                                                                   │
│  • discover_basketball_events() → NBA + CBA                      │
│  • discover_football_events() → Premier, La Liga, etc.           │
│  • discover_tennis_events() → ATP, WTA, Grand Slams              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Eventos estructurados
                         │ {sport, league, home, away, start_time, url}
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   POSTGRESQL DATABASE                            │
│                                                                   │
│  Tablas:                                                          │
│  • events (partidos)                                              │
│  • odds (cuotas por bookmaker)                                    │
│  • alerts (alertas generadas)                                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ SQL Queries
                         │ (app/crud.py)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SCHEDULER (APScheduler)                         │
│  app/scheduler.py                                                 │
│                                                                   │
│  10 JOBS AUTOMATIZADOS:                                           │
│                                                                   │
│  🏀 BASKETBALL (3 jobs):                                          │
│     • job_ingest_mock() - Cada 10 min                            │
│     • job_anomalies() - Cada 2 min                               │
│     • job_ev_baseline() - Cada 2 min                             │
│                                                                   │
│  ⚽ FOOTBALL (3 jobs):                                            │
│     • job_ingest_mock_football() - Cada 15 min                   │
│     • job_anomalies_football() - Cada 3 min                      │
│     • job_ev_football() - Cada 5 min                             │
│                                                                   │
│  🎾 TENNIS (3 jobs):                                              │
│     • job_ingest_mock_tennis() - Cada 20 min                     │
│     • job_anomalies_tennis() - Cada 3 min                        │
│     • job_ev_tennis() - Cada 5 min                               │
│                                                                   │
│  🔧 UTILS (1 job):                                                │
│     • job_flashscore_smoke() - Cada 60 min                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Análisis de cuotas
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              MODELOS ESTADÍSTICOS                                │
│                                                                   │
│  🏀 BASKETBALL (app/decision/ev.py):                             │
│     • Distribución Normal                                         │
│     • μ (media) = 228 puntos (NBA), 210 (CBA)                    │
│     • σ (desviación) = 12 (NBA), 14 (CBA)                        │
│     • Calcula P(Over/Under)                                       │
│                                                                   │
│  ⚽ FOOTBALL (app/decision/football_models.py):                  │
│     • Modelo de Poisson                                           │
│     • λ_home, λ_away (goles esperados)                           │
│     • Calcula P(1X2), P(BTTS), P(Over/Under goles)              │
│                                                                   │
│  🎾 TENNIS (app/decision/tennis_models.py):                      │
│     • Sistema ELO                                                 │
│     • Distribución Normal para juegos totales                     │
│     • Calcula P(Moneyline), P(Over/Under games)                  │
│                                                                   │
│  📊 ANOMALÍAS (app/decision/anomaly.py):                         │
│     • Z-score = (odd - μ) / σ                                    │
│     • Detecta cuotas anormales (|Z| > threshold)                 │
│     • Compara entre múltiples bookmakers                          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Alertas generadas
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FORMATTERS                                    │
│  app/formatters.py                                                │
│                                                                   │
│  Genera mensajes HTML para Telegram:                              │
│  • format_alert_basketball_anomaly()                              │
│  • format_alert_basketball_ev()                                   │
│  • format_alert_football_anomaly()                                │
│  • format_alert_football_ev()                                     │
│  • format_alert_tennis_anomaly()                                  │
│  • format_alert_tennis_ev()                                       │
│                                                                   │
│  Incluye:                                                         │
│  • Emojis por deporte/mercado                                     │
│  • Hora de inicio (zona horaria Bogotá)                          │
│  • Información del partido                                        │
│  • Cuota y bookmaker                                              │
│  • Z-score o EV%                                                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Mensajes formateados
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  TELEGRAM BOT                                    │
│  app/telegram.py                                                  │
│                                                                   │
│  Características:                                                 │
│  • Retry logic (3 intentos con exponential backoff)              │
│  • Manejo de rate limiting (429 errors)                          │
│  • Logging detallado                                              │
│  • Soporte para botones inline                                    │
│  • Formato HTML                                                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ Notificaciones
                         ▼
                    👤 USUARIO
                         │
                         │ Acceso web
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI WEB APP                               │
│  app/main.py                                                      │
│                                                                   │
│  ENDPOINTS:                                                       │
│  • GET  /              → Página de login                         │
│  • POST /login         → Autenticación                           │
│  • GET  /dashboard     → Dashboard principal                     │
│  • GET  /api/alerts    → API JSON de alertas                     │
│  • GET  /logout        → Cerrar sesión                           │
│                                                                   │
│  AUTENTICACIÓN:                                                   │
│  • Usuario: admin                                                 │
│  • Password: admin                                                │
│  • Session-based (cookies)                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTML + JavaScript
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (templates/)                         │
│                                                                   │
│  📄 index.html:                                                   │
│     • Página de login                                             │
│     • Diseño minimalista                                          │
│                                                                   │
│  📄 dashboard.html:                                               │
│     • 4 tarjetas de estadísticas                                  │
│     • 6 filtros (deporte, liga, mercado, etc.)                   │
│     • Tabla de alertas con paginación                             │
│     • Auto-refresh cada 30 segundos                               │
│     • Diseño responsive (mobile-first)                            │
│     • Tema oscuro profesional                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ ESTRUCTURA DE ARCHIVOS

```
BetDesk/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app principal
│   ├── db.py                      # Conexión PostgreSQL
│   ├── crud.py                    # Operaciones de BD
│   ├── scheduler.py               # 10 jobs automatizados
│   ├── security.py                # Autenticación
│   ├── telegram.py                # Integración Telegram
│   ├── formatters.py              # Formateo de mensajes
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── sport_configs.py      # Configuración por deporte
│   │   └── leagues.py             # Configuración por liga
│   │
│   ├── decision/
│   │   ├── __init__.py
│   │   ├── anomaly.py             # Detección de anomalías
│   │   ├── ev.py                  # Cálculo de EV
│   │   ├── football_models.py     # Modelos de fútbol
│   │   ├── tennis_models.py       # Modelos de tenis
│   │   └── utils.py               # Utilidades estadísticas
│   │
│   └── ingest/
│       ├── __init__.py
│       ├── event_discovery.py     # Scraping de eventos
│       ├── provider_flashscore.py # Scraping de cuotas
│       ├── scraper_config.py      # Configuración scraper
│       ├── odds_parser.py         # Parseo de cuotas
│       └── html_utils.py          # Utilidades HTML
│
├── templates/
│   ├── index.html                 # Página de login
│   ├── dashboard.html             # Dashboard principal
│   ├── alerts.html                # Vista de alertas
│   └── login_info.html            # Info de login
│
├── sql/
│   ├── schema.sql                 # Esquema de BD
│   └── odds_schema.sql            # Esquema de cuotas
│
├── docker-compose.yml             # PostgreSQL container
├── requirements.txt               # Dependencias Python
├── setup.py                       # Script de inicialización
└── README.md                      # Documentación
```

---

## 🔑 CONCEPTOS CLAVE

### 1. **Anomalías (Z-Score)**

```python
# Detecta cuotas anormalmente altas o bajas
Z = (odd - μ) / σ

Ejemplo:
- Cuota normal Over 228.5: 1.90 (μ = 1.90, σ = 0.10)
- Cuota anómala Over 228.5: 2.30 (Z = 4.0) ← ALERTA!
```

### 2. **Expected Value (EV)**

```python
# Calcula si una apuesta tiene valor esperado positivo
EV = (P × Odd) - 1

Ejemplo:
- P(Over 228.5) = 0.55 (modelo)
- Odd = 2.00 (bookmaker)
- EV = (0.55 × 2.00) - 1 = 0.10 = 10% ← ALERTA!
```

### 3. **Modelos Estadísticos**

**Basketball (Normal):**
```python
μ = 228 puntos (NBA)
σ = 12 puntos
P(Over 228.5) = 1 - Φ((228.5 - 228) / 12)
```

**Football (Poisson):**
```python
λ_home = 1.5 goles
λ_away = 1.2 goles
P(Home Win) = Σ P(home=i) × P(away<i)
```

**Tennis (ELO):**
```python
P(A gana) = 1 / (1 + 10^((ELO_B - ELO_A) / 400))
```

---

## 📡 API ENDPOINTS

### GET /api/alerts

Retorna alertas en formato JSON:

```json
{
  "alerts": [
    {
      "id": 123,
      "sport": "basketball",
      "league": "NBA",
      "event": "Lakers vs Celtics",
      "market": "TOTAL",
      "selection": "OVER",
      "line": 228.5,
      "odds": 1.90,
      "bookmaker": "Bwin.co",
      "reason": "anomaly",
      "score": 2.30,
      "start_time_utc": "2025-01-30T19:30:00Z",
      "created_at_utc": "2025-01-30T18:00:00Z",
      "sent_at_utc": "2025-01-30T18:00:05Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

### Filtros disponibles:

- `?sport=basketball` - Filtrar por deporte
- `?league=NBA` - Filtrar por liga
- `?market=TOTAL` - Filtrar por mercado
- `?reason=anomaly` - Filtrar por tipo (anomaly/ev)
- `?sent=true` - Solo alertas enviadas
- `?page=1&per_page=50` - Paginación

---

## 🎨 FRONTEND ACTUAL

### Dashboard (dashboard.html)

**Características:**
- ✅ 4 tarjetas de estadísticas (Total, Enviadas, Pendientes, Tasa éxito)
- ✅ 6 filtros interactivos
- ✅ Tabla responsive con paginación
- ✅ Auto-refresh cada 30 segundos
- ✅ Tema oscuro profesional
- ✅ Mobile-first design

**Tecnologías:**
- HTML5 + CSS3
- JavaScript vanilla (sin frameworks)
- Fetch API para llamadas AJAX
- CSS Grid + Flexbox

**Colores:**
```css
--bg-dark: #1a1a2e
--bg-card: #16213e
--accent: #0f3460
--primary: #e94560
--text: #ffffff
--text-muted: #a0a0a0
```

---

## 💡 OPORTUNIDADES DE MEJORA FRONTEND

### 1. **Visualizaciones**
- Gráficos de tendencias (Chart.js)
- Heatmap de cuotas por bookmaker
- Timeline de alertas
- Distribución de Z-scores

### 2. **Interactividad**
- Filtros avanzados con búsqueda
- Ordenamiento por columna
- Exportar a CSV/Excel
- Notificaciones push en navegador

### 3. **UX/UI**
- Animaciones suaves
- Loading skeletons
- Toast notifications
- Modal para detalles de alerta

### 4. **Performance**
- Virtual scrolling para tablas grandes
- Lazy loading de imágenes
- Service Worker para offline
- Caché inteligente

### 5. **Funcionalidades**
- Favoritos/Watchlist
- Historial de alertas
- Comparador de bookmakers
- Calculadora de apuestas

---

## 🔧 TECNOLOGÍAS USADAS

**Backend:**
- Python 3.11
- FastAPI (web framework)
- PostgreSQL (base de datos)
- SQLAlchemy (ORM)
- APScheduler (jobs automatizados)
- Playwright (web scraping)
- BeautifulSoup4 (HTML parsing)
- Requests (HTTP client)

**Frontend:**
- HTML5
- CSS3 (Grid, Flexbox)
- JavaScript (ES6+)
- Fetch API

**DevOps:**
- Docker (PostgreSQL container)
- Git (control de versiones)

---

## 📊 DATOS DE EJEMPLO

### Alerta de Anomalía (Basketball):
```
🎯 ANOMALÍA - BALONCESTO
🏆 NBA
🏀 Lakers vs Celtics
🕐 30/01 19:30

📊 Mercado: TOTAL
🎲 Over 228.5 @ 1.90
🏪 Bwin.co
📈 Z-score: 2.30
```

### Alerta de EV+ (Football):
```
⚽ EV+ FÚTBOL
🏆 Premier League
⚽ Arsenal vs Chelsea
🕐 30/01 15:00

📊 Mercado: 1X2
🎲 🏠 Arsenal @ 2.10
🏪 Bet365
💰 EV: 8.5%
📊 Prob: 52.0%
```

---

## 🚀 CÓMO EJECUTAR

```bash
# 1. Iniciar PostgreSQL
docker-compose up -d

# 2. Crear tablas
python setup.py

# 3. Iniciar servidor
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4. Abrir navegador
http://localhost:8000

# Login: admin / admin
```

---

## 📝 NOTAS IMPORTANTES

1. **Scraping Real:** El sistema usa Playwright para scrapear Flashscore en tiempo real
2. **Rate Limiting:** Hay delays entre requests para evitar bloqueos
3. **Filtro de Eventos en Vivo:** Solo captura eventos futuros, no en vivo
4. **Zona Horaria:** Todas las horas se muestran en zona horaria de Bogotá
5. **Telegram:** Requiere TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env

---

## 🎯 PRÓXIMOS PASOS SUGERIDOS

1. **Mejorar scrapers** para más ligas (Euroleague, Serie A, etc.)
2. **Implementar ML** para predicciones más precisas
3. **Agregar APIs externas** (The Odds API, API-Football)
4. **Sistema de backtesting** para validar modelos
5. **Dashboard de estadísticas** avanzadas
6. **Mobile app** (React Native o Flutter)

---

**Desarrollado por:** BLACKBOXAI  
**Cliente:** Gabo  
**Versión:** 2.0  
**Fecha:** 30 Enero 2025

---

**¡Usa este documento como referencia para mejorar el frontend!** 🚀
