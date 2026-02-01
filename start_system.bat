@echo off
echo ========================================
echo  INICIANDO SISTEMA BETDESK
echo ========================================
echo.

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo Por favor instala Python 3.10+ desde https://python.org
    pause
    exit /b 1
)

REM Verificar que Node.js esté instalado
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js no está instalado o no está en el PATH
    echo Por favor instala Node.js 18+ desde https://nodejs.org
    pause
    exit /b 1
)

REM Verificar que Docker esté corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Docker no está corriendo
    echo 1. Abre Docker Desktop
    echo 2. Espera a que el ícono esté verde
    echo 3. Vuelve a ejecutar este script
    pause
    exit /b 1
)

echo ✅ Verificaciones completadas
echo.

REM Verificar que existe el archivo .env
if not exist ".env" (
    echo ⚠️  ADVERTENCIA: No se encontró archivo .env
    echo Creando archivo .env básico...
    echo.
    echo # Configuración básica - EDITA ESTOS VALORES:
    echo DATABASE_URL=postgresql://betdesk:betdesk@localhost:5432/betdesk
    echo.
    echo # Telegram (OBLIGATORIO para alertas)
    echo TELEGRAM_BOT_TOKEN=tu_token_aqui
    echo TELEGRAM_CHAT_ID=tu_chat_id_aqui
    echo.
    echo # API del frontend
    echo NEXT_PUBLIC_API_URL=http://localhost:8000
    echo.
    echo Por favor edita el archivo .env con tus valores reales antes de continuar.
    pause
    exit /b 1
)

echo ✅ Archivo .env encontrado
echo.

REM Verificar que la base de datos esté corriendo
echo 🔍 Verificando base de datos...
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo 📦 Iniciando base de datos...
    docker-compose up -d
    timeout /t 10 /nobreak >nul
)

docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ❌ ERROR: No se pudo iniciar la base de datos
    echo Revisa que Docker esté funcionando correctamente
    pause
    exit /b 1
)

echo ✅ Base de datos corriendo
echo.

REM Crear tablas si no existen
echo 🏗️  Verificando tablas de base de datos...
python -c "from app.db import create_tables; create_tables()" 2>nul
if errorlevel 1 (
    echo ❌ ERROR: No se pudieron crear las tablas
    echo Revisa la configuración de la base de datos
    pause
    exit /b 1
)

echo ✅ Tablas de base de datos listas
echo.

REM Instalar dependencias del backend si no están instaladas
if not exist "venv" (
    echo 📦 Creando entorno virtual...
    python -m venv venv
)

echo 📦 Activando entorno virtual...
call venv\Scripts\activate.bat

echo 📦 Instalando dependencias del backend...
pip install -r requirements.txt >nul 2>&1

REM Instalar dependencias del frontend si no están instaladas
if not exist "betting-dashboard-frontend\node_modules" (
    echo 📦 Instalando dependencias del frontend...
    cd betting-dashboard-frontend
    npm install >nul 2>&1
    cd ..
)

echo ✅ Dependencias instaladas
echo.

echo ========================================
echo 🎯 INICIANDO SERVICIOS
echo ========================================
echo.

REM Iniciar backend en una nueva ventana
echo 🚀 Iniciando backend (FastAPI)...
start "BetDesk Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Esperar 5 segundos para que el backend inicie
echo ⏳ Esperando que el backend inicie...
timeout /t 5 /nobreak >nul

REM Verificar que el backend esté respondiendo
echo 🔍 Verificando backend...
curl -s http://127.0.0.1:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  ADVERTENCIA: El backend no responde aún, puede tardar unos segundos en iniciar
) else (
    echo ✅ Backend funcionando en http://127.0.0.1:8000
)

echo.

REM Iniciar frontend en una nueva ventana
echo 🚀 Iniciando frontend (Next.js)...
start "BetDesk Frontend" cmd /k "cd betting-dashboard-frontend && npm run dev"

REM Esperar 3 segundos para que el frontend inicie
echo ⏳ Esperando que el frontend inicie...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo 🎉 ¡SISTEMA INICIADO EXITOSAMENTE!
echo ========================================
echo.
echo 🌐 URLs de acceso:
echo    📊 Backend (API):     http://127.0.0.1:8000
echo    🎨 Frontend (UI):     http://localhost:3000
echo    📱 Telegram:         Alertas automáticas
echo.
echo 📋 Funcionalidades activas:
echo    ✅ 10 jobs automáticos ejecutándose
echo    ✅ Scraping de Flashscore cada 30-60 min
echo    ✅ Análisis de cuotas cada 2-5 min
echo    ✅ Alertas EV+ y anomalías
echo    ✅ Dashboard web en tiempo real
echo.
echo 🛑 Para detener el sistema:
echo    1. Cierra las ventanas de terminal
echo    2. Ejecuta: docker-compose down
echo.
echo 📖 Para más información: INSTRUCCIONES_INICIO_COMPLETO.md
echo.

pause
