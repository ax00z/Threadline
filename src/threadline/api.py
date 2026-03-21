from __future__ import annotations
import tempfile
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import networkx as nx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from threadline.anomaly import detect_anomalies
from threadline.crypto import build_chain, verify_chain
from threadline.ner import extract_from_messages
from threadline.pairwise import compute_pairwise
from threadline.parser import parse_file, detect_format
from threadline.sentiment import analyze_sentiment
from threadline.store import MessageStore
from threadline.heatmap import build_heatmap
from threadline.response_time import compute_response_times
from threadline.intel import analyze_intel

app = FastAPI(title="Threadline")
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000", "http://127.0.0.1:8001", "http://localhost:8001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_WEB_BUILD = Path(__file__).resolve().parent.parent.parent / "web" / "build"

_ACCEPTED = {".txt", ".json", ".csv"}
_REPLY_WINDOW_SECS = 3600  # 1 hour window for consecutive-message edges

_store = MessageStore()


def _build_graph(messages: list[dict]) -> dict:
    G = nx.Graph()

    sender_counts: Counter[str] = Counter(m["sender"] for m in messages)
    for sender, count in sender_counts.items():
        G.add_node(sender, message_count=count)

    def _add_edge(a: str, b: str):
        if a == b:
            return
        if G.has_edge(a, b):
            G[a][b]["weight"] += 1
        else:
            G.add_edge(a, b, weight=1)

    # Build message_id → sender lookup for reply-based edges
    id_to_sender: dict = {}
    for m in messages:
        mid = m.get("message_id")
        if mid is not None:
            id_to_sender[mid] = m["sender"]

    # Pre-parse timestamps once
    parsed_ts: list[datetime | None] = []
    for m in messages:
        try:
            parsed_ts.append(datetime.fromisoformat(m["timestamp"]))
        except (ValueError, TypeError, KeyError):
            parsed_ts.append(None)

    for i, msg in enumerate(messages):
        # Reply-based edges (Telegram): direct connection between replier and replied-to
        reply_to = msg.get("reply_to")
        if reply_to is not None and reply_to in id_to_sender:
            _add_edge(msg["sender"], id_to_sender[reply_to])

        # Consecutive-message edges (all formats): within time window
        if i < len(messages) - 1:
            a = msg["sender"]
            b = messages[i + 1]["sender"]
            if a == b:
                continue
            ta, tb = parsed_ts[i], parsed_ts[i + 1]
            if ta is not None and tb is not None:
                if abs((tb - ta).total_seconds()) > _REPLY_WINDOW_SECS:
                    continue
            _add_edge(a, b)

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
        t0 = time.perf_counter()
        messages = [msg.to_dict() for msg in parse_file(tmp_path)]
        t1 = time.perf_counter()
        print(f"[perf] parse: {t1-t0:.2f}s ({len(messages)} msgs)")

        messages = build_chain(messages)
        t2 = time.perf_counter()
        print(f"[perf] chain: {t2-t1:.2f}s")

        if not messages:
            raise HTTPException(422, "No messages found in file")

        # Run heavy analysis steps in parallel (all read-only on messages)
        results: dict = {}
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(_build_graph, messages): "graph",
                pool.submit(extract_from_messages, messages): "ner",
                pool.submit(analyze_sentiment, messages): "sentiment",
                pool.submit(compute_pairwise, messages): "pairwise",
                pool.submit(build_heatmap, messages): "heatmap",
                pool.submit(compute_response_times, messages): "response_times",
                pool.submit(analyze_intel, messages): "intel",
            }
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()
                print(f"[perf] {name}: {time.perf_counter()-t2:.2f}s")

        graph = results["graph"]
        ner = results["ner"]

        # Anomaly detection needs NER output, run after
        anomalies = detect_anomalies(messages, ner_entities=ner.get("entities"))
        t3 = time.perf_counter()
        print(f"[perf] anomalies: {t3-t2:.2f}s")

        _store.load(messages)

        stats = {
            "total_messages": len(messages),
            "unique_senders": len(graph["sender_counts"]),
            "senders": graph["sender_counts"],
            "first_message": messages[0]["timestamp"],
            "last_message": messages[-1]["timestamp"],
            "source_format": fmt,
        }

        chain = {"valid": True, "checked": len(messages), "broken_at": None}

        # Strip messages to only fields the frontend needs
        slim_messages = [
            {
                "timestamp": m["timestamp"],
                "sender": m["sender"],
                "body": m["body"],
                "line_number": m.get("line_number", 0),
                "chain_index": m.get("chain_index"),
                "source_format": m.get("source_format", ""),
            }
            for m in messages
        ]

        print(f"[perf] TOTAL: {time.perf_counter()-t0:.2f}s")

        return {
            "messages": slim_messages,
            "stats": stats,
            "graph": graph,
            "ner": ner,
            "chain": chain,
            "anomalies": anomalies,
            "pairwise": results["pairwise"],
            "sentiment": results["sentiment"],
            "heatmap": results["heatmap"],
            "response_times": results["response_times"],
            "intel": results["intel"],
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


if _WEB_BUILD.is_dir():
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file = _WEB_BUILD / path
        if file.is_file():
            return FileResponse(file)
        return FileResponse(_WEB_BUILD / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("threadline.api:app", host="127.0.0.1", port=8000, reload=True)
