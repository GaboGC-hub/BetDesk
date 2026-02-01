# app/ingest/odds_parser.py
"""
Parser de cuotas desde páginas de eventos de Flashscore
Extrae odds de múltiples bookmakers por mercado
"""

import re
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import json

logger = logging.getLogger("betdesk.scraper")


# ============================================================================
# BASKETBALL ODDS PARSER
# ============================================================================

def parse_basketball_odds(html: str, event_url: str = None) -> List[Dict]:
    """
    Parsea cuotas de basketball desde HTML de Flashscore
    
    Args:
        html: HTML de la página del evento
        event_url: URL del evento (para logging)
        
    Returns:
        Lista de odds:
        {
            "market": "TOTAL",
            "line": 228.5,
            "bookmaker": "Bet365",
            "selection": "OVER",
            "odds": 1.90,
            "captured_at_utc": datetime(...)
        }
    """
    logger.info(f"🏀 Parsing basketball odds from {event_url or 'HTML'}")
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        odds_list = []
        captured_at = datetime.now(timezone.utc)
        
        # Estrategia 1: Buscar datos en JSON embebido
        odds_from_json = _extract_odds_from_json(soup, "basketball")
        if odds_from_json:
            for odd in odds_from_json:
                odd["captured_at_utc"] = captured_at
            return odds_from_json
        
        # Estrategia 2: Parsear tablas HTML de odds
        odds_tables = soup.find_all('div', class_=re.compile(r'oddsTab|ui-table'))
        
        for table in odds_tables:
            # Identificar mercado
            market_header = table.find_previous(class_=re.compile(r'oddsHeader|marketHeader'))
            if not market_header:
                continue
            
            market_text = market_header.get_text(strip=True).upper()
            market_type = _identify_basketball_market(market_text)
            
            if not market_type:
                continue
            
            # Extraer línea si existe
            line = _extract_line_from_text(market_text)
            
            # Parsear filas de bookmakers
            rows = table.find_all('div', class_=re.compile(r'oddsRow|table__row'))
            
            for row in rows:
                try:
                    odd = _parse_basketball_odds_row(row, market_type, line, captured_at)
                    if odd:
                        odds_list.append(odd)
                except Exception as e:
                    logger.debug(f"Error parsing basketball odds row: {e}")
                    continue
        
        logger.info(f"✅ Parsed {len(odds_list)} basketball odds")
        return odds_list
        
    except Exception as e:
        logger.error(f"❌ Basketball odds parsing failed: {e}")
        return []


def _parse_basketball_odds_row(row, market: str, line: Optional[float], captured_at: datetime) -> Optional[Dict]:
    """Parsea una fila de odds de basketball"""
    try:
        # Extraer bookmaker
        bookmaker_elem = row.find(class_=re.compile(r'bookmaker|participant'))
        if not bookmaker_elem:
            return None
        
        bookmaker = bookmaker_elem.get_text(strip=True)
        
        # Extraer odds (pueden ser 2 o 3 columnas dependiendo del mercado)
        odds_cells = row.find_all(class_=re.compile(r'odds|cell'))
        
        if market == "TOTAL" and len(odds_cells) >= 2:
            # Over/Under
            over_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            under_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if over_odds:
                result.append({
                    "market": "TOTAL",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "OVER",
                    "odds": over_odds,
                    "captured_at_utc": captured_at
                })
            if under_odds:
                result.append({
                    "market": "TOTAL",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "UNDER",
                    "odds": under_odds,
                    "captured_at_utc": captured_at
                })
            return result[0] if result else None
        
        elif market == "SPREAD" and len(odds_cells) >= 2:
            # Spread (Handicap)
            home_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            away_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if home_odds:
                result.append({
                    "market": "SPREAD",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "HOME",
                    "odds": home_odds,
                    "captured_at_utc": captured_at
                })
            if away_odds:
                result.append({
                    "market": "SPREAD",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "AWAY",
                    "odds": away_odds,
                    "captured_at_utc": captured_at
                })
            return result[0] if result else None
        
        elif market == "MONEYLINE" and len(odds_cells) >= 2:
            # Moneyline (1X2 sin empate)
            home_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            away_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if home_odds:
                result.append({
                    "market": "MONEYLINE",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "HOME",
                    "odds": home_odds,
                    "captured_at_utc": captured_at
                })
            if away_odds:
                result.append({
                    "market": "MONEYLINE",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "AWAY",
                    "odds": away_odds,
                    "captured_at_utc": captured_at
                })
            return result[0] if result else None
        
        return None
        
    except Exception as e:
        logger.debug(f"Error parsing basketball odds row: {e}")
        return None


def _identify_basketball_market(text: str) -> Optional[str]:
    """Identifica el tipo de mercado de basketball"""
    text_upper = text.upper()
    
    if "TOTAL" in text_upper or "OVER/UNDER" in text_upper or "O/U" in text_upper:
        return "TOTAL"
    elif "SPREAD" in text_upper or "HANDICAP" in text_upper or "AH" in text_upper:
        return "SPREAD"
    elif "MONEYLINE" in text_upper or "WINNER" in text_upper or "1X2" in text_upper:
        return "MONEYLINE"
    
    return None


# ============================================================================
# FOOTBALL ODDS PARSER
# ============================================================================

def parse_football_odds(html: str, event_url: str = None) -> List[Dict]:
    """
    Parsea cuotas de football desde HTML de Flashscore
    
    Returns:
        Lista de odds para mercados: 1X2, TOTAL, BTTS
    """
    logger.info(f"⚽ Parsing football odds from {event_url or 'HTML'}")
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        odds_list = []
        captured_at = datetime.now(timezone.utc)
        
        # Estrategia 1: JSON embebido
        odds_from_json = _extract_odds_from_json(soup, "football")
        if odds_from_json:
            for odd in odds_from_json:
                odd["captured_at_utc"] = captured_at
            return odds_from_json
        
        # Estrategia 2: Parsear tablas HTML
        odds_tables = soup.find_all('div', class_=re.compile(r'oddsTab|ui-table'))
        
        for table in odds_tables:
            market_header = table.find_previous(class_=re.compile(r'oddsHeader|marketHeader'))
            if not market_header:
                continue
            
            market_text = market_header.get_text(strip=True).upper()
            market_type = _identify_football_market(market_text)
            
            if not market_type:
                continue
            
            line = _extract_line_from_text(market_text)
            
            rows = table.find_all('div', class_=re.compile(r'oddsRow|table__row'))
            
            for row in rows:
                try:
                    odd = _parse_football_odds_row(row, market_type, line, captured_at)
                    if odd:
                        if isinstance(odd, list):
                            odds_list.extend(odd)
                        else:
                            odds_list.append(odd)
                except Exception as e:
                    logger.debug(f"Error parsing football odds row: {e}")
                    continue
        
        logger.info(f"✅ Parsed {len(odds_list)} football odds")
        return odds_list
        
    except Exception as e:
        logger.error(f"❌ Football odds parsing failed: {e}")
        return []


def _parse_football_odds_row(row, market: str, line: Optional[float], captured_at: datetime):
    """Parsea una fila de odds de football"""
    try:
        bookmaker_elem = row.find(class_=re.compile(r'bookmaker|participant'))
        if not bookmaker_elem:
            return None
        
        bookmaker = bookmaker_elem.get_text(strip=True)
        odds_cells = row.find_all(class_=re.compile(r'odds|cell'))
        
        if market == "1X2" and len(odds_cells) >= 3:
            # 1X2 (Home, Draw, Away)
            home_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            draw_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            away_odds = _parse_odds_value(odds_cells[2].get_text(strip=True))
            
            result = []
            if home_odds:
                result.append({
                    "market": "1X2",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "HOME",
                    "odds": home_odds,
                    "captured_at_utc": captured_at
                })
            if draw_odds:
                result.append({
                    "market": "1X2",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "DRAW",
                    "odds": draw_odds,
                    "captured_at_utc": captured_at
                })
            if away_odds:
                result.append({
                    "market": "1X2",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "AWAY",
                    "odds": away_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        elif market == "TOTAL" and len(odds_cells) >= 2:
            # Over/Under goles
            over_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            under_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if over_odds:
                result.append({
                    "market": "TOTAL",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "OVER",
                    "odds": over_odds,
                    "captured_at_utc": captured_at
                })
            if under_odds:
                result.append({
                    "market": "TOTAL",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "UNDER",
                    "odds": under_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        elif market == "BTTS" and len(odds_cells) >= 2:
            # Both Teams To Score
            yes_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            no_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if yes_odds:
                result.append({
                    "market": "BTTS",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "YES",
                    "odds": yes_odds,
                    "captured_at_utc": captured_at
                })
            if no_odds:
                result.append({
                    "market": "BTTS",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "NO",
                    "odds": no_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        return None
        
    except Exception as e:
        logger.debug(f"Error parsing football odds row: {e}")
        return None


def _identify_football_market(text: str) -> Optional[str]:
    """Identifica el tipo de mercado de football"""
    text_upper = text.upper()
    
    if "1X2" in text_upper or "FULL TIME RESULT" in text_upper or "MATCH RESULT" in text_upper:
        return "1X2"
    elif "TOTAL" in text_upper or "OVER/UNDER" in text_upper or "GOALS" in text_upper:
        return "TOTAL"
    elif "BTTS" in text_upper or "BOTH TEAMS TO SCORE" in text_upper or "GG" in text_upper:
        return "BTTS"
    
    return None


# ============================================================================
# TENNIS ODDS PARSER
# ============================================================================

def parse_tennis_odds(html: str, event_url: str = None) -> List[Dict]:
    """
    Parsea cuotas de tennis desde HTML de Flashscore
    
    Returns:
        Lista de odds para mercados: MONEYLINE, TOTAL_GAMES, HANDICAP_SETS
    """
    logger.info(f"🎾 Parsing tennis odds from {event_url or 'HTML'}")
    
    try:
        soup = BeautifulSoup(html, 'lxml')
        odds_list = []
        captured_at = datetime.now(timezone.utc)
        
        # Estrategia 1: JSON embebido
        odds_from_json = _extract_odds_from_json(soup, "tennis")
        if odds_from_json:
            for odd in odds_from_json:
                odd["captured_at_utc"] = captured_at
            return odds_from_json
        
        # Estrategia 2: Parsear tablas HTML
        odds_tables = soup.find_all('div', class_=re.compile(r'oddsTab|ui-table'))
        
        for table in odds_tables:
            market_header = table.find_previous(class_=re.compile(r'oddsHeader|marketHeader'))
            if not market_header:
                continue
            
            market_text = market_header.get_text(strip=True).upper()
            market_type = _identify_tennis_market(market_text)
            
            if not market_type:
                continue
            
            line = _extract_line_from_text(market_text)
            
            rows = table.find_all('div', class_=re.compile(r'oddsRow|table__row'))
            
            for row in rows:
                try:
                    odd = _parse_tennis_odds_row(row, market_type, line, captured_at)
                    if odd:
                        if isinstance(odd, list):
                            odds_list.extend(odd)
                        else:
                            odds_list.append(odd)
                except Exception as e:
                    logger.debug(f"Error parsing tennis odds row: {e}")
                    continue
        
        logger.info(f"✅ Parsed {len(odds_list)} tennis odds")
        return odds_list
        
    except Exception as e:
        logger.error(f"❌ Tennis odds parsing failed: {e}")
        return []


def _parse_tennis_odds_row(row, market: str, line: Optional[float], captured_at: datetime):
    """Parsea una fila de odds de tennis"""
    try:
        bookmaker_elem = row.find(class_=re.compile(r'bookmaker|participant'))
        if not bookmaker_elem:
            return None
        
        bookmaker = bookmaker_elem.get_text(strip=True)
        odds_cells = row.find_all(class_=re.compile(r'odds|cell'))
        
        if market == "MONEYLINE" and len(odds_cells) >= 2:
            # Winner (Player 1 vs Player 2)
            player1_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            player2_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if player1_odds:
                result.append({
                    "market": "MONEYLINE",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "HOME",
                    "odds": player1_odds,
                    "captured_at_utc": captured_at
                })
            if player2_odds:
                result.append({
                    "market": "MONEYLINE",
                    "line": None,
                    "bookmaker": bookmaker,
                    "selection": "AWAY",
                    "odds": player2_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        elif market == "TOTAL_GAMES" and len(odds_cells) >= 2:
            # Over/Under total games
            over_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            under_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if over_odds:
                result.append({
                    "market": "TOTAL_GAMES",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "OVER",
                    "odds": over_odds,
                    "captured_at_utc": captured_at
                })
            if under_odds:
                result.append({
                    "market": "TOTAL_GAMES",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "UNDER",
                    "odds": under_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        elif market == "HANDICAP_SETS" and len(odds_cells) >= 2:
            # Handicap de sets
            player1_odds = _parse_odds_value(odds_cells[0].get_text(strip=True))
            player2_odds = _parse_odds_value(odds_cells[1].get_text(strip=True))
            
            result = []
            if player1_odds:
                result.append({
                    "market": "HANDICAP_SETS",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "HOME",
                    "odds": player1_odds,
                    "captured_at_utc": captured_at
                })
            if player2_odds:
                result.append({
                    "market": "HANDICAP_SETS",
                    "line": line,
                    "bookmaker": bookmaker,
                    "selection": "AWAY",
                    "odds": player2_odds,
                    "captured_at_utc": captured_at
                })
            return result
        
        return None
        
    except Exception as e:
        logger.debug(f"Error parsing tennis odds row: {e}")
        return None


def _identify_tennis_market(text: str) -> Optional[str]:
    """Identifica el tipo de mercado de tennis"""
    text_upper = text.upper()
    
    if "WINNER" in text_upper or "MONEYLINE" in text_upper or "MATCH" in text_upper:
        return "MONEYLINE"
    elif "TOTAL GAMES" in text_upper or "GAMES O/U" in text_upper:
        return "TOTAL_GAMES"
    elif "HANDICAP" in text_upper or "SETS" in text_upper:
        return "HANDICAP_SETS"
    
    return None


# ============================================================================
# UTILIDADES COMUNES
# ============================================================================

def _extract_odds_from_json(soup: BeautifulSoup, sport: str) -> List[Dict]:
    """
    Intenta extraer odds desde JSON embebido en el HTML
    Flashscore a veces incluye datos en window.__INITIAL_STATE__ o similar
    """
    try:
        scripts = soup.find_all('script')
        
        for script in scripts:
            if not script.string:
                continue
            
            # Buscar patrones comunes de datos JSON
            if 'window.__INITIAL_STATE__' in script.string:
                # Extraer JSON
                match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.+?});', script.string, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    # Aquí iría la lógica para extraer odds del JSON
                    # Esto depende de la estructura específica de Flashscore
                    logger.debug("Found JSON data in HTML")
                    return []  # Por ahora retornamos vacío
            
            elif 'oddsData' in script.string or 'bookmakers' in script.string:
                # Otro patrón posible
                logger.debug("Found potential odds data in script")
                return []
        
        return []
        
    except Exception as e:
        logger.debug(f"Error extracting odds from JSON: {e}")
        return []


def _extract_line_from_text(text: str) -> Optional[float]:
    """
    Extrae la línea (número) de un texto de mercado
    Ej: "Over/Under 2.5" -> 2.5
    """
    try:
        # Buscar números decimales
        match = re.search(r'(\d+\.?\d*)', text)
        if match:
            return float(match.group(1))
        return None
    except:
        return None


def _parse_odds_value(text: str) -> Optional[float]:
    """
    Parsea un valor de odds desde texto
    Maneja formatos: "1.90", "1,90", "19/10" (fracción)
    """
    try:
        text = text.strip()
        
        if not text or text == '-' or text == 'N/A':
            return None
        
        # Formato decimal con coma
        text = text.replace(',', '.')
        
        # Formato fracción (ej: "19/10")
        if '/' in text:
            parts = text.split('/')
            if len(parts) == 2:
                numerator = float(parts[0])
                denominator = float(parts[1])
                # Convertir a decimal odds
                return (numerator / denominator) + 1.0
        
        # Formato decimal directo
        odds = float(text)
        
        # Validar rango razonable
        if 1.01 <= odds <= 1000.0:
            return odds
        
        return None
        
    except:
        return None


def _normalize_bookmaker_name(name: str) -> str:
    """Normaliza nombres de bookmakers"""
    name_map = {
        "bet365": "Bet365",
        "betfair": "Betfair",
        "william hill": "William Hill",
        "1xbet": "1xBet",
        "pinnacle": "Pinnacle",
        "betway": "Betway",
        "unibet": "Unibet",
        "bwin": "Bwin",
        "888sport": "888Sport",
        "ladbrokes": "Ladbrokes",
    }
    
    name_lower = name.lower()
    for key, value in name_map.items():
        if key in name_lower:
            return value
    
    return name.title()
