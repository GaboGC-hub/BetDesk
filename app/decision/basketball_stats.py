# app/decision/basketball_stats.py

"""
Motor de estadísticas dinámicas para basketball
Calcula mean/std por equipo basado en datos reales
"""
from typing import Dict, Tuple, Optional, List
from datetime import datetime, timedelta
import numpy as np
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


class BasketballStatsEngine:
    """
    Motor de estadísticas dinámicas para basketball
    Calcula estadísticas por equipo en lugar de usar valores fijos
    """
    
    # Valores por defecto si no hay suficientes datos
    DEFAULT_STATS = {
        "NBA": {
            "points_mean": 112.0,
            "points_std": 10.0,
            "opponent_points_mean": 112.0,
            "opponent_points_std": 10.0,
            "total_mean": 224.0,
            "total_std": 14.0
        },
        "CBA": {
            "points_mean": 105.0,
            "points_std": 12.0,
            "opponent_points_mean": 105.0,
            "opponent_points_std": 12.0,
            "total_mean": 210.0,
            "total_std": 16.0
        }
    }
    
    MIN_GAMES_REQUIRED = 5  # Mínimo de partidos para calcular stats
    
    def __init__(self, db_session=None):
        """
        Args:
            db_session: Sesión de base de datos (opcional)
        """
        self.db = db_session
        self._cache = {}  # Cache de estadísticas
        self._cache_ttl = timedelta(hours=6)  # TTL del cache
    
    def get_team_stats(
        self, 
        team: str, 
        league: str, 
        last_n_games: int = 10,
        use_cache: bool = True
    ) -> Dict:
        """
        Obtiene estadísticas dinámicas de un equipo
        
        Args:
            team: Nombre del equipo
            league: Liga (NBA, CBA, etc.)
            last_n_games: Número de partidos a analizar
            use_cache: Si usar cache
        
        Returns:
            {
                "points_mean": 112.5,
                "points_std": 8.3,
                "opponent_points_mean": 108.2,
                "opponent_points_std": 7.9,
                "total_mean": 220.7,
                "total_std": 11.2,
                "games_analyzed": 10,
                "last_updated": datetime,
                "data_quality": "HIGH" | "MEDIUM" | "LOW" | "DEFAULT"
            }
        """
        # Verificar cache
        cache_key = f"{team}_{league}_{last_n_games}"
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.utcnow() - cached["last_updated"] < self._cache_ttl:
                return cached
        
        # Si no hay BD, usar valores por defecto
        if not self.db:
            return self._get_default_stats(league, team)
        
        try:
            # Consultar últimos N partidos del equipo
            sql = text("""
                SELECT 
                    home_team, away_team, home_score, away_score,
                    (home_team = :team) as is_home,
                    game_date
                FROM game_results
                WHERE (home_team = :team OR away_team = :team)
                  AND league = :league
                  AND game_date >= NOW() - INTERVAL '60 days'
                  AND home_score IS NOT NULL
                  AND away_score IS NOT NULL
                ORDER BY game_date DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(sql, {
                "team": team,
                "league": league,
                "limit": last_n_games
            }).fetchall()
            
            if len(results) < self.MIN_GAMES_REQUIRED:
                logger.warning(f"Insufficient data for {team} ({len(results)} games), using defaults")
                return self._get_default_stats(league, team)
            
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
            
            # Calcular estadísticas
            stats = {
                "points_mean": float(np.mean(team_points)),
                "points_std": float(np.std(team_points)),
                "opponent_points_mean": float(np.mean(opponent_points)),
                "opponent_points_std": float(np.std(opponent_points)),
                "total_mean": float(np.mean(totals)),
                "total_std": float(np.std(totals)),
                "games_analyzed": len(results),
                "last_updated": datetime.utcnow(),
                "data_quality": self._assess_data_quality(len(results), last_n_games),
                "team": team,
                "league": league
            }
            
            # Guardar en cache
            self._cache[cache_key] = stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats for {team}: {e}")
            return self._get_default_stats(league, team)
    
    def calculate_matchup_total(
        self, 
        home: str, 
        away: str, 
        league: str,
        last_n_games: int = 10
    ) -> Tuple[float, float]:
        """
        Calcula mean y std esperados para el total del partido
        
        Args:
            home: Equipo local
            away: Equipo visitante
            league: Liga
            last_n_games: Partidos a analizar
        
        Returns:
            (mean, std) - Ej: (225.5, 12.3)
        
        Método:
            1. Obtener stats de ambos equipos
            2. Promediar puntos esperados considerando ataque y defensa
            3. Combinar desviaciones estándar
        """
        home_stats = self.get_team_stats(home, league, last_n_games)
        away_stats = self.get_team_stats(away, league, last_n_games)
        
        # Calcular puntos esperados del local
        # Promedio entre: lo que anota el local y lo que permite el visitante
        home_expected = (
            home_stats['points_mean'] * 0.6 +  # 60% peso al ataque
            away_stats['opponent_points_mean'] * 0.4  # 40% peso a la defensa rival
        )
        
        # Calcular puntos esperados del visitante
        away_expected = (
            away_stats['points_mean'] * 0.6 +
            home_stats['opponent_points_mean'] * 0.4
        )
        
        # Total esperado
        total_mean = home_expected + away_expected
        
        # Desviación estándar combinada
        # Usar fórmula de varianza combinada
        total_variance = (
            home_stats['points_std']**2 + 
            away_stats['points_std']**2
        )
        total_std = np.sqrt(total_variance)
        
        logger.info(f"Matchup {home} vs {away}: Total={total_mean:.1f}±{total_std:.1f}")
        
        return total_mean, total_std
    
    def calculate_spread_probabilities(
        self,
        home: str,
        away: str,
        league: str,
        spread_line: float,
        last_n_games: int = 10
    ) -> Dict[str, float]:
        """
        Calcula probabilidades para el spread
        
        Args:
            home: Equipo local
            away: Equipo visitante
            league: Liga
            spread_line: Línea del spread (ej: -5.5)
            last_n_games: Partidos a analizar
        
        Returns:
            {
                "home_cover": 0.55,  # Probabilidad de que local cubra
                "away_cover": 0.45,
                "expected_margin": -3.2  # Margen esperado (negativo = local gana)
            }
        """
        home_stats = self.get_team_stats(home, league, last_n_games)
        away_stats = self.get_team_stats(away, league, last_n_games)
        
        # Calcular margen esperado
        home_expected = (
            home_stats['points_mean'] * 0.6 +
            away_stats['opponent_points_mean'] * 0.4
        )
        away_expected = (
            away_stats['points_mean'] * 0.6 +
            home_stats['opponent_points_mean'] * 0.4
        )
        
        expected_margin = home_expected - away_expected
        
        # Desviación estándar del margen
        margin_std = np.sqrt(
            home_stats['points_std']**2 +
            away_stats['points_std']**2
        )
        
        # Calcular probabilidad usando distribución normal
        from scipy.stats import norm
        
        # Probabilidad de que el margen real sea mayor que el spread
        # (es decir, que el local cubra)
        prob_home_cover = 1 - norm.cdf(spread_line, loc=expected_margin, scale=margin_std)
        prob_away_cover = 1 - prob_home_cover
        
        return {
            "home_cover": prob_home_cover,
            "away_cover": prob_away_cover,
            "expected_margin": expected_margin,
            "margin_std": margin_std
        }
    
    def get_recent_form(
        self,
        team: str,
        league: str,
        last_n_games: int = 5
    ) -> Dict:
        """
        Obtiene forma reciente del equipo
        
        Returns:
            {
                "wins": 4,
                "losses": 1,
                "win_rate": 0.80,
                "avg_points": 115.2,
                "avg_points_allowed": 108.5,
                "trend": "WINNING_STREAK" | "LOSING_STREAK" | "MIXED"
            }
        """
        if not self.db:
            return {"trend": "UNKNOWN"}
        
        try:
            sql = text("""
                SELECT 
                    home_team, away_team, home_score, away_score,
                    (home_team = :team) as is_home,
                    CASE 
                        WHEN home_team = :team AND home_score > away_score THEN 1
                        WHEN away_team = :team AND away_score > home_score THEN 1
                        ELSE 0
                    END as won
                FROM game_results
                WHERE (home_team = :team OR away_team = :team)
                  AND league = :league
                  AND game_date >= NOW() - INTERVAL '30 days'
                ORDER BY game_date DESC
                LIMIT :limit
            """)
            
            results = self.db.execute(sql, {
                "team": team,
                "league": league,
                "limit": last_n_games
            }).fetchall()
            
            if not results:
                return {"trend": "UNKNOWN"}
            
            wins = sum(r['won'] for r in results)
            losses = len(results) - wins
            
            # Calcular promedios
            points = []
            points_allowed = []
            for r in results:
                if r['is_home']:
                    points.append(r['home_score'])
                    points_allowed.append(r['away_score'])
                else:
                    points.append(r['away_score'])
                    points_allowed.append(r['home_score'])
            
            # Determinar tendencia
            if wins >= 4:
                trend = "WINNING_STREAK"
            elif losses >= 4:
                trend = "LOSING_STREAK"
            else:
                trend = "MIXED"
            
            return {
                "wins": wins,
                "losses": losses,
                "win_rate": wins / len(results),
                "avg_points": float(np.mean(points)),
                "avg_points_allowed": float(np.mean(points_allowed)),
                "trend": trend,
                "games_analyzed": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error getting form for {team}: {e}")
            return {"trend": "UNKNOWN"}
    
    def _get_default_stats(self, league: str, team: str) -> Dict:
        """Retorna estadísticas por defecto"""
        defaults = self.DEFAULT_STATS.get(league, self.DEFAULT_STATS["NBA"])
        
        return {
            **defaults,
            "games_analyzed": 0,
            "last_updated": datetime.utcnow(),
            "data_quality": "DEFAULT",
            "team": team,
            "league": league
        }
    
    def _assess_data_quality(self, games_found: int, games_requested: int) -> str:
        """Evalúa calidad de los datos"""
        ratio = games_found / games_requested
        
        if ratio >= 0.8:
            return "HIGH"
        elif ratio >= 0.5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def clear_cache(self):
        """Limpia el cache de estadísticas"""
        self._cache = {}
        logger.info("Stats cache cleared")


# Funciones de utilidad
def create_team_stats_table(db_session):
    """
    Crea tabla para almacenar estadísticas pre-calculadas
    
    Esto permite cachear estadísticas y no recalcular cada vez
    """
    sql = text("""
        CREATE TABLE IF NOT EXISTS team_stats (
            id SERIAL PRIMARY KEY,
            team VARCHAR(200) NOT NULL,
            league VARCHAR(100) NOT NULL,
            season VARCHAR(20),
            points_mean DECIMAL(10,2),
            points_std DECIMAL(10,2),
            opponent_points_mean DECIMAL(10,2),
            opponent_points_std DECIMAL(10,2),
            total_mean DECIMAL(10,2),
            total_std DECIMAL(10,2),
            games_analyzed INT,
            last_updated TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(team, league, season)
        );
        
        CREATE INDEX IF NOT EXISTS idx_team_stats_lookup 
        ON team_stats(team, league);
    """)
    
    db_session.execute(sql)
    db_session.commit()
    logger.info("team_stats table created")


# Ejemplo de uso
if __name__ == "__main__":
    print("=" * 80)
    print("MOTOR DE ESTADÍSTICAS DE BASKETBALL")
    print("=" * 80)
    
    # Crear engine sin BD (usará valores por defecto)
    engine = BasketballStatsEngine()
    
    # Ejemplo 1: Stats de un equipo
    print("\n1. Estadísticas de Lakers:")
    stats = engine.get_team_stats("Lakers", "NBA")
    print(f"   Puntos: {stats['points_mean']:.1f} ± {stats['points_std']:.1f}")
    print(f"   Total: {stats['total_mean']:.1f} ± {stats['total_std']:.1f}")
    print(f"   Calidad: {stats['data_quality']}")
    
    # Ejemplo 2: Total esperado de un partido
    print("\n2. Total esperado Lakers vs Celtics:")
    mean, std = engine.calculate_matchup_total("Lakers", "Celtics", "NBA")
    print(f"   Total: {mean:.1f} ± {std:.1f}")
    
    # Ejemplo 3: Probabilidades de spread
    print("\n3. Probabilidades de spread Lakers -5.5:")
    probs = engine.calculate_spread_probabilities("Lakers", "Celtics", "NBA", -5.5)
    print(f"   Lakers cubren: {probs['home_cover']*100:.1f}%")
    print(f"   Celtics cubren: {probs['away_cover']*100:.1f}%")
    print(f"   Margen esperado: {probs['expected_margin']:.1f}")
