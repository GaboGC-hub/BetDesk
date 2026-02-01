# app/crud.py
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import text
from .db import SessionLocal


# -----------------------
# Alerts (dashboard)
# -----------------------
def get_latest_alerts(limit: int = 200, sport: str = None, market: str = None) -> list[dict]:
    """
    Obtiene alertas recientes con filtros opcionales
    
    Args:
        limit: Número máximo de alertas
        sport: Filtro opcional por deporte
        market: Filtro opcional por mercado
    
    Returns:
        Lista de dicts con alertas
    """
    conditions = []
    params = {"limit": limit}
    
    if sport:
        conditions.append("sport = :sport")
        params["sport"] = sport
    
    if market:
        conditions.append("market = :market")
        params["market"] = market
    
    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
    
    sql = text(f"""
        SELECT id, sport, league, event, start_time_utc, market, line, selection,
               bookmaker, odds, reason, score, created_at_utc, sent_at_utc
        FROM alerts
        {where_clause}
        ORDER BY created_at_utc DESC
        LIMIT :limit
    """)
    
    with SessionLocal() as db:
        rows = db.execute(sql, params).mappings().all()
        return [dict(r) for r in rows]


def mark_sent(alert_id: int) -> None:
    if not alert_id:
        return
    sql = text("UPDATE alerts SET sent_at_utc = now() WHERE id = :id")
    with SessionLocal() as db:
        db.execute(sql, {"id": alert_id})
        db.commit()


def create_alert_ev(row: dict, ev: float) -> int:
    """
    Crea alerta EV. Devuelve id o 0 si fue dedupeado por ON CONFLICT.
    Requiere que exista un índice UNIQUE para que ON CONFLICT DO NOTHING sea útil.
    """
    now = datetime.now(timezone.utc)
    event_name = f"{row.get('home','')} vs {row.get('away','')}".strip()

    sql = text("""
      INSERT INTO alerts (
        sport, league, event, start_time_utc, market, line, selection,
        bookmaker, odds, reason, score, created_at_utc, sent_at_utc
      )
      VALUES (
        :sport, :league, :event, :start_time_utc, :market, :line, :selection,
        :bookmaker, :odds, 'EV', :score, :created_at_utc, NULL
      )
      ON CONFLICT DO NOTHING
      RETURNING id
    """)

    with SessionLocal() as db:
        res = db.execute(sql, {
            "sport": row["sport"],
            "league": row["league"],
            "event": event_name,
            "start_time_utc": row["start_time_utc"],
            "market": row["market"],
            "line": row["line"],
            "selection": row["selection"],
            "bookmaker": row["bookmaker"],
            "odds": row["odds"],
            "score": float(ev),
            "created_at_utc": now,
        }).scalar()
        db.commit()
        return int(res) if res is not None else 0


def create_alert_from_anomaly(row: dict, score: float) -> int:
    now = datetime.now(timezone.utc)
    event_name = f"{row.get('home','')} vs {row.get('away','')}".strip()

    sql = text("""
      INSERT INTO alerts (
        sport, league, event, start_time_utc, market, line, selection,
        bookmaker, odds, reason, score, created_at_utc, sent_at_utc
      )
      VALUES (
        :sport, :league, :event, :start_time_utc, :market, :line, :selection,
        :bookmaker, :odds, 'ANOMALY', :score, :created_at_utc, NULL
      )
      ON CONFLICT DO NOTHING
      RETURNING id
    """)

    with SessionLocal() as db:
        res = db.execute(sql, {
            "sport": row["sport"],
            "league": row["league"],
            "event": event_name,
            "start_time_utc": row["start_time_utc"],
            "market": row["market"],
            "line": row["line"],
            "selection": row["selection"],
            "bookmaker": row["bookmaker"],
            "odds": row["odds"],
            "score": float(score),
            "created_at_utc": now,
        }).scalar()
        db.commit()
        return int(res) if res is not None else 0


# -----------------------
# Events / Odds ingestion
# -----------------------
def upsert_event(event: dict) -> int:
    sql = text("""
      INSERT INTO events (sport, league, start_time_utc, home, away, flashscore_url, status)
      VALUES (:sport, :league, :start_time_utc, :home, :away, :flashscore_url, 'scheduled')
      ON CONFLICT (flashscore_url) DO UPDATE
      SET start_time_utc = EXCLUDED.start_time_utc,
          home = EXCLUDED.home,
          away = EXCLUDED.away,
          league = EXCLUDED.league
      RETURNING id
    """)
    with SessionLocal() as db:
        event_id = db.execute(sql, event).scalar_one()
        db.commit()
        return int(event_id)


def insert_odds(event_id: int, rows: list[dict]) -> None:
    sql = text("""
      INSERT INTO odds (event_id, market, line, bookmaker, selection, odds, captured_at_utc)
      VALUES (:event_id, :market, :line, :bookmaker, :selection, :odds, :captured_at_utc)
    """)
    with SessionLocal() as db:
        for r in rows:
            db.execute(sql, {"event_id": event_id, **r})
        db.commit()


def fetch_latest_odds_snapshot(minutes: int = 10, sport: str = None) -> list[dict]:
    """
    Obtiene snapshot de odds recientes, opcionalmente filtrado por deporte
    
    Args:
        minutes: Ventana de tiempo en minutos
        sport: Filtro opcional por deporte ("basketball", "football", "tennis")
    
    Returns:
        Lista de dicts con odds y metadata del evento
    """
    if sport:
        sql = text("""
          SELECT e.id as event_id, e.sport, e.league, e.home, e.away, e.start_time_utc,
                 o.market, o.line, o.bookmaker, o.selection, o.odds, o.captured_at_utc
          FROM odds o
          JOIN events e ON e.id = o.event_id
          WHERE o.captured_at_utc >= (now() AT TIME ZONE 'utc') - (:mins || ' minutes')::interval
            AND e.sport = :sport
        """)
        with SessionLocal() as db:
            rows = db.execute(sql, {"mins": minutes, "sport": sport}).mappings().all()
            return [dict(r) for r in rows]
    else:
        sql = text("""
          SELECT e.id as event_id, e.sport, e.league, e.home, e.away, e.start_time_utc,
                 o.market, o.line, o.bookmaker, o.selection, o.odds, o.captured_at_utc
          FROM odds o
          JOIN events e ON e.id = o.event_id
          WHERE o.captured_at_utc >= (now() AT TIME ZONE 'utc') - (:mins || ' minutes')::interval
        """)
        with SessionLocal() as db:
            rows = db.execute(sql, {"mins": minutes}).mappings().all()
            return [dict(r) for r in rows]
