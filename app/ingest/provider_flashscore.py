# app/ingest/provider_flashscore.py

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from datetime import datetime, timezone
import time
from typing import Optional

def scrape_flashscore_odds(
    event_url: str,
    market: str,  # "TOTAL", "SPREAD", "MONEYLINE"
    sport: str = "basketball"
) -> list[dict]:
    """
    Scraper unificado para Flashscore con soporte para múltiples mercados
    """
    
    # Mapeo de mercados a URLs de Flashscore (formato correcto)
    market_urls = {
        "TOTAL": "odds/over-under/full-time/",
        "SPREAD": "odds/asian-handicap/full-time/",
        "MONEYLINE": "odds/1x2-odds/full-time/"
    }
    
    if market not in market_urls:
        raise ValueError(f"Mercado no soportado: {market}")
    
    # Construir URL completa
    # Formato: https://www.flashscore.com/match/basketball/team1-id/team2-id/odds/1x2-odds/full-time/?mid=xxx
    base_url = event_url.rstrip('/')
    
    # Extraer mid si existe en la URL original
    mid_param = ""
    if "?mid=" in event_url:
        mid_param = "?" + event_url.split("?")[1]
    elif "mid=" in event_url:
        # Extraer mid de la URL
        import re
        mid_match = re.search(r'mid=([^/&]+)', event_url)
        if mid_match:
            mid_param = f"?mid={mid_match.group(1)}"
    
    # Limpiar base_url de parámetros y paths extras
    base_url = base_url.split('?')[0].rstrip('/')
    
    full_url = f"{base_url}/{market_urls[market]}{mid_param}"
    
    print(f"🔍 Scraping {market} desde: {full_url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            # Navegar a la página
            page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
            
            # Esperar a que cargue la tabla de cuotas
            page.wait_for_selector("div.ui-table__row", timeout=15000)
            
            # Cerrar modales si aparecen
            try:
                close_button = page.query_selector("button.close, .modal-close, [aria-label='Close']")
                if close_button:
                    close_button.click()
                    time.sleep(0.5)
            except:
                pass
            
            # Parsear según el mercado
            if market == "TOTAL":
                rows = _parse_total_market(page)
            elif market == "SPREAD":
                rows = _parse_spread_market(page)
            elif market == "MONEYLINE":
                rows = _parse_moneyline_market(page)
            
            print(f"✅ Extraídas {len(rows)} cuotas del mercado {market}")
            return rows
            
        except PlaywrightTimeout:
            print(f"⏱️ Timeout al cargar {full_url}")
            return []
        except Exception as e:
            print(f"❌ Error scraping {market}: {e}")
            return []
        finally:
            browser.close()


def _parse_total_market(page) -> list[dict]:
    """Parser para mercado TOTAL (Over/Under)"""
    rows = []
    row_elements = page.query_selector_all("div.ui-table__row")
    
    for row_el in row_elements:
        try:
            # Bookmaker
            bookmaker_el = row_el.query_selector(".oddsCell__bookmakerCell a.prematchLink img")
            if not bookmaker_el:
                continue
            bookmaker = bookmaker_el.get_attribute("alt").strip()
            
            # Línea (total)
            line_el = row_el.query_selector("div.wcl-oddsCell_qJ5md span.wcl-oddsValue_3e8Cq")
            if not line_el:
                continue
            line_text = line_el.inner_text().strip()
            line = float(line_text.replace(",", "."))
            
            # Cuotas Over y Under
            odds_elements = row_el.query_selector_all("a.oddsCell__odd")
            if len(odds_elements) < 2:
                continue
                
            odds_over = float(odds_elements[0].inner_text().strip().replace(",", "."))
            odds_under = float(odds_elements[1].inner_text().strip().replace(",", "."))
            
            captured_at = datetime.now(timezone.utc)
            
            # Agregar ambas selecciones
            rows.append({
                "market": "TOTAL",
                "line": line,
                "bookmaker": bookmaker,
                "selection": "OVER",
                "odds": odds_over,
                "captured_at_utc": captured_at,
            })
            rows.append({
                "market": "TOTAL",
                "line": line,
                "bookmaker": bookmaker,
                "selection": "UNDER",
                "odds": odds_under,
                "captured_at_utc": captured_at,
            })
            
        except Exception as e:
            print(f"⚠️ Error parseando fila TOTAL: {e}")
            continue
    
    return rows


def _parse_spread_market(page) -> list[dict]:
    """Parser para mercado SPREAD (Handicap)"""
    rows = []
    row_elements = page.query_selector_all("div.ui-table__row")
    
    for row_el in row_elements:
        try:
            # Bookmaker
            bookmaker_el = row_el.query_selector(".oddsCell__bookmakerCell a.prematchLink img")
            if not bookmaker_el:
                continue
            bookmaker = bookmaker_el.get_attribute("alt").strip()
            
            # Línea de handicap (puede ser +/- X.5)
            line_el = row_el.query_selector("div.wcl-oddsCell_qJ5md span.wcl-oddsValue_3e8Cq")
            if not line_el:
                continue
            line_text = line_el.inner_text().strip()
            # Extraer valor numérico (ej. "-5.5" -> -5.5)
            line = float(line_text.replace(",", "."))
            
            # Cuotas para ambos equipos
            odds_elements = row_el.query_selector_all("a.oddsCell__odd")
            if len(odds_elements) < 2:
                continue
                
            odds_home = float(odds_elements[0].inner_text().strip().replace(",", "."))
            odds_away = float(odds_elements[1].inner_text().strip().replace(",", "."))
            
            captured_at = datetime.now(timezone.utc)
            
            rows.append({
                "market": "SPREAD",
                "line": line,
                "bookmaker": bookmaker,
                "selection": "HOME",
                "odds": odds_home,
                "captured_at_utc": captured_at,
            })
            rows.append({
                "market": "SPREAD",
                "line": line,
                "bookmaker": bookmaker,
                "selection": "AWAY",
                "odds": odds_away,
                "captured_at_utc": captured_at,
            })
            
        except Exception as e:
            print(f"⚠️ Error parseando fila SPREAD: {e}")
            continue
    
    return rows


def _parse_moneyline_market(page) -> list[dict]:
    """Parser para mercado MONEYLINE (Ganador directo)"""
    rows = []
    row_elements = page.query_selector_all("div.ui-table__row")
    
    for row_el in row_elements:
        try:
            # Bookmaker
            bookmaker_el = row_el.query_selector(".oddsCell__bookmakerCell a.prematchLink img")
            if not bookmaker_el:
                continue
            bookmaker = bookmaker_el.get_attribute("alt").strip()
            
            # Cuotas para local y visitante (no hay línea en ML)
            odds_elements = row_el.query_selector_all("a.oddsCell__odd")
            if len(odds_elements) < 2:
                continue
                
            odds_home = float(odds_elements[0].inner_text().strip().replace(",", "."))
            odds_away = float(odds_elements[1].inner_text().strip().replace(",", "."))
            
            captured_at = datetime.now(timezone.utc)
            
            rows.append({
                "market": "MONEYLINE",
                "line": None,  # No hay línea en moneyline
                "bookmaker": bookmaker,
                "selection": "HOME",
                "odds": odds_home,
                "captured_at_utc": captured_at,
            })
            rows.append({
                "market": "MONEYLINE",
                "line": None,
                "bookmaker": bookmaker,
                "selection": "AWAY",
                "odds": odds_away,
                "captured_at_utc": captured_at,
            })
            
        except Exception as e:
            print(f"⚠️ Error parseando fila MONEYLINE: {e}")
            continue
    
    return rows


def fetch_event_page_html(url: str) -> str:
    """
    Función simple para obtener el HTML de una página de evento de Flashscore.
    Usada para smoke tests y debugging.
    
    Args:
        url: URL del evento en Flashscore
        
    Returns:
        HTML de la página como string
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)  # Esperar a que cargue contenido dinámico
            html = page.content()
            return html
        except Exception as e:
            print(f"❌ Error obteniendo HTML: {e}")
            return ""
        finally:
            browser.close()


# ============================================================================
# NUEVAS FUNCIONES - FASE 3: EVENT DISCOVERY
# ============================================================================

import logging
from typing import List, Dict

logger = logging.getLogger("betdesk.scraper")


def upcoming_basketball_events(max_events: int = 20) -> List[Dict]:
    """
    Obtiene eventos próximos de basketball desde Flashscore
    Usa event_discovery con fallback a mock
    """
    logger.info("🏀 Fetching upcoming basketball events...")
    try:
        from .event_discovery import discover_events_with_fallback
        return discover_events_with_fallback("basketball", max_events)
    except Exception as e:
        logger.error(f"Error in upcoming_basketball_events: {e}")
        from .provider_mock import upcoming_nba_cba_events
        return upcoming_nba_cba_events()


def upcoming_football_events(max_events: int = 30) -> List[Dict]:
    """
    Obtiene eventos próximos de football desde Flashscore
    Usa event_discovery con fallback a mock
    """
    logger.info("⚽ Fetching upcoming football events...")
    try:
        from .event_discovery import discover_events_with_fallback
        return discover_events_with_fallback("football", max_events)
    except Exception as e:
        logger.error(f"Error in upcoming_football_events: {e}")
        from .provider_mock import upcoming_football_events as mock_football
        return mock_football()


def upcoming_tennis_events(max_events: int = 25) -> List[Dict]:
    """
    Obtiene eventos próximos de tennis desde Flashscore
    Usa event_discovery con fallback a mock
    """
    logger.info("🎾 Fetching upcoming tennis events...")
    try:
        from .event_discovery import discover_events_with_fallback
        return discover_events_with_fallback("tennis", max_events)
    except Exception as e:
        logger.error(f"Error in upcoming_tennis_events: {e}")
        from .provider_mock import upcoming_tennis_events as mock_tennis
        return mock_tennis()


def odds_for_event(url: str) -> List[Dict]:
    """
    Extrae cuotas de un evento usando el scraper existente
    Detecta el deporte y usa el parser apropiado
    """
    logger.info(f"📊 Fetching odds for event: {url}")
    
    try:
        # Detectar deporte desde URL
        sport = _detect_sport_from_url(url)
        
        if not sport:
            logger.warning(f"Could not detect sport from URL: {url}")
            return []
        
        # Usar scraper existente para cada mercado
        all_odds = []
        
        if sport == "basketball":
            markets = ["TOTAL", "SPREAD", "MONEYLINE"]
        elif sport == "football":
            markets = ["TOTAL"]  # Agregar más según necesidad
        elif sport == "tennis":
            markets = ["MONEYLINE"]
        else:
            return []
        
        for market in markets:
            try:
                odds = scrape_flashscore_odds(url, market, sport)
                all_odds.extend(odds)
            except Exception as e:
                logger.debug(f"Error scraping {market} for {url}: {e}")
                continue
        
        logger.info(f"✅ Extracted {len(all_odds)} odds from {url}")
        return all_odds
        
    except Exception as e:
        logger.error(f"Error in odds_for_event: {e}")
        return []


def _detect_sport_from_url(url: str) -> Optional[str]:
    """Detecta deporte desde URL"""
    url_lower = url.lower()
    
    if '/basketball/' in url_lower or '/baloncesto/' in url_lower:
        return "basketball"
    elif '/football/' in url_lower or '/futbol/' in url_lower or '/soccer/' in url_lower:
        return "football"
    elif '/tennis/' in url_lower or '/tenis/' in url_lower:
        return "tennis"
    
    return None


def test_scraper_connection() -> bool:
    """Prueba la conexión con Flashscore"""
    try:
        html = fetch_event_page_html("https://www.flashscore.com/")
        if html and len(html) > 1000:
            logger.info("✅ Scraper connection test: OK")
            return True
        else:
            logger.warning("⚠️  Scraper connection test: Invalid response")
            return False
    except Exception as e:
        logger.error(f"❌ Scraper connection test failed: {e}")
        return False
