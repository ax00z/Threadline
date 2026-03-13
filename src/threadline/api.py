from __future__ import annotations
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel

from threadline.anomaly import detect_anomalies
from threadline.crypto import build_chain, verify_chain
from threadline.ner import extract_from_messages
from threadline.pairwise import compute_pairwise
from threadline.parser import parse_file, detect_format
from threadline.store import MessageStore

app = FastAPI(title="Threadline")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_ACCEPTED = {".txt", ".json", ".csv"}
_REPLY_WINDOW_SECS = 300

_store = MessageStore()


def _build_graph(messages: list[dict]) -> dict:
    G = nx.Graph()

    sender_counts: Counter[str] = Counter(m["sender"] for m in messages)
    for sender, count in sender_counts.items():
        G.add_node(sender, message_count=count)

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
        return {"nodes": [], "edges": [], "communities": [], "sender_counts": {}}

    # TODO: these get slow on big graphs, might need to cache or run async
    degree_c = nx.degree_centrality(G)
    between_c = nx.betweenness_centrality(G, weight="weight")
    close_c = nx.closeness_centrality(G)
    pagerank = nx.pagerank(G, weight="weight")

    community_sets = nx.community.louvain_communities(G, weight="weight", seed=42)
    node_community: dict[str, int] = {}
    for idx, members in enumerate(community_sets):
        for member in members:
            node_community[member] = idx

    nodes = []
    for node, data in G.nodes(data=True):
        nodes.append({
            "id": node,
            "message_count": data["message_count"],
            "degree_centrality": round(degree_c[node], 4),
            "betweenness_centrality": round(between_c[node], 4),
            "closeness_centrality": round(close_c[node], 4),
            "pagerank": round(pagerank[node], 4),
            "community": node_community.get(node, 0),
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data["weight"],
        })

    nodes.sort(key=lambda n: n["message_count"], reverse=True)

    communities = []
    for idx, members in enumerate(community_sets):
        community_nodes = [n for n in nodes if n["community"] == idx]
        communities.append({
            "id": idx,
            "members": sorted(members),
            "size": len(members),
            "total_messages": sum(n["message_count"] for n in community_nodes),
        })
    communities.sort(key=lambda c: c["total_messages"], reverse=True)

    return {
        "nodes": nodes,
        "edges": edges,
        "communities": communities,
        "sender_counts": dict(sender_counts.most_common()),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename or ""
    ext = Path(name).suffix.lower()
    if ext not in _ACCEPTED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Send .txt, .json, or .csv")

    fmt = detect_format(name)
    with tempfile.NamedTemporaryFile(mode="wb", suffix=ext, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        messages = [msg.to_dict() for msg in parse_file(tmp_path)]
        messages = build_chain(messages)

        if not messages:
            raise HTTPException(422, "No messages found in file")

        graph = _build_graph(messages)
        ner = extract_from_messages(messages)
        _store.load(messages)

        stats = {
            "total_messages": len(messages),
            "unique_senders": len(graph["sender_counts"]),
            "senders": graph["sender_counts"],
            "first_message": messages[0]["timestamp"],
            "last_message": messages[-1]["timestamp"],
            "source_format": fmt,
        }

        chain = verify_chain(messages)
        anomalies = detect_anomalies(messages, ner_entities=ner.get("entities"))
        pairwise = compute_pairwise(messages)

        return {
            "messages": messages,
            "stats": stats,
            "graph": graph,
            "ner": ner,
            "chain": chain,
            "anomalies": anomalies,
            "pairwise": pairwise,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


class QueryRequest(BaseModel):
    sql: str


@app.post("/api/query")
async def query(req: QueryRequest):
    result = _store.query(req.sql)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("threadline.api:app", host="127.0.0.1", port=8000, reload=True)
