#!/usr/bin/env python3
import subprocess
import sys
import os
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(ROOT, "web")
BUILD_DIR = os.path.join(WEB_DIR, "build")
PORT = 8000


def _npm():
    return "npm.cmd" if sys.platform == "win32" else "npm"


def _build_frontend():
    index = os.path.join(BUILD_DIR, "index.html")
    if os.path.isfile(index):
        print("[threadline] Frontend already built. Skipping build.")
        print("             (delete web/build/ to force a rebuild)")
        return

    print("[threadline] Building frontend...")
    result = subprocess.run(
        [_npm(), "run", "build"],
        cwd=WEB_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("[threadline] Frontend build failed:")
        print(result.stderr)
        sys.exit(1)
    print("[threadline] Frontend built successfully.")


def _run_production():
    _build_frontend()

    url = f"http://localhost:{PORT}"
    print(f"[threadline] Starting Threadline on {url}")

    # oopens browser after a short delay (non-blocking)
    import threading
    def _open():
        time.sleep(2)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()

    try:
        subprocess.run(
            [
                sys.executable, "-m", "uvicorn",
                "threadline.api:app",
                "--host", "127.0.0.1",
                "--port", str(PORT),
                "--log-level", "info",
            ],
            cwd=ROOT,
        )
    except KeyboardInterrupt:
        print("\n[threadline] Stopped.")


def _run_dev():
    procs: list[subprocess.Popen] = []
    frontend_port = 5173
    frontend_url = f"http://localhost:{frontend_port}"

    try:
        print(f"[threadline] DEV MODE")
        print(f"[threadline] Starting API server on port {PORT}...")
        api = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "threadline.api:app",
                "--host", "127.0.0.1",
                "--port", str(PORT),
                "--log-level", "warning",
                "--reload",
            ],
            cwd=ROOT,
        )
        procs.append(api)

        print(f"[threadline] Starting Vite dev server on port {frontend_port}...")
        ui = subprocess.Popen(
            [_npm(), "run", "dev", "--", "--port", str(frontend_port)],
            cwd=WEB_DIR,
        )
        procs.append(ui)

        time.sleep(3)
        print(f"[threadline] Opening {frontend_url}")
        webbrowser.open(frontend_url)
        print("[threadline] Running in dev mode. Press Ctrl+C to stop.\n")

        while True:
            for p in procs:
                if p.poll() is not None:
                    raise KeyboardInterrupt
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[threadline] Shutting down...")
    finally:
        for p in procs:
            if p.poll() is None:
                p.terminate()
        for p in procs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        print("[threadline] Stopped.")


def main():
    if "--dev" in sys.argv:
        _run_dev()
    else:
        _run_production()


if __name__ == "__main__":
    main()
