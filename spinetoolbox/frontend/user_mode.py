"""Small local bridge reserved for the parallel user-mode frontend."""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..load_project import load_project_dict


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        request = urlparse(self.path)
        if request.path == "/api/health":
            self._send_json({"status": "ok", "application": "Spine Toolbox"})
            return
        if request.path == "/api/project":
            self._send_project(parse_qs(request.query).get("path", [os.getcwd()])[0])
            return
        self.send_error(404)

    def _send_project(self, project_path):
        project_dir = Path(project_path).expanduser().resolve()
        try:
            project = load_project_dict(project_dir)
        except (OSError, ValueError) as error:
            self._send_json({"error": str(error)}, status=400)
            return
        items = []
        for name, item in project.get("items", {}).items():
            item_data = {"name": name, "type": item.get("type", "Unknown"), "x": item.get("x", 0), "y": item.get("y", 0)}
            if item.get("type") == "Data Store":
                database = item.get("url", {}).get("database", {})
                item_data["database"] = database.get("path", name)
            items.append(item_data)
        self._send_json({"path": str(project_dir), "items": items, "connections": project.get("project", {}).get("connections", [])})

    def _send_json(self, payload, status=200):
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def log_message(self, *_args):
        return


def main():
    """Run the local API used by the user-mode frontend."""
    ThreadingHTTPServer(("127.0.0.1", 8765), _Handler).serve_forever()


if __name__ == "__main__":
    main()