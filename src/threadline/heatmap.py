from __future__ import annotations
from datetime import datetime


def build_heatmap(messages: list[dict]) -> dict:
    """Build an hour-of-day x day-of-week activity matrix."""
    # 7 rows (Mon=0..Sun=6) x 24 cols (0..23)
    matrix = [[0] * 24 for _ in range(7)]
    per_sender: dict[str, list[list[int]]] = {}

    for msg in messages:
        try:
            dt = datetime.fromisoformat(msg["timestamp"])
        except (ValueError, KeyError):
            continue
        dow = dt.weekday()
        hour = dt.hour
        matrix[dow][hour] += 1

        sender = msg.get("sender", "")
        if sender not in per_sender:
            per_sender[sender] = [[0] * 24 for _ in range(7)]
        per_sender[sender][dow][hour] += 1

    peak_dow, peak_hour, peak_count = 0, 0, 0
    for d in range(7):
        for h in range(24):
            if matrix[d][h] > peak_count:
                peak_dow, peak_hour, peak_count = d, h, matrix[d][h]

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return {
        "matrix": matrix,
        "per_sender": per_sender,
        "peak": {
            "day": day_names[peak_dow],
            "hour": peak_hour,
            "count": peak_count,
        },
        "day_labels": day_names,
    }
