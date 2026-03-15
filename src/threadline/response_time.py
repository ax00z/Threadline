from __future__ import annotations
from datetime import datetime

_MAX_GAP = 3600  # ignore gaps over 1 hour (separate conversations)


def compute_response_times(messages: list[dict]) -> dict:
    """Compute per-sender average response times and fastest responders."""
    if len(messages) < 2:
        return {"per_sender": {}, "pairs": [], "fastest": None, "slowest": None}

    sender_times: dict[str, list[float]] = {}
    pair_times: dict[tuple[str, str], list[float]] = {}

    prev = messages[0]
    prev_dt = _parse(prev.get("timestamp", ""))

    for msg in messages[1:]:
        cur_dt = _parse(msg.get("timestamp", ""))
        if prev_dt is None or cur_dt is None:
            prev, prev_dt = msg, cur_dt
            continue

        a, b = prev.get("sender", ""), msg.get("sender", "")
        if a != b:
            delta = (cur_dt - prev_dt).total_seconds()
            if 0 < delta <= _MAX_GAP:
                sender_times.setdefault(b, []).append(delta)
                key = tuple(sorted([a, b]))
                pair_times.setdefault(key, []).append(delta)

        prev, prev_dt = msg, cur_dt

    per_sender = {}
    for sender, times in sender_times.items():
        per_sender[sender] = {
            "avg_seconds": round(sum(times) / len(times), 1),
            "median_seconds": round(sorted(times)[len(times) // 2], 1),
            "min_seconds": round(min(times), 1),
            "count": len(times),
        }

    pairs = []
    for (a, b), times in pair_times.items():
        pairs.append({
            "pair": [a, b],
            "avg_seconds": round(sum(times) / len(times), 1),
            "count": len(times),
        })
    pairs.sort(key=lambda p: p["avg_seconds"])

    fastest = min(per_sender, key=lambda s: per_sender[s]["avg_seconds"]) if per_sender else None
    slowest = max(per_sender, key=lambda s: per_sender[s]["avg_seconds"]) if per_sender else None

    return {
        "per_sender": per_sender,
        "pairs": pairs,
        "fastest": fastest,
        "slowest": slowest,
    }


def _parse(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None
