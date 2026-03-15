from __future__ import annotations
import argparse
import subprocess
import sys
import webbrowser
from collections import Counter
from pathlib import Path

from .parser import parse_file, detect_format

_ROOT = Path(__file__).resolve().parent.parent.parent
_WEB_DIR = _ROOT / "web"


def _build_frontend() -> bool:
    build_dir = _WEB_DIR / "build"
    if build_dir.is_dir():
        return True
    if not (_WEB_DIR / "package.json").exists():
        print("error: web/ directory not found", file=sys.stderr)
        return False
    print("building frontend...", file=sys.stderr)
    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    r = subprocess.run([npm, "run", "build"], cwd=str(_WEB_DIR))
    return r.returncode == 0


def main() -> None:
    ap = argparse.ArgumentParser(prog="threadline")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("parse", help="parse a chat export file")
    p.add_argument("input", help="path to chat export (.txt, .json, .csv)")
    p.add_argument("-o", "--output", help="write JSONL to this path (default: stdout)")
    p.add_argument("--stats", action="store_true", help="print summary stats to stderr")

    s = sub.add_parser("serve", help="launch the full app (backend + UI)")
    s.add_argument("-p", "--port", type=int, default=8000, help="port (default 8000)")
    s.add_argument("--no-browser", action="store_true", help="don't auto-open browser")

    args = ap.parse_args()
    if args.cmd is None:
        ap.print_help()
        sys.exit(1)

    if args.cmd == "serve":
        _run_serve(args)
        return

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


def _run_serve(args) -> None:
    if not _build_frontend():
        print("error: frontend build failed", file=sys.stderr)
        sys.exit(1)

    import uvicorn

    url = f"http://127.0.0.1:{args.port}"
    print(f"threadline running at {url}", file=sys.stderr)

    if not args.no_browser:
        import threading
        threading.Timer(1.0, webbrowser.open, args=[url]).start()

    uvicorn.run("threadline.api:app", host="127.0.0.1", port=args.port)
