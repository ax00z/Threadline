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


def _extract_regex_only(text: str) -> list[Entity]:
    """Fast regex-only extraction (no spaCy)."""
    entities: list[Entity] = []
    seen_spans: set[tuple[int, int]] = set()
    for pattern, label in _PATTERNS:
        for m in pattern.finditer(text):
            span = (m.start(), m.end())
            if _overlaps(span, seen_spans):
                continue
            match_text = m.group().strip()
            if label == "PHONE" and len(re.sub(r"\D", "", match_text)) < 7:
                continue
            entities.append(Entity(text=match_text, label=label, start=m.start(), end=m.end()))
            seen_spans.add(span)
    return entities


def extract_from_messages(messages: list[dict], *, _body_cache: dict | None = None) -> dict:
    label_counts: dict[str, int] = {}
    sender_entities: dict[str, dict[str, set[str]]] = {}
    unique: dict[str, dict] = {}
    total_found = 0
    cache = _body_cache if _body_cache is not None else {}

    # Phase 1: fast regex pass on all messages
    for msg in messages:
        body = msg.get("body", "")
        if not body:
            continue
        sender = msg.get("sender", "Unknown")

        if body in cache:
            ents = cache[body]
        else:
            ents = _extract_regex_only(body)
            if len(body) < 200:
                cache[body] = ents

        for e in ents:
            total_found += 1
            label_counts[e.label] = label_counts.get(e.label, 0) + 1
            sender_entities.setdefault(sender, {}).setdefault(e.label, set()).add(e.text)
            key = f"{e.label}:{e.text}"
            if key not in unique:
                unique[key] = {"text": e.text, "label": e.label, "count": 0, "senders": []}
            unique[key]["count"] += 1
            if sender not in unique[key]["senders"]:
                unique[key]["senders"].append(sender)

    # Phase 2: spaCy batch pass (much faster than per-message)
    if _nlp is not None:
        # Deduplicate bodies to avoid processing the same text twice
        body_senders: dict[str, list[str]] = {}
        for msg in messages:
            body = msg.get("body", "")
            if body and len(body) > 2:
                body_senders.setdefault(body, []).append(msg.get("sender", "Unknown"))

        unique_bodies = list(body_senders.keys())
        # Process in batches with nlp.pipe for massive speedup
        for doc, body in zip(_nlp.pipe(unique_bodies, batch_size=256), unique_bodies):
            senders = body_senders[body]
            for ent in doc.ents:
                mapped = _SPACY_LABEL_MAP.get(ent.label_)
                if not mapped:
                    continue
                cleaned = ent.text.strip()
                if len(cleaned) < 2:
                    continue
                count_mult = len(senders)  # how many messages had this body
                total_found += count_mult
                label_counts[mapped] = label_counts.get(mapped, 0) + count_mult
                key = f"{mapped}:{cleaned}"
                if key not in unique:
                    unique[key] = {"text": cleaned, "label": mapped, "count": 0, "senders": []}
                unique[key]["count"] += count_mult
                for s in set(senders):
                    sender_entities.setdefault(s, {}).setdefault(mapped, set()).add(cleaned)
                    if s not in unique[key]["senders"]:
                        unique[key]["senders"].append(s)

    unique_list = sorted(unique.values(), key=lambda x: x["count"], reverse=True)

    # Build minimal entities list for anomaly detector (not the full per-message list)
    entities_summary = [
        {"label": e["label"], "senders": e["senders"]}
        for e in unique_list
    ]

    return {
        "entities": entities_summary,
        "unique_entities": unique_list,
        "label_counts": label_counts,
        "sender_entities": {
            s: {lbl: sorted(texts) for lbl, texts in labels.items()}
            for s, labels in sender_entities.items()
        },
        "total_found": total_found,
        "spacy_active": spacy_available(),
    }
