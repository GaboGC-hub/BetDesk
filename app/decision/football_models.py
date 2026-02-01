# app/decision/football_models.py
"""
Modelos de decisión para fútbol
Incluye cálculos de probabilidades y EV para mercados de fútbol
"""
import math
from typing import Optional
from .utils import (
    poisson_pmf,
    expected_value,
    implied_probability,
    remove_vig_proportional
)
from ..config.sport_configs import get_sport_config


# ==================== MODELO POISSON PARA GOLES ====================

def poisson_match_probabilities(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10
) -> dict[str, float]:
    """
    Calcula probabilidades de resultado usando distribución de Poisson
    
    Args:
        lambda_home: Goles esperados del equipo local
        lambda_away: Goles esperados del equipo visitante
        max_goals: Máximo de goles a considerar
    
    Returns:
        dict: {"home": P(home wins), "draw": P(draw), "away": P(away wins)}
    """
    prob_home = 0.0
    prob_draw = 0.0
    prob_away = 0.0
    
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            # P(home_goals, away_goals) = P(home_goals) * P(away_goals)
            prob = poisson_pmf(home_goals, lambda_home) * poisson_pmf(away_goals, lambda_away)
            
            if home_goals > away_goals:
                prob_home += prob
            elif home_goals == away_goals:
                prob_draw += prob
            else:
                prob_away += prob
    
    return {
        "HOME": prob_home,
        "DRAW": prob_draw,
        "AWAY": prob_away
    }


def prob_over_goals_poisson(
    lambda_home: float,
    lambda_away: float,
    line: float,
    max_goals: int = 15
) -> float:
    """
    Calcula P(Total goles > line) usando Poisson
    
    Args:
        lambda_home: Goles esperados del local
        lambda_away: Goles esperados del visitante
        line: Línea de goles (ej. 2.5)
        max_goals: Máximo de goles a considerar
    
    Returns:
        float: Probabilidad de over
    """
    lambda_total = lambda_home + lambda_away
    
    # P(Total > line) = 1 - P(Total <= floor(line))
    k_max = int(math.floor(line))
    prob_under = 0.0
    
    for k in range(k_max + 1):
        prob_under += poisson_pmf(k, lambda_total)
    
    return 1.0 - prob_under


def prob_btts(
    lambda_home: float,
    lambda_away: float,
    max_goals: int = 10
) -> float:
    """
    Calcula P(Ambos equipos anotan) usando Poisson
    
    Args:
        lambda_home: Goles esperados del local
        lambda_away: Goles esperados del visitante
        max_goals: Máximo de goles a considerar
    
    Returns:
        float: Probabilidad de BTTS
    """
    # P(BTTS) = 1 - P(home=0 OR away=0)
    # P(home=0 OR away=0) = P(home=0) + P(away=0) - P(home=0 AND away=0)
    
    prob_home_zero = poisson_pmf(0, lambda_home)
    prob_away_zero = poisson_pmf(0, lambda_away)
    prob_both_zero = prob_home_zero * prob_away_zero
    
    prob_at_least_one_zero = prob_home_zero + prob_away_zero - prob_both_zero
    
    return 1.0 - prob_at_least_one_zero


# ==================== CÁLCULO DE EV PARA MERCADOS DE FÚTBOL ====================

def calculate_ev_1x2(
    row: dict,
    league: str,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado 1X2
    
    Args:
        row: Diccionario con datos de la cuota (market, selection, odds, etc.)
        league: Nombre de la liga
        use_baseline: Si True, usa parámetros baseline de configuración
    
    Returns:
        float: EV o None si no se puede calcular
    """
    try:
        config = get_sport_config("football", league, "goals")
        lambda_home = config["lambda_home"]
        lambda_away = config["lambda_away"]
    except (ValueError, KeyError):
        return None
    
    # Calcular probabilidades usando Poisson
    probs = poisson_match_probabilities(lambda_home, lambda_away)
    
    selection = row["selection"].upper()
    if selection not in probs:
        return None
    
    prob = probs[selection]
    odds = float(row["odds"])
    
    return expected_value(prob, odds)


def calculate_ev_goals(
    row: dict,
    league: str,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado Over/Under goles
    
    Args:
        row: Diccionario con datos de la cuota
        league: Nombre de la liga
        use_baseline: Si True, usa parámetros baseline
    
    Returns:
        float: EV o None si no se puede calcular
    """
    try:
        config = get_sport_config("football", league, "goals")
        lambda_home = config["lambda_home"]
        lambda_away = config["lambda_away"]
    except (ValueError, KeyError):
        return None
    
    line = float(row["line"]) if row["line"] is not None else None
    if line is None:
        return None
    
    selection = row["selection"].upper()
    odds = float(row["odds"])
    
    if selection == "OVER":
        prob = prob_over_goals_poisson(lambda_home, lambda_away, line)
    elif selection == "UNDER":
        prob = 1.0 - prob_over_goals_poisson(lambda_home, lambda_away, line)
    else:
        return None
    
    return expected_value(prob, odds)


def calculate_ev_btts(
    row: dict,
    league: str,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado BTTS (Ambos anotan)
    
    Args:
        row: Diccionario con datos de la cuota
        league: Nombre de la liga
        use_baseline: Si True, usa parámetros baseline
    
    Returns:
        float: EV o None si no se puede calcular
    """
    try:
        config = get_sport_config("football", league, "btts")
        
        # Opción 1: Usar probabilidad baseline directa
        if "prob_baseline" in config:
            prob_yes = config["prob_baseline"]
        else:
            # Opción 2: Calcular con Poisson
            goals_config = get_sport_config("football", league, "goals")
            lambda_home = goals_config["lambda_home"]
            lambda_away = goals_config["lambda_away"]
            prob_yes = prob_btts(lambda_home, lambda_away)
    except (ValueError, KeyError):
        return None
    
    selection = row["selection"].upper()
    odds = float(row["odds"])
    
    if selection == "YES":
        prob = prob_yes
    elif selection == "NO":
        prob = 1.0 - prob_yes
    else:
        return None
    
    return expected_value(prob, odds)


# ==================== AJUSTES AVANZADOS ====================

def adjust_lambda_for_home_advantage(
    lambda_home: float,
    lambda_away: float,
    home_advantage_factor: float = 1.15
) -> tuple[float, float]:
    """
    Ajusta lambdas considerando ventaja de local
    
    Args:
        lambda_home: Goles esperados del local (neutral)
        lambda_away: Goles esperados del visitante (neutral)
        home_advantage_factor: Factor de ventaja local (1.15 = 15% más goles)
    
    Returns:
        tuple: (lambda_home_adjusted, lambda_away_adjusted)
    """
    lambda_home_adj = lambda_home * home_advantage_factor
    lambda_away_adj = lambda_away / home_advantage_factor
    
    return (lambda_home_adj, lambda_away_adj)


def adjust_lambda_for_form(
    lambda_base: float,
    recent_goals_scored: list[int],
    recent_goals_conceded: list[int],
    weight: float = 0.3
) -> float:
    """
    Ajusta lambda basado en forma reciente del equipo
    
    Args:
        lambda_base: Lambda base del equipo
        recent_goals_scored: Goles anotados en últimos N partidos
        recent_goals_conceded: Goles recibidos en últimos N partidos
        weight: Peso de la forma reciente (0.3 = 30%)
    
    Returns:
        float: Lambda ajustado
    """
    if not recent_goals_scored:
        return lambda_base
    
    avg_scored = sum(recent_goals_scored) / len(recent_goals_scored)
    
    # Combinar lambda base con forma reciente
    lambda_adjusted = (1 - weight) * lambda_base + weight * avg_scored
    
    return lambda_adjusted


def dixon_coles_adjustment(
    lambda_home: float,
    lambda_away: float,
    rho: float = -0.15
) -> dict[str, float]:
    """
    Aplica ajuste de Dixon-Coles para resultados de pocos goles
    Mejora la precisión para 0-0, 1-0, 0-1, 1-1
    
    Args:
        lambda_home: Goles esperados del local
        lambda_away: Goles esperados del visitante
        rho: Parámetro de correlación (típicamente negativo)
    
    Returns:
        dict: Probabilidades ajustadas para resultados clave
    """
    # Calcular probabilidades base con Poisson
    probs = {}
    
    for home_goals in range(2):
        for away_goals in range(2):
            prob_base = poisson_pmf(home_goals, lambda_home) * poisson_pmf(away_goals, lambda_away)
            
            # Factor de ajuste Dixon-Coles
            if home_goals == 0 and away_goals == 0:
                tau = 1 - lambda_home * lambda_away * rho
            elif home_goals == 0 and away_goals == 1:
                tau = 1 + lambda_home * rho
            elif home_goals == 1 and away_goals == 0:
                tau = 1 + lambda_away * rho
            elif home_goals == 1 and away_goals == 1:
                tau = 1 - rho
            else:
                tau = 1.0
            
            probs[f"{home_goals}-{away_goals}"] = prob_base * tau
    
    return probs


# ==================== FUNCIONES DE UTILIDAD ====================

def get_fair_odds_1x2(
    lambda_home: float,
    lambda_away: float,
    remove_vig: bool = True
) -> dict[str, float]:
    """
    Calcula cuotas justas (fair odds) para mercado 1X2
    
    Args:
        lambda_home: Goles esperados del local
        lambda_away: Goles esperados del visitante
        remove_vig: Si True, asume que las probabilidades suman 1
    
    Returns:
        dict: {"HOME": odds, "DRAW": odds, "AWAY": odds}
    """
    probs = poisson_match_probabilities(lambda_home, lambda_away)
    
    fair_odds = {}
    for outcome, prob in probs.items():
        if prob > 0:
            fair_odds[outcome] = 1.0 / prob
        else:
            fair_odds[outcome] = 999.0  # Muy improbable
    
    return fair_odds


def compare_odds_to_fair(
    market_odds: dict[str, float],
    lambda_home: float,
    lambda_away: float
) -> dict[str, dict]:
    """
    Compara cuotas del mercado con cuotas justas
    
    Args:
        market_odds: {"HOME": 2.10, "DRAW": 3.40, "AWAY": 3.20}
        lambda_home: Goles esperados del local
        lambda_away: Goles esperados del visitante
    
    Returns:
        dict: Análisis por cada resultado con EV y diferencia
    """
    fair_odds = get_fair_odds_1x2(lambda_home, lambda_away)
    probs = poisson_match_probabilities(lambda_home, lambda_away)
    
    analysis = {}
    for outcome in ["HOME", "DRAW", "AWAY"]:
        if outcome in market_odds and outcome in fair_odds:
            market_odd = market_odds[outcome]
            fair_odd = fair_odds[outcome]
            prob = probs[outcome]
            ev = expected_value(prob, market_odd)
            
            analysis[outcome] = {
                "market_odds": market_odd,
                "fair_odds": fair_odd,
                "probability": prob,
                "ev": ev,
                "value_pct": ((market_odd / fair_odd) - 1.0) * 100,  # % de valor
            }
    
    return analysis
