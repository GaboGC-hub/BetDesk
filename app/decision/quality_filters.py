# app/decision/quality_filters.py
"""
Filtros de calidad para picks
Asegura que solo se alerten picks de alta calidad
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np
import logging

logger = logging.getLogger(__name__)


class QualityFilter:
    """
    Filtros de calidad para validar picks antes de alertar
    """
    
    # Bookmakers considerados "sharp" (profesionales)
    SHARP_BOOKMAKERS = [
        'Pinnacle', 'Betfair', 'Bet365', 'Bookmaker.eu', 
        'SBObet', 'IBC', 'Singbet'
    ]
    
    # Bookmakers considerados "soft" (recreativos)
    SOFT_BOOKMAKERS = [
        'Bwin', '1xBet', 'Betsson', 'Codere', 'William Hill',
        'Ladbrokes', 'Coral', 'Paddy Power'
    ]
    
    @staticmethod
    def check_liquidity(
        odd: Dict,
        odds_snapshot: List[Dict], 
        min_bookmakers: int = 3
    ) -> Dict:
        """
        Verifica liquidez: mínimo N bookmakers con la misma línea
        
        Args:
            odd: Odd a verificar
            odds_snapshot: Lista de odds del mismo mercado
            min_bookmakers: Mínimo de bookmakers requeridos
        
        Returns:
            {
                "passed": True/False,
                "bookmaker_count": 5,
                "bookmakers": ["Bwin", "Bet365", ...],
                "score": 0.0-1.0
            }
        """
        # Filtrar odds relevantes (mismo mercado, línea y selección)
        market = odd.get('market')
        line = odd.get('line')
        selection = odd.get('selection')
        
        relevant_odds = [
            o for o in odds_snapshot
            if o.get('market') == market
            and o.get('line') == line
            and o.get('selection') == selection
        ]
        
        # Contar bookmakers únicos
        bookmakers = list(set([o.get('bookmaker', '') for o in relevant_odds]))
        count = len(bookmakers)
        
        # Calcular score (0-1)
        score = min(count / (min_bookmakers * 2), 1.0)  # Máximo score con 2x el mínimo
        
        return {
            "passed": count >= min_bookmakers,
            "bookmaker_count": count,
            "bookmakers": bookmakers,
            "score": score,
            "min_required": min_bookmakers
        }
    
    @staticmethod
    def check_stability(
        odd: Dict, 
        historical_odds: List[Dict], 
        max_variation: float = 0.05,
        time_window_minutes: int = 60
    ) -> Dict:
        """
        Verifica estabilidad: variación < 5% en última hora
        
        Args:
            odd: Odd actual
            historical_odds: Odds históricas
            max_variation: Variación máxima permitida (0.05 = 5%)
            time_window_minutes: Ventana de tiempo en minutos
        
        Returns:
            {
                "passed": True/False,
                "variation": 0.03,  # 3%
                "min_odd": 1.85,
                "max_odd": 1.95,
                "avg_odd": 1.90,
                "score": 0.0-1.0
            }
        """
        if not historical_odds:
            return {
                "passed": False,
                "variation": 0.0,
                "score": 0.0,
                "reason": "No historical data"
            }
        
        # Filtrar por ventana de tiempo
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        recent_odds = [
            o for o in historical_odds 
            if o.get('captured_at_utc', datetime.min) >= cutoff_time
        ]
        
        if len(recent_odds) < 2:
            return {
                "passed": False,
                "variation": 0.0,
                "score": 0.0,
                "reason": "Insufficient historical data"
            }
        
        # Calcular estadísticas
        odds_values = [o['odds'] for o in recent_odds]
        min_odd = min(odds_values)
        max_odd = max(odds_values)
        avg_odd = np.mean(odds_values)
        
        # Calcular variación
        if min_odd > 0:
            variation = (max_odd - min_odd) / min_odd
        else:
            variation = 1.0
        
        # Calcular score (inverso de variación)
        score = max(1.0 - (variation / max_variation), 0.0)
        
        return {
            "passed": variation <= max_variation,
            "variation": variation,
            "min_odd": min_odd,
            "max_odd": max_odd,
            "avg_odd": avg_odd,
            "current_odd": odd['odds'],
            "score": score,
            "samples": len(recent_odds)
        }
    
    @staticmethod
    def check_sharp_books(
        odd: Dict, 
        odds_snapshot: List[Dict],
        tolerance: float = 0.10
    ) -> Dict:
        """
        Verifica que bookmakers "sharp" tengan odds similares
        
        Args:
            odd: Odd a verificar
            odds_snapshot: Todas las odds del mercado
            tolerance: Tolerancia permitida (0.10 = 10%)
        
        Returns:
            {
                "passed": True/False,
                "sharp_odds": [1.90, 1.92, 1.88],
                "sharp_avg": 1.90,
                "deviation": 0.05,  # 5%
                "score": 0.0-1.0
            }
        """
        # Buscar odds de sharp books
        sharp_odds = [
            o['odds'] for o in odds_snapshot 
            if o.get('bookmaker', '') in QualityFilter.SHARP_BOOKMAKERS
            and o.get('market') == odd.get('market')
            and o.get('line') == odd.get('line')
            and o.get('selection') == odd.get('selection')
        ]
        
        if not sharp_odds:
            return {
                "passed": False,
                "sharp_odds": [],
                "score": 0.0,
                "reason": "No sharp bookmakers found"
            }
        
        # Calcular promedio de sharp books
        sharp_avg = np.mean(sharp_odds)
        
        # Calcular desviación
        if sharp_avg > 0:
            deviation = abs(odd['odds'] - sharp_avg) / sharp_avg
        else:
            deviation = 1.0
        
        # Calcular score
        score = max(1.0 - (deviation / tolerance), 0.0)
        
        return {
            "passed": deviation <= tolerance,
            "sharp_odds": sharp_odds,
            "sharp_avg": sharp_avg,
            "current_odd": odd['odds'],
            "deviation": deviation,
            "score": score,
            "sharp_count": len(sharp_odds)
        }
    
    @staticmethod
    def check_volume(
        odds_snapshot: List[Dict],
        min_total_bookmakers: int = 5
    ) -> Dict:
        """
        Verifica volumen: suficientes bookmakers en el mercado
        
        Args:
            odds_snapshot: Todas las odds del mercado
            min_total_bookmakers: Mínimo de bookmakers totales
        
        Returns:
            {
                "passed": True/False,
                "total_bookmakers": 8,
                "sharp_count": 3,
                "soft_count": 5,
                "score": 0.0-1.0
            }
        """
        bookmakers = list(set([o.get('bookmaker', '') for o in odds_snapshot]))
        total = len(bookmakers)
        
        sharp_count = len([b for b in bookmakers if b in QualityFilter.SHARP_BOOKMAKERS])
        soft_count = len([b for b in bookmakers if b in QualityFilter.SOFT_BOOKMAKERS])
        
        # Calcular score
        score = min(total / (min_total_bookmakers * 2), 1.0)
        
        return {
            "passed": total >= min_total_bookmakers,
            "total_bookmakers": total,
            "sharp_count": sharp_count,
            "soft_count": soft_count,
            "score": score,
            "bookmakers": bookmakers
        }
    
    @staticmethod
    def apply_all_filters(
        odd: Dict, 
        odds_snapshot: List[Dict], 
        historical_odds: List[Dict] = None,
        min_quality_score: float = 0.7
    ) -> Dict:
        """
        Aplica todos los filtros y retorna resultado consolidado
        
        Args:
            odd: Odd a evaluar
            odds_snapshot: Snapshot actual del mercado
            historical_odds: Odds históricas (opcional)
            min_quality_score: Score mínimo requerido (0.7 = 70%)
        
        Returns:
            {
                "passed": True/False,
                "quality_score": 0.85,  # 0-1
                "filters": {
                    "liquidity": {...},
                    "stability": {...},
                    "sharp_books": {...},
                    "volume": {...}
                },
                "recommendation": "STRONG_BET" | "MODERATE_BET" | "WEAK_BET" | "SKIP"
            }
        """
        # Aplicar filtros individuales
        liquidity = QualityFilter.check_liquidity(
            odd,
            odds_snapshot
        )
        
        stability = QualityFilter.check_stability(
            odd,
            historical_odds or []
        )
        
        sharp_books = QualityFilter.check_sharp_books(
            odd,
            odds_snapshot
        )
        
        volume = QualityFilter.check_volume(odds_snapshot)
        
        # Calcular score ponderado
        weights = {
            "liquidity": 0.30,
            "stability": 0.25,
            "sharp_books": 0.30,
            "volume": 0.15
        }
        
        quality_score = (
            liquidity["score"] * weights["liquidity"] +
            stability["score"] * weights["stability"] +
            sharp_books["score"] * weights["sharp_books"] +
            volume["score"] * weights["volume"]
        )
        
        # Determinar recomendación
        if quality_score >= 0.85:
            recommendation = "STRONG_BET"
        elif quality_score >= 0.70:
            recommendation = "MODERATE_BET"
        elif quality_score >= 0.50:
            recommendation = "WEAK_BET"
        else:
            recommendation = "SKIP"
        
        # Verificar que pase el mínimo
        passed = quality_score >= min_quality_score
        
        return {
            "passed": passed,
            "quality_score": quality_score,
            "filters": {
                "liquidity": liquidity,
                "stability": stability,
                "sharp_books": sharp_books,
                "volume": volume
            },
            "recommendation": recommendation,
            "weights": weights
        }


def get_quality_summary(quality_result: Dict) -> str:
    """
    Genera resumen legible de la calidad del pick
    
    Args:
        quality_result: Resultado de apply_all_filters()
    
    Returns:
        String con resumen formateado
    """
    score = quality_result["quality_score"]
    rec = quality_result["recommendation"]
    filters = quality_result["filters"]
    
    summary = f"📊 Calidad: {score*100:.0f}% ({rec})\n"
    summary += f"├─ Liquidez: {filters['liquidity']['bookmaker_count']} bookmakers\n"
    summary += f"├─ Estabilidad: {filters['stability'].get('variation', 0)*100:.1f}% variación\n"
    summary += f"├─ Sharp books: {filters['sharp_books'].get('sharp_count', 0)} confirmaciones\n"
    summary += f"└─ Volumen: {filters['volume']['total_bookmakers']} bookmakers totales\n"
    
    return summary


# Ejemplo de uso
if __name__ == "__main__":
    # Ejemplo de odds snapshot
    odds_snapshot = [
        {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.90, "bookmaker": "Bwin"},
        {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.92, "bookmaker": "Bet365"},
        {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.88, "bookmaker": "Pinnacle"},
        {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.91, "bookmaker": "Betfair"},
        {"market": "TOTAL", "line": 228.5, "selection": "OVER", "odds": 1.95, "bookmaker": "1xBet"},
    ]
    
    odd_to_check = odds_snapshot[0]
    
    result = QualityFilter.apply_all_filters(odd_to_check, odds_snapshot)
    
    print("Resultado de filtros de calidad:")
    print(f"Passed: {result['passed']}")
    print(f"Quality Score: {result['quality_score']:.2f}")
    print(f"Recommendation: {result['recommendation']}")
    print("\nDetalle:")
    print(get_quality_summary(result))
