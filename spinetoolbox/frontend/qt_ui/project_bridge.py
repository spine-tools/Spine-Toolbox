"""Reads and writes the same project.json Data Connection file references as the classic Qt UI."""

import hashlib
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import time
from PySide6.QtCore import (
    QFileSystemWatcher,
    QItemSelectionModel,
    QModelIndex,
    QObject,
    QRect,
    QSettings,
    Qt,
    QTimer,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from spine_engine.project_item.connection import FilterSettings
from spine_engine.utils.helpers import (
    connections_to_selected_items,
    gather_leaf_data,
    resolve_python_interpreter,
    shorten,
)
from spine_engine.utils.serialization import deserialize_path, serialize_path
from spine_items.utils import convert_to_sqlalchemy_url, database_label
from ...config import (
    LATEST_PROJECT_VERSION,
    PLOTS_DIR_ENV_VAR,
    PROGRESS_MARKER,
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_FILENAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_LOCAL_DATA_FILENAME,
    REPORT_PROGRESS_ENV_VAR,
)
from ...execution_managers import QProcessExecutionManager
from ...helpers import (
    find_project_setup_script,
    is_installable_project,
    is_spine_toolbox_project_dir,
    normcase_database_url_path,
    open_url,
    update_recent_projects,
)
from ...load_project import load_local_project_dict, load_project_dict, merge_local_dict_to_project_dict
from ...logger import QtLogger
from ...project_item.logging_connection import HeadlessConnection
from ...project_upgrader import upgrade_to_latest
from .database_editor_backend import DatabaseEditorBackend
from .saved_plots import SavedPlots

_INPUT_DATA_CONNECTION_NAME = "Input data"
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg"}
_IMAGE_SCAN_SKIPPED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}

# QSettings organization and application names; recent projects are stored under "appSettings/recentProjects"
_SETTINGS_ORGANIZATION = "SpineProject"
_SETTINGS_APPLICATION = "Spine Toolbox"
_TOUR_SEEN_KEY = "appSettings/userModeTourSeen"
_USER_POSITIONS_FILENAME = "user_mode.json"
_STORE_CHAINS_FILENAME = "user_mode_stores.json"
_RUN_RESULTS_FILENAME = "user_mode_runs.json"
# joins the keys of several selected chains into one key
CHAIN_KEY_SEPARATOR = "\x1f"


def _data_store_url(url_dict: dict, project_dir: str) -> str | None:
    """Builds a SQLAlchemy URL string from a Data Store item's "url" dict, or None if the dict is incomplete."""
    database = url_dict.get("database")
    if isinstance(database, dict):
        url_dict = {**url_dict, "database": deserialize_path(database, project_dir)}
    sa_url = convert_to_sqlalchemy_url(url_dict)
    return sa_url.render_as_string(hide_password=False) if sa_url is not None else None


def _find_project_folder(folder: Path, max_depth: int = 2) -> Path | None:
    """Returns folder or its nearest subfolder, up to max_depth levels down, that is a Spine Toolbox project."""
    level = [folder]
    for _ in range(max_depth + 1):
        for candidate in level:
            if is_spine_toolbox_project_dir(str(candidate)):
                return candidate
        children = []
        for parent in level:
            try:
                children += sorted(
                    child
                    for child in parent.iterdir()
                    if child.is_dir() and not child.name.startswith(".") and child.name not in _IMAGE_SCAN_SKIPPED_DIRS
                )
            except OSError:
                continue
        level = children
    return None


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


class ProjectBridge(QObject):
    """Exposes a project's Data Connection file references to QML."""

    # emitted for setup progress/result; status is "info", "success" or "error"
    setupStatusChanged = Signal(str, str)
    # emitted when the project's dependency installation starts or ends
    setupRunningChanged = Signal(bool)
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
    # emitted when the Data view should be shown, e.g. after a Data Store is opened from the workflow
    dataViewRequested = Signal()
    # emitted when the record of which chain filled which database changes
    storeWarningsChanged = Signal()
    # emitted when a run has finished and its results were recorded
    runResultsChanged = Signal()

    def __init__(self, project_dir: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_dir = Path(project_dir)
        self._config_file = self._project_dir / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._db_editors: dict[str, QWidget] = {}
        self._data_areas: dict[str, tuple[QRect, bool]] = {}
        self._database_editor = DatabaseEditorBackend()
        self._filter_names_cache: dict[tuple[str, str], tuple[tuple[int, int], list[str]]] = {}
        self._setup_manager: QProcessExecutionManager | None = None
        self._setup_logger = QtLogger()
        self._setup_logger.msg.connect(lambda text: self._report_setup(text, "info"))
        self._setup_logger.msg_success.connect(lambda text: self._report_setup(text, "success"))
        self._setup_logger.msg_error.connect(lambda text: self._report_setup(text, "error"))
        self._setup_logger.msg_proc.connect(self._show_setup_output)
        self._setup_logger.msg_proc_error.connect(self._remember_setup_error)
        self._setup_last_error = ""
        self._run_manager: QProcessExecutionManager | None = None
        self._written_images: list[Path] = []
        self._member_states: dict[str, str] = {}
        self._display_members: dict[str, list[str]] = {}
        self._display_states: dict[str, str] = {}
        self._run_started = 0.0
        self._run_info: dict = {}
        self._saved_pythonpath: str | None = None
        self._plots_watcher = QFileSystemWatcher(self)
        self._plots_watcher.directoryChanged.connect(self.plotsChanged)
        self._run_logger = QtLogger()
        self._run_logger.msg.connect(lambda text: self._handle_run_output(text, "stdout"))
        self._run_logger.msg_proc.connect(lambda text: self._handle_run_output(text, "stdout"))
        self._run_logger.msg_error.connect(lambda text: self.executionLogAppended.emit(text, "stderr"))
        self._run_logger.msg_proc_error.connect(lambda text: self.executionLogAppended.emit(text, "stderr"))

    def _load_raw(self) -> dict:
        """Returns project data as stored, without upgrading; use this when the result is going to be saved."""
        if self._config_file.exists():
            return load_project_dict(self._project_dir)
        return {"project": {"version": LATEST_PROJECT_VERSION, "settings": {}}, "items": {}}

    def _load(self) -> dict:
        """Returns project data upgraded to the latest version in memory; the file on disk is left as is."""
        data = self._load_raw()
        version = data.get("project", {}).get("version", LATEST_PROJECT_VERSION)
        # versions 1 and 2 need item factories, which the bridge does not have
        if version >= LATEST_PROJECT_VERSION or version < 3:
            return data
        return upgrade_to_latest(version, data, self._project_dir, {}, lambda message: None)

    def _load_merged(self) -> dict:
        """Returns project data with local_data.json merged in. The result holds per-user data and must not be saved."""
        data = self._load()
        merge_local_dict_to_project_dict(load_local_project_dict(self._base_dir()), data)
        return data

    def _save(self, data: dict) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with self._config_file.open("w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=4)

    def _find_data_connection(self, data: dict) -> tuple[str, dict] | tuple[None, None]:
        for name, item in data["items"].items():
            if item.get("type") == "Data Connection":
                return name, item
        return None, None

    @staticmethod
    def _chain(data: dict, chain_key: str) -> dict | None:
        """Returns the chain of chain_key; several keys joined by CHAIN_KEY_SEPARATOR give their combined entries."""
        chains = data.get("project", {}).get("chains", {}).get("items", {})
        selected = [chains[key] for key in chain_key.split(CHAIN_KEY_SEPARATOR) if key in chains]
        if len(selected) < 2:
            return selected[0] if selected else None
        return {"entries": [entry for chain in selected for entry in chain.get("entries", [])]}

    def _stack_resolver(self, data: dict, chain_key: str = ""):
        """Returns a function mapping a raw project.json item name to the display name of the stack
        it belongs to, or to itself if it isn't part of one. Items a chain lists on their own
        are not collapsed into their stack."""
        stacks = data.get("project", {}).get("stacks", {})
        item_to_stack = {}
        for stack_key, stack in stacks.items():
            display_name = stack.get("name", stack_key)
            for member in stack.get("items", []):
                item_to_stack[member] = display_name
        chain = self._chain(data, chain_key)
        single_items = {entry["item"] for entry in chain["entries"] if "item" in entry} if chain else set()
        return lambda name: name if name in single_items else item_to_stack.get(name, name)

    def _stack_members(self, data: dict, display_name: str) -> list[str]:
        """Returns the raw project.json item names display_name stands for (inverse of _stack_resolver);
        a single-element list of display_name itself if it doesn't name a stack."""
        stacks = data.get("project", {}).get("stacks", {})
        for stack_key, stack in stacks.items():
            if stack.get("name", stack_key) == display_name:
                return list(stack.get("items", []))
        return [display_name]

    def _visible_display_names(self, data: dict, chain_key: str = "") -> set[str]:
        """Returns the display names shown on the User Mode canvas (stacks collapsed to their display
        name), minus anything listed in project.json's "hidden_items". A chain limits them to its entries."""
        resolve = self._stack_resolver(data, chain_key)
        hidden = set(data.get("project", {}).get("hidden_items", []))
        names = {resolve(name) for name in data.get("items", {})}
        chain = self._chain(data, chain_key)
        if chain:
            stacks = data.get("project", {}).get("stacks", {})
            names &= {entry["item"] for entry in chain["entries"] if "item" in entry} | {
                stacks[entry["stack"]].get("name", entry["stack"])
                for entry in chain["entries"]
                if entry.get("stack") in stacks
            }
        stack_of = self._stack_resolver(data)
        return {name for name in names if name not in hidden and stack_of(name) not in hidden}

    def _find_filter_connection(self, data: dict, from_name: str, to_name: str) -> dict | None:
        """Returns the connection carrying the filter of the link from_name -> to_name, as returned by
        get_workflow, or None if there is no such link or it has no filter."""
        resolve = self._stack_resolver(data)
        for connection in data.get("project", {}).get("connections", []):
            if resolve(connection["from"][0]) == from_name and resolve(connection["to"][0]) == to_name:
                return self._filter_connection(data, connection)
        return None

    def _connection_filter_type(self, data: dict, connection: dict) -> str | None:
        """Returns "scenario" or "alternative", whichever filter type is enabled on connection, or None
        if there is nothing to filter: only a Data Store source provides a filterable
        database resource, and the database must have scenarios/alternatives to choose from."""
        if data.get("items", {}).get(connection["from"][0], {}).get("type") != "Data Store":
            return None
        engine_connection = HeadlessConnection.from_dict(connection)
        if engine_connection.is_filter_type_enabled("scenario_filter"):
            filter_type = "scenario"
        elif engine_connection.is_filter_type_enabled("alternative_filter"):
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

    def _local_data_path(self) -> Path:
        """Path to this project's local_data.json, which holds per-user data such as
        connections' scenario/alternative filter selections, kept out of the shared project.json."""
        return self._base_dir() / PROJECT_CONFIG_DIR_NAME / PROJECT_LOCAL_DATA_DIR_NAME / PROJECT_LOCAL_DATA_FILENAME

    def _save_local_data(self, local_data: dict) -> None:
        local_data_path = self._local_data_path()
        local_data_path.parent.mkdir(parents=True, exist_ok=True)
        with local_data_path.open("w", encoding="utf-8") as output_file:
            json.dump(local_data, output_file, indent=4)

    def _connection_filter_names(self, data: dict, connection: dict, filter_type: str) -> list[str]:
        """Returns available scenario/alternative names for connection's filter_type, read live from
        the Data Store the connection leaves. Falls back to project.json's flat "scenarios"/"alternatives"
        list (used by the bundled demo project, which has no real database) if the database can't be opened."""
        source = data.get("items", {}).get(connection["from"][0], {})
        db_url = _data_store_url(source.get("url") or {}, str(self._base_dir()))
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

    def _connection_filter_items(self, data: dict, connection: dict, filter_type: str) -> list[dict]:
        """Returns [{"name", "enabled"}, ...] for filter_type on connection: names read live from the
        connected database, online state from the connection's "known_filters", defaulting to its
        "auto_online" setting for names with no stored override. data must include the local data."""
        names = self._connection_filter_names(data, connection, filter_type)
        settings = FilterSettings.from_dict(connection.get("filter_settings", {}))
        online = settings.known_filters.get(database_label(connection["from"][0]), {}).get(f"{filter_type}_filter", {})
        return [{"name": name, "enabled": online.get(name, settings.auto_online)} for name in names]

    @Slot(str, str, result=str)
    def get_connection_filters(self, from_name: str, to_name: str) -> str:
        """Returns the scenario/alternative filter checklist for the link between from_name and to_name,
        with item names read live from the connected database. Returns {} if there's no such connection
        or it has no filters enabled."""
        data = self._load_merged()
        connection = self._find_filter_connection(data, from_name, to_name)
        if connection is None:
            return json.dumps({})
        filter_type = self._connection_filter_type(data, connection)
        if filter_type is None:
            return json.dumps({})
        items = self._connection_filter_items(data, connection, filter_type)
        required = bool(HeadlessConnection.from_dict(connection).require_filter_online(f"{filter_type}_filter"))
        return json.dumps({"filter_type": filter_type, "required": required, "items": items})

    @Slot(str, str, str, str, bool, result=bool)
    def set_connection_filter_enabled(
        self, from_name: str, to_name: str, filter_type: str, item_name: str, enabled: bool
    ) -> bool:
        """Stores whether item_name is online for filter_type ("scenario"/"alternative") on the connection
        between from_name and to_name, in local_data.json's "known_filters" -- the same place and schema
        spine_engine reads when actually running the project. Returns whether such a connection exists."""
        connection = self._find_filter_connection(self._load_merged(), from_name, to_name)
        if connection is None:
            return False
        engine_connection = HeadlessConnection.from_dict(connection)
        engine_connection.set_filter_enabled(
            database_label(engine_connection.source), f"{filter_type}_filter", item_name, enabled
        )
        local_entries = gather_leaf_data(
            engine_connection.to_dict(), HeadlessConnection.connection_dict_local_entries()
        )
        local_data = load_local_project_dict(self._base_dir())
        local_connections = local_data.setdefault("project", {}).setdefault("connections", {})
        local_connections.setdefault(engine_connection.source, {})[engine_connection.destination] = local_entries
        self._save_local_data(local_data)
        return True

    def _base_dir(self) -> Path:
        return self._project_dir

    def _user_positions_file(self) -> Path:
        return self._project_dir / PROJECT_CONFIG_DIR_NAME / _USER_POSITIONS_FILENAME

    def _read_user_layouts(self) -> dict[str, dict]:
        """Returns the saved card positions per chain key ("" is the whole workflow)."""
        try:
            data = json.loads(self._user_positions_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        # files from before chains hold the positions of the whole workflow directly
        return data["layouts"] if "layouts" in data else {"": data}

    def _write_user_layouts(self, layouts: dict[str, dict]) -> None:
        if layouts:
            self._user_positions_file().write_text(json.dumps({"layouts": layouts}), encoding="utf-8")
        else:
            self._user_positions_file().unlink(missing_ok=True)

    @Slot(str, result=str)
    def get_user_positions(self, chain_key: str) -> str:
        """Returns the saved User Mode card positions of a chain as JSON of display name -> {x, y}."""
        return json.dumps(self._read_user_layouts().get(chain_key, {}))

    @Slot(str, str)
    def set_user_positions(self, chain_key: str, positions: str) -> None:
        if self._config_file.exists():
            layouts = self._read_user_layouts()
            layouts[chain_key] = json.loads(positions)
            self._write_user_layouts(layouts)

    @Slot(str)
    def reset_user_positions(self, chain_key: str) -> None:
        layouts = self._read_user_layouts()
        if layouts.pop(chain_key, None) is not None:
            self._write_user_layouts(layouts)

    @property
    def project_dir(self) -> str:
        """Directory of the project currently open, or "" if none."""
        return str(self._project_dir) if self._config_file.exists() else ""

    @Slot(result=bool)
    def has_setup_script(self) -> bool:
        """Returns whether the open project bundles a dependency/setup script (e.g. FlexTool's update_flextool.py)."""
        return find_project_setup_script(str(self._base_dir())) is not None

    def _setup_script_digest(self, project_dir: str) -> str:
        script_name = find_project_setup_script(project_dir)
        return hashlib.sha256(Path(project_dir, script_name).read_bytes()).hexdigest() if script_name else ""

    @Slot(result=bool)
    def is_project_setup_done(self) -> bool:
        """Returns whether the current version of the setup script has already completed successfully."""
        project_dir = str(self._base_dir())
        return (
            QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).value(f"appSettings/projectSetupDigest/{project_dir}")
            == self._setup_script_digest(project_dir)
        )

    @Slot(result=bool)
    def is_tour_seen(self) -> bool:
        """Returns whether the first-run tour has been finished or skipped."""
        settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
        return settings.value(_TOUR_SEEN_KEY, defaultValue=False, type=bool)

    @Slot()
    def mark_tour_seen(self) -> None:
        QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).setValue(_TOUR_SEEN_KEY, True)

    @Slot()
    def install_project_dependencies(self) -> None:
        """Editable-installs the project directory if it is installable, then runs its setup script."""
        project_dir = str(self._base_dir())
        self._setup_last_error = ""
        self.setupRunningChanged.emit(True)
        if not is_installable_project(project_dir):
            self._handle_install_finished(0, project_dir)
            return
        python = resolve_python_interpreter(QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION))
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
            self.setupRunningChanged.emit(False)
            self._setup_logger.msg_error.emit("Installing dependencies failed, setup script was not run")
            return
        python = resolve_python_interpreter(QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION))
        script_name = find_project_setup_script(project_dir)
        script_path = os.path.join(project_dir, script_name)
        self._setup_manager = QProcessExecutionManager(
            self._setup_logger, python, [script_path, "--skip-git"], semisilent=True
        )
        self._setup_manager.execution_finished.connect(
            lambda exit_code: self._handle_setup_finished(exit_code, project_dir)
        )
        self._setup_logger.msg.emit(f"Running {script_name}...")
        self._setup_manager.start_execution(workdir=project_dir)

    def _report_setup(self, text: str, status: str) -> None:
        """Shows text in the banner and appends it to the Runs log."""
        self.setupStatusChanged.emit(text, status)
        self.executionLogAppended.emit(text, "stderr" if status == "error" else "stdout")

    def _show_setup_output(self, text: str) -> None:
        self.executionLogAppended.emit(text, "stdout")
        lines = text.strip().splitlines()
        if lines:
            self.setupStatusChanged.emit(lines[-1], "info")

    def _remember_setup_error(self, text: str) -> None:
        self.executionLogAppended.emit(text, "stderr")
        lines = text.strip().splitlines()
        if lines:
            self._setup_last_error = lines[-1]

    def _handle_setup_finished(self, exit_code: int, project_dir: str) -> None:
        """Reports the outcome of the project setup script."""
        self._setup_manager = None
        self.setupRunningChanged.emit(False)
        if exit_code == 0:
            # stored under the shared QSettings key, so setup is not offered again for this project
            QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).setValue(
                f"appSettings/projectSetupDigest/{project_dir}", self._setup_script_digest(project_dir)
            )
            QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION).setValue(
                f"appSettings/projectSetupDone/{project_dir}", True
            )
            self._setup_logger.msg_success.emit("Installing dependencies succeeded")
        else:
            self._setup_logger.msg_error.emit(
                f"Installing dependencies failed: {self._setup_last_error or 'see the Runs log'}"
            )

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
        """Returns the items the engine goes through for selected: those connected to a selected item."""
        connections = [HeadlessConnection.from_dict(d) for d in data.get("project", {}).get("connections", [])]
        included = {
            name
            for connection in connections_to_selected_items(connections, selected)
            for name in (connection.source, connection.destination)
        }
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

    @Slot(list, str)
    def run_workflow(self, selected_names: list, chain_key: str = "") -> None:
        """Runs the project (or, if selected_names is non-empty, just those items/stacks) via the
        existing headless CLI, so execution reuses the real engine instead of reimplementing it here.
        An empty selected_names means "run project": defaults to every item visible in User Mode,
        excluding anything hidden there, limited to the chain chain_key if it is given."""
        if self._run_manager is not None:
            self.runStatusChanged.emit("A run is already in progress", "error")
            return
        data = self._load()
        if not selected_names:
            selected_names = self._visible_display_names(data, chain_key)
        real_names = sorted(
            {name for display_name in selected_names for name in self._stack_members(data, display_name)}
        )
        if not self._prepare_databases_for_run(data, set(real_names), chain_key):
            return
        project_dir = str(self._base_dir())
        args = [project_dir, "--execute-only"]
        if real_names:
            args += ["--select", *real_names]
        python = resolve_python_interpreter(QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION))
        self._display_members = {
            name: self._stack_members(data, name) for name in self._visible_display_names(data, chain_key)
        }
        self._member_states = {name: "waiting" for name in self._included_items(set(real_names), data)}
        self._display_states = {}
        os.environ[REPORT_PROGRESS_ENV_VAR] = "1"
        os.environ["PYTHONUNBUFFERED"] = "1"
        # piped output defaults to the Windows code page, which cannot encode e.g. the check marks tools print
        os.environ["PYTHONIOENCODING"] = "utf-8"
        plots_dir = self._plots_dir()
        shutil.rmtree(plots_dir, ignore_errors=True)
        plots_dir.mkdir(parents=True, exist_ok=True)
        os.environ[PLOTS_DIR_ENV_VAR] = str(plots_dir)
        self._saved_pythonpath = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = os.pathsep.join(
            [str(Path(__file__).parent / "plot_capture")] + ([self._saved_pythonpath] if self._saved_pythonpath else [])
        )
        self._run_started = time.time()
        self._write_latest_run(chain_key, data)
        self._run_info = self._start_run_info(data, set(real_names), chain_key)
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
        os.environ.pop("PYTHONIOENCODING", None)
        if self._saved_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = self._saved_pythonpath
        self._written_images = self._find_written_images()
        self._record_run_results(exit_code)
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
        return self._base_dir() / PROJECT_CONFIG_DIR_NAME / "user_mode_plots"

    def _find_written_images(self) -> list[Path]:
        """Returns image files in the project that were written since the run started."""
        found = []
        for root, dirs, files in os.walk(self._base_dir()):
            dirs[:] = [
                d for d in dirs if d not in _IMAGE_SCAN_SKIPPED_DIRS and d not in ("user_mode_plots", "user_mode_saved_plots")
            ]
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

    def _saved_plots(self) -> SavedPlots:
        # outside the plots folder, which is emptied at the start of every run
        return SavedPlots(self._project_dir / PROJECT_CONFIG_DIR_NAME / "user_mode_saved_plots")

    def _write_latest_run(self, chain_key: str, data: dict) -> None:
        run = {"chain": chain_key, "chain_name": self._chain_name(data, chain_key), "started": self._run_started}
        (self._plots_dir() / "latest_run.json").write_text(json.dumps(run), encoding="utf-8")

    def _latest_run(self) -> dict:
        try:
            return json.loads((self._plots_dir() / "latest_run.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"chain": "", "chain_name": "All items", "started": 0.0}

    @Slot(str, result=bool)
    def save_plot(self, url: str) -> bool:
        """Keeps a plot of the latest run in the project, tagged with the chain and run it came from."""
        source = Path(QUrl(url).toLocalFile())
        if not source.is_file():
            return False
        run = self._latest_run()
        self._saved_plots().save(source, run["chain"], run["chain_name"], run["started"])
        return True

    @Slot(str, result=bool)
    def save_plot_as(self, url: str) -> bool:
        """Copies a plot to a file the user chooses."""
        source = Path(QUrl(url).toLocalFile())
        host = self.parent() if isinstance(self.parent(), QWidget) else None
        target, _ = QFileDialog.getSaveFileName(
            host, "Save plot", str(Path.home() / source.name), "PNG image (*.png);;All files (*)"
        )
        if not target:
            return False
        shutil.copy2(source, target)
        return True

    @Slot(str, str, str, result=str)
    def get_saved_plots(self, chain_key: str, run: str, query: str) -> str:
        """Returns the saved plots as JSON; "*" as chain_key or run means any."""
        entries = self._saved_plots().entries(
            None if chain_key == "*" else chain_key, None if run == "*" else float(run), query
        )
        return json.dumps([{**entry, "url": QUrl.fromLocalFile(entry["path"]).toString()} for entry in entries])

    @Slot(result=str)
    def get_saved_plot_filters(self) -> str:
        return json.dumps(self._saved_plots().filters())

    @Slot(str)
    def delete_saved_plot(self, file_name: str) -> None:
        self._saved_plots().delete(file_name)

    def _run_results_file(self) -> Path:
        return self._project_dir / PROJECT_CONFIG_DIR_NAME / _RUN_RESULTS_FILENAME

    def _read_run_records(self) -> dict[str, dict]:
        """Returns what the latest run of each chain produced, keyed by chain key (\"\" is the whole workflow)."""
        try:
            records = json.loads(self._run_results_file().read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return records if isinstance(records, dict) else {}

    def _result_stores(self, data: dict, real_names: set[str]) -> dict[str, dict]:
        """Returns the Data Stores the run writes to, only the result databases if it writes to any."""
        written = self._written_stores(data, real_names, include_purging=True)
        results = set(data.get("project", {}).get("result_data_stores", []))
        return {name: item for name, item in written.items() if name in results} or written

    def _start_run_info(self, data: dict, real_names: set[str], chain_key: str) -> dict:
        """Notes the state of the result databases before a run, to tell afterwards what the run changed."""
        from .run_results import commit_mark

        marks = {}
        for name, item in self._result_stores(data, real_names).items():
            url = _data_store_url(item.get("url") or {}, str(self._base_dir()))
            if url:
                marks[name] = (url, commit_mark(url))
        return {
            "chain": chain_key,
            "chain_name": self._chain_name(data, chain_key),
            "real_names": real_names,
            "marks": marks,
        }

    def _record_run_results(self, exit_code: int) -> None:
        """Saves the scenarios and exported files the finished run produced."""
        from .run_results import changed_scenarios, files_written_since

        info = self._run_info
        if not info:
            return
        items = self._load().get("items", {})
        files = []
        for name in sorted(info["real_names"]):
            if items.get(name, {}).get("type") == "Exporter":
                item_dir = self._base_dir() / PROJECT_CONFIG_DIR_NAME / "items" / shorten(name)
                files += files_written_since(item_dir, self._run_started)
        records = self._read_run_records()
        records[info["chain"]] = {
            "chain_name": info["chain_name"],
            "started": self._run_started,
            "finished": time.time(),
            "exit_code": exit_code,
            "stores": {name: changed_scenarios(url, mark) for name, (url, mark) in info["marks"].items()},
            "files": files,
        }
        self._run_results_file().write_text(json.dumps(records), encoding="utf-8")
        self._run_info = {}
        self.runResultsChanged.emit()

    @Slot(str, result=str)
    def get_run_results(self, chain_key: str) -> str:
        """Returns what the latest run of a chain produced as JSON, or "{}" if it has not run."""
        record = self._read_run_records().get(chain_key)
        if record is None:
            return "{}"
        started = datetime.fromtimestamp(record["started"]).strftime("%d.%m.%Y %H:%M")
        return json.dumps({**record, "started_label": started})

    @Slot(str, result=bool)
    def open_run_results(self, chain_key: str) -> bool:
        """Opens the result databases of a chain's latest run, with the scenarios of the run selected."""
        record = self._read_run_records().get(chain_key)
        if not record or not record["stores"]:
            return False
        items = self._load().get("items", {})
        for name, scenarios in record["stores"].items():
            if not self._open_database_in("run", name):
                continue
            url = _data_store_url(items.get(name, {}).get("url") or {}, str(self._base_dir()))
            for tab in self._open_editor_tabs(url, "run"):
                self._select_scenarios(tab, scenarios)
        return True

    def _select_scenarios(self, tab, names: list[str], attempts: int = 25) -> None:
        """Selects the scenarios called names in the scenario tree of an editor tab; the tree fills in
        gradually, so this waits for them to appear."""
        try:
            view = tab.ui.scenario_tree_view
            model = view.model()
            found = []
            for row in range(model.rowCount(QModelIndex())):
                database_index = model.index(row, 0, QModelIndex())
                found += [
                    model.index(child, 0, database_index)
                    for child in range(model.rowCount(database_index))
                    if model.index(child, 0, database_index).data() in names
                ]
            if len(found) < len(names) and attempts > 0:
                QTimer.singleShot(400, lambda: self._select_scenarios(tab, names, attempts - 1))
                return
            selection_model = view.selectionModel()
            selection_model.clearSelection()
            for index in found:
                selection_model.select(index, QItemSelectionModel.SelectionFlag.Select)
        except RuntimeError:
            return  # the tab was closed meanwhile

    @Slot(str, result=bool)
    def open_file(self, path: str) -> bool:
        return open_url(Path(path).as_uri())

    @Slot(str, result=bool)
    def open_folder(self, path: str) -> bool:
        return open_url(Path(path).parent.as_uri())

    @Slot(result=bool)
    def is_execution_running(self) -> bool:
        """Returns whether a workflow run is currently in progress."""
        return self._run_manager is not None

    @Slot(result=str)
    def get_project_name(self) -> str:
        """Returns the current project's name, or "" when none is open."""
        if (self._project_dir / PROJECT_CONFIG_DIR_NAME).is_dir():
            return self._project_dir.name
        return ""

    def _connection_filter_states(self, data: dict, chain_key: str = "") -> list[dict]:
        """Returns {"from", "to", "filter_type", "filter_satisfied", "filter_state"} for
        every visible, de-duplicated (stack-collapsed) connection. filter_state is None when the connection
        has no filter, else "ok"/"disabled_ok"/"error" -- an unsatisfied filter is only an "error" if no
        sibling line into the same target is satisfied either (that sibling still supplies the target)."""
        project = data.get("project", {})
        resolve = self._stack_resolver(data, chain_key)
        visible = self._visible_display_names(data, chain_key)

        edges = [
            (resolve(connection["from"][0]), resolve(connection["to"][0]), connection)
            for connection in project.get("connections", [])
        ]
        outgoing: dict[str, list[tuple[str, dict]]] = {}
        for from_name, to_name, connection in edges:
            if from_name != to_name:
                outgoing.setdefault(from_name, []).append((to_name, connection))

        connections = []
        seen = set()
        for from_name, to_name, connection in edges:
            if from_name == to_name or from_name not in visible:
                continue  # internal to a stack or not shown in User Mode
            # links through hidden items are bridged to the next visible item
            targets = []
            pending = [(to_name, connection, True)]
            passed = set()
            while pending:
                name, last, direct = pending.pop()
                if name in visible:
                    targets.append((name, last, direct))
                elif name not in passed:
                    passed.add(name)
                    pending.extend((next_name, next_edge, False) for next_name, next_edge in outgoing.get(name, []))
            for target_name, last_connection, direct in targets:
                if target_name != from_name:
                    self._append_connection(
                        data, connections, seen, from_name, target_name, connection, last_connection, direct
                    )
        return self._with_filter_states(connections)

    def _append_connection(
        self,
        data: dict,
        connections: list[dict],
        seen: set,
        from_name: str,
        to_name: str,
        first: dict,
        last: dict,
        direct: bool,
    ) -> None:
        """Appends the link from_name -> to_name unless present; bridged links carry no filter."""
        key = (from_name, to_name)
        if key in seen:
            return
        seen.add(key)
        carrier = self._filter_connection(data, first) if direct else None
        filter_type = self._connection_filter_type(data, carrier) if carrier is not None else None
        filter_satisfied = True
        if filter_type is not None:
            # zero enabled items means nothing actually passes through the link, regardless of
            # whether "require filter online" is set -- that flag only affects wording, not reality
            filter_items = self._connection_filter_items(data, carrier, filter_type)
            filter_satisfied = any(item["enabled"] for item in filter_items)
        connections.append(
            {
                "from": from_name,
                "to": to_name,
                "from_anchor": first["from"][1] if len(first["from"]) > 1 else "right",
                "to_anchor": last["to"][1] if len(last["to"]) > 1 else "left",
                "filter_type": filter_type,
                "filter_satisfied": filter_satisfied,
            }
        )

    @staticmethod
    def _with_filter_states(connections: list[dict]) -> list[dict]:
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

    @Slot(str, result=str)
    def get_workflow(self, chain_key: str = "") -> str:
        """Returns items/connections as JSON, collapsing any project.json "stacks" into a single node each.
        A chain limits them to its entries; links through the items left out are bridged."""
        data = self._load_merged()
        project = data.get("project", {})
        raw_items = data.get("items", {})
        stacks = project.get("stacks", {})
        stacked_names = {member for stack in stacks.values() for member in stack.get("items", [])}
        resolve = self._stack_resolver(data, chain_key)

        items = []
        for stack_key, stack in stacks.items():
            members = [name for name in stack.get("items", []) if name in raw_items]
            if not members:
                continue
            x, y = self._stack_position(data, members)
            display_name = stack.get("name", stack_key)
            items.append({"name": display_name, "type": "Stack", "x": x, "y": y, "subtitle": "Stack"})
        for name, item in raw_items.items():
            if resolve(name) != name:
                continue
            item_type = item.get("type", "")
            items.append(
                {
                    "name": name,
                    "type": item_type,
                    "x": item.get("x", 0.0),
                    "y": item.get("y", 0.0),
                    "subtitle": item_type,
                }
            )

        # items/stacks left out stay in project.json untouched, just hidden from this simplified view
        visible = self._visible_display_names(data, chain_key)
        items = [item for item in items if item["name"] in visible]
        connections = self._connection_filter_states(data, chain_key)

        # stacks, hidden items and chains leave gaps that the layout may close
        hidden = set(project.get("hidden_items", []))
        compact_rows = bool(stacked_names or hidden & raw_items.keys() or self._chain(data, chain_key))
        return json.dumps({"items": items, "connections": connections, "compact_rows": compact_rows})

    @Slot(str, result=str)
    def get_chain_members(self, chain_key: str) -> str:
        """Returns the names of the cards of the whole workflow that the chain(s) of chain_key cover, as JSON."""
        data = self._load_merged()
        stack_of = self._stack_resolver(data)
        return json.dumps(sorted({stack_of(name) for name in self._visible_display_names(data, chain_key)}))

    @Slot(result=str)
    def get_chains(self) -> str:
        """Returns the User Mode chains as JSON: {"default": key or null, "chains": [{"key", "name"}]}."""
        chains = self._load().get("project", {}).get("chains", {})
        default = chains.get("default")
        items = chains.get("items", {})
        return json.dumps(
            {
                "default": default if default in items else None,
                "chains": [{"key": key, "name": chain.get("name", key)} for key, chain in items.items()],
            }
        )

    @Slot(result=str)
    def get_instructions(self) -> str:
        """Returns the instructions of the items shown in User Mode as a JSON list of name/text, in workflow order."""
        data = self._load_merged()
        instructions = data.get("project", {}).get("instructions", {}).get("items", {})
        resolve = self._stack_resolver(data)
        shown = self._visible_display_names(data)
        names = dict.fromkeys(resolve(name) for name in data.get("items", {}))
        return json.dumps(
            [{"name": name, "text": instructions[name]} for name in names if name in shown and name in instructions]
        )

    def _resolve_item_directory(self, name: str, item: dict) -> Path | None:
        """Prefers the item's real (executed) data directory, then the folder holding its first file
        reference, then falls back to the project root; returns None if nothing usable exists."""
        project_dir = self._base_dir()
        data_dir = Path(project_dir, PROJECT_CONFIG_DIR_NAME, "items", shorten(name))
        if data_dir.is_dir():
            return data_dir
        for reference in item.get("file_references") or []:
            reference_path = Path(deserialize_path(reference, str(project_dir)))
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

    @Slot(str, result=str)
    def get_data_stores(self, view: str) -> str:
        """Returns the names of the Data Store items shown in User Mode as a JSON list.

        With view "results" only the Data Stores marked as result databases are included.
        """
        data = self._load()
        resolve = self._stack_resolver(data)
        hidden = set(data.get("project", {}).get("hidden_items", []))
        results = set(data.get("project", {}).get("result_data_stores", []))
        names = [
            name
            for name, item in data.get("items", {}).items()
            if item.get("type") == "Data Store"
            and resolve(name) not in hidden
            and (view != "results" or name in results)
        ]
        return json.dumps(names)

    def _open_database_in(self, view: str, display_name: str) -> bool:
        data = self._load()
        found = self._stack_member_of_type(data, display_name, "Data Store")
        if found is None:
            return False
        _name, item = found
        url = _data_store_url(item.get("url") or {}, str(self._base_dir()))
        if not url:
            return False
        self._ensure_db_editor(view)
        editor = self._db_editors[view]
        normcased_url = normcase_database_url_path(url)
        for index in range(editor.tab_widget.count()):
            tab = editor.tab_widget.widget(index)
            if tab.db_urls == [normcased_url]:
                editor.set_current_tab(tab)
                return True
        # not open_url_in_new_tab(): it would switch to the same database open in the other view's editor
        editor.add_new_tab([url])
        return True

    @Slot(str, result=bool)
    def open_database(self, display_name: str) -> bool:
        """Opens the Data Store item called display_name (or the first Data Store inside the stack it names)
        in the Data view's classic Qt DB Editor, reusing the same tab if that database is already open there."""
        if not self._open_database_in("data", display_name):
            return False
        self.dataViewRequested.emit()
        return True

    @Slot()
    def open_result_databases(self) -> None:
        """Opens every Data Store marked as a result database in the Results view's DB Editor."""
        for name in json.loads(self.get_data_stores("results")):
            self._open_database_in("results", name)

    @Slot(str, result=str)
    def open_project(self, folder_url: str) -> str:
        """Switches to the project in folder_url or up to two levels below it and registers it as a recent project.

        Returns an empty string and reports the reason through setupStatusChanged if no project can be opened.
        """
        chosen_path = Path(QUrl(folder_url).toLocalFile() or folder_url)
        local_path = _find_project_folder(chosen_path)
        if local_path is None:
            self.setupStatusChanged.emit(
                f"{chosen_path} is not a Spine Toolbox project: no {PROJECT_CONFIG_DIR_NAME} folder found in it or in the two folder levels below it",
                "error",
            )
            return ""
        for view in list(self._db_editors):
            if not self._db_editors[view].close():
                self.setupStatusChanged.emit("Close the open database editors before switching project", "error")
                return ""
            del self._db_editors[view]
        self._close_sessions()
        self._project_dir = local_path
        self._config_file = local_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        update_recent_projects(
            QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION), local_path.name, str(local_path)
        )
        return local_path.name

    @Slot()
    def open_dev_mode(self) -> None:
        """Requests switching to the classic Qt UI; the embedder decides how (see devModeRequested)."""
        self.devModeRequested.emit()

    def _ensure_db_editor(self, view: str) -> None:
        """Creates the DB editor of view ("data" or "results"), with no tabs open yet, if it doesn't exist."""
        if view in self._db_editors:
            return
        # imported lazily: pulls in the full widget/spinedb_api stack, only needed once the user asks for it
        from ...spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
        from ...spine_db_manager import SpineDBManager

        settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
        db_mngr = SpineDBManager(settings, None)
        editor = MultiSpineDBEditor(db_mngr, register=False)
        host = self.parent()
        if isinstance(host, QWidget):
            editor.setParent(host, Qt.WindowType.Widget)
        editor.destroyed.connect(lambda _=None: self._forget_db_editor(view))
        self._db_editors[view] = editor
        self._place_db_editor(view)

    @Slot(str, float, float, float, float, bool)
    def set_data_area(self, view: str, x: float, y: float, width: float, height: float, visible: bool) -> None:
        """Sets where view's DB editor ("data" or "results") is on screen."""
        self._data_areas[view] = (QRect(round(x), round(y), round(width), round(height)), visible)
        self._place_db_editor(view)

    def _place_db_editor(self, view: str) -> None:
        editor = self._db_editors.get(view)
        if editor is None:
            return
        area, visible = self._data_areas.get(view, (QRect(), False))
        editor.setGeometry(area)
        editor.setVisible(visible)

    def _forget_db_editor(self, view: str) -> None:
        self._db_editors.pop(view, None)

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

    def _open_editor_tabs(self, url: str, view: str | None = None) -> list:
        normcased_url = normcase_database_url_path(url)
        editors = [self._db_editors[view]] if view in self._db_editors else self._db_editors.values()
        return [
            editor.tab_widget.widget(index)
            for editor in editors
            for index in range(editor.tab_widget.count())
            if editor.tab_widget.widget(index).db_urls == [normcased_url]
        ]

    def _purge_now(self, url: str, settings: dict[str, bool], label: str) -> bool:
        """Purges the database at url and refreshes the Data view tabs showing it; reports failures to the user."""
        # imported lazily, same reason as _ensure_db_editor
        from spinedb_api.purge import purge_url

        host = self.parent() if isinstance(self.parent(), QWidget) else None
        tabs = self._open_editor_tabs(url)
        if any(tab.db_mngr.dirty(*tab.db_maps) for tab in tabs):
            QMessageBox.warning(
                host, "Uncommitted changes", "Commit or roll back the changes open in Data view before purging."
            )
            return False
        errors: list[str] = []
        logger = QtLogger()
        logger.msg_error.connect(errors.append)
        logger.msg_warning.connect(errors.append)
        purged = purge_url(url, settings, logger)
        for tab in tabs:
            tab.refresh_session()
        if not purged:
            QMessageBox.warning(host, "Purge failed", "<br>".join(errors) or f"Purging {label} failed.")
        else:
            self.runStatusChanged.emit(f"Purged {label}", "success")
        return purged

    def _purge_database(self, url: str, label: str) -> bool:
        """Lets the user choose what to purge from the database at url, then purges it.
        Returns whether anything was purged."""
        from ...widgets.custom_qwidgets import PurgeSettingsDialog
        from ...widgets.select_database_items import SelectDatabaseItems

        host = self.parent() if isinstance(self.parent(), QWidget) else None
        dialog = PurgeSettingsDialog({item: True for item in SelectDatabaseItems.data_item_types()}, parent=host)
        dialog.setWindowTitle(f"Purge {label}")
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        chosen: dict[str, bool] = {}
        dialog.accepted.connect(lambda: chosen.update(dialog.get_checked_states()))
        dialog.exec()
        if not any(chosen.values()):
            return False
        answer = QMessageBox.question(
            host,
            "Purge database",
            f"Remove the selected items from <b>{label}</b>? This cannot be undone.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        purged = self._purge_now(url, chosen, label)
        if purged and any(chosen.get(item) for item in SelectDatabaseItems.data_item_types()):
            self._forget_store_chain(label)
        return purged

    def _read_store_chains(self) -> dict[str, str]:
        """Returns Data Store name -> key of the chain whose run last wrote to it ("" is the whole workflow)."""
        try:
            records = json.loads(
                (self._project_dir / PROJECT_CONFIG_DIR_NAME / _STORE_CHAINS_FILENAME).read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return {}
        return records if isinstance(records, dict) else {}

    def _write_store_chains(self, records: dict[str, str]) -> None:
        if self._config_file.exists():
            path = self._project_dir / PROJECT_CONFIG_DIR_NAME / _STORE_CHAINS_FILENAME
            path.write_text(json.dumps(records), encoding="utf-8")
            self.storeWarningsChanged.emit()

    def _forget_store_chain(self, store_name: str) -> None:
        records = self._read_store_chains()
        if records.pop(store_name, None) is not None:
            self._write_store_chains(records)

    @staticmethod
    def _chain_name(data: dict, chain_key: str) -> str:
        if not chain_key:
            return "All items"
        chains = data.get("project", {}).get("chains", {}).get("items", {})
        return " + ".join(chains.get(key, {}).get("name", key) for key in chain_key.split(CHAIN_KEY_SEPARATOR))

    @staticmethod
    def _written_stores(data: dict, real_names: set[str], include_purging: bool = False) -> dict[str, dict]:
        """Returns the Data Stores items in real_names write to, leaving out those a connection purges itself
        unless include_purging is set."""
        items = data.get("items", {})
        stores = {}
        for connection in data.get("project", {}).get("connections", []):
            source, destination = connection["from"][0], connection["to"][0]
            if source not in real_names or items.get(destination, {}).get("type") != "Data Store":
                continue
            if include_purging or not (connection.get("options") or {}).get("purge_before_writing"):
                stores[destination] = items[destination]
        return stores

    def _prepare_databases_for_run(self, data: dict, real_names: set[str], chain_key: str) -> bool:
        """Warns about databases the run writes to that hold the data of another chain and purges them on request.
        Records the chain as their writer. Returns False if the user cancelled the run."""
        from ...widgets.select_database_items import SelectDatabaseItems

        stores = self._written_stores(data, real_names)
        records = self._read_store_chains()
        stale = {name: records[name] for name in stores if records.get(name, chain_key) != chain_key}
        if stale:
            host = self.parent() if isinstance(self.parent(), QWidget) else None
            listing = "<br>".join(
                f"<b>{name}</b>: data from chain <b>{self._chain_name(data, key)}</b>" for name, key in stale.items()
            )
            box = QMessageBox(
                QMessageBox.Icon.Warning,
                "Database holds data from another chain",
                f"{listing}<br><br>Chain <b>{self._chain_name(data, chain_key)}</b> writes to the same database, "
                "so the old data stays in it and may not match this chain's inputs. "
                "Purge the value and scenario items first?",
                parent=host,
            )
            purge_button = box.addButton("Purge and run", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("Run without purging", QMessageBox.ButtonRole.DestructiveRole)
            cancel_button = box.addButton(QMessageBox.StandardButton.Cancel)
            box.exec()
            clicked = box.clickedButton()
            if clicked is None or clicked is cancel_button:
                return False
            if clicked is purge_button:
                settings = {
                    item: True
                    for item in SelectDatabaseItems.data_item_types() + SelectDatabaseItems.scenario_item_types()
                }
                for name in stale:
                    url = _data_store_url(stores[name].get("url") or {}, str(self._base_dir()))
                    if url and not self._purge_now(url, settings, name):
                        return False
        records.update({name: chain_key for name in stores})
        self._write_store_chains(records)
        return True

    @Slot(str, result=str)
    def get_store_warnings(self, chain_key: str) -> str:
        """Returns the Data Stores shown in a chain that were last written by another chain as JSON of
        store name -> that chain's name."""
        data = self._load()
        visible = self._visible_display_names(data, chain_key)
        purged_on_write = {
            connection["to"][0]
            for connection in data.get("project", {}).get("connections", [])
            if (connection.get("options") or {}).get("purge_before_writing")
        }
        return json.dumps(
            {
                name: self._chain_name(data, key)
                for name, key in self._read_store_chains().items()
                if key != chain_key and name in visible and name not in purged_on_write
            }
        )

    @Slot(str, result=bool)
    def purge_data_store(self, display_name: str) -> bool:
        """Purges the Data Store item called display_name (or the first one inside the stack it names)."""
        found = self._stack_member_of_type(self._load(), display_name, "Data Store")
        if found is None:
            return False
        name, item = found
        url = _data_store_url(item.get("url") or {}, str(self._base_dir()))
        return bool(url) and self._purge_database(url, name)

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
        return deserialize_path(references[0], str(self._project_dir))

    @Slot(str, result=str)
    def set_input_reference(self, file_url: str) -> str:
        """Stores file_url as the project's Data Connection file reference and returns its display name."""
        local_path = QUrl(file_url).toLocalFile() or file_url
        data = self._load_raw()
        name, item = self._find_data_connection(data)
        if item is None:
            name = _INPUT_DATA_CONNECTION_NAME
            item = {"type": "Data Connection", "description": "", "x": 0.0, "y": 0.0, "db_references": []}
            data["items"][name] = item
        item["file_references"] = [serialize_path(local_path, str(self._project_dir))]
        self._save(data)
        return os.path.basename(local_path)
