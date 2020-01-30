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

import logging
import os
import json
from PySide2.QtWidgets import QFileDialog, QMessageBox
from .config import LATEST_PROJECT_VERSION
from .helpers import create_dir, recursive_overwrite, serialize_path


class ProjectUpgrader:
    """Class to upgrade/convert projects from earlier versions to the current version."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): toolbox of this project
        """
        self._toolbox = toolbox

    def is_valid(self, p):
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

    def upgrade(self, project_dict, old_project_dir, new_project_dir):
        """Converts the project described in given project description file to the latest version.

        Args:
            project_dict (dict): Full path to project description file, ie. .proj or .json
            old_project_dir (str): Path to the original project directory
            new_project_dir (str): New project directory

        Returns:
            dict: Latest version of the project info dictionary
        """
        try:
            v = project_dict["project"]["version"]
        except KeyError:
            return self.upgrade_from_no_version_to_version_1(project_dict, old_project_dir, new_project_dir)
        return self.upgrade_to_latest(v, project_dict)

    @staticmethod
    def upgrade_to_latest(v, project_dict):
        """Upgrades the given project dictionary to the latest version.

        NOTE: Implement this when the structure of the project file needs
        to be changed.

        Args:
            v (int): project version
            project_dict (dict): Project JSON to be converted

        Returns:
            dict: Upgraded project information JSON
        """
        logging.debug(
            "Implementation of upgrading project JSON from version %s->%s is missing", v, LATEST_PROJECT_VERSION
        )
        raise NotImplementedError()

    def upgrade_from_no_version_to_version_1(self, old, old_project_dir, new_project_dir):
        """Converts project information dictionaries without 'version' to version 1.

        Args:
            old (dict): Project information JSON
            old_project_dir (str): Path to old project directory
            new_project_dir (str): Path to new project directory

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
        new["tool_specifications"] = self.upgrade_tool_specification_paths(spec_paths, old_project_dir)
        # Old projects may have obsolete category names that need to be updated
        if "Data Interfaces" in old["objects"].keys():
            old["objects"]["Importers"] = old["objects"]["Data Interfaces"]
            old["objects"].pop("Data Interfaces")
        if "Data Exporters" in old["objects"].keys():
            old["objects"]["Exporters"] = old["objects"]["Data Exporters"]
            old["objects"].pop("Data Exporters")
        # Get all item names to a list from old project dict. Needed for upgrading connections.
        item_names = list()
        for category_name in old["objects"]:
            if category_name not in self._toolbox.categories:
                continue
            for item_name, item_dict in old["objects"][category_name].items():
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
        for category_name in old["objects"]:
            if category_name not in self._toolbox.categories:
                self._toolbox.msg_error.emit(
                    "Upgrading project item's to category '{}' failed. Unknown category.".format(category_name)
                )
                continue
            item_class = self._toolbox.categories[category_name]["item_maker"]
            for item_name, item_dict in old["objects"][category_name].items():
                new_item_dict = item_class.upgrade_from_no_version_to_version_1(item_name, item_dict, old_project_dir)
                new_objects[category_name][item_name] = new_item_dict
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
    def upgrade_tool_specification_paths(spec_paths, old_project_dir):
        """Upgrades a list of tool specifications paths to new format.
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
            dict: Upgraded project information JSON or None if the operation failed
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
