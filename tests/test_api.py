"""API endpoint tests — upload, health, query, error handling."""

import io
import json
import pytest
from fastapi.testclient import TestClient
from threadline.api import app, _DENSE_GRAPH_EDGE_THRESHOLD, _build_graph


client = TestClient(app)


WA_SAMPLE = (
    "[1/15/25, 2:34 PM] Marcus: hey\n"
    "[1/15/25, 3:01 PM] Fiona: hi\n"
    "[1/15/25, 3:02 PM] Marcus: what's up\n"
)

TELEGRAM_SAMPLE = json.dumps({
    "name": "test",
    "type": "personal_chat",
    "messages": [
        {"id": 1, "type": "message", "date": "2025-01-10T10:00:00", "from": "Alpha", "text": "hey"},
        {"id": 2, "type": "message", "date": "2025-01-10T10:01:00", "from": "Bravo", "text": "yo"},
    ],
})

CSV_SAMPLE = "timestamp,sender,body\n2025-01-01T10:00:00,Petra,hello\n2025-01-01T10:01:00,Sven,hi\n"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_upload_whatsapp():
    r = client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    assert r.status_code == 200
    data = r.json()
    assert data["stats"]["total_messages"] == 3
    assert data["stats"]["unique_senders"] == 2
    assert data["chain"]["valid"] is True
    assert data["chain"]["checked"] == 3


def test_upload_telegram():
    r = client.post("/api/upload", files={"file": ("export.json", TELEGRAM_SAMPLE, "application/json")})
    assert r.status_code == 200
    data = r.json()
    assert data["stats"]["total_messages"] == 2
    assert data["chain"]["valid"] is True


def test_upload_csv():
    r = client.post("/api/upload", files={"file": ("sms.csv", CSV_SAMPLE, "text/csv")})
    assert r.status_code == 200
    data = r.json()
    assert data["stats"]["total_messages"] == 2
    assert data["chain"]["valid"] is True


def test_upload_returns_graph():
    r = client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    data = r.json()
    assert "graph" in data
    assert len(data["graph"]["nodes"]) == 2
    assert len(data["graph"]["edges"]) >= 1


def test_build_graph_prunes_dense_networks():
    participants = [f"Person-{i:02d}" for i in range(30)]
    messages = []

    for cycle in range(12):
        for idx, sender in enumerate(participants):
            messages.append({
                "sender": sender,
                "timestamp": f"2025-01-01T00:{cycle:02d}:{idx:02d}",
                "body": f"msg {cycle}-{idx}",
            })

    graph = _build_graph(messages)

    assert len(graph["nodes"]) == len(participants)
    assert len(graph["edges"]) <= max(_DENSE_GRAPH_EDGE_THRESHOLD, len(participants) * 5)


def test_upload_returns_ner():
    chat = "[1/15/25, 2:34 PM] Marcus: call 555-867-5309\n"
    r = client.post("/api/upload", files={"file": ("chat.txt", chat, "text/plain")})
    data = r.json()
    assert data["ner"]["total_found"] >= 1


def test_upload_messages_have_chain_index():
    r = client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    data = r.json()
    for msg in data["messages"]:
        assert "chain_index" in msg


def test_upload_chain_valid():
    r = client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    chain = r.json()["chain"]
    assert chain["valid"] is True
    assert chain["checked"] > 0


def test_upload_rejects_unsupported_extension():
    r = client.post("/api/upload", files={"file": ("data.pdf", b"junk", "application/pdf")})
    assert r.status_code == 400


def test_upload_rejects_empty_file():
    r = client.post("/api/upload", files={"file": ("empty.txt", "", "text/plain")})
    assert r.status_code == 422


def test_query_after_upload():
    client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    r = client.post("/api/query", json={"sql": "SELECT COUNT(*) as cnt FROM messages"})
    assert r.status_code == 200
    data = r.json()
    assert data["row_count"] == 1
    assert data["rows"][0][0] == "3"


def test_query_select_only():
    client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    r = client.post("/api/query", json={"sql": "DROP TABLE messages"})
    assert r.status_code == 400


def test_query_delete_blocked():
    client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    r = client.post("/api/query", json={"sql": "DELETE FROM messages WHERE sender = 'Marcus'"})
    assert r.status_code == 400


def test_query_with_filter():
    client.post("/api/upload", files={"file": ("chat.txt", WA_SAMPLE, "text/plain")})
    r = client.post("/api/query", json={"sql": "SELECT * FROM messages WHERE sender = 'Marcus'"})
    assert r.status_code == 200
    assert r.json()["row_count"] == 2
