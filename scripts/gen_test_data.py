#!/usr/bin/env python3
"""Generate synthetic WhatsApp/Telegram/CSV chat data for testing."""
import argparse
import json
import random
import sys
from datetime import datetime, timedelta

NAMES = [
    "Marcus", "Kofi", "Darius", "Mei", "Leon",
    "Ana", "Kenji", "Victor", "Sven", "Oscar",
    "Petra", "Fiona", "Tyler", "Nina", "Rachel",
]

MESSAGES = [
    "ok", "got it", "yeah", "when are you free?", "call me",
    "check your email", "on my way", "running late, 10 mins",
    "what did they say?", "let's meet at the usual spot",
    "don't use your regular phone", "delete this after",
    "the package is ready", "did you talk to him?",
    "stay off the radar for now", "confirmed",
    "use the other number", "meeting at 9", "all good",
    "not here, call me later",
]


def gen_whatsapp(n: int, participants: int) -> str:
    names = random.sample(NAMES, min(participants, len(NAMES)))
    start = datetime(2024, 9, 1, 8, 0)
    lines = []
    ts = start
    for _ in range(n):
        ts += timedelta(minutes=random.randint(1, 120))
        mo = ts.month
        day = ts.day
        yr = ts.strftime("%y")
        h = ts.hour
        ampm = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        m = ts.minute
        sender = random.choice(names)
        body = random.choice(MESSAGES)
        lines.append(f"[{mo}/{day}/{yr}, {h12}:{m:02d} {ampm}] {sender}: {body}")
    return "\n".join(lines)


def gen_telegram(n: int, participants: int) -> dict:
    names = random.sample(NAMES, min(participants, len(NAMES)))
    start = datetime(2024, 9, 1, 8, 0)
    ts = start
    msgs = []
    for i in range(n):
        ts += timedelta(minutes=random.randint(1, 60))
        msgs.append({
            "id": i + 1,
            "type": "message",
            "date": ts.strftime("%Y-%m-%dT%H:%M:%S"),
            "from": random.choice(names),
            "text": random.choice(MESSAGES),
        })
    return {"name": "test_chat", "type": "personal_chat", "messages": msgs}


def gen_csv(n: int, participants: int) -> str:
    names = random.sample(NAMES, min(participants, len(NAMES)))
    start = datetime(2024, 9, 1, 8, 0)
    ts = start
    rows = ["timestamp,sender,body"]
    for _ in range(n):
        ts += timedelta(minutes=random.randint(1, 60))
        rows.append(f"{ts.strftime('%Y-%m-%dT%H:%M:%S')},{random.choice(names)},{random.choice(MESSAGES)}")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=5000, help="number of messages")
    ap.add_argument("-p", type=int, default=6, help="number of participants")
    ap.add_argument("--format", choices=["whatsapp", "telegram", "csv"], default="whatsapp")
    ap.add_argument("-o", "--output", help="output file (default: stdout)")
    args = ap.parse_args()

    random.seed(42)

    if args.format == "whatsapp":
        out = gen_whatsapp(args.n, args.p)
        mode = "w"
    elif args.format == "telegram":
        out = json.dumps(gen_telegram(args.n, args.p), indent=2, ensure_ascii=False)
        mode = "w"
    else:
        out = gen_csv(args.n, args.p)
        mode = "w"

    if args.output:
        with open(args.output, mode, encoding="utf-8") as f:
            f.write(out)
        print(f"wrote {args.n} messages to {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
