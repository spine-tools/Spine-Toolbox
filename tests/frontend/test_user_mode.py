import json
import threading
from http.client import HTTPConnection
from pathlib import Path

from spinetoolbox.frontend.user_mode import _Handler


def test_project_endpoint_returns_data_store_and_connections():
    from http.server import ThreadingHTTPServer

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        project_dir = Path(__file__).parents[2] / "execution_tests" / "active_by_default"
        connection = HTTPConnection(*server.server_address)
        connection.request("GET", f"/api/project?path={project_dir.as_posix()}")
        response = connection.getresponse()
        payload = json.loads(response.read())
    finally:
        connection.close()
        server.shutdown()
        thread.join()

    assert response.status == 200
    data_store = next(item for item in payload["items"] if item["type"] == "Data Store")
    assert data_store["name"] == "Test data"
    assert data_store["database"] == "Test data.sqlite"
    assert payload["connections"][0]["name"] == "from Test data to Exporter"