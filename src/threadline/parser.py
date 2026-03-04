from __future__ import annotations
import csv
import json
import re
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

_SYSTEM_TOKENS = (
    "Messages and calls are end-to-end encrypted",
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
    return any(t.lower() in lo for t in _SYSTEM_TOKENS)


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


def _parse_whatsapp(path: str) -> Generator[Message, None, None]:
    pending_ts = pending_sender = pending_body = None
    line_num = 0

    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line_num += 1
            line = raw.rstrip("\n").rstrip("\r")

            m = _BRACKET.match(line) or _DASH.match(line)
            if m:
                if pending_ts and not _is_system(pending_body or ""):
                    yield Message(
                        timestamp=pending_ts,
                        sender=pending_sender.strip(),
                        body=pending_body.strip(),
                        line_number=line_num - 1,
                        source_format="whatsapp",
                    )
                pending_ts = _parse_whatsapp_ts(m.group(1), m.group(2))
                pending_sender = m.group(3)
                pending_body = m.group(4)
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
        sender = msg.get("from") or msg.get("actor") or "Unknown"
        ts_raw = msg.get("date") or msg.get("date_unixtime", "")

        if str(ts_raw).isdigit():
            import datetime
            ts = datetime.datetime.utcfromtimestamp(int(ts_raw)).strftime(
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

        yield Message(
            timestamp=ts,
            sender=str(sender),
            body=str(text).strip(),
            line_number=i,
            source_format="telegram",
        )


def _parse_csv(path: str) -> Generator[Message, None, None]:
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        reader = csv.DictReader(fh, dialect=dialect)

        # map common field name variants to our canonical names
        _TS_KEYS = ("timestamp", "date", "datetime", "time", "sent", "date_sent")
        _FROM_KEYS = ("sender", "from", "from_name", "name", "author", "contact")
        _BODY_KEYS = ("body", "message", "text", "content", "msg")

        def pick(row: dict, candidates: tuple) -> str:
            lc = {k.lower(): v for k, v in row.items()}
            for c in candidates:
                if c in lc:
                    return lc[c] or ""
            return ""

        for i, row in enumerate(reader):
            ts = pick(row, _TS_KEYS)
            sender = pick(row, _FROM_KEYS)
            body = pick(row, _BODY_KEYS)
            if not body:
                continue
            yield Message(
                timestamp=ts or "",
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
