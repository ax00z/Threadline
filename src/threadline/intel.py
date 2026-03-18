"""Algorithmic intelligence module — TF-IDF keywords, topic clustering, threat scoring.

Pure Python + scikit-learn. No LLM, no cloud APIs.
Falls back gracefully if sklearn is not installed.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


def _available() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


# ── Lightweight TF-IDF (no sklearn needed) ──────────────────────────

_STOP = frozenset(
    "i me my we our you your he she it they them his her its a an the "
    "and but or so if in on at to for of by with is am are was were be "
    "been being have has had do does did will would shall should can "
    "could may might must not no nor this that these those what which "
    "who whom how when where why all each every some any few more most "
    "other another such only own same than too very just about above "
    "after again also as before between both during from here into "
    "out over then there through under up well back down off because "
    "while ok okay yes yeah sure lol haha hahaha like right got get "
    "going go let know think want need make come take see good really "
    "much even still already also actually anyway oh hey hi hello "
    "thanks thank bye please sorry".split()
)

_WORD_RE = re.compile(r"[a-zA-Z]{3,}")


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOP]


def extract_keywords(messages: list[dict], top_n: int = 30) -> list[dict]:
    """Extract top keywords using TF-IDF across per-sender documents."""
    # Build one "document" per sender — concat all their message bodies then tokenize once
    sender_bodies: dict[str, list[str]] = {}
    for m in messages:
        sender = m.get("sender", "")
        body = m.get("body", "")
        if body:
            sender_bodies.setdefault(sender, []).append(body)

    # Tokenize once per sender (batch) instead of per message
    sender_docs: dict[str, list[str]] = {}
    for sender, bodies in sender_bodies.items():
        sender_docs[sender] = _tokenize(" ".join(bodies))

    if not sender_docs:
        return []

    # Compute IDF
    n_docs = len(sender_docs)
    doc_freq: Counter[str] = Counter()
    for tokens in sender_docs.values():
        doc_freq.update(set(tokens))

    # Compute TF-IDF per word (global)
    global_tf: Counter[str] = Counter()
    for tokens in sender_docs.values():
        global_tf.update(tokens)

    scored: list[tuple[str, float]] = []
    for word, tf in global_tf.items():
        df = doc_freq.get(word, 1)
        idf = math.log((n_docs + 1) / (df + 1)) + 1
        scored.append((word, tf * idf))

    scored.sort(key=lambda x: -x[1])

    # Per-sender breakdown for top keywords
    results = []
    for word, score in scored[:top_n]:
        senders_using = sorted(
            [s for s, tokens in sender_docs.items() if word in tokens]
        )
        results.append({
            "keyword": word,
            "score": round(score, 2),
            "count": global_tf[word],
            "senders": senders_using,
        })
    return results


# ── Topic clustering (sklearn-powered) ──────────────────────────────

def cluster_topics(messages: list[dict], n_clusters: int = 0) -> dict[str, Any]:
    """Cluster messages into topics using TF-IDF + KMeans.

    Auto-selects n_clusters if 0. Returns topics with top terms and member counts.
    """
    if not _available() or len(messages) < 10:
        return {"available": False, "topics": []}

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import MiniBatchKMeans

    # Sample if too many messages — TF-IDF on 100k+ docs is slow
    import random
    sample = messages
    if len(messages) > 5000:
        rng = random.Random(42)
        sample = rng.sample(messages, 5000)

    bodies = [m.get("body", "") for m in sample]
    senders = [m.get("sender", "") for m in sample]

    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words="english",
        min_df=2,
        max_df=0.9,
        token_pattern=r"[a-zA-Z]{3,}",
    )

    try:
        tfidf = vectorizer.fit_transform(bodies)
    except ValueError:
        return {"available": True, "topics": []}

    if n_clusters == 0:
        n_clusters = max(2, min(8, len(messages) // 50))

    n_clusters = min(n_clusters, tfidf.shape[0])
    km = MiniBatchKMeans(n_clusters=n_clusters, random_state=42, n_init=3)
    labels = km.fit_predict(tfidf)

    feature_names = vectorizer.get_feature_names_out()
    topics = []
    for idx in range(n_clusters):
        mask = [i for i, l in enumerate(labels) if l == idx]
        if not mask:
            continue
        # Top terms from cluster centroid
        centroid = km.cluster_centers_[idx]
        top_indices = centroid.argsort()[-8:][::-1]
        top_terms = [feature_names[i] for i in top_indices if centroid[i] > 0]

        cluster_senders = Counter(senders[i] for i in mask)
        topics.append({
            "id": idx,
            "size": len(mask),
            "top_terms": top_terms,
            "top_senders": [s for s, _ in cluster_senders.most_common(5)],
            "sample": bodies[mask[0]][:120] if mask else "",
        })

    topics.sort(key=lambda t: -t["size"])
    return {"available": True, "topics": topics}


# ── Threat scoring ──────────────────────────────────────────────────

_THREAT_PATTERNS: list[tuple[str, float, str]] = [
    (r"\b(?:kill|murder|shoot|stab|attack|bomb|explod|weapon|gun|knife)\w*\b", 0.9, "violence"),
    (r"\b(?:drug|cocaine|heroin|meth|fentanyl|pills|dose|dealer|stash)\w*\b", 0.8, "narcotics"),
    (r"\b(?:launder|wire\s*transfer|offshore|shell\s*company|crypto\s*wallet)\w*\b", 0.7, "financial"),
    (r"\b(?:blackmail|extort|ransom|threat|intimidat)\w*\b", 0.8, "coercion"),
    (r"\b(?:traffick|smuggl|undocumented|passport|border)\w*\b", 0.8, "trafficking"),
    (r"\b(?:hack|breach|exploit|phish|malware|credential|password)\w*\b", 0.6, "cyber"),
    (r"\b(?:meet|drop|pickup|deliver|handoff|location|spot)\w*\b", 0.3, "logistics"),
    (r"\b(?:burner|untraceable|encrypt|signal|telegram|delete\s*(?:everything|all|chat))\w*\b", 0.5, "opsec"),
]

_COMPILED_THREATS = [(re.compile(p, re.IGNORECASE), w, cat) for p, w, cat in _THREAT_PATTERNS]


def score_threats(messages: list[dict]) -> dict[str, Any]:
    """Score messages for threat indicators. Returns per-sender and per-category breakdown."""
    sender_scores: dict[str, float] = {}
    sender_counts: dict[str, int] = {}
    category_hits: Counter[str] = Counter()
    flagged: list[dict] = []

    # Pre-compute sender message counts for density calc
    sender_msg_counts: Counter[str] = Counter(m.get("sender", "") for m in messages)

    for idx, m in enumerate(messages):
        body = m.get("body", "")
        if not body:
            continue
        sender = m.get("sender", "")
        msg_score = 0.0
        msg_cats: list[str] = []

        for pattern, weight, category in _COMPILED_THREATS:
            if pattern.search(body):
                msg_score += weight
                msg_cats.append(category)
                category_hits[category] += 1

        if msg_score > 0:
            sender_scores[sender] = sender_scores.get(sender, 0) + msg_score
            sender_counts[sender] = sender_counts.get(sender, 0) + 1

            if msg_score >= 0.5:
                flagged.append({
                    "index": idx,
                    "sender": sender,
                    "timestamp": m.get("timestamp", ""),
                    "score": round(msg_score, 2),
                    "categories": msg_cats,
                    "body": body[:200],
                })

    total_msgs = len(messages)
    per_sender: list[dict] = []
    for sender, raw_score in sorted(sender_scores.items(), key=lambda x: -x[1]):
        per_sender.append({
            "sender": sender,
            "raw_score": round(raw_score, 2),
            "flagged_messages": sender_counts[sender],
            "threat_density": round(sender_counts[sender] / max(1, sender_msg_counts[sender]), 3),
        })

    # Overall threat level
    flagged_pct = len(flagged) / max(1, total_msgs)
    if flagged_pct > 0.1:
        level = "high"
    elif flagged_pct > 0.03:
        level = "medium"
    elif flagged_pct > 0:
        level = "low"
    else:
        level = "none"

    return {
        "level": level,
        "flagged_count": len(flagged),
        "total_messages": total_msgs,
        "categories": dict(category_hits.most_common()),
        "per_sender": per_sender,
        "flagged": flagged[:50],  # cap at 50 most relevant
    }


def analyze_intel(messages: list[dict]) -> dict[str, Any]:
    """Run all intelligence analyses and return combined results."""
    return {
        "keywords": extract_keywords(messages),
        "topics": cluster_topics(messages),
        "threats": score_threats(messages),
    }
