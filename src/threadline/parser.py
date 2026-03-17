from __future__ import annotations
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from .models import Message

# WhatsApp bracket:  [1/15/25, 2:34:00 PM] Name: body
_BRACKET = re.compile(
    r"^\[(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]\s*([^:]+):\s*(.+)$"
)

# WhatsApp dash:  1/15/25, 2:34 AM - Name: body
_DASH = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\s*-\s*([^:]+):\s*(.+)$"
)

# WhatsApp compact (no delimiters):  [010125, 080000] Name: body  (MMDDYY, HHMMSS)
_COMPACT = re.compile(
    r"^\[(\d{6}),\s*(\d{6})\]\s*([^:]+):\s*(.+)$"
)

_SYSTEM_TOKENS = (
    "messages and calls are end-to-end encrypted",
    "created group",
    "added",
    "removed",
    "left",
    "changed the subject",
    "changed this group",
    "changed their phone number",
    "security code changed",
    "joined using this group",
    "pinned a message",
    "disappeared messages",
    "turned on",
    "turned off",
)


def _is_system(body: str) -> bool:
    lo = body.lower()
    return any(t in lo for t in _SYSTEM_TOKENS)


def _parse_whatsapp_ts(date_str: str, time_str: str) -> str:
    parts = date_str.split("/")
    month = int(parts[0])
    day = int(parts[1])
    year = int(parts[2])
    if year < 100:
        year += 2000

    time_str = time_str.strip()
    ampm = None
    if time_str.upper().endswith("AM") or time_str.upper().endswith("PM"):
        ampm = time_str[-2:].upper()
        time_str = time_str[:-2].strip()

    time_parts = time_str.split(":")
    hour = int(time_parts[0])
    minute = int(time_parts[1])
    second = int(time_parts[2]) if len(time_parts) > 2 else 0

    if ampm == "PM" and hour != 12:
        hour += 12
    elif ampm == "AM" and hour == 12:
        hour = 0

    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"


def _parse_compact_ts(date_str: str, time_str: str) -> str:
    """Parse compact MMDDYY, HHMMSS format (no delimiters)."""
    month = int(date_str[0:2])
    day = int(date_str[2:4])
    year = int(date_str[4:6]) + 2000
    hour = int(time_str[0:2])
    minute = int(time_str[2:4])
    second = int(time_str[4:6])
    return f"{year:04d}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"


def _parse_whatsapp(path: str) -> Generator[Message, None, None]:
    pending_ts = pending_sender = pending_body = None
    line_num = 0

    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line_num += 1
            line = raw.rstrip("\n").rstrip("\r")

            m = _BRACKET.match(line) or _DASH.match(line)
            mc = _COMPACT.match(line) if not m else None
            if m or mc:
                if pending_ts and not _is_system(pending_body or ""):
                    yield Message(
                        timestamp=pending_ts,
                        sender=pending_sender.strip(),
                        body=pending_body.strip(),
                        line_number=line_num - 1,
                        source_format="whatsapp",
                    )
                match = m or mc
                if mc:
                    pending_ts = _parse_compact_ts(match.group(1), match.group(2))
                else:
                    pending_ts = _parse_whatsapp_ts(match.group(1), match.group(2))
                pending_sender = match.group(3)
                pending_body = match.group(4)
            elif pending_ts and line:
                pending_body = (pending_body or "") + "\n" + line

    if pending_ts and not _is_system(pending_body or ""):
        yield Message(
            timestamp=pending_ts,
            sender=pending_sender.strip(),
            body=pending_body.strip(),
            line_number=line_num,
            source_format="whatsapp",
        )


def _parse_telegram(path: str) -> Generator[Message, None, None]:
    with open(path, encoding="utf-8", errors="replace") as fh:
        data = json.load(fh)

    messages = data if isinstance(data, list) else data.get("messages", [])

    for i, msg in enumerate(messages):
        if msg.get("type") != "message":
            continue

        # Resolve sender: from → from_id → forwarded_from → "Unknown"
        sender = msg.get("from") or None
        if not sender:
            fid = msg.get("from_id")
            if fid and str(fid) not in ("None", "null"):
                sender = str(fid)
        if not sender:
            sender = msg.get("forwarded_from") or "Unknown"

        ts_raw = msg.get("date") or msg.get("date_unixtime", "")

        if str(ts_raw).isdigit():
            ts = datetime.utcfromtimestamp(int(ts_raw)).strftime(
                "%Y-%m-%dT%H:%M:%S"
            )
        else:
            ts = str(ts_raw)

        text = msg.get("text", "")
        if isinstance(text, list):
            parts = []
            for part in text:
                if isinstance(part, str):
                    parts.append(part)
                elif isinstance(part, dict):
                    parts.append(part.get("text", ""))
            text = "".join(parts)

        if not text.strip():
            continue

        # Store reply_to for graph edge building
        reply_to = msg.get("reply_to_message_id")

        yield Message(
            timestamp=ts,
            sender=str(sender),
            body=str(text).strip(),
            line_number=i,
            source_format="telegram",
            reply_to=reply_to,
            message_id=msg.get("id"),
        )


_CSV_TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%SZ",       # ISO with Z
    "%Y-%m-%dT%H:%M:%S",        # ISO
    "%Y-%m-%d %H:%M:%S",        # Standard
    "%Y-%m-%d %H:%M",           # No seconds
    "%m/%d/%Y %H:%M:%S",        # US
    "%m/%d/%Y %I:%M:%S %p",     # US 12h
    "%d/%m/%Y %H:%M:%S",        # EU
    "%b %d, %Y %I:%M %p",       # Aug 12, 2025 04:22 PM
    "%b %d, %Y %I:%M:%S %p",    # Aug 12, 2025 04:22:00 PM
    "%B %d, %Y %I:%M %p",       # August 12, 2025 04:22 PM
    "%d-%m-%Y %H:%M:%S",        # EU dash
    "%Y/%m/%d %H:%M:%S",        # JP
]


def _normalize_ts(raw: str) -> str:
    """Try to parse a timestamp string into ISO format."""
    raw = raw.strip().strip('"')
    if not raw:
        return ""

    # Unix epoch (all digits, 10+ chars)
    if raw.isdigit() and len(raw) >= 10:
        try:
            return datetime.utcfromtimestamp(int(raw)).strftime("%Y-%m-%dT%H:%M:%S")
        except (ValueError, OSError):
            pass

    # Already ISO-ish
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", raw):
        return raw.replace("Z", "")

    # Try known formats
    for fmt in _CSV_TS_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue

    return raw


def _fuzzy_pick(row: dict, candidates: tuple) -> str:
    """Match column names flexibly: strip, lowercase, check if any candidate
    word appears in the column name or vice versa."""
    cleaned = {k.strip().lower(): v for k, v in row.items()}

    # Exact match first
    for c in candidates:
        if c in cleaned:
            return cleaned[c] or ""

    # Substring match: candidate appears inside column name
    for col_key, val in cleaned.items():
        for c in candidates:
            if c in col_key or col_key.startswith(c):
                return val or ""

    # Reverse substring: column name word appears in a candidate
    for col_key, val in cleaned.items():
        col_words = re.split(r"[\s_\-()]+", col_key)
        for word in col_words:
            if word and word in candidates:
                return val or ""

    return ""


def _parse_csv(path: str) -> Generator[Message, None, None]:
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(8192)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(fh, dialect=dialect)

        _TS_KEYS = ("timestamp", "date", "datetime", "time", "sent", "date_sent", "created")
        _FROM_KEYS = ("sender", "from", "from_name", "name", "author", "contact", "user", "party", "source", "originator")
        _BODY_KEYS = ("body", "message", "text", "content", "msg")

        for i, row in enumerate(reader):
            ts = _fuzzy_pick(row, _TS_KEYS)
            sender = _fuzzy_pick(row, _FROM_KEYS)
            body = _fuzzy_pick(row, _BODY_KEYS)
            if not body:
                continue
            yield Message(
                timestamp=_normalize_ts(ts) if ts else "",
                sender=sender or "Unknown",
                body=body.strip(),
                line_number=i,
                source_format="csv",
            )


def detect_format(path: str) -> str:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".json":
        return "telegram"
    if ext == ".csv":
        return "csv"
    return "whatsapp"


def parse_file(path: str) -> Generator[Message, None, None]:
    fmt = detect_format(path)
    if fmt == "telegram":
        yield from _parse_telegram(path)
    elif fmt == "csv":
        yield from _parse_csv(path)
    else:
        yield from _parse_whatsapp(path)
