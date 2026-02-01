# 🚀 INSTRUCCIONES COMPLETAS DE INICIO - BETDESK

## 🎯 Guía para Iniciar Backend + Frontend

Esta guía te explica **paso a paso** cómo configurar e iniciar tanto el backend (FastAPI) como el frontend (Next.js) del sistema BetDesk.

---

## 📋 Requisitos Previos

### ✅ Software Necesario

- **Python 3.10+** (verificar con `python --version`)
- **Node.js 18+** (verificar con `node --version`)
- **Docker Desktop** (para PostgreSQL)
- **Cuenta de Telegram** (para recibir alertas)

### ✅ Verificar Instalaciones

```bash
# Python
python --version
# Debe mostrar: Python 3.10.x o superior

# Node.js
node --version
# Debe mostrar: v18.x.x o superior

# npm (viene con Node.js)
npm --version
# Debe mostrar: 9.x.x o superior

# Docker
docker --version
# Debe mostrar: Docker version 24.x.x
```

---

## ⚙️ CONFIGURACIÓN INICIAL (5 minutos)

### Paso 1: Preparar el Proyecto

```bash
# 1. Navegar al directorio del proyecto
cd Betplay

# 2. Crear entorno virtual de Python (opcional pero recomendado)
python -m venv venv
venv\Scripts\activate  # En Windows
# source venv/bin/activate  # En Linux/Mac

# 3. Instalar dependencias del backend
pip install -r requirements.txt

# 4. Instalar dependencias del frontend
cd betting-dashboard-frontend
npm install
cd ..
```

### Paso 2: Configurar Variables de Entorno

```bash
# Crear archivo .env en la raíz del proyecto
# Copiar y pegar este contenido:

# Base de datos
DATABASE_URL=postgresql://betdesk:betdesk@localhost:5432/betdesk

# Telegram (OBLIGATORIO para alertas)
TELEGRAM_BOT_TOKEN=tu_token_de_telegram_aqui
TELEGRAM_CHAT_ID=tu_chat_id_de_telegram_aqui

# API del frontend (opcional)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**¿Cómo obtener TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID?**

```bash
# 1. Buscar @BotFather en Telegram
# 2. Enviar: /newbot
# 3. Seguir instrucciones para crear el bot
# 4. Copiar el TOKEN que te da BotFather
# 5. Buscar tu bot en Telegram y enviar: /start
# 6. Ejecutar este comando para obtener tu CHAT_ID:

curl -X GET "https://api.telegram.org/bot[TU_TOKEN]/getUpdates"
# Buscar "chat": {"id": TU_CHAT_ID}
```

### Paso 3: Iniciar Base de Datos

```bash
# 1. Abrir Docker Desktop (si no está abierto)
# 2. Esperar a que el ícono de Docker esté verde

# 3. Iniciar PostgreSQL
docker-compose up -d

# 4. Verificar que esté corriendo
docker-compose ps
# Debe mostrar: betdesk_db (Up)
```

### Paso 4: Crear Tablas de Base de Datos

```bash
# Crear todas las tablas necesarias
python -c "from app.db import create_tables; create_tables()"

# Verificar que se crearon
python -c "import psycopg; conn = psycopg.connect('host=localhost dbname=betdesk user=betdesk password=betdesk'); cur = conn.cursor(); cur.execute('SELECT table_name FROM information_schema.tables WHERE table_schema = \'public\''); print([row[0] for row in cur.fetchall()]); conn.close()"
# Debe mostrar: ['alerts', 'events', 'odds']
```

---

## 🚀 INICIO DEL SISTEMA

### Opción 1: Inicio Automático (Recomendado)

**Script de inicio automático:**

```bash
# Crear script start_system.bat (Windows)
echo off
echo Iniciando BetDesk Backend + Frontend...

REM Iniciar backend en background
start "BetDesk Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Esperar 5 segundos
timeout /t 5 /nobreak > nul

REM Iniciar frontend
cd betting-dashboard-frontend
start "BetDesk Frontend" cmd /k "npm run dev"

cd ..
echo.
echo ✅ Sistema iniciado!
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo.
pause
```

**Ejecutar:**

```bash
# Hacer doble clic en start_system.bat
# O ejecutar desde terminal:
start_system.bat
```

### Opción 2: Inicio Manual (Terminal)

**Paso 1: Iniciar Backend (Terminal 1)**

```bash
# Terminal 1 - Backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Paso 2: Iniciar Frontend (Terminal 2)**

```bash
# Terminal 2 - Frontend
cd betting-dashboard-frontend
npm run dev
```

---

## 🌐 ACCEDER AL SISTEMA

### ✅ Verificar que Todo Funciona

**1. Backend (FastAPI)**

- URL: http://127.0.0.1:8000
- Health check: http://127.0.0.1:8000/api/health
- Dashboard: http://127.0.0.1:8000/alerts

**2. Frontend (Next.js)**

- URL: http://localhost:3000
- Dashboard principal con estadísticas
- Filtros por deporte y tipo de alerta

**3. Telegram**

- Las alertas llegan automáticamente a tu chat
- Formato mejorado con emojis y detalles

### ✅ Probar Funcionalidades

**En el Frontend (http://localhost:3000):**

- ✅ Ver estadísticas generales
- ✅ Filtrar por deporte (Basketball, Football, Tennis)
- ✅ Filtrar por tipo (EV+, Anomalías)
- ✅ Ver alertas en tiempo real

**En Telegram:**

- ✅ Recibir alertas automáticamente
- ✅ Ver detalles de cada oportunidad
- ✅ Diferentes tipos de alertas (EV+, Anomalías)

---

## 🔧 CONFIGURACIÓN AVANZADA

### Ajustar Frecuencia de Jobs

```python
# Archivo: app/scheduler.py
# Cambiar estos valores según necesites:

# Basketball (cada cuánto scrapear/analizar)
sched.add_job(job_ingest_basketball, "interval", minutes=30)      # Scraping
sched.add_job(job_anomalies_basketball, "interval", minutes=2)    # Anomalías
sched.add_job(job_ev_basketball, "interval", minutes=2)           # EV

# Football
sched.add_job(job_ingest_football, "interval", minutes=45)
sched.add_job(job_anomalies_football, "interval", minutes=3)
sched.add_job(job_ev_football, "interval", minutes=5)

# Tennis
sched.add_job(job_ingest_tennis, "interval", minutes=60)
sched.add_job(job_anomalies_tennis, "interval", minutes=3)
sched.add_job(job_ev_tennis, "interval", minutes=5)
```

### Ajustar Umbrales de Detección

```python
# Archivo: app/config/sport_configs.py

SPORT_CONFIGS = {
    "basketball": {
        "NBA": {
            "anomaly_z_threshold": 1.2,  # Más bajo = más alertas de anomalías
            "ev_threshold": 0.02,         # 2% EV mínimo
            "min_bookmakers": 2,
        }
    },
    "football": {
        "Premier League": {
            "anomaly_z_threshold": 1.5,
            "ev_threshold": 0.03,         # 3% EV mínimo
            "min_bookmakers": 3,
        }
    }
}
```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### Problema 1: "Error de hidratación React"

**✅ YA SOLUCIONADO** - Se arregló usando dynamic imports para el componente Target.

### Problema 2: "No se puede conectar a la base de datos"

```bash
# Verificar que Docker esté corriendo
docker-compose ps

# Si no está corriendo:
docker-compose up -d

# Reiniciar contenedor si es necesario:
docker-compose restart
```

### Problema 3: "No recibo alertas en Telegram"

```bash
# Verificar configuración de Telegram
cat .env

# Probar envío manual
python -c "from app.telegram import send_telegram; send_telegram('Test message')"

# Verificar que el bot esté iniciado (/start en Telegram)
```

### Problema 4: "Frontend no carga"

```bash
# Verificar que el backend esté corriendo
curl http://127.0.0.1:8000/api/health

# Reiniciar frontend
cd betting-dashboard-frontend
rm -rf .next
npm run dev
```

### Problema 5: "Demasiadas/Pocas alertas"

```python
# Ajustar umbrales en app/config/sport_configs.py
# Subir valores = menos alertas
# Bajar valores = más alertas
```

---

## 📊 MONITOREO DEL SISTEMA

### Ver Logs en Tiempo Real

```bash
# Los logs se muestran en la terminal del backend
# Buscar por tipo:

# ✅ = Éxito (scraping completado, alerta enviada)
# ⚠️  = Advertencia (fallback a datos mock)
# ❌ = Error (problema de conexión)
# 🔍 = Scraping (eventos encontrados)
# 📊 = Análisis (EV calculado)
# 🚨 = Alerta (enviada a Telegram)
```

### Verificar Estado de Jobs

```python
# En Python REPL
from app.scheduler import start_scheduler
# Los jobs se muestran automáticamente al iniciar
```

### Ver Estadísticas de la BD

```python
# Ver cantidad de alertas
python -c "import psycopg; conn = psycopg.connect('host=localhost dbname=betdesk user=betdesk password=betdesk'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM alerts'); print(f'Alertas: {cur.fetchone()[0]}'); cur.execute('SELECT COUNT(*) FROM events'); print(f'Eventos: {cur.fetchone()[0]}'); cur.execute('SELECT COUNT(*) FROM odds'); print(f'Cuotas: {cur.fetchone()[0]}'); conn.close()"
```

---

## 🎯 RESUMEN RÁPIDO DE INICIO

```bash
# 1. Verificar requisitos
python --version  # 3.10+
node --version    # 18+
docker --version  # 24+

# 2. Preparar proyecto
cd Betplay
pip install -r requirements.txt
cd betting-dashboard-frontend && npm install && cd ..

# 3. Configurar .env
# Crear archivo con TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID

# 4. Iniciar base de datos
docker-compose up -d

# 5. Crear tablas
python -c "from app.db import create_tables; create_tables()"

# 6. Iniciar sistema
# Terminal 1 - Backend:
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 - Frontend:
cd betting-dashboard-frontend && npm run dev

# 7. Acceder
# Backend: http://127.0.0.1:8000
# Frontend: http://localhost:3000
# Telegram: Alertas automáticas
```

---

## 🎉 ¡LISTO PARA USAR!

**El sistema BetDesk está completamente configurado y funcionando:**

- ✅ **Backend FastAPI** corriendo en puerto 8000
- ✅ **Frontend Next.js** corriendo en puerto 3000
- ✅ **Base de datos PostgreSQL** con Docker
- ✅ **Telegram Bot** configurado para alertas
- ✅ **10 jobs automáticos** ejecutándose
- ✅ **7 módulos de IA** para análisis avanzado

**¡Empieza a recibir alertas de oportunidades de apuestas automáticamente!**

---

**Versión:** 1.0
**Última actualización:** Enero 2025
**Estado:** ✅ **COMPLETAMENTE FUNCIONAL**
