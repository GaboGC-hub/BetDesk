# app/decision/utils.py
"""
Utilidades comunes para modelos de decisión
"""
import math
from typing import Optional
from decimal import Decimal, getcontext

getcontext().prec = 10

def D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    return Decimal(str(x))


def normal_cdf(x: float) -> float:
    """
    Función de distribución acumulativa (CDF) de la distribución normal estándar
    
    Args:
        x: Valor en la distribución normal estándar
    
    Returns:
        float: Probabilidad P(X <= x)
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def normal_pdf(x: float) -> float:
    """
    Función de densidad de probabilidad (PDF) de la distribución normal estándar
    
    Args:
        x: Valor en la distribución normal estándar
    
    Returns:
        float: Densidad de probabilidad en x
    """
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


def prob_over_normal(mu: float, sigma: float, line: float) -> float:
    """
    Calcula P(X > line) para una distribución normal
    
    Args:
        mu: Media de la distribución
        sigma: Desviación estándar
        line: Línea/umbral
    
    Returns:
        float: Probabilidad de que X sea mayor que line
    """
    if sigma <= 0:
        return 0.0
    
    z = (line - mu) / sigma
    return 1.0 - normal_cdf(z)


def prob_under_normal(mu: float, sigma: float, line: float) -> float:
    """
    Calcula P(X < line) para una distribución normal
    
    Args:
        mu: Media de la distribución
        sigma: Desviación estándar
        line: Línea/umbral
    
    Returns:
        float: Probabilidad de que X sea menor que line
    """
    if sigma <= 0:
        return 0.0
    
    z = (line - mu) / sigma
    return normal_cdf(z)


def poisson_pmf(k: int, lambda_param: float) -> float:
    """
    Función de masa de probabilidad de Poisson
    
    Args:
        k: Número de eventos
        lambda_param: Parámetro lambda (tasa promedio)
    
    Returns:
        float: P(X = k)
    """
    if lambda_param <= 0:
        return 0.0
    
    return (lambda_param ** k) * math.exp(-lambda_param) / math.factorial(k)


def poisson_cdf(k: int, lambda_param: float) -> float:
    """
    Función de distribución acumulativa de Poisson
    
    Args:
        k: Número de eventos
        lambda_param: Parámetro lambda (tasa promedio)
    
    Returns:
        float: P(X <= k)
    """
    if lambda_param <= 0:
        return 0.0
    
    prob = 0.0
    for i in range(k + 1):
        prob += poisson_pmf(i, lambda_param)
    
    return prob


def expected_value(prob: float, odds: float) -> float:
    """
    Calcula el valor esperado (EV) de una apuesta
    
    Args:
        prob: Probabilidad real del evento (0-1)
        odds: Cuota decimal (ej. 2.0)
    
    Returns:
        float: EV por unidad apostada
    
    Ejemplo:
        prob=0.55, odds=2.0 -> EV = 0.55*(2-1) - 0.45 = 0.10 (10% de ganancia esperada)
    """
    if prob <= 0 or prob >= 1:
        return -1.0
    
    if odds <= 1.0:
        return -1.0
    
    # EV = P(win) * (odds - 1) - P(lose) * 1
    return prob * (odds - 1.0) - (1.0 - prob)


def implied_probability(odds: float, remove_vig: bool = False, total_prob: float = 1.0) -> float:
    """
    Calcula la probabilidad implícita de una cuota
    
    Args:
        odds: Cuota decimal
        remove_vig: Si True, ajusta por el margen de la casa (vig)
        total_prob: Suma total de probabilidades implícitas (para calcular vig)
    
    Returns:
        float: Probabilidad implícita (0-1)
    """
    if odds <= 1.0:
        return 0.0
    
    implied_prob = 1.0 / odds
    
    if remove_vig and total_prob > 1.0:
        # Ajustar por overround (margen de la casa)
        implied_prob = implied_prob / total_prob
    
    return implied_prob


def kelly_criterion(prob: float, odds: float, fraction: float = 1.0) -> float:
    """
    Calcula el tamaño óptimo de apuesta según el criterio de Kelly
    
    Args:
        prob: Probabilidad real del evento
        odds: Cuota decimal
        fraction: Fracción del Kelly a usar (0.25 = Quarter Kelly, más conservador)
    
    Returns:
        float: Fracción del bankroll a apostar (0-1)
    """
    if prob <= 0 or prob >= 1 or odds <= 1.0:
        return 0.0
    
    # Kelly = (prob * odds - 1) / (odds - 1)
    kelly = (prob * odds - 1.0) / (odds - 1.0)
    
    # Aplicar fracción (para ser más conservador)
    kelly = kelly * fraction
    
    # No apostar si Kelly es negativo o mayor a 1
    return max(0.0, min(kelly, 1.0))


def sharpe_ratio(ev: float, std_dev: float, risk_free_rate: float = 0.0) -> float:
    """
    Calcula el ratio de Sharpe para una apuesta
    
    Args:
        ev: Valor esperado
        std_dev: Desviación estándar del retorno
        risk_free_rate: Tasa libre de riesgo
    
    Returns:
        float: Ratio de Sharpe
    """
    if std_dev <= 0:
        return 0.0
    
    return (ev - risk_free_rate) / std_dev


def confidence_interval(prob: float, n_samples: int, confidence: float = 0.95) -> tuple[float, float]:
    """
    Calcula el intervalo de confianza para una probabilidad estimada
    
    Args:
        prob: Probabilidad estimada
        n_samples: Número de muestras
        confidence: Nivel de confianza (0.95 = 95%)
    
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    if n_samples <= 0 or prob <= 0 or prob >= 1:
        return (prob, prob)
    
    # Z-score para el nivel de confianza
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence, 1.96)
    
    # Error estándar
    se = math.sqrt(prob * (1 - prob) / n_samples)
    
    # Intervalo
    lower = max(0.0, prob - z * se)
    upper = min(1.0, prob + z * se)
    
    return (lower, upper)


def odds_to_american(decimal_odds: float) -> int:
    """
    Convierte cuotas decimales a formato americano
    
    Args:
        decimal_odds: Cuota decimal (ej. 2.0)
    
    Returns:
        int: Cuota americana (ej. +100)
    """
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1.0) * 100)
    else:
        return int(-100 / (decimal_odds - 1.0))


def american_to_odds(american_odds: int) -> float:
    """
    Convierte cuotas americanas a formato decimal
    
    Args:
        american_odds: Cuota americana (ej. +100 o -110)
    
    Returns:
        float: Cuota decimal
    """
    if american_odds > 0:
        return 1.0 + (american_odds / 100.0)
    else:
        return 1.0 + (100.0 / abs(american_odds))


def calculate_vig(odds_list: list[float]) -> float:
    """
    Calcula el margen de la casa (vig/overround) de un mercado
    
    Args:
        odds_list: Lista de cuotas decimales del mercado
    
    Returns:
        float: Margen de la casa (ej. 0.05 = 5%)
    """
    if not odds_list:
        return 0.0
    
    total_implied_prob = sum(1.0 / odds for odds in odds_list if odds > 1.0)
    
    return max(0.0, total_implied_prob - 1.0)


def remove_vig_proportional(odds_list: list[float]) -> list[float]:
    """
    Elimina el margen de la casa proporcionalmente de las cuotas
    
    Args:
        odds_list: Lista de cuotas decimales
    
    Returns:
        list: Lista de cuotas ajustadas (fair odds)
    """
    if not odds_list:
        return []
    
    total_implied_prob = sum(1.0 / odds for odds in odds_list if odds > 1.0)
    
    if total_implied_prob <= 1.0:
        return odds_list  # No hay vig
    
    # Ajustar cada cuota proporcionalmente
    fair_odds = []
    for odds in odds_list:
        if odds > 1.0:
            implied_prob = 1.0 / odds
            fair_prob = implied_prob / total_implied_prob
            fair_odds.append(1.0 / fair_prob)
        else:
            fair_odds.append(odds)
    
    return fair_odds
