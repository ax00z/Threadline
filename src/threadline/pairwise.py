from __future__ import annotations

from collections import Counter
from datetime import datetime


def compute_pairwise(
    messages: list[dict],
    reply_window_secs: int = 300,
) -> list[dict]:
    pairs: dict[tuple[str, str], dict] = {}

    # Pre-parse all timestamps once
    parsed_ts: list[datetime | None] = []
    for m in messages:
        try:
            parsed_ts.append(datetime.fromisoformat(m["timestamp"]))
        except (ValueError, TypeError, KeyError):
            parsed_ts.append(None)

    for i in range(len(messages) - 1):
        a = messages[i]["sender"]
        b = messages[i + 1]["sender"]
        if a == b:
            continue

        ta, tb = parsed_ts[i], parsed_ts[i + 1]
        if ta is not None and tb is not None:
            if abs((tb - ta).total_seconds()) > reply_window_secs:
                continue

        key = tuple(sorted([a, b]))
        ts = messages[i + 1]["timestamp"]
        date_str = ts[:10]

        if key not in pairs:
            pairs[key] = {
                "pair": list(key),
                "first_contact": ts,
                "last_contact": ts,
                "message_count": 0,
                "daily_counts": Counter(),
            }

        p = pairs[key]
        p["message_count"] += 1
        p["last_contact"] = ts
        p["daily_counts"][date_str] += 1

    result = []
    for p in pairs.values():
        try:
            first = datetime.fromisoformat(p["first_contact"])
            last = datetime.fromisoformat(p["last_contact"])
            duration = max(1, (last - first).days + 1)
        except (ValueError, TypeError):
            duration = 1

        result.append({
            "pair": p["pair"],
            "first_contact": p["first_contact"],
            "last_contact": p["last_contact"],
            "message_count": p["message_count"],
            "duration_days": duration,
            "daily_counts": dict(p["daily_counts"]),
        })

    result.sort(key=lambda x: x["message_count"], reverse=True)
    return result
