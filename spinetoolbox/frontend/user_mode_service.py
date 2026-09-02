"""Backend application service for the parallel User Mode frontend."""
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..headless import open_project
from ..load_project import load_local_project_dict, load_project_dict, merge_local_dict_to_project_dict
from ..load_specification import load_specification_local_data


@dataclass
class Job:
    status: str = "starting"
    events: list[dict[str, str]] = field(default_factory=list)
    error: str | None = None


class _Logger:
    def __init__(self) -> None:
        self.msg_error = self

    def emit(self, _message: str) -> None:
        return


class UserModeService:
    """Provides project and execution operations without depending on Qt."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._jobs_lock = threading.Lock()

    def project(self, project_path: str) -> dict[str, Any]:
        project_dir = self._project_dir(project_path)
        project = load_project_dict(project_dir)
        items = []
        for name, item in project.get("items", {}).items():
            item_data = {"name": name, "type": item.get("type", "Unknown"), "x": item.get("x", 0), "y": item.get("y", 0)}
            if item.get("type") == "Data Store":
                database = item.get("url", {}).get("database", {})
                item_data["database"] = database.get("path", name)
            items.append(item_data)
        return {"path": str(project_dir), "items": items, "connections": project.get("project", {}).get("connections", [])}

    def start_run(self, project_path: str, tool: str | None = None, scenario: str | None = None) -> tuple[str, Job]:
        project_dir = self._project_dir(project_path)
        project = load_project_dict(project_dir)
        job_id = uuid.uuid4().hex
        job = Job()
        with self._jobs_lock:
            self._jobs[job_id] = job
        thread = threading.Thread(target=self._run, args=(job_id, project, project_dir, tool, scenario), daemon=True)
        thread.start()
        return job_id, job

    def job(self, job_id: str) -> Job | None:
        with self._jobs_lock:
            return self._jobs.get(job_id)

    @staticmethod
    def _project_dir(project_path: str) -> Path:
        return Path(project_path).expanduser().resolve()

    def _run(self, job_id: str, project: dict, project_dir: Path, tool: str | None, _scenario: str | None) -> None:
        try:
            from spine_engine import SpineEngine

            local_data = load_local_project_dict(project_dir)
            merge_local_dict_to_project_dict(local_data, project)
            settings, items, specifications, connections, jumps = open_project(
                project, project_dir, load_specification_local_data(project_dir), _Logger()
            )
            execution_permits = self._execution_permits(items, tool)
            engine = SpineEngine(
                items=items,
                specifications=specifications,
                connections=connections,
                jumps=jumps,
                execution_permits=execution_permits,
                settings=settings,
                project_dir=str(project_dir),
            )
            job = self._jobs[job_id]
            job.status = "running"
            while True:
                event_type, event_data = engine.get_event()
                job.events.append({"type": event_type, "data": str(event_data)})
                if event_type == "dag_exec_finished":
                    break
            job.status = str(engine.state().name).lower()
        except Exception as error:
            job = self._jobs[job_id]
            job.status = "failed"
            job.error = str(error)

    @staticmethod
    def _execution_permits(items: dict[str, dict], tool: str | None) -> dict[str, bool]:
        if not tool:
            return {name: True for name in items}
        selected = {name for name, item in items.items() if name == tool or item.get("type") == tool}
        return {name: not selected or name in selected for name in items}