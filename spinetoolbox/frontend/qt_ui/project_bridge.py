"""Reads and writes the same project.json Data Connection file references as the classic Qt UI."""
import json
import os
from pathlib import Path
import sys
from PySide6.QtCore import QObject, QSettings, QUrl, Signal, Slot
from ...config import LATEST_PROJECT_VERSION, PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME, PROJECT_SETUP_SCRIPT
from ...execution_managers import QProcessExecutionManager
from ...helpers import open_url
from ...logger import QtLogger

_INPUT_DATA_CONNECTION_NAME = "Input data"

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


def _data_dir(name: str, project_dir: str) -> str:
    """Mirrors spine_engine.project_item.executable_item_base's item data directory convention."""
    return os.path.join(project_dir, PROJECT_CONFIG_DIR_NAME, "items", name.lower().replace(" ", "_"))


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

    def __init__(self, project_dir: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_dir = Path(project_dir)
        self._config_file = self._project_dir / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._db_editor = None
        self._setup_manager: QProcessExecutionManager | None = None
        self._setup_logger = QtLogger()
        self._setup_logger.msg.connect(lambda text: self.setupStatusChanged.emit(text, "info"))
        self._setup_logger.msg_success.connect(lambda text: self.setupStatusChanged.emit(text, "success"))
        self._setup_logger.msg_error.connect(lambda text: self.setupStatusChanged.emit(text, "error"))

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

    def _find_connection(self, data: dict, from_name: str, to_name: str) -> dict | None:
        """Finds the raw project.json connection whose (possibly stacked) endpoints resolve to
        from_name/to_name, as returned by get_workflow."""
        resolve = self._stack_resolver(data)
        for connection in data.get("project", {}).get("connections", []):
            if resolve(connection["from"][0]) == from_name and resolve(connection["to"][0]) == to_name:
                return connection
        return None

    def _connection_filter_type(self, connection: dict) -> str | None:
        """Returns "scenario" or "alternative", whichever filter type is enabled on connection, or None
        if the connection has no filters."""
        enabled_types = connection.get("filter_settings", {}).get("enabled_filter_types", {})
        if enabled_types.get("scenario_filter"):
            return "scenario"
        if enabled_types.get("alternative_filter"):
            return "alternative"
        return None

    def _connection_requires_filter(self, connection: dict, filter_type: str) -> bool:
        return bool(connection.get("options", {}).get(f"require_{filter_type}_filter"))

    def _connection_filter_selection(self, data: dict, from_name: str, to_name: str, filter_type: str) -> dict:
        """Returns the stored online-state overrides (name -> bool) for filter_type on the from_name/to_name
        link, from project.json's "connection_filter_selection"."""
        key = f"{from_name}->{to_name}"
        return data.get("project", {}).get("connection_filter_selection", {}).get(key, {}).get(filter_type, {})

    def _connection_database_url(self, data: dict, connection: dict) -> str | None:
        """Returns the URL of whichever endpoint of connection is a Data Store, or None if neither is."""
        raw_items = data.get("items", {})
        project_dir = str(self._base_dir())
        for raw_name in (connection["from"][0], connection["to"][0]):
            item = raw_items.get(raw_name, {})
            if item.get("type") == "Data Store":
                url = _data_store_url(item.get("url") or {}, project_dir)
                if url:
                    return url
        return None

    def _connection_filter_names(self, data: dict, connection: dict, filter_type: str) -> list[str]:
        """Returns available scenario/alternative names for connection's filter_type, read live from
        whichever endpoint is a Data Store. Falls back to project.json's flat "scenarios"/"alternatives"
        list (used by the bundled demo project, which has no real database) if there's no Data Store
        endpoint or it can't be opened."""
        db_url = self._connection_database_url(data, connection)
        if db_url:
            from spinedb_api import DatabaseMapping  # imported lazily, same reason as get_database_contents

            try:
                with DatabaseMapping(db_url) as db_map:
                    query = db_map.scenario_sq if filter_type == "scenario" else db_map.alternative_sq
                    return [row.name for row in db_map.query(query)]
            except Exception:
                pass
        return data.get("project", {}).get(filter_type + "s", [])

    def _connection_filter_items(
        self, data: dict, connection: dict, from_name: str, to_name: str, filter_type: str
    ) -> list[dict]:
        """Returns [{"name", "enabled"}, ...] for filter_type on the from_name/to_name link: names read
        live from the connected database, online state from "connection_filter_selection" (default True)."""
        names = self._connection_filter_names(data, connection, filter_type)
        selection = self._connection_filter_selection(data, from_name, to_name, filter_type)
        return [{"name": name, "enabled": selection.get(name, True)} for name in names]

    @Slot(str, str, result=str)
    def get_connection_filters(self, from_name: str, to_name: str) -> str:
        """Returns the scenario/alternative filter checklist for the link between from_name and to_name,
        with item names read live from the connected database. Returns {} if there's no such connection
        or it has no filters enabled."""
        data = self._load()
        connection = self._find_connection(data, from_name, to_name)
        if connection is None:
            return json.dumps({})
        filter_type = self._connection_filter_type(connection)
        if filter_type is None:
            return json.dumps({})
        items = self._connection_filter_items(data, connection, from_name, to_name, filter_type)
        required = self._connection_requires_filter(connection, filter_type)
        return json.dumps({"filter_type": filter_type, "required": required, "items": items})

    @Slot(str, str, str, str, bool, result=bool)
    def set_connection_filter_enabled(
        self, from_name: str, to_name: str, filter_type: str, item_name: str, enabled: bool
    ) -> bool:
        """Stores whether item_name is online for filter_type ("scenario"/"alternative") on the connection
        between from_name and to_name, in project.json's "connection_filter_selection". Returns whether
        such a connection exists."""
        data = self._load()
        if self._find_connection(data, from_name, to_name) is None:
            return False
        project = data.setdefault("project", {})
        key = f"{from_name}->{to_name}"
        selection = project.setdefault("connection_filter_selection", {}).setdefault(key, {}).setdefault(
            filter_type, {}
        )
        selection[item_name] = enabled
        self._save(data)
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

    @Slot(result=bool)
    def has_setup_script(self) -> bool:
        """Returns whether the open project bundles a dependency/setup script (e.g. FlexTool's update_flextool.py)."""
        return (self._base_dir() / PROJECT_SETUP_SCRIPT).is_file()

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
        self._setup_manager.execution_finished.connect(self._handle_setup_finished)
        self._setup_logger.msg.emit(f"Running {PROJECT_SETUP_SCRIPT}...")
        self._setup_manager.start_execution(workdir=project_dir)

    def _handle_setup_finished(self, exit_code: int) -> None:
        """Reports the outcome of the project setup script."""
        self._setup_manager = None
        if exit_code == 0:
            self._setup_logger.msg_success.emit("Project setup finished successfully")
        else:
            self._setup_logger.msg_error.emit("Project setup script failed")

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
            x = stack.get("x")
            y = stack.get("y")
            if x is None or y is None:
                x = sum(raw_items[name].get("x", 0.0) for name in members) / len(members)
                y = sum(raw_items[name].get("y", 0.0) for name in members) / len(members)
            display_name = stack.get("name", stack_key)
            items.append({"name": display_name, "type": "Stack", "x": x, "y": y, "subtitle": "Stack"})
        for name, item in raw_items.items():
            if name in item_to_stack:
                continue
            item_type = item.get("type", "")
            items.append(
                {"name": name, "type": item_type, "x": item.get("x", 0.0), "y": item.get("y", 0.0), "subtitle": item_type}
            )

        def resolve(name: str) -> str:
            return item_to_stack.get(name, name)

        connections = []
        seen = set()
        for connection in project.get("connections", []):
            from_name = resolve(connection["from"][0])
            to_name = resolve(connection["to"][0])
            if from_name == to_name:
                continue  # internal to a stack, hidden while collapsed
            key = (from_name, to_name)
            if key in seen:
                continue
            seen.add(key)
            filter_type = self._connection_filter_type(connection)
            filter_required = filter_type is not None and self._connection_requires_filter(connection, filter_type)
            filter_satisfied = True
            if filter_required:
                filter_items = self._connection_filter_items(data, connection, from_name, to_name, filter_type)
                filter_satisfied = any(item["enabled"] for item in filter_items)
            connections.append(
                {
                    "from": from_name,
                    "to": to_name,
                    "filter_type": filter_type,
                    "filter_required": filter_required,
                    "filter_satisfied": filter_satisfied,
                }
            )

        # items/stacks listed here stay in project.json untouched, just hidden from this simplified view
        hidden = set(project.get("hidden_items", []))
        items = [item for item in items if item["name"] not in hidden]
        visible_names = {item["name"] for item in items}
        connections = [c for c in connections if c["from"] in visible_names and c["to"] in visible_names]

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

    @Slot(str, result=bool)
    def open_item_directory(self, display_name: str) -> bool:
        """Opens the data directory of the Data Connection item called display_name, or, if display_name is a
        collapsed stack, of the first Data Connection item inside it. Returns whether a directory was opened."""
        data = self._load()
        raw_items = data.get("items", {})
        stacks = data.get("project", {}).get("stacks", {})

        member_names = stacks.get(display_name, {}).get("items") if display_name not in raw_items else [display_name]
        if member_names is None:
            for stack in stacks.values():
                if stack.get("name") == display_name:
                    member_names = stack.get("items", [])
                    break
        if not member_names:
            return False

        for name in member_names:
            item = raw_items.get(name, {})
            if item.get("type") != "Data Connection":
                continue
            directory = self._resolve_item_directory(name, item)
            if directory is None:
                return False
            return open_url(directory.as_uri())
        return False

    @Slot(str, result=str)
    def open_project(self, folder_url: str) -> str:
        """Switches to the project at folder_url and registers it as a recent project; empty string means invalid."""
        local_path = Path(QUrl(folder_url).toLocalFile() or folder_url)
        if not (local_path / PROJECT_CONFIG_DIR_NAME).is_dir():
            return ""
        self._project_dir = local_path
        self._config_file = local_path / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._add_recent_project(local_path.name, str(local_path))
        return local_path.name

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

    @Slot()
    def open_database_editor(self) -> None:
        """Opens the classic Qt DB Editor (in-process) with the project's Data Store URLs."""
        if self._db_editor is not None:
            self._db_editor.show()
            self._db_editor.raise_()
            self._db_editor.activateWindow()
            return
        # imported lazily: pulls in the full widget/spinedb_api stack, only needed once the user asks for it
        from ...spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
        from ...spine_db_manager import SpineDBManager

        settings = QSettings(_SETTINGS_ORGANIZATION, _SETTINGS_APPLICATION)
        db_mngr = SpineDBManager(settings, None)
        editor = MultiSpineDBEditor(db_mngr)
        editor.add_new_tab(self._database_urls())
        editor.destroyed.connect(self._forget_db_editor)
        editor.show()
        self._db_editor = editor

    def _forget_db_editor(self) -> None:
        self._db_editor = None

    @Slot(result=str)
    def get_databases(self) -> str:
        """Returns [{"name": ..., "url": ...}, ...] for every Data Store in the project."""
        data = self._load()
        project_dir = str(self._base_dir())
        databases = []
        for name, item in data.get("items", {}).items():
            if item.get("type") != "Data Store":
                continue
            url = _data_store_url(item.get("url") or {}, project_dir)
            if url:
                databases.append({"name": name, "url": url})
        return json.dumps(databases)

    @Slot(str, result=str)
    def get_database_contents(self, url: str) -> str:
        """Returns {"entity_classes": [{"name": ..., "entity_count": ...}], "alternatives": [...],
        "scenarios": [...]} read live from the database at url, or {"error": ...} if it couldn't be opened."""
        from spinedb_api import DatabaseMapping  # imported lazily: only needed once the user opens this page

        try:
            with DatabaseMapping(url) as db_map:
                entity_classes = []
                for row in db_map.query(db_map.entity_class_sq):
                    count = db_map.query(db_map.entity_sq).filter_by(class_id=row.id).count()
                    entity_classes.append({"name": row.name, "entity_count": count})
                alternatives = [row.name for row in db_map.query(db_map.alternative_sq)]
                scenarios = [row.name for row in db_map.query(db_map.scenario_sq)]
        except Exception as error:
            return json.dumps({"error": str(error)})
        return json.dumps({"entity_classes": entity_classes, "alternatives": alternatives, "scenarios": scenarios})

    @Slot(str, str, result=str)
    def get_entity_class_values(self, url: str, class_name: str) -> str:
        """Returns [{"entity": ..., "parameter": ..., "alternative": ..., "value": ...}, ...] for every
        parameter value of class_name's entities in the database at url."""
        from spinedb_api import DatabaseMapping, from_database  # imported lazily, same reason as above

        try:
            with DatabaseMapping(url) as db_map:
                class_row = db_map.query(db_map.entity_class_sq).filter_by(name=class_name).first()
                if class_row is None:
                    return json.dumps([])
                entities = {row.id: row.name for row in db_map.query(db_map.entity_sq).filter_by(class_id=class_row.id)}
                definitions = {
                    row.id: row.name
                    for row in db_map.query(db_map.parameter_definition_sq).filter_by(entity_class_id=class_row.id)
                }
                alternatives = {row.id: row.name for row in db_map.query(db_map.alternative_sq)}

                rows = []
                for value_row in db_map.query(db_map.parameter_value_sq):
                    if value_row.entity_id not in entities or value_row.parameter_definition_id not in definitions:
                        continue
                    try:
                        parsed_value = from_database(value_row.value, value_row.type)
                    except Exception:
                        parsed_value = None
                    rows.append(
                        {
                            "entity": entities[value_row.entity_id],
                            "parameter": definitions[value_row.parameter_definition_id],
                            "alternative": alternatives.get(value_row.alternative_id, ""),
                            "value": str(parsed_value),
                        }
                    )
        except Exception:
            return json.dumps([])
        return json.dumps(rows)

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

