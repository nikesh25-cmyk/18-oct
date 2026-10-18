"""Small local HTTP API for research jobs. Bind to loopback unless protected."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .jobs import JobManager


def create_server(host: str, port: int, manager: JobManager) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format_string, *args):
            pass

        def send_json(self, status: int, data: dict) -> None:
            body = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/health":
                self.send_json(200, {"ok": True})
                return
            if self.path.startswith("/jobs/"):
                job_id = self.path.removeprefix("/jobs/")
                try:
                    self.send_json(200, manager.get(job_id))
                except KeyError:
                    self.send_json(404, {"error": "Job not found."})
                return
            self.send_json(404, {"error": "Route not found."})

        def do_POST(self):
            if self.path.endswith("/cancel") and self.path.startswith("/jobs/"):
                job_id = self.path[len("/jobs/"):-len("/cancel")]
                try:
                    changed = manager.cancel(job_id)
                    self.send_json(200, {"cancelled": changed})
                except KeyError:
                    self.send_json(404, {"error": "Job not found."})
                return
            if self.path != "/jobs":
                self.send_json(404, {"error": "Route not found."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 2 or size > 4096:
                    raise ValueError("Request body must be 2–4096 bytes.")
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict) or not isinstance(payload.get("goal"), str):
                    raise ValueError("A text goal is required.")
                job_id = manager.start(payload["goal"])
            except (ValueError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": str(exc)})
                return
            self.send_json(201, {"id": job_id})

    return ThreadingHTTPServer((host, port), Handler)
