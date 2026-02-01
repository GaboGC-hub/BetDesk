# app/decision/tennis_models.py
"""
Modelos de decisión para tenis
Incluye cálculos de probabilidades y EV para mercados de tenis
"""
import math
from typing import Optional
from .utils import (
    prob_over_normal,
    prob_under_normal,
    expected_value,
    normal_cdf
)
from ..config.sport_configs import get_sport_config


# ==================== MODELO ELO PARA TENIS ====================

def elo_win_probability(
    elo_player1: float,
    elo_player2: float,
    k_factor: float = 400.0
) -> float:
    """
    Calcula probabilidad de victoria usando sistema ELO
    
    Args:
        elo_player1: Rating ELO del jugador 1
        elo_player2: Rating ELO del jugador 2
        k_factor: Factor K (400 es estándar para tenis)
    
    Returns:
        float: P(Player1 gana)
    """
    diff = elo_player2 - elo_player1
    return 1.0 / (1.0 + 10.0 ** (diff / k_factor))


def surface_adjustment(
    base_prob: float,
    surface: str,
    player1_surface_factor: float = 1.0,
    player2_surface_factor: float = 1.0
) -> float:
    """
    Ajusta probabilidad según la superficie
    
    Args:
        base_prob: Probabilidad base
        surface: "clay", "grass", "hard"
        player1_surface_factor: Factor de rendimiento en superficie (1.0 = neutral)
        player2_surface_factor: Factor de rendimiento en superficie
    
    Returns:
        float: Probabilidad ajustada
    """
    # Ajuste simple basado en factores relativos
    if player2_surface_factor == 0:
        return base_prob
    
    relative_factor = player1_surface_factor / player2_surface_factor
    
    # Ajustar probabilidad (limitado para evitar extremos)
    adjusted_prob = base_prob * relative_factor
    
    return max(0.01, min(0.99, adjusted_prob))


# ==================== MODELO PARA TOTAL DE GAMES ====================

def prob_over_games(
    mu_games: float,
    sigma_games: float,
    line: float
) -> float:
    """
    Calcula P(Total games > line) usando distribución normal
    
    Args:
        mu_games: Media de games totales esperados
        sigma_games: Desviación estándar
        line: Línea de games (ej. 22.5)
    
    Returns:
        float: Probabilidad de over
    """
    return prob_over_normal(mu_games, sigma_games, line)


def prob_under_games(
    mu_games: float,
    sigma_games: float,
    line: float
) -> float:
    """
    Calcula P(Total games < line) usando distribución normal
    
    Args:
        mu_games: Media de games totales esperados
        sigma_games: Desviación estándar
        line: Línea de games
    
    Returns:
        float: Probabilidad de under
    """
    return prob_under_normal(mu_games, sigma_games, line)


def estimate_games_from_match_prob(
    prob_player1: float,
    format_sets: int = 3,
    avg_games_per_set: float = 10.0
) -> tuple[float, float]:
    """
    Estima media y desviación de games totales basado en probabilidad de victoria
    
    Args:
        prob_player1: Probabilidad de que gane el jugador 1
        format_sets: Formato del partido (3 o 5 sets)
        avg_games_per_set: Promedio de games por set
    
    Returns:
        tuple: (mu_games, sigma_games)
    """
    # Estimación simple: partidos más parejos tienden a tener más games
    competitiveness = 1.0 - abs(prob_player1 - 0.5) * 2  # 0 = muy desigual, 1 = muy parejo
    
    # Sets esperados
    if format_sets == 3:
        # Al mejor de 3: mínimo 2 sets, máximo 3
        expected_sets = 2.0 + competitiveness
    else:
        # Al mejor de 5: mínimo 3 sets, máximo 5
        expected_sets = 3.0 + competitiveness * 2
    
    mu_games = expected_sets * avg_games_per_set
    
    # Más competitividad = más varianza
    sigma_games = 2.0 + competitiveness * 3.0
    
    return (mu_games, sigma_games)


# ==================== MODELO PARA HÁNDICAP DE SETS ====================

def prob_set_handicap(
    prob_player1: float,
    handicap: float,
    format_sets: int = 3
) -> float:
    """
    Calcula probabilidad de cubrir hándicap de sets
    
    Args:
        prob_player1: Probabilidad de que gane el jugador 1
        handicap: Hándicap de sets (ej. -1.5 significa debe ganar por 2+ sets)
        format_sets: Formato del partido (3 o 5 sets)
    
    Returns:
        float: P(Player1 cubre el handicap)
    """
    if format_sets == 3:
        # Al mejor de 3: posibles resultados 2-0, 2-1, 1-2, 0-2
        # Handicap -1.5: necesita ganar 2-0
        # Handicap +1.5: cubre con 2-1, 1-2, 0-2
        
        if handicap == -1.5:
            # Necesita ganar 2-0
            # Aproximación: P(2-0) ≈ prob^2 * factor
            return prob_player1 ** 2 * 0.7
        elif handicap == 1.5:
            # Cubre si no pierde 0-2
            return 1.0 - ((1 - prob_player1) ** 2 * 0.7)
    
    elif format_sets == 5:
        # Al mejor de 5: más complejo
        if handicap == -1.5:
            # Necesita ganar 3-0 o 3-1
            prob_3_0 = prob_player1 ** 3 * 0.5
            prob_3_1 = prob_player1 ** 3 * (1 - prob_player1) * 3 * 0.6
            return prob_3_0 + prob_3_1
        elif handicap == 1.5:
            return 1.0 - (prob_player1 ** 3 * 0.5)
    
    # Default: usar probabilidad base
    return prob_player1 if handicap < 0 else (1 - prob_player1)


# ==================== CÁLCULO DE EV PARA MERCADOS DE TENIS ====================

def calculate_ev_moneyline_tennis(
    row: dict,
    league: str,
    elo_player1: Optional[float] = None,
    elo_player2: Optional[float] = None,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado Moneyline en tenis
    
    Args:
        row: Diccionario con datos de la cuota
        league: Nombre del torneo (ATP, WTA, etc.)
        elo_player1: Rating ELO del jugador 1 (opcional)
        elo_player2: Rating ELO del jugador 2 (opcional)
        use_baseline: Si True y no hay ELO, usa probabilidad 50-50
    
    Returns:
        float: EV o None si no se puede calcular
    """
    selection = row["selection"].upper()
    odds = float(row["odds"])
    
    # Si tenemos ratings ELO, usarlos
    if elo_player1 is not None and elo_player2 is not None:
        prob_player1 = elo_win_probability(elo_player1, elo_player2)
        
        if selection == "HOME":
            prob = prob_player1
        elif selection == "AWAY":
            prob = 1.0 - prob_player1
        else:
            return None
    else:
        # Sin ELO, usar baseline 50-50 o probabilidad implícita
        if use_baseline:
            prob = 0.5  # Neutral
        else:
            return None
    
    return expected_value(prob, odds)


def calculate_ev_total_games_tennis(
    row: dict,
    league: str,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado Total Games en tenis
    
    Args:
        row: Diccionario con datos de la cuota
        league: Nombre del torneo
        use_baseline: Si True, usa parámetros baseline
    
    Returns:
        float: EV o None si no se puede calcular
    """
    try:
        config = get_sport_config("tennis", league, "games")
        mu_games = config["mu"]
        sigma_games = config["sigma"]
    except (ValueError, KeyError):
        return None
    
    line = float(row["line"]) if row["line"] is not None else None
    if line is None:
        return None
    
    selection = row["selection"].upper()
    odds = float(row["odds"])
    
    if selection == "OVER":
        prob = prob_over_games(mu_games, sigma_games, line)
    elif selection == "UNDER":
        prob = prob_under_games(mu_games, sigma_games, line)
    else:
        return None
    
    return expected_value(prob, odds)


def calculate_ev_handicap_sets_tennis(
    row: dict,
    league: str,
    prob_player1: Optional[float] = None,
    use_baseline: bool = True
) -> Optional[float]:
    """
    Calcula EV para mercado Hándicap de Sets
    
    Args:
        row: Diccionario con datos de la cuota
        league: Nombre del torneo
        prob_player1: Probabilidad de victoria del jugador 1 (opcional)
        use_baseline: Si True, usa 50-50 si no hay prob
    
    Returns:
        float: EV o None si no se puede calcular
    """
    line = float(row["line"]) if row["line"] is not None else None
    if line is None:
        return None
    
    selection = row["selection"].upper()
    odds = float(row["odds"])
    
    # Determinar formato (3 o 5 sets) según el torneo
    format_sets = 5 if "Grand Slam" in league else 3
    
    # Si no tenemos probabilidad, usar baseline
    if prob_player1 is None:
        if use_baseline:
            prob_player1 = 0.5
        else:
            return None
    
    if selection == "HOME":
        prob = prob_set_handicap(prob_player1, line, format_sets)
    elif selection == "AWAY":
        prob = prob_set_handicap(1.0 - prob_player1, -line, format_sets)
    else:
        return None
    
    return expected_value(prob, odds)


# ==================== AJUSTES AVANZADOS ====================

def adjust_for_fatigue(
    base_prob: float,
    matches_last_7_days: int,
    fatigue_factor: float = 0.02
) -> float:
    """
    Ajusta probabilidad por fatiga del jugador
    
    Args:
        base_prob: Probabilidad base
        matches_last_7_days: Partidos jugados en últimos 7 días
        fatigue_factor: Factor de penalización por partido (0.02 = 2%)
    
    Returns:
        float: Probabilidad ajustada
    """
    if matches_last_7_days <= 1:
        return base_prob
    
    # Penalizar por cada partido adicional
    penalty = (matches_last_7_days - 1) * fatigue_factor
    adjusted_prob = base_prob * (1.0 - penalty)
    
    return max(0.01, min(0.99, adjusted_prob))


def adjust_for_h2h(
    base_prob: float,
    h2h_wins: int,
    h2h_losses: int,
    weight: float = 0.15
) -> float:
    """
    Ajusta probabilidad basado en historial head-to-head
    
    Args:
        base_prob: Probabilidad base
        h2h_wins: Victorias en enfrentamientos directos
        h2h_losses: Derrotas en enfrentamientos directos
        weight: Peso del H2H (0.15 = 15%)
    
    Returns:
        float: Probabilidad ajustada
    """
    total_h2h = h2h_wins + h2h_losses
    
    if total_h2h == 0:
        return base_prob
    
    h2h_prob = h2h_wins / total_h2h
    
    # Combinar probabilidad base con H2H
    adjusted_prob = (1 - weight) * base_prob + weight * h2h_prob
    
    return max(0.01, min(0.99, adjusted_prob))


def estimate_elo_from_ranking(
    ranking: int,
    base_elo: float = 1500.0,
    top_elo: float = 2400.0
) -> float:
    """
    Estima rating ELO aproximado desde ranking ATP/WTA
    
    Args:
        ranking: Posición en el ranking (1 = mejor)
        base_elo: ELO base para jugadores fuera del top
        top_elo: ELO para el #1 del mundo
    
    Returns:
        float: ELO estimado
    """
    if ranking <= 0:
        return base_elo
    
    # Función logarítmica inversa
    # Top 1 = 2400, Top 10 ≈ 2200, Top 50 ≈ 1900, Top 100 ≈ 1700
    
    if ranking == 1:
        return top_elo
    
    # Escala logarítmica
    elo = top_elo - (math.log(ranking) * 150)
    
    return max(base_elo, elo)


# ==================== FUNCIONES DE UTILIDAD ====================

def get_fair_odds_moneyline_tennis(
    prob_player1: float
) -> dict[str, float]:
    """
    Calcula cuotas justas para Moneyline en tenis
    
    Args:
        prob_player1: Probabilidad de victoria del jugador 1
    
    Returns:
        dict: {"HOME": odds, "AWAY": odds}
    """
    if prob_player1 <= 0 or prob_player1 >= 1:
        return {"HOME": 2.0, "AWAY": 2.0}
    
    return {
        "HOME": 1.0 / prob_player1,
        "AWAY": 1.0 / (1.0 - prob_player1)
    }


def analyze_tennis_match(
    player1_name: str,
    player2_name: str,
    elo_player1: float,
    elo_player2: float,
    surface: str = "hard",
    format_sets: int = 3
) -> dict:
    """
    Análisis completo de un partido de tenis
    
    Args:
        player1_name: Nombre del jugador 1
        player2_name: Nombre del jugador 2
        elo_player1: Rating ELO del jugador 1
        elo_player2: Rating ELO del jugador 2
        surface: Superficie ("clay", "grass", "hard")
        format_sets: Formato (3 o 5 sets)
    
    Returns:
        dict: Análisis completo con probabilidades y cuotas justas
    """
    # Probabilidad base
    prob_player1 = elo_win_probability(elo_player1, elo_player2)
    
    # Estimar games totales
    mu_games, sigma_games = estimate_games_from_match_prob(prob_player1, format_sets)
    
    # Cuotas justas
    fair_odds_ml = get_fair_odds_moneyline_tennis(prob_player1)
    
    return {
        "player1": player1_name,
        "player2": player2_name,
        "elo_player1": elo_player1,
        "elo_player2": elo_player2,
        "prob_player1_win": prob_player1,
        "prob_player2_win": 1.0 - prob_player1,
        "fair_odds_player1": fair_odds_ml["HOME"],
        "fair_odds_player2": fair_odds_ml["AWAY"],
        "expected_games": mu_games,
        "games_std_dev": sigma_games,
        "surface": surface,
        "format": f"Best of {format_sets}",
    }
