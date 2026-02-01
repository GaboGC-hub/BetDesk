# app/decision/ev.py
"""
Módulo de cálculo de Expected Value (EV) mejorado
Mantiene nombres de funciones y firmas públicas para compatibilidad con el resto
Mejoras realizadas:
 - Corrección y clarificación de las fórmulas de cobertura de spread
 - Manejo robusto de desvigado (devig) cuando hay duplicados o falta de datos
 - Validaciones defensivas y logs explicativos
 - Tipado más explícito y docstrings ampliados
 - Uso seguro de probabilidades (acotado entre 0 y 1)
"""
from typing import Dict, List, Optional, Tuple
import math
import logging

from .devig import devig_odds, get_fair_odds
from .basketball_stats import BasketballStatsEngine

logger = logging.getLogger(__name__)


def normal_cdf(x: float) -> float:
    """CDF de la distribución normal estándar.

    Args:
        x: valor z
    Returns:
        Probabilidad acumulada P(Z <= x)
    """
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def prob_over(mu: float, sigma: float, line: float) -> float:
    """
    Calcula P(Total > line) suponiendo normalidad.
    Si sigma es 0 o negativo devuelve 0.5 (incertidumbre máxima).
    """
    if sigma <= 0 or math.isnan(sigma):
        logger.debug("sigma no positivo en prob_over: %s", sigma)
        return 0.5

    z = (line - mu) / sigma
    return 1.0 - normal_cdf(z)


def prob_under(mu: float, sigma: float, line: float) -> float:
    """Calcula P(Total < line)."""
    if sigma <= 0 or math.isnan(sigma):
        logger.debug("sigma no positivo en prob_under: %s", sigma)
        return 0.5

    z = (line - mu) / sigma
    return normal_cdf(z)


def prob_home_cover(mu_margin: float, sigma: float, line: float) -> float:
    """
    Calcula la probabilidad de que el equipo local (home) cubra el spread.

    Fórmula (definición consistente con handicap aplicado al HOME):
        Se considera que la línea aplica al HOME (handicap sobre el HOME).
        Home cubre si: margin + line > 0  => margin > -line

    Args:
        mu_margin: media del margen (home - away)
        sigma: desviación estándar del margen
        line: línea del spread (ej: -5.5 significa home favorito por 5.5)
    """
    if sigma <= 0 or math.isnan(sigma):
        logger.debug("sigma no positivo en prob_home_cover: %s", sigma)
        return 0.5

    # Umbral: home cubre si margin > -line
    threshold = -line
    z = (threshold - mu_margin) / sigma
    return 1.0 - normal_cdf(z)


def prob_away_cover(mu_margin: float, sigma: float, line: float) -> float:
    """
    Probabilidad de que el visitante (away) cubra el spread.

    Dado que home_cover = P(margin > -line) entonces away_cover = P(margin < -line)
    """
    if sigma <= 0 or math.isnan(sigma):
        logger.debug("sigma no positivo en prob_away_cover: %s", sigma)
        return 0.5

    threshold = -line
    z = (threshold - mu_margin) / sigma
    return normal_cdf(z)


def expected_value(p: float, odds: float) -> float:
    """
    EV por unidad apostada.

    EV = p * (odds - 1) - (1 - p)

    Args:
        p: probabilidad de ganar (0..1)
        odds: cuota decimal (>0)
    Returns:
        EV en unidades por cada 1 apostado (ej: 0.05 = 5% retorno esperado)
    """
    if odds <= 0 or math.isnan(odds):
        logger.warning("Odds inválidas en expected_value: %s", odds)
        return 0.0

    # Asegurar p en rango
    p_clamped = min(max(p, 0.0), 1.0)
    return p_clamped * (odds - 1.0) - (1.0 - p_clamped)


def calculate_ev_with_devig(
    model_prob: float,
    odd: Dict,
    market_odds: List[Dict],
    use_devig: bool = True
) -> Dict:
    """
    Calcula EV usando odds desvigadas (sin margen) cuando sea posible.

    Mantiene la firma original para compatibilidad.
    """
    # Validaciones básicas
    if not isinstance(odd, dict) or 'odds' not in odd:
        raise ValueError("'odd' debe ser un dict que contenga la clave 'odds'")

    original_odd = float(odd['odds'])

    fair_odd = original_odd
    devig_applied = False

    if use_devig and isinstance(market_odds, list) and len(market_odds) >= 2:
        # Filtrar sólo las entradas exactamente del mismo mercado/line/selection
        same_market_entries = [
            o for o in market_odds
            if o.get('market') == odd.get('market')
            and o.get('line') == odd.get('line')
            and o.get('selection') == odd.get('selection')
            and 'odds' in o
        ]

        if len(same_market_entries) >= 2:
            try:
                odds_list = [float(o['odds']) for o in same_market_entries]
                # Calcular odds "fair" usando la función devig_odds
                devigged = devig_odds(odds_list)

                # Intentar localizar el índice de la odd original intentando coincidir bookmaker primero
                idx = None
                try:
                    idx = next(i for i, o in enumerate(same_market_entries)
                               if float(o.get('odds')) == original_odd and o.get('bookmaker') == odd.get('bookmaker'))
                except StopIteration:
                    # Si no coincide por bookmaker, buscar por el primer índice que tenga el mismo valor de odds
                    try:
                        idx = odds_list.index(original_odd)
                    except ValueError:
                        idx = 0

                # Asegurar tamaño y tomar la fair odd correspondiente
                if idx is not None and 0 <= idx < len(devigged):
                    fair_odd = float(devigged[idx])
                    devig_applied = not math.isclose(fair_odd, original_odd)
                else:
                    fair_odd = original_odd

            except Exception as e:
                logger.exception("Error al aplicar devig_odds: %s", e)
                fair_odd = original_odd
        else:
            logger.debug("No hay suficientes odds en el mismo mercado para desvigado: %s", same_market_entries)

    # Seguridad: evitar odds no positivas
    if fair_odd <= 0 or math.isnan(fair_odd):
        logger.warning("Fair odd inválida calculada, usando original: %s", fair_odd)
        fair_odd = original_odd

    # Calcular probabilidad implícita acotada
    implied_prob = 1.0 / fair_odd if fair_odd > 0 else 0.5
    implied_prob = min(max(implied_prob, 0.0), 1.0)

    # Asegurar model_prob en rango
    model_prob_clamped = min(max(float(model_prob), 0.0), 1.0)

    # EV
    ev = expected_value(model_prob_clamped, fair_odd)
    ev_pct = ev * 100.0

    # Edge y ROI (mantengo nombres originales)
    edge = model_prob_clamped - implied_prob
    roi = ev_pct

    return {
        "ev": ev,
        "ev_pct": ev_pct,
        "model_prob": model_prob_clamped,
        "implied_prob": implied_prob,
        "original_odd": original_odd,
        "devigged_odd": fair_odd,
        "edge": edge,
        "roi": roi,
        "devig_applied": bool(use_devig and devig_applied)
    }


def calculate_basketball_total_ev(
    home: str,
    away: str,
    league: str,
    line: float,
    selection: str,
    odd: Dict,
    market_odds: List[Dict],
    stats_engine: Optional[BasketballStatsEngine] = None,
    use_devig: bool = True
) -> Dict:
    """
    Calcula EV para mercado TOTAL de baloncesto usando estadísticas dinámicas.

    Conserva argumentos y formato de salida para compatibilidad.
    """
    if stats_engine is None:
        stats_engine = BasketballStatsEngine()

    # Obtener media y desviación del total (esperamos una tupla (mean,std))
    total_mean, total_std = stats_engine.calculate_matchup_total(home, away, league)

    sel = (selection or "").upper()
    if sel == "OVER":
        model_prob = prob_over(total_mean, total_std, line)
    else:
        model_prob = prob_under(total_mean, total_std, line)

    ev_result = calculate_ev_with_devig(model_prob, odd, market_odds, use_devig)

    ev_result.update({
        "model_type": "NORMAL_DISTRIBUTION",
        "model_params": {
            "total_mean": total_mean,
            "total_std": total_std,
            "line": line,
            "selection": sel
        }
    })

    return ev_result


def calculate_basketball_spread_ev(
    home: str,
    away: str,
    league: str,
    spread_line: float,
    selection: str,
    odd: Dict,
    market_odds: List[Dict],
    stats_engine: Optional[BasketballStatsEngine] = None,
    use_devig: bool = True
) -> Dict:
    """
    Calcula EV para mercado SPREAD de baloncesto.

    Devuelve estructura compatible con calculate_ev_with_devig.
    """
    if stats_engine is None:
        stats_engine = BasketballStatsEngine()

    spread_probs = stats_engine.calculate_spread_probabilities(home, away, league, spread_line)

    sel = (selection or "").upper()
    if sel == "HOME":
        model_prob = float(spread_probs.get("home_cover", 0.5))
    else:
        model_prob = float(spread_probs.get("away_cover", 0.5))

    ev_result = calculate_ev_with_devig(model_prob, odd, market_odds, use_devig)

    ev_result.update({
        "model_type": "SPREAD_ANALYSIS",
        "model_params": {
            "expected_margin": spread_probs.get("expected_margin"),
            "margin_std": spread_probs.get("margin_std"),
            "spread_line": spread_line,
            "selection": sel
        }
    })

    return ev_result


def should_bet(
    ev_result: Dict,
    min_ev: float = 0.03,
    min_edge: float = 0.02,
    min_prob: float = 0.45
) -> Tuple[bool, str]:
    """
    Determina si vale la pena apostar basado en criterios simples.

    Usa valores por defecto compatibles con la versión original.
    """
    ev = float(ev_result.get("ev", 0.0))
    edge = float(ev_result.get("edge", 0.0))
    prob = float(ev_result.get("model_prob", 0.0))

    if ev < min_ev:
        return False, f"EV insuficiente: {ev*100:.1f}% < {min_ev*100:.1f}%"

    if edge < min_edge:
        return False, f"Edge insuficiente: {edge*100:.1f}% < {min_edge*100:.1f}%"

    if prob < min_prob:
        return False, f"Probabilidad muy baja: {prob*100:.1f}% < {min_prob*100:.1f}%"

    return True, f"✅ EV={ev*100:.1f}%, Edge={edge*100:.1f}%, Prob={prob*100:.1f}%"


# Nota: el bloque if __name__ == '__main__' se omite en este archivo de librería para evitar
# ejecución accidental cuando se importa desde otros módulos del proyecto.
