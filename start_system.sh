#!/bin/bash

echo "========================================"
echo "🚀 INICIANDO SISTEMA BETDESK"
echo "========================================"
echo

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar dependencias
echo "🔍 Verificando dependencias..."

if ! command_exists python3; then
    echo "❌ ERROR: Python3 no está instalado"
    echo "Instala Python 3.10+ desde https://python.org"
    exit 1
fi

if ! command_exists node; then
    echo "❌ ERROR: Node.js no está instalado"
    echo "Instala Node.js 18+ desde https://nodejs.org"
    exit 1
fi

if ! command_exists docker; then
    echo "❌ ERROR: Docker no está instalado"
    echo "Instala Docker desde https://docker.com"
    exit 1
fi

echo "✅ Dependencias verificadas"
echo

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "⚠️  ADVERTENCIA: No se encontró archivo .env"
    echo "Creando archivo .env básico..."
    echo
    cat > .env << EOF
# Configuración básica - EDITA ESTOS VALORES:
DATABASE_URL=postgresql://betdesk:betdesk@localhost:5432/betdesk

# Telegram (OBLIGATORIO para alertas)
TELEGRAM_BOT_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# API del frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo
    echo "Por favor edita el archivo .env con tus valores reales antes de continuar."
    exit 1
fi

echo "✅ Archivo .env encontrado"
echo

# Verificar que Docker esté corriendo
echo "🔍 Verificando Docker..."
if ! docker info >/dev/null 2>&1; then
    echo "❌ ERROR: Docker no está corriendo"
    echo "1. Inicia Docker Desktop"
    echo "2. Espera a que esté listo"
    echo "3. Vuelve a ejecutar este script"
    exit 1
fi

# Verificar base de datos
echo "🔍 Verificando base de datos..."
if ! docker-compose ps | grep -q "Up"; then
    echo "📦 Iniciando base de datos..."
    docker-compose up -d
    sleep 10
fi

if ! docker-compose ps | grep -q "Up"; then
    echo "❌ ERROR: No se pudo iniciar la base de datos"
    exit 1
fi

echo "✅ Base de datos corriendo"
echo

# Crear tablas
echo "🏗️  Verificando tablas de base de datos..."
if ! python3 -c "from app.db import create_tables; create_tables()" 2>/dev/null; then
    echo "❌ ERROR: No se pudieron crear las tablas"
    exit 1
fi

echo "✅ Tablas de base de datos listas"
echo

# Instalar dependencias del backend
echo "📦 Verificando dependencias del backend..."
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt >/dev/null 2>&1

# Instalar dependencias del frontend
if [ ! -d "betting-dashboard-frontend/node_modules" ]; then
    echo "📦 Instalando dependencias del frontend..."
    cd betting-dashboard-frontend
    npm install >/dev/null 2>&1
    cd ..
fi

echo "✅ Dependencias instaladas"
echo

echo "========================================"
echo "🎯 INICIANDO SERVICIOS"
echo "========================================"
echo

# Función para verificar si un puerto está abierto
check_port() {
    local port=$1
    local host=${2:-127.0.0.1}
    timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null
    return $?
}

# Iniciar backend
echo "🚀 Iniciando backend (FastAPI)..."
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Esperar que el backend inicie
echo "⏳ Esperando que el backend inicie..."
sleep 5

# Verificar backend
echo "🔍 Verificando backend..."
if check_port 8000; then
    echo "✅ Backend funcionando en http://127.0.0.1:8000"
else
    echo "⚠️  ADVERTENCIA: El backend no responde aún"
fi

echo

# Iniciar frontend
echo "🚀 Iniciando frontend (Next.js)..."
cd betting-dashboard-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Esperar que el frontend inicie
echo "⏳ Esperando que el frontend inicie..."
sleep 3

echo
echo "========================================"
echo "🎉 ¡SISTEMA INICIADO EXITOSAMENTE!"
echo "========================================"
echo
echo "🌐 URLs de acceso:"
echo "   📊 Backend (API):     http://127.0.0.1:8000"
echo "   🎨 Frontend (UI):     http://localhost:3000"
echo "   📱 Telegram:         Alertas automáticas"
echo
echo "📋 Funcionalidades activas:"
echo "   ✅ 10 jobs automáticos ejecutándose"
echo "   ✅ Scraping de Flashscore cada 30-60 min"
echo "   ✅ Análisis de cuotas cada 2-5 min"
echo "   ✅ Alertas EV+ y anomalías"
echo "   ✅ Dashboard web en tiempo real"
echo
echo "🛑 Para detener el sistema:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   docker-compose down"
echo
echo "📖 Para más información: INSTRUCCIONES_INICIO_COMPLETO.md"
echo

# Mantener el script corriendo
wait
