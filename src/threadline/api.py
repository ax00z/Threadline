from __future__ import annotations
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from threadline.parser import parse_file, detect_format

app = FastAPI(title="Threadline")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ACCEPTED = {".txt", ".json", ".csv"}
_REPLY_WINDOW_SECS = 300  # 5 min, messages within this gap are considered a reply chain


def _build_graph(messages: list[dict]) -> dict:
    G = nx.Graph()

    sender_counts: Counter[str] = Counter(m["sender"] for m in messages)
    for sender, count in sender_counts.items():
        G.add_node(sender, message_count=count)

    # edges: sender -> next sender within the reply window
    for i in range(len(messages) - 1):
        a = messages[i]["sender"]
        b = messages[i + 1]["sender"]
        if a == b:
            continue
        try:
            ta = datetime.fromisoformat(messages[i]["timestamp"])
            tb = datetime.fromisoformat(messages[i + 1]["timestamp"])
            if abs((tb - ta).total_seconds()) > _REPLY_WINDOW_SECS:
                continue
        except ValueError:
            pass

        if G.has_edge(a, b):
            G[a][b]["weight"] += 1
        else:
            G.add_edge(a, b, weight=1)

    if len(G.nodes) == 0:
        return {"nodes": [], "edges": []}

    degree_c = nx.degree_centrality(G)
    between_c = nx.betweenness_centrality(G, weight="weight")
    close_c = nx.closeness_centrality(G)

    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "message_count": data.get("message_count", 0),
            "degree_centrality": round(degree_c.get(node, 0), 4),
            "betweenness_centrality": round(between_c.get(node, 0), 4),
            "closeness_centrality": round(close_c.get(node, 0), 4),
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1),
        })

    nodes.sort(key=lambda n: n["message_count"], reverse=True)

    return {"nodes": nodes, "edges": edges}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename or ""
    ext = Path(name).suffix.lower()
    if ext not in _ACCEPTED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Send .txt, .json, or .csv")

    suffix = ext if ext else ".txt"
    with tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        messages = []
        sender_counts: Counter[str] = Counter()
        for msg in parse_file(tmp_path):
            d = msg.to_dict()
            messages.append(d)
            sender_counts[msg.sender] += 1

        if not messages:
            raise HTTPException(422, "No messages found in file")

        stats = {
            "total_messages": len(messages),
            "unique_senders": len(sender_counts),
            "senders": dict(sender_counts.most_common()),
            "first_message": messages[0]["timestamp"],
            "last_message": messages[-1]["timestamp"],
            "source_format": detect_format(tmp_path),
        }
        graph = _build_graph(messages)
        return {"messages": messages, "stats": stats, "graph": graph}
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("threadline.api:app", host="127.0.0.1", port=8000, reload=True)
