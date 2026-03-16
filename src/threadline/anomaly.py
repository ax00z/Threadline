from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass(slots=True)
class Anomaly:
    kind: str       # burst | off_hours | new_contact | keyword_cluster
    severity: str   # high | medium | low
    timestamp: str
    description: str
    message_indices: list[int]
    actors: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


_SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def detect_bursts(
    messages: list[dict],
    window_minutes: int = 30,
    threshold_factor: float = 3.0,
    min_absolute: int = 10,
) -> list[Anomaly]:
    if len(messages) < min_absolute:
        return []

    buckets: dict[str, list[int]] = {}
    for msg in messages:
        ts = msg.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            continue
        # bucket key: truncate to window
        mins = (dt.hour * 60 + dt.minute) // window_minutes * window_minutes
        key = f"{dt.date()}T{mins // 60:02d}:{mins % 60:02d}"
        if key not in buckets:
            buckets[key] = []
        idx = msg.get("chain_index", msg.get("line_number", 0))
        buckets[key].append(idx)

    if not buckets:
        return []

    avg = len(messages) / len(buckets)
    threshold = max(avg * threshold_factor, min_absolute)

    anomalies = []
    for key, indices in buckets.items():
        count = len(indices)
        if count >= threshold:
            senders = list({messages[i]["sender"] for i in indices if i < len(messages)})
            anomalies.append(Anomaly(
                kind="burst",
                severity="high" if count >= threshold * 2 else "medium",
                timestamp=key,
                description=f"{count} messages in {window_minutes}min window (avg {avg:.0f})",
                message_indices=indices,
                actors=sorted(senders),
            ))
    return anomalies


def detect_off_hours(
    messages: list[dict],
    start_hour: int = 1,
    end_hour: int = 5,
) -> list[Anomaly]:
    flagged: list[dict] = []
    for msg in messages:
        ts = msg.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            continue
        hour = dt.hour
        if start_hour <= end_hour:
            hit = start_hour <= hour < end_hour
        else:
            hit = hour >= start_hour or hour < end_hour
        if hit:
            flagged.append(msg)

    if not flagged:
        return []

    # group consecutive off-hours messages into clusters
    clusters: list[list[dict]] = []
    current: list[dict] = [flagged[0]]
    for i in range(1, len(flagged)):
        prev_ts = flagged[i - 1].get("timestamp", "")
        curr_ts = flagged[i].get("timestamp", "")
        try:
            gap = abs((datetime.fromisoformat(curr_ts) - datetime.fromisoformat(prev_ts)).total_seconds())
        except (ValueError, TypeError):
            gap = 9999
        if gap < 3600:  # within an hour = same cluster
            current.append(flagged[i])
        else:
            clusters.append(current)
            current = [flagged[i]]
    clusters.append(current)

    anomalies = []
    for cluster in clusters:
        indices = [m.get("chain_index", m.get("line_number", 0)) for m in cluster]
        senders = sorted({m["sender"] for m in cluster})
        anomalies.append(Anomaly(
            kind="off_hours",
            severity="medium" if len(cluster) >= 5 else "low",
            timestamp=cluster[0]["timestamp"],
            description=f"{len(cluster)} messages between {start_hour}:00-{end_hour}:00",
            message_indices=indices,
            actors=senders,
        ))
    return anomalies


def detect_new_contacts(
    messages: list[dict],
    late_threshold: float = 0.7,
    reply_window_secs: int = 300,
) -> list[Anomaly]:
    if len(messages) < 2:
        return []

    cutoff = int(len(messages) * late_threshold)
    seen_pairs: set[tuple[str, str]] = set()
    anomalies = []

    for i in range(len(messages) - 1):
        a = messages[i]["sender"]
        b = messages[i + 1]["sender"]
        if a == b:
            continue
        try:
            ta = datetime.fromisoformat(messages[i]["timestamp"])
            tb = datetime.fromisoformat(messages[i + 1]["timestamp"])
            if abs((tb - ta).total_seconds()) > reply_window_secs:
                continue
        except (ValueError, TypeError):
            pass

        pair = (min(a, b), max(a, b))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)

        if i >= cutoff:
            idx_a = messages[i].get("chain_index", i)
            idx_b = messages[i + 1].get("chain_index", i + 1)
            anomalies.append(Anomaly(
                kind="new_contact",
                severity="medium",
                timestamp=messages[i + 1]["timestamp"],
                description=f"first interaction between {pair[0]} and {pair[1]} at message {i + 1}/{len(messages)}",
                message_indices=[idx_a, idx_b],
                actors=sorted(pair),
            ))
    return anomalies


def detect_keyword_clusters(
    messages: list[dict],
    ner_entities: list[dict] | None = None,
    window_size: int = 5,
) -> list[Anomaly]:
    if len(messages) < 2:
        return []

    # build per-message category sets from NER data on each message
    msg_categories: list[set[str]] = []
    category_map = {
        "MONEY": "money",
        "LOCATION": "location",
        "COORDINATES": "location",
        "DATE": "time",
    }

    # build a lookup from message index to NER entities
    ner_by_index: dict[int, list[dict]] = {}
    if ner_entities:
        for e in ner_entities:
            if isinstance(e, dict):
                for s in e.get("senders", []):
                    # map sender to entities for matching
                    pass
                # store by text for later matching
                ner_by_index.setdefault(e.get("label", ""), []).append(e)

    for msg in messages:
        cats: set[str] = set()
        ents = msg.get("entities", [])
        if isinstance(ents, list):
            for e in ents:
                if isinstance(e, dict):
                    mapped = category_map.get(e.get("label", ""))
                    if mapped:
                        cats.add(mapped)

        # also check global NER entities for this message's sender
        if ner_entities:
            sender = msg.get("sender", "")
            for e in ner_entities:
                if isinstance(e, dict) and sender in e.get("senders", []):
                    mapped = category_map.get(e.get("label", ""))
                    if mapped:
                        cats.add(mapped)

        # also check body for time keywords
        body = msg.get("body", "").lower()
        time_words = ("tonight", "tomorrow", "midnight", "dawn", "right now", "asap")
        if any(w in body for w in time_words):
            cats.add("time")
        msg_categories.append(cats)

    anomalies = []
    checked_windows: set[int] = set()

    for i in range(len(messages) - window_size + 1):
        window_cats: set[str] = set()
        for j in range(i, i + window_size):
            window_cats |= msg_categories[j]

        if len(window_cats) >= 2 and i not in checked_windows:
            indices = [messages[j].get("chain_index", j) for j in range(i, i + window_size)]
            senders = sorted({messages[j]["sender"] for j in range(i, i + window_size)})
            cats_str = " + ".join(sorted(window_cats))
            anomalies.append(Anomaly(
                kind="keyword_cluster",
                severity="high" if len(window_cats) >= 3 else "medium",
                timestamp=messages[i]["timestamp"],
                description=f"co-occurrence of {cats_str} within {window_size} messages",
                message_indices=indices,
                actors=senders,
            ))
            # skip overlapping windows
            for k in range(i, i + window_size):
                checked_windows.add(k)

    return anomalies


def detect_anomalies(
    messages: list[dict],
    ner_entities: list[dict] | None = None,
) -> list[dict]:
    results: list[Anomaly] = []
    results.extend(detect_bursts(messages))
    results.extend(detect_off_hours(messages))
    results.extend(detect_new_contacts(messages))
    results.extend(detect_keyword_clusters(messages, ner_entities))

    results.sort(key=lambda a: (_SEVERITY_ORDER.get(a.severity, 9), a.timestamp))
    return [a.to_dict() for a in results]
