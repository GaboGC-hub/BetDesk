# app/ingest/event_discovery.py
"""
Sistema de descubrimiento de eventos deportivos desde Flashscore
Extrae partidos próximos para Basketball, Football y Tennis
"""

import re
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from .scraper_config import apply_rate_limit, SCRAPER_CONFIG

logger = logging.getLogger("betdesk.scraper")

# =============================================================================
# PLAYWRIGHT HELPER
# =============================================================================

def _fetch_with_playwright(url: str) -> str:
    """
    Obtiene HTML usando Playwright con configuración anti-detección
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=SCRAPER_CONFIG.get(
                "user_agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ),
        )

        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page.goto(url, wait_until="networkidle", timeout=30000)

        try:
            page.wait_for_selector(".event__match", timeout=8000)
        except Exception:
            logger.warning("No event__match detected, returning raw HTML")

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1500)

        html = page.content()
        browser.close()
        return html


# =============================================================================
# HELPERS COMUNES
# =============================================================================

def _is_event_started(match_div) -> bool:
    """Detecta si un evento ya inició usando señales confiables"""
    class_str = " ".join(match_div.get("class", [])).lower()
    if any(k in class_str for k in ["live", "inprogress", "started"]):
        return True

    stage = match_div.find("div", class_=re.compile(r"event__stage"))
    if stage:
        txt = stage.get_text(strip=True).lower()
        if any(k in txt for k in ["live", "half", "ended"]):
            return True

    score = match_div.find("div", class_=re.compile(r"event__score"))
    if score:
        txt = score.get_text(strip=True)
        if re.match(r"\d+\s*[:\-]\s*\d+", txt):
            return True

    return False


def _extract_participants(match_div):
    home = match_div.find("div", class_=re.compile(r"participant.*home"))
    away = match_div.find("div", class_=re.compile(r"participant.*away"))

    if home and away:
        return home.get_text(strip=True), away.get_text(strip=True)

    parts = match_div.find_all("div", class_=re.compile(r"participant"))
    if len(parts) >= 2:
        return parts[0].get_text(strip=True), parts[1].get_text(strip=True)

    return None, None


def _extract_event_url(match_div, sport: str) -> str:
    link = match_div.find("a", href=True)
    if not link:
        return f"https://www.flashscore.com/{sport}/"

    href = link.get("href", "")
    if href.startswith("http"):
        return href
    return f"https://www.flashscore.com{href}"


def _parse_event_time(time_str: str) -> datetime:
    now = datetime.now(timezone.utc)

    if not time_str:
        return now + timedelta(hours=1)

    time_str = time_str.strip().lower()

    if re.fullmatch(r"\d{1,2}:\d{2}", time_str):
        h, m = map(int, time_str.split(":"))
        return now.replace(hour=h, minute=m, second=0, microsecond=0)

    m = re.search(r"(\d{1,2})\.(\d{1,2}).*?(\d{1,2}):(\d{2})", time_str)
    if m:
        d, mo, h, mi = map(int, m.groups())
        return datetime(now.year, mo, d, h, mi, tzinfo=timezone.utc)

    return now + timedelta(hours=1)


# =============================================================================
# BASKETBALL
# =============================================================================

def discover_basketball_events(max_events: int = 20) -> List[Dict]:
    logger.info("🏀 Discovering basketball events...")
    all_events = []

    leagues = [
        {"name": "NBA", "url": "https://www.flashscore.com/basketball/usa/nba/fixtures/"},
        {"name": "CBA", "url": "https://www.flashscore.com/basketball/china/cba/fixtures/"},
    ]

    for league in leagues:
        try:
            apply_rate_limit()
            html = _fetch_with_playwright(league["url"])
            soup = BeautifulSoup(html, "lxml")
            match_divs = soup.find_all("div", class_="event__match")

            for match_div in match_divs[: max_events // 2]:
                if _is_event_started(match_div):
                    continue

                home, away = _extract_participants(match_div)
                if not home or not away:
                    continue

                time_div = match_div.find("div", class_=re.compile(r"event__time"))
                start_time = _parse_event_time(
                    time_div.get_text(strip=True) if time_div else None
                )

                all_events.append(
                    {
                        "sport": "basketball",
                        "league": league["name"],
                        "home": home,
                        "away": away,
                        "start_time_utc": start_time,
                        "flashscore_url": _extract_event_url(match_div, "basketball"),
                    }
                )
        except Exception as e:
            logger.error(f"Basketball discovery failed: {e}")

    return all_events


# =============================================================================
# FOOTBALL
# =============================================================================

def discover_football_events(max_events: int = 30) -> List[Dict]:
    logger.info("⚽ Discovering football events...")
    all_events = []

    leagues = [
        {
            "name": "Premier League",
            "url": "https://www.flashscore.co/futbol/inglaterra/premier-league/partidos/",
        },
        {
            "name": "La Liga",
            "url": "https://www.flashscore.co/futbol/espana/laliga-ea-sports/partidos/",
        },
        {
            "name": "Champions League",
            "url": "https://www.flashscore.co/futbol/europa/champions-league/partidos/",
        },
    ]

    for league in leagues:
        try:
            apply_rate_limit()
            html = _fetch_with_playwright(league["url"])
            soup = BeautifulSoup(html, "lxml")
            match_divs = soup.find_all("div", class_="event__match")

            for match_div in match_divs[: max_events // 3]:
                if _is_event_started(match_div):
                    continue

                home, away = _extract_participants(match_div)
                if not home or not away:
                    continue

                time_div = match_div.find("div", class_=re.compile(r"event__time"))
                start_time = _parse_event_time(
                    time_div.get_text(strip=True) if time_div else None
                )

                all_events.append(
                    {
                        "sport": "football",
                        "league": league["name"],
                        "home": home,
                        "away": away,
                        "start_time_utc": start_time,
                        "flashscore_url": _extract_event_url(match_div, "football"),
                    }
                )
        except Exception as e:
            logger.error(f"Football discovery failed: {e}")

    return all_events


# =============================================================================
# TENNIS
# =============================================================================

def discover_tennis_events(max_events: int = 25) -> List[Dict]:
    logger.info("🎾 Discovering tennis events...")
    events = []

    try:
        apply_rate_limit()
        html = _fetch_with_playwright("https://www.flashscore.com/tennis/")
        soup = BeautifulSoup(html, "lxml")
        match_divs = soup.find_all("div", class_="event__match")

        for match_div in match_divs[:max_events]:
            if _is_event_started(match_div):
                continue

            home, away = _extract_participants(match_div)
            if not home or not away:
                continue

            time_div = match_div.find("div", class_=re.compile(r"event__time"))
            start_time = _parse_event_time(
                time_div.get_text(strip=True) if time_div else None
            )

            events.append(
                {
                    "sport": "tennis",
                    "league": "ATP",
                    "home": home,
                    "away": away,
                    "start_time_utc": start_time,
                    "flashscore_url": _extract_event_url(match_div, "tennis"),
                }
            )

    except Exception as e:
        logger.error(f"Tennis discovery failed: {e}")

    return events


# =============================================================================
# FALLBACK
# =============================================================================

def discover_events_with_fallback(sport: str, max_events: int = 20) -> List[Dict]:
    try:
        if sport == "basketball":
            events = discover_basketball_events(max_events)
        elif sport == "football":
            events = discover_football_events(max_events)
        elif sport == "tennis":
            events = discover_tennis_events(max_events)
        else:
            raise ValueError(f"Unknown sport: {sport}")

        if not events:
            logger.warning(f"No events found for {sport}")
        return events

    except Exception as e:
        logger.error(f"Event discovery failed for {sport}: {e}")
        return []
