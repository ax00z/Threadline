"""anomaly detection tests — bursts, off-hours, new contacts, keyword clusters"""

from threadline.anomaly import (
    detect_anomalies,
    detect_bursts,
    detect_off_hours,
    detect_new_contacts,
    detect_keyword_clusters,
)


def _msg(sender="A", body="hey", ts="2025-01-15T10:00:00", idx=0):
    return {
        "timestamp": ts,
        "sender": sender,
        "body": body,
        "line_number": idx,
        "chain_index": idx,
        "source_format": "whatsapp",
        "entities": [],
    }


def _make_steady_with_spike():
    """100 msgs spread over 10 hours, then 20 msgs crammed into one 30-min window"""
    msgs = []
    for i in range(100):
        hour = i // 10
        minute = (i % 10) * 6
        msgs.append(_msg(ts=f"2025-01-15T{hour + 8:02d}:{minute:02d}:00", idx=i))
    for i in range(20):
        msgs.append(_msg(ts=f"2025-01-15T19:0{i % 10}:00", idx=100 + i, sender="B"))
    return msgs


def test_burst_flags_spike():
    msgs = _make_steady_with_spike()
    results = detect_bursts(msgs, window_minutes=30, threshold_factor=2.0, min_absolute=5)
    assert len(results) >= 1
    kinds = [r.kind for r in results]
    assert "burst" in kinds


def test_burst_no_false_positive():
    # uniform distribution — 1 msg per 30-min window
    msgs = [_msg(ts=f"2025-01-15T{h:02d}:{m:02d}:00", idx=i)
            for i, (h, m) in enumerate([(8, 0), (8, 30), (9, 0), (9, 30), (10, 0),
                                         (10, 30), (11, 0), (11, 30), (12, 0), (12, 30)])]
    results = detect_bursts(msgs, min_absolute=5)
    assert len(results) == 0


def test_burst_too_few_messages():
    msgs = [_msg(idx=i) for i in range(3)]
    assert detect_bursts(msgs) == []


def test_off_hours_flagged():
    msgs = [
        _msg(ts="2025-01-15T02:00:00", idx=0),
        _msg(ts="2025-01-15T02:15:00", idx=1),
        _msg(ts="2025-01-15T03:00:00", idx=2),
    ]
    results = detect_off_hours(msgs)
    assert len(results) >= 1
    assert results[0].kind == "off_hours"


def test_off_hours_custom_range():
    msgs = [_msg(ts="2025-01-15T23:00:00", idx=0)]
    results = detect_off_hours(msgs, start_hour=22, end_hour=6)
    assert len(results) == 1


def test_off_hours_normal_clean():
    msgs = [_msg(ts=f"2025-01-15T{h:02d}:00:00", idx=i) for i, h in enumerate([9, 10, 11, 14, 15])]
    results = detect_off_hours(msgs)
    assert len(results) == 0


def test_new_contact_late():
    # 20 msgs between A and B, then msg 18 introduces C
    msgs = []
    for i in range(20):
        sender = "A" if i % 2 == 0 else "B"
        msgs.append(_msg(sender=sender, ts=f"2025-01-15T10:{i:02d}:00", idx=i))
    msgs.append(_msg(sender="C", ts="2025-01-15T10:20:00", idx=20))
    msgs.append(_msg(sender="A", ts="2025-01-15T10:20:30", idx=21))
    results = detect_new_contacts(msgs, late_threshold=0.7)
    assert len(results) >= 1
    assert "C" in results[0].actors


def test_new_contact_early_not_flagged():
    msgs = [
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=0),
        _msg(sender="C", ts="2025-01-15T10:01:00", idx=1),
        _msg(sender="A", ts="2025-01-15T10:02:00", idx=2),
        _msg(sender="B", ts="2025-01-15T10:03:00", idx=3),
    ]
    # C appears at index 0-1 which is < 70% of 4 messages
    results = detect_new_contacts(msgs, late_threshold=0.7)
    c_results = [r for r in results if "C" in r.actors]
    assert len(c_results) == 0


def test_keyword_cluster_found():
    msgs = [
        _msg(body="meet me downtown", idx=0, ts="2025-01-15T10:00:00"),
        _msg(body="bring $5000 cash", idx=1, ts="2025-01-15T10:01:00"),
        _msg(body="tonight at 8", idx=2, ts="2025-01-15T10:02:00"),
        _msg(body="ok", idx=3, ts="2025-01-15T10:03:00"),
        _msg(body="done", idx=4, ts="2025-01-15T10:04:00"),
    ]
    # inject NER entities
    msgs[0]["entities"] = [{"label": "LOCATION", "text": "downtown"}]
    msgs[1]["entities"] = [{"label": "MONEY", "text": "$5000"}]
    results = detect_keyword_clusters(msgs, window_size=5)
    assert len(results) >= 1
    assert results[0].kind == "keyword_cluster"


def test_keyword_cluster_isolated_not_flagged():
    msgs = [
        _msg(body="bring $5000 cash", idx=0, ts="2025-01-15T10:00:00"),
        _msg(body="ok", idx=1, ts="2025-01-15T10:01:00"),
        _msg(body="sure", idx=2, ts="2025-01-15T10:02:00"),
        _msg(body="cool", idx=3, ts="2025-01-15T10:03:00"),
        _msg(body="bye", idx=4, ts="2025-01-15T10:04:00"),
    ]
    msgs[0]["entities"] = [{"label": "MONEY", "text": "$5000"}]
    # only money, no location or time
    results = detect_keyword_clusters(msgs, window_size=5)
    assert len(results) == 0


def test_detect_anomalies_returns_sorted():
    msgs = []
    # off-hours low-severity
    msgs.append(_msg(ts="2025-01-15T03:00:00", idx=0))
    # normal msgs to pad
    for i in range(1, 10):
        msgs.append(_msg(ts=f"2025-01-15T10:{i:02d}:00", idx=i))
    results = detect_anomalies(msgs)
    if len(results) >= 2:
        sev = [r["severity"] for r in results]
        order = [{"high": 0, "medium": 1, "low": 2}[s] for s in sev]
        assert order == sorted(order)


def test_anomaly_dict_shape():
    msgs = [_msg(ts="2025-01-15T02:00:00", idx=0)]
    results = detect_anomalies(msgs)
    if results:
        r = results[0]
        assert set(r.keys()) == {"kind", "severity", "timestamp", "description", "message_indices", "actors"}
