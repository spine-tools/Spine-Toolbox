######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains functions used in upgrading and converting projects
and project dicts from earlier versions to the latest version."""
from collections.abc import Callable
import copy
from enum import Enum, auto
import json
import os
import pathlib
import shutil
from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget
from spine_engine.utils.serialization import deserialize_path, serialize_path
from .config import LATEST_PROJECT_VERSION, PROJECT_FILENAME
from .helpers import home_dir
from .project_settings import ProjectSettings


class ProjectUpgradeFailed(Exception):
    pass


class InvalidProjectDict(Exception):
    pass


class VersionCheck(Enum):
    OK = auto()
    UPGRADE_REQUIRED = auto()
    TOO_RECENT = auto()


def check_project_version(project_dict: dict) -> VersionCheck:
    version = project_dict["project"]["version"]
    if version > LATEST_PROJECT_VERSION:
        return VersionCheck.TOO_RECENT
    if version < LATEST_PROJECT_VERSION:
        return VersionCheck.UPGRADE_REQUIRED
    return VersionCheck.OK


def upgrade_project(
    project_dict: dict, project_dir: pathlib.Path | str, item_factories: dict, issue_warning: Callable[[str], None]
) -> dict:
    """Upgrades the project described in given project dictionary to the latest version.

    Args:
        project_dict: Project configuration dictionary
        project_dir: Path to current project directory
        item_factories: Mapping of item type to item factory
        issue_warning: A callback to issue ignorable warnings.

    Returns:
        Latest version of the project info dictionary
    """
    version = project_dict["project"]["version"]
    backup_project_file(project_dir, version)
    upgraded_dict = upgrade_to_latest(version, project_dict, project_dir, item_factories, issue_warning)
    force_save(upgraded_dict, project_dir)
    return upgraded_dict


def upgrade_to_latest(
    version: int,
    project_dict: dict,
    project_dir: pathlib.Path | str,
    item_factories: dict,
    issue_warning: Callable[[str], None],
) -> dict:
    """Upgrades the given project dictionary to the latest version.

    Args:
        version: Current version of the project dictionary
        project_dict: Project dictionary (JSON) to be upgraded
        project_dir: Path to current project directory
        item_factories: Mapping of item type to item factory
        issue_warning: A callback to issue ignorable warnings.

    Returns:
        Upgraded project dictionary
    """
    # Note: upgrade_vx_to_vx() methods should not depend on self._toolbox.item_factories
    # because these are likely to change
    while version < LATEST_PROJECT_VERSION:
        if version == 1:
            project_dict = upgrade_v1_to_v2(project_dict, item_factories)
        elif version == 2:
            project_dict = upgrade_v2_to_v3(project_dict, project_dir, item_factories, issue_warning)
        elif version == 3:
            project_dict = upgrade_v3_to_v4(project_dict)
        elif version == 4:
            project_dict = upgrade_v4_to_v5(project_dict)
        elif version == 5:
            project_dict = upgrade_v5_to_v6(project_dict, project_dir)
        elif version == 6:
            project_dict = upgrade_v6_to_v7(project_dict)
        elif version == 7:
            project_dict = upgrade_v7_to_v8(project_dict)
        elif version == 8:
            project_dict = upgrade_v8_to_v9(project_dict)
        elif version == 9:
            project_dict = upgrade_v9_to_v10(project_dict)
        elif version == 10:
            project_dict = upgrade_v10_to_v11(project_dict)
        elif version == 11:
            project_dict = upgrade_v11_to_v12(project_dict)
        elif version == 12:
            project_dict = upgrade_v12_to_v13(project_dict)
        version += 1
    return project_dict


def upgrade_v1_to_v2(old: dict, item_factories: dict) -> dict:
    """Upgrades version 1 project dictionary to version 2.

    Changes:
        objects -> items, tool_specifications -> specifications
        store project item dicts under ["items"][<project item name>] instead of using their categories as keys
        specifications must be a dict instead of a list
        Add specifications["Tool"] that must be a dict
        Remove "short name" from all project items

    Args:
        old: Version 1 project dictionary
        item_factories: Mapping of item type to item factory

    Returns:
        Version 2 project dictionary
    """
    new = {
        "version": 2,
        "name": old["project"]["name"],
        "description": old["project"]["description"],
        "specifications": {"Tool": old["project"]["tool_specifications"]},
        "connections": old["project"]["connections"],
    }
    # Change 'objects' to 'items' and remove all 'short name' entries
    # Also stores item_dict under their name and not under category
    items = {}
    for category in old["objects"].keys():
        for item_name in old["objects"][category].keys():
            old["objects"][category][item_name].pop("short name", "")  # Remove 'short name'
            # Add type to old item_dict if not there
            if "type" not in old["objects"][category][item_name]:
                old["objects"][category][item_name]["type"] = category[:-1]  # Hackish, but should do the trick
            # Upgrade item_dict to version 2 if needed
            v1_item_dict = old["objects"][category][item_name]
            item_type = old["objects"][category][item_name]["type"]
            if item_type == "Exporter":
                # Factories don't contain 'Exporter' anymore.
                item_type = "GdxExporter"
            v2_item_dict = item_factories[item_type].item_class().upgrade_v1_to_v2(item_name, v1_item_dict)
            items[item_name] = v2_item_dict  # Store items using their name as key
    return {"project": new, "items": items}


def upgrade_v2_to_v3(
    old: dict, project_dir: pathlib.Path | str, factories: dict, issue_warning: Callable[[str], None]
) -> dict:
    """Upgrades version 2 project dictionary to version 3.

    Changes:
        1. Move "specifications" from "project" -> "Tool" to just "project"
        2. The "mappings" from importer items are used to build Importer specifications

    Args:
        old: Version 2 project dictionary
        project_dir: Path to current project directory
        factories: Mapping of item type to item factory
        issue_warning: A callback to issue ignorable warnings.

    Returns:
        Version 3 project dictionary
    """
    new = copy.deepcopy(old)
    project = new["project"]
    project["version"] = 3
    # Put DT specs in their own subkey
    project["specifications"]["Data Transformer"] = dt_specs = []
    tool_specs = project["specifications"].get("Tool", [])
    for i, spec in reversed(list(enumerate(tool_specs))):
        spec_path = deserialize_path(spec, project_dir)
        if not os.path.exists(spec_path):
            issue_warning(f"Upgrading Tool spec failed. <b>{spec_path}</b> does not exist.")
            continue
        with open(spec_path, "r") as fp:
            try:
                spec = json.load(fp)
            except ValueError:
                continue
            if spec.get("item_type") == "Data Transformer":
                dt_specs.append(tool_specs.pop(i))
    project["specifications"]["Importer"] = importer_specs = []
    for item_name, old_item_dict in old["items"].items():
        item_type = old_item_dict["type"]
        if item_type == "Exporter":
            # Factories don't contain 'Exporter' anymore.
            item_type = "GdxExporter"
        try:
            new["items"][item_name] = factories[item_type].item_class().upgrade_v2_to_v3(item_name, old_item_dict)
        except KeyError:
            # This happens when an unknown item type is encountered.
            # Factories do not contain 'Combiner' anymore
            if item_type == "Combiner":
                new["items"][item_name] = old_item_dict
        if item_type == "Importer":
            mappings = old_item_dict.get("mappings")
            # Sanitize old mappings, as we used to do in Importer.from_dict
            if mappings is None:
                mappings = []
            # Convert table_types and table_row_types keys to int since json always has strings as keys.
            for _, mapping in mappings:
                table_types = mapping.get("table_types", {})
                mapping["table_types"] = {
                    table_name: {int(col): t for col, t in col_types.items()}
                    for table_name, col_types in table_types.items()
                }
                table_row_types = mapping.get("table_row_types", {})
                mapping["table_row_types"] = {
                    table_name: {int(row): t for row, t in row_types.items()}
                    for table_name, row_types in table_row_types.items()
                }
            # Convert serialized paths to absolute in mappings
            _fix_1d_array_to_array(mappings)
            # Make item specs from sanitized mappings
            for k, (label, mapping) in enumerate(mappings):
                spec_name = make_unique_importer_specification_name(item_name, label, k)
                spec = {"name": spec_name, "item_type": "Importer", "mapping": mapping}
                spec_path = os.path.join(project_dir, spec_name + ".json")
                # FIXME: Let's try and handle write errors here...
                with open(spec_path, "w") as fp:
                    json.dump(spec, fp, indent=4)
                importer_specs.append(serialize_path(spec_path, project_dir))
    return new


def upgrade_v3_to_v4(old: dict) -> dict:
    """Upgrades version 3 project dictionary to version 4.

    Changes:
        1. Rename "Exporter" item type to "GdxExporter"

    Args:
        old: Version 3 project dictionary

    Returns:
        Version 4 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 4
    for item_dict in new["items"].values():
        if item_dict["type"] == "Exporter":
            item_dict["type"] = "GdxExporter"
    return new


def upgrade_v4_to_v5(old: dict) -> dict:
    """Upgrades version 4 project dictionary to version 5.

    Changes:
        1. Get rid of "Combiner" items.

    Args:
        old: Version 4 project dictionary

    Returns:
        Version 5 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 5
    combiners = []
    for name, item_dict in new["items"].items():
        if item_dict["type"] == "Combiner":
            combiners.append(name)
    for combiner in combiners:
        del new["items"][combiner]
    conns_to_item = {}
    conns_from_item = {}
    for conn in new["project"]["connections"]:
        from_name, _ = conn["from"]
        to_name, _ = conn["to"]
        conns_to_item.setdefault(to_name, []).append(conn)
        conns_from_item.setdefault(from_name, []).append(conn)
    conns_to_remove = []
    conns_to_add = []
    combiners_copy = combiners.copy()
    while combiners:
        combiner = combiners.pop()
        conns_to = conns_to_item.get(combiner, [])
        conns_from = conns_from_item.get(combiner, [])
        for conn_to in conns_to:
            conns_to_remove.append(conn_to)
            from_name, from_anchor = conn_to["from"]
            resource_filters = conn_to.get("resource_filters", {})
            for conn_from in conns_from:
                conns_to_remove.append(conn_from)
                to_name, to_anchor = conn_from["to"]
                more_resource_filters = conn_from.get("resource_filters", {})
                new_conn = {"from": [from_name, from_anchor], "to": [to_name, to_anchor]}
                for resource, filters in more_resource_filters.items():
                    for filter_type, values in filters.items():
                        existing_values = resource_filters.setdefault(resource, {}).setdefault(filter_type, [])
                        for value in values:
                            if value not in existing_values:
                                existing_values.append(value)
                if resource_filters:
                    new_conn["resource_filters"] = resource_filters
                if not {from_name, to_name}.intersection(combiners_copy):
                    conns_to_add.append(new_conn)
                conns_to_item.setdefault(to_name, []).append(new_conn)
                conns_from_item.setdefault(from_name, []).append(new_conn)
    new["project"]["connections"] += conns_to_add
    for conn in conns_to_remove:
        try:
            new["project"]["connections"].remove(conn)
        except ValueError:
            pass
    return new


def upgrade_v5_to_v6(old: dict, project_dir: pathlib.Path | str) -> dict:
    """Upgrades version 5 project dictionary to version 6.

    Changes:
        1. Data store URL labels do not have '{' and '}' anymore
        2. Importer stores resource labels instead of serialized paths in "file_selection".
        3. Gimlet's "selections" is now called "file_selection"
        4. Gimlet stores resource labels instead of serialized paths in "file_selection".
        5. Gimlet and Tool store command line arguments as serialized CmdLineArg objects, not serialized paths

    Args:
        old: Version 5 project dictionary
        project_dir: Path to current project directory

    Returns:
        Version 6 project dictionary
    """

    def fix_file_selection(item_dict):
        old_selection = item_dict.get("file_selection", [])
        new_selection = []
        for path, selected in old_selection:
            deserialized = deserialize_path(path, project_dir)
            if deserialized.startswith("{") and deserialized.endswith("}"):
                # Fix old-style data store resource labels '{db_url@item name}'.
                deserialized = deserialized[1:-1]
            new_selection.append([deserialized, selected])
        item_dict["file_selection"] = new_selection

    def fix_cmd_line_args(item_dict):
        old_args = item_dict.get("cmd_line_args", [])
        new_args = []
        for arg in old_args:
            deserialized = deserialize_path(arg, project_dir)
            if deserialized.startswith("{") and deserialized.endswith("}"):
                # Fix old-style data store resource labels '{db_url@item name}'.
                deserialized = deserialized[1:-1]
            # We assume all args are resource labels. This may not always be true, though, and needs to be
            # fixed manually once the project has been loaded.
            new_args.append({"type": "resource", "arg": deserialized})
        item_dict["cmd_line_args"] = new_args

    new = copy.deepcopy(old)
    new["project"]["version"] = 6
    importer_dicts = [item_dict for item_dict in new["items"].values() if item_dict["type"] == "Importer"]
    for import_dict in importer_dicts:
        fix_file_selection(import_dict)
    gimlet_dicts = [item_dict for item_dict in new["items"].values() if item_dict["type"] == "Gimlet"]
    for gimlet_dict in gimlet_dicts:
        gimlet_dict["file_selection"] = gimlet_dict.pop("selections", [])
        fix_file_selection(gimlet_dict)
        fix_cmd_line_args(gimlet_dict)
    tool_dicts = [item_dict for item_dict in new["items"].values() if item_dict["type"] == "Tool"]
    for tool_dict in tool_dicts:
        fix_cmd_line_args(tool_dict)
    return new


def upgrade_v6_to_v7(old: dict) -> dict:
    """Upgrades version 6 project dictionary to version 7.

    Changes:
        1. Introduces Mergers in between DS -> DS links.

    Args:
        old: Version 6 project dictionary

    Returns:
        dict: Version 7 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 7
    data_stores = []
    for name, item_dict in new["items"].items():
        if item_dict["type"] == "Data Store":
            data_stores.append(name)
    ds_ds_connections = {}
    to_remove = []
    for conn in new["project"]["connections"]:
        from_name, _ = conn["from"]
        to_name, _ = conn["to"]
        if from_name in data_stores and to_name in data_stores:
            ds_ds_connections.setdefault(tuple(conn["to"]), []).append(conn["from"])
            to_remove.append(conn)
    for to_conn, from_conns in ds_ds_connections.items():
        to_name, to_pos = to_conn
        from_names, from_positions = zip(*from_conns)
        from_pos = max(set(from_positions), key=from_positions.count)
        names = from_names + (to_name,)
        items = [new["items"][name] for name in names]
        x = sum(item["x"] for item in items) / len(items)
        y = sum(item["y"] for item in items) / len(items)
        merger_name = f"{to_name} merger"
        new["items"][merger_name] = {
            "type": "Merger",
            "description": f"Merges data into {to_name}",
            "x": x,
            "y": y,
            "cancel_on_error": new["items"][to_name].pop("cancel_on_error", False),
        }
        for from_name in from_names:
            new["project"]["connections"].append({"from": [from_name, from_pos], "to": [merger_name, to_pos]})
        new["project"]["connections"].append({"from": [merger_name, "right"], "to": list(to_conn)})
    for conn in to_remove:
        new["project"]["connections"].remove(conn)
    return new


def upgrade_v7_to_v8(old: dict) -> dict:
    """Upgrades version 7 project dictionary to version 8.

    Changes:
        1. Move purge settings from items to their outgoing connections.

    Args:
        old: Version 7 project dictionary

    Returns:
        Version 8 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 8
    purge_options_by_name = {}
    for name, item_dict in new["items"].items():
        if item_dict.get("purge_before_writing", False):
            purge_options_by_name[name] = {
                "purge_before_writing": True,
                "purge_settings": item_dict.get("purge_settings"),
            }
    for conn in new["project"]["connections"]:
        from_name, _ = conn["from"]
        purge_options = purge_options_by_name.get(from_name)
        if purge_options is not None:
            conn.setdefault("options", {}).update(purge_options)
    return new


def upgrade_v8_to_v9(old: dict) -> dict:
    """Upgrades version 8 project dictionary to version 9.

    Changes:
        1. Remove ["project"]["name"] key

    Args:
        old: Version 8 project dictionary

    Returns:
        Version 9 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 9
    try:
        new["project"].pop("name")
    except KeyError:
        pass
    return new


def upgrade_v9_to_v10(old: dict) -> dict:
    """Upgrades version 9 project dictionary to version 10.

    Changes:
        1. Remove connections from Gimlets and GDXExporters
        2. Remove Gimlet items

    Args:
        old: Version 9 project dictionary

    Returns:
        Version 10 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 10
    names_to_remove = []  # Gimlet and GdxExporter item names
    # Get Gimlet and GdxExporter names and remove connections
    for name, item_dict in new["items"].items():
        if item_dict["type"] in ["Gimlet", "GdxExporter"]:
            names_to_remove.append(name)
    # Get list of connections to remove
    connections_to_remove = []
    for conn in new["project"]["connections"]:
        for name_to_remove in names_to_remove:
            if name_to_remove in conn["from"] or name_to_remove in conn["to"]:
                connections_to_remove.append(conn)
    for conn_to_remove in connections_to_remove:
        new["project"]["connections"].remove(conn_to_remove)
    # Remove Gimlet and GdxExporter item dictionaries
    for name in names_to_remove:
        new["items"].pop(name)
    return new


def upgrade_v10_to_v11(old: dict) -> dict:
    """Upgrades version 10 project dictionary to version 11.

    Changes:
        1. Add ["project"]["settings"] key

    Args:
        old: Version 10 project dictionary

    Returns:
        Version 11 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 11
    new["project"]["settings"] = ProjectSettings().to_dict()
    return new


def upgrade_v11_to_v12(old: dict) -> dict:
    """Upgrades version 11 project dictionary to version 12.

    Changes:
        1. Julia's execution settings are now Tool Spec settings instead of global settings
        Execution settings are local user settings so this only updates the project version
        to make sure that these projects cannot be opened with an older Toolbox version.

    Args:
        old: Version 11 project dictionary

    Returns:
        Version 12 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 12
    return new


def upgrade_v12_to_v13(old: dict) -> dict:
    """Upgrades version 12 project dictionary to version 13.

    Changes:
        1. Connections now have enabled filter types field.
        Old projects should open just fine so this only updates the project version
        to make sure that these projects cannot be opened with an older Toolbox version.

    Args:
        old: Version 12 project dictionary

    Returns:
        Version 13 project dictionary
    """
    new = copy.deepcopy(old)
    new["project"]["version"] = 13
    return new


def make_unique_importer_specification_name(importer_name: str, label: dict, k: int) -> str:
    return f"{importer_name} - {os.path.basename(label['path'])} - {k}"


def get_project_directory(parent: QWidget) -> str:
    """Asks the user to select a new project directory. If the selected directory
    is already a Spine Toolbox project directory, asks if overwrite is ok. Used
    when opening a project from an old style project file (.proj).

    Args:
        parent: A parent widget.

    Returns:
        Path to project directory or an empty string if operation is canceled.
    """
    # Ask user for a new directory where to save the project
    answer = QFileDialog.getExistingDirectory(parent, "Select a project directory", home_dir())
    if not answer:  # Canceled (american-english), cancelled (british-english)
        return ""
    if not os.path.isdir(answer):  # Check that it's a directory
        msg = "Selection is not a directory, please try again"
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.warning(parent, "Invalid selection", msg)
        return ""
    # Check if the selected directory is already a project directory and ask if overwrite is ok
    if os.path.isdir(os.path.join(answer, ".spinetoolbox")):
        msg = (
            f"Directory \n\n{answer}\n\nalready contains a Spine Toolbox project."
            f"\n\nWould you like to overwrite it?"
        )
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Overwrite?",
            msg,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=parent,
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText("Overwrite")
        msgbox_answer = message_box.exec()
        if msgbox_answer != QMessageBox.StandardButton.Ok:
            return ""
    return answer


def check_project_dict_valid(version: int, project_dict: dict) -> None:
    """Checks given project dict if it is valid for given version.

    Args:
        version: project version to validate against
        project_dict: project dictionary
    """
    if version == 1:
        check_valid_v1(project_dict)
    elif 2 <= version <= 8:
        check_valid_v2_to_v8(project_dict, version)
    elif 9 <= version <= 10:
        check_valid_v9_to_v10(project_dict)
    elif 11 <= version <= 13:
        check_valid_v11_to_v12(project_dict)
    else:
        raise NotImplementedError(f"No validity check available for version {version}")


def check_valid_v1(project_dict: dict):
    """Checks that the given project JSON dictionary contains
    a valid version 1 Spine Toolbox project. Valid meaning, that
    it contains all required keys and values are of the correct
    type.

    Args:
        project_dict: Project information JSON
    """
    if "project" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'project' not found.")
    if "objects" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'objects' not found.")
    required_project_keys = ["version", "name", "description", "tool_specifications", "connections"]
    project = project_dict["project"]
    objects = project_dict["objects"]
    if not isinstance(project, dict):
        raise InvalidProjectDict("Invalid project.json file. 'project' must be a dict.")
    if not isinstance(objects, dict):
        raise InvalidProjectDict("Invalid project.json file. 'objects' must be a dict.")
    for req_key in required_project_keys:
        if req_key not in project:
            raise InvalidProjectDict(f"Invalid project.json file. Key {req_key} not found.")
    # Check types in project dict
    if not project["version"] == 1:
        raise InvalidProjectDict("Invalid project version")
    if not isinstance(project["name"], str) or not isinstance(project["description"], str):
        raise InvalidProjectDict("Invalid project.json file. 'name' and 'description' must be strings.")
    if not isinstance(project["tool_specifications"], list):
        raise InvalidProjectDict("Invalid project.json file. 'tool_specifications' must be a list.")
    if not isinstance(project["connections"], list):
        raise InvalidProjectDict("Invalid project.json file. 'connections' must be a list.")


def check_valid_v2_to_v8(project_dict: dict, version: int) -> None:
    """Checks that the given project JSON dictionary contains
    a valid version 2 to 8 Spine Toolbox project. Valid meaning, that
    it contains all required keys and values are of the correct
    type.

    Args:
        project_dict: Project dict to check.
        version: Project version to validate against.
    """
    if "project" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'project' not found.")
    if "items" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'items' not found.")
    required_project_keys = ["version", "name", "description", "specifications", "connections"]
    project = project_dict["project"]
    items = project_dict["items"]
    if not isinstance(project, dict):
        raise InvalidProjectDict("Invalid project.json file. 'project' must be a dict.")
    if not isinstance(items, dict):
        raise InvalidProjectDict("Invalid project.json file. 'items' must be a dict.")
    for req_key in required_project_keys:
        if req_key not in project:
            raise InvalidProjectDict(f"Invalid project.json file. Key {req_key} not found.")
    # Check types in project dict
    if not project["version"] == version:
        raise InvalidProjectDict(f"Invalid project version:'{project['version']}'")
    if not isinstance(project["name"], str) or not isinstance(project["description"], str):
        raise InvalidProjectDict("Invalid project.json file. 'name' and 'description' must be strings.")
    if not isinstance(project["specifications"], dict):
        raise InvalidProjectDict("Invalid project.json file. 'specifications' must be a dictionary.")
    if not isinstance(project["connections"], list):
        raise InvalidProjectDict("Invalid project.json file. 'connections' must be a list.")


def check_valid_v9_to_v10(project_dict: dict) -> None:
    """Checks that the given project JSON dictionary contains
    a valid version 9 or 10 Spine Toolbox project. Valid meaning, that
    it contains all required keys and values are of the correct
    type.

    Args:
        project_dict: Project information JSON
    """
    if "project" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'project' not found.")
    if "items" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'items' not found.")
    required_project_keys = ["version", "description", "specifications", "connections"]
    project = project_dict["project"]
    items = project_dict["items"]
    if not isinstance(project, dict):
        raise InvalidProjectDict("Invalid project.json file. 'project' must be a dict.")
    if not isinstance(items, dict):
        raise InvalidProjectDict("Invalid project.json file. 'items' must be a dict.")
    for req_key in required_project_keys:
        if req_key not in project:
            raise InvalidProjectDict(f"Invalid project.json file. Key {req_key} not found.")


def check_valid_v11_to_v12(project_dict: dict) -> None:
    """Checks that the given project JSON dictionary contains
    a valid version 11 or 12 Spine Toolbox project. Valid meaning, that
    it contains all required keys and values are of the correct
    type.

    Args:
        project_dict: Project information JSON
    """
    if "project" not in project_dict:
        raise InvalidProjectDict("Invalid project.json file. Key 'project' not found.")
    if "settings" not in project_dict["project"]:
        raise InvalidProjectDict("Invalid project.json file. Key 'items' not found in 'project'.")
    if not isinstance(project_dict["project"]["settings"], dict):
        raise InvalidProjectDict("Invalid project.json file. 'settings' must be a dict.")


def backup_project_file(project_dir, version: int) -> None:
    """Makes a backup copy of project.json file."""
    src = os.path.join(project_dir, ".spinetoolbox", PROJECT_FILENAME)
    backup_filename = "project.json.bak" + str(version)
    dst = os.path.join(project_dir, ".spinetoolbox", backup_filename)
    try:
        shutil.copyfile(src, dst)
    except OSError:
        raise ProjectUpgradeFailed(f"Making a backup of '{src}' failed. Check permissions.")


def force_save(project_dict: dict, project_dir: pathlib.Path | str) -> None:
    """Saves given project dictionary to project.json file.
    Used to force save project.json file when the project
    dictionary has been upgraded."""
    project_json_path = pathlib.Path(project_dir, ".spinetoolbox", PROJECT_FILENAME)
    try:
        with open(project_json_path, "w") as fp:
            json.dump(project_dict, fp, indent=4)
    except OSError:
        raise ProjectUpgradeFailed("Saving project.json file failed. Check permissions.")


def _fix_1d_array_to_array(mappings: dict) -> None:
    """
    Replaces '1d array' with 'array' for parameter type in Importer mappings.

    With spinedb_api >= 0.3, '1d array' parameter type was replaced by 'array'.
    Other settings in a mapping are backwards compatible except the name.
    """
    for more_mappings in mappings:
        for settings in more_mappings:
            table_mappings = settings.get("table_mappings")
            if table_mappings is None:
                continue
            for sheet_settings in table_mappings.values():
                for setting in sheet_settings:
                    parameter_setting = setting.get("parameters")
                    if parameter_setting is None:
                        continue
                    parameter_type = parameter_setting.get("parameter_type")
                    if parameter_type == "1d array":
                        parameter_setting["parameter_type"] = "array"
