#!/usr/bin/env python3
"""Threadline — single-command launcher.

    python launch.py              # Build frontend if needed, serve on port 8000
    python launch.py --port 9000  # Custom port
    python launch.py --rebuild    # Force frontend rebuild
    python launch.py --dev        # Dev mode: API + Vite HMR
"""
import os
import subprocess
import sys
import time
import webbrowser
import socket
import signal
import threading

# When frozen by PyInstaller, _MEIPASS points to the temp extract dir
if getattr(sys, 'frozen', False):
    ROOT = os.path.dirname(sys.executable)
    _BUNDLE = sys._MEIPASS
    WEB_DIR = os.path.join(_BUNDLE, "web")
    BUILD_DIR = os.path.join(WEB_DIR, "build")
else:
    ROOT = os.path.dirname(os.path.abspath(__file__))
    WEB_DIR = os.path.join(ROOT, "web")
    BUILD_DIR = os.path.join(WEB_DIR, "build")


def _npm():
    return "npm.cmd" if sys.platform == "win32" else "npm"


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def _find_port(start: int = 8000) -> int:
    for p in range(start, start + 20):
        if _port_free(p):
            return p
    return start


def _build_frontend(force: bool = False):
    index = os.path.join(BUILD_DIR, "index.html")
    if not force and os.path.isfile(index):
        print("[threadline] Frontend build exists. Use --rebuild to force.")
        return True

    # Check node_modules exist
    if not os.path.isdir(os.path.join(WEB_DIR, "node_modules")):
        print("[threadline] Installing frontend dependencies...")
        r = subprocess.run([_npm(), "install"], cwd=WEB_DIR, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"[threadline] npm install failed:\n{r.stderr[-500:]}")
            return False

    print("[threadline] Building frontend...")
    r = subprocess.run([_npm(), "run", "build"], cwd=WEB_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[threadline] Build failed:\n{r.stderr[-500:]}")
        return False
    print("[threadline] Frontend built.")
    return True


def _run_production(port: int, rebuild: bool):
    if not _build_frontend(force=rebuild):
        sys.exit(1)

    # Verify build output exists
    if not os.path.isfile(os.path.join(BUILD_DIR, "index.html")):
        print("[threadline] ERROR: web/build/index.html not found after build.")
        print("[threadline] Try: python launch.py --rebuild")
        sys.exit(1)

    port = _find_port(port)
    url = f"http://localhost:{port}"
    print(f"\n  THREADLINE")
    print(f"  -----------------------------")
    print(f"  Local:   {url}")
    print(f"  Status:  Starting...\n")

    def _open():
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=_open, daemon=True).start()

    if getattr(sys, 'frozen', False):
        # When frozen, run uvicorn in-process (can't subprocess the exe)
        import uvicorn
        try:
            uvicorn.run(
                "threadline.api:app",
                host="127.0.0.1",
                port=port,
                log_level="warning",
            )
        except KeyboardInterrupt:
            print("\n[threadline] Stopped.")
    else:
        try:
            subprocess.run(
                [
                    sys.executable, "-m", "uvicorn",
                    "threadline.api:app",
                    "--host", "127.0.0.1",
                    "--port", str(port),
                    "--log-level", "warning",
                ],
                cwd=ROOT,
            )
        except KeyboardInterrupt:
            print("\n[threadline] Stopped.")


def _run_dev():
    api_port = _find_port(8001)
    ui_port = 5173
    procs = []

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


def main():
    args = sys.argv[1:]
    if "--dev" in args:
        _run_dev()
    else:
        port = 8000
        rebuild = "--rebuild" in args
        if "--port" in args:
            try:
                port = int(args[args.index("--port") + 1])
            except (IndexError, ValueError):
                print("Usage: --port NUMBER")
                sys.exit(1)
        _run_production(port, rebuild)


if __name__ == "__main__":
    main()
