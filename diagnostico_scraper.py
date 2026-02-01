#!/usr/bin/env python
"""
Diagnóstico del Scraper
Prueba el scraper y muestra errores detallados
"""

import sys
import traceback
from datetime import datetime

def test_imports():
    """Verifica que todos los imports funcionen"""
    print("1️⃣ Verificando imports...")
    try:
        from app.ingest.provider_flashscore import FlashscoreProvider
        from app.ingest.event_discovery import discover_events
        from app.ingest.odds_parser import parse_odds_from_html
        from app.db import get_db_connection
        print("✅ Todos los imports funcionan correctamente")
        return True
    except Exception as e:
        print(f"❌ Error en imports: {e}")
        traceback.print_exc()
        return False

def test_database():
    """Verifica conexión a la base de datos"""
    print("\n2️⃣ Verificando conexión a base de datos...")
    try:
        from app.db import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM events")
        count = cur.fetchone()[0]
        print(f"✅ Conexión exitosa. Eventos en BD: {count}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        traceback.print_exc()
        return False

def test_event_discovery():
    """Prueba el descubrimiento de eventos"""
    print("\n3️⃣ Probando descubrimiento de eventos...")
    try:
        from app.ingest.event_discovery import discover_events
        
        # Probar con basketball
        print("   📍 Probando Basketball/NBA...")
        events = discover_events("basketball", "usa/nba")
        print(f"   ✅ Eventos encontrados: {len(events)}")
        
        if events:
            print(f"   📋 Primer evento: {events[0].get('home')} vs {events[0].get('away')}")
        else:
            print("   ⚠️  No se encontraron eventos (puede ser normal si no hay partidos)")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_scraper_provider():
    """Prueba el provider de Flashscore"""
    print("\n4️⃣ Probando FlashscoreProvider...")
    try:
        from app.ingest.provider_flashscore import FlashscoreProvider
        
        provider = FlashscoreProvider()
        print("   ✅ Provider inicializado")
        
        # Probar scraping de un deporte
        print("   📍 Intentando scraping de Basketball...")
        result = provider.scrape_sport("basketball")
        
        print(f"   📊 Resultado:")
        print(f"      - Eventos: {result.get('events_found', 0)}")
        print(f"      - Odds: {result.get('odds_found', 0)}")
        print(f"      - Errores: {result.get('errors', 0)}")
        
        if result.get('errors', 0) > 0:
            print(f"   ⚠️  Detalles de errores:")
            for err in result.get('error_details', []):
                print(f"      - {err}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def test_scheduler_jobs():
    """Verifica los jobs del scheduler"""
    print("\n5️⃣ Verificando configuración del scheduler...")
    try:
        from app.scheduler import scheduler
        
        jobs = scheduler.get_jobs()
        print(f"   ✅ Jobs configurados: {len(jobs)}")
        
        for job in jobs:
            print(f"      - {job.id}: próxima ejecución en {job.next_run_time}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        traceback.print_exc()
        return False

def main():
    print("="*70)
    print("🔍 DIAGNÓSTICO DEL SCRAPER")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Ejecutar tests
    results.append(("Imports", test_imports()))
    results.append(("Base de datos", test_database()))
    results.append(("Event Discovery", test_event_discovery()))
    results.append(("Scraper Provider", test_scraper_provider()))
    results.append(("Scheduler", test_scheduler_jobs()))
    
    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n🎯 Tests pasados: {passed}/{total}")
    
    if passed == total:
        print("\n✅ Todos los tests pasaron. El scraper debería funcionar correctamente.")
    else:
        print("\n⚠️  Algunos tests fallaron. Revisa los errores arriba.")
    
    print("="*70)

if __name__ == "__main__":
    main()
