"""Backend application service for the parallel User Mode frontend."""
import threading
import base64
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..headless import open_project
from ..load_project import load_local_project_dict, load_project_dict, merge_local_dict_to_project_dict, ProjectLoadingFailed
import json
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
        supplied = Path(project_path)
        # If the user passed a path to a file (e.g. project.json), load it directly
        if supplied.is_file():
            try:
                with supplied.open("r", encoding="utf8") as fh:
                    project = json.load(fh)
                    project_dir = supplied.parent
            except Exception as e:
                raise ProjectLoadingFailed(f"Could not read project file: {supplied}: {e}")
        else:
            # Treat as directory; try normal loader first, then fallbacks
            project_dir = self._project_dir(project_path)
            try:
                project = load_project_dict(project_dir)
            except ProjectLoadingFailed:
                # Try project.json at project root
                alt_path = Path(project_dir) / "project.json"
                if alt_path.exists():
                    try:
                        with alt_path.open("r", encoding="utf8") as fh:
                            project = json.load(fh)
                    except Exception as e:
                        raise ProjectLoadingFailed(f"Could not read project.json at {alt_path}: {e}")
                else:
                    # Search up parent directories for a project file (useful if user picked a subfolder)
                    found = False
                    for parent in (Path(project_dir),) + tuple(Path(project_dir).parents)[:3]:
                        p1 = parent / ".spinetoolbox" / "project.json"
                        p2 = parent / "project.json"
                        if p1.exists():
                            with p1.open("r", encoding="utf8") as fh:
                                project = json.load(fh)
                            project_dir = parent
                            found = True
                            break
                        if p2.exists():
                            with p2.open("r", encoding="utf8") as fh:
                                project = json.load(fh)
                            project_dir = parent
                            found = True
                            break
                    if not found:
                        # Build a helpful diagnostic listing
                        try:
                            entries = [p.name for p in Path(project_dir).iterdir()]
                        except Exception:
                            entries = []
                        raise ProjectLoadingFailed(
                            f"Project file not found in {project_dir}. Checked: .spinetoolbox/project.json and project.json. Contents: {entries}"
                        )
        items = []
        for name, item in project.get("items", {}).items():
            item_data = {"name": name, "type": item.get("type", "Unknown"), "x": item.get("x", 0), "y": item.get("y", 0)}
            if item.get("type") == "Data Store":
                database = item.get("url", {}).get("database", {})
                item_data["database"] = database.get("path", name)
            items.append(item_data)
        return {"path": str(project_dir), "items": items, "connections": project.get("project", {}).get("connections", [])}

    def start_run(self, project_path: str, tool: str | None = None, scenario: str | None = None) -> tuple[str, Job]:
        supplied = Path(project_path)
        if supplied.is_file():
            try:
                with supplied.open("r", encoding="utf8") as fh:
                    project = json.load(fh)
                    project_dir = supplied.parent
            except Exception as e:
                raise ProjectLoadingFailed(f"Could not read project file: {supplied}: {e}")
        else:
            project_dir = self._project_dir(project_path)
            try:
                project = load_project_dict(project_dir)
            except ProjectLoadingFailed:
                alt_path = Path(project_dir) / "project.json"
                if alt_path.exists():
                    with alt_path.open("r", encoding="utf8") as fh:
                        project = json.load(fh)
                else:
                    # Search up a few levels
                    found = False
                    for parent in (Path(project_dir),) + tuple(Path(project_dir).parents)[:3]:
                        p1 = parent / ".spinetoolbox" / "project.json"
                        p2 = parent / "project.json"
                        if p1.exists():
                            with p1.open("r", encoding="utf8") as fh:
                                project = json.load(fh)
                            project_dir = parent
                            found = True
                            break
                        if p2.exists():
                            with p2.open("r", encoding="utf8") as fh:
                                project = json.load(fh)
                            project_dir = parent
                            found = True
                            break
                    if not found:
                        raise
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

    def import_excel(self, project_path: str, filename: str, content: str, data_store: str | None = None) -> dict[str, Any]:
        """Import an Excel workbook into a project's Data Store."""
        from sqlalchemy.engine.url import URL
        from spinedb_api import DatabaseMapping, import_data
        from spinedb_api.spine_io.importers.excel_reader import get_mapped_data_from_xlsx

        project_dir = self._project_dir(project_path)
        project = load_project_dict(project_dir)
        stores = {
            name: item for name, item in project.get("items", {}).items() if item.get("type") == "Data Store"
        }
        if not stores:
            raise ValueError("The project has no Data Store to import into")
        store_name = data_store or next(iter(stores))
        if store_name not in stores:
            raise ValueError(f"Unknown Data Store: {store_name}")
        database = stores[store_name].get("url", {}).get("database", {})
        database_path = Path(database.get("path", f"{store_name}.sqlite"))
        if database.get("relative", True):
            database_path = project_dir / database_path
        workbook = base64.b64decode(content)
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix or ".xlsx", delete=False) as temporary_file:
            temporary_file.write(workbook)
            temporary_path = temporary_file.name
        try:
            mapped_data, errors = get_mapped_data_from_xlsx(temporary_path)
            url = URL.create("sqlite", database=str(database_path))
            with DatabaseMapping(url) as db_map:
                imported, import_errors = import_data(db_map, **mapped_data)
                db_map.commit_session(f"Import data from Excel: {filename}")
            return {"filename": filename, "data_store": store_name, "imported": imported, "errors": errors + import_errors}
        finally:
            Path(temporary_path).unlink(missing_ok=True)

    def list_scenarios(self, project_path: str, data_store: str | None = None) -> dict[str, Any]:
        """List scenario names found in a project's Data Store database."""
        from sqlalchemy.engine.url import URL
        from spinedb_api import DatabaseMapping, SpineDBAPIError, SpineDBVersionError

        project_dir = self._project_dir(project_path)
        project = load_project_dict(project_dir)
        stores = {
            name: item for name, item in project.get("items", {}).items() if item.get("type") == "Data Store"
        }
        if not stores:
            raise ValueError("The project has no Data Store to read scenarios from")
        store_name = data_store or next(iter(stores))
        if store_name not in stores:
            raise ValueError(f"Unknown Data Store: {store_name}")
        database = stores[store_name].get("url", {}).get("database", {})
        database_path = Path(database.get("path", f"{store_name}.sqlite"))
        if database.get("relative", True):
            database_path = project_dir / database_path
        if not database_path.exists():
            return {"data_store": store_name, "scenarios": []}
        url = URL.create("sqlite", database=str(database_path))
        try:
            with DatabaseMapping(url) as db_map:
                scenarios = [row.name for row in db_map.query(db_map.scenario_sq)]
        except (SpineDBAPIError, SpineDBVersionError) as error:
            raise ValueError(f"Could not read scenarios from {store_name}: {error}")
        return {"data_store": store_name, "scenarios": scenarios}

    def open_database_editor(self, project_path: str, data_store: str | None = None) -> dict[str, Any]:
        """Open the classic Spine DB Editor for a project's Data Store."""
        from sqlalchemy.engine.url import URL

        supplied = Path(project_path).expanduser()
        if not supplied.is_absolute() and not supplied.exists():
            raise ValueError("Classic DB Editor needs an absolute project path. Open the project with the Load project button.")
        project_dir = self._project_dir(project_path)
        try:
            project = load_project_dict(project_dir)
        except ProjectLoadingFailed:
            project_dir = Path(self.project(project_path)["path"])
            project = load_project_dict(project_dir)
        stores = {
            name: item for name, item in project.get("items", {}).items() if item.get("type") == "Data Store"
        }
        if not stores:
            raise ValueError("The project has no Data Store to open")
        store_name = data_store or next(iter(stores))
        if store_name not in stores:
            raise ValueError(f"Unknown Data Store: {store_name}")
        database = stores[store_name].get("url", {}).get("database", {})
        database_path = Path(database.get("path", f"{store_name}.sqlite"))
        if database.get("relative", True):
            database_path = project_dir / database_path
        if not database_path.exists():
            raise ValueError(f"Database file for {store_name} does not exist: {database_path}")
        url = URL.create("sqlite", database=database_path.as_posix())
        subprocess.Popen(
            [sys.executable, "-m", "spinetoolbox.spine_db_editor.main", str(url)],
            cwd=Path(__file__).resolve().parents[2],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        return {"data_store": store_name, "url": str(url)}

    def open_database_from_bytes(self, filename: str, content_b64: str) -> dict[str, Any]:
        """Receive a database file as base64, write to temp file and return introspected schema and sample rows."""
        import sqlite3

        data = base64.b64decode(content_b64)
        suffix = Path(filename).suffix or ".sqlite"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = Path(tmp.name)
        try:
            conn = sqlite3.connect(str(tmp_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            # Get list of tables and views
            cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY name")
            tables = []
            for row in cur.fetchall():
                table_name = row[0]
                # Get columns
                cur.execute(f"PRAGMA table_info('{table_name}')")
                cols = [c[1] for c in cur.fetchall()]
                # Get first 100 rows
                cur.execute(f"SELECT * FROM '{table_name}' LIMIT 100")
                rows = [dict(r) for r in cur.fetchall()]
                tables.append({"name": table_name, "columns": cols, "rows": rows})
            conn.close()
            return {"filename": filename, "tables": tables}
        finally:
            tmp_path.unlink(missing_ok=True)

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

    def project_from_json(self, content: str) -> dict[str, Any]:
        """Parse a `project.json` content string and return the same metadata as `project()`.

        This is used when the frontend cannot supply an absolute folder path but can read the
        `project.json` file from a directory picker; it lets the UI show items and connections.
        """
        try:
            project = json.loads(content)
        except Exception as e:
            raise ProjectLoadingFailed(f"Invalid project JSON: {e}")
        items = []
        for name, item in project.get("items", {}).items():
            item_data = {"name": name, "type": item.get("type", "Unknown"), "x": item.get("x", 0), "y": item.get("y", 0)}
            if item.get("type") == "Data Store":
                database = item.get("url", {}).get("database", {})
                item_data["database"] = database.get("path", name)
            items.append(item_data)
        return {"path": "", "items": items, "connections": project.get("project", {}).get("connections", [])}