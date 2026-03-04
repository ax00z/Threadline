import json
import tempfile
import os
import pytest
from threadline.parser import parse_file, detect_format
from threadline.models import Message


def write_tmp(content: str, suffix: str = ".txt") -> str:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


# --- WhatsApp bracket format ---

WA_BRACKET = """\
[1/15/25, 2:34 PM] Marcus: hey what time are we meeting
[1/15/25, 3:01 PM] Fiona: around 6 probably
[1/15/25, 3:02 PM] Marcus: works for me
[1/15/25, 3:02 PM] Lily: same
"""

def test_bracket_count():
    p = write_tmp(WA_BRACKET)
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 4
    finally:
        os.unlink(p)


def test_bracket_fields():
    p = write_tmp(WA_BRACKET)
    try:
        msgs = list(parse_file(p))
        assert msgs[0].sender == "Marcus"
        assert msgs[0].body == "hey what time are we meeting"
        assert msgs[0].timestamp.startswith("2025-01-15")
        assert msgs[0].source_format == "whatsapp"
    finally:
        os.unlink(p)


def test_bracket_24h():
    chat = "[12/3/24, 14:05] Renzo: good afternoon\n"
    p = write_tmp(chat)
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 1
        assert "14:05" in msgs[0].timestamp
    finally:
        os.unlink(p)


# --- WhatsApp dash format ---

WA_DASH = """\
1/20/25, 9:10 AM - Nina: morning
1/20/25, 9:11 AM - Tyler: hey
1/20/25, 9:15 AM - Nina: did you see the news
"""

def test_dash_format():
    p = write_tmp(WA_DASH)
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 3
        assert msgs[1].sender == "Tyler"
    finally:
        os.unlink(p)


# --- Multi-line messages ---

def test_multiline():
    chat = "[2/1/25, 10:00 AM] Sam: first line\nsecond line\nthird line\n[2/1/25, 10:01 AM] Jo: got it\n"
    p = write_tmp(chat)
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 2
        assert "second line" in msgs[0].body
        assert "third line" in msgs[0].body
    finally:
        os.unlink(p)


# --- System message filtering ---

def test_system_messages_filtered():
    chat = (
        "[3/1/25, 8:00 AM] Victor: hey\n"
        "[3/1/25, 8:01 AM] Victor: Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.\n"
        "[3/1/25, 8:02 AM] Petra: hi\n"
    )
    p = write_tmp(chat)
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 2
        assert all(m.sender in ("Victor", "Petra") for m in msgs)
    finally:
        os.unlink(p)


# --- Telegram JSON format ---

TELEGRAM_DATA = {
    "name": "Test Chat",
    "type": "personal_chat",
    "messages": [
        {"id": 1, "type": "message", "date": "2025-02-10T10:00:00", "from": "Leon", "text": "hello"},
        {"id": 2, "type": "message", "date": "2025-02-10T10:01:00", "from": "Mei", "text": "hey"},
        {"id": 3, "type": "service", "date": "2025-02-10T10:02:00", "actor": "Leon", "text": ""},
        {"id": 4, "type": "message", "date": "2025-02-10T10:03:00", "from": "Leon", "text": [{"type": "bold", "text": "check this out"}]},
    ]
}

def test_telegram_count():
    p = write_tmp(json.dumps(TELEGRAM_DATA), suffix=".json")
    try:
        msgs = list(parse_file(p))
        # 2 plain messages + 1 rich text message; service message skipped
        assert len(msgs) == 3
    finally:
        os.unlink(p)


def test_telegram_fields():
    p = write_tmp(json.dumps(TELEGRAM_DATA), suffix=".json")
    try:
        msgs = list(parse_file(p))
        assert msgs[0].sender == "Leon"
        assert msgs[0].source_format == "telegram"
        assert msgs[2].body == "check this out"
    finally:
        os.unlink(p)


def test_telegram_list_format():
    data = [
        {"id": 1, "type": "message", "date": "2025-01-01T12:00:00", "from": "Rachel", "text": "hi"},
    ]
    p = write_tmp(json.dumps(data), suffix=".json")
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 1
    finally:
        os.unlink(p)


# --- CSV format ---

CSV_DATA = "timestamp,sender,body\n2025-03-01T09:00:00,Petra,good morning\n2025-03-01T09:01:00,Sven,morning\n"

def test_csv_count():
    p = write_tmp(CSV_DATA, suffix=".csv")
    try:
        msgs = list(parse_file(p))
        assert len(msgs) == 2
    finally:
        os.unlink(p)


def test_csv_fields():
    p = write_tmp(CSV_DATA, suffix=".csv")
    try:
        msgs = list(parse_file(p))
        assert msgs[0].sender == "Petra"
        assert msgs[0].body == "good morning"
        assert msgs[0].source_format == "csv"
    finally:
        os.unlink(p)


# --- Format detection ---

def test_detect_format():
    assert detect_format("chat.txt") == "whatsapp"
    assert detect_format("export.json") == "telegram"
    assert detect_format("sms.csv") == "csv"


# --- Model serialisation ---

def test_message_to_dict():
    m = Message(timestamp="2025-01-01T10:00:00", sender="Sam", body="test", line_number=1, source_format="whatsapp")
    d = m.to_dict()
    assert d["sender"] == "Sam"
    assert d["source_format"] == "whatsapp"


def test_message_to_json():
    m = Message(timestamp="2025-01-01T10:00:00", sender="Sam", body="test", line_number=1)
    parsed = json.loads(m.to_json())
    assert parsed["body"] == "test"
