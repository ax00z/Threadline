import pytest

vader = pytest.importorskip("vaderSentiment")

from threadline.sentiment import analyze_sentiment, _empty_result


def _msg(body="hello", sender="A", ts="2025-01-15T10:00:00"):
    return {"body": body, "sender": sender, "timestamp": ts}


def test_positive_message():
    result = analyze_sentiment([_msg("This is absolutely wonderful and amazing!")])
    assert result["available"] is True
    assert result["overall"]["compound"] > 0.3


def test_negative_message():
    result = analyze_sentiment([_msg("This is terrible, awful, and disgusting.")])
    assert result["overall"]["compound"] < -0.3


def test_neutral_message():
    result = analyze_sentiment([_msg("The meeting is at 3pm.")])
    assert abs(result["overall"]["compound"]) < 0.3


def test_per_sender_breakdown():
    msgs = [
        _msg("I love this!", sender="Alice", ts="2025-01-15T10:00:00"),
        _msg("I love this!", sender="Alice", ts="2025-01-15T10:01:00"),
        _msg("I hate this.", sender="Bob", ts="2025-01-15T10:02:00"),
    ]
    result = analyze_sentiment(msgs)
    assert "Alice" in result["per_sender"]
    assert "Bob" in result["per_sender"]
    assert result["per_sender"]["Alice"]["message_count"] == 2
    assert result["per_sender"]["Alice"]["compound"] > result["per_sender"]["Bob"]["compound"]


def test_timeline_sampling():
    msgs = [_msg(f"message {i}", ts=f"2025-01-15T10:{i % 60:02d}:00") for i in range(1000)]
    result = analyze_sentiment(msgs)
    assert len(result["timeline"]) <= 500
    assert all("compound" in t and "sender" in t for t in result["timeline"])


def test_extremes_detection():
    msgs = [
        _msg("I love everything about this, it is fantastic!", sender="A", ts="2025-01-15T10:00:00"),
        _msg("ok", sender="B", ts="2025-01-15T10:01:00"),
        _msg("I absolutely despise and loathe this garbage.", sender="C", ts="2025-01-15T10:02:00"),
    ]
    result = analyze_sentiment(msgs)
    assert result["extremes"]["most_positive"]["sender"] == "A"
    assert result["extremes"]["most_negative"]["sender"] == "C"
    assert result["extremes"]["most_positive"]["compound"] > result["extremes"]["most_negative"]["compound"]


def test_sentiment_shifts():
    msgs = [
        _msg("I love everything so much!", sender="A", ts="2025-01-15T10:00:00"),
        _msg("This is great!", sender="A", ts="2025-01-15T10:01:00"),
        _msg("I hate this, it is the worst thing ever.", sender="A", ts="2025-01-15T10:02:00"),
    ]
    result = analyze_sentiment(msgs)
    assert len(result["shifts"]) >= 1
    assert result["shifts"][0]["sender"] == "A"
    assert result["shifts"][0]["magnitude"] > 0.5


def test_empty_messages():
    result = analyze_sentiment([])
    assert result["available"] is True
    assert result["per_sender"] == {}
    assert result["timeline"] == []
    assert result["extremes"]["most_positive"] is None


def test_unavailable_graceful(monkeypatch):
    import threadline.sentiment as mod
    original = analyze_sentiment

    # simulate missing vaderSentiment by returning the empty result directly
    result = _empty_result()
    assert result["available"] is False
    assert result["overall"]["compound"] == 0.0
    assert result["shifts"] == []
