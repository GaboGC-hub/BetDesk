# app/decision/anomaly.py
import math
from collections import defaultdict

def mean(xs): return sum(xs) / len(xs)

def stdev(xs):
    m = mean(xs)
    v = sum((x - m) ** 2 for x in xs) / (len(xs) - 1) if len(xs) > 1 else 0.0
    return math.sqrt(v)

def detect_anomalies(rows: list[dict], z_threshold: float = 3.0, min_books: int = 3) -> list[tuple[dict, float]]:
    """
    rows: lista de odds recientes con keys:
      event_id, market, line, selection, bookmaker, odds, ...
    Devuelve: [(row_outlier, zscore), ...]
    """
    groups = defaultdict(list)
    for r in rows:
        key = (r["event_id"], r["market"], float(r["line"]) if r["line"] is not None else None, r["selection"])
        groups[key].append(r)

    out = []
    for key, items in groups.items():
        if len(items) < min_books:
            continue

        # Prob implícita aproximada (sin desvigar aquí, MVP)
        ps = [1.0 / float(i["odds"]) for i in items if float(i["odds"]) > 1.0]
        if len(ps) < min_books:
            continue

        m = mean(ps)
        s = stdev(ps)
        if s <= 1e-9:
            continue

        for it in items:
            p = 1.0 / float(it["odds"])
            z = (p - m) / s
            # Queremos "mejor cuota" => menor p implícita (más alta cuota) suele ser outlier negativo
            if abs(z) >= z_threshold:
                out.append((it, float(z)))

    return out