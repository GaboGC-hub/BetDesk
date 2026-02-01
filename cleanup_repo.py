#!/usr/bin/env python
"""Script para limpiar y organizar el repositorio"""

import os
import shutil

print("🧹 LIMPIANDO REPOSITORIO BETDESK")
print("="*70)

# Archivos de prueba a eliminar
test_files = [
    'analyze_flashscore_html.py',
    'analyze_html_structure.py', 
    'analyze_playwright_html.py',
    'enable_real_scraping.py',
    'test_fase1.py',
    'test_fase2.py',
    'test_integration.py',
    'test_odds_scraping_visual.py',
    'test_parse_saved_html.py',
    'test_playwright_debug.py',
    'test_real_discovery.py',
    'test_scraper_fase3.py',
    'test_scraper_real.py',
    'test_scraping_automatico.py',
    'test_server_integration.py',
    'test_ui_con_servidor.py',
    'test_ui_visual.py',
    'test_updated_parser.py',
    'test_url_format.py',
    'start_and_test_ui.py',
    'test_correcciones_completo.py'
]

# Documentos de prueba a eliminar
doc_files = [
    'FASE1_RESUMEN.md',
    'FASE2_PLAN.md',
    'FASE2_RESUMEN.md',
    'FASE2_COMPLETADO.md',
    'FASE3_PLAN.md',
    'FASE3_COMPLETADO.md',
    'PLAN_EXPANSION.md',
    'DATOS_REALES.md',
    'DATOS_REALES_CONFIRMADO.md',
    'COMO_VERIFICAR_DATOS_REALES.md',
    'SCRAPING_AUTOMATICO.md',
    'SCRAPING_REAL_EXITOSO.md',
    'URLS_CORREGIDAS.md',
    'TESTING_EXHAUSTIVO_PROGRESO.md',
    'TESTING_COMPLETO_RESUMEN.md',
    'RESUMEN_UI_Y_MEJORAS.md',
    'CORRECCIONES_FINALES.md',
    'INSTRUCCIONES_REINICIO.md',
    'UI_PROFESIONAL_CREADA.md',
    'RESUMEN_FINAL.md'
]

# Eliminar archivos de prueba
print("\n📝 Eliminando archivos de prueba...")
deleted_tests = 0
for f in test_files:
    if os.path.exists(f):
        os.remove(f)
        deleted_tests += 1
        print(f"   ✅ {f}")

print(f"\n✅ Eliminados {deleted_tests} archivos de prueba")

# Eliminar documentos de prueba
print("\n📄 Eliminando documentos de prueba...")
deleted_docs = 0
for f in doc_files:
    if os.path.exists(f):
        os.remove(f)
        deleted_docs += 1
        print(f"   ✅ {f}")

print(f"\n✅ Eliminados {deleted_docs} documentos de prueba")

# Limpiar directorio scheduler vacío
if os.path.exists('scheduler') and not os.listdir('scheduler'):
    os.rmdir('scheduler')
    print("\n✅ Eliminado directorio scheduler vacío")

print("\n" + "="*70)
print("✅ LIMPIEZA COMPLETADA")
print("\n📁 Estructura final del repositorio:")
print("""
Betplay/
├── app/                    # Código principal
│   ├── config/            # Configuraciones
│   ├── decision/          # Modelos de decisión
│   ├── ingest/            # Scraping
│   ├── crud.py
│   ├── db.py
│   ├── formatters.py
│   ├── main.py
│   ├── scheduler.py
│   ├── security.py
│   └── telegram.py
├── debug/                  # Screenshots y HTML de debug
├── sql/                    # Esquemas de BD
├── templates/              # Templates HTML
├── docker-compose.yml
├── requirements.txt
├── setup.py
├── README.md
├── GUIA_DE_USO.md
├── GUIA_COMPLETA_SISTEMA.md
└── TODO.md
""")
