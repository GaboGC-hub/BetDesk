# app/decision/error_detection.py
"""
Detector de errores en las cuotas (mejorado)

Mantiene las firmas públicas y nombres de funciones/clases para compatibilidad.
Mejoras principales:
 - Manejo defensivo de tipos (odds como floats/Decimal)
 - Estadística robusta (ddof=1 cuando el tamaño de muestra lo permite)
 - Cálculo de confianza más informativo combinando múltiples señales
 - Mejor razonamiento y mensajes en `reasoning`
 - Validaciones de entrada y logs más claros
 - Conserva las claves de salida originales y agrega campos auxiliares
"""
from typing import List, Dict, Optional
import logging
import math
import numpy as np
from decimal import Decimal
from statistics import mean, pstdev
from .utils import D

logger = logging.getLogger(__name__)


class OddsErrorDetector:
    """
    Detecta posibles errores en las cuotas que representan oportunidades.

    Conserva constantes públicas que pueden ajustarse desde fuera si es necesario.
    """

    # Umbrales para detección (ajustables)
    SIGMA_THRESHOLD_ERROR: float = 3.0      # 3 sigmas = posible error
    SIGMA_THRESHOLD_CRITICAL: float = 4.0   # 4 sigmas = error muy probable

    HISTORICAL_DEVIATION_THRESHOLD: float = 0.30  # 30% desviación vs histórico
    MIN_MARKET_SAMPLE: int = 3
    MIN_HISTORICAL_SAMPLE: int = 5

    @staticmethod
    def _to_float(value) -> float:
        """Convierte una odd a float de forma segura (acepta Decimal)."""
        if value is None:
            return float('nan')
        if isinstance(value, Decimal):
            return float(value)
        try:
            return float(value)
        except Exception:
            return float('nan')

    @staticmethod
    def detect_pricing_error(
        odd: Dict,
        odds_snapshot: List[Dict],
        historical_data: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Detecta errores de pricing en una odd.

        Devuelve un dict con las claves originales esperadas por el sistema.
        """
        reasoning: List[str] = []

        # Validaciones mínimas
        if not isinstance(odd, dict) or 'odds' not in odd:
            logger.debug("Entrada inválida para detect_pricing_error: %s", odd)
            return {
                "is_error": False,
                "confidence": 0.0,
                "error_type": "NONE",
                "reasoning": ["Odd inválida o incompleta"]
            }

        actual_odd = OddsErrorDetector._to_float(odd.get('odds'))

        # 1. Comparar con mercado actual
        market_analysis = OddsErrorDetector._analyze_market_deviation(odd, odds_snapshot)

        if not market_analysis.get("valid", False):
            reasoning.append("Datos de mercado insuficientes para análisis estadístico")
            return {
                "is_error": False,
                "confidence": 0.0,
                "error_type": "NONE",
                "reasoning": reasoning,
                "market_analysis": market_analysis
            }

        deviation_sigmas = float(market_analysis["deviation_sigmas"])
        market_mean = float(market_analysis["market_mean"])

        # 2. Histórico (si aplica)
        historical_analysis = None
        if historical_data:
            historical_analysis = OddsErrorDetector._analyze_historical_deviation(odd, historical_data)

        # Iniciales
        is_error = False
        error_type = "NONE"
        confidence = 0.0
        action = "SKIP"

        # Señales individuales que suman confianza
        signals = []  # cada señal es (peso, mensaje)

        # Señal: desviación sigma
        if deviation_sigmas >= OddsErrorDetector.SIGMA_THRESHOLD_CRITICAL:
            signals.append((0.6, f"Desviación crítica de mercado: {deviation_sigmas:.2f}σ"))
        elif deviation_sigmas >= OddsErrorDetector.SIGMA_THRESHOLD_ERROR:
            signals.append((0.35, f"Desviación significativa de mercado: {deviation_sigmas:.2f}σ"))
        else:
            signals.append((0.0, f"Desviación de mercado normal: {deviation_sigmas:.2f}σ"))

        # Señal: confirmación histórica
        if historical_analysis and historical_analysis.get("valid"):
            dev_pct = float(historical_analysis.get("deviation_pct", 0.0))
            if historical_analysis.get("significant_deviation"):
                signals.append((0.25, f"Confirmado por histórico: {dev_pct*100:.0f}%"))
            else:
                signals.append((0.05, f"Histórico sin confirmación fuerte: {dev_pct*100:.0f}%"))

        # Señal: consistencia con mercados relacionados
        consistency_check = OddsErrorDetector._check_market_consistency(odd, odds_snapshot)
        if consistency_check.get("inconsistent"):
            signals.append((0.15, "Inconsistencia con mercados relacionados"))
            for inc in consistency_check.get('inconsistencies', []):
                reasoning.append(inc)

        # Combinar señales para formar confidence
        raw_confidence = sum(w for w, _ in signals)
        # Normalizar (max posible 1.0+), escalar y saturar
        confidence = min(raw_confidence, 1.0)

        # Decidir error / tipo / acción usando reglas heurísticas
        if deviation_sigmas >= OddsErrorDetector.SIGMA_THRESHOLD_CRITICAL:
            is_error = True
            # Si la odd está mucho más alta que el mercado -> posible error humano beneficioso
            if actual_odd > market_mean * 1.5:
                error_type = "HUMAN_ERROR"
                action = "BET_IMMEDIATELY"
                reasoning.append("Odd muy alta respecto al mercado; puede ser error humano (o valor) ")
            elif actual_odd < market_mean * 0.7:
                error_type = "SYSTEM_ERROR"
                action = "SKIP"
                reasoning.append("Odd muy baja respecto al mercado; posible error del sistema")
            else:
                error_type = "LATE_UPDATE"
                action = "MONITOR"
                reasoning.append("Desviación crítica pero dentro de rangos, posible actualización tardía")

        elif deviation_sigmas >= OddsErrorDetector.SIGMA_THRESHOLD_ERROR:
            # Caso 3: >3 sigmas; se requiere confirmación histórica o consistencia
            if historical_analysis and historical_analysis.get("valid") and historical_analysis.get("significant_deviation"):
                is_error = True
                error_type = "HUMAN_ERROR"
                action = "BET_IMMEDIATELY" if actual_odd > market_mean else "SKIP"
                reasoning.append("Desviación significativa confirmada por histórico")
            else:
                # No confirmado: monitorear
                is_error = False
                action = "MONITOR"
                reasoning.append("Desviación significativa sin confirmación histórica; monitorear")

        else:
            # No es error según desviaciones, pero si consistencia falla mucho, marcar para revisión
            if consistency_check.get("inconsistent"):
                is_error = False
                confidence = max(confidence, 0.2)
                action = "MONITOR"
                reasoning.append("Inconsistencia de mercado detectada; revisar")

        # Ajustes finales de confidence: si is_error true y señales fuertes, aumentar
        if is_error:
            confidence = max(confidence, 0.6)
            # Si es crítico, asegurarnos de marcar alto
            if deviation_sigmas >= OddsErrorDetector.SIGMA_THRESHOLD_CRITICAL:
                confidence = min(max(confidence, 0.8), 1.0)

        # Limitar confidence entre 0 y 1
        confidence = float(min(max(confidence, 0.0), 1.0))

        # Añadir razonamiento detallado (mercado/histórico)
        reasoning.append(f"Desviación en sigmas: {deviation_sigmas:.2f}")
        reasoning.append(f"Media mercado: {market_mean:.3f}, Odd actual: {actual_odd:.3f}")

        result = {
            "is_error": bool(is_error),
            "confidence": confidence,
            "error_type": error_type,
            "expected_odd": market_mean,
            "actual_odd": actual_odd,
            "deviation_sigmas": deviation_sigmas,
            "action": action,
            "reasoning": reasoning,
            "market_analysis": market_analysis,
            "historical_analysis": historical_analysis,
            "consistency_check": consistency_check
        }

        return result

    @staticmethod
    def _analyze_market_deviation(odd: Dict, odds_snapshot: List[Dict]) -> Dict:
        """
        Analiza desviación respecto al mercado actual.

        Retorna un dict con keys: valid, market_mean, market_std, market_min, market_max,
        deviation_sigmas, sample_size
        """
        # Filtrar odds del mismo mercado/línea/selección excluyendo la misma casa
        candidates = [
            OddsErrorDetector._to_float(o.get('odds')) for o in odds_snapshot
            if o.get('market') == odd.get('market')
            and o.get('line') == odd.get('line')
            and o.get('selection') == odd.get('selection')
            and o.get('bookmaker') != odd.get('bookmaker')
        ]

        # Eliminar NaNs
        market_odds = [v for v in candidates if not math.isnan(v)]

        if len(market_odds) < OddsErrorDetector.MIN_MARKET_SAMPLE:
            return {"valid": False}

        # Usar ddof=1 si sample >1 para estimador no sesgado
        ddof = 1 if len(market_odds) > 1 else 0
        market_mean = float(np.mean(market_odds))
        market_std = float(np.std(market_odds, ddof=ddof))

        if market_std == 0 or math.isnan(market_std):
            return {"valid": False}

        # Deviation en sigmas respecto a market_mean
        actual_odd = OddsErrorDetector._to_float(odd.get('odds'))
        deviation_sigmas = abs(actual_odd - market_mean) / market_std

        return {
            "valid": True,
            "market_mean": market_mean,
            "market_std": market_std,
            "market_min": min(market_odds),
            "market_max": max(market_odds),
            "deviation_sigmas": float(deviation_sigmas),
            "sample_size": len(market_odds)
        }

    @staticmethod
    def _analyze_historical_deviation(odd: Dict, historical_data: List[Dict]) -> Dict:
        """
        Analiza desviación respecto a datos históricos del mismo evento/mercado/selection.
        """
        if not historical_data:
            return {"valid": False}

        hist_vals = [
            OddsErrorDetector._to_float(h.get('odds')) for h in historical_data
            if h.get('market') == odd.get('market')
            and h.get('line') == odd.get('line')
            and h.get('selection') == odd.get('selection')
        ]

        hist_vals = [v for v in hist_vals if not math.isnan(v)]

        if len(hist_vals) < OddsErrorDetector.MIN_HISTORICAL_SAMPLE:
            return {"valid": False}

        ddof = 1 if len(hist_vals) > 1 else 0
        historical_mean = float(np.mean(hist_vals))
        historical_std = float(np.std(hist_vals, ddof=ddof))

        actual_odd = OddsErrorDetector._to_float(odd.get('odds'))
        deviation_pct = abs(actual_odd - historical_mean) / historical_mean if historical_mean != 0 else float('inf')

        significant_deviation = deviation_pct > OddsErrorDetector.HISTORICAL_DEVIATION_THRESHOLD

        return {
            "valid": True,
            "historical_mean": historical_mean,
            "historical_std": historical_std,
            "deviation_pct": float(deviation_pct),
            "significant_deviation": bool(significant_deviation),
            "sample_size": len(hist_vals)
        }

    @staticmethod
    def _check_market_consistency(odd: Dict, odds_snapshot: List[Dict]) -> Dict:
        """
        Verifica consistencia con mercados relacionados (TOTAL/MONEYLINE).
        """
        inconsistencies: List[str] = []

        market = odd.get('market')
        line = odd.get('line')
        selection = odd.get('selection')

        actual_odd = OddsErrorDetector._to_float(odd.get('odds'))

        # TOTAL (Over/Under) -> comprobar suma de probabilidades implícitas
        if market == "TOTAL":
            opposite_selection = "UNDER" if selection == "OVER" else "OVER"

            opposite_odds = [
                OddsErrorDetector._to_float(o.get('odds')) for o in odds_snapshot
                if o.get('market') == market
                and o.get('line') == line
                and o.get('selection') == opposite_selection
            ]
            opposite_odds = [v for v in opposite_odds if not math.isnan(v)]

            if opposite_odds:
                avg_opposite = float(np.mean(opposite_odds))
                implied_prob_current = 1.0 / actual_odd if actual_odd > 0 else 0.0
                implied_prob_opposite = 1.0 / avg_opposite if avg_opposite > 0 else 0.0
                total_prob = implied_prob_current + implied_prob_opposite

                # Tolerancia amplia para cubrir distintos mercados
                if total_prob < 0.95 or total_prob > 1.20:
                    inconsistencies.append(f"Probabilidades implícitas inconsistentes: {total_prob:.3f}")

        # MONEYLINE -> suma de probabilidades de ambos lados
        elif market == "MONEYLINE":
            opposite_selection = "AWAY" if selection == "HOME" else "HOME"
            opposite_odds = [
                OddsErrorDetector._to_float(o.get('odds')) for o in odds_snapshot
                if o.get('market') == market and o.get('selection') == opposite_selection
            ]
            opposite_odds = [v for v in opposite_odds if not math.isnan(v)]

            if opposite_odds:
                avg_opposite = float(np.mean(opposite_odds))
                implied_prob_current = 1.0 / actual_odd if actual_odd > 0 else 0.0
                implied_prob_opposite = 1.0 / avg_opposite if avg_opposite > 0 else 0.0
                total_prob = implied_prob_current + implied_prob_opposite
                if total_prob < 0.95 or total_prob > 1.15:
                    inconsistencies.append(f"Probabilidades implícitas inconsistentes: {total_prob:.3f}")

        return {
            "inconsistent": len(inconsistencies) > 0,
            "inconsistencies": inconsistencies
        }

    @staticmethod
    def scan_all_odds(odds_snapshot: List[Dict], historical_data: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Escanea todas las odds buscando errores (devuelve solo las que superan umbral de confianza).
        """
        errors: List[Dict] = []

        for odd in odds_snapshot:
            try:
                result = OddsErrorDetector.detect_pricing_error(odd, odds_snapshot, historical_data)
            except Exception as e:
                logger.exception("Error al analizar odd: %s", e)
                continue

            # Umbral para reportar: confidencia > 0.7 y is_error True
            if result.get("is_error") and result.get("confidence", 0.0) > 0.7:
                errors.append({**odd, "error_detection": result})

        # Ordenar por confianza
        errors.sort(key=lambda x: x["error_detection"]["confidence"], reverse=True)
        return errors


def format_error_alert(odd: Dict, error_detection: Dict) -> str:
    """
    Formatea alerta de error de cuota para mensajes/registro.
    Conserva la salida original para compatibilidad.
    """
    lines: List[str] = []
    lines.append("🚨 ERROR DE CUOTA DETECTADO 🚨")
    lines.append("")
    lines.append(f"🏀 {odd.get('event', 'Unknown')}")
    lines.append(f"📊 {odd.get('market', '')} {odd.get('line', '')} {odd.get('selection', '')}")
    lines.append(f"🏪 {odd.get('bookmaker', '')}")
    lines.append("")

    odd_val = OddsErrorDetector._to_float(odd.get('odds'))
    expected = error_detection.get('expected_odd')
    deviation = error_detection.get('deviation_sigmas')
    confidence = error_detection.get('confidence', 0.0)

    lines.append(f"💰 Cuota: {odd_val:.2f}")
    if expected is not None:
        lines.append(f"📈 Esperado: {expected:.2f}")
    if deviation is not None:
        lines.append(f"📊 Desviación: {deviation:.1f}σ")
    lines.append(f"🎯 Confianza: {confidence*100:.0f}%")
    lines.append("")
    lines.append(f"⚡ Acción: {error_detection.get('action', 'SKIP')}")
    lines.append("")
    lines.append("Razonamiento:")
    for reason in error_detection.get('reasoning', []):
        lines.append(f"  • {reason}")

    return "\n".join(lines)
