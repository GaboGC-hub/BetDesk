-- Evita duplicar la misma alerta en un corto periodo:
-- (mismo evento+mercado+línea+selección+book+odds+reason)
CREATE UNIQUE INDEX IF NOT EXISTS uq_alert_dedupe
ON alerts (event, market, line, selection, bookmaker, odds, reason);