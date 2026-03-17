from __future__ import annotations


def _empty_result():
    return {
        "available": False,
        "overall": {"positive": 0.0, "negative": 0.0, "neutral": 0.0, "compound": 0.0},
        "per_sender": {},
        "timeline": [],
        "extremes": {"most_positive": None, "most_negative": None},
        "shifts": [],
    }


def analyze_sentiment(messages: list[dict]) -> dict:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        return _empty_result()

    if not messages:
        return {
            "available": True,
            "overall": {"positive": 0.0, "negative": 0.0, "neutral": 0.0, "compound": 0.0},
            "per_sender": {},
            "timeline": [],
            "extremes": {"most_positive": None, "most_negative": None},
            "shifts": [],
        }

    sia = SentimentIntensityAnalyzer()

    # For large datasets, score all messages but cache short/empty body results
    scored: list[dict] = []
    _cache: dict[str, dict] = {}
    for msg in messages:
        body = msg.get("body", "")
        if body in _cache:
            scores = _cache[body]
        else:
            scores = sia.polarity_scores(body)
            if len(body) < 100:  # cache short messages (likely repeated)
                _cache[body] = scores
        scored.append({
            "sender": msg.get("sender", ""),
            "timestamp": msg.get("timestamp", ""),
            "body": body,
            **scores,
        })

    n = len(scored)
    if n == 0:
        return {**_empty_result(), "available": True}

    overall = {
        "positive": sum(s["pos"] for s in scored) / n,
        "negative": sum(s["neg"] for s in scored) / n,
        "neutral": sum(s["neu"] for s in scored) / n,
        "compound": sum(s["compound"] for s in scored) / n,
    }

    # per-sender
    sender_buckets: dict[str, list[dict]] = {}
    for s in scored:
        sender_buckets.setdefault(s["sender"], []).append(s)

    per_sender = {}
    for sender, items in sender_buckets.items():
        c = len(items)
        per_sender[sender] = {
            "positive": sum(i["pos"] for i in items) / c,
            "negative": sum(i["neg"] for i in items) / c,
            "neutral": sum(i["neu"] for i in items) / c,
            "compound": sum(i["compound"] for i in items) / c,
            "message_count": c,
        }

    # timeline (sample if >500)
    step = max(1, n // 500)
    timeline = [
        {"timestamp": scored[i]["timestamp"], "compound": scored[i]["compound"], "sender": scored[i]["sender"]}
        for i in range(0, n, step)
    ]

    # extremes
    most_pos = max(scored, key=lambda s: s["compound"])
    most_neg = min(scored, key=lambda s: s["compound"])
    extremes = {
        "most_positive": {"body": most_pos["body"], "sender": most_pos["sender"],
                          "timestamp": most_pos["timestamp"], "compound": most_pos["compound"]},
        "most_negative": {"body": most_neg["body"], "sender": most_neg["sender"],
                          "timestamp": most_neg["timestamp"], "compound": most_neg["compound"]},
    }

    # shifts — compound change >0.5 within 5 messages from same sender
    shifts: list[dict] = []
    sender_history: dict[str, list[dict]] = {}
    for s in scored:
        name = s["sender"]
        hist = sender_history.setdefault(name, [])
        hist.append(s)
        if len(hist) >= 2:
            window = hist[-5:]
            for prev in window[:-1]:
                delta = s["compound"] - prev["compound"]
                if abs(delta) > 0.5:
                    direction = "positive" if delta > 0 else "negative"
                    shifts.append({
                        "timestamp": s["timestamp"],
                        "sender": name,
                        "description": f"sentiment shift {direction} ({delta:+.2f})",
                        "magnitude": round(abs(delta), 3),
                    })
                    break

    return {
        "available": True,
        "overall": overall,
        "per_sender": per_sender,
        "timeline": timeline,
        "extremes": extremes,
        "shifts": shifts,
    }
