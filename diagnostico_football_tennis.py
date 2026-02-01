#!/usr/bin/env python
"""
Diagnóstico de scrapers de Football y Tennis
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def diagnose_sport(sport_name: str, url: str):
    """Diagnostica un deporte específico"""
    print(f"\n{'='*80}")
    print(f"🔍 DIAGNÓSTICO: {sport_name.upper()}")
    print(f"{'='*80}")
    print(f"URL: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(5000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
        html = page.content()
        browser.close()
    
    soup = BeautifulSoup(html, 'lxml')
    
    # Buscar diferentes estructuras
    print(f"\n📊 Análisis de estructura HTML:")
    
    # 1. Divs con clase event__match
    match_divs = soup.find_all('div', class_='event__match')
    print(f"   - div.event__match: {len(match_divs)} encontrados")
    
    # 2. Divs con clase que contenga 'event'
    event_divs = soup.find_all('div', class_=lambda x: x and 'event' in x.lower())
    print(f"   - div[class*='event']: {len(event_divs)} encontrados")
    
    # 3. Links a partidos
    match_links = soup.find_all('a', href=lambda x: x and '/match/' in x)
    print(f"   - a[href*='/match/']: {len(match_links)} encontrados")
    
    # 4. Cualquier div con participantes
    participant_divs = soup.find_all('div', class_=lambda x: x and 'participant' in x.lower())
    print(f"   - div[class*='participant']: {len(participant_divs)} encontrados")
    
    # Mostrar primeros 3 divs event__match si existen
    if match_divs:
        print(f"\n📋 Primeros 3 div.event__match:")
        for i, div in enumerate(match_divs[:3], 1):
            print(f"\n   {i}. Clases: {div.get('class', [])}")
            
            # Buscar participantes
            participants = div.find_all('div', class_=lambda x: x and 'participant' in x.lower())
            if participants:
                print(f"      Participantes encontrados: {len(participants)}")
                for p in participants[:2]:
                    print(f"      - {p.get_text(strip=True)}")
            
            # Buscar hora
            time_div = div.find('div', class_=lambda x: x and 'time' in x.lower())
            if time_div:
                print(f"      Hora: {time_div.get_text(strip=True)}")
            
            # Buscar marcador
            score_div = div.find('div', class_=lambda x: x and 'score' in x.lower())
            if score_div:
                print(f"      Marcador: {score_div.get_text(strip=True)}")
    
    # Guardar HTML para inspección manual
    filename = f"debug_{sport_name.lower()}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"\n💾 HTML guardado en: {filename}")
    
    return len(match_divs)

# ============================================================================
# DIAGNÓSTICO
# ============================================================================

print("="*80)
print("🔬 DIAGNÓSTICO DE SCRAPERS")
print("="*80)

# Football
football_count = diagnose_sport(
    "Football",
    "https://www.flashscore.com/football/fixtures/"
)

# Tennis
tennis_count = diagnose_sport(
    "Tennis",
    "https://www.flashscore.com/tennis/fixtures/"
)

# Resumen
print(f"\n{'='*80}")
print("📊 RESUMEN")
print(f"{'='*80}")
print(f"⚽ Football: {football_count} div.event__match encontrados")
print(f"🎾 Tennis: {tennis_count} div.event__match encontrados")

if football_count == 0 and tennis_count == 0:
    print("\n⚠️  POSIBLES CAUSAS:")
    print("   1. No hay eventos programados en este momento")
    print("   2. Flashscore usa estructura diferente para football/tennis")
    print("   3. Contenido cargado dinámicamente con JavaScript")
    print("   4. Necesita más tiempo de espera")
    print("\n💡 SOLUCIÓN:")
    print("   - Revisar archivos debug_football.html y debug_tennis.html")
    print("   - Buscar la estructura real de los eventos")
    print("   - Actualizar selectores en event_discovery.py")

print(f"\n{'='*80}")
