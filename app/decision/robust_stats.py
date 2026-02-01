# app/decision/robust_stats.py
"""
Motor de estadísticas robustas
Incluye H2H, forma reciente, tendencias, estadísticas de jugadores
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class RobustStatsEngine:
    """
    Motor de estadísticas robustas para análisis profundo
    """
    
    def __init__(self, db_session=None):
        self.db = db_session
        self._cache = {}
        self._cache_ttl = timedelta(hours=12)
    
    def get_h2h_stats(
        self,
        home: str,
        away: str,
        sport: str,
        league: str,
        last_n: int = 5
    ) -> Dict:
        """
        Obtiene estadísticas Head-to-Head (enfrentamientos directos)
        
        Args:
            home: Equipo local
            away: Equipo visitante
            sport: Deporte
            league: Liga
            last_n: Últimos N enfrentamientos
        
        Returns:
            {
                "total_games": 5,
                "home_wins": 3,
                "away_wins": 2,
                "home_win_rate": 0.60,
                "avg_total": 225.5,
                "avg_margin": 5.2,
                "last_results": ["W", "L", "W", "W", "L"],
                "trend": "HOME_FAVORED" | "AWAY_FAVORED" | "BALANCED",
                "data_quality": "HIGH" | "MEDIUM" | "LOW"
            }
        """
        cache_key = f"h2h_{home}_{away}_{sport}_{league}_{last_n}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.utcnow() - cached["last_updated"] < self._cache_ttl:
                return cached["data"]
        
        if not self.db:
            return self._get_default_h2h()
        
        try:
            sql = text("""
                SELECT 
                    home_team, away_team, home_score, away_score, game_date
                FROM game_results
                WHERE sport = :sport
                  AND league = :league
                  AND (
                      (home_team = :home AND away_team = :away) OR
                      (home_team = :away AND away_team = :home)
                  )
                  AND game_date >= NOW() - INTERVAL '2 years'
                  AND home_score IS NOT NULL
                  AND away_score IS NOT NULL
                ORDER BY game_date DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(sql, {
                "sport": sport,
                "league": league,
                "home": home,
                "away": away,
                "limit": last_n
            }).fetchall()
            
            if not results:
                return self._get_default_h2h()
            
            # Analizar resultados
            home_wins = 0
            totals = []
            margins = []
            last_results = []
            
            for r in results:
                total = r['home_score'] + r['away_score']
                totals.append(total)
                
                # Determinar ganador desde perspectiva del equipo local actual
                if r['home_team'] == home:
                    margin = r['home_score'] - r['away_score']
                    if r['home_score'] > r['away_score']:
                        home_wins += 1
                        last_results.append("W")
                    else:
                        last_results.append("L")
                else:
                    margin = r['away_score'] - r['home_score']
                    if r['away_score'] > r['home_score']:
                        home_wins += 1
                        last_results.append("W")
                    else:
                        last_results.append("L")
                
                margins.append(margin)
            
            total_games = len(results)
            away_wins = total_games - home_wins
            home_win_rate = home_wins / total_games
            
            # Determinar tendencia
            if home_win_rate >= 0.65:
                trend = "HOME_FAVORED"
            elif home_win_rate <= 0.35:
                trend = "AWAY_FAVORED"
            else:
                trend = "BALANCED"
            
            # Evaluar calidad de datos
            if total_games >= last_n * 0.8:
                data_quality = "HIGH"
            elif total_games >= last_n * 0.5:
                data_quality = "MEDIUM"
            else:
                data_quality = "LOW"
            
            stats = {
                "total_games": total_games,
                "home_wins": home_wins,
                "away_wins": away_wins,
                "home_win_rate": home_win_rate,
                "avg_total": float(np.mean(totals)) if totals else 0.0,
                "avg_margin": float(np.mean(margins)) if margins else 0.0,
                "last_results": last_results,
                "trend": trend,
                "data_quality": data_quality,
                "last_updated": datetime.utcnow()
            }
            
            # Guardar en cache
            self._cache[cache_key] = {
                "data": stats,
                "last_updated": datetime.utcnow()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting H2H stats: {e}")
            return self._get_default_h2h()
    
    def get_form_stats(
        self,
        team: str,
        sport: str,
        league: str,
        last_n: int = 5
    ) -> Dict:
        """
        Obtiene estadísticas de forma reciente
        
        Returns:
            {
                "wins": 4,
                "losses": 1,
                "win_rate": 0.80,
                "avg_points_scored": 115.2,
                "avg_points_allowed": 108.5,
                "avg_margin": 6.7,
                "streak": "W4" | "L2",
                "trend": "HOT" | "COLD" | "NEUTRAL",
                "over_under_record": {"over": 3, "under": 2}
            }
        """
        if not self.db:
            return {"trend": "NEUTRAL"}
        
        try:
            sql = text("""
                SELECT 
                    home_team, away_team, home_score, away_score,
                    (home_team = :team) as is_home,
                    game_date
                FROM game_results
                WHERE sport = :sport
                  AND league = :league
                  AND (home_team = :team OR away_team = :team)
                  AND game_date >= NOW() - INTERVAL '30 days'
                  AND home_score IS NOT NULL
                  AND away_score IS NOT NULL
                ORDER BY game_date DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(sql, {
                "sport": sport,
                "league": league,
                "team": team,
                "limit": last_n
            }).fetchall()
            
            if not results:
                return {"trend": "NEUTRAL"}
            
            wins = 0
            points_scored = []
            points_allowed = []
            margins = []
            results_sequence = []
            
            for r in results:
                if r['is_home']:
                    scored = r['home_score']
                    allowed = r['away_score']
                    won = scored > allowed
                else:
                    scored = r['away_score']
                    allowed = r['home_score']
                    won = scored > allowed
                
                points_scored.append(scored)
                points_allowed.append(allowed)
                margins.append(scored - allowed)
                
                if won:
                    wins += 1
                    results_sequence.append("W")
                else:
                    results_sequence.append("L")
            
            losses = len(results) - wins
            win_rate = wins / len(results)
            
            # Calcular racha actual
            streak_type = results_sequence[0]
            streak_count = 1
            for r in results_sequence[1:]:
                if r == streak_type:
                    streak_count += 1
                else:
                    break
            streak = f"{streak_type}{streak_count}"
            
            # Determinar tendencia
            if win_rate >= 0.75:
                trend = "HOT"
            elif win_rate <= 0.25:
                trend = "COLD"
            else:
                trend = "NEUTRAL"
            
            return {
                "wins": wins,
                "losses": losses,
                "win_rate": win_rate,
                "avg_points_scored": float(np.mean(points_scored)),
                "avg_points_allowed": float(np.mean(points_allowed)),
                "avg_margin": float(np.mean(margins)),
                "streak": streak,
                "trend": trend,
                "games_analyzed": len(results),
                "results_sequence": results_sequence
            }
            
        except Exception as e:
            logger.error(f"Error getting form stats: {e}")
            return {"trend": "NEUTRAL"}
    
    def get_trends(
        self,
        team: str,
        sport: str,
        league: str,
        market: str = "TOTAL",
        last_n: int = 10
    ) -> Dict:
        """
        Obtiene tendencias de mercados específicos
        
        Args:
            market: "TOTAL", "SPREAD", etc.
        
        Returns:
            {
                "over_count": 7,
                "under_count": 3,
                "over_rate": 0.70,
                "avg_total": 228.5,
                "trend": "OVER_TREND" | "UNDER_TREND" | "NEUTRAL",
                "confidence": 0.85
            }
        """
        if not self.db or market != "TOTAL":
            return {"trend": "NEUTRAL"}
        
        try:
            sql = text("""
                SELECT 
                    home_score, away_score,
                    (home_score + away_score) as total
                FROM game_results
                WHERE sport = :sport
                  AND league = :league
                  AND (home_team = :team OR away_team = :team)
                  AND game_date >= NOW() - INTERVAL '30 days'
                  AND home_score IS NOT NULL
                  AND away_score IS NOT NULL
                ORDER BY game_date DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(sql, {
                "sport": sport,
                "league": league,
                "team": team,
                "limit": last_n
            }).fetchall()
            
            if not results:
                return {"trend": "NEUTRAL"}
            
            totals = [r['total'] for r in results]
            avg_total = float(np.mean(totals))
            
            # Calcular tendencia OVER/UNDER vs promedio de liga
            # (simplificado: usar 220 como promedio de NBA)
            league_avg = 220.0
            
            over_count = sum(1 for t in totals if t > league_avg)
            under_count = len(totals) - over_count
            over_rate = over_count / len(totals)
            
            # Determinar tendencia
            if over_rate >= 0.70:
                trend = "OVER_TREND"
                confidence = over_rate
            elif over_rate <= 0.30:
                trend = "UNDER_TREND"
                confidence = 1 - over_rate
            else:
                trend = "NEUTRAL"
                confidence = 0.5
            
            return {
                "over_count": over_count,
                "under_count": under_count,
                "over_rate": over_rate,
                "avg_total": avg_total,
                "trend": trend,
                "confidence": confidence,
                "games_analyzed": len(totals)
            }
            
        except Exception as e:
            logger.error(f"Error getting trends: {e}")
            return {"trend": "NEUTRAL"}
    
    def get_comprehensive_analysis(
        self,
        home: str,
        away: str,
        sport: str,
        league: str
    ) -> Dict:
        """
        Análisis comprehensivo combinando todas las estadísticas
        
        Returns:
            {
                "h2h": {...},
                "home_form": {...},
                "away_form": {...},
                "home_trends": {...},
                "away_trends": {...},
                "recommendation": {
                    "market": "TOTAL",
                    "selection": "OVER",
                    "confidence": 0.75,
                    "reasoning": [str]
                }
            }
        """
        h2h = self.get_h2h_stats(home, away, sport, league)
        home_form = self.get_form_stats(home, sport, league)
        away_form = self.get_form_stats(away, sport, league)
        home_trends = self.get_trends(home, sport, league)
        away_trends = self.get_trends(away, sport, league)
        
        # Generar recomendación basada en análisis
        recommendation = self._generate_recommendation(
            h2h, home_form, away_form, home_trends, away_trends
        )
        
        return {
            "h2h": h2h,
            "home_form": home_form,
            "away_form": away_form,
            "home_trends": home_trends,
            "away_trends": away_trends,
            "recommendation": recommendation
        }
    
    def _generate_recommendation(
        self,
        h2h: Dict,
        home_form: Dict,
        away_form: Dict,
        home_trends: Dict,
        away_trends: Dict
    ) -> Dict:
        """
        Genera recomendación basada en análisis estadístico
        """
        reasoning = []
        confidence_factors = []
        
        # Analizar tendencia OVER/UNDER
        over_signals = 0
        under_signals = 0
        
        # Factor 1: H2H
        if h2h.get("avg_total", 0) > 220:
            over_signals += 1
            reasoning.append(f"H2H promedio alto: {h2h['avg_total']:.1f}")
            confidence_factors.append(0.15)
        elif h2h.get("avg_total", 0) < 210:
            under_signals += 1
            reasoning.append(f"H2H promedio bajo: {h2h['avg_total']:.1f}")
            confidence_factors.append(0.15)
        
        # Factor 2: Forma de equipos
        home_avg = home_form.get("avg_points_scored", 0)
        away_avg = away_form.get("avg_points_scored", 0)
        combined_avg = home_avg + away_avg
        
        if combined_avg > 225:
            over_signals += 1
            reasoning.append(f"Equipos anotando bien: {combined_avg:.1f} PPG combinado")
            confidence_factors.append(0.20)
        elif combined_avg < 215:
            under_signals += 1
            reasoning.append(f"Equipos anotando poco: {combined_avg:.1f} PPG combinado")
            confidence_factors.append(0.20)
        
        # Factor 3: Tendencias
        if home_trends.get("trend") == "OVER_TREND":
            over_signals += 1
            reasoning.append(f"Local con tendencia OVER ({home_trends['over_rate']*100:.0f}%)")
            confidence_factors.append(0.15)
        
        if away_trends.get("trend") == "OVER_TREND":
            over_signals += 1
            reasoning.append(f"Visitante con tendencia OVER ({away_trends['over_rate']*100:.0f}%)")
            confidence_factors.append(0.15)
        
        # Determinar recomendación
        if over_signals > under_signals:
            selection = "OVER"
            confidence = min(sum(confidence_factors), 0.85)
        elif under_signals > over_signals:
            selection = "UNDER"
            confidence = min(sum(confidence_factors), 0.85)
        else:
            selection = "NONE"
            confidence = 0.0
            reasoning.append("Señales mixtas - no hay recomendación clara")
        
        return {
            "market": "TOTAL",
            "selection": selection,
            "confidence": confidence,
            "reasoning": reasoning,
            "over_signals": over_signals,
            "under_signals": under_signals
        }
    
    def _get_default_h2h(self) -> Dict:
        """Retorna H2H por defecto"""
        return {
            "total_games": 0,
            "trend": "BALANCED",
            "data_quality": "NONE"
        }
    
    def format_analysis_summary(self, analysis: Dict) -> str:
        """
        Formatea análisis comprehensivo para mostrar
        """
        lines = []
        lines.append("📊 ANÁLISIS ESTADÍSTICO COMPLETO")
        lines.append("")
        
        # H2H
        h2h = analysis["h2h"]
        if h2h.get("total_games", 0) > 0:
            lines.append(f"🔄 H2H (últimos {h2h['total_games']} juegos):")
            lines.append(f"   • Record: {h2h['home_wins']}-{h2h['away_wins']}")
            lines.append(f"   • Total promedio: {h2h['avg_total']:.1f}")
            lines.append(f"   • Tendencia: {h2h['trend']}")
        else:
            lines.append("🔄 H2H: Sin datos")
        
        lines.append("")
        
        # Forma
        home_form = analysis["home_form"]
        away_form = analysis["away_form"]
        
        if home_form.get("trend") != "NEUTRAL":
            lines.append(f"🏠 Forma Local:")
            lines.append(f"   • Record: {home_form['wins']}-{home_form['losses']} ({home_form['streak']})")
            lines.append(f"   • Promedio: {home_form['avg_points_scored']:.1f} PPG")
            lines.append(f"   • Tendencia: {home_form['trend']}")
        
        if away_form.get("trend") != "NEUTRAL":
            lines.append(f"✈️ Forma Visitante:")
            lines.append(f"   • Record: {away_form['wins']}-{away_form['losses']} ({away_form['streak']})")
            lines.append(f"   • Promedio: {away_form['avg_points_scored']:.1f} PPG")
            lines.append(f"   • Tendencia: {away_form['trend']}")
        
        lines.append("")
        
        # Recomendación
        rec = analysis["recommendation"]
        if rec["selection"] != "NONE":
            lines.append(f"💡 RECOMENDACIÓN:")
            lines.append(f"   • Mercado: {rec['market']} {rec['selection']}")
            lines.append(f"   • Confianza: {rec['confidence']*100:.0f}%")
            lines.append(f"   • Razonamiento:")
            for reason in rec["reasoning"]:
                lines.append(f"     - {reason}")
        
        return "\n".join(lines)


# Ejemplo de uso
if __name__ == "__main__":
    print("=" * 80)
    print("MOTOR DE ESTADÍSTICAS ROBUSTAS")
    print("=" * 80)
    
    engine = RobustStatsEngine()
    
    # Análisis comprehensivo
    analysis = engine.get_comprehensive_analysis(
        "Lakers", "Celtics", "basketball", "NBA"
    )
    
    print(engine.format_analysis_summary(analysis))
