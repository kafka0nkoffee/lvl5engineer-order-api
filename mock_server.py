"""
WireMock-compatible mock server.
Each server instance gets its OWN call log so payment and inventory
calls can be verified independently — matching how real WireMock works
(separate WireMock instances per service).
"""
import json, time, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path


class MockCallLog:
    def __init__(self):
        self._calls = []
        self._lock  = threading.Lock()

    def record(self, method, path, body):
        with self._lock:
            self._calls.append({"method": method, "path": path, "body": body})

    def all(self):
        with self._lock:
            return list(self._calls)

    def reset(self):
        with self._lock:
            self._calls.clear()

    def was_called(self, method, path):
        return any(c["method"] == method and c["path"] == path for c in self.all())

    def call_count(self, method, path):
        return sum(1 for c in self.all() if c["method"] == method and c["path"] == path)

    def any_calls_matching(self, path_prefix):
        return [c for c in self.all() if c["path"].startswith(path_prefix)]


def make_handler(stubs, call_log):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args): pass

        def do_GET(self):  self._handle("GET")
        def do_POST(self): self._handle("POST")

        def _handle(self, method):
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length).decode() if length else ""

            for stub in stubs:
                req  = stub.get("request", {})
                resp = stub.get("response", {})
                if req.get("method", "GET") != method: continue
                if req.get("url") and req["url"] != self.path: continue
                if req.get("urlPathPattern"):
                    import re
                    if not re.match(req["urlPathPattern"], self.path): continue

                delay = resp.get("fixedDelayMilliseconds", 0)
                if delay: time.sleep(delay / 1000)

                rb = resp.get("body", "")
                if isinstance(rb, dict): rb = json.dumps(rb)

                self.send_response(resp.get("status", 200))
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(rb.encode())
                call_log.record(method, self.path, body)
                return

            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"No stub matched {method} {self.path}"}).encode())

    return Handler


def start_mock_server(port: int, mappings_dir: str) -> tuple[HTTPServer, MockCallLog]:
    stubs    = [json.loads(f.read_text()) for f in Path(mappings_dir).glob("*.json")]
    log      = MockCallLog()
    handler  = make_handler(stubs, log)
    server   = HTTPServer(("localhost", port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, log
