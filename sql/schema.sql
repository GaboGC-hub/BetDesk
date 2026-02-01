-- sql/schema.sql
CREATE TABLE IF NOT EXISTS alerts (
  id BIGSERIAL PRIMARY KEY,
  sport TEXT NOT NULL,
  league TEXT NOT NULL,
  event TEXT NOT NULL,
  start_time_utc TIMESTAMPTZ NOT NULL,
  market TEXT NOT NULL,
  line NUMERIC NULL,
  selection TEXT NOT NULL,
  bookmaker TEXT NOT NULL,
  odds NUMERIC NOT NULL,
  reason TEXT NOT NULL,      -- "EV" o "ANOMALY" o "TEST"
  score NUMERIC NOT NULL,    -- EV o z-score
  created_at_utc TIMESTAMPTZ NOT NULL,
  sent_at_utc TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS idx_alerts_created ON alerts(created_at_utc DESC);