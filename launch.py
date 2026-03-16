#!/usr/bin/env python3
"""
Threadline — Single-command launcher.

Usage:  python launch.py

Starts the FastAPI backend and SvelteKit dev server together,
then opens the browser.  Press Ctrl+C to stop both.
"""

import subprocess
import sys
import os
import time
import webbrowser
import signal

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")

BACKEND_PORT = 8000
FRONTEND_PORT = 5173
FRONTEND_URL = f"http://localhost:{FRONTEND_PORT}"


def main():
    procs: list[subprocess.Popen] = []

    try:
        # 1) Start FastAPI backend
        print(f"[threadline] Starting API server on port {BACKEND_PORT}...")
        api = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "threadline.api:app",
                "--host", "127.0.0.1",
                "--port", str(BACKEND_PORT),
                "--log-level", "warning",
            ],
            cwd=ROOT,
        )
        procs.append(api)

        # 2) Start Vite / SvelteKit dev server
        print(f"[threadline] Starting UI on port {FRONTEND_PORT}...")
        # Use npm.cmd on Windows, npm elsewhere
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        ui = subprocess.Popen(
            [npm, "run", "dev", "--", "--port", str(FRONTEND_PORT)],
            cwd=WEB_DIR,
        )
        procs.append(ui)

        # 3) Give servers a moment, then open browser
        time.sleep(3)
        print(f"[threadline] Opening {FRONTEND_URL}")
        webbrowser.open(FRONTEND_URL)

        print("[threadline] Running. Press Ctrl+C to stop.\n")

        # Wait for either process to exit
        while True:
            for p in procs:
                ret = p.poll()
                if ret is not None:
                    print(f"[threadline] Process {p.args} exited with code {ret}")
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[threadline] Shutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        # Give them a moment to exit gracefully
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("[threadline] Stopped.")


if __name__ == "__main__":
    main()
