CREATE TABLE IF NOT EXISTS events (
  id BIGSERIAL PRIMARY KEY,
  sport TEXT NOT NULL,
  league TEXT NOT NULL,
  start_time_utc TIMESTAMPTZ NOT NULL,
  home TEXT,
  away TEXT,
  flashscore_url TEXT UNIQUE,
  status TEXT DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS odds (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT REFERENCES events(id) ON DELETE CASCADE,
  market TEXT NOT NULL,          -- "TOTAL" | "SPREAD" | "ML" | etc.
  line NUMERIC NULL,             -- ej. 228.5, -4.5, etc.
  bookmaker TEXT NOT NULL,
  selection TEXT NOT NULL,       -- "HOME"|"AWAY"|"OVER"|"UNDER"
  odds NUMERIC NOT NULL,
  captured_at_utc TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_odds_event_market_line_time
ON odds(event_id, market, line, captured_at_utc);

-- Tabla de estadísticas por equipo
CREATE TABLE IF NOT EXISTS team_stats (
    id SERIAL PRIMARY KEY,
    team VARCHAR(200) NOT NULL,
    league VARCHAR(100) NOT NULL,
    season VARCHAR(20),
    points_mean DECIMAL(10,2),
    points_std DECIMAL(10,2),
    total_mean DECIMAL(10,2),
    total_std DECIMAL(10,2),
    games_analyzed INT,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(team, league, season)
);

-- Tabla de resultados de partidos
CREATE TABLE IF NOT EXISTS game_results (
    id SERIAL PRIMARY KEY,
    sport VARCHAR(50),
    league VARCHAR(100),
    home_team VARCHAR(200),
    away_team VARCHAR(200),
    home_score INT,
    away_score INT,
    game_date TIMESTAMPTZ,
    UNIQUE(sport, league, home_team, away_team, game_date)
);
