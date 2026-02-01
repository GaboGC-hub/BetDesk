# app/decision/devig.py
"""
Módulo de desvigado (devig) de odds
Elimina el margen de la casa de apuestas antes de calcular EV
"""
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


def devig_odds(odds_list: List[float], method: str = "multiplicative") -> List[float]:
    """
    Elimina el margen (vig) de las odds
    
    Args:
        odds_list: Lista de odds del mismo mercado [1.90, 2.10, 3.50]
        method: Método de desvigado ("multiplicative", "additive", "power")
    
    Returns:
        Lista de odds desvigadas [1.95, 2.15, 3.60]
    
    Ejemplo:
        >>> devig_odds([1.90, 2.10])
        [1.905, 2.105]
    """
    if not odds_list or len(odds_list) < 2:
        return odds_list
    
    # Filtrar odds inválidas
    valid_odds = [o for o in odds_list if o > 1.0]
    if len(valid_odds) < 2:
        return odds_list
    
    if method == "multiplicative":
        return _devig_multiplicative(valid_odds)
    elif method == "additive":
        return _devig_additive(valid_odds)
    elif method == "power":
        return _devig_power(valid_odds)
    else:
        return _devig_multiplicative(valid_odds)


def _devig_multiplicative(odds_list: List[float]) -> List[float]:
    """
    Método multiplicativo (más preciso)
    
    Proceso:
    1. Convertir odds a probabilidades implícitas
    2. Calcular overround (margen de la casa)
    3. Normalizar probabilidades (eliminar margen)
    4. Convertir de vuelta a odds
    """
    # Convertir odds a probabilidades implícitas
    implied_probs = [1.0 / odd for odd in odds_list]
    
    # Calcular overround (margen de la casa)
    overround = sum(implied_probs)
    
    if overround <= 1.0:
        # No hay margen, retornar odds originales
        return odds_list
    
    # Normalizar probabilidades (eliminar margen)
    true_probs = [p / overround for p in implied_probs]
    
    # Convertir de vuelta a odds
    devigged_odds = [1.0 / p if p > 0 else odd for p, odd in zip(true_probs, odds_list)]
    
    return devigged_odds


def _devig_additive(odds_list: List[float]) -> List[float]:
    """
    Método aditivo (más simple)
    
    Resta el margen proporcionalmente a cada probabilidad
    """
    implied_probs = [1.0 / odd for odd in odds_list]
    overround = sum(implied_probs)
    
    if overround <= 1.0:
        return odds_list
    
    margin = overround - 1.0
    margin_per_outcome = margin / len(odds_list)
    
    true_probs = [p - margin_per_outcome for p in implied_probs]
    true_probs = [max(p, 0.01) for p in true_probs]  # Evitar divisiones por cero
    
    devigged_odds = [1.0 / p for p in true_probs]
    
    return devigged_odds


def _devig_power(odds_list: List[float], k: float = 1.5) -> List[float]:
    """
    Método de potencia (Shin method)
    
    Usa un exponente para ajustar las probabilidades
    """
    implied_probs = [1.0 / odd for odd in odds_list]
    overround = sum(implied_probs)
    
    if overround <= 1.0:
        return odds_list
    
    # Aplicar potencia
    adjusted_probs = [p ** k for p in implied_probs]
    total = sum(adjusted_probs)
    
    # Normalizar
    true_probs = [p / total for p in adjusted_probs]
    
    devigged_odds = [1.0 / p if p > 0 else odd for p, odd in zip(true_probs, odds_list)]
    
    return devigged_odds


def devig_market(odds_snapshot: List[Dict], market_key: str = None) -> List[Dict]:
    """
    Desviga todas las odds de un mercado
    
    Args:
        odds_snapshot: Lista de dicts con odds
        market_key: Clave para agrupar mercado (ej: "TOTAL_228.5_OVER")
    
    Returns:
        Lista de dicts con odds desvigadas agregadas
    
    Ejemplo:
        >>> odds = [
        ...     {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.90, "bookmaker": "Bwin"},
        ...     {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.95, "bookmaker": "Bet365"},
        ...     {"market": "TOTAL", "line": 228.5, "selection": "UNDER", "odds": 2.10, "bookmaker": "Bwin"},
        ... ]
        >>> devigged = devig_market(odds)
    """
    if not odds_snapshot:
        return []
    
    # Agrupar por mercado
    grouped = {}
    for odd in odds_snapshot:
        if market_key:
            key = market_key
        else:
            key = f"{odd.get('market', '')}_{odd.get('line', '')}_{odd.get('selection', '')}"
        
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(odd)
    
    # Desvigar cada grupo
    result = []
    for key, odds_list in grouped.items():
        if len(odds_list) < 2:
            # No se puede desvigar con menos de 2 odds
            for odd in odds_list:
                result.append({
                    **odd,
                    "odds_devigged": odd["odds"],
                    "devig_method": "none"
                })
            continue
        
        # Extraer valores de odds
        odds_values = [o["odds"] for o in odds_list]
        
        # Desvigar
        devigged_values = devig_odds(odds_values)
        
        # Agregar odds desvigadas a los dicts
        for odd, devigged in zip(odds_list, devigged_values):
            result.append({
                **odd,
                "odds_devigged": devigged,
                "devig_method": "multiplicative",
                "original_odds": odd["odds"],
                "margin_removed": odd["odds"] - devigged
            })
    
    return result


def calculate_market_margin(odds_list: List[float]) -> float:
    """
    Calcula el margen (overround) de un mercado
    
    Args:
        odds_list: Lista de odds del mercado
    
    Returns:
        Margen en decimal (ej: 0.05 = 5%)
    
    Ejemplo:
        >>> calculate_market_margin([1.90, 2.10])
        0.002  # 0.2% de margen
    """
    if not odds_list or len(odds_list) < 2:
        return 0.0
    
    implied_probs = [1.0 / odd for odd in odds_list if odd > 1.0]
    overround = sum(implied_probs)
    
    return max(overround - 1.0, 0.0)


def get_fair_odds(odds_list: List[float]) -> float:
    """
    Calcula la odd justa promedio de un mercado
    
    Returns:
        Odd justa promedio (float)
    """
    devigged = devig_odds(odds_list, method="multiplicative")
    return sum(devigged) / len(devigged) if devigged else 0.0


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo 1: Mercado 1X2
    print("Ejemplo 1: Mercado 1X2")
    odds_1x2 = [2.10, 3.40, 3.60]  # Home, Draw, Away
    print(f"Odds originales: {odds_1x2}")
    print(f"Margen: {calculate_market_margin(odds_1x2)*100:.2f}%")
    
    devigged = devig_odds(odds_1x2)
    print(f"Odds desvigadas: {[f'{o:.3f}' for o in devigged]}")
    print(f"Margen después: {calculate_market_margin(devigged)*100:.2f}%")
    print()
    
    # Ejemplo 2: Mercado TOTAL
    print("Ejemplo 2: Mercado TOTAL")
    odds_total = [1.90, 2.10]  # Over, Under
    print(f"Odds originales: {odds_total}")
    print(f"Margen: {calculate_market_margin(odds_total)*100:.2f}%")
    
    devigged = devig_odds(odds_total)
    print(f"Odds desvigadas: {[f'{o:.3f}' for o in devigged]}")
    print(f"Margen después: {calculate_market_margin(devigged)*100:.2f}%")
