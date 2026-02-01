# 🎯 PLAN DE MEJORAS DE CALIDAD - BETDESK

## 📋 TAREAS A REALIZAR

### 1. ✅ Desvigado (Devig) antes de EV

**Objetivo:** Eliminar el margen de la casa de apuestas antes de calcular EV
**Archivo:** `app/decision/ev.py`
**Implementación:**

- Calcular probabilidad implícita de todas las odds del mercado
- Normalizar para eliminar overround
- Usar probabilidades desvigadas para calcular EV

### 2. ✅ Mean/Std Dinámico por Equipo (Basketball)

**Objetivo:** Usar estadísticas reales de cada equipo en lugar de valores fijos
**Archivo:** `app/decision/basketball_stats.py` (nuevo)
**Implementación:**

- Crear tabla `team_stats` en BD
- Calcular mean/std por equipo basado en últimos N partidos
- Actualizar automáticamente con cada partido

### 3. ✅ Filtros de Calidad

**Objetivo:** Solo alertar picks de alta calidad
**Implementación:**

- **Liquidez:** Mínimo 3 bookmakers con la misma línea
- **Línea Estable:** Variación < 5% en última hora
- **Volumen:** Odds disponibles en bookmakers principales

### 4. ✅ Validación Multi-Book en Anomalías

**Objetivo:** Confirmar anomalías comparando múltiples casas
**Archivo:** `app/decision/anomaly.py`
**Implementación:**

- Calcular Z-score vs promedio de mercado
- Validar que al menos 3 bookmakers tienen odds similares
- Detectar "soft books" vs "sharp books"

### 5. ✅ Clasificación del Pick

**Objetivo:** Categorizar cada pick según su origen
**Tipos:**

- **MODEL:** EV+ basado en modelo estadístico
- **ANOMALY:** Odd anómala vs mercado
- **HYBRID:** Ambos criterios (máxima confianza)
- **ARBITRAGE:** Oportunidad de arbitraje detectada

### 6. ✅ Estadísticas Robustas

**Objetivo:** Agregar métricas avanzadas
**Implementación:**

- H2H (Head to Head) últimos 5 enfrentamientos
- Forma reciente (últimos 5 partidos)
- Estadísticas de jugadores clave
- Tendencias (racha de victorias/derrotas)

### 7. ✅ Detección de Errores de Cuota

**Objetivo:** Encontrar odds mal puestas por error humano
**Implementación:**

- Detectar odds > 3 desviaciones estándar
- Validar contra odds históricas
- Alertar inmediatamente (oportunidad de oro)

### 8. 🔍 Revisar Scrapers de Football/Tennis

**Objetivo:** Solucionar por qué no aparecen partidos
**Investigación:**

- Verificar selectores CSS
- Analizar HTML real de Flashscore
- Ajustar parsers

### 9. 🔧 Revisar Errores Backend/Frontend

**Objetivo:** Solucionar Internal Server Error y CSS
**Tareas:**

- Verificar conexión a BD
- Validar esquema de tablas
- Arreglar carga de CSS en Next.js

---

## 📊 ARQUITECTURA DE MEJORAS

```
┌─────────────────────────────────────────────────────────────────┐
│                    FLUJO MEJORADO                                │
└─────────────────────────────────────────────────────────────────┘

1. SCRAPING
   └─ Múltiples bookmakers (liquidez)

2. ALMACENAMIENTO
   ├─ odds (con timestamp)
   ├─ team_stats (dinámico)
   └─ market_history (estabilidad)

3. DESVIGADO ⭐ NUEVO
   └─ Eliminar margen de casa

4. MODELOS MEJORADOS ⭐
   ├─ Basketball: Mean/Std por equipo
   ├─ Football: Poisson + H2H + Forma
   └─ Tennis: ELO + Superficie + H2H

5. CÁLCULO DE EV (con odds desvigadas)
   └─ EV = (prob_devig × (odds-1)) - ((1-prob_devig) × 1)

6. FILTROS DE CALIDAD ⭐ NUEVO
   ├─ Liquidez (≥3 bookmakers)
   ├─ Estabilidad (variación <5%)
   └─ Volumen (bookmakers principales)

7. VALIDACIÓN MULTI-BOOK ⭐ NUEVO
   └─ Confirmar anomalías vs mercado

8. CLASIFICACIÓN ⭐ NUEVO
   ├─ MODEL (EV+ puro)
   ├─ ANOMALY (odd anómala)
   ├─ HYBRID (ambos)
   └─ ARBITRAGE (sin riesgo)

9. DETECCIÓN DE ERRORES ⭐ NUEVO
   └─ Odds > 3σ → Alerta inmediata

10. ALERTAS MEJORADAS
    └─ Con clasificación + confianza + stats
```

---

## 🔧 IMPLEMENTACIÓN DETALLADA

### Mejora 1: Desvigado (Devig)

**Archivo:** `app/decision/devig.py` (nuevo)

```python
def devig_odds(odds_list: List[float]) -> List[float]:
    """
    Elimina el margen (vig) de las odds

    Args:
        odds_list: Lista de odds del mismo mercado [1.90, 2.10, 3.50]

    Returns:
        Lista de odds desvigadas [1.95, 2.15, 3.60]

    Método: Multiplicative (más preciso)
    """
    # Convertir odds a probabilidades implícitas
    implied_probs = [1/odd for odd in odds_list]

    # Calcular overround (margen de la casa)
    overround = sum(implied_probs)

    # Normalizar probabilidades (eliminar margen)
    true_probs = [p / overround for p in implied_probs]

    # Convertir de vuelta a odds
    devigged_odds = [1/p for p in true_probs]

    return devigged_odds

# EJEMPLO:
# Odds originales: [1.90, 2.10] (1X2 sin empate)
# Prob implícitas: [0.526, 0.476] = 1.002 (0.2% de margen)
# Prob desvigadas: [0.525, 0.475] = 1.000
# Odds desvigadas: [1.905, 2.105]
```

**Integración en EV:**

```python
def calculate_ev_with_devig(odd: dict, model_prob: float, market_odds: List[dict]) -> float:
    """
    Calcula EV usando odds desvigadas
    """
    # 1. Obtener todas las odds del mercado
    odds_values = [o['odds'] for o in market_odds]

    # 2. Desvigar
    devigged = devig_odds(odds_values)

    # 3. Encontrar odd desvigada correspondiente
    idx = market_odds.index(odd)
    devigged_odd = devigged[idx]

    # 4. Calcular EV con odd desvigada
    ev = (model_prob * (devigged_odd - 1)) - ((1 - model_prob) * 1)

    return ev
```

---

### Mejora 2: Mean/Std Dinámico por Equipo

**Archivo:** `app/decision/basketball_stats.py` (nuevo)

```python
from typing import Dict, Tuple
import numpy as np

class BasketballStatsEngine:
    """
    Motor de estadísticas dinámicas para basketball
    """

    def __init__(self, db_session):
        self.db = db_session

    def get_team_stats(self, team: str, league: str, last_n_games: int = 10) -> Dict:
        """
        Obtiene estadísticas dinámicas de un equipo

        Returns:
            {
                "points_mean": 112.5,
                "points_std": 8.3,
                "opponent_points_mean": 108.2,
                "opponent_points_std": 7.9,
                "total_mean": 220.7,
                "total_std": 11.2,
                "games_analyzed": 10
            }
        """
        # Consultar últimos N partidos del equipo
        sql = """
            SELECT home_score, away_score, is_home
            FROM game_results
            WHERE (home_team = :team OR away_team = :team)
              AND league = :league
              AND game_date >= NOW() - INTERVAL '30 days'
            ORDER BY game_date DESC
            LIMIT :limit
        """

        results = self.db.execute(sql, {
            "team": team,
            "league": league,
            "limit": last_n_games
        }).fetchall()

        if len(results) < 5:
            # No hay suficientes datos, usar valores por defecto
            return self._get_default_stats(league)

        # Calcular estadísticas
        team_points = []
        opponent_points = []
        totals = []

        for row in results:
            if row['is_home']:
                team_points.append(row['home_score'])
                opponent_points.append(row['away_score'])
            else:
                team_points.append(row['away_score'])
                opponent_points.append(row['home_score'])

            totals.append(row['home_score'] + row['away_score'])

        return {
            "points_mean": np.mean(team_points),
            "points_std": np.std(team_points),
            "opponent_points_mean": np.mean(opponent_points),
            "opponent_points_std": np.std(opponent_points),
            "total_mean": np.mean(totals),
            "total_std": np.std(totals),
            "games_analyzed": len(results)
        }

    def calculate_matchup_total(self, home: str, away: str, league: str) -> Tuple[float, float]:
        """
        Calcula mean y std esperados para el total del partido

        Returns:
            (mean, std) - Ej: (225.5, 12.3)
        """
        home_stats = self.get_team_stats(home, league)
        away_stats = self.get_team_stats(away, league)

        # Promedio de puntos esperados
        home_expected = (home_stats['points_mean'] + away_stats['opponent_points_mean']) / 2
        away_expected = (away_stats['points_mean'] + home_stats['opponent_points_mean']) / 2

        total_mean = home_expected + away_expected

        # Desviación estándar combinada
        total_std = np.sqrt(
            home_stats['points_std']**2 +
            away_stats['points_std']**2
        )

        return total_mean, total_std
```

**Integración en Scheduler:**

```python
def job_ev_baseline_improved():
    """
    Job mejorado con stats dinámicas
    """
    rows = fetch_latest_odds_snapshot(minutes=60, sport="basketball")

    stats_engine = BasketballStatsEngine(db_session)

    for row in rows:
        # Obtener stats dinámicas
        mean, std = stats_engine.calculate_matchup_total(
            row['home'],
            row['away'],
            row['league']
        )

        # Calcular probabilidades con stats reales
        probs = calculate_normal_probabilities(mean, std, row['line'])

        # ... resto del código
```

---

### Mejora 3: Filtros de Calidad

**Archivo:** `app/decision/quality_filters.py` (nuevo)

```python
from typing import List, Dict

class QualityFilter:
    """
    Filtros de calidad para picks
    """

    @staticmethod
    def check_liquidity(odds_snapshot: List[Dict], min_bookmakers: int = 3) -> bool:
        """
        Verifica liquidez: mínimo N bookmakers con la misma línea

        Args:
            odds_snapshot: Lista de odds del mismo mercado
            min_bookmakers: Mínimo de bookmakers requeridos

        Returns:
            True si cumple criterio de liquidez
        """
        # Agrupar por línea
        lines = {}
        for odd in odds_snapshot:
            key = f"{odd['market']}_{odd['line']}_{odd['selection']}"
            if key not in lines:
                lines[key] = []
            lines[key].append(odd['bookmaker'])

        # Verificar que al menos una línea tenga suficientes bookmakers
        for bookmakers in lines.values():
            if len(set(bookmakers)) >= min_bookmakers:
                return True

        return False

    @staticmethod
    def check_stability(odd: Dict, historical_odds: List[Dict], max_variation: float = 0.05) -> bool:
        """
        Verifica estabilidad: variación < 5% en última hora

        Args:
            odd: Odd actual
            historical_odds: Odds históricas de la última hora
            max_variation: Variación máxima permitida (0.05 = 5%)

        Returns:
            True si la línea es estable
        """
        if not historical_odds:
            return False

        current_odd = odd['odds']
        historical_values = [h['odds'] for h in historical_odds]

        # Calcular variación
        min_odd = min(historical_values)
        max_odd = max(historical_values)
        variation = (max_odd - min_odd) / min_odd

        return variation <= max_variation

    @staticmethod
    def check_sharp_books(odd: Dict, odds_snapshot: List[Dict]) -> bool:
        """
        Verifica que bookmakers "sharp" (Pinnacle, Betfair) tengan odds similares

        Args:
            odd: Odd a verificar
            odds_snapshot: Todas las odds del mercado

        Returns:
            True si sharp books confirman la odd
        """
        sharp_books = ['Pinnacle', 'Betfair', 'Bet365']

        # Buscar odds de sharp books
        sharp_odds = [
            o['odds'] for o in odds_snapshot
            if o['bookmaker'] in sharp_books
            and o['market'] == odd['market']
            and o['line'] == odd['line']
            and o['selection'] == odd['selection']
        ]

        if not sharp_odds:
            return False

        # Verificar que la odd esté dentro del rango de sharp books
        avg_sharp = np.mean(sharp_odds)
        tolerance = 0.10  # 10% de tolerancia

        return abs(odd['odds'] - avg_sharp) / avg_sharp <= tolerance

    @staticmethod
    def apply_all_filters(odd: Dict, odds_snapshot: List[Dict], historical_odds: List[Dict]) -> Dict:
        """
        Aplica todos los filtros y retorna resultado

        Returns:
            {
                "passed": True/False,
                "liquidity": True/False,
                "stability": True/False,
                "sharp_books": True/False,
                "quality_score": 0.0-1.0
            }
        """
        liquidity = QualityFilter.check_liquidity(odds_snapshot, min_bookmakers=3)
        stability = QualityFilter.check_stability(odd, historical_odds)
        sharp_books = QualityFilter.check_sharp_books(odd, odds_snapshot)

        # Calcular score de calidad
        quality_score = (
            (0.4 if liquidity else 0) +
            (0.3 if stability else 0) +
            (0.3 if sharp_books else 0)
        )

        return {
            "passed": quality_score >= 0.7,  # Requiere 70% de calidad
            "liquidity": liquidity,
            "stability": stability,
            "sharp_books": sharp_books,
            "quality_score": quality_score
        }
```

---

### Mejora 4: Validación Multi-Book en Anomalías

**Archivo:** `app/decision/anomaly.py` (mejorado)

```python
def detect_anomalies_multibook(odds_snapshot: List[dict]) -> List[dict]:
    """
    Detecta anomalías validando contra múltiples bookmakers

    Mejoras:
    - Calcula Z-score vs promedio de mercado
    - Valida que al menos 3 bookmakers tengan odds similares
    - Clasifica bookmakers en sharp vs soft
    """
    import numpy as np

    # Agrupar por mercado
    grouped = {}
    for odd in odds_snapshot:
        key = f"{odd['market']}_{odd['line']}_{odd['selection']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(odd)

    anomalies = []

    for key, odds_list in grouped.items():
        if len(odds_list) < 4:  # Necesitamos al menos 4 bookmakers
            continue

        # Clasificar bookmakers
        sharp_books = ['Pinnacle', 'Betfair', 'Bet365', 'Bookmaker.eu']
        soft_books = ['Bwin', '1xBet', 'Betsson', 'Codere']

        sharp_odds = [o for o in odds_list if o['bookmaker'] in sharp_books]
        soft_odds = [o for o in odds_list if o['bookmaker'] in soft_books]

        if len(sharp_odds) < 2:
            continue

        # Calcular promedio de sharp books (referencia del mercado)
        sharp_mean = np.mean([o['odds'] for o in sharp_odds])
        sharp_std = np.std([o['odds'] for o in sharp_odds])

        if sharp_std == 0:
            continue

        # Buscar anomalías en soft books
        for odd in soft_odds:
            z_score = (odd['odds'] - sharp_mean) / sharp_std

            if abs(z_score) > 2.5:  # Anomalía significativa
                # Validar que es una oportunidad real
                if z_score > 0:  # Odd más alta que el mercado (bueno para nosotros)
                    anomalies.append({
                        **odd,
                        "z_score": z_score,
                        "market_mean": sharp_mean,
                        "market_std": sharp_std,
                        "type": "SOFT_BOOK_OVERLAY",  # Soft book con odd generosa
                        "confidence": min(abs(z_score) / 5.0, 1.0)  # 0-1
                    })

    return anomalies
```

---

### Mejora 5: Clasificación del Pick

**Archivo:** `app/decision/pick_classifier.py` (nuevo)

```python
from enum import Enum
from typing import Dict

class PickType(Enum):
    MODEL = "MODEL"           # EV+ basado en modelo
    ANOMALY = "ANOMALY"       # Odd anómala vs mercado
    HYBRID = "HYBRID"         # Ambos criterios
    ARBITRAGE = "ARBITRAGE"   # Oportunidad de arbitraje
    ERROR = "ERROR"           # Posible error de cuota

class PickClassifier:
    """
    Clasifica picks según su origen y confianza
    """

    @staticmethod
    def classify_pick(
        ev: float = None,
        z_score: float = None,
        quality_score: float = 0.0,
        is_arbitrage: bool = False,
        is_error: bool = False
    ) -> Dict:
        """
        Clasifica un pick

        Returns:
            {
                "type": PickType,
                "confidence": 0.0-1.0,
                "priority": 1-5 (5 = máxima)
            }
        """
        # Error de cuota (máxima prioridad)
        if is_error:
            return {
                "type": PickType.ERROR,
                "confidence": 0.95,
                "priority": 5,
                "description": "Posible error de cuota - Actuar inmediatamente"
            }

        # Arbitraje (sin riesgo)
        if is_arbitrage:
            return {
                "type": PickType.ARBITRAGE,
                "confidence": 1.0,
                "priority": 5,
                "description": "Arbitraje sin riesgo"
            }

        # Hybrid (modelo + anomalía)
        if ev and ev > 0.05 and z_score and abs(z_score) > 2.0:
            confidence = min((ev * 10 + abs(z_score) / 5) / 2, 1.0)
            return {
                "type": PickType.HYBRID,
                "confidence": confidence * quality_score,
                "priority": 4,
                "description": f"EV+{ev*100:.1f}% + Anomalía Z={z_score:.2f}"
            }

        # Solo modelo
        if ev and ev > 0.03:
            confidence = min(ev * 10, 1.0)
            return {
                "type": PickType.MODEL,
                "confidence": confidence * quality_score,
                "priority": 3,
                "description": f"EV+{ev*100:.1f}% según modelo"
            }

        # Solo anomalía
        if z_score and abs(z_score) > 2.0:
            confidence = min(abs(z_score) / 5, 1.0)
            return {
                "type": PickType.ANOMALY,
                "confidence": confidence * quality_score,
                "priority": 2,
                "description": f"Anomalía Z={z_score:.2f}"
            }

        # No califica
        return {
            "type": None,
            "confidence": 0.0,
            "priority": 0,
            "description": "No cumple criterios"
        }
```

---

### Mejora 6: Estadísticas Robustas

**Archivo:** `app/decision/robust_stats.py` (nuevo)

```python
class RobustStatsEngine:
    """
    Motor de estadísticas robustas multi-deporte
    """

    def get_h2h_stats(self, home: str, away: str, sport: str, last_n: int = 5) -> Dict:
        """
        Head to Head - Últimos enfrentamientos directos

        Returns:
            {
                "games_played": 5,
                "home_wins": 3,
                "away_wins": 2,
                "avg_total": 225.5,
                "home_avg_score": 115.2,
                "away_avg_score": 110.3,
                "trend": "HOME_ADVANTAGE"
            }
        """
        sql = """
            SELECT *
            FROM game_results
            WHERE ((home_team = :home AND away_team = :away)
                OR (home_team = :away AND away_team = :home))
              AND sport = :sport
            ORDER BY game_date DESC
            LIMIT :limit
        """

        results = self.db.execute(sql, {
            "home": home,
            "away": away,
            "sport": sport,
            "limit": last_n
        }).fetchall()

        # Analizar resultados...
        # (implementación completa)

    def get_form_stats(self, team: str, sport: str, last_n: int = 5) -> Dict:
        """
        Forma reciente - Últimos N partidos

        Returns:
            {
                "games": 5,
                "wins": 4,
                "losses": 1,
                "win_rate": 0.80,
                "avg_score": 112.5,
                "trend": "WINNING_STREAK",
                "streak_length": 3
            }
        """
        # Implementación...

    def get_player_stats(self, team: str, sport: str) -> Dict:
        """
        Estadísticas de jugadores clave

        Returns:
            {
                "key_players": [
                    {
                        "name": "LeBron James",
                        "ppg": 27.5,
                        "status": "ACTIVE"
                    }
                ],
                "injuries": [...],
                "impact_score": 0.85
            }
        """
        # Implementación...

    def get_trends(self, team: str, sport: str) -> Dict:
        """
        Tendencias y patrones

        Returns:
            {
                "home_record": "8-2",
                "away_record": "5-5",
                "vs_top_teams": "3-4",
                "recent_totals": "OVER_TREND",
                "back_to_back": False
            }
        """
        # Implementación...
```

---

### Mejora 7: Detección de Errores de Cuota

**Archivo:** `app/decision/error_detection.py` (nuevo)

```python
class OddsErrorDetector:
    """
    Detecta posibles errores en las cuotas
    """

    @staticmethod
    def detect_pricing_error(odd: Dict, odds_snapshot: List[Dict], historical_data: List[Dict]) -> Dict:
        """
        Detecta errores de pricing

        Criterios:
        1. Odd > 3 desviaciones estándar del mercado
        2. Odd muy diferente a histórico del mismo evento
        3. Odd inconsistente con mercados relacionados

        Returns:
            {
                "is_error": True/False,
                "confidence": 0.0-1.0,
                "error_type": "HUMAN_ERROR" | "SYSTEM_ERROR" | "LATE_UPDATE",
                "expected_odd": 1.95,
                "actual_odd": 3.50,
                "deviation": 4.2  # sigmas
            }
        """
        # 1. Comparar con mercado actual
        market_odds = [
            o['odds'] for o in odds_snapshot
            if o['market'] == odd['market']
            and o['line'] == odd['line']
            and o['selection'] == odd['selection']
            and o['bookmaker'] != odd['bookmaker']
        ]

        if len(market_odds) < 3:
            return {"is_error": False}

        market_mean = np.mean(market_odds)
        market_std = np.std(market_odds)

        if market_std == 0:
            return {"is_error": False}

        deviation = abs(odd['odds'] - market_mean) / market_std

        # 2. Comparar con histórico
        historical_mean = None
        if historical_data:
            historical_odds = [h['odds'] for h in historical_data]
            historical_mean = np.mean(historical_odds)

        # 3. Detectar error
        is_error = False
        error_type = None
        confidence = 0.0

        if deviation > 3.0:  # Más de 3 sigmas
            is_error = True
            confidence = min(deviation / 5.0, 1.0)

            if odd['odds'] > market_mean * 1.5:
                error_type = "HUMAN_ERROR"  # Odd demasiado alta
            elif odd['odds'] < market_mean * 0.7:
                error_type = "SYSTEM_ERROR"  # Odd demasiado baja
            else:
                error_type = "LATE_UPDATE"  # Actualización tardía

        return {
            "is_error": is_error,
            "confidence": confidence,
            "error_type": error_type,
            "expected_odd": market_mean,
            "actual_odd": odd['odds'],
            "deviation": deviation,
            "action": "BET_IMMEDIATELY" if is_error and odd['odds'] > market_mean else "SKIP"
        }
```

---

## 📝 ORDEN DE IMPLEMENTACIÓN

### Fase 1: Correcciones Urgentes (1-2 horas)

1. ✅ Revisar y arreglar scrapers de football/tennis
2. ✅ Solucionar Internal Server Error en backend
3. ✅ Arreglar CSS en frontend

### Fase 2: Mejoras de Calidad (3-4 horas)

4. ✅ Implementar desvigado
5. ✅ Agregar filtros de calidad
6. ✅ Implementar clasificación de picks

### Fase 3: Estadísticas Avanzadas (4-5 horas)

7. ✅ Mean/Std dinámico por equipo
8. ✅ Estadísticas robustas (H2H, forma, etc.)
9. ✅ Validación multi-book

### Fase 4: Detección de Oportunidades (2-3 horas)

10. ✅ Detección de errores de cuota
11. ✅ Detección de arbitraje

---

## 🎯 RESULTADO ESPERADO

### Antes:

```
🎯 ANOMALÍA - BALONCESTO
🏆 NBA
🏀 Lakers vs Celtics
📊 Mercado: TOTAL
🎲 Over 228.5 @ 1.90
🏪 Bwin
📈 Z-score: 2.30
```

### Después:

```
⭐ HYBRID PICK - ALTA CONFIANZA
🏀 NBA: Lakers vs Celtics
🕐 15/01 19:30

📊 ANÁLISIS:
• Tipo: HYBRID (Modelo + Anomalía)
• Confianza: 87%
• Prioridad: ⭐⭐⭐⭐

💰 APUESTA:
• Mercado: TOTAL Over 228.5
• Cuota: 1.90 (Bwin)
• EV: +8.5% (desvigado)
• Z-score: 2.30 vs mercado

✅ CALIDAD:
• Liquidez: 5 bookmakers
• Estabilidad: ✓ (variación 2%)
• Sharp books: ✓ Confirmado

📈 ESTADÍSTICAS:
• Total esperado: 225.5 ±
```
