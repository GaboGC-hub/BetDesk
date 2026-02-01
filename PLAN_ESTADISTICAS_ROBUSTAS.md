# 📊 PLAN: SISTEMA DE ESTADÍSTICAS ROBUSTO

## 🎯 Objetivo

Implementar un sistema de análisis estadístico avanzado que combine múltiples fuentes de datos para generar predicciones más precisas y alertas de mayor calidad.

---

## 🏗️ Arquitectura del Sistema

### 1. **Módulo de Recolección de Estadísticas**

```
app/stats/
├── __init__.py
├── collector.py          # Recolector principal
├── h2h.py               # Head-to-Head (enfrentamientos directos)
├── form.py              # Forma reciente (últimos partidos)
├── trends.py            # Tendencias (local/visitante)
├── player_stats.py      # Estadísticas de jugadores clave
└── cache.py             # Sistema de caché
```

### 2. **Fuentes de Datos**

- **Flashscore:** Resultados históricos, calendarios
- **API-Football:** Estadísticas detalladas de fútbol
- **The Odds API:** Movimiento de líneas
- **Base de datos local:** Historial acumulado

### 3. **Modelos Estadísticos Mejorados**

#### **Basketball (NBA/Euroleague)**

```python
Factores a considerar:
✅ Distribución Normal actual (mu=228, sigma=12)
+ Forma reciente (últimos 5 partidos)
+ H2H (últimos 3 enfrentamientos)
+ Rendimiento local/visitante
+ Back-to-back games (descanso)
+ Lesiones de jugadores clave
+ Ritmo de juego (pace)
+ Eficiencia ofensiva/defensiva
```

**Fórmula propuesta:**

```
Predicción_Total = Base_Normal + Ajuste_Forma + Ajuste_H2H + Ajuste_Local + Ajuste_Descanso
```

#### **Football (Ligas principales)**

```python
Factores a considerar:
✅ Modelo Poisson actual (lambda_home, lambda_away)
+ xG (Expected Goals) últimos 5 partidos
+ H2H últimos 5 enfrentamientos
+ Forma local/visitante separada
+ Posesión promedio
+ Tiros a puerta
+ Corners
+ Tarjetas (disciplina)
```

**Fórmula propuesta:**

```
Lambda_Ajustado = Lambda_Base * Factor_Forma * Factor_H2H * Factor_Local * Factor_xG
```

#### **Tennis (ATP/WTA)**

```python
Factores a considerar:
✅ Sistema ELO actual
+ Superficie (clay, hard, grass)
+ H2H en misma superficie
+ Forma últimos 10 partidos
+ % primer servicio
+ % puntos ganados con servicio
+ Break points salvados
+ Fatiga (partidos recientes)
```

**Fórmula propuesta:**

```
Prob_Victoria = ELO_Base + Ajuste_Superficie + Ajuste_H2H + Ajuste_Forma + Ajuste_Servicio
```

---

## 📋 Implementación por Fases

### **FASE 1: Infraestructura Base** (2-3 horas)

- [ ] Crear módulo `app/stats/`
- [ ] Implementar `collector.py` con estructura base
- [ ] Crear tablas en BD para estadísticas históricas
- [ ] Sistema de caché (Redis o SQLite)

**Tablas nuevas:**

```sql
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

CREATE TABLE player_stats (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    team VARCHAR(200),
    player_name VARCHAR(200),
    position VARCHAR(50),
    ppg FLOAT,  -- points per game
    rpg FLOAT,  -- rebounds per game
    apg FLOAT,  -- assists per game
    injury_status VARCHAR(50),
    last_updated TIMESTAMP
);
```

### **FASE 2: Recolección de Datos** (3-4 horas)

- [ ] Implementar scraper de resultados históricos
- [ ] Integrar API-Football (si disponible)
- [ ] Parsear estadísticas de Flashscore
- [ ] Poblar base de datos con datos históricos

**Endpoints a scrapear:**

```python
# Basketball
"https://www.flashscore.com/basketball/usa/nba/results/"
"https://www.flashscore.com/basketball/usa/nba/standings/"

# Football
"https://www.flashscore.com/football/england/premier-league/results/"
"https://www.flashscore.com/football/spain/laliga/results/"

# Tennis
"https://www.flashscore.com/tennis/atp-singles/results/"
```

### **FASE 3: Modelos Estadísticos** (4-5 horas)

- [ ] Implementar cálculo de forma reciente
- [ ] Implementar análisis H2H
- [ ] Implementar tendencias local/visitante
- [ ] Integrar con modelos existentes

**Ejemplo - Forma reciente:**

```python
def calculate_form(team: str, sport: str, last_n: int = 5) -> dict:
    """
    Calcula la forma reciente de un equipo

    Returns:
        {
            'wins': 3,
            'losses': 2,
            'points_avg': 112.4,
            'points_against_avg': 108.2,
            'trend': 'up'  # up, down, stable
        }
    """
    pass
```

### **FASE 4: Sistema de Scoring** (2-3 horas)

- [ ] Crear sistema de puntuación para alertas
- [ ] Combinar múltiples factores
- [ ] Establecer umbrales de confianza
- [ ] Filtrar alertas de baja calidad

**Sistema de scoring propuesto:**

```python
Alert_Score = (
    EV_Score * 0.30 +           # Expected Value
    Anomaly_Score * 0.25 +      # Desviación estadística
    Form_Score * 0.20 +         # Forma reciente
    H2H_Score * 0.15 +          # Historial directo
    Trend_Score * 0.10          # Tendencias
)

# Solo enviar alertas con Score > 70/100
```

### **FASE 5: Dashboard de Estadísticas** (2-3 horas)

- [ ] Página de estadísticas por equipo
- [ ] Gráficos de tendencias
- [ ] Comparador de equipos
- [ ] Historial de predicciones

---

## 🔧 Tecnologías Adicionales

### **APIs Recomendadas:**

1. **API-Football** (https://www.api-football.com/)
   - 100 requests/día gratis
   - Estadísticas detalladas
   - xG, posesión, tiros

2. **The Odds API** (https://the-odds-api.com/)
   - 500 requests/mes gratis
   - Movimiento de líneas
   - Múltiples bookmakers

3. **SportsData.io**
   - Estadísticas de jugadores
   - Lesiones en tiempo real

### **Librerías Python:**

```python
# Análisis estadístico
scipy>=1.11.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0

# Machine Learning (opcional)
xgboost>=2.0.0
lightgbm>=4.0.0

# Visualización
matplotlib>=3.7.0
plotly>=5.17.0
```

---

## 📊 Ejemplo de Alerta Mejorada

**Antes:**

```
🎯 ANOMALÍA - BALONCESTO
🏆 NBA
🏀 Lakers vs Celtics
📊 Mercado: TOTAL
🎲 Over 228.5 @ 1.90
📈 Z-score: 2.30
```

**Después:**

```
🎯 ALERTA DE ALTA CONFIANZA - BALONCESTO
🏆 NBA
🏀 Lakers vs Celtics
🕐 15/01 19:30

📊 Mercado: TOTAL Over 228.5 @ 1.90
💰 EV: +8.5% | 🎯 Score: 87/100

📈 ANÁLISIS:
• Forma Lakers: 4-1 (avg 118 pts)
• Forma Celtics: 3-2 (avg 112 pts)
• H2H últimos 3: Over 3/3 (avg 235 pts)
• Ritmo combinado: 102.5 (Top 5 NBA)
• Tendencia: Ambos equipos Over en casa

✅ RECOMENDACIÓN: FUERTE
```

---

## ⏱️ Timeline Estimado

| Fase                    | Tiempo     | Prioridad |
| ----------------------- | ---------- | --------- |
| Fase 1: Infraestructura | 2-3h       | ALTA      |
| Fase 2: Recolección     | 3-4h       | ALTA      |
| Fase 3: Modelos         | 4-5h       | MEDIA     |
| Fase 4: Scoring         | 2-3h       | MEDIA     |
| Fase 5: Dashboard       | 2-3h       | BAJA      |
| **TOTAL**               | **13-18h** | -         |

---

## 🎯 Próximos Pasos Inmediatos

1. ✅ Eliminar provider_mock.py (HECHO)
2. 🔄 Arreglar scraper de Flashscore (EN PROGRESO)
3. ⏳ Implementar Fase 1: Infraestructura
4. ⏳ Implementar Fase 2: Recolección
5. ⏳ Implementar Fase 3: Modelos

---

## 💡 Notas Importantes

- **Caché:** Estadísticas se actualizan cada 24h
- **Performance:** Cálculos se hacen en background
- **Escalabilidad:** Sistema modular para agregar deportes
- **Precisión:** Validar predicciones vs resultados reales
- **Compliance:** Respetar rate limits de APIs

---

**Autor:** BLACKBOXAI  
**Fecha:** 2024  
**Versión:** 1.0
