# app/decision/pick_classifier.py
"""
Clasificador de picks según su origen y confianza
Categoriza picks en: MODEL, ANOMALY, HYBRID, ARBITRAGE, ERROR
"""
from enum import Enum
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PickType(Enum):
    """Tipos de picks"""
    MODEL = "MODEL"           # EV+ basado en modelo estadístico
    ANOMALY = "ANOMALY"       # Odd anómala vs mercado
    HYBRID = "HYBRID"         # Ambos criterios (máxima confianza)
    ARBITRAGE = "ARBITRAGE"   # Oportunidad de arbitraje sin riesgo
    ERROR = "ERROR"           # Posible error de cuota (actuar inmediatamente)
    
    def __str__(self):
        return self.value


class PickPriority(Enum):
    """Prioridades de picks"""
    CRITICAL = 5    # ERROR, ARBITRAGE
    HIGH = 4        # HYBRID
    MEDIUM = 3      # MODEL con EV alto
    LOW = 2         # ANOMALY
    MINIMAL = 1     # MODEL con EV bajo
    
    def __str__(self):
        return f"Priority {self.value}"


class PickClassifier:
    """
    Clasifica picks según múltiples criterios
    """
    
    # Umbrales para clasificación
    EV_THRESHOLD_LOW = 0.03      # 3% EV mínimo
    EV_THRESHOLD_MEDIUM = 0.05   # 5% EV para prioridad media
    EV_THRESHOLD_HIGH = 0.08     # 8% EV para prioridad alta
    
    Z_SCORE_THRESHOLD_LOW = 2.0   # Z-score mínimo para anomalía
    Z_SCORE_THRESHOLD_HIGH = 3.0  # Z-score alto (muy anómalo)
    
    QUALITY_THRESHOLD = 0.70      # 70% calidad mínima
    
    @staticmethod
    def classify_pick(
        ev: Optional[float] = None,
        z_score: Optional[float] = None,
        quality_score: float = 0.0,
        is_arbitrage: bool = False,
        is_error: bool = False,
        error_confidence: float = 0.0,
        model_confidence: float = 0.0
    ) -> Dict:
        """
        Clasifica un pick según múltiples criterios
        
        Args:
            ev: Expected Value (decimal, ej: 0.05 = 5%)
            z_score: Z-score de anomalía
            quality_score: Score de calidad (0-1)
            is_arbitrage: Si es oportunidad de arbitraje
            is_error: Si es posible error de cuota
            error_confidence: Confianza del error (0-1)
            model_confidence: Confianza del modelo (0-1)
        
        Returns:
            {
                "type": PickType,
                "priority": PickPriority,
                "confidence": 0.0-1.0,
                "description": str,
                "action": "BET_NOW" | "BET_SOON" | "MONITOR" | "SKIP",
                "kelly_fraction": 0.0-1.0,  # Fracción de Kelly sugerida
                "reasoning": [str]  # Lista de razones
            }
        """
        reasoning = []
        
        # 1. ERROR DE CUOTA (máxima prioridad)
        if is_error and error_confidence > 0.7:
            reasoning.append(f"Error de cuota detectado (confianza: {error_confidence*100:.0f}%)")
            reasoning.append("Actuar INMEDIATAMENTE antes de corrección")
            
            return {
                "type": PickType.ERROR,
                "priority": PickPriority.CRITICAL,
                "confidence": error_confidence,
                "description": "⚠️ ERROR DE CUOTA - Actuar inmediatamente",
                "action": "BET_NOW",
                "kelly_fraction": 0.5,  # Apostar fuerte pero con precaución
                "reasoning": reasoning,
                "emoji": "🚨"
            }
        
        # 2. ARBITRAJE (sin riesgo)
        if is_arbitrage:
            reasoning.append("Oportunidad de arbitraje sin riesgo")
            reasoning.append("Ganancia garantizada independiente del resultado")
            
            return {
                "type": PickType.ARBITRAGE,
                "priority": PickPriority.CRITICAL,
                "confidence": 1.0,
                "description": "💎 ARBITRAJE - Sin riesgo",
                "action": "BET_NOW",
                "kelly_fraction": 1.0,  # Apostar máximo permitido
                "reasoning": reasoning,
                "emoji": "💎"
            }
        
        # 3. HYBRID (modelo + anomalía)
        has_ev = ev is not None and ev > PickClassifier.EV_THRESHOLD_LOW
        has_anomaly = z_score is not None and abs(z_score) > PickClassifier.Z_SCORE_THRESHOLD_LOW
        
        if has_ev and has_anomaly:
            reasoning.append(f"EV+{ev*100:.1f}% según modelo estadístico")
            reasoning.append(f"Anomalía detectada (Z-score: {abs(z_score):.2f})")
            reasoning.append("Doble confirmación: modelo + mercado")
            
            # Calcular confianza combinada
            ev_confidence = min(ev / PickClassifier.EV_THRESHOLD_HIGH, 1.0)
            anomaly_confidence = min(abs(z_score) / PickClassifier.Z_SCORE_THRESHOLD_HIGH, 1.0)
            combined_confidence = (ev_confidence + anomaly_confidence) / 2
            
            # Ajustar por calidad
            final_confidence = combined_confidence * quality_score
            
            # Determinar prioridad
            if ev > PickClassifier.EV_THRESHOLD_HIGH and abs(z_score) > PickClassifier.Z_SCORE_THRESHOLD_HIGH:
                priority = PickPriority.CRITICAL
                action = "BET_NOW"
                kelly = 0.4
            else:
                priority = PickPriority.HIGH
                action = "BET_SOON"
                kelly = 0.25
            
            return {
                "type": PickType.HYBRID,
                "priority": priority,
                "confidence": final_confidence,
                "description": f"⭐ HYBRID - EV+{ev*100:.1f}% + Z={abs(z_score):.2f}",
                "action": action,
                "kelly_fraction": kelly,
                "reasoning": reasoning,
                "emoji": "⭐",
                "ev": ev,
                "z_score": z_score
            }
        
        # 4. SOLO MODELO (EV+)
        if has_ev:
            reasoning.append(f"EV+{ev*100:.1f}% según modelo estadístico")
            
            if model_confidence > 0:
                reasoning.append(f"Confianza del modelo: {model_confidence*100:.0f}%")
            
            # Calcular confianza
            ev_confidence = min(ev / PickClassifier.EV_THRESHOLD_HIGH, 1.0)
            final_confidence = ev_confidence * quality_score
            
            # Determinar prioridad y acción
            if ev > PickClassifier.EV_THRESHOLD_HIGH:
                priority = PickPriority.MEDIUM
                action = "BET_SOON"
                kelly = 0.20
                description = f"💰 MODEL - EV+{ev*100:.1f}% (Alto)"
            elif ev > PickClassifier.EV_THRESHOLD_MEDIUM:
                priority = PickPriority.MEDIUM
                action = "BET_SOON"
                kelly = 0.15
                description = f"💰 MODEL - EV+{ev*100:.1f}% (Medio)"
            else:
                priority = PickPriority.MINIMAL
                action = "MONITOR"
                kelly = 0.10
                description = f"💰 MODEL - EV+{ev*100:.1f}% (Bajo)"
            
            return {
                "type": PickType.MODEL,
                "priority": priority,
                "confidence": final_confidence,
                "description": description,
                "action": action,
                "kelly_fraction": kelly,
                "reasoning": reasoning,
                "emoji": "💰",
                "ev": ev
            }
        
        # 5. SOLO ANOMALÍA
        if has_anomaly:
            reasoning.append(f"Anomalía detectada (Z-score: {abs(z_score):.2f})")
            reasoning.append("Odd significativamente diferente del mercado")
            
            # Calcular confianza
            anomaly_confidence = min(abs(z_score) / PickClassifier.Z_SCORE_THRESHOLD_HIGH, 1.0)
            final_confidence = anomaly_confidence * quality_score
            
            # Determinar prioridad
            if abs(z_score) > PickClassifier.Z_SCORE_THRESHOLD_HIGH:
                priority = PickPriority.MEDIUM
                action = "BET_SOON"
                kelly = 0.15
                description = f"📊 ANOMALY - Z={abs(z_score):.2f} (Alto)"
            else:
                priority = PickPriority.LOW
                action = "MONITOR"
                kelly = 0.10
                description = f"📊 ANOMALY - Z={abs(z_score):.2f}"
            
            return {
                "type": PickType.ANOMALY,
                "priority": priority,
                "confidence": final_confidence,
                "description": description,
                "action": action,
                "kelly_fraction": kelly,
                "reasoning": reasoning,
                "emoji": "📊",
                "z_score": z_score
            }
        
        # 6. NO CALIFICA
        reasoning.append("No cumple criterios mínimos")
        reasoning.append(f"EV: {ev*100:.1f}% (mín: {PickClassifier.EV_THRESHOLD_LOW*100:.1f}%)" if ev else "Sin EV")
        reasoning.append(f"Z-score: {abs(z_score):.2f} (mín: {PickClassifier.Z_SCORE_THRESHOLD_LOW})" if z_score else "Sin anomalía")
        
        return {
            "type": None,
            "priority": None,
            "confidence": 0.0,
            "description": "❌ NO CALIFICA",
            "action": "SKIP",
            "kelly_fraction": 0.0,
            "reasoning": reasoning,
            "emoji": "❌"
        }
    
    @staticmethod
    def get_action_emoji(action: str) -> str:
        """Retorna emoji según la acción"""
        emojis = {
            "BET_NOW": "🚀",
            "BET_SOON": "✅",
            "MONITOR": "👀",
            "SKIP": "❌"
        }
        return emojis.get(action, "")
    
    @staticmethod
    def get_priority_emoji(priority: Optional[PickPriority]) -> str:
        """Retorna emoji según la prioridad"""
        if priority is None:
            return ""
        
        emojis = {
            PickPriority.CRITICAL: "🔥🔥🔥🔥🔥",
            PickPriority.HIGH: "🔥🔥🔥🔥",
            PickPriority.MEDIUM: "🔥🔥🔥",
            PickPriority.LOW: "🔥🔥",
            PickPriority.MINIMAL: "🔥"
        }
        return emojis.get(priority, "")
    
    @staticmethod
    def format_classification(classification: Dict) -> str:
        """
        Formatea la clasificación para mostrar
        
        Args:
            classification: Resultado de classify_pick()
        
        Returns:
            String formateado
        """
        if not classification.get("type"):
            return "❌ Pick no califica"
        
        lines = []
        lines.append(f"{classification['emoji']} {classification['description']}")
        lines.append(f"Prioridad: {PickClassifier.get_priority_emoji(classification['priority'])}")
        lines.append(f"Confianza: {classification['confidence']*100:.0f}%")
        lines.append(f"Acción: {PickClassifier.get_action_emoji(classification['action'])} {classification['action']}")
        lines.append(f"Kelly: {classification['kelly_fraction']*100:.0f}%")
        
        if classification.get("reasoning"):
            lines.append("\nRazonamiento:")
            for reason in classification["reasoning"]:
                lines.append(f"  • {reason}")
        
        return "\n".join(lines)


def calculate_kelly_criterion(
    probability: float,
    odds: float,
    fraction: float = 0.25
) -> float:
    """
    Calcula el tamaño de apuesta según Kelly Criterion
    
    Args:
        probability: Probabilidad de ganar (0-1)
        odds: Cuota decimal (ej: 1.90)
        fraction: Fracción de Kelly a usar (0.25 = 25% Kelly)
    
    Returns:
        Porcentaje del bankroll a apostar (0-1)
    
    Fórmula:
        Kelly% = (probability × odds - 1) / (odds - 1)
    """
    if odds <= 1.0 or probability <= 0 or probability >= 1:
        return 0.0
    
    kelly = (probability * odds - 1) / (odds - 1)
    
    # Aplicar fracción (más conservador)
    fractional_kelly = kelly * fraction
    
    # Limitar entre 0 y 1
    return max(0.0, min(fractional_kelly, 1.0))


# Ejemplo de uso
if __name__ == "__main__":
    print("=" * 80)
    print("EJEMPLOS DE CLASIFICACIÓN DE PICKS")
    print("=" * 80)
    
    # Ejemplo 1: HYBRID (modelo + anomalía)
    print("\n1. HYBRID PICK:")
    result = PickClassifier.classify_pick(
        ev=0.085,
        z_score=3.2,
        quality_score=0.85
    )
    print(PickClassifier.format_classification(result))
    
    # Ejemplo 2: Solo MODEL
    print("\n" + "=" * 80)
    print("2. MODEL PICK:")
    result = PickClassifier.classify_pick(
        ev=0.06,
        quality_score=0.75
    )
    print(PickClassifier.format_classification(result))
    
    # Ejemplo 3: Solo ANOMALY
    print("\n" + "=" * 80)
    print("3. ANOMALY PICK:")
    result = PickClassifier.classify_pick(
        z_score=2.8,
        quality_score=0.70
    )
    print(PickClassifier.format_classification(result))
    
    # Ejemplo 4: ERROR
    print("\n" + "=" * 80)
    print("4. ERROR PICK:")
    result = PickClassifier.classify_pick(
        is_error=True,
        error_confidence=0.9,
        quality_score=0.80
    )
    print(PickClassifier.format_classification(result))
    
    # Ejemplo 5: No califica
    print("\n" + "=" * 80)
    print("5. NO CALIFICA:")
    result = PickClassifier.classify_pick(
        ev=0.02,
        z_score=1.5,
        quality_score=0.60
    )
    print(PickClassifier.format_classification(result))
