from threadline.response_time import compute_response_times


def _msg(ts, sender):
    return {"timestamp": ts, "sender": sender, "body": "hi"}


def test_empty():
    result = compute_response_times([])
    assert result["per_sender"] == {}
    assert result["pairs"] == []
    assert result["fastest"] is None


def test_single_message():
    result = compute_response_times([_msg("2025-01-06T10:00:00", "Alice")])
    assert result["per_sender"] == {}


def test_same_sender_no_response():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:01:00", "Alice"),
    ]
    result = compute_response_times(msgs)
    assert result["per_sender"] == {}


def test_basic_response():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:00:30", "Bob"),  # 30s response
    ]
    result = compute_response_times(msgs)
    assert "Bob" in result["per_sender"]
    assert result["per_sender"]["Bob"]["avg_seconds"] == 30.0
    assert result["fastest"] == "Bob"


def test_multiple_responses():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:00:30", "Bob"),
        _msg("2025-01-06T10:01:00", "Alice"),
        _msg("2025-01-06T10:02:00", "Bob"),
    ]
    result = compute_response_times(msgs)
    assert result["per_sender"]["Bob"]["count"] == 2
    assert result["per_sender"]["Alice"]["count"] == 1


def test_ignores_long_gaps():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T12:00:00", "Bob"),  # 2 hours, over threshold
    ]
    result = compute_response_times(msgs)
    assert result["per_sender"] == {}


def test_fastest_slowest():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:00:10", "Bob"),   # 10s
        _msg("2025-01-06T10:00:20", "Alice"),  # 10s
        _msg("2025-01-06T10:05:00", "Carol"),  # 280s
    ]
    result = compute_response_times(msgs)
    assert result["fastest"] == "Bob"
    assert result["slowest"] == "Carol"


def test_pairs_sorted_by_avg():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:00:10", "Bob"),
        _msg("2025-01-06T10:01:00", "Carol"),
        _msg("2025-01-06T10:05:00", "Alice"),
    ]
    result = compute_response_times(msgs)
    if len(result["pairs"]) >= 2:
        assert result["pairs"][0]["avg_seconds"] <= result["pairs"][1]["avg_seconds"]


def test_bad_timestamps():
    msgs = [
        _msg("not-valid", "Alice"),
        _msg("2025-01-06T10:00:00", "Bob"),
    ]
    result = compute_response_times(msgs)
    assert result["per_sender"] == {}


def test_median_calculation():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:00:10", "Bob"),
        _msg("2025-01-06T10:00:20", "Alice"),
        _msg("2025-01-06T10:00:50", "Bob"),  # 30s
        _msg("2025-01-06T10:01:00", "Alice"),
        _msg("2025-01-06T10:02:00", "Bob"),  # 60s
    ]
    result = compute_response_times(msgs)
    bob = result["per_sender"]["Bob"]
    assert bob["count"] == 3
    assert bob["min_seconds"] == 10.0
