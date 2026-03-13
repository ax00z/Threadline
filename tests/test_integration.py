"""end-to-end pipeline test: file → parse → chain → graph → NER → store"""

import json
import os
import tempfile

from threadline.parser import parse_file
from threadline.crypto import build_chain, verify_chain
from threadline.ner import extract_from_messages
from threadline.store import MessageStore


WA_CHAT = """\
[1/15/25, 2:34 PM] Marcus: hey call me at 555-867-5309
[1/15/25, 3:01 PM] Fiona: sure, send your email too
[1/15/25, 3:02 PM] Marcus: marcus@threadline.dev
[1/15/25, 3:05 PM] Fiona: got it. meet at 40.7128, -74.0060 tomorrow
[1/15/25, 3:06 PM] Marcus: perfect. I'll bring $500 cash
[1/15/25, 3:10 PM] Fiona: check https://example.com/plan
[1/15/25, 3:12 PM] Marcus: done
[1/15/25, 3:15 PM] Fiona: see you 01/16/2025
"""


def _pipeline(content, suffix=".txt"):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    try:
        messages = [m.to_dict() for m in parse_file(f.name)]
        messages = build_chain(messages)
        chain = verify_chain(messages)
        ner = extract_from_messages(messages)
        store = MessageStore()
        store.load(messages)
        return messages, chain, ner, store
    finally:
        os.unlink(f.name)


def test_full_pipeline_parses_all():
    msgs, chain, ner, store = _pipeline(WA_CHAT)
    assert len(msgs) == 8


def test_full_pipeline_chain_valid():
    msgs, chain, ner, store = _pipeline(WA_CHAT)
    assert chain["valid"] is True
    assert chain["checked"] == 8


def test_full_pipeline_every_msg_has_hash():
    msgs, _, _, _ = _pipeline(WA_CHAT)
    for m in msgs:
        assert "chain_hash" in m
        assert "previous_hash" in m
        assert isinstance(m["chain_index"], int)


def test_full_pipeline_ner_finds_entities():
    _, _, ner, _ = _pipeline(WA_CHAT)
    labels = {e["label"] for e in ner["entities"]}
    assert "PHONE" in labels
    assert "EMAIL" in labels
    assert "URL" in labels
    assert "MONEY" in labels
    assert "COORDINATES" in labels


def test_full_pipeline_ner_attributes_to_senders():
    _, _, ner, _ = _pipeline(WA_CHAT)
    assert "Marcus" in ner["sender_entities"]
    assert "Fiona" in ner["sender_entities"]
    marcus_labels = set(ner["sender_entities"]["Marcus"].keys())
    assert "EMAIL" in marcus_labels


def test_full_pipeline_store_query():
    _, _, _, store = _pipeline(WA_CHAT)
    result = store.query("SELECT COUNT(*) as cnt FROM messages")
    assert result["rows"][0][0] == "8"


def test_full_pipeline_store_sender_filter():
    _, _, _, store = _pipeline(WA_CHAT)
    result = store.query("SELECT * FROM messages WHERE sender = 'Marcus'")
    assert result["row_count"] == 4


def test_full_pipeline_store_blocks_writes():
    _, _, _, store = _pipeline(WA_CHAT)
    result = store.query("DELETE FROM messages")
    assert "error" in result


def test_pipeline_telegram():
    data = {
        "name": "ops",
        "type": "personal_chat",
        "messages": [
            {"id": 1, "type": "message", "date": "2025-01-10T08:00:00", "from": "Alpha", "text": "coordinates 34.0522, -118.2437"},
            {"id": 2, "type": "message", "date": "2025-01-10T08:01:00", "from": "Bravo", "text": "send $200 USD to confirm"},
            {"id": 3, "type": "message", "date": "2025-01-10T08:02:00", "from": "Alpha", "text": "done. call 310-555-0199"},
        ],
    }
    msgs, chain, ner, store = _pipeline(json.dumps(data), suffix=".json")
    assert len(msgs) == 3
    assert chain["valid"] is True
    assert msgs[0]["source_format"] == "telegram"
    labels = {e["label"] for e in ner["entities"]}
    assert "COORDINATES" in labels
    assert "PHONE" in labels


def test_pipeline_csv():
    csv = "timestamp,sender,body\n2025-03-01T09:00:00,Petra,hey\n2025-03-01T09:01:00,Sven,hi\n"
    msgs, chain, ner, store = _pipeline(csv, suffix=".csv")
    assert len(msgs) == 2
    assert chain["valid"] is True
    assert msgs[0]["source_format"] == "csv"


def test_chain_survives_ner_enrichment():
    """NER adds entities to msg dicts. hash must still verify because entities aren't hashed."""
    msgs, chain, ner, _ = _pipeline(WA_CHAT)
    assert chain["valid"] is True
    # explicitly re-verify after NER has mutated the dicts
    recheck = verify_chain(msgs)
    assert recheck["valid"] is True


def test_tamper_after_pipeline_detected():
    msgs, _, _, _ = _pipeline(WA_CHAT)
    msgs[3]["body"] = "EVIDENCE TAMPERED"
    result = verify_chain(msgs)
    assert result["valid"] is False
    assert result["broken_at"] == 3
