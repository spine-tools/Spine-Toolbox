"""Reads and writes the same project.json Data Connection file references as the classic Qt UI."""
import json
import os
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, QUrl, Slot

from ...config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME, LATEST_PROJECT_VERSION

_INPUT_DATA_CONNECTION_NAME = "Input data"

# same QSettings location and "appSettings/recentProjects" format the classic Qt UI uses
_SETTINGS_ORGANIZATION = "SpineProject"
_SETTINGS_APPLICATION = "Spine Toolbox"


def _serialize_path(path: str, project_dir: str) -> dict:
    """Mirrors spine_engine.utils.serialization.serialize_path without importing the heavy spine_engine package."""
    is_relative = os.path.commonpath([os.path.abspath(path), project_dir]) == project_dir
    stored = os.path.relpath(path, project_dir) if is_relative else path
    return {"type": "path", "relative": is_relative, "path": stored.replace(os.sep, "/")}


def _deserialize_path(serialized: dict, project_dir: str) -> str:
    """Mirrors spine_engine.utils.serialization.deserialize_path."""
    path = serialized["path"]
    return os.path.normpath(os.path.join(project_dir, path) if serialized["relative"] else path)


class ProjectBridge(QObject):
    """Exposes a project's Data Connection file references to QML."""

    def __init__(self, project_dir: str | Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project_dir = Path(project_dir)
        self._config_file = self._project_dir / PROJECT_CONFIG_DIR_NAME / PROJECT_FILENAME

    def _load(self) -> dict:
        if not self._config_file.exists():
            return {"project": {"version": LATEST_PROJECT_VERSION, "settings": {}}, "items": {}}
        with self._config_file.open(encoding="utf-8") as input_file:
            return json.load(input_file)

    def _save(self, data: dict) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with self._config_file.open("w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=4)

    def _find_data_connection(self, data: dict) -> tuple[str, dict] | tuple[None, None]:
        for name, item in data["items"].items():
            if item.get("type") == "Data Connection":
                return name, item
        return None, None

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
        """Returns the current project folder's name, or an empty string if it isn't a valid project yet."""
        if not (self._project_dir / PROJECT_CONFIG_DIR_NAME).is_dir():
            return ""
        return self._project_dir.name

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

