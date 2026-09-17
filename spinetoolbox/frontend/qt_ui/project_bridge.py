"""Reads and writes the same project.json Data Connection file references as the classic Qt UI."""
import json
import os
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QUrl, Slot

from ...config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME, LATEST_PROJECT_VERSION
from ...helpers import open_url

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


class ProjectBridge(QObject):
    """Exposes a project's Data Connection file references to QML."""

    def __init__(self, project_dir: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_dir = Path(project_dir)
        self._config_file = self._project_dir / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME
        self._db_editor = None

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

    def _base_dir(self) -> Path:
        """Returns the project directory items are relative to, falling back to the bundled example's own
        folder when no real project is open (self._project_dir is then just the launch cwd)."""
        if self._config_file.exists():
            return self._project_dir
        return _EXAMPLE_PROJECT_FILE.parent

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
            connections.append({"from": from_name, "to": to_name})

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
        from ...spine_db_manager import SpineDBManager
        from ...spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor

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

