"""JSON-lines protocol for the Tauri-managed User Mode Python process."""
import json
import sys

from .user_mode_service import UserModeService


def handle_request(service: UserModeService, request: dict) -> dict:
    """Dispatch one bridge request and return a JSON-serializable response."""
    method = request.get("method")
    params = request.get("params", {})
    if method == "health":
        return {"status": "ok", "application": "Spine Toolbox"}
    if method == "project":
        return service.project(params["path"])
    if method == "start_run":
        job_id, job = service.start_run(params["path"], params.get("tool"), params.get("scenario"))
        return {"job_id": job_id, "status": job.status}
    if method == "job":
        job = service.job(params["job_id"])
        if job is None:
            raise ValueError("Unknown job")
        return {"status": job.status, "events": job.events, "error": job.error}
    raise ValueError(f"Unknown method: {method}")


def main() -> None:
    """Read requests from stdin and write responses to stdout."""
    service = UserModeService()
    for line in sys.stdin:
        try:
            request = json.loads(line)
            response = {"id": request.get("id"), "ok": True, "result": handle_request(service, request)}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            response = {"id": request.get("id") if "request" in locals() else None, "ok": False, "error": str(error)}
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()