# app/ingest/html_utils.py
"""
Utilidades para parsear HTML de Flashscore
Funciones helper para extracción de datos
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional, Tuple
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger("betdesk.scraper")


# ============================================================================
# EXTRACCIÓN DE DATOS DEL EVENTO
# ============================================================================

def extract_event_id(url: str) -> Optional[str]:
    """
    Extrae el ID del evento desde la URL de Flashscore
    
    Args:
        url: URL del evento (ej: "https://www.flashscore.com/match/abc123/")
        
    Returns:
        ID del evento o None
    
    Examples:
        >>> extract_event_id("https://www.flashscore.com/match/abc123/")
        'abc123'
    """
    try:
        # Patrón: /match/ID/ o /partido/deporte/equipo1-ID/equipo2-ID2/
        match = re.search(r'/match/([a-zA-Z0-9]+)/', url)
        if match:
            return match.group(1)
        
        # Patrón alternativo
        match = re.search(r'-([a-zA-Z0-9]{8})/', url)
        if match:
            return match.group(1)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting event ID from {url}: {e}")
        return None


def extract_team_names(html: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extrae nombres de equipos/jugadores desde HTML
    
    Args:
        html: HTML de la página del evento
        
    Returns:
        Tupla (home, away) o (None, None)
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Estrategia 1: Buscar en participantes
        participants = soup.find_all(class_=re.compile(r'participant|team'))
        
        if len(participants) >= 2:
            home = participants[0].get_text(strip=True)
            away = participants[1].get_text(strip=True)
            return (home, away)
        
        # Estrategia 2: Buscar en título
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            # Formato: "Team1 vs Team2 - Flashscore"
            match = re.search(r'(.+?)\s+vs\s+(.+?)\s*[-–]', title_text)
            if match:
                return (match.group(1).strip(), match.group(2).strip())
        
        # Estrategia 3: Buscar en h1
        h1 = soup.find('h1')
        if h1:
            h1_text = h1.get_text()
            match = re.search(r'(.+?)\s+vs\s+(.+?)$', h1_text)
            if match:
                return (match.group(1).strip(), match.group(2).strip())
        
        return (None, None)
        
    except Exception as e:
        logger.debug(f"Error extracting team names: {e}")
        return (None, None)


def extract_league_name(html: str) -> Optional[str]:
    """
    Extrae nombre de la liga/torneo desde HTML
    
    Args:
        html: HTML de la página del evento
        
    Returns:
        Nombre de la liga o None
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Estrategia 1: Buscar en breadcrumb
        breadcrumb = soup.find(class_=re.compile(r'breadcrumb|tournament'))
        if breadcrumb:
            links = breadcrumb.find_all('a')
            if len(links) >= 2:
                # Típicamente: Sport > Country > League
                return links[-1].get_text(strip=True)
        
        # Estrategia 2: Buscar en metadata
        meta_league = soup.find('meta', {'property': 'og:title'})
        if meta_league:
            content = meta_league.get('content', '')
            # Formato: "Team1 vs Team2 - League - Flashscore"
            match = re.search(r'-\s*(.+?)\s*-\s*Flashscore', content)
            if match:
                return match.group(1).strip()
        
        # Estrategia 3: Buscar en clase específica
        league_elem = soup.find(class_=re.compile(r'tournamentHeader|leagueName'))
        if league_elem:
            return league_elem.get_text(strip=True)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting league name: {e}")
        return None


def extract_start_time(html: str) -> Optional[datetime]:
    """
    Extrae hora de inicio del evento desde HTML
    
    Args:
        html: HTML de la página del evento
        
    Returns:
        datetime en UTC o None
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Estrategia 1: Buscar en elemento de tiempo
        time_elem = soup.find(class_=re.compile(r'startTime|matchTime'))
        if time_elem:
            time_text = time_elem.get_text(strip=True)
            return _parse_time_string(time_text)
        
        # Estrategia 2: Buscar en atributo data-time
        time_elem = soup.find(attrs={'data-time': True})
        if time_elem:
            timestamp = time_elem.get('data-time')
            try:
                return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            except:
                pass
        
        # Estrategia 3: Buscar en metadata
        meta_time = soup.find('meta', {'property': 'og:updated_time'})
        if meta_time:
            time_str = meta_time.get('content', '')
            return _parse_iso_time(time_str)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting start time: {e}")
        return None


def extract_sport_type(html: str, url: str = None) -> Optional[str]:
    """
    Detecta el tipo de deporte desde HTML o URL
    
    Args:
        html: HTML de la página
        url: URL del evento (opcional)
        
    Returns:
        "basketball", "football", "tennis" o None
    """
    try:
        # Estrategia 1: Desde URL
        if url:
            url_lower = url.lower()
            if '/basketball/' in url_lower or '/baloncesto/' in url_lower:
                return "basketball"
            elif '/football/' in url_lower or '/futbol/' in url_lower or '/soccer/' in url_lower:
                return "football"
            elif '/tennis/' in url_lower or '/tenis/' in url_lower:
                return "tennis"
        
        # Estrategia 2: Desde HTML
        soup = BeautifulSoup(html, 'lxml')
        
        # Buscar en breadcrumb
        breadcrumb = soup.find(class_=re.compile(r'breadcrumb'))
        if breadcrumb:
            text = breadcrumb.get_text().lower()
            if 'basketball' in text or 'baloncesto' in text:
                return "basketball"
            elif 'football' in text or 'futbol' in text or 'soccer' in text:
                return "football"
            elif 'tennis' in text or 'tenis' in text:
                return "tennis"
        
        # Buscar en metadata
        meta_sport = soup.find('meta', {'name': 'sport'})
        if meta_sport:
            sport = meta_sport.get('content', '').lower()
            if 'basketball' in sport:
                return "basketball"
            elif 'football' in sport or 'soccer' in sport:
                return "football"
            elif 'tennis' in sport:
                return "tennis"
        
        return None
        
    except Exception as e:
        logger.debug(f"Error detecting sport type: {e}")
        return None


# ============================================================================
# BÚSQUEDA DE SECCIONES
# ============================================================================

def find_odds_section(html: str, market: str = None) -> Optional[str]:
    """
    Encuentra la sección de odds en el HTML
    
    Args:
        html: HTML completo
        market: Mercado específico a buscar (opcional)
        
    Returns:
        HTML de la sección de odds o None
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Buscar contenedor principal de odds
        odds_container = soup.find(class_=re.compile(r'oddsContainer|oddsWrapper|odds-section'))
        
        if odds_container:
            return str(odds_container)
        
        # Buscar por ID
        odds_div = soup.find(id=re.compile(r'odds|betting'))
        if odds_div:
            return str(odds_div)
        
        # Si se especificó un mercado, buscar esa sección específica
        if market:
            market_section = soup.find(text=re.compile(market, re.IGNORECASE))
            if market_section:
                parent = market_section.find_parent('div', class_=re.compile(r'section|tab'))
                if parent:
                    return str(parent)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error finding odds section: {e}")
        return None


def find_event_status(html: str) -> Optional[str]:
    """
    Encuentra el estado del evento (scheduled, live, finished)
    
    Args:
        html: HTML de la página
        
    Returns:
        Estado del evento o None
    """
    try:
        soup = BeautifulSoup(html, 'lxml')
        
        # Buscar indicador de estado
        status_elem = soup.find(class_=re.compile(r'status|matchStatus'))
        if status_elem:
            status_text = status_elem.get_text().lower()
            
            if 'live' in status_text or 'en vivo' in status_text:
                return "live"
            elif 'finished' in status_text or 'finalizado' in status_text:
                return "finished"
            elif 'scheduled' in status_text or 'programado' in status_text:
                return "scheduled"
        
        # Buscar en clases CSS
        if soup.find(class_=re.compile(r'live|inplay')):
            return "live"
        elif soup.find(class_=re.compile(r'finished|ended')):
            return "finished"
        
        # Default: scheduled
        return "scheduled"
        
    except Exception as e:
        logger.debug(f"Error finding event status: {e}")
        return None


# ============================================================================
# UTILIDADES DE PARSING
# ============================================================================

def _parse_time_string(time_str: str) -> Optional[datetime]:
    """
    Parsea string de tiempo a datetime
    
    Formatos soportados:
    - "19:30"
    - "2024-01-25 19:30"
    - "25.01.2024 19:30"
    """
    try:
        # Formato ISO
        if 'T' in time_str or len(time_str) > 16:
            return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        
        # Formato "HH:MM"
        if re.match(r'^\d{1,2}:\d{2}$', time_str):
            now = datetime.now(timezone.utc)
            hour, minute = map(int, time_str.split(':'))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Formato "DD.MM.YYYY HH:MM"
        match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})', time_str)
        if match:
            day, month, year, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        
        # Formato "YYYY-MM-DD HH:MM"
        match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})', time_str)
        if match:
            year, month, day, hour, minute = map(int, match.groups())
            return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)
        
        return None
        
    except Exception as e:
        logger.debug(f"Error parsing time string '{time_str}': {e}")
        return None


def _parse_iso_time(iso_str: str) -> Optional[datetime]:
    """Parsea string ISO 8601 a datetime"""
    try:
        return datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
    except:
        return None


def clean_text(text: str) -> str:
    """
    Limpia texto extraído de HTML
    
    Args:
        text: Texto a limpiar
        
    Returns:
        Texto limpio
    """
    if not text:
        return ""
    
    # Remover espacios múltiples
    text = re.sub(r'\s+', ' ', text)
    
    # Remover caracteres especiales
    text = text.strip()
    
    # Remover saltos de línea
    text = text.replace('\n', ' ').replace('\r', '')
    
    return text


def is_valid_html(html: str, min_length: int = 1000) -> bool:
    """
    Valida que el HTML sea válido y suficientemente largo
    
    Args:
        html: HTML a validar
        min_length: Longitud mínima esperada
        
    Returns:
        True si es válido
    """
    if not html or len(html) < min_length:
        return False
    
    # Verificar que contenga tags HTML básicos
    if '<html' not in html.lower() and '<body' not in html.lower():
        return False
    
    # Verificar que no sea una página de error
    if 'error 404' in html.lower() or 'page not found' in html.lower():
        return False
    
    return True


def extract_json_from_script(html: str, pattern: str = None) -> Optional[dict]:
    """
    Extrae datos JSON desde tags <script>
    
    Args:
        html: HTML completo
        pattern: Patrón regex para buscar (opcional)
        
    Returns:
        Dict con datos JSON o None
    """
    try:
        import json
        soup = BeautifulSoup(html, 'lxml')
        scripts = soup.find_all('script')
        
        for script in scripts:
            if not script.string:
                continue
            
            # Si hay patrón, buscar específicamente
            if pattern:
                match = re.search(pattern, script.string, re.DOTALL)
                if match:
                    json_str = match.group(1)
                    return json.loads(json_str)
            else:
                # Buscar cualquier JSON
                match = re.search(r'({.+})', script.string, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        continue
        
        return None
        
    except Exception as e:
        logger.debug(f"Error extracting JSON from script: {e}")
        return None
