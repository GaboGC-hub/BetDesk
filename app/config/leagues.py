# app/config/leagues.py
"""
Definición de ligas soportadas y sus metadatos
"""

SUPPORTED_LEAGUES = {
    # ==================== BALONCESTO ====================
    "basketball": {
        "NBA": {
            "name": "NBA",
            "full_name": "National Basketball Association",
            "country": "USA",
            "priority": 1,  # Prioridad alta
            "flashscore_id": "nba",
            "markets": ["TOTAL", "SPREAD", "MONEYLINE"],
        },
        "CBA": {
            "name": "CBA",
            "full_name": "Chinese Basketball Association",
            "country": "China",
            "priority": 2,
            "flashscore_id": "cba",
            "markets": ["TOTAL", "SPREAD", "MONEYLINE"],
        },
        "Euroleague": {
            "name": "Euroleague",
            "full_name": "Turkish Airlines EuroLeague",
            "country": "Europe",
            "priority": 1,
            "flashscore_id": "euroleague",
            "markets": ["TOTAL", "SPREAD", "MONEYLINE"],
        },
    },
    
    # ==================== FÚTBOL ====================
    "football": {
        "Premier League": {
            "name": "Premier League",
            "full_name": "Premier League",
            "country": "England",
            "priority": 1,
            "flashscore_id": "premier-league",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "La Liga": {
            "name": "La Liga",
            "full_name": "LaLiga Santander",
            "country": "Spain",
            "priority": 1,
            "flashscore_id": "laliga",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "Serie A": {
            "name": "Serie A",
            "full_name": "Serie A TIM",
            "country": "Italy",
            "priority": 1,
            "flashscore_id": "serie-a",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "Bundesliga": {
            "name": "Bundesliga",
            "full_name": "Bundesliga",
            "country": "Germany",
            "priority": 1,
            "flashscore_id": "bundesliga",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "Ligue 1": {
            "name": "Ligue 1",
            "full_name": "Ligue 1 Uber Eats",
            "country": "France",
            "priority": 1,
            "flashscore_id": "ligue-1",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "Champions League": {
            "name": "Champions League",
            "full_name": "UEFA Champions League",
            "country": "Europe",
            "priority": 1,
            "flashscore_id": "champions-league",
            "markets": ["1X2", "TOTAL", "BTTS", "HANDICAP"],
        },
        "Copa Libertadores": {
            "name": "Copa Libertadores",
            "full_name": "Copa Libertadores",
            "country": "South America",
            "priority": 2,
            "flashscore_id": "copa-libertadores",
            "markets": ["1X2", "TOTAL", "BTTS"],
        },
        "Liga Colombiana": {
            "name": "Liga Colombiana",
            "full_name": "Liga BetPlay Dimayor",
            "country": "Colombia",
            "priority": 2,
            "flashscore_id": "liga-betplay",
            "markets": ["1X2", "TOTAL", "BTTS"],
        },
    },
    
    # ==================== TENIS ====================
    "tennis": {
        "ATP": {
            "name": "ATP",
            "full_name": "ATP Tour",
            "country": "International",
            "priority": 1,
            "flashscore_id": "atp",
            "markets": ["MONEYLINE", "TOTAL_GAMES", "HANDICAP_SETS"],
        },
        "WTA": {
            "name": "WTA",
            "full_name": "WTA Tour",
            "country": "International",
            "priority": 1,
            "flashscore_id": "wta",
            "markets": ["MONEYLINE", "TOTAL_GAMES", "HANDICAP_SETS"],
        },
        "Grand Slam": {
            "name": "Grand Slam",
            "full_name": "Grand Slam Tournaments",
            "country": "International",
            "priority": 1,
            "flashscore_id": "grand-slam",
            "markets": ["MONEYLINE", "TOTAL_GAMES", "HANDICAP_SETS", "SET_EXACT"],
        },
        "ATP Masters 1000": {
            "name": "ATP Masters 1000",
            "full_name": "ATP Masters 1000",
            "country": "International",
            "priority": 1,
            "flashscore_id": "atp-masters-1000",
            "markets": ["MONEYLINE", "TOTAL_GAMES", "HANDICAP_SETS"],
        },
        "WTA 1000": {
            "name": "WTA 1000",
            "full_name": "WTA 1000",
            "country": "International",
            "priority": 1,
            "flashscore_id": "wta-1000",
            "markets": ["MONEYLINE", "TOTAL_GAMES", "HANDICAP_SETS"],
        },
    },
}


def get_league_info(sport: str, league: str) -> dict:
    """
    Obtiene información de una liga específica
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
    
    Returns:
        dict: Información de la liga
    
    Raises:
        ValueError: Si el deporte/liga no existe
    """
    if sport not in SUPPORTED_LEAGUES:
        raise ValueError(f"Deporte no soportado: {sport}")
    
    if league not in SUPPORTED_LEAGUES[sport]:
        raise ValueError(f"Liga no soportada: {league} para {sport}")
    
    return SUPPORTED_LEAGUES[sport][league]


def get_leagues_by_sport(sport: str) -> list[str]:
    """
    Obtiene lista de ligas para un deporte
    
    Args:
        sport: "basketball", "football", "tennis"
    
    Returns:
        list: Lista de nombres de ligas
    """
    if sport not in SUPPORTED_LEAGUES:
        return []
    
    return list(SUPPORTED_LEAGUES[sport].keys())


def get_leagues_by_priority(sport: str, priority: int = 1) -> list[str]:
    """
    Obtiene ligas filtradas por prioridad
    
    Args:
        sport: "basketball", "football", "tennis"
        priority: Nivel de prioridad (1 = alta, 2 = media, 3 = baja)
    
    Returns:
        list: Lista de nombres de ligas con esa prioridad
    """
    if sport not in SUPPORTED_LEAGUES:
        return []
    
    return [
        league_name
        for league_name, league_info in SUPPORTED_LEAGUES[sport].items()
        if league_info.get("priority", 3) == priority
    ]


def get_supported_markets(sport: str, league: str) -> list[str]:
    """
    Obtiene mercados soportados para una liga
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
    
    Returns:
        list: Lista de mercados soportados
    """
    try:
        league_info = get_league_info(sport, league)
        return league_info.get("markets", [])
    except ValueError:
        return []


def is_market_supported(sport: str, league: str, market: str) -> bool:
    """
    Verifica si un mercado está soportado para una liga
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
        market: Nombre del mercado
    
    Returns:
        bool: True si está soportado
    """
    supported = get_supported_markets(sport, league)
    return market.upper() in [m.upper() for m in supported]


def get_all_sports() -> list[str]:
    """
    Obtiene lista de todos los deportes soportados
    
    Returns:
        list: Lista de deportes
    """
    return list(SUPPORTED_LEAGUES.keys())


def get_flashscore_id(sport: str, league: str) -> str:
    """
    Obtiene el ID de Flashscore para una liga
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
    
    Returns:
        str: ID de Flashscore
    """
    try:
        league_info = get_league_info(sport, league)
        return league_info.get("flashscore_id", "")
    except ValueError:
        return ""
