"""Tests for the intelligence analysis module."""
import pytest
from threadline.intel import extract_keywords, cluster_topics, score_threats, analyze_intel


def _make_msgs(bodies, senders=None):
    msgs = []
    for i, body in enumerate(bodies):
        sender = (senders or ["Alice", "Bob", "Charlie"])[i % len(senders or ["Alice", "Bob", "Charlie"])]
        msgs.append({
            "sender": sender,
            "body": body,
            "timestamp": f"2025-01-15T{10 + i % 10}:00:00",
        })
    return msgs


class TestExtractKeywords:
    def test_basic_extraction(self):
        msgs = _make_msgs([
            "The quarterly report needs updating",
            "Send the report to the finance team",
            "Finance approved the budget report",
            "The team meeting is scheduled for Monday",
            "Budget meeting with finance department",
        ])
        kws = extract_keywords(msgs)
        assert len(kws) > 0
        words = [k["keyword"] for k in kws]
        assert "report" in words
        assert "finance" in words

    def test_returns_senders(self):
        msgs = _make_msgs([
            "The investigation is ongoing",
            "We need more evidence for the investigation",
            "Evidence collected from the scene",
        ], senders=["Alice", "Bob", "Alice"])
        kws = extract_keywords(msgs)
        inv = next((k for k in kws if k["keyword"] == "investigation"), None)
        assert inv is not None
        assert "Alice" in inv["senders"]

    def test_stops_removed(self):
        msgs = _make_msgs(["The the the and and and"])
        kws = extract_keywords(msgs)
        words = [k["keyword"] for k in kws]
        assert "the" not in words
        assert "and" not in words

    def test_empty_messages(self):
        assert extract_keywords([]) == []

    def test_top_n_limit(self):
        msgs = _make_msgs([f"word{i} appears here" for i in range(100)])
        kws = extract_keywords(msgs, top_n=5)
        assert len(kws) <= 5


class TestClusterTopics:
    def test_not_available_small(self):
        msgs = _make_msgs(["short"] * 3)
        result = cluster_topics(msgs)
        # Either not available or empty topics for tiny data
        assert isinstance(result, dict)
        assert "topics" in result

    def test_empty(self):
        result = cluster_topics([])
        assert result["available"] is False

    @pytest.mark.skipif(
        not __import__("threadline.intel", fromlist=["_available"])._available(),
        reason="sklearn not installed",
    )
    def test_with_sklearn(self):
        msgs = _make_msgs(
            ["report budget finance quarterly"] * 30
            + ["meeting schedule calendar agenda"] * 30
            + ["investigation evidence suspect case"] * 30,
            senders=["Alice", "Bob", "Charlie"],
        )
        result = cluster_topics(msgs)
        assert result["available"] is True
        assert len(result["topics"]) >= 2
        for topic in result["topics"]:
            assert "top_terms" in topic
            assert topic["size"] > 0


class TestScoreThreats:
    def test_no_threats(self):
        msgs = _make_msgs([
            "Good morning team",
            "Let's have lunch at noon",
            "The meeting went well",
        ])
        result = score_threats(msgs)
        assert result["level"] == "none"
        assert result["flagged_count"] == 0

    def test_detects_violence(self):
        msgs = _make_msgs([
            "Normal message here",
            "They threatened to attack the building",
            "Bring the weapons to the location",
        ])
        result = score_threats(msgs)
        assert result["flagged_count"] > 0
        assert "violence" in result["categories"]

    def test_detects_narcotics(self):
        msgs = _make_msgs([
            "The dealer has the cocaine ready",
            "Pick up the drugs from the stash",
        ])
        result = score_threats(msgs)
        assert "narcotics" in result["categories"]

    def test_detects_financial(self):
        msgs = _make_msgs([
            "Wire transfer to the offshore account",
            "Set up the shell company",
        ])
        result = score_threats(msgs)
        assert "financial" in result["categories"]

    def test_detects_opsec(self):
        msgs = _make_msgs([
            "Use the burner phone",
            "Delete everything from the chat",
        ])
        result = score_threats(msgs)
        assert "opsec" in result["categories"]

    def test_per_sender_breakdown(self):
        msgs = _make_msgs([
            "Attack the target",
            "Normal message",
            "Bring the weapons",
        ], senders=["Suspect", "Innocent", "Suspect"])
        result = score_threats(msgs)
        assert len(result["per_sender"]) > 0
        top = result["per_sender"][0]
        assert top["sender"] == "Suspect"
        assert top["flagged_messages"] == 2

    def test_threat_level_calculation(self):
        # Many flagged messages → high
        msgs = _make_msgs(["Attack with weapons now"] * 20)
        result = score_threats(msgs)
        assert result["level"] in ("medium", "high")

    def test_flagged_capped(self):
        msgs = _make_msgs(["Kill the target with weapons"] * 100)
        result = score_threats(msgs)
        assert len(result["flagged"]) <= 50


class TestAnalyzeIntel:
    def test_returns_all_keys(self):
        msgs = _make_msgs(["Hello world testing"] * 5)
        result = analyze_intel(msgs)
        assert "keywords" in result
        assert "topics" in result
        assert "threats" in result

    def test_empty_input(self):
        result = analyze_intel([])
        assert result["keywords"] == []
        assert result["threats"]["level"] == "none"
