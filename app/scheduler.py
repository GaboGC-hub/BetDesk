# app/scheduler.py
"""
Scheduler mejorado con integración completa de:
- Desvigado
- Filtros de calidad
- Clasificación de picks
- Detección de errores
- Estadísticas dinámicas
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict

from apscheduler.schedulers.background import BackgroundScheduler

from .telegram import send_telegram
from .crud import (
    upsert_event, insert_odds,
    fetch_latest_odds_snapshot,
    create_alert_from_anomaly,
    create_alert_ev,
    mark_sent
)
from .decision.anomaly import detect_anomalies
from .decision.ev import (
    calculate_basketball_total_ev,
    calculate_basketball_spread_ev,
    should_bet,
    expected_value
)
from .decision.devig import devig_market
from .decision.quality_filters import QualityFilter
from .decision.pick_classifier import PickClassifier
from .decision.error_detection import OddsErrorDetector, format_error_alert
from .decision.basketball_stats import BasketballStatsEngine
from .decision.robust_stats import RobustStatsEngine
from .decision.football_models import (
    poisson_match_probabilities,
    prob_over_goals_poisson,
    prob_btts
)
from .decision.tennis_models import (
    elo_win_probability,
    prob_over_games
)
from .config import get_sport_config, get_ev_threshold, get_anomaly_threshold, get_min_bookmakers
from .formatters import (
    format_alert_football_anomaly,
    format_alert_football_ev,
    format_alert_tennis_anomaly,
    format_alert_tennis_ev,
    format_alert_basketball_anomaly,
    format_alert_basketball_ev
)
# Importar funciones de scraping real con fallback a mock
from .ingest.provider_flashscore import (
    upcoming_basketball_events,
    upcoming_football_events,
    upcoming_tennis_events,
    odds_for_event
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("betdesk")

# Inicializar engines globales
stats_engine = BasketballStatsEngine()
robust_stats_engine = RobustStatsEngine()

def job_ingest_mock():
    """Ingesta de eventos de basketball (intenta scraping real, fallback a mock)"""
    try:
        # Intenta obtener eventos reales, si falla usa mock automáticamente
        events = upcoming_basketball_events()
        for e in events:
            event_id = upsert_event(e)
            rows = odds_for_event(e["flashscore_url"])
            insert_odds(event_id, rows)
        logger.info(f"✅ Basketball ingest OK. Events: {len(events)}")
    except Exception:
        logger.exception("❌ Basketball ingest FAILED")

def job_anomalies():
    try:
        rows = fetch_latest_odds_snapshot(minutes=60, sport="basketball")
        hits = detect_anomalies(rows, z_threshold=1.2, min_books=2)
        logger.info(f"Basketball anomalies scan OK. rows={len(rows)} hits={len(hits)}")

        for row, z in hits:
            alert_id = create_alert_from_anomaly(row, score=abs(z))
            if alert_id:
                msg = format_alert_basketball_anomaly(row, z)
                send_telegram(msg)
                mark_sent(alert_id)
    except Exception:
        logger.exception("Basketball anomalies FAILED")

def start_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")
    now = datetime.now(timezone.utc)

    # ========== BALONCESTO ==========
    sched.add_job(job_ingest_mock, "interval", minutes=10, next_run_time=now, id="ingest_basketball")
    sched.add_job(job_anomalies, "interval", minutes=2, next_run_time=now, id="anomalies_basketball")
    sched.add_job(job_ev_baseline, "interval", minutes=2, next_run_time=now, id="ev_basketball")
    
    # ========== FÚTBOL ==========
    sched.add_job(job_ingest_mock_football, "interval", minutes=15, next_run_time=now, id="ingest_football")
    sched.add_job(job_anomalies_football, "interval", minutes=3, next_run_time=now, id="anomalies_football")
    sched.add_job(job_ev_football, "interval", minutes=5, next_run_time=now, id="ev_football")
    
    # ========== TENIS ==========
    sched.add_job(job_ingest_mock_tennis, "interval", minutes=20, next_run_time=now, id="ingest_tennis")
    sched.add_job(job_anomalies_tennis, "interval", minutes=3, next_run_time=now, id="anomalies_tennis")
    sched.add_job(job_ev_tennis, "interval", minutes=5, next_run_time=now, id="ev_tennis")
    
    # ========== UTILIDADES ==========
    sched.add_job(job_flashscore_smoke, "interval", minutes=60, next_run_time=now, id="flashscore_smoke")

    sched.start()
    logger.info("✅ Scheduler started with 10 jobs (3 sports)")
    logger.info("   🏀 Basketball: 3 jobs")
    logger.info("   ⚽ Football: 3 jobs")
    logger.info("   🎾 Tennis: 3 jobs")
    logger.info("   🔧 Utils: 1 job")
    return sched

def job_ev_baseline():
    """
    Job mejorado de EV para basketball con:
    - Detección de errores de cuota (prioridad máxima)
    - Desvigado
    - Estadísticas dinámicas por equipo
    - Filtros de calidad
    - Clasificación de picks
    """
    try:
        rows = fetch_latest_odds_snapshot(minutes=60, sport="basketball")
        
        if not rows:
            logger.info("Basketball EV: No odds found")
            return
        
        # PASO 1: Detectar errores de cuota (prioridad máxima)
        errors = OddsErrorDetector.scan_all_odds(rows)
        
        for error_odd in errors:
            error_detection = error_odd["error_detection"]
            
            if error_detection["action"] == "BET_IMMEDIATELY":
                # Alerta inmediata de error
                msg = format_error_alert(error_odd, error_detection)
                send_telegram(msg)
                logger.warning(f"🚨 ERROR DE CUOTA detectado: {error_odd.get('event', 'Unknown')}")
        
        # PASO 2: Procesar odds normales con sistema mejorado
        processed = 0
        alerts_sent = 0
        
        for r in rows:
            # Solo basketball
            if r["league"] not in ("NBA", "CBA"):
                continue
            
            market = r["market"]
            line = float(r["line"]) if r["line"] is not None else None
            selection = r["selection"]
            home = r.get("home", "")
            away = r.get("away", "")
            league = r["league"]
            
            # Solo procesar mercados TOTAL y SPREAD por ahora
            if market not in ("TOTAL", "SPREAD"):
                continue
            
            if line is None:
                continue
            
            processed += 1
            
            try:
                # Calcular EV con desvigado y estadísticas dinámicas
                if market == "TOTAL":
                    ev_result = calculate_basketball_total_ev(
                        home=home,
                        away=away,
                        league=league,
                        line=line,
                        selection=selection,
                        odd=r,
                        market_odds=rows,
                        stats_engine=stats_engine,
                        use_devig=True
                    )
                elif market == "SPREAD":
                    ev_result = calculate_basketball_spread_ev(
                        home=home,
                        away=away,
                        league=league,
                        spread_line=line,
                        selection=selection,
                        odd=r,
                        market_odds=rows,
                        stats_engine=stats_engine,
                        use_devig=True
                    )
                else:
                    continue
                
                # Verificar si vale la pena apostar
                should_bet_result, reason = should_bet(ev_result, min_ev=0.03, min_edge=0.02)
                
                if not should_bet_result:
                    continue
                
                # Aplicar filtros de calidad
                quality = QualityFilter.apply_all_filters(
                    odd=r,
                    odds_snapshot=rows,
                    historical_odds=None,  # TODO: Agregar histórico
                    min_quality_score=0.70
                )
                
                if not quality["passed"]:
                    logger.debug(f"Pick rejected by quality filters: {r.get('event', 'Unknown')}")
                    continue
                
                # Clasificar pick
                classification = PickClassifier.classify_pick(
                    ev=ev_result["ev"],
                    z_score=None,  # No tenemos z-score en este job
                    quality_score=quality["quality_score"],
                    model_confidence=0.75
                )
                
                # Solo alertar si la acción es BET_NOW o BET_SOON
                if classification["action"] not in ["BET_NOW", "BET_SOON"]:
                    continue
                
                # Crear alerta
                alert_id = create_alert_ev(r, ev=ev_result["ev"])
                
                if alert_id:
                    # Formatear mensaje mejorado
                    msg = _format_improved_basketball_alert(
                        r, ev_result, quality, classification
                    )
                    send_telegram(msg)
                    mark_sent(alert_id)
                    alerts_sent += 1
                    
                    logger.info(
                        f"✅ Basketball EV alert: {r.get('event', 'Unknown')} | "
                        f"EV={ev_result['ev_pct']:.1f}% | "
                        f"Quality={quality['quality_score']*100:.0f}% | "
                        f"Type={classification['type']}"
                    )
                    
            except Exception as e:
                logger.error(f"Error processing odd: {e}")
                continue
        
        logger.info(
            f"Basketball EV scan OK. "
            f"rows={len(rows)} processed={processed} alerts={alerts_sent} errors={len(errors)}"
        )
        
    except Exception:
        logger.exception("Basketball EV FAILED")


def _format_improved_basketball_alert(
    row: Dict,
    ev_result: Dict,
    quality: Dict,
    classification: Dict
) -> str:
    """
    Formatea alerta mejorada de basketball con toda la información
    """
    home = row.get('home', '')
    away = row.get('away', '')
    league = row['league']
    market = row['market']
    selection = row['selection']
    line = row.get('line')
    odds = row['odds']
    bookmaker = row['bookmaker']
    
    # Emoji según clasificación
    emoji = classification.get('emoji', '💰')
    
    # Formatear selección
    if market == "TOTAL":
        selection_text = f"{selection} {line}"
    elif market == "SPREAD":
        if selection == "HOME":
            selection_text = f"{home} ({line:+.1f})"
        else:
            selection_text = f"{away} ({-line:+.1f})"
    else:
        selection_text = selection
    
    msg = f"""
{emoji} <b>{classification['description']}</b>
🏀 {league}: {home} vs {away}

💰 <b>APUESTA:</b>
• {market} {selection_text}
• Cuota: {odds} @ {bookmaker}
• Cuota desvigada: {ev_result['devigged_odd']:.2f}
• EV: <b>+{ev_result['ev_pct']:.1f}%</b>
• Kelly: {classification['kelly_fraction']*100:.0f}%

⭐ <b>CLASIFICACIÓN:</b>
• Tipo: {classification['type']}
• Confianza: {classification['confidence']*100:.0f}%
• Acción: {classification['action']}

✅ <b>CALIDAD:</b>
• Score: {quality['quality_score']*100:.0f}%
• Liquidez: {quality['filters']['liquidity']['bookmaker_count']} bookmakers
• Recomendación: {quality['recommendation']}

📊 <b>MODELO:</b>
• Prob. modelo: {ev_result['model_prob']*100:.1f}%
• Prob. implícita: {ev_result['implied_prob']*100:.1f}%
• Edge: {ev_result['edge']*100:.1f}%
"""
    
    # Agregar parámetros del modelo si están disponibles
    if 'model_params' in ev_result:
        params = ev_result['model_params']
        if 'total_mean' in params:
            msg += f"• Total esperado: {params['total_mean']:.1f} ± {params['total_std']:.1f}\n"
    
    return msg.strip()
                
from .ingest.provider_flashscore import fetch_event_page_html

def job_flashscore_smoke():
    # Pega aquí una URL real de un partido NBA/CBA en Flashscore
    url = "https://www.flashscore.co/partido/baloncesto/philadelphia-76ers-vwRW2QSh/sacramento-kings-CvwE1OCB/?mid=CWqzG5JH"  # <-- TU URL
    html = fetch_event_page_html(url)
    # Confirmación simple: guardar tamaño del HTML en logs
    logger.info(f"Flashscore smoke OK. html_len={len(html)}")


# ============================================================================
# JOBS DE FÚTBOL
# ============================================================================

def job_ingest_mock_football():
    """Ingesta de eventos de football (intenta scraping real, fallback a mock)"""
    try:
        # Intenta obtener eventos reales, si falla usa mock automáticamente
        events = upcoming_football_events()
        for e in events:
            event_id = upsert_event(e)
            rows = odds_for_event(e["flashscore_url"])
            insert_odds(event_id, rows)
        logger.info(f"✅ Football ingest OK. Events: {len(events)}")
    except Exception:
        logger.exception("❌ Football ingest FAILED")


def job_anomalies_football():
    """Detecta anomalías en cuotas de fútbol"""
    try:
        rows = fetch_latest_odds_snapshot(minutes=30, sport="football")
        
        # Usar umbral por defecto para fútbol (1.5)
        z_threshold = 1.5
        min_books = 3
        
        hits = detect_anomalies(rows, z_threshold=z_threshold, min_books=min_books)
        logger.info(f"Football anomalies scan OK. rows={len(rows)} hits={len(hits)}")

        for row, z in hits:
            alert_id = create_alert_from_anomaly(row, score=abs(z))
            if alert_id:
                msg = format_alert_football_anomaly(row, z)
                send_telegram(msg)
                mark_sent(alert_id)
    except Exception:
        logger.exception("Football anomalies FAILED")


def job_ev_football():
    """Calcula EV para mercados de fútbol"""
    try:
        rows = fetch_latest_odds_snapshot(minutes=30, sport="football")
        
        for r in rows:
            league = r["league"]
            market = r["market"]
            odds = float(r["odds"])
            selection = r["selection"]
            line = float(r["line"]) if r["line"] is not None else None
            
            # Obtener configuración de la liga
            config = get_sport_config("football", league)
            if not config:
                continue
            
            ev_min = get_ev_threshold("football", league, market)
            p = None
            
            # Calcular probabilidad según el mercado
            if market == "1X2":
                lambda_home = config.get("lambda_home", 1.5)
                lambda_away = config.get("lambda_away", 1.2)
                
                probs = poisson_match_probabilities(lambda_home, lambda_away)
                
                if selection == "HOME":
                    p = probs["HOME"]
                elif selection == "DRAW":
                    p = probs["DRAW"]
                elif selection == "AWAY":
                    p = probs["AWAY"]
                    
            elif market == "TOTAL" and line is not None:
                lambda_home = config.get("lambda_home", 1.5)
                lambda_away = config.get("lambda_away", 1.2)
                
                if selection == "OVER":
                    p = prob_over_goals_poisson(lambda_home, lambda_away, line)
                elif selection == "UNDER":
                    p = 1.0 - prob_over_goals_poisson(lambda_home, lambda_away, line)
                    
            elif market == "BTTS":
                lambda_home = config.get("lambda_home", 1.5)
                lambda_away = config.get("lambda_away", 1.2)
                
                p_btts = prob_btts(lambda_home, lambda_away)
                
                if selection == "YES":
                    p = p_btts
                elif selection == "NO":
                    p = 1.0 - p_btts
            
            if p is None or p <= 0 or p >= 1:
                continue
            
            ev = expected_value(p, odds)
            if ev >= ev_min:
                alert_id = create_alert_ev(r, ev=ev)
                if alert_id:
                    msg = format_alert_football_ev(r, ev, p)
                    send_telegram(msg)
                    mark_sent(alert_id)
                    
        logger.info(f"Football EV scan OK. rows={len(rows)}")
    except Exception:
        logger.exception("Football EV FAILED")


# ============================================================================
# JOBS DE TENIS
# ============================================================================

def job_ingest_mock_tennis():
    """Ingesta de eventos de tennis (intenta scraping real, fallback a mock)"""
    try:
        # Intenta obtener eventos reales, si falla usa mock automáticamente
        events = upcoming_tennis_events()
        for e in events:
            event_id = upsert_event(e)
            rows = odds_for_event(e["flashscore_url"])
            insert_odds(event_id, rows)
        logger.info(f"✅ Tennis ingest OK. Events: {len(events)}")
    except Exception:
        logger.exception("❌ Tennis ingest FAILED")


def job_anomalies_tennis():
    """Detecta anomalías en cuotas de tenis"""
    try:
        rows = fetch_latest_odds_snapshot(minutes=30, sport="tennis")
        
        # Usar umbral por defecto para tenis (1.8)
        z_threshold = 1.8
        min_books = 3
        
        hits = detect_anomalies(rows, z_threshold=z_threshold, min_books=min_books)
        logger.info(f"Tennis anomalies scan OK. rows={len(rows)} hits={len(hits)}")

        for row, z in hits:
            alert_id = create_alert_from_anomaly(row, score=abs(z))
            if alert_id:
                msg = format_alert_tennis_anomaly(row, z)
                send_telegram(msg)
                mark_sent(alert_id)
    except Exception:
        logger.exception("Tennis anomalies FAILED")


def job_ev_tennis():
    """Calcula EV para mercados de tenis"""
    try:
        rows = fetch_latest_odds_snapshot(minutes=30, sport="tennis")
        
        for r in rows:
            league = r["league"]
            market = r["market"]
            odds = float(r["odds"])
            selection = r["selection"]
            line = float(r["line"]) if r["line"] is not None else None
            
            # Obtener configuración del torneo
            config = get_sport_config("tennis", league)
            if not config:
                continue
            
            ev_min = get_ev_threshold("tennis", league, market)
            p = None
            
            # Calcular probabilidad según el mercado
            if market == "MONEYLINE":
                # Para simplificar, usamos ELO base de 2000 para ambos
                # En producción, esto vendría de una base de datos de jugadores
                elo_diff = 200  # Diferencia de ELO estimada
                
                if selection == "HOME":
                    p = elo_win_probability(2000 + elo_diff, 2000)
                elif selection == "AWAY":
                    p = elo_win_probability(2000, 2000 + elo_diff)
                    
            elif market == "TOTAL_GAMES" and line is not None:
                mu_games = config.get("mu_games", 22.5)
                sigma_games = config.get("sigma_games", 4.0)
                
                if selection == "OVER":
                    p = prob_over_games(mu_games, sigma_games, line)
                elif selection == "UNDER":
                    p = 1.0 - prob_over_games(mu_games, sigma_games, line)
            
            if p is None or p <= 0 or p >= 1:
                continue
            
            ev = expected_value(p, odds)
            if ev >= ev_min:
                alert_id = create_alert_ev(r, ev=ev)
                if alert_id:
                    msg = format_alert_tennis_ev(r, ev, p)
                    send_telegram(msg)
                    mark_sent(alert_id)
                    
        logger.info(f"Tennis EV scan OK. rows={len(rows)}")
    except Exception:
        logger.exception("Tennis EV FAILED")
