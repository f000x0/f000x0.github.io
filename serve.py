#!/usr/bin/env python3
"""Serve this project locally. No third-party packages are required."""
import argparse
import contextlib
import functools
import json
import threading
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from build import ROOT, PROFILE, build

STATE_DIR = ROOT / ".local"
STATE_FILE = STATE_DIR / "server.json"
MARKER = str(ROOT)
BUILD_LOCK = threading.Lock()
last_built = None


def ensure_built():
    global last_built
    version = (PROFILE.stat().st_mtime_ns, (ROOT / "build.py").stat().st_mtime_ns)
    with BUILD_LOCK:
        if last_built != version or not (ROOT / "index.html").exists():
            build()
            last_built = version


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/__homepage_health":
            body = json.dumps({"project": MARKER}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        # Only serve public site artifacts, never local state or project sources.
        from urllib.parse import unquote
        from pathlib import PurePosixPath
        decoded = unquote(path)
        parts = PurePosixPath(decoded).parts
        if any(p.startswith(".") or p == ".." for p in parts) or not (decoded in ("/", "/index.html") or decoded.startswith("/assets/")):
            self.send_error(404)
            return
        if decoded in ("/", "/index.html"):
            try:
                ensure_built()
            except Exception as error:
                self.log_error("Build failed: %s", error)
                self.send_error(500, "Could not build the homepage. Check data/profile.json and the terminal output.")
                return
        return super().do_GET()

    def do_HEAD(self):
        path = self.path.split("?", 1)[0]
        from urllib.parse import unquote
        from pathlib import PurePosixPath
        decoded = unquote(path)
        if any(p.startswith(".") or p == ".." for p in PurePosixPath(decoded).parts) or not (decoded in ("/", "/index.html") or decoded.startswith("/assets/")):
            self.send_error(404)
            return
        return super().do_HEAD()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(404)
        return None


def existing_server():
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        port = int(state["port"])
        url = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(url + "/__homepage_health", timeout=1) as response:
            if json.load(response).get("project") == MARKER:
                return f"http://localhost:{port}"
    except (OSError, ValueError, KeyError):
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Preview Li Hu's academic homepage locally.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    ensure_built()
    current = existing_server()
    if current:
        print(f"Homepage is already running: {current}", flush=True)
        if not args.no_browser:
            webbrowser.open(current)
        return
    handler = functools.partial(Handler, directory=str(ROOT))
    server = None
    for port in range(args.port, min(args.port + 20, 65536)):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), handler)
            break
        except OSError as error:
            if error.errno not in (48, 98, 10048):
                raise
    if server is None:
        raise SystemExit("No free port found. Try: python3 serve.py --port 9000")
    url = f"http://localhost:{server.server_port}"
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps({"port": server.server_port, "url": url}), encoding="utf-8")
    print(f"\nLi Hu · Academic Homepage\n{url}\n\nEdit data/profile.json and refresh to update the content.\nPress Ctrl+C to stop.\n", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLocal preview stopped.")
    finally:
        server.server_close()
        with contextlib.suppress(OSError):
            STATE_FILE.unlink()


if __name__ == "__main__":
    main()
