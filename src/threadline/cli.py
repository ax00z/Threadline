from __future__ import annotations
import argparse
import sys
from collections import Counter
from pathlib import Path

from .parser import parse_file, detect_format


def main() -> None:
    ap = argparse.ArgumentParser(prog="threadline")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("parse", help="parse a chat export file")
    p.add_argument("input", help="path to chat export (.txt, .json, .csv)")
    p.add_argument("-o", "--output", help="write JSONL to this path (default: stdout)")
    p.add_argument("--stats", action="store_true", help="print summary stats to stderr")

    args = ap.parse_args()
    if args.cmd is None:
        ap.print_help()
        sys.exit(1)

    path = args.input
    if not Path(path).exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    fmt = detect_format(path)
    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout

    count = 0
    sender_counts: Counter[str] = Counter()
    try:
        for msg in parse_file(path):
            out.write(msg.to_json() + "\n")
            sender_counts[msg.sender] += 1
            count += 1
    finally:
        if args.output:
            out.close()

    if args.stats:
        print(f"format:   {fmt}", file=sys.stderr)
        print(f"messages: {count:,}", file=sys.stderr)
        print(f"senders:  {len(sender_counts)}", file=sys.stderr)
        for name, n in sender_counts.most_common(10):
            print(f"  {name}: {n:,}", file=sys.stderr)
