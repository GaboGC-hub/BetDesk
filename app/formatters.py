# app/formatters.py
"""
Formateadores de mensajes para alertas de Telegram
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BOGOTA_TZ = ZoneInfo("America/Bogota")

def _format_start_time(start_time_utc) -> str:
    """
    Formatea la hora de inicio del partido en zona horaria de Bogotá
    
    Args:
        start_time_utc: datetime en UTC o None
        
    Returns:
        String formateado "DD/MM HH:MM" o vacío si no hay hora
    """
    if not start_time_utc:
        return ""
    
    if isinstance(start_time_utc, datetime):
        # Convertir a hora de Bogotá
        bogota_time = start_time_utc.astimezone(BOGOTA_TZ)
        return bogota_time.strftime("%d/%m %H:%M")
    
    return ""

def format_alert_football_anomaly(row: dict, z_score: float) -> str:
    """
    Formatea alerta de anomalía para fútbol
    """
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "1X2": "⚽",
        "TOTAL": "🎯",
        "BTTS": "🔥",
        "SPREAD": "📊"
    }.get(market, "📈")
    
    # Formatear selección
    selection_text = {
        "HOME": f"🏠 {home}",
        "AWAY": f"✈️ {away}",
        "DRAW": "🤝 Empate",
        "OVER": f"Over {line}",
        "UNDER": f"Under {line}",
        "YES": "Sí",
        "NO": "No"
    }.get(selection, selection)
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>ANOMALÍA - FÚTBOL</b>\n"
        f"🏆 {league}\n"
        f"⚽ {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"📈 Z-score: <b>{abs(z_score):.2f}</b>\n"
    )
    
    return msg


def format_alert_football_ev(row: dict, ev: float, prob: float = None) -> str:
    """
    Formatea alerta de EV positivo para fútbol
    """
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "1X2": "⚽",
        "TOTAL": "🎯",
        "BTTS": "🔥"
    }.get(market, "💰")
    
    # Formatear selección
    selection_text = {
        "HOME": f"🏠 {home}",
        "AWAY": f"✈️ {away}",
        "DRAW": "🤝 Empate",
        "OVER": f"Over {line}",
        "UNDER": f"Under {line}",
        "YES": "Sí",
        "NO": "No"
    }.get(selection, selection)
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>EV+ FÚTBOL</b>\n"
        f"🏆 {league}\n"
        f"⚽ {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"💰 EV: <b>{ev*100:.1f}%</b>\n"
    )
    
    if prob:
        msg += f"📊 Prob: {prob*100:.1f}%\n"
    
    return msg


def format_alert_tennis_anomaly(row: dict, z_score: float) -> str:
    """
    Formatea alerta de anomalía para tenis
    """
    home = row.get('home', 'Player 1')
    away = row.get('away', 'Player 2')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "MONEYLINE": "🎾",
        "TOTAL_GAMES": "🎯",
        "HANDICAP_SETS": "📊"
    }.get(market, "📈")
    
    # Formatear selección
    if market == "MONEYLINE":
        selection_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    elif market == "TOTAL_GAMES":
        selection_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "HANDICAP_SETS":
        selection_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    else:
        selection_text = selection
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>ANOMALÍA - TENIS</b>\n"
        f"🏆 {league}\n"
        f"🎾 {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"📈 Z-score: <b>{abs(z_score):.2f}</b>\n"
    )
    
    return msg


def format_alert_tennis_ev(row: dict, ev: float, prob: float = None) -> str:
    """
    Formatea alerta de EV positivo para tenis
    """
    home = row.get('home', 'Player 1')
    away = row.get('away', 'Player 2')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "MONEYLINE": "🎾",
        "TOTAL_GAMES": "🎯",
        "HANDICAP_SETS": "📊"
    }.get(market, "💰")
    
    # Formatear selección
    if market == "MONEYLINE":
        selection_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    elif market == "TOTAL_GAMES":
        selection_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "HANDICAP_SETS":
        selection_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    else:
        selection_text = selection
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>EV+ TENIS</b>\n"
        f"🏆 {league}\n"
        f"🎾 {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"💰 EV: <b>{ev*100:.1f}%</b>\n"
    )
    
    if prob:
        msg += f"📊 Prob: {prob*100:.1f}%\n"
    
    return msg


def format_alert_basketball_anomaly(row: dict, z_score: float) -> str:
    """
    Formatea alerta de anomalía para baloncesto (mejorada)
    
    Args:
        row: Dict con datos de la odd
        z_score: Z-score de la anomalía
        
    Returns:
        Mensaje formateado en HTML para Telegram
    """
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "TOTAL": "🎯",
        "SPREAD": "📊",
        "MONEYLINE": "🏀"
    }.get(market, "📈")
    
    # Formatear selección
    if market == "TOTAL":
        selection_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "SPREAD":
        selection_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    elif market == "MONEYLINE":
        selection_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    else:
        selection_text = selection
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>ANOMALÍA - BALONCESTO</b>\n"
        f"🏆 {league}\n"
        f"🏀 {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"📈 Z-score: <b>{abs(z_score):.2f}</b>\n"
    )
    
    return msg


def format_alert_basketball_ev(row: dict, ev: float, prob: float = None) -> str:
    """
    Formatea alerta de EV positivo para baloncesto (mejorada)
    """
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    start_time = row.get('start_time_utc')
    
    # Emoji por mercado
    market_emoji = {
        "TOTAL": "🎯",
        "SPREAD": "📊",
        "MONEYLINE": "🏀"
    }.get(market, "💰")
    
    # Formatear selección
    if market == "TOTAL":
        selection_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "SPREAD":
        selection_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    elif market == "MONEYLINE":
        selection_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    else:
        selection_text = selection
    
    # Formatear hora de inicio
    time_str = _format_start_time(start_time)
    time_line = f"🕐 {time_str}\n" if time_str else ""
    
    msg = (
        f"{market_emoji} <b>EV+ BALONCESTO</b>\n"
        f"🏆 {league}\n"
        f"🏀 {home} vs {away}\n"
        f"{time_line}"
        f"📊 Mercado: {market}\n"
        f"🎲 {selection_text} @ <b>{odds}</b>\n"
        f"🏪 {bookmaker}\n"
        f"💰 EV: <b>{ev*100:.1f}%</b>\n"
    )
    
    if prob:
        msg += f"📊 Prob: {prob*100:.1f}%\n"
    
    return msg
