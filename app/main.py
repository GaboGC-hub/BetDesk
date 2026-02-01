#app/main.py
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import FastAPI, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from typing import Optional
import logging
import psycopg2 as psycopg

from .security import require_basic_auth
from .crud import get_latest_alerts
from .scheduler import start_scheduler

load_dotenv()

logger = logging.getLogger("betdesk")
BOGOTA = ZoneInfo("America/Bogota")
templates = Jinja2Templates(directory="templates")


def get_db_connection():
    """Obtiene una conexión a la base de datos usando psycopg"""
    import os
    db_url = os.environ.get("DATABASE_URL", "postgresql://betdesk:betdesk@localhost:5432/betdesk")
    return psycopg.connect("host=localhost dbname=betdesk user=betdesk password=betdesk")


app = FastAPI(
    title="BetDesk API",
    description="Sistema de análisis de apuestas deportivas",
    version="1.0.0"
)

# Configurar CORS para permitir requests desde Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev
        "http://127.0.0.1:3000",
        "http://localhost:8000",  # FastAPI
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup():
    start_scheduler()


# ============================================================================
# API ENDPOINTS PARA FRONTEND NEXT.JS
# ============================================================================

@app.get("/api/health")
async def api_health_check():
    """Health check endpoint para el frontend"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/stats")
async def get_stats():
    """Obtiene estadísticas generales del sistema"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total de alertas
        cur.execute("SELECT COUNT(*) FROM alerts")
        total_alertas = cur.fetchone()[0]
        
        # Alertas por tipo (aproximado basado en mensaje)
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE message LIKE '%EV+%') as ev_alerts,
                COUNT(*) FILTER (WHERE message LIKE '%ANOMALÍA%' OR message LIKE '%ANOMALIA%') as anomaly_alerts
            FROM alerts
        """)
        result = cur.fetchone()
        alertas_ev = result[0] if result else 0
        anomalias = result[1] if result else 0
        
        # Alertas enviadas (todas las que están en la tabla)
        enviadas = total_alertas
        
        cur.close()
        conn.close()
        
        return {
            "totalAlertas": total_alertas,
            "alertasEV": alertas_ev,
            "anomalias": anomalias,
            "enviadas": enviadas,
            "lastUpdate": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "totalAlertas": 0,
            "alertasEV": 0,
            "anomalias": 0,
            "enviadas": 0,
            "lastUpdate": datetime.utcnow().isoformat()
        }


@app.get("/api/alerts")
async def get_alerts_api(
    sport: Optional[str] = None,
    alert_type: Optional[str] = None,
    limit: int = 50
):
    """
    Obtiene alertas recientes
    
    Query params:
    - sport: basketball, football, tennis (opcional)
    - alert_type: ev+, anomalia (opcional)
    - limit: número máximo de alertas (default: 50)
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Construir query con filtros
        query = """
            SELECT 
                id,
                sport,
                league,
                event,
                market,
                line,
                selection,
                odds,
                bookmaker,
                message,
                created_at,
                start_time_utc
            FROM alerts
            WHERE 1=1
        """
        params = []
        
        if sport:
            query += " AND LOWER(sport) = LOWER(%s)"
            params.append(sport)
        
        if alert_type:
            if alert_type.lower() == "ev+":
                query += " AND message LIKE %s"
                params.append("%EV+%")
            elif alert_type.lower() == "anomalia":
                query += " AND (message LIKE %s OR message LIKE %s)"
                params.extend(["%ANOMALÍA%", "%ANOMALIA%"])
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        alerts = []
        for row in rows:
            # Determinar tipo de alerta basado en el mensaje
            alert_type_detected = "ev+" if "EV+" in row[9] else "anomalia"
            
            # Extraer EV del mensaje si existe
            ev_value = 0
            if "EV:" in row[9]:
                try:
                    ev_str = row[9].split("EV:")[1].split("%")[0].strip()
                    ev_value = float(ev_str.replace("+", ""))
                except:
                    ev_value = 0
            
            alerts.append({
                "id": str(row[0]),
                "sport": row[1],
                "league": row[2],
                "match": row[3],
                "market": row[4],
                "line": row[5],
                "selection": row[6],
                "odds": float(row[7]) if row[7] else 0,
                "bookmaker": row[8],
                "message": row[9],
                "type": alert_type_detected,
                "ev": ev_value,
                "timestamp": row[10].isoformat() if row[10] else None,
                "startTime": row[11].isoformat() if row[11] else None
            })
        
        cur.close()
        conn.close()
        
        return {
            "alerts": alerts,
            "total": len(alerts),
            "filters": {
                "sport": sport,
                "type": alert_type,
                "limit": limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return {
            "alerts": [],
            "total": 0,
            "error": str(e)
        }


@app.get("/api/sports")
async def get_sports():
    """Obtiene lista de deportes disponibles"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT DISTINCT sport, COUNT(*) as count
            FROM alerts
            GROUP BY sport
            ORDER BY count DESC
        """)
        
        sports = []
        for row in cur.fetchall():
            sports.append({
                "name": row[0],
                "count": row[1]
            })
        
        cur.close()
        conn.close()
        
        return {"sports": sports}
    except Exception as e:
        logger.error(f"Error getting sports: {e}")
        return {"sports": []}


# ============================================================================
# RUTAS HTML ORIGINALES (para compatibilidad)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request, _: None = Depends(require_basic_auth)):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request, _: None = Depends(require_basic_auth)):
    alerts = get_latest_alerts(200)

    # Convertir fecha a string en Cali para mostrar
    for a in alerts:
        dt = a["start_time_utc"]
        if isinstance(dt, datetime):
            a["start_time_cali"] = dt.astimezone(BOGOTA).strftime("%Y-%m-%d %H:%M")
        else:
            a["start_time_cali"] = str(dt)

    return templates.TemplateResponse("dashboard.html", {"request": request, "alerts": alerts})


@app.get("/health")
def health():
    return {"status": "ok"}
