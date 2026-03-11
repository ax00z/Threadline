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


# try loading spacy, totally fine if it's not installed or broken
_nlp = None
try:
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import spacy
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
except Exception:
    _nlp = None

_SPACY_LABEL_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORG",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
}


# this is pretty loose, catches some junk but better than missing real numbers
_PHONE = re.compile(
    r"(?<!\d)"
    r"(?:\+?\d{1,3}[\s\-.]?)?"
    r"(?:\(?\d{2,4}\)?[\s\-.]?)"
    r"\d{3,4}[\s\-.]?"
    r"\d{3,4}"
    r"(?!\d)",
)

_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
)

_URL = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+",
)

_MONEY = re.compile(
    r"(?:[$\u20ac\u00a3])\s?\d[\d,]*\.?\d*"
    r"|"
    r"\d[\d,]*\.?\d*\s?(?:USD|EUR|GBP|CAD|AUD|BTC|ETH)",
    re.IGNORECASE,
)

_DATE = re.compile(
    r"\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b"
    r"|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
    r"[\s\-]\d{1,2}(?:[\s,\-]+\d{2,4})?\b",
    re.IGNORECASE,
)

# TODO: add monero, litecoin etc
_CRYPTO = re.compile(
    r"\b(?:"
    r"(?:bc1|[13])[a-zA-HJ-NP-Z0-9]{25,39}"  # btc
    r"|"
    r"0x[0-9a-fA-F]{40}"  # eth
    r")\b",
)

_COORDS = re.compile(
    r"-?\d{1,3}\.\d{4,},\s?-?\d{1,3}\.\d{4,}",
)


_PATTERNS: list[tuple[re.Pattern, str]] = [
    (_URL, "URL"),
    (_EMAIL, "EMAIL"),
    (_CRYPTO, "CRYPTO_WALLET"),
    (_MONEY, "MONEY"),
    (_PHONE, "PHONE"),
    (_COORDS, "COORDINATES"),
    (_DATE, "DATE"),
]


def _overlaps(span: tuple[int, int], seen: set[tuple[int, int]]) -> bool:
    for s, e in seen:
        if span[0] < e and span[1] > s:
            return True
    return False


def extract_entities(text: str) -> list[Entity]:
    entities: list[Entity] = []
    seen_spans: set[tuple[int, int]] = set()

    # regex first — these are deterministic and take priority
    for pattern, label in _PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if _overlaps(span, seen_spans):
                continue
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

    # spacy pass for names/orgs/locations
    if _nlp is not None and text.strip():
        doc = _nlp(text)
        for ent in doc.ents:
            mapped = _SPACY_LABEL_MAP.get(ent.label_)
            if not mapped:
                continue
            span = (ent.start_char, ent.end_char)
            if _overlaps(span, seen_spans):
                continue
            # skip single-char or whitespace-only
            cleaned = ent.text.strip()
            if len(cleaned) < 2:
                continue
            entities.append(Entity(
                text=cleaned,
                label=mapped,
                start=ent.start_char,
                end=ent.end_char,
            ))
            seen_spans.add(span)

    entities.sort(key=lambda e: e.start)
    return entities


def spacy_available() -> bool:
    return _nlp is not None


def extract_from_messages(messages: list[dict]) -> dict:
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
            if e.text not in sender_entities[sender][e.label]:
                sender_entities[sender][e.label].append(e.text)

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
        "spacy_active": spacy_available(),
    }
