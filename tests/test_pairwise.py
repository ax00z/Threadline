"""pairwise relationship stats tests"""

from threadline.pairwise import compute_pairwise


def _msg(sender="A", ts="2025-01-15T10:00:00", idx=0):
    return {
        "timestamp": ts,
        "sender": sender,
        "body": "hey",
        "line_number": idx,
        "chain_index": idx,
        "source_format": "whatsapp",
        "entities": [],
    }


def test_basic_pair():
    msgs = [
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=0),
        _msg(sender="B", ts="2025-01-15T10:01:00", idx=1),
        _msg(sender="A", ts="2025-01-15T10:02:00", idx=2),
    ]
    result = compute_pairwise(msgs)
    assert len(result) == 1
    assert set(result[0]["pair"]) == {"A", "B"}
    assert result[0]["message_count"] == 2


def test_no_self_pairs():
    msgs = [_msg(sender="A", ts=f"2025-01-15T10:0{i}:00", idx=i) for i in range(5)]
    result = compute_pairwise(msgs)
    assert len(result) == 0


def test_outside_reply_window():
    msgs = [
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=0),
        _msg(sender="B", ts="2025-01-15T10:10:00", idx=1),  # 600s gap
    ]
    result = compute_pairwise(msgs)
    assert len(result) == 0


def test_daily_counts():
    msgs = [
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=0),
        _msg(sender="B", ts="2025-01-15T10:01:00", idx=1),
        _msg(sender="A", ts="2025-01-16T10:00:00", idx=2),
        _msg(sender="B", ts="2025-01-16T10:01:00", idx=3),
        _msg(sender="A", ts="2025-01-16T10:02:00", idx=4),
        _msg(sender="B", ts="2025-01-16T10:03:00", idx=5),
    ]
    result = compute_pairwise(msgs)
    assert len(result) == 1
    daily = result[0]["daily_counts"]
    assert "2025-01-15" in daily
    assert "2025-01-16" in daily


def test_duration():
    msgs = [
        _msg(sender="A", ts="2025-01-10T10:00:00", idx=0),
        _msg(sender="B", ts="2025-01-10T10:01:00", idx=1),
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=2),
        _msg(sender="B", ts="2025-01-15T10:01:00", idx=3),
    ]
    result = compute_pairwise(msgs)
    assert result[0]["duration_days"] == 6


def test_sorted_by_count():
    msgs = [
        _msg(sender="A", ts="2025-01-15T10:00:00", idx=0),
        _msg(sender="B", ts="2025-01-15T10:01:00", idx=1),
        _msg(sender="C", ts="2025-01-15T10:02:00", idx=2),
        _msg(sender="D", ts="2025-01-15T10:03:00", idx=3),
        _msg(sender="C", ts="2025-01-15T10:04:00", idx=4),
        _msg(sender="D", ts="2025-01-15T10:04:30", idx=5),
        _msg(sender="C", ts="2025-01-15T10:04:45", idx=6),
        _msg(sender="D", ts="2025-01-15T10:05:00", idx=7),
    ]
    result = compute_pairwise(msgs)
    counts = [r["message_count"] for r in result]
    assert counts == sorted(counts, reverse=True)


def test_empty():
    assert compute_pairwise([]) == []


def test_single_message():
    assert compute_pairwise([_msg()]) == []
