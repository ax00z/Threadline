import copy
import pytest
from threadline.crypto import build_chain, verify_chain, _canonical, _sha256


def _make_msg(body="hey", sender="Alice", idx=0):
    return {
        "timestamp": "2024-01-15T10:00:00",
        "sender": sender,
        "body": body,
        "line_number": idx,
        "source_format": "whatsapp",
        "entities": [],
    }


def test_determinism():
    a = _make_msg()
    b = _make_msg()
    assert _canonical(a) == _canonical(b)
    assert _sha256(_canonical(a)) == _sha256(_canonical(b))


def test_different_body_different_hash():
    a = _make_msg(body="hello")
    b = _make_msg(body="goodbye")
    assert _sha256(_canonical(a)) != _sha256(_canonical(b))


def test_build_chain_adds_fields():
    msgs = [_make_msg(idx=i) for i in range(5)]
    result = build_chain(msgs)
    assert len(result) == 5
    for i, msg in enumerate(result):
        assert "chain_hash" in msg
        assert "previous_hash" in msg
        assert msg["chain_index"] == i
        assert len(msg["chain_hash"]) == 64
        assert len(msg["previous_hash"]) == 64


def test_first_message_has_genesis():
    msgs = build_chain([_make_msg()])
    assert msgs[0]["previous_hash"] == "0" * 64


def test_chain_links():
    msgs = build_chain([_make_msg(idx=i) for i in range(3)])
    assert msgs[1]["previous_hash"] == msgs[0]["chain_hash"]
    assert msgs[2]["previous_hash"] == msgs[1]["chain_hash"]


def test_verify_valid_chain():
    msgs = build_chain([_make_msg(body=f"msg {i}", idx=i) for i in range(10)])
    result = verify_chain(msgs)
    assert result["valid"] is True
    assert result["checked"] == 10
    assert result["broken_at"] is None


def test_verify_catches_tampered_body():
    msgs = build_chain([_make_msg(body=f"msg {i}", idx=i) for i in range(5)])
    msgs[2]["body"] = "TAMPERED"
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 2


def test_verify_catches_tampered_hash():
    msgs = build_chain([_make_msg(body=f"msg {i}", idx=i) for i in range(5)])
    msgs[3]["chain_hash"] = "deadbeef" * 8
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 3


def test_verify_catches_swapped_messages():
    msgs = build_chain([_make_msg(body=f"msg {i}", idx=i) for i in range(5)])
    msgs[1], msgs[2] = msgs[2], msgs[1]
    result = verify_chain(msgs)
    assert result["valid"] is False


def test_verify_empty():
    result = verify_chain([])
    assert result["valid"] is True
    assert result["checked"] == 0


def test_verify_single():
    msgs = build_chain([_make_msg()])
    result = verify_chain(msgs)
    assert result["valid"] is True
    assert result["checked"] == 1


def test_entities_not_in_hash():
    """entities field shouldn't affect the hash"""
    a = _make_msg()
    b = copy.deepcopy(a)
    b["entities"] = [{"text": "something", "label": "PHONE"}]
    assert _canonical(a) == _canonical(b)


def test_chain_hash_excluded_from_canonical():
    """hash fields in the dict shouldn't leak into canonical form"""
    msg = _make_msg()
    msg["chain_hash"] = "abc123"
    msg["previous_hash"] = "def456"
    msg["chain_index"] = 99
    clean = _make_msg()
    assert _canonical(msg) == _canonical(clean)
