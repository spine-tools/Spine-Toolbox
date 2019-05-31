######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Spine Toolbox project class.

:authors: P. Savolainen (VTT), E. Rinne (VTT)
:date:   10.1.2018
"""

import os
import logging
import json
from PySide2.QtWidgets import QMessageBox
from metaobject import MetaObject
from helpers import project_dir, create_dir, copy_dir
from data_store import DataStore
from data_connection import DataConnection
from tool import Tool
from view import View
from tool_templates import JuliaTool, PythonTool, GAMSTool, ExecutableTool
from config import DEFAULT_WORK_DIR, INVALID_CHARS


class SpineToolboxProject(MetaObject):
    """Class for Spine Toolbox projects.

    Attributes:
        toolbox (ToolboxUI): toolbox of this project
        name (str): Project name
        description (str): Project description
        work_dir (str): Project work directory
        ext (str): Project save file extension(.proj)
    """

    def __init__(self, toolbox, name, description, work_dir=None, ext='.proj'):
        """Class constructor."""
        super().__init__(name, description)
        self._toolbox = toolbox
        self._qsettings = self._toolbox.qsettings()
        self.project_dir = os.path.join(project_dir(self._qsettings), self.short_name)
        if not work_dir:
            self.work_dir = DEFAULT_WORK_DIR
        else:
            self.work_dir = work_dir
        self.filename = self.short_name + ext
        self.path = os.path.join(project_dir(self._qsettings), self.filename)
        self.dirty = False  # TODO: Indicates if project has changed since loading
        # Make project directory
        try:
            create_dir(self.project_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating project directory {0} failed." " Check permissions.".format(self.project_dir)
            )
        # Make work directory
        try:
            create_dir(self.work_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating work directory {0} failed." " Check permissions.".format(self.work_dir)
            )

    def change_name(self, name):
        """Changes project name and updates project dir and save file name.

        Args:
            name (str): Project (long) name
        """
        super().set_name(name)
        # Update project dir instance variable
        self.project_dir = os.path.join(project_dir(self._qsettings), self.short_name)
        # Update file name and path
        self.change_filename(self.short_name + ".proj")

    def change_filename(self, new_filename):
        """Change the save filename associated with this project.

        Args:
            new_filename (str): Filename used in saving the project. No full path. Example 'project.proj'
        """
        self.filename = new_filename
        self.path = os.path.join(project_dir(self._qsettings), self.filename)

    def change_work_dir(self, new_work_path):
        """Change project work directory.

        Args:
            new_work_path (str): Absolute path to new work directory
        """
        if not new_work_path:
            self.work_dir = DEFAULT_WORK_DIR
            return False
        if not create_dir(new_work_path):
            return False
        self.work_dir = new_work_path
        return True

    def rename_project(self, name):
        """Save project under a new name. Used with File->Save As... menu command.
        Checks if given project name is valid.

        Args:
            name (str): New (long) name for project
        """
        # Check for illegal characters
        if name.strip() == '' or name.lower() == self.name.lower():
            self._toolbox.msg_warning.emit("Renaming project cancelled")
            return False
        # Check if new short name is the same as the current one
        new_short_name = name.lower().replace(" ", "_")
        if new_short_name == self.short_name:
            msg = "<b>{0}</b> project directory already taken.".format(new_short_name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Try again", msg)
            return False
        # Check that new name is legal
        if any(True for x in name if x in INVALID_CHARS):
            msg = "<b>{0}</b> contains invalid characters.".format(name)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Invalid characters", msg)
            return False
        # Check that the new project name directory is not taken
        projects_path = project_dir(self._qsettings)  # Path to directory where project files (.proj) are
        new_project_dir = os.path.join(projects_path, new_short_name)  # New project directory
        taken_dirs = list()
        dir_contents = [os.path.join(projects_path, x) for x in os.listdir(projects_path)]
        for path in dir_contents:
            if os.path.isdir(path):
                taken_dirs.append(os.path.split(path)[1])
        if new_short_name in taken_dirs:
            msg = "Project directory <b>{0}</b> already exists.".format(new_project_dir)
            # noinspection PyTypeChecker, PyArgumentList, PyCallByClass
            QMessageBox.information(self._toolbox, "Try again", msg)
            return False
        # Copy project directory to new project directory
        if not copy_dir(self._toolbox, self.project_dir, new_project_dir):
            self._toolbox.msg_error.emit("Copying project directory failed")
            return False
        # Change name
        self.change_name(name)
        return True

    def save(self, tool_def_paths):
        """Collect project information and objects
        into a dictionary and write to a JSON file.

        Args:
            tool_def_paths (list): List of paths to tool definition files
        """
        # Clear dictionary
        saved_dict = dict()  # This is written to JSON file
        project_dict = dict()  # Dictionary for storing project info
        project_dict['name'] = self.name
        project_dict['description'] = self.description
        project_dict['work_dir'] = self.work_dir
        project_dict['tool_templates'] = tool_def_paths
        connection_table = self._toolbox.connection_model.get_connections()
        from_to_conn_table = [
            [False if not j else (j.src_connector.position, j.dst_connector.position) for j in connection_table[i]]
            for i in range(len(connection_table))
        ]
        project_dict['connections'] = from_to_conn_table
        project_dict["scene_x"] = self._toolbox.ui.graphicsView.scene().sceneRect().x()
        project_dict["scene_y"] = self._toolbox.ui.graphicsView.scene().sceneRect().y()
        project_dict["scene_w"] = self._toolbox.ui.graphicsView.scene().sceneRect().width()
        project_dict["scene_h"] = self._toolbox.ui.graphicsView.scene().sceneRect().height()
        item_dict = dict()  # Dictionary for storing project items
        # Traverse all items in project model by category
        category_names = [category_item.name for category_item in self._toolbox.project_item_model.root().children()]
        for category in category_names:
            items = self._toolbox.project_item_model.items(category)
            item_dict[category] = dict()
            for item in items:
                # Save generic things common for all project items
                name = item.name
                item_dict[category][name] = dict()
                item_dict[category][name]["short name"] = item.short_name
                item_dict[category][name]["description"] = item.description
                x = item.get_icon().sceneBoundingRect().center().x()
                y = item.get_icon().sceneBoundingRect().center().y()
                item_dict[category][name]["x"] = x
                item_dict[category][name]["y"] = y
                # Save item type specific things
                if item.item_type == "Data Store":
                    item_dict[category][name]["url"] = item.url()
                elif item.item_type == "Data Connection":
                    item_dict[category][name]["references"] = item.file_references()
                elif item.item_type == "Tool":
                    if not item.tool_template():
                        item_dict[category][name]["tool"] = ""
                    else:
                        item_dict[category][name]["tool"] = item.tool_template().name
                    item_dict[category][name]["execute_in_work"] = item.execute_in_work
                elif item.item_type == "View":
                    pass
                else:
                    logging.error("Unrecognized item type: %s", item.item_type)
        # Save project to file
        saved_dict['project'] = project_dict
        saved_dict['objects'] = item_dict
        # Write into JSON file
        with open(self.path, 'w') as fp:
            json.dump(saved_dict, fp, indent=4)

    def load(self, item_dict):
        """Populate project item model with items loaded from project file.

        Args:
            item_dict (dict): Dictionary containing all project items in JSON format

        Returns:
            Boolean value depending on operation success.
        """
        data_stores = item_dict['Data Stores']
        data_connections = item_dict['Data Connections']
        tools = item_dict['Tools']
        views = item_dict['Views']
        n = len(data_stores.keys()) + len(data_connections.keys()) + len(tools.keys()) + len(views.keys())
        self._toolbox.msg.emit("Loading project items...")
        if n == 0:
            self._toolbox.msg_warning.emit("Project has no items")
        # Recreate Data Stores
        for name in data_stores.keys():
            desc = data_stores[name]['description']
            try:
                url = data_stores[name]["url"]
            except KeyError:
                # Keep compatibility with previous version
                try:
                    url = data_stores[name]["reference"]["url"]
                except KeyError:
                    url = None
            try:
                x = data_stores[name]["x"]
                y = data_stores[name]["y"]
            except KeyError:
                x = 0
                y = 0
            # logging.debug("{} - {} '{}' data:{}".format(name, short_name, desc, ref))
            self.add_data_store(name, desc, url, x, y, verbosity=False)
        # Recreate Data Connections
        for name in data_connections.keys():
            desc = data_connections[name]['description']
            try:
                refs = data_connections[name]["references"]
            except KeyError:
                refs = list()
            try:
                x = data_connections[name]["x"]
                y = data_connections[name]["y"]
            except KeyError:
                x = 0
                y = 0
            # logging.debug("{} - {} '{}' data:{}".format(name, short_name, desc, data))
            self.add_data_connection(name, desc, refs, x, y, verbosity=False)
        # Recreate Tools
        for name in tools.keys():
            desc = tools[name]['description']
            tool_name = tools[name]['tool']
            # Find tool template from model
            tool_template = self._toolbox.tool_template_model.find_tool_template(tool_name)
            # Clarifications for user
            if not tool_name == "" and not tool_template:
                self._toolbox.msg_error.emit(
                    "Tool <b>{0}</b> should have a Tool template <b>{1}</b> but "
                    "it was not found. Add it to Tool templates and reopen "
                    "project.".format(name, tool_name)
                )
            try:
                x = tools[name]["x"]
                y = tools[name]["y"]
            except KeyError:
                x = 0
                y = 0
            try:
                execute_in_work = tools[name]["execute_in_work"]  # boolean
            except KeyError:
                execute_in_work = True
            self.add_tool(name, desc, tool_template, execute_in_work, x, y, verbosity=False)
        # Recreate Views
        for name in views.keys():
            desc = views[name]['description']
            try:
                x = views[name]["x"]
                y = views[name]["y"]
            except KeyError:
                x = 0
                y = 0
            # logging.debug("{} - {} '{}' data:{}".format(name, short_name, desc, data))
            self.add_view(name, desc, x, y, verbosity=False)
        return True

    def load_tool_template_from_file(self, jsonfile):
        """Create a Tool template according to a tool definition file.

        Args:
            jsonfile (str): Path of the tool template definition file

        Returns:
            Instance of a subclass if Tool
        """
        try:
            with open(jsonfile, 'r') as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self._toolbox.msg_error.emit("Tool template definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._toolbox.msg_error.emit("Tool template definition file <b>{0}</b> not found".format(jsonfile))
            return None
        # Infer path to the main program
        try:
            includes_main_path = definition["includes_main_path"]  # path to main program relative to definition file
        except KeyError:
            includes_main_path = "."  # assume main program and definition file are on the same path
        path = os.path.normpath(os.path.join(os.path.dirname(jsonfile), includes_main_path))
        return self.load_tool_template_from_dict(definition, path)

    def load_tool_template_from_dict(self, definition, path):
        """Create a Tool template according to a dictionary.

        Args:
            definition (dict): Dictionary with the tool definition
            path (str): Folder of the main program file

        Returns:
            Instance of a subclass if Tool
        """
        try:
            _tooltype = definition["tooltype"].lower()
        except KeyError:
            self._toolbox.msg_error.emit(
                "No tool type defined in tool definition file. Supported types are " "'gams', 'julia' and 'executable'"
            )
            return None
        if _tooltype == "julia":
            return JuliaTool.load(self._toolbox, path, definition)
        if _tooltype == "python":
            return PythonTool.load(self._toolbox, path, definition)
        elif _tooltype == "gams":
            return GAMSTool.load(self._toolbox, path, definition)
        elif _tooltype == "executable":
            return ExecutableTool.load(self._toolbox, path, definition)
        else:
            self._toolbox.msg_warning.emit("Tool type <b>{}</b> not available".format(_tooltype))
            return None

    def add_data_store(self, name, description, reference, x=0, y=0, set_selected=False, verbosity=True):
        """Adds a Data Store to project item model.

        Args:
            name (str): Name
            description (str): Description of item
            reference (dict): Information on referenced database
            x (int): X coordinate of item on scene
            y (int): Y coordinate of item on scene
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        category = "Data Stores"
        data_store = DataStore(self._toolbox, name, description, reference, x, y)
        ds_category = self._toolbox.project_item_model.find_category(category)
        self._toolbox.project_item_model.insert_item(data_store, ds_category)
        # Append connection model
        self.append_connection_model(name, category)
        if verbosity:
            self._toolbox.msg.emit("Data Store <b>{0}</b> added to project.".format(name))
        if set_selected:
            self.set_item_selected(data_store)

    def add_data_connection(self, name, description, references, x=0, y=0, set_selected=False, verbosity=True):
        """Adds a Data Connection to project item model.

        Args:
            name (str): Name
            description (str): Description of item
            references (list(str)): List of file paths
            x (int): X coordinate of item on scene
            y (int): Y coordinate of item on scene
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        category = "Data Connections"
        data_connection = DataConnection(self._toolbox, name, description, references, x, y)
        dc_category = self._toolbox.project_item_model.find_category(category)
        self._toolbox.project_item_model.insert_item(data_connection, dc_category)
        # Append connection model
        self.append_connection_model(name, category)
        if verbosity:
            self._toolbox.msg.emit("Data Connection <b>{0}</b> added to project.".format(name))
        if set_selected:
            self.set_item_selected(data_connection)

    def add_tool(self, name, description, tool_template, use_work=True, x=0, y=0, set_selected=False, verbosity=True):
        """Adds a Tool to project item model.

        Args:
            name (str): Name
            description (str): Description of item
            tool_template (ToolTemplate): Tool template of this tool
            use_work (bool): Execute in work directory
            x (int): X coordinate of item on scene
            y (int): Y coordinate of item on scene
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        category = "Tools"
        tool = Tool(self._toolbox, name, description, tool_template, use_work, x, y)
        tool_category = self._toolbox.project_item_model.find_category(category)
        self._toolbox.project_item_model.insert_item(tool, tool_category)
        # Append connection model
        self.append_connection_model(name, category)
        if verbosity:
            self._toolbox.msg.emit("Tool <b>{0}</b> added to project.".format(name))
        if set_selected:
            self.set_item_selected(tool)

    def add_view(self, name, description, x=0, y=0, set_selected=False, verbosity=True):
        """Adds a View to project item model.

        Args:
            name (str): Name
            description (str): Description of item
            x (int): X coordinate of item on scene
            y (int): Y coordinate of item on scene
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        category = "Views"
        view = View(self._toolbox, name, description, x, y)
        view_category = self._toolbox.project_item_model.find_category(category)
        self._toolbox.project_item_model.insert_item(view, view_category)
        # Append connection model
        self.append_connection_model(name, category)
        if verbosity:
            self._toolbox.msg.emit("View <b>{0}</b> added to project.".format(name))
        if set_selected:
            self.set_item_selected(view)

    def append_connection_model(self, item_name, category):
        """Adds new item to connection model to keep project and connection model synchronized."""
        row_in_con_model = self._toolbox.project_item_model.new_item_index(category)
        self._toolbox.connection_model.append_item(item_name, row_in_con_model)

    def set_item_selected(self, item):
        """Sets item selected and shows its info screen.

        Args:
            item (ProjectItem): Project item to select
        """
        ind = self._toolbox.project_item_model.find_item(item.name)
        self._toolbox.ui.treeView_project.setCurrentIndex(ind)
