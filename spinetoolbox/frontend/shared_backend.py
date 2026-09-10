"""Shared command/event backend for Toolbox frontends."""
import json
import sys
from dataclasses import dataclass, field
from typing import Any

from .user_mode_rpc import handle_request
from .user_mode_service import UserModeService


@dataclass
class SharedBackendState:
    project: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


class SharedBackendService(UserModeService):
    """Owns frontend-visible project state and publishes state-change events."""

    def __init__(self) -> None:
        super().__init__()
        self.state = SharedBackendState()

    def project(self, project_path: str) -> dict[str, Any]:
        project = super().project(project_path)
        self.state.project = project
        self.emit_event("project_loaded", {"path": project["path"], "item_count": len(project["items"])})
        return project

    def current_project(self) -> dict[str, Any] | None:
        return self.state.project

    def events_since(self, event_id: int = 0) -> dict[str, Any]:
        return {"events": [event for event in self.state.events if event["id"] > event_id]}

    def emit_event(self, event_type: str, payload: dict[str, Any]) -> None:
        self.state.events.append({"id": len(self.state.events) + 1, "type": event_type, "payload": payload})


def handle_shared_request(service: SharedBackendService, request: dict) -> dict:
    """Dispatch one shared-backend request."""
    method = request.get("method")
    params = request.get("params", {})
    if method == "current_project":
        return service.current_project()
    if method == "events":
        return service.events_since(params.get("since", 0))
    return handle_request(service, request)


def main() -> None:
    """Read requests from stdin and write responses to stdout."""
    service = SharedBackendService()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = {"id": request.get("id"), "ok": True, "result": handle_shared_request(service, request)}
        except Exception as error:
            response = {"id": request.get("id") if "request" in locals() else None, "ok": False, "error": str(error)}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()