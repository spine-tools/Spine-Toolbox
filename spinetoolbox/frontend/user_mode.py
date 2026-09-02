"""Small local bridge reserved for the parallel user-mode frontend."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path != "/api/health":
            self.send_error(404)
            return
        payload = json.dumps({"status": "ok", "application": "Spine Toolbox"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


def main():
    """Run the local API used by the user-mode frontend."""
    ThreadingHTTPServer(("127.0.0.1", 8765), _Handler).serve_forever()


if __name__ == "__main__":
    main()