"""Reads and writes the same project.json Data Connection file references as the classic Qt UI."""
import json
import os
from pathlib import Path
import shutil
import sys
import time
from PySide6.QtCore import QFileSystemWatcher, QObject, QSettings, QUrl, Signal, Slot
from ...config import (
    LATEST_PROJECT_VERSION,
    PLOTS_DIR_ENV_VAR,
    PROGRESS_MARKER,
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_FILENAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_LOCAL_DATA_FILENAME,
    PROJECT_SETUP_SCRIPT,
    REPORT_PROGRESS_ENV_VAR,
)
from ...execution_managers import QProcessExecutionManager
from ...helpers import open_url
from ...logger import QtLogger
from .database_editor_backend import DatabaseEditorBackend

_INPUT_DATA_CONNECTION_NAME = "Input data"
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}
_IMAGE_SCAN_SKIPPED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}

# same QSettings location and "appSettings/recentProjects" format the classic Qt UI uses
_SETTINGS_ORGANIZATION = "SpineProject"
_SETTINGS_APPLICATION = "Spine Toolbox"

# shown until the user opens a real project, so the UI has something to demonstrate
_EXAMPLE_PROJECT_FILE = Path(__file__).parent / "examples" / "project.json"
_EXAMPLE_PROJECT_NAME = "FlexTool (example)"


def _serialize_path(path: str, project_dir: str) -> dict:
    """Mirrors spine_engine.utils.serialization.serialize_path without importing the heavy spine_engine package."""
    is_relative = os.path.commonpath([os.path.abspath(path), project_dir]) == project_dir
    stored = os.path.relpath(path, project_dir) if is_relative else path
    return {"type": "path", "relative": is_relative, "path": stored.replace(os.sep, "/")}


def _deserialize_path(serialized: dict, project_dir: str) -> str:
    """Mirrors spine_engine.utils.serialization.deserialize_path."""
    path = serialized["path"]
    return os.path.normpath(os.path.join(project_dir, path) if serialized["relative"] else path)


def _data_store_url(url_dict: dict, project_dir: str) -> str | None:
    """Builds a SQLAlchemy URL string from a Data Store item's "url" dict."""
    database = url_dict.get("database")
    if not database:
        return None
    if isinstance(database, dict):
        database = _deserialize_path(database, project_dir)
    dialect = url_dict.get("dialect") or "sqlite"
    if dialect == "sqlite":
        return "sqlite:///" + database.replace(os.sep, "/")
    host = url_dict.get("host") or ""
    port = f":{url_dict['port']}" if url_dict.get("port") else ""
    return f"{dialect}://{host}{port}/{database}"


def _sqlite_file_stamp(db_url: str) -> tuple[int, int] | None:
    """Returns (mtime, size) of the SQLite file behind db_url, or None if it isn't an existing SQLite file."""
    prefix = "sqlite:///"
    if not db_url.startswith(prefix):
        return None
    try:
        stat = os.stat(db_url[len(prefix) :])
    except OSError:
        return None
    return stat.st_mtime_ns, stat.st_size


def _data_dir(name: str, project_dir: str) -> str:
    """Mirrors spine_engine.project_item.executable_item_base's item data directory convention."""
    return os.path.join(project_dir, PROJECT_CONFIG_DIR_NAME, "items", name.lower().replace(" ", "_"))


def _database_resource_label(item_name: str) -> str:
    """Mirrors spine_items.utils.database_label: the resource label spine_engine keys "known_filters" by."""
    return "db_url@" + item_name


def _resolve_python_interpreter() -> str:
    """Returns the Python interpreter configured in Spine Toolbox settings, or the current one if none is set.

    Reimplemented locally instead of using spine_engine.utils.helpers.resolve_python_interpreter: importing
    spine_engine here (which pulls in networkx) after PySide6 triggers a very slow shiboken signature scan.
    """
    settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
    return settings.value("appSettings/pythonPath") or sys.executable


class ProjectBridge(QObject):
    """Exposes a project's Data Connection file references to QML."""

    # emitted for setup progress/result; status is "info", "success" or "error"
    setupStatusChanged = Signal(str, str)
    # emitted for run progress/result; status is "info", "success" or "error"
    runStatusChanged = Signal(str, str)
    # emitted whenever a workflow run starts or stops
    executionStateChanged = Signal(bool)
    # emitted per output line from a workflow run; kind is "stdout" or "stderr"
    executionLogAppended = Signal(str, str)
    plotsChanged = Signal()
    itemRunStateChanged = Signal(str, str)
    """Emits a display name and its run state: "waiting", "running", "done", "failed", "skipped" or "excluded"."""
    # emitted when the user asks (via the User Mode switch) to go back to the classic Qt UI
    devModeRequested = Signal()

    def __init__(self, project_dir: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_dir = Path(project_dir)
        self._config_file = self._project_dir / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._db_editor = None
        self._database_editor = DatabaseEditorBackend()
        self._filter_names_cache: dict[tuple[str, str], tuple[tuple[int, int], list[str]]] = {}
        self._setup_manager: QProcessExecutionManager | None = None
        self._setup_logger = QtLogger()
        self._setup_logger.msg.connect(lambda text: self.setupStatusChanged.emit(text, "info"))
        self._setup_logger.msg_success.connect(lambda text: self.setupStatusChanged.emit(text, "success"))
        self._setup_logger.msg_error.connect(lambda text: self.setupStatusChanged.emit(text, "error"))
        self._run_manager: QProcessExecutionManager | None = None
        self._written_images: list[Path] = []
        self._member_states: dict[str, str] = {}
        self._display_members: dict[str, list[str]] = {}
        self._display_states: dict[str, str] = {}
        self._run_started = 0.0
        self._saved_pythonpath: str | None = None
        self._plots_watcher = QFileSystemWatcher(self)
        self._plots_watcher.directoryChanged.connect(self.plotsChanged)
        self._run_logger = QtLogger()
        self._run_logger.msg.connect(lambda text: self._handle_run_output(text, "stdout"))
        self._run_logger.msg_proc.connect(lambda text: self._handle_run_output(text, "stdout"))
        self._run_logger.msg_error.connect(lambda text: self.executionLogAppended.emit(text, "stderr"))
        self._run_logger.msg_proc_error.connect(lambda text: self.executionLogAppended.emit(text, "stderr"))

    def _load(self) -> dict:
        if self._config_file.exists():
            with self._config_file.open(encoding="utf-8") as input_file:
                return json.load(input_file)
        if _EXAMPLE_PROJECT_FILE.exists():
            with _EXAMPLE_PROJECT_FILE.open(encoding="utf-8") as input_file:
                return json.load(input_file)
        return {"project": {"version": LATEST_PROJECT_VERSION, "settings": {}}, "items": {}}

    def _save(self, data: dict) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with self._config_file.open("w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=4)

    def _find_data_connection(self, data: dict) -> tuple[str, dict] | tuple[None, None]:
        for name, item in data["items"].items():
            if item.get("type") == "Data Connection":
                return name, item
        return None, None

    def _scenario_selectable_name(self, data: dict, display_name: str) -> str | None:
        """Returns display_name if it (or the stack it names) is listed in project.json's
        "scenario_selectable_items", None otherwise."""
        project = data.get("project", {})
        if display_name in project.get("scenario_selectable_items", []):
            return display_name
        return None

    def _stack_resolver(self, data: dict):
        """Returns a function mapping a raw project.json item name to the display name of the stack
        it belongs to, or to itself if it isn't part of one."""
        stacks = data.get("project", {}).get("stacks", {})
        item_to_stack = {}
        for stack_key, stack in stacks.items():
            display_name = stack.get("name", stack_key)
            for member in stack.get("items", []):
                item_to_stack[member] = display_name
        return lambda name: item_to_stack.get(name, name)

    def _stack_members(self, data: dict, display_name: str) -> list[str]:
        """Returns the raw project.json item names display_name stands for (inverse of _stack_resolver);
        a single-element list of display_name itself if it doesn't name a stack."""
        stacks = data.get("project", {}).get("stacks", {})
        for stack_key, stack in stacks.items():
            if stack.get("name", stack_key) == display_name:
                return list(stack.get("items", []))
        return [display_name]

    def _visible_display_names(self, data: dict) -> set[str]:
        """Returns the display names shown on the User Mode canvas (stacks collapsed to their display
        name), minus anything listed in project.json's "hidden_items"."""
        resolve = self._stack_resolver(data)
        hidden = set(data.get("project", {}).get("hidden_items", []))
        return {resolve(name) for name in data.get("items", {})} - hidden

    def _direct_predecessors(self, data: dict, display_name: str) -> list[str]:
        """Resolved display names with a direct connection into display_name."""
        resolve = self._stack_resolver(data)
        return [
            resolve(connection["from"][0])
            for connection in data.get("project", {}).get("connections", [])
            if resolve(connection["to"][0]) == display_name
        ]

    def _direct_successors(self, data: dict, display_name: str) -> list[str]:
        """Resolved display names with a direct connection out of display_name."""
        resolve = self._stack_resolver(data)
        return [
            resolve(connection["to"][0])
            for connection in data.get("project", {}).get("connections", [])
            if resolve(connection["from"][0]) == display_name
        ]

    def _merge_group(self, data: dict, display_name: str) -> list[str]:
        """Returns display_name plus any other scenario-selectable item that shares a direct downstream
        target with it (single-hop only), so starvation can be judged per shared target rather than
        per item in isolation."""
        selectable = set(data.get("project", {}).get("scenario_selectable_items", []))
        group = {display_name}
        for target in self._direct_successors(data, display_name):
            group.update(name for name in self._direct_predecessors(data, target) if name in selectable)
        return list(group)

    def _find_connection(self, data: dict, from_name: str, to_name: str) -> dict | None:
        """Finds the raw project.json connection whose (possibly stacked) endpoints resolve to
        from_name/to_name, as returned by get_workflow."""
        resolve = self._stack_resolver(data)
        for connection in data.get("project", {}).get("connections", []):
            if resolve(connection["from"][0]) == from_name and resolve(connection["to"][0]) == to_name:
                return connection
        return None

    def _connection_filter_type(self, data: dict, connection: dict) -> str | None:
        """Returns "scenario" or "alternative", whichever filter type is enabled on connection, or None
        if there is nothing to filter: like the classic UI, only a Data Store source provides a filterable
        database resource, and the database must have scenarios/alternatives to choose from."""
        if data.get("items", {}).get(connection["from"][0], {}).get("type") != "Data Store":
            return None
        enabled_types = connection.get("filter_settings", {}).get("enabled_filter_types", {})
        if enabled_types.get("scenario_filter"):
            filter_type = "scenario"
        elif enabled_types.get("alternative_filter"):
            filter_type = "alternative"
        else:
            return None
        return filter_type if self._connection_filter_names(data, connection, filter_type) else None

    def _filter_connection(self, data: dict, connection: dict) -> dict | None:
        """Returns the connection whose filter applies to connection: itself, or, for a link leaving a stack,
        the first filterable link inside that stack, so the filter shows on the stack's outgoing line."""
        if self._connection_filter_type(data, connection) is not None:
            return connection
        resolve = self._stack_resolver(data)
        stack = resolve(connection["from"][0])
        if stack == connection["from"][0]:
            return None
        for inner in data.get("project", {}).get("connections", []):
            if (
                resolve(inner["from"][0]) == stack
                and resolve(inner["to"][0]) == stack
                and self._connection_filter_type(data, inner) is not None
            ):
                return inner
        return None

    def _connection_requires_filter(self, connection: dict, filter_type: str) -> bool:
        return bool(connection.get("options", {}).get(f"require_{filter_type}_filter"))

    def _connection_data_store(self, data: dict, connection: dict) -> tuple[str, dict] | None:
        """Returns (name, item) of whichever endpoint of connection is a Data Store, or None if neither is."""
        raw_items = data.get("items", {})
        for raw_name in (connection["from"][0], connection["to"][0]):
            item = raw_items.get(raw_name, {})
            if item.get("type") == "Data Store":
                return raw_name, item
        return None

    def _connection_database_url(self, data: dict, connection: dict) -> str | None:
        """Returns the URL of whichever endpoint of connection is a Data Store, or None if neither is."""
        endpoint = self._connection_data_store(data, connection)
        if endpoint is None:
            return None
        return _data_store_url(endpoint[1].get("url") or {}, str(self._base_dir()))

    def _connection_resource_label(self, data: dict, connection: dict) -> str | None:
        """Returns the resource label spine_engine uses to key "known_filters" for connection's Data Store
        endpoint, or None if neither endpoint is one."""
        endpoint = self._connection_data_store(data, connection)
        return _database_resource_label(endpoint[0]) if endpoint is not None else None

    def _local_data_path(self) -> Path:
        """Path to this project's local_data.json, which (like the classic Qt UI) holds per-user data such as
        connections' scenario/alternative filter selections, kept out of the shared project.json."""
        return self._base_dir() / PROJECT_CONFIG_DIR_NAME / PROJECT_LOCAL_DATA_DIR_NAME / PROJECT_LOCAL_DATA_FILENAME

    def _load_local_data(self) -> dict:
        local_data_path = self._local_data_path()
        if not local_data_path.exists():
            return {}
        with local_data_path.open(encoding="utf-8") as input_file:
            return json.load(input_file)

    def _save_local_data(self, local_data: dict) -> None:
        local_data_path = self._local_data_path()
        local_data_path.parent.mkdir(parents=True, exist_ok=True)
        with local_data_path.open("w", encoding="utf-8") as output_file:
            json.dump(local_data, output_file, indent=4)

    def _connection_filter_selection(
        self, local_data: dict, connection: dict, resource_label: str, filter_type: str
    ) -> dict:
        """Returns the stored online-state overrides (name -> bool) for resource_label/filter_type, read from
        local_data.json's "known_filters" -- the same file and schema spine_engine itself reads when running
        (see spine_engine.project_item.connection.FilterSettings and spinetoolbox.load_project)."""
        raw_from, raw_to = connection["from"][0], connection["to"][0]
        known_filters = (
            local_data.get("project", {})
            .get("connections", {})
            .get(raw_from, {})
            .get(raw_to, {})
            .get("filter_settings", {})
            .get("known_filters", {})
            .get(resource_label, {})
        )
        return known_filters.get(f"{filter_type}_filter", {})

    def _connection_filter_names(self, data: dict, connection: dict, filter_type: str) -> list[str]:
        """Returns available scenario/alternative names for connection's filter_type, read live from
        whichever endpoint is a Data Store. Falls back to project.json's flat "scenarios"/"alternatives"
        list (used by the bundled demo project, which has no real database) if there's no Data Store
        endpoint or it can't be opened."""
        db_url = self._connection_database_url(data, connection)
        if db_url:
            # opening a database costs ~100 ms, so names are reused until the SQLite file changes
            stamp = _sqlite_file_stamp(db_url)
            cached = self._filter_names_cache.get((db_url, filter_type))
            if cached is not None and stamp is not None and cached[0] == stamp:
                return cached[1]
            from spinedb_api import DatabaseMapping  # imported lazily, same reason as get_database_contents

            try:
                with DatabaseMapping(db_url) as db_map:
                    names = {
                        "scenario": [row.name for row in db_map.query(db_map.scenario_sq)],
                        "alternative": [row.name for row in db_map.query(db_map.alternative_sq)],
                    }
                if stamp is not None:
                    for name_type, type_names in names.items():
                        self._filter_names_cache[(db_url, name_type)] = (stamp, type_names)
                return names[filter_type]
            except Exception:
                pass
        return data.get("project", {}).get(filter_type + "s", [])

    def _connection_filter_items(self, data: dict, local_data: dict, connection: dict, filter_type: str) -> list[dict]:
        """Returns [{"name", "enabled"}, ...] for filter_type on connection: names read live from the
        connected database, online state from local_data.json's "known_filters", defaulting to the link's
        "auto_online" setting for names with no stored override (mirrors spine_engine's own behavior)."""
        names = self._connection_filter_names(data, connection, filter_type)
        resource_label = self._connection_resource_label(data, connection)
        auto_online = connection.get("filter_settings", {}).get("auto_online", True)
        selection = (
            self._connection_filter_selection(local_data, connection, resource_label, filter_type)
            if resource_label is not None
            else {}
        )
        return [{"name": name, "enabled": selection.get(name, auto_online)} for name in names]

    @Slot(str, str, result=str)
    def get_connection_filters(self, from_name: str, to_name: str) -> str:
        """Returns the scenario/alternative filter checklist for the link between from_name and to_name,
        with item names read live from the connected database. Returns {} if there's no such connection
        or it has no filters enabled."""
        data = self._load()
        connection = self._find_connection(data, from_name, to_name)
        if connection is not None:
            connection = self._filter_connection(data, connection)
        if connection is None:
            return json.dumps({})
        filter_type = self._connection_filter_type(data, connection)
        if filter_type is None:
            return json.dumps({})
        items = self._connection_filter_items(data, self._load_local_data(), connection, filter_type)
        required = self._connection_requires_filter(connection, filter_type)
        return json.dumps({"filter_type": filter_type, "required": required, "items": items})

    @Slot(str, str, str, str, bool, result=bool)
    def set_connection_filter_enabled(
        self, from_name: str, to_name: str, filter_type: str, item_name: str, enabled: bool
    ) -> bool:
        """Stores whether item_name is online for filter_type ("scenario"/"alternative") on the connection
        between from_name and to_name, in local_data.json's "known_filters" -- the same place and schema
        spine_engine reads when actually running the project. Returns whether such a connection exists."""
        data = self._load()
        connection = self._find_connection(data, from_name, to_name)
        if connection is not None:
            connection = self._filter_connection(data, connection)
        if connection is None:
            return False
        resource_label = self._connection_resource_label(data, connection)
        if resource_label is None:
            return False
        raw_from, raw_to = connection["from"][0], connection["to"][0]
        local_data = self._load_local_data()
        known_filters = (
            local_data.setdefault("project", {})
            .setdefault("connections", {})
            .setdefault(raw_from, {})
            .setdefault(raw_to, {})
            .setdefault("filter_settings", {})
            .setdefault("known_filters", {})
            .setdefault(resource_label, {})
        )
        known_filters.setdefault(f"{filter_type}_filter", {})[item_name] = enabled
        self._save_local_data(local_data)
        return True

    @Slot(str, result=str)
    def get_item_scenarios(self, display_name: str) -> str:
        """Returns [{"name": ..., "enabled": ...}, ...] for display_name, demo-only: scenarios and their
        per-item enabled state both come straight from project.json ("scenarios"/"item_scenario_selection"),
        no database is queried. Returns an empty list if display_name isn't scenario-selectable."""
        data = self._load()
        project = data.get("project", {})
        name = self._scenario_selectable_name(data, display_name)
        if name is None:
            return json.dumps([])

        scenarios = project.get("scenarios", [])
        selection = project.get("item_scenario_selection", {}).get(name, {})
        return json.dumps([{"name": scenario, "enabled": selection.get(scenario, True)} for scenario in scenarios])

    @Slot(result=str)
    def get_scenario_status(self) -> str:
        """Returns [{"name", "total", "enabled", "state"}, ...] for every visible scenario-selectable
        item. state is "ok" (it has scenarios enabled), "disabled_ok" (none enabled here, but another
        item feeding the same direct downstream target does), or "error" (none enabled here and nothing
        else feeding the same target(s) does either, so that target would get no data from this side)."""
        data = self._load()
        project = data.get("project", {})
        visible = self._visible_display_names(data)
        scenarios = project.get("scenarios", [])
        selections = project.get("item_scenario_selection", {})

        counts = {}
        for name in project.get("scenario_selectable_items", []):
            if name not in visible:
                continue
            selection = selections.get(name, {})
            enabled = sum(1 for scenario in scenarios if selection.get(scenario, True))
            counts[name] = enabled

        statuses = []
        for name, enabled in counts.items():
            if enabled > 0:
                state = "ok"
            elif any(counts.get(sibling, 0) > 0 for sibling in self._merge_group(data, name) if sibling != name):
                state = "disabled_ok"
            else:
                state = "error"
            statuses.append({"name": name, "total": len(scenarios), "enabled": enabled, "state": state})
        return json.dumps(statuses)

    @Slot(result=bool)
    def has_starved_scenarios(self) -> bool:
        """Returns whether any visible scenario-selectable item is in get_scenario_status()'s "error" state."""
        return any(item["state"] == "error" for item in json.loads(self.get_scenario_status()))

    @Slot(result=bool)
    def has_unselected_scenarios(self) -> bool:
        """Returns whether any visible connection's scenario/alternative filter is in an "error" state
        (nothing enabled on it, and no sibling line into the same target covers it either). Hidden
        items/connections are ignored since they don't run in User Mode. Item-level scenario starvation
        is covered separately by has_starved_scenarios()."""
        data = self._load()
        return any(connection["filter_state"] == "error" for connection in self._connection_filter_states(data))

    @Slot(str, str, bool, result=bool)
    def set_item_scenario_enabled(self, display_name: str, scenario_name: str, enabled: bool) -> bool:
        """Stores whether scenario_name is enabled for display_name in project.json's
        "item_scenario_selection". Returns whether display_name is scenario-selectable."""
        data = self._load()
        project = data.setdefault("project", {})
        name = self._scenario_selectable_name(data, display_name)
        if name is None:
            return False

        project.setdefault("item_scenario_selection", {}).setdefault(name, {})[scenario_name] = enabled
        self._save(data)
        return True

    def _base_dir(self) -> Path:
        """Returns the project directory items are relative to, falling back to the bundled example's own
        folder when no real project is open (self._project_dir is then just the launch cwd)."""
        if self._config_file.exists():
            return self._project_dir
        return _EXAMPLE_PROJECT_FILE.parent

    @property
    def project_dir(self) -> str:
        """Directory of the project currently open, or "" if none (e.g. the bundled example is shown instead)."""
        return str(self._project_dir) if self._config_file.exists() else ""

    @Slot(result=bool)
    def has_setup_script(self) -> bool:
        """Returns whether the open project bundles a dependency/setup script (e.g. FlexTool's update_flextool.py)."""
        return (self._base_dir() / PROJECT_SETUP_SCRIPT).is_file()

    @Slot(result=bool)
    def is_project_setup_done(self) -> bool:
        """Returns whether the setup script has already completed successfully for the open project."""
        project_dir = str(self._base_dir())
        return QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).value(
            f"appSettings/projectSetupDone/{project_dir}", defaultValue=False, type=bool
        )

    @Slot()
    def install_project_dependencies(self) -> None:
        """Editable-installs the project directory, then runs its setup script once that finishes."""
        project_dir = str(self._base_dir())
        python = _resolve_python_interpreter()
        self._setup_manager = QProcessExecutionManager(
            self._setup_logger, python, ["-m", "pip", "install", "--upgrade", "-e", project_dir], semisilent=True
        )
        self._setup_manager.execution_finished.connect(
            lambda exit_code: self._handle_install_finished(exit_code, project_dir)
        )
        self._setup_logger.msg.emit(f"Installing dependencies for {project_dir}...")
        self._setup_manager.start_execution()

    def _handle_install_finished(self, exit_code: int, project_dir: str) -> None:
        """Runs the project's setup script once its dependencies have been installed."""
        self._setup_manager = None
        if exit_code != 0:
            self._setup_logger.msg_error.emit("Installing project dependencies failed, setup script was not run")
            return
        python = _resolve_python_interpreter()
        script_path = os.path.join(project_dir, PROJECT_SETUP_SCRIPT)
        self._setup_manager = QProcessExecutionManager(
            self._setup_logger, python, [script_path, "--skip-git"], semisilent=True
        )
        self._setup_manager.execution_finished.connect(
            lambda exit_code: self._handle_setup_finished(exit_code, project_dir)
        )
        self._setup_logger.msg.emit(f"Running {PROJECT_SETUP_SCRIPT}...")
        self._setup_manager.start_execution(workdir=project_dir)

    def _handle_setup_finished(self, exit_code: int, project_dir: str) -> None:
        """Reports the outcome of the project setup script."""
        self._setup_manager = None
        if exit_code == 0:
            # same QSettings key the classic Qt UI checks, so it won't offer to install again for this project
            QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).setValue(
                f"appSettings/projectSetupDone/{project_dir}", True
            )
            self._setup_logger.msg_success.emit("Project setup finished successfully")
        else:
            self._setup_logger.msg_error.emit("Project setup script failed")

    def _handle_run_output(self, text: str, kind: str) -> None:
        """Turns progress marker lines into item state updates and forwards everything else to the run log."""
        if PROGRESS_MARKER not in text:
            self.executionLogAppended.emit(text, kind)
            return
        lines = text.splitlines()
        log_text = "\n".join(line for line in lines if PROGRESS_MARKER not in line)
        if log_text.strip():
            self.executionLogAppended.emit(log_text, kind)
        for line in lines:
            if PROGRESS_MARKER in line:
                state, item_name = line.split(PROGRESS_MARKER, 1)[1].strip().split(maxsplit=1)
                self._member_states[item_name] = state
                self._publish_display_state(self._display_name_of(item_name))

    def _included_items(self, selected: set[str], data: dict) -> set[str]:
        """Returns the items the engine goes through for selected: those connected to a selected item
        (same rule as the classic UI's SpineEngineWorker)."""
        included = set()
        for connection in data.get("project", {}).get("connections", []):
            source, destination = connection["from"][0], connection["to"][0]
            if source in selected or destination in selected:
                included.update((source, destination))
        return included or selected

    def _display_state(self, display_name: str) -> str:
        members = self._display_members[display_name]
        states = {self._member_states[member] for member in members if member in self._member_states}
        for state in ("failed", "running", "waiting", "done", "excluded", "skipped"):
            if state in states:
                return state
        return ""

    def _publish_display_state(self, display_name: str) -> None:
        if display_name not in self._display_members:
            return
        state = self._display_state(display_name)
        if state != self._display_states.get(display_name, ""):
            self._display_states[display_name] = state
            self.itemRunStateChanged.emit(display_name, state)

    def _display_name_of(self, item_name: str) -> str:
        return next((name for name, members in self._display_members.items() if item_name in members), item_name)

    @Slot(list)
    def run_workflow(self, selected_names: list) -> None:
        """Runs the project (or, if selected_names is non-empty, just those items/stacks) via the
        existing headless CLI, so execution reuses the real engine instead of reimplementing it here.
        An empty selected_names means "run project": defaults to every item visible in User Mode,
        excluding anything hidden there."""
        if self._run_manager is not None:
            self.runStatusChanged.emit("A run is already in progress", "error")
            return
        data = self._load()
        if not selected_names:
            selected_names = self._visible_display_names(data)
        real_names = sorted(
            {name for display_name in selected_names for name in self._stack_members(data, display_name)}
        )
        project_dir = str(self._base_dir())
        args = [project_dir, "--execute-only"]
        if real_names:
            args += ["--select", *real_names]
        python = _resolve_python_interpreter()
        self._display_members = {name: self._stack_members(data, name) for name in self._visible_display_names(data)}
        self._member_states = {name: "waiting" for name in self._included_items(set(real_names), data)}
        self._display_states = {}
        os.environ[REPORT_PROGRESS_ENV_VAR] = "1"
        os.environ["PYTHONUNBUFFERED"] = "1"
        plots_dir = self._plots_dir()
        shutil.rmtree(plots_dir, ignore_errors=True)
        plots_dir.mkdir(parents=True, exist_ok=True)
        os.environ[PLOTS_DIR_ENV_VAR] = str(plots_dir)
        self._saved_pythonpath = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).parent / "plot_capture")] + ([self._saved_pythonpath] if self._saved_pythonpath else [])
        )
        self._run_started = time.time()
        self._written_images = []
        if self._plots_watcher.directories():
            self._plots_watcher.removePaths(self._plots_watcher.directories())
        self._plots_watcher.addPath(str(plots_dir))
        self.plotsChanged.emit()
        self._run_logger.msg.emit("Running: " + " ".join([python, "-m", "spinetoolbox", *args]))
        self._run_manager = QProcessExecutionManager(
            self._run_logger, python, ["-m", "spinetoolbox", *args], semisilent=True
        )
        self._run_manager.execution_finished.connect(self._handle_run_finished)
        self.executionStateChanged.emit(True)
        for display_name in self._display_members:
            self._publish_display_state(display_name)
        self.runStatusChanged.emit("Running project...", "info")
        self._run_manager.start_execution(workdir=project_dir)

    @Slot()
    def stop_workflow(self) -> None:
        """Stops the currently running workflow, if any."""
        if self._run_manager is not None:
            self._run_manager.stop_execution()

    def _handle_run_finished(self, exit_code: int) -> None:
        """Reports the outcome of a workflow run."""
        user_stopped = self._run_manager.user_stopped
        self._run_manager = None
        os.environ.pop(PLOTS_DIR_ENV_VAR, None)
        os.environ.pop(REPORT_PROGRESS_ENV_VAR, None)
        os.environ.pop("PYTHONUNBUFFERED", None)
        if self._saved_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = self._saved_pythonpath
        self._written_images = self._find_written_images()
        self._database_editor.refresh_sessions()
        for member, state in list(self._member_states.items()):
            if state in ("waiting", "running"):
                if exit_code != 0 and not user_stopped:
                    self._member_states[member] = "failed"
                else:
                    del self._member_states[member]
        for display_name in self._display_members:
            self._publish_display_state(display_name)
        self.executionStateChanged.emit(False)
        self.plotsChanged.emit()
        if user_stopped:
            self.runStatusChanged.emit("Execution stopped", "info")
        elif exit_code == 0:
            self.runStatusChanged.emit("Execution finished successfully", "success")
        else:
            self.runStatusChanged.emit("Execution failed", "error")

    def _plots_dir(self) -> Path:
        return self._base_dir() / PROJECT_CONFIG_DIR_NAME / "easy_mode_plots"

    def _find_written_images(self) -> list[Path]:
        """Returns image files in the project that were written since the run started."""
        found = []
        for root, dirs, files in os.walk(self._base_dir()):
            dirs[:] = [d for d in dirs if d not in _IMAGE_SCAN_SKIPPED_DIRS and d != "easy_mode_plots"]
            for name in files:
                path = Path(root, name)
                if path.suffix.lower() in _IMAGE_SUFFIXES and path.stat().st_mtime >= self._run_started:
                    found.append(path)
        return sorted(found)

    @Slot(result=list)
    def get_plots(self) -> list:
        """Returns file URLs of the plots and images produced by the latest run."""
        paths = [*sorted(self._plots_dir().glob("*.png")), *self._written_images]
        return [QUrl.fromLocalFile(str(path)).toString() for path in paths]

    @Slot(result=bool)
    def is_execution_running(self) -> bool:
        """Returns whether a workflow run is currently in progress."""
        return self._run_manager is not None

    def _add_recent_project(self, name: str, project_dir: str) -> None:
        """Mirrors spinetoolbox.helpers.update_recent_projects so both UIs share the same recent-projects list."""
        settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
        entry = name + "<>" + project_dir
        recents = settings.value("appSettings/recentProjects", defaultValue=None)
        if not recents:
            recents_list = [entry]
        else:
            recents_list = str(recents).split("\n")
            normalized = [os.path.normcase(item) for item in recents_list]
            try:
                recents_list.insert(0, recents_list.pop(normalized.index(os.path.normcase(entry))))
            except ValueError:
                recents_list.insert(0, entry)
                del recents_list[20:]
        settings.setValue("appSettings/recentProjects", "\n".join(recents_list))
        settings.sync()

    @Slot(result=str)
    def get_project_name(self) -> str:
        """Returns the current project's name, falling back to the bundled example when none is open yet."""
        if (self._project_dir / PROJECT_CONFIG_DIR_NAME).is_dir():
            return self._project_dir.name
        if _EXAMPLE_PROJECT_FILE.exists():
            return _EXAMPLE_PROJECT_NAME
        return ""

    def _connection_filter_states(self, data: dict) -> list[dict]:
        """Returns {"from", "to", "filter_type", "filter_required", "filter_satisfied", "filter_state"} for
        every visible, de-duplicated (stack-collapsed) connection. filter_state is None when the connection
        has no filter, else "ok"/"disabled_ok"/"error" -- an unsatisfied filter is only an "error" if no
        sibling line into the same target is satisfied either (that sibling still supplies the target)."""
        project = data.get("project", {})
        resolve = self._stack_resolver(data)
        visible = self._visible_display_names(data)
        local_data = self._load_local_data()

        connections = []
        seen = set()
        for connection in project.get("connections", []):
            from_name = resolve(connection["from"][0])
            to_name = resolve(connection["to"][0])
            if from_name == to_name or from_name not in visible or to_name not in visible:
                continue  # internal to a stack, hidden while collapsed, or not shown in User Mode
            key = (from_name, to_name)
            if key in seen:
                continue
            seen.add(key)
            carrier = self._filter_connection(data, connection)
            filter_type = self._connection_filter_type(data, carrier) if carrier is not None else None
            filter_required = filter_type is not None and self._connection_requires_filter(carrier, filter_type)
            filter_satisfied = True
            if filter_type is not None:
                # zero enabled items means nothing actually passes through the link, regardless of
                # whether "require filter online" is set -- that flag only affects wording, not reality
                filter_items = self._connection_filter_items(data, local_data, carrier, filter_type)
                filter_satisfied = any(item["enabled"] for item in filter_items)
            connections.append(
                {
                    "from": from_name,
                    "to": to_name,
                    "from_anchor": connection["from"][1] if len(connection["from"]) > 1 else "right",
                    "to_anchor": connection["to"][1] if len(connection["to"]) > 1 else "left",
                    "filter_type": filter_type,
                    "filter_required": filter_required,
                    "filter_satisfied": filter_satisfied,
                }
            )

        for connection in connections:
            if connection["filter_type"] is None:
                connection["filter_state"] = None
            elif connection["filter_satisfied"]:
                connection["filter_state"] = "ok"
            else:
                siblings_satisfied = any(
                    other["filter_satisfied"]
                    for other in connections
                    if other is not connection and other["to"] == connection["to"] and other["filter_type"] is not None
                )
                connection["filter_state"] = "disabled_ok" if siblings_satisfied else "error"
        return connections

    def _stack_position(self, data: dict, members: list[str]) -> tuple[float, float]:
        """Returns the dev mode position of the members connected to items outside the stack, so the stack
        sits where it links to the rest of the workflow; all members count if none are connected outside."""
        raw_items = data.get("items", {})
        member_set = set(members)
        connected = {
            endpoint[0]
            for connection in data.get("project", {}).get("connections", [])
            if (connection["from"][0] in member_set) != (connection["to"][0] in member_set)
            for endpoint in (connection["from"], connection["to"])
            if endpoint[0] in member_set
        }
        anchors = [name for name in members if name in connected] or members
        x = sum(raw_items[name].get("x", 0.0) for name in anchors) / len(anchors)
        y = sum(raw_items[name].get("y", 0.0) for name in anchors) / len(anchors)
        return x, y

    @Slot(result=str)
    def get_workflow(self) -> str:
        """Returns items/connections as JSON, collapsing any project.json "stacks" into a single node each."""
        data = self._load()
        project = data.get("project", {})
        raw_items = data.get("items", {})
        stacks = project.get("stacks", {})

        item_to_stack = {}
        for stack_key, stack in stacks.items():
            display_name = stack.get("name", stack_key)
            for member in stack.get("items", []):
                item_to_stack[member] = display_name

        items = []
        for stack_key, stack in stacks.items():
            members = [name for name in stack.get("items", []) if name in raw_items]
            if not members:
                continue
            x, y = self._stack_position(data, members)
            display_name = stack.get("name", stack_key)
            items.append({"name": display_name, "type": "Stack", "x": x, "y": y, "subtitle": "Stack"})
        for name, item in raw_items.items():
            if name in item_to_stack:
                continue
            item_type = item.get("type", "")
            items.append(
                {"name": name, "type": item_type, "x": item.get("x", 0.0), "y": item.get("y", 0.0), "subtitle": item_type}
            )

        # items/stacks listed here stay in project.json untouched, just hidden from this simplified view
        hidden = set(project.get("hidden_items", []))
        items = [item for item in items if item["name"] not in hidden]
        connections = self._connection_filter_states(data)

        return json.dumps({"items": items, "connections": connections})

    def _resolve_item_directory(self, name: str, item: dict) -> Path | None:
        """Prefers the item's real (executed) data directory, then the folder holding its first file
        reference, then falls back to the project root; returns None if nothing usable exists."""
        project_dir = self._base_dir()
        data_dir = Path(_data_dir(name, str(project_dir)))
        if data_dir.is_dir():
            return data_dir
        for reference in item.get("file_references") or []:
            reference_path = Path(_deserialize_path(reference, str(project_dir)))
            if reference_path.exists():
                return reference_path.parent
        return project_dir if project_dir.is_dir() else None

    def _stack_member_of_type(self, data: dict, display_name: str, item_type: str) -> tuple[str, dict] | None:
        """Returns (name, item) of display_name itself if it matches item_type, or of the first item_type
        member of the stack display_name names; None if neither applies."""
        raw_items = data.get("items", {})
        stacks = data.get("project", {}).get("stacks", {})

        member_names = stacks.get(display_name, {}).get("items") if display_name not in raw_items else [display_name]
        if member_names is None:
            for stack in stacks.values():
                if stack.get("name") == display_name:
                    member_names = stack.get("items", [])
                    break

        for name in member_names or []:
            item = raw_items.get(name, {})
            if item.get("type") == item_type:
                return name, item
        return None

    @Slot(str, result=bool)
    def open_item_directory(self, display_name: str) -> bool:
        """Opens the data directory of the Data Connection item called display_name, or, if display_name is a
        collapsed stack, of the first Data Connection item inside it. Returns whether a directory was opened."""
        data = self._load()
        found = self._stack_member_of_type(data, display_name, "Data Connection")
        if found is None:
            return False
        name, item = found
        directory = self._resolve_item_directory(name, item)
        if directory is None:
            return False
        return open_url(directory.as_uri())

    @Slot(str, result=bool)
    def open_database(self, display_name: str) -> bool:
        """Opens the Data Store item called display_name (or the first Data Store inside the stack it names)
        in the classic Qt DB Editor, reusing the same tab if that database is already open there."""
        data = self._load()
        found = self._stack_member_of_type(data, display_name, "Data Store")
        if found is None:
            return False
        _name, item = found
        url = _data_store_url(item.get("url") or {}, str(self._base_dir()))
        if not url:
            return False
        self._ensure_db_editor()
        self._db_editor.open_url_in_new_tab(url)
        self._db_editor.show()
        self._db_editor.raise_()
        self._db_editor.activateWindow()
        return True

    @Slot(str, result=str)
    def open_project(self, folder_url: str) -> str:
        """Switches to the project at folder_url and registers it as a recent project; empty string means invalid."""
        local_path = Path(QUrl(folder_url).toLocalFile() or folder_url)
        if not (local_path / PROJECT_CONFIG_DIR_NAME).is_dir():
            return ""
        self._close_sessions()
        self._project_dir = local_path
        self._config_file = local_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._add_recent_project(local_path.name, str(local_path))
        return local_path.name

    @Slot()
    def open_dev_mode(self) -> None:
        """Requests switching to the classic Qt UI; the embedder decides how (see devModeRequested)."""
        self.devModeRequested.emit()

    def _database_urls(self) -> list[str]:
        data = self._load()
        urls = []
        for item in data["items"].values():
            if item.get("type") != "Data Store":
                continue
            url = _data_store_url(item.get("url") or {}, str(self._project_dir))
            if url:
                urls.append(url)
        return urls

    def _ensure_db_editor(self) -> None:
        """Creates self._db_editor, with no tabs open yet, if it doesn't already exist."""
        if self._db_editor is not None:
            return
        # imported lazily: pulls in the full widget/spinedb_api stack, only needed once the user asks for it
        from ...spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
        from ...spine_db_manager import SpineDBManager

        settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
        db_mngr = SpineDBManager(settings, None)
        editor = MultiSpineDBEditor(db_mngr)
        editor.destroyed.connect(self._forget_db_editor)
        self._db_editor = editor

    @Slot()
    def open_database_editor(self) -> None:
        """Opens the classic Qt DB Editor (in-process) with every Data Store in the project, each in its own tab."""
        is_new = self._db_editor is None
        self._ensure_db_editor()
        if is_new:
            self._db_editor.add_new_tab(self._database_urls())
        self._db_editor.show()
        self._db_editor.raise_()
        self._db_editor.activateWindow()

    def _forget_db_editor(self) -> None:
        self._db_editor = None

    @Slot(result=str)
    def get_databases(self) -> str:
        return self._database_editor.get_databases(self._load(), str(self._base_dir()), _data_store_url)

    @Slot(str, result=str)
    def get_database_contents(self, url: str) -> str:
        return self._database_editor.get_database_contents(url)

    @Slot(str, str, result=str)
    def get_entity_class_values(self, url: str, class_name: str) -> str:
        return self._database_editor.get_entity_class_values(url, class_name)

    @Slot(str, str, str, result=str)
    def get_pivot(self, url: str, class_name: str, alternative: str) -> str:
        return self._database_editor.get_pivot(url, class_name, alternative)

    def _close_sessions(self) -> None:
        self._database_editor.close_sessions()

    @Slot(str, result=str)
    def reload_database(self, url: str) -> str:
        return self._database_editor.reload_database(url)

    @Slot(str, result=str)
    def get_session_state(self, url: str) -> str:
        return self._database_editor.get_session_state(url)

    @Slot(str, str, str, result=str)
    def add_item(self, url: str, item_type: str, fields_json: str) -> str:
        return self._database_editor.add_item(url, item_type, fields_json)

    @Slot(str, str, str, str, result=str)
    def update_item(self, url: str, item_type: str, key_json: str, fields_json: str) -> str:
        return self._database_editor.update_item(url, item_type, key_json, fields_json)

    @Slot(str, str, str, result=str)
    def remove_item(self, url: str, item_type: str, key_json: str) -> str:
        return self._database_editor.remove_item(url, item_type, key_json)

    @Slot(str, str, str, result=str)
    def set_scenario_alternatives(self, url: str, scenario_name: str, alternative_names_json: str) -> str:
        return self._database_editor.set_scenario_alternatives(url, scenario_name, alternative_names_json)

    @Slot(str, str, str, str, str, str, result=str)
    def set_parameter_value(
        self, url: str, class_name: str, entity: str, parameter: str, alternative: str, text: str
    ) -> str:
        return self._database_editor.set_parameter_value(url, class_name, entity, parameter, alternative, text)

    @Slot(str, result=str)
    def undo_edit(self, url: str) -> str:
        return self._database_editor.undo_edit(url)

    @Slot(str, result=str)
    def redo_edit(self, url: str) -> str:
        return self._database_editor.redo_edit(url)

    @Slot(str, str, result=str)
    def commit_edits(self, url: str, comment: str) -> str:
        return self._database_editor.commit_edits(url, comment)

    @Slot(str, result=str)
    def discard_edits(self, url: str) -> str:
        return self._database_editor.discard_edits(url)

    @Slot(result=str)
    def get_input_reference(self) -> str:
        """Returns the first Data Connection file reference, or an empty string if there is none."""
        data = self._load()
        _name, item = self._find_data_connection(data)
        if item is None:
            return ""
        references = item.get("file_references") or item.get("references") or []
        if not references:
            return ""
        return _deserialize_path(references[0], str(self._project_dir))

    @Slot(str, result=str)
    def set_input_reference(self, file_url: str) -> str:
        """Stores file_url as the project's Data Connection file reference and returns its display name."""
        local_path = QUrl(file_url).toLocalFile() or file_url
        data = self._load()
        name, item = self._find_data_connection(data)
        if item is None:
            name = _INPUT_DATA_CONNECTION_NAME
            item = {"type": "Data Connection", "description": "", "x": 0.0, "y": 0.0, "db_references": []}
            data["items"][name] = item
        item["file_references"] = [_serialize_path(local_path, str(self._project_dir))]
        self._save(data)
        return os.path.basename(local_path)

