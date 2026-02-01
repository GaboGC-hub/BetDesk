#!/usr/bin/env python
# setup.py
"""
Script de configuración inicial para BetDesk
Maneja la creación de tablas y verificación de dependencias
"""

import os
import sys
import subprocess


def print_header(text):
    """Imprime un header bonito"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_docker():
    """Verifica si Docker está corriendo"""
    print("🔍 Verificando Docker...")
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Docker está corriendo")
            return True
        else:
            print("⚠️  Docker no está corriendo")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️  Docker no está instalado o no está corriendo")
        return False


def start_database():
    """Intenta iniciar la base de datos con Docker"""
    print("\n🚀 Iniciando base de datos PostgreSQL...")
    
    if not check_docker():
        print("\n❌ Docker no está disponible.")
        print("\n📝 Opciones:")
        print("   1. Instala Docker Desktop desde: https://www.docker.com/products/docker-desktop")
        print("   2. Inicia Docker Desktop manualmente")
        print("   3. Usa una base de datos PostgreSQL existente")
        print("\nDespués de iniciar Docker, ejecuta:")
        print("   docker-compose up -d")
        return False
    
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Base de datos iniciada correctamente")
            return True
        else:
            print(f"⚠️  Error al iniciar base de datos: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def create_env_file():
    """Crea archivo .env si no existe"""
    print("\n📝 Verificando archivo .env...")
    
    if os.path.exists(".env"):
        print("✅ Archivo .env ya existe")
        return True
    
    print("⚠️  Archivo .env no encontrado. Creando uno de ejemplo...")
    
    env_content = """# BetDesk Configuration

# Database
DATABASE_URL=postgresql://betdesk:betdesk@localhost:5432/betdesk

# Telegram (REQUERIDO para recibir alertas)
TELEGRAM_BOT_TOKEN=8410038424:AAFQYoA-oPi1FsKWAw1rxEUY3sqqW6ZPzt4
TELEGRAM_CHAT_ID=8010809405

# Opcional: Configuración de scraping
SCRAPER_DELAY=2.0
SCRAPER_MAX_RETRIES=3
"""
    
    try:
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Archivo .env creado")
        print("\n⚠️  IMPORTANTE: Edita .env y agrega tus credenciales de Telegram")
        return True
    except Exception as e:
        print(f"❌ Error creando .env: {e}")
        return False


def create_database_tables():
    """Crea las tablas en la base de datos"""
    print("\n🗄️  Creando tablas en la base de datos...")
    
    try:
        from app.db import create_tables
        create_tables()
        return True
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        print("   Asegúrate de haber instalado las dependencias:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        print("\n💡 Posibles causas:")
        print("   1. La base de datos no está corriendo")
        print("   2. Las credenciales en .env son incorrectas")
        print("   3. PostgreSQL no está instalado")
        return False


def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "psycopg",
        "requests",
        "bs4",
        "playwright"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"⚠️  Faltan dependencias: {', '.join(missing)}")
        print("\n📝 Instala las dependencias con:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ Todas las dependencias instaladas")
    return True


def main():
    """Función principal de setup"""
    print_header("🎯 BETDESK - CONFIGURACIÓN INICIAL")
    
    # 1. Verificar dependencias
    if not check_dependencies():
        print("\n❌ Setup incompleto. Instala las dependencias primero.")
        return False
    
    # 2. Crear archivo .env
    create_env_file()
    
    # 3. Intentar iniciar base de datos
    db_started = start_database()
    
    # 4. Crear tablas (solo si la BD está corriendo)
    if db_started:
        import time
        print("\n⏳ Esperando 5 segundos para que PostgreSQL inicie...")
        time.sleep(5)
        
        if create_database_tables():
            print_header("✅ CONFIGURACIÓN COMPLETADA")
            print("\n🚀 Para iniciar BetDesk, ejecuta:")
            print("   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
            print("\n📱 Dashboard web:")
            print("   http://127.0.0.1:8000/alerts")
            print("\n📖 Para más información, lee:")
            print("   GUIA_DE_USO.md")
            return True
    else:
        print_header("⚠️  CONFIGURACIÓN PARCIAL")
        print("\n📝 Pasos pendientes:")
        print("   1. Inicia Docker Desktop")
        print("   2. Ejecuta: docker-compose up -d")
        print("   3. Ejecuta: python -c \"from app.db import create_tables; create_tables()\"")
        print("   4. Ejecuta: python -m uvicorn app.main:app --host 127.0.0.1 --port 8000")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelado por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
