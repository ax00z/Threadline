from threadline.heatmap import build_heatmap


def _msg(ts, sender="Alice"):
    return {"timestamp": ts, "sender": sender, "body": "hi"}


def test_empty():
    result = build_heatmap([])
    assert result["matrix"] == [[0] * 24 for _ in range(7)]
    assert result["peak"]["count"] == 0


def test_single_message():
    # 2025-01-06 is a Monday
    result = build_heatmap([_msg("2025-01-06T14:30:00")])
    assert result["matrix"][0][14] == 1  # Monday, 2pm
    assert result["peak"] == {"day": "Mon", "hour": 14, "count": 1}


def test_multiple_days():
    msgs = [
        _msg("2025-01-06T09:00:00"),  # Monday
        _msg("2025-01-06T09:01:00"),  # Monday
        _msg("2025-01-07T21:00:00"),  # Tuesday
    ]
    result = build_heatmap(msgs)
    assert result["matrix"][0][9] == 2
    assert result["matrix"][1][21] == 1
    assert result["peak"]["day"] == "Mon"


def test_per_sender():
    msgs = [
        _msg("2025-01-06T10:00:00", "Alice"),
        _msg("2025-01-06T10:05:00", "Bob"),
    ]
    result = build_heatmap(msgs)
    assert "Alice" in result["per_sender"]
    assert "Bob" in result["per_sender"]
    assert result["per_sender"]["Alice"][0][10] == 1
    assert result["per_sender"]["Bob"][0][10] == 1


def test_day_labels():
    result = build_heatmap([])
    assert result["day_labels"] == ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def test_weekend_messages():
    # 2025-01-11 is a Saturday, 2025-01-12 is Sunday
    msgs = [
        _msg("2025-01-11T22:00:00"),
        _msg("2025-01-12T03:00:00"),
    ]
    result = build_heatmap(msgs)
    assert result["matrix"][5][22] == 1  # Saturday
    assert result["matrix"][6][3] == 1   # Sunday


def test_bad_timestamp_skipped():
    msgs = [
        _msg("not-a-date"),
        _msg("2025-01-06T12:00:00"),
    ]
    result = build_heatmap(msgs)
    total = sum(sum(row) for row in result["matrix"])
    assert total == 1


def test_midnight_boundary():
    msgs = [
        _msg("2025-01-06T00:00:00"),
        _msg("2025-01-06T23:59:59"),
    ]
    result = build_heatmap(msgs)
    assert result["matrix"][0][0] == 1
    assert result["matrix"][0][23] == 1


def test_matrix_shape():
    result = build_heatmap([_msg("2025-01-06T12:00:00")])
    assert len(result["matrix"]) == 7
    for row in result["matrix"]:
        assert len(row) == 24
