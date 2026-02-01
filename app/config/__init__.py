# app/config/__init__.py
"""
Configuración centralizada para el sistema BetDesk
"""

from .sport_configs import SPORT_CONFIGS, get_sport_config, get_ev_threshold, get_anomaly_threshold, get_min_bookmakers
from .leagues import SUPPORTED_LEAGUES, get_league_info, get_leagues_by_sport, get_supported_markets, is_market_supported

__all__ = [
    "SPORT_CONFIGS",
    "get_sport_config",
    "get_ev_threshold",
    "get_anomaly_threshold",
    "get_min_bookmakers",
    "SUPPORTED_LEAGUES",
    "get_league_info",
    "get_leagues_by_sport",
    "get_supported_markets",
    "is_market_supported",
]
