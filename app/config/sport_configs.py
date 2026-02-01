# app/config/sport_configs.py
"""
Configuración de parámetros estadísticos por deporte y liga
Estos valores son baselines iniciales que pueden ser refinados con datos históricos
"""

SPORT_CONFIGS = {
    # ==================== BALONCESTO ====================
    "basketball": {
        "NBA": {
            "total": {
                "mu": 228.0,           # Media de puntos totales
                "sigma": 12.0,         # Desviación estándar
                "ev_min": 0.02,        # EV mínimo para alerta (2%)
            },
            "spread": {
                "sigma": 8.0,          # Desviación estándar del margen
                "ev_min": 0.02,
            },
            "moneyline": {
                "ev_min": 0.03,
            },
        },
        "CBA": {
            "total": {
                "mu": 210.0,
                "sigma": 14.0,
                "ev_min": 0.04,        # Mayor umbral por menor liquidez
            },
            "spread": {
                "sigma": 10.0,
                "ev_min": 0.04,
            },
            "moneyline": {
                "ev_min": 0.05,
            },
        },
        "Euroleague": {
            "total": {
                "mu": 165.0,
                "sigma": 10.0,
                "ev_min": 0.03,
            },
            "spread": {
                "sigma": 7.0,
                "ev_min": 0.03,
            },
            "moneyline": {
                "ev_min": 0.04,
            },
        },
    },
    
    # ==================== FÚTBOL ====================
    "football": {
        "Premier League": {
            "goals": {
                "lambda_home": 1.5,    # Goles esperados local
                "lambda_away": 1.2,    # Goles esperados visitante
                "ev_min": 0.03,
            },
            "1x2": {
                "ev_min": 0.04,        # Mayor umbral por 3 resultados
            },
            "btts": {
                "prob_baseline": 0.52, # Probabilidad base ambos anotan
                "ev_min": 0.03,
            },
        },
        "La Liga": {
            "goals": {
                "lambda_home": 1.4,
                "lambda_away": 1.1,
                "ev_min": 0.03,
            },
            "1x2": {
                "ev_min": 0.04,
            },
            "btts": {
                "prob_baseline": 0.48,
                "ev_min": 0.03,
            },
        },
        "Serie A": {
            "goals": {
                "lambda_home": 1.3,
                "lambda_away": 1.0,
                "ev_min": 0.03,
            },
            "1x2": {
                "ev_min": 0.04,
            },
            "btts": {
                "prob_baseline": 0.45,
                "ev_min": 0.03,
            },
        },
        "Bundesliga": {
            "goals": {
                "lambda_home": 1.6,
                "lambda_away": 1.4,
                "ev_min": 0.03,
            },
            "1x2": {
                "ev_min": 0.04,
            },
            "btts": {
                "prob_baseline": 0.55,
                "ev_min": 0.03,
            },
        },
        "Ligue 1": {
            "goals": {
                "lambda_home": 1.4,
                "lambda_away": 1.2,
                "ev_min": 0.03,
            },
            "1x2": {
                "ev_min": 0.04,
            },
            "btts": {
                "prob_baseline": 0.50,
                "ev_min": 0.03,
            },
        },
        "Champions League": {
            "goals": {
                "lambda_home": 1.6,
                "lambda_away": 1.4,
                "ev_min": 0.04,        # Mayor umbral por importancia
            },
            "1x2": {
                "ev_min": 0.05,
            },
            "btts": {
                "prob_baseline": 0.53,
                "ev_min": 0.04,
            },
        },
        "Copa Libertadores": {
            "goals": {
                "lambda_home": 1.5,
                "lambda_away": 1.1,
                "ev_min": 0.04,
            },
            "1x2": {
                "ev_min": 0.05,
            },
            "btts": {
                "prob_baseline": 0.48,
                "ev_min": 0.04,
            },
        },
        "Liga Colombiana": {
            "goals": {
                "lambda_home": 1.3,
                "lambda_away": 0.9,
                "ev_min": 0.05,        # Mayor umbral por menor liquidez
            },
            "1x2": {
                "ev_min": 0.06,
            },
            "btts": {
                "prob_baseline": 0.42,
                "ev_min": 0.05,
            },
        },
    },
    
    # ==================== TENIS ====================
    "tennis": {
        "ATP": {
            "games": {
                "mu": 22.5,            # Media de games totales
                "sigma": 4.0,          # Desviación estándar
                "ev_min": 0.04,
            },
            "moneyline": {
                "ev_min": 0.03,
            },
            "sets": {
                "ev_min": 0.04,
            },
        },
        "WTA": {
            "games": {
                "mu": 20.0,
                "sigma": 3.5,
                "ev_min": 0.04,
            },
            "moneyline": {
                "ev_min": 0.03,
            },
            "sets": {
                "ev_min": 0.04,
            },
        },
        "Grand Slam": {
            "games": {
                "mu": 35.0,            # Más games por formato al mejor de 5
                "sigma": 8.0,
                "ev_min": 0.05,
            },
            "moneyline": {
                "ev_min": 0.04,
            },
            "sets": {
                "ev_min": 0.05,
            },
        },
        "ATP Masters 1000": {
            "games": {
                "mu": 23.0,
                "sigma": 4.2,
                "ev_min": 0.04,
            },
            "moneyline": {
                "ev_min": 0.03,
            },
            "sets": {
                "ev_min": 0.04,
            },
        },
        "WTA 1000": {
            "games": {
                "mu": 20.5,
                "sigma": 3.8,
                "ev_min": 0.04,
            },
            "moneyline": {
                "ev_min": 0.03,
            },
            "sets": {
                "ev_min": 0.04,
            },
        },
    },
}


def get_sport_config(sport: str, league: str, market: str = None) -> dict:
    """
    Obtiene la configuración para un deporte/liga/mercado específico
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga (ej. "NBA", "Premier League", "ATP")
        market: Mercado específico (ej. "total", "1x2", "moneyline")
    
    Returns:
        dict: Configuración con parámetros estadísticos
    
    Raises:
        ValueError: Si el deporte/liga no está configurado
    """
    if sport not in SPORT_CONFIGS:
        raise ValueError(f"Deporte no configurado: {sport}")
    
    if league not in SPORT_CONFIGS[sport]:
        raise ValueError(f"Liga no configurada: {league} para {sport}")
    
    league_config = SPORT_CONFIGS[sport][league]
    
    if market is None:
        return league_config
    
    # Normalizar nombre del mercado
    market_normalized = market.lower().replace("_", "").replace("-", "")
    
    # Buscar el mercado en la configuración
    for key, value in league_config.items():
        if key.lower().replace("_", "").replace("-", "") == market_normalized:
            return value
    
    raise ValueError(f"Mercado no configurado: {market} para {league}")


def get_ev_threshold(sport: str, league: str, market: str) -> float:
    """
    Obtiene el umbral de EV mínimo para generar alerta
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
        market: Mercado específico
    
    Returns:
        float: Umbral de EV (ej. 0.03 = 3%)
    """
    try:
        config = get_sport_config(sport, league, market)
        return config.get("ev_min", 0.03)  # Default 3%
    except ValueError:
        return 0.03  # Default si no está configurado


def get_anomaly_threshold(sport: str, league: str) -> float:
    """
    Obtiene el umbral de z-score para detección de anomalías
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
    
    Returns:
        float: Umbral de z-score (ej. 1.5)
    """
    # Umbrales por deporte (pueden refinarse por liga)
    thresholds = {
        "basketball": 1.2,  # Más sensible (mercado más líquido)
        "football": 1.5,    # Moderado
        "tennis": 1.8,      # Menos sensible (más volatilidad)
    }
    
    return thresholds.get(sport, 1.5)  # Default 1.5


def get_min_bookmakers(sport: str, league: str) -> int:
    """
    Obtiene el número mínimo de bookmakers para análisis
    
    Args:
        sport: "basketball", "football", "tennis"
        league: Nombre de la liga
    
    Returns:
        int: Número mínimo de bookmakers
    """
    # Ligas principales requieren más bookmakers
    major_leagues = [
        "NBA", "Premier League", "La Liga", "Serie A", 
        "Bundesliga", "Champions League", "ATP", "WTA"
    ]
    
    if league in major_leagues:
        return 3
    else:
        return 2  # Ligas menores pueden tener menos cobertura
