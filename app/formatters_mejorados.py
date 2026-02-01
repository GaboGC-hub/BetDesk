# app/formatters_mejorados.py
"""
Formateadores mejorados de mensajes para alertas de Telegram
"""

def format_basketball_anomaly_mejorado(row: dict, z_score: float) -> str:
    """Formato mejorado para anomalías de basketball"""
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    
    # Formatear selección
    if market == "TOTAL":
        sel_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "SPREAD":
        sel_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    else:
        sel_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    
    return (
        f"🚨 <b>ANOMALÍA DETECTADA</b> 🚨\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏀 <b>{league}</b>\n"
        f"⚔️ {home} vs {away}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Mercado:</b> {market}\n"
        f"🎯 <b>Apuesta:</b> {sel_text}\n"
        f"💰 <b>Cuota:</b> {odds}\n"
        f"🏪 <b>Casa:</b> {bookmaker}\n"
        f"📈 <b>Z-score:</b> {abs(z_score):.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>Cuota significativamente diferente</i>"
    )


def format_basketball_ev_mejorado(row: dict, ev: float, prob: float = None) -> str:
    """Formato mejorado para EV+ de basketball"""
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    
    # Formatear selección
    if market == "TOTAL":
        sel_text = f"Over {line}" if selection == "OVER" else f"Under {line}"
    elif market == "SPREAD":
        sel_text = f"{home} ({line:+.1f})" if selection == "HOME" else f"{away} ({-line:+.1f})"
    else:
        sel_text = f"🏆 {home}" if selection == "HOME" else f"🏆 {away}"
    
    msg = (
        f"💎 <b>VALOR ESPERADO POSITIVO</b> 💎\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🏀 <b>{league}</b>\n"
        f"⚔️ {home} vs {away}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Mercado:</b> {market}\n"
        f"🎯 <b>Apuesta:</b> {sel_text}\n"
        f"💰 <b>Cuota:</b> {odds}\n"
        f"🏪 <b>Casa:</b> {bookmaker}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 <b>EV:</b> {ev*100:.1f}%\n"
    )
    
    if prob:
        msg += f"🎲 <b>Probabilidad:</b> {prob*100:.1f}%\n"
    
    msg += (
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ <i>Oportunidad de valor matemático</i>"
    )
    
    return msg
