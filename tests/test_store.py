"""DuckDB message store tests — loading, querying, safety."""

import pytest
from threadline.store import MessageStore


def _sample_msgs():
    return [
        {"timestamp": "2025-01-01T10:00:00", "sender": "Alice", "body": "hey", "line_number": 1, "source_format": "whatsapp"},
        {"timestamp": "2025-01-01T10:01:00", "sender": "Bob", "body": "hi", "line_number": 2, "source_format": "whatsapp"},
        {"timestamp": "2025-01-01T10:02:00", "sender": "Alice", "body": "what's up", "line_number": 3, "source_format": "whatsapp"},
        {"timestamp": "2025-01-01T10:05:00", "sender": "Charlie", "body": "yo", "line_number": 4, "source_format": "whatsapp"},
    ]


def test_load_returns_count():
    store = MessageStore()
    count = store.load(_sample_msgs())
    assert count == 4


def test_select_all():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("SELECT * FROM messages")
    assert result["row_count"] == 4
    assert "sender" in result["columns"]


def test_count():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("SELECT COUNT(*) as cnt FROM messages")
    assert result["rows"][0][0] == "4"


def test_where_filter():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("SELECT * FROM messages WHERE sender = 'Alice'")
    assert result["row_count"] == 2


def test_group_by():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("SELECT sender, COUNT(*) as cnt FROM messages GROUP BY sender ORDER BY cnt DESC")
    assert result["row_count"] == 3
    assert result["rows"][0][0] == "Alice"


def test_with_clause():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("WITH counts AS (SELECT sender, COUNT(*) as n FROM messages GROUP BY sender) SELECT * FROM counts")
    assert result["row_count"] == 3


def test_blocks_insert():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("INSERT INTO messages VALUES (99, '2025-01-01T00:00:00', 'X', 'bad', 0, 'whatsapp')")
    assert "error" in result


def test_blocks_update():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("UPDATE messages SET body = 'hacked' WHERE sender = 'Alice'")
    assert "error" in result


def test_blocks_drop():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("DROP TABLE messages")
    assert "error" in result


def test_invalid_sql():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("SELECT * FROM nonexistent_table")
    assert "error" in result


def test_auto_limit():
    store = MessageStore()
    store.load(_sample_msgs())
    # default limit is 500, but with 4 rows it doesn't matter
    result = store.query("SELECT * FROM messages")
    assert result["row_count"] <= 500


def test_reload_replaces():
    store = MessageStore()
    store.load(_sample_msgs())
    store.load([{"timestamp": "2025-06-01T00:00:00", "sender": "Z", "body": "only one", "line_number": 1, "source_format": "csv"}])
    result = store.query("SELECT COUNT(*) FROM messages")
    assert result["rows"][0][0] == "1"


def test_empty_load():
    store = MessageStore()
    store.load([])
    result = store.query("SELECT COUNT(*) FROM messages")
    assert result["rows"][0][0] == "0"


def test_explain_allowed():
    store = MessageStore()
    store.load(_sample_msgs())
    result = store.query("EXPLAIN SELECT * FROM messages")
    assert "error" not in result
