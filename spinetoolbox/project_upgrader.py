######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains ProjectUpgrader class used in upgrading and converting projects
and project dicts from earlier versions to the latest version.

:authors: P. Savolainen (VTT)
:date:   8.11.2019
"""

import shutil
import os
import json
import copy
from PySide2.QtWidgets import QFileDialog, QMessageBox
from spinetoolbox.helpers import create_dir, serialize_path, deserialize_path
from .config import LATEST_PROJECT_VERSION, PROJECT_FILENAME
from .helpers import recursive_overwrite


class ProjectUpgrader:
    """Class to upgrade/convert projects from earlier versions to the current version."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): toolbox of this project
        """
        self._toolbox = toolbox

    def upgrade_to_v1(self, project_dict, old_project_dir):
        """Upgrades no version project dict to version 1.
        This may be removed when we no longer want to support
        upgrading legacy .proj projects to current ones."""
        return self.upgrade_from_no_version_to_version_1(project_dict, old_project_dir)

    def upgrade(self, project_dict, project_dir):
        """Upgrades the project described in given project dictionary to the latest version.

        Args:
            project_dict (dict): Project configuration dictionary
            project_dir (str): Path to current project directory

        Returns:
            dict: Latest version of the project info dictionary
        """
        v = project_dict["project"]["version"]
        n = project_dict["project"]["name"]
        if v > LATEST_PROJECT_VERSION:
            # User is trying to load a more recent project than this version of Toolbox can handle
            self._toolbox.msg_warning.emit(f"Opening project <b>{n}</b> failed. The project's version is {v}, while "
                                           f"this version of Spine Toolbox supports project versions up to and "
                                           f"including {LATEST_PROJECT_VERSION}. To open this project, you should "
                                           f"upgrade Spine Toolbox")
            return False
        if v < LATEST_PROJECT_VERSION:
            # Back up project.json file before upgrading
            if not self.backup_project_file(project_dir):
                self._toolbox.msg_error.emit("Upgrading project failed")
                return False
            self._toolbox.msg_warning.emit("Backed up project.json -> project.json.bak")
            upgraded_dict = self.upgrade_to_latest(v, project_dict, project_dir)
            # Force save project dict to project.json
            if not self.force_save(upgraded_dict, project_dir):
                self._toolbox.msg_error.emit("Upgrading project failed")
                return False
            return upgraded_dict
        else:
            return project_dict

    def upgrade_to_latest(self, v, project_dict, project_dir):
        """Upgrades the given project dictionary to the latest version.

        Args:
            v (int): Current version of the project dictionary
            project_dict (dict): Project dictionary (JSON) to be upgraded
            project_dir (str): Path to current project directory

        Returns:
            dict: Upgraded project dictionary
        """
        while v < LATEST_PROJECT_VERSION:
            if v == 1:
                project_dict = self.upgrade_v1_to_v2(project_dict, self._toolbox.item_factories)
                v += 1
                self._toolbox.msg_success.emit(f"Project upgraded to version {v}")
            # Example on what to do when version 3 comes
            elif v == 2:
                project_dict = self.upgrade_v2_to_v3(project_dict, project_dir, self._toolbox.item_factories)
                v += 1
                self._toolbox.msg_success.emit(f"Project upgraded to version {v}")
        return project_dict

    @staticmethod
    def make_unique_importer_specification_name(importer_name, label, k):
        return f"{importer_name} - {os.path.basename(label['path'])} - {k}"

    def upgrade_v2_to_v3(self, old, project_dir, factories):
        """Upgrades version 2 project dictionary to version 3.

        Changes:
            1. Move "specifications" from "project" -> "Tool" to just "project"
            2. The "mappings" from importer items are used to build Importer specifications

        Args:
            old (dict): Version 2 project dictionary
            project_dir (str): Path to current project directory
            factories (dict): Mapping of item type to item factory

        Returns:
            dict: Version 3 project dictionary
        """
        new = copy.deepcopy(old)
        project = new["project"]
        project["version"] = 3
        # Put DT specs in their own subkey
        project["specifications"]["Data Transformer"] = dt_specs = []
        tool_specs = project["specifications"].get("Tool", [])
        for i, spec in reversed(list(enumerate(tool_specs))):
            spec_path = deserialize_path(spec, project_dir)
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
            new["items"][item_name] = factories[item_type].item_class().upgrade_v2_to_v3(item_name, old_item_dict, self)
            if item_type == "Importer":
                mappings = old_item_dict.get("mappings")
                # Sanitize old mappings, as we use to do in Importer.from_dict
                if mappings is None:
                    mappings = list()
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
                    spec_name = self.make_unique_importer_specification_name(item_name, label, k)
                    spec = dict(name=spec_name, item_type="Importer", mapping=mapping)
                    spec_path = os.path.join(project_dir, spec_name + ".json")
                    # FIXME: Let's try and handle write errors here...
                    with open(spec_path, "w") as fp:
                        json.dump(spec, fp, indent=4)
                    importer_specs.append(serialize_path(spec_path, project_dir))
        return new

    @staticmethod
    def upgrade_v1_to_v2(old, factories):
        """Upgrades version 1 project dictionary to version 2.

        Changes:
            objects -> items, tool_specifications -> specifications
            store project item dicts under ["items"][<project item name>] instead of using their categories as keys
            specifications must be a dict instead of a list
            Add specifications["Tool"] that must be a dict
            Remove "short name" from all project items

        Args:
            old (dict): Version 1 project dictionary
            factories (dict): Mapping of item type to item factory

        Returns:
            dict: Version 2 project dictionary
        """
        new = dict()
        new["version"] = 2
        new["name"] = old["project"]["name"]
        new["description"] = old["project"]["description"]
        new["specifications"] = dict()
        new["specifications"]["Tool"] = old["project"]["tool_specifications"]
        new["connections"] = old["project"]["connections"]
        # Change 'objects' to 'items' and remove all 'short name' entries
        # Also stores item_dict under their name and not under category
        items = dict()
        for category in old["objects"].keys():
            for item_name in old["objects"][category].keys():
                old["objects"][category][item_name].pop("short name", "")  # Remove 'short name'
                # Add type to old item_dict if not there
                if "type" not in old["objects"][category][item_name]:
                    old["objects"][category][item_name]["type"] = category[:-1]  # Hackish, but should do the trick
                # Upgrade item_dict to version 2 if needed
                v1_item_dict = old["objects"][category][item_name]
                item_type = old["objects"][category][item_name]["type"]
                v2_item_dict = factories[item_type].item_class().upgrade_v1_to_v2(item_name, v1_item_dict)
                items[item_name] = v2_item_dict  # Store items using their name as key
        return dict(project=new, items=items)

    def upgrade_from_no_version_to_version_1(self, old, old_project_dir):
        """Converts project information dictionaries without 'version' to version 1.

        Args:
            old (dict): Project information JSON
            old_project_dir (str): Path to old project directory

        Returns:
             dict: Project information JSON upgraded to version 1
        """
        new = dict()
        new["version"] = 1
        new["name"] = old["project"]["name"]
        new["description"] = old["project"]["description"]
        new["work_dir"] = old["project"]["work_dir"]
        try:
            spec_paths = old["project"]["tool_specifications"]
        except KeyError:
            try:
                spec_paths = old["project"]["tool_templates"]
            except KeyError:
                spec_paths = list()
        new["tool_specifications"] = self.upgrade_specification_paths(spec_paths, old_project_dir)
        # Old projects may have obsolete category names that need to be updated
        if "Data Interfaces" in old["objects"].keys():
            old["objects"]["Importers"] = old["objects"]["Data Interfaces"]
            old["objects"].pop("Data Interfaces")
        if "Data Exporters" in old["objects"].keys():
            old["objects"]["Exporters"] = old["objects"]["Data Exporters"]
            old["objects"].pop("Data Exporters")
        # Get all item names to a list from old project dict. Needed for upgrading connections.
        item_names = list()
        for category in old["objects"]:
            if category not in self._toolbox.item_factories:
                continue
            for item_name, item_dict in old["objects"][category].items():
                item_names.append(item_name)
        # Parse connections
        try:
            old_connections = old["project"]["connections"]
        except KeyError:
            new["connections"] = list()
        else:
            # old connections maybe of two types, convert them to the newer format
            new["connections"] = self.upgrade_connections(item_names, old_connections)
        # Upgrade objects dict
        new_objects = dict(old["objects"])
        for category in old["objects"]:
            item_type = {
                "Data Connections": "Data Connection",
                "Data Stores": "Data Store",
                "Exporters": "Exporter",
                "Importers": "Importer",
                "Tools": "Tool",
                "Views": "View",
            }.get(category)
            if item_type is None:
                self._toolbox.msg_error.emit(f"Upgrading project item failed. Unknown category '{category}'.")
                continue
            if item_type not in self._toolbox.item_factories:
                self._toolbox.msg_error.emit(f"Upgrading project item failed. Unknown item type '{item_type}'.")
                continue
            item_class = self._toolbox.item_factories[item_type].item_class()
            for item_name, item_dict in old["objects"][category].items():
                new_item_dict = item_class.upgrade_from_no_version_to_version_1(item_name, item_dict, old_project_dir)
                new_objects[category][item_name] = new_item_dict
        return dict(project=new, objects=new_objects)

    def upgrade_connections(self, item_names, connections_old):
        """Upgrades connections from old format to the new format.

        - Old format. List of lists, e.g.

        .. code-block::

            [
                [False, False, ["right", "left"], False],
                [False, ["bottom", "left"], False, False],
                ...
            ]

        - New format. List of dicts, e.g.

        .. code-block::

            [
                {"from": ["DC1", "right"], "to": ["Tool1", "left"]},
                ...
            ]
        """
        if not connections_old:
            return list()
        if not isinstance(connections_old[0], list):
            # Connections are already in new format. Return as-is
            return connections_old
        # Convert from old format to new format
        connections = list()
        for i, row in enumerate(connections_old):
            for j, entry in enumerate(row):
                if entry is False:
                    continue
                try:
                    src_item = item_names[i]
                    dst_item = item_names[j]
                except IndexError:
                    # Might happen when e.g. the project file contains project items
                    # that couldn't be restored because the corresponding project item plugin wasn't found
                    self._toolbox.msg_warning.emit("Restoring a connection failed")
                    continue
                try:
                    src_anchor, dst_anchor = entry
                except TypeError:
                    # Happens when first loading a project that wasn't saved with the current version
                    src_anchor = dst_anchor = "bottom"
                entry_new = {"from": [src_item, src_anchor], "to": [dst_item, dst_anchor]}
                connections.append(entry_new)
        return connections

    @staticmethod
    def upgrade_specification_paths(spec_paths, old_project_dir):
        """Upgrades a list of specifications paths to new format.
        Paths in (old) project directory (yes, old is correct) are converted
        to relative, others as absolute.
        """
        if not spec_paths:
            return list()
        new_paths = list()
        for p in spec_paths:
            ser_path = serialize_path(p, old_project_dir)
            if ser_path["relative"]:
                ser_path["path"] = os.path.join(".spinetoolbox", "items", ser_path["path"])
            new_paths.append(ser_path)
        return new_paths

    def open_proj_json(self, proj_file_path):
        """Opens an old style project file (.proj) for reading,

        Args:
            proj_file_path (str): Full path to the old .proj project file

        Returns:
            dict: Project dictionary or None if the operation fails.
        """
        try:
            with open(proj_file_path, "r") as fh:
                try:
                    proj_info = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self._toolbox.msg_error.emit(
                        "Error in project file <b>{0}</b>. Invalid JSON.".format(proj_file_path)
                    )
                    return None
        except OSError:
            self._toolbox.msg_error.emit("Opening project file <b>{0}</b> failed".format(proj_file_path))
            return None
        return proj_info

    def get_project_directory(self):
        """Asks the user to select a new project directory. If the selected directory
        is already a Spine Toolbox project directory, asks if overwrite is ok. Used
        when opening a project from an old style project file (.proj).

        Returns:
            str: Path to project directory or an empty string if operation is canceled.
        """
        # Ask user for a new directory where to save the project
        answer = QFileDialog.getExistingDirectory(self._toolbox, "Select a project directory", os.path.abspath("C:\\"))
        if not answer:  # Canceled (american-english), cancelled (british-english)
            return ""
        if not os.path.isdir(answer):  # Check that it's a directory
            msg = "Selection is not a directory, please try again"
            # noinspection PyCallByClass, PyArgumentList
            QMessageBox.warning(self._toolbox, "Invalid selection", msg)
            return ""
        # Check if the selected directory is already a project directory and ask if overwrite is ok
        if os.path.isdir(os.path.join(answer, ".spinetoolbox")):
            msg = (
                "Directory \n\n{0}\n\nalready contains a Spine Toolbox project."
                "\n\nWould you like to overwrite it?".format(answer)
            )
            message_box = QMessageBox(
                QMessageBox.Question,
                "Overwrite?",
                msg,
                buttons=QMessageBox.Ok | QMessageBox.Cancel,
                parent=self._toolbox,
            )
            message_box.button(QMessageBox.Ok).setText("Overwrite")
            msgbox_answer = message_box.exec_()
            if msgbox_answer != QMessageBox.Ok:
                return ""
        return answer  # New project directory

    def copy_data(self, proj_file_path, project_dir):
        """Copies project item directories from the old project to the new project directory.

        Args:
            proj_file_path (str): Path to .proj file
            project_dir (str): New project directory

        Returns:
            bool: True if copying succeeded, False if it failed
        """
        proj_info = self.open_proj_json(proj_file_path)
        if not proj_info:
            return False
        name = proj_info["project"]["name"]
        dir_name = name.lower().replace(" ", "_")
        proj_file_dir, _ = os.path.split(proj_file_path)
        old_project_dir = os.path.join(proj_file_dir, dir_name)
        if not os.path.isdir(old_project_dir):
            return False
        self._toolbox.msg.emit("Copying data to new project directory")
        # Make items directory to new project directory
        config_dir = os.path.join(project_dir, ".spinetoolbox")
        items_dir = os.path.join(config_dir, "items")
        try:
            create_dir(items_dir)
        except OSError:
            self._toolbox.msg_error.emit("Creating directory {0} failed".format(items_dir))
            return False
        src_dir = os.path.abspath(old_project_dir)
        dst_dir = os.path.abspath(items_dir)
        recursive_overwrite(self._toolbox, src_dir, dst_dir, ignore=None, silent=False)
        return True

    def is_valid(self, v, p):
        """Checks given project dict if it is valid for given version."""
        if v == 1:
            is_valid = self.is_valid_v1(p)
        elif v == 2:
            is_valid = self.is_valid_v2(p)
        elif v == 3:
            is_valid = self.is_valid_v3(p)
        else:
            raise NotImplementedError(f"No validity check available for version {v}")
        return is_valid

    def is_valid_v1(self, p):
        """Checks that the given project JSON dictionary contains
        a valid version 1 Spine Toolbox project. Valid meaning, that
        it contains all required keys and values are of the correct
        type.

        Args:
            p (dict): Project information JSON

        Returns:
            bool: True if project is a valid version 1 project, False if it is not
        """
        if "project" not in p.keys():
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'project' not found.")
            return False
        if "objects" not in p.keys():
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'objects' not found.")
            return False
        required_project_keys = ["version", "name", "description", "tool_specifications", "connections"]
        project = p["project"]
        objects = p["objects"]
        if not isinstance(project, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'project' must be a dict.")
            return False
        if not isinstance(objects, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'objects' must be a dict.")
            return False
        for req_key in required_project_keys:
            if req_key not in project:
                self._toolbox.msg_error.emit("Invalid project.json file. Key {0} not found.".format(req_key))
                return False
        # Check types in project dict
        if not project["version"] == 1:
            self._toolbox.msg_error.emit("Invalid project version")
            return False
        if not isinstance(project["name"], str) or not isinstance(project["description"], str):
            self._toolbox.msg_error.emit("Invalid project.json file. 'name' and 'description' must be strings.")
            return False
        if not isinstance(project["tool_specifications"], list):
            self._toolbox.msg_error.emit("Invalid project.json file. 'tool_specifications' must be a list.")
            return False
        if not isinstance(project["connections"], list):
            self._toolbox.msg_error.emit("Invalid project.json file. 'connections' must be a list.")
            return False
        return True

    def is_valid_v2(self, p):
        """Checks that the given project JSON dictionary contains
        a valid version 2 Spine Toolbox project. Valid meaning, that
        it contains all required keys and values are of the correct
        type.

        Args:
            p (dict): Project information JSON

        Returns:
            bool: True if project is a valid version 2 project, False if it is not
        """
        if "project" not in p.keys():
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'project' not found.")
            return False
        if "items" not in p.keys():
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'items' not found.")
            return False
        required_project_keys = ["version", "name", "description", "specifications", "connections"]
        project = p["project"]
        items = p["items"]
        if not isinstance(project, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'project' must be a dict.")
            return False
        if not isinstance(items, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'items' must be a dict.")
            return False
        for req_key in required_project_keys:
            if req_key not in project:
                self._toolbox.msg_error.emit("Invalid project.json file. Key {0} not found.".format(req_key))
                return False
        # Check types in project dict
        if not project["version"] == 2:
            self._toolbox.msg_error.emit("Invalid project version:'{0}'".format(project["version"]))
            return False
        if not isinstance(project["name"], str) or not isinstance(project["description"], str):
            self._toolbox.msg_error.emit("Invalid project.json file. 'name' and 'description' must be strings.")
            return False
        if not isinstance(project["specifications"], dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'specifications' must be a dictionary.")
            return False
        if not isinstance(project["connections"], list):
            self._toolbox.msg_error.emit("Invalid project.json file. 'connections' must be a list.")
            return False
        return True

    def is_valid_v3(self, p):
        """Checks that the given project JSON dictionary contains
        a valid version 3 Spine Toolbox project. Valid meaning, that
        it contains all required keys and values are of the correct
        type.

        Args:
            p (dict): Project information JSON

        Returns:
            bool: True if project is a valid version 2 project, False if it is not
        """
        if "project" not in p:
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'project' not found.")
            return False
        if "items" not in p:
            self._toolbox.msg_error.emit("Invalid project.json file. Key 'items' not found.")
            return False
        required_project_keys = ["version", "name", "description", "specifications", "connections"]
        project = p["project"]
        items = p["items"]
        if not isinstance(project, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'project' must be a dict.")
            return False
        if not isinstance(items, dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'items' must be a dict.")
            return False
        for req_key in required_project_keys:
            if req_key not in project:
                self._toolbox.msg_error.emit("Invalid project.json file. Key {0} not found.".format(req_key))
                return False
        # Check types in project dict
        if not project["version"] == 3:
            self._toolbox.msg_error.emit("Invalid project version:'{0}'".format(project["version"]))
            return False
        if not isinstance(project["name"], str) or not isinstance(project["description"], str):
            self._toolbox.msg_error.emit("Invalid project.json file. 'name' and 'description' must be strings.")
            return False
        if not isinstance(project["specifications"], dict):
            self._toolbox.msg_error.emit("Invalid project.json file. 'specifications' must be a dict.")
            return False
        if not isinstance(project["connections"], list):
            self._toolbox.msg_error.emit("Invalid project.json file. 'connections' must be a list.")
            return False
        return True

    def backup_project_file(self, project_dir):
        """Makes a backup copy of project.json file."""
        src = os.path.join(project_dir, ".spinetoolbox", PROJECT_FILENAME)
        dst = os.path.join(project_dir, ".spinetoolbox", "project.json.bak")
        try:
            shutil.copyfile(src, dst)
        except OSError:
            self._toolbox.msg_error.emit(f"Making a backup of '{src}' failed. Check permissions.")
            return False
        return True

    def force_save(self, p, project_dir):
        """Saves given project dictionary to project.json file.
        Used to force save project.json file when the project
        dictionary has been upgraded."""
        project_json_path = os.path.join(project_dir, ".spinetoolbox", PROJECT_FILENAME)
        try:
            with open(project_json_path, "w") as fp:
                json.dump(p, fp, indent=4)
        except OSError:
            self._toolbox.msg_error.emit("Saving project.json file failed. Check permissions.")
            return False
        return True


def _fix_1d_array_to_array(mappings):
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
