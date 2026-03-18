#!/usr/bin/env python3
"""Threadline launcher — single entry point for dev and production.

Usage:
    python launch.py          # Production: build frontend, serve everything on port 8000
    python launch.py --dev    # Dev: API on 8001 + Vite on 5173 with HMR
    python launch.py --port N # Production on custom port
"""
import subprocess
import sys
import os
import time
import webbrowser
import signal

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")
BUILD_DIR = os.path.join(WEB_DIR, "build")


def _npm():
    return "npm.cmd" if sys.platform == "win32" else "npm"


def _build_frontend():
    index = os.path.join(BUILD_DIR, "index.html")
    if os.path.isfile(index):
        print("[threadline] Frontend build found, skipping. Delete web/build/ to force rebuild.")
        return True

    print("[threadline] Building frontend...")
    result = subprocess.run(
        [_npm(), "run", "build"],
        cwd=WEB_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[threadline] Frontend build failed:")
        print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
        return False
    print("[threadline] Frontend built.")
    return True


def _run_production(port: int):
    if not _build_frontend():
        sys.exit(1)

    url = f"http://localhost:{port}"
    print(f"[threadline] Starting on {url}")

    import threading
    def _open():
        time.sleep(1.5)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

    try:
        subprocess.run(
            [
                sys.executable, "-m", "uvicorn",
                "threadline.api:app",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--log-level", "info",
            ],
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        print("\n[threadline] Stopped.")


def _run_dev():
    api_port = 8001
    ui_port = 5173
    procs: list[subprocess.Popen] = []

    def _cleanup():
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()

    try:
        print(f"[threadline] DEV MODE — API:{api_port}  UI:{ui_port}")

        api = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "threadline.api:app",
                "--host", "127.0.0.1",
                "--port", str(api_port),
                "--log-level", "warning",
                "--reload",
            ],
            cwd=ROOT,
        )
        procs.append(api)

        ui = subprocess.Popen(
            [_npm(), "run", "dev", "--", "--port", str(ui_port)],
            cwd=WEB_DIR,
        )
        procs.append(ui)

        time.sleep(3)
        url = f"http://localhost:{ui_port}"
        print(f"[threadline] Opening {url}")
        webbrowser.open(url)
        print("[threadline] Ctrl+C to stop.\n")

        while True:
            for p in procs:
                if p.poll() is not None:
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[threadline] Shutting down...")
    finally:
        _cleanup()
        print("[threadline] Stopped.")


def main():
    args = sys.argv[1:]
    if "--dev" in args:
        _run_dev()
    else:
        port = 8000
        if "--port" in args:
            try:
                port = int(args[args.index("--port") + 1])
            except (IndexError, ValueError):
                print("Usage: --port NUMBER")
                sys.exit(1)
        _run_production(port)


if __name__ == "__main__":
    main()
