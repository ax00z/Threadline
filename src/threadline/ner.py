"""
Regex-based Named Entity Recognition for forensic message analysis.

Air-gapped, zero-dependency NER that extracts investigatively relevant
entities from chat message text: phone numbers, emails, URLs, monetary
amounts, dates, and crypto wallet addresses.

Designed for deterministic, reproducible results (no ML model variance).
"""

from __future__ import annotations
import re
from dataclasses import dataclass, asdict
from typing import Generator


@dataclass(slots=True)
class Entity:
    text: str
    label: str
    start: int
    end: int

    def to_dict(self) -> dict:
        return asdict(self)


# --- Phone numbers ---
# Matches: +1-555-123-4567, (555) 123-4567, 555.123.4567, +44 20 7946 0958
_PHONE = re.compile(
    r"(?<!\d)"                        # not preceded by digit
    r"(?:\+?\d{1,3}[\s\-.]?)?"        # optional country code
    r"(?:\(?\d{2,4}\)?[\s\-.]?)"      # area code
    r"\d{3,4}[\s\-.]?"                # first group
    r"\d{3,4}"                        # second group
    r"(?!\d)",                         # not followed by digit
)

# --- Email addresses ---
_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

# --- URLs ---
_URL = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+",
)

# --- Money / currency amounts ---
_MONEY = re.compile(
    r"(?:[$\u20ac\u00a3])\s?\d[\d,]*\.?\d*"  # $100, EUR 50, $1,234.56
    r"|"
    r"\d[\d,]*\.?\d*\s?(?:USD|EUR|GBP|CAD|AUD|BTC|ETH)",
    re.IGNORECASE,
)

# --- Dates (various formats) ---
_DATE = re.compile(
    r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"  # 1/15/2025, 15-01-2025
    r"|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"[\s\-]\d{1,2}(?:[\s,\-]+\d{2,4})?\b",      # Jan 15, 2025
    re.IGNORECASE,
)

# --- Crypto wallet addresses ---
_CRYPTO = re.compile(
    r"\b(?:"
    r"(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}"      # Bitcoin (base58/bech32)
    r"|"
    r"0x[0-9a-fA-F]{40}"                            # Ethereum
    r")\b",
)

# --- Coordinates (lat/long) ---
_COORDS = re.compile(
    r"-?\d{1,3}\.\d{4,},\s?-?\d{1,3}\.\d{4,}",
)


# All patterns with their labels, ordered by priority
_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_URL, "URL"),
    (_EMAIL, "EMAIL"),
    (_CRYPTO, "CRYPTO_WALLET"),
    (_MONEY, "MONEY"),
    (_PHONE, "PHONE"),
    (_COORDS, "COORDINATES"),
    (_DATE, "DATE"),
]


def extract_entities(text: str) -> list[Entity]:
    """Extract all entities from a single message body."""
    entities: list[Entity] = []
    seen_spans: set[tuple[int, int]] = set()

    for pattern, label in _PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            # Skip if this span overlaps with an already-found entity
            if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
                continue
            # Skip very short matches (likely false positives)
            match_text = m.group().strip()
            if label == "PHONE" and len(re.sub(r"\D", "", match_text)) < 7:
                continue
            entities.append(Entity(
                text=match_text,
                label=label,
                start=m.start(),
                end=m.end(),
            ))
            seen_spans.add(span)

    entities.sort(key=lambda e: e.start)
    return entities


def extract_from_messages(
    messages: list[dict],
) -> dict:
    """Run NER across all messages. Returns entity summary + per-sender breakdown."""
    all_entities: list[dict] = []
    label_counts: dict[str, int] = {}
    sender_entities: dict[str, dict[str, list[str]]] = {}

    for msg in messages:
        body = msg.get("body", "")
        sender = msg.get("sender", "Unknown")
        ents = extract_entities(body)

        if not ents:
            continue

        for e in ents:
            ent_dict = e.to_dict()
            ent_dict["sender"] = sender
            ent_dict["timestamp"] = msg.get("timestamp", "")
            all_entities.append(ent_dict)

            label_counts[e.label] = label_counts.get(e.label, 0) + 1

            if sender not in sender_entities:
                sender_entities[sender] = {}
            if e.label not in sender_entities[sender]:
                sender_entities[sender][e.label] = []
            # Deduplicate per sender
            if e.text not in sender_entities[sender][e.label]:
                sender_entities[sender][e.label].append(e.text)

    # Build unique entities list (deduplicated)
    unique: dict[str, dict] = {}
    for e in all_entities:
        key = f"{e['label']}:{e['text']}"
        if key not in unique:
            unique[key] = {
                "text": e["text"],
                "label": e["label"],
                "count": 0,
                "senders": [],
            }
        unique[key]["count"] += 1
        if e["sender"] not in unique[key]["senders"]:
            unique[key]["senders"].append(e["sender"])

    unique_list = sorted(unique.values(), key=lambda x: x["count"], reverse=True)

    return {
        "entities": all_entities,
        "unique_entities": unique_list,
        "label_counts": label_counts,
        "sender_entities": sender_entities,
        "total_found": len(all_entities),
    }
