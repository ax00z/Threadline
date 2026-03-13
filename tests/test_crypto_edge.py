"""edge-case tests for the hash chain — unicode, empty bodies, large batches, etc."""

import copy
import json
from threadline.crypto import build_chain, verify_chain, _canonical, _sha256


def _msg(body="test", sender="A", idx=0, ts="2024-01-01T00:00:00"):
    return {
        "timestamp": ts,
        "sender": sender,
        "body": body,
        "line_number": idx,
        "source_format": "whatsapp",
        "entities": [],
    }


def test_unicode_body():
    msgs = build_chain([
        _msg(body="привет мир", idx=0),
        _msg(body="こんにちは世界", idx=1),
        _msg(body="🔥💀🚀", idx=2),
    ])
    result = verify_chain(msgs)
    assert result["valid"] is True
    assert result["checked"] == 3


def test_unicode_sender():
    msgs = build_chain([
        _msg(sender="José García", idx=0),
        _msg(sender="田中太郎", idx=1),
    ])
    assert verify_chain(msgs)["valid"] is True


def test_empty_body():
    msgs = build_chain([_msg(body=""), _msg(body="", idx=1)])
    result = verify_chain(msgs)
    assert result["valid"] is True
    # both have same body but different line_number → different hashes
    assert msgs[0]["chain_hash"] != msgs[1]["chain_hash"]


def test_whitespace_only_body():
    msgs = build_chain([_msg(body="   \t\n")])
    assert verify_chain(msgs)["valid"] is True


def test_large_batch():
    batch = [_msg(body=f"message number {i}", idx=i) for i in range(5000)]
    msgs = build_chain(batch)
    assert len(msgs) == 5000
    result = verify_chain(msgs)
    assert result["valid"] is True
    assert result["checked"] == 5000


def test_single_message():
    msgs = build_chain([_msg()])
    assert verify_chain(msgs)["valid"] is True


def test_body_with_json_special_chars():
    """bodies with quotes, backslashes, newlines — must serialize correctly"""
    tricky = 'he said "hello\\world"\nand then\ttabbed'
    msgs = build_chain([_msg(body=tricky)])
    assert verify_chain(msgs)["valid"] is True


def test_body_with_html():
    msgs = build_chain([_msg(body='<script>alert("xss")</script>')])
    assert verify_chain(msgs)["valid"] is True


def test_canonical_field_order_irrelevant():
    """dict key insertion order shouldn't matter — canonical sorts"""
    a = {"body": "hi", "sender": "X", "timestamp": "2024-01-01T00:00:00", "line_number": 0, "source_format": "whatsapp"}
    b = {"source_format": "whatsapp", "line_number": 0, "timestamp": "2024-01-01T00:00:00", "body": "hi", "sender": "X"}
    assert _canonical(a) == _canonical(b)


def test_canonical_ignores_extra_fields():
    """random extra fields in the dict shouldn't affect hash"""
    base = _msg()
    extended = {**base, "extra_field": "should be ignored", "analysis_score": 99}
    assert _canonical(base) == _canonical(extended)


def test_missing_optional_field():
    """if a hash field is missing, canonical should still work"""
    partial = {"body": "hello", "sender": "X", "timestamp": "2024-01-01T00:00:00"}
    # should not crash
    result = _canonical(partial)
    assert "body" in result
    assert "line_number" not in result


def test_rebuild_produces_same_hashes():
    """building chain twice on identical data gives same result"""
    a = [_msg(body=f"m{i}", idx=i) for i in range(20)]
    b = [_msg(body=f"m{i}", idx=i) for i in range(20)]
    build_chain(a)
    build_chain(b)
    for i in range(20):
        assert a[i]["chain_hash"] == b[i]["chain_hash"]


def test_verify_missing_chain_hash_field():
    """messages without chain_hash should fail verification"""
    msgs = [_msg()]
    # no build_chain called — no chain_hash
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 0


def test_tamper_sender():
    msgs = build_chain([_msg(sender="Alice", idx=0), _msg(sender="Bob", idx=1)])
    msgs[0]["sender"] = "Charlie"
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 0


def test_tamper_timestamp():
    msgs = build_chain([_msg(ts="2024-01-01T00:00:00"), _msg(ts="2024-01-01T01:00:00", idx=1)])
    msgs[1]["timestamp"] = "2024-06-15T00:00:00"
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 1


def test_tamper_line_number():
    msgs = build_chain([_msg(idx=0), _msg(idx=1)])
    msgs[0]["line_number"] = 999
    result = verify_chain(msgs)
    assert result["valid"] is False


def test_insert_message_breaks_chain():
    """inserting a new message into an existing chain should break it"""
    msgs = build_chain([_msg(idx=i) for i in range(3)])
    injected = _msg(body="injected evidence", idx=99)
    injected["chain_hash"] = "a" * 64
    injected["previous_hash"] = msgs[0]["chain_hash"]
    injected["chain_index"] = 1
    msgs.insert(1, injected)
    result = verify_chain(msgs)
    assert result["valid"] is False


def test_delete_message_breaks_chain():
    """removing a message from the chain should break it"""
    msgs = build_chain([_msg(body=f"m{i}", idx=i) for i in range(5)])
    del msgs[2]
    result = verify_chain(msgs)
    assert result["valid"] is False


def test_rust_compatible_canonical():
    """canonical JSON must match what the rust verifier expects — sorted keys, compact separators"""
    msg = _msg(body="hello world", sender="Agent", idx=42, ts="2025-06-01T12:00:00")
    canon = _canonical(msg)
    parsed = json.loads(canon)
    # keys must be alphabetical
    keys = list(parsed.keys())
    assert keys == sorted(keys)
    # no spaces after separators
    assert ": " not in canon
    assert ", " not in canon
