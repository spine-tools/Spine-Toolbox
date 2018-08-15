#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Spine Toolbox project class.

:authors: Pekka Savolainen <pekka.t.savolainen@vtt.fi>, Erkka Rinne <erkka.rinne@vtt.fi>
:date:   10.1.2018
"""

import os
import logging
import json
from PySide2.QtCore import Qt
from metaobject import MetaObject
from helpers import project_dir, create_dir
from data_store import DataStore
from data_connection import DataConnection
from tool import Tool
from view import View
from tool_templates import GAMSTool, JuliaTool
from config import DEFAULT_WORK_DIR


class SpineToolboxProject(MetaObject):
    """Class for Spine Toolbox projects.

    Attributes:
        parent(ToolboxUI): Parent of this project
        name(str): Project name
        description(str): Project description
        work_dir (str): Project work directory
        ext(str): Project save file extension(.proj)
    """
    def __init__(self, parent, name, description, configs, work_dir, ext='.proj'):
        """Class constructor."""
        super().__init__(name, description)
        self._parent = parent
        self._configs = configs
        self.project_dir = os.path.join(project_dir(self._configs), self.short_name)
        if not work_dir:
            self.work_dir = DEFAULT_WORK_DIR
        else:
            self.work_dir = work_dir
        self.filename = self.short_name + ext
        self.path = os.path.join(project_dir(self._configs), self.filename)
        self.dirty = False  # TODO: Indicates if project has changed since loading
        self.project_contents = dict()
        # Make project directory
        try:
            create_dir(self.project_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating project directory {0} failed."
                                        " Check permissions.".format(self.project_dir))
        # Make work directory
        try:
            create_dir(self.work_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating work directory {0} failed."
                                        " Check permissions.".format(self.work_dir))

    def set_name(self, name):
        """Change project name. Calls superclass method.

        Args:
            name (str): Project name
        """
        super().set_name(name)

    def set_description(self, desc):
        """Change project description. Calls superclass method.

        Args:
            desc (str): Project description
        """
        super().set_description(desc)

    def change_filename(self, new_filename):
        """Change the save filename associated with this project.

        Args:
            new_filename (str): Filename used in saving the project. No full path. Example 'project.proj'
        """
        # TODO: Add check that file extension is supported (.proj)
        self.filename = new_filename
        self.path = os.path.join(project_dir(self._configs), self.filename)

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
        connection_table = self._parent.connection_model.get_connections()
        bool_con_table = [[False if not j else True for j in connection_table[i]] for i in range(len(connection_table))]
        project_dict['connections'] = bool_con_table
        project_dict["scene_x"] = self._parent.ui.graphicsView.scene().sceneRect().x()
        project_dict["scene_y"] = self._parent.ui.graphicsView.scene().sceneRect().y()
        project_dict["scene_w"] = self._parent.ui.graphicsView.scene().sceneRect().width()
        project_dict["scene_h"] = self._parent.ui.graphicsView.scene().sceneRect().height()
        item_dict = dict()  # Dictionary for storing project items
        n = 0
        # Traverse all items in project model
        top_level_items = self._parent.project_item_model.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            top_level_item_txt = top_level_item.data(Qt.DisplayRole)
            # logging.debug("Children of {0}".format(top_level_item.data(Qt.DisplayRole)))
            item_dict[top_level_item_txt] = dict()
            if top_level_item.hasChildren():
                n_children = top_level_item.rowCount()
                for i in range(n_children):
                    n += 1
                    child = top_level_item.child(i, 0)
                    child_data = child.data(Qt.UserRole)
                    name = child_data.name
                    # logging.debug("{0}".format(child.data(Qt.DisplayRole)))
                    item_dict[top_level_item_txt][name] = dict()
                    item_dict[top_level_item_txt][name]["short name"] = child_data.short_name
                    item_dict[top_level_item_txt][name]["description"] = child_data.description
                    x = child_data.get_icon().master().sceneBoundingRect().center().x()
                    y = child_data.get_icon().master().sceneBoundingRect().center().y()
                    item_dict[top_level_item_txt][name]["x"] = x
                    item_dict[top_level_item_txt][name]["y"] = y
                    if child_data.item_type == "Tool":
                        if not child_data.tool_template():
                            item_dict[top_level_item_txt][name]["tool"] = ""
                        else:
                            item_dict[top_level_item_txt][name]["tool"] = child_data.tool_template().name
                    elif child_data.item_type == "Data Connection":
                        # Save references
                        item_dict[top_level_item_txt][name]["references"] = child_data.file_references()
                    elif child_data.item_type == "Data Store":
                        item_dict[top_level_item_txt][name]["references"] = child_data.data_references()
                    elif child_data.item_type == "View":
                        item_dict[top_level_item_txt][name]["data"] = child_data.get_data()
                    else:
                        logging.error("Unrecognized item type: {0}".format(child_data.item_type))
        # Save project stuff
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
        self._parent.msg.emit("Loading project items...")
        # Recreate Data Stores
        for name in data_stores.keys():
            short_name = data_stores[name]['short name']
            desc = data_stores[name]['description']
            try:
                refs = data_stores[name]["references"]
            except KeyError:
                refs = list()
            try:
                x = data_stores[name]["x"]
                y = data_stores[name]["y"]
            except KeyError:
                x = 0
                y = 0
            # logging.debug("{} - {} '{}' data:{}".format(name, short_name, desc, refs))
            self.add_data_store(name, desc, refs, x, y)
        # Recreate Data Connections
        for name in data_connections.keys():
            short_name = data_connections[name]['short name']
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
            self.add_data_connection(name, desc, refs, x, y)
        # Recreate Tools
        for name in tools.keys():
            short_name = tools[name]['short name']
            desc = tools[name]['description']
            tool_name = tools[name]['tool']
            # Find tool template from model
            tool_template = self._parent.tool_template_model.find_tool_template(tool_name)
            # Clarifications for user
            if not tool_name == "" and not tool_template:
                self._parent.msg_error.emit("Tool <b>{0}</b> should have a Tool template <b>{1}</b> but "
                                            "it was not found. Add it to Tool templates and reopen "
                                            "project.".format(name, tool_name))
            try:
                x = tools[name]["x"]
                y = tools[name]["y"]
            except KeyError:
                x = 0
                y = 0
            self.add_tool(name, desc, tool_template, x, y)
        # Recreate Views
        for name in views.keys():
            short_name = views[name]['short name']
            desc = views[name]['description']
            try:
                data = views[name]['data']
            except KeyError:
                logging.error("'data' keyword not found in View {0}".format(name))
                data = ''
            try:
                x = views[name]["x"]
                y = views[name]["y"]
            except KeyError:
                x = 0
                y = 0
            # logging.debug("{} - {} '{}' data:{}".format(name, short_name, desc, data))
            self.add_view(name, desc, x, y, data)
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
                    self._parent.msg_error.emit("Tool template definition file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self._parent.msg_error.emit("Tool template definition file <b>{0}</b> not found".format(jsonfile))
            return None
        # Infer path to the main program
        try:
            includes_main_path = definition['includes_main_path'] # path to main program relative to definition file
        except KeyError:
            includes_main_path = "."    # assume main program and definition file are on the same path
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
            _tooltype = definition['tooltype'].lower()
        except KeyError:
            self._parent.msg_error.emit("No type of tool defined in tool definition file. Should be "
                                        "GAMS, Julia or executable")
            return None
        if _tooltype == "gams":
            return GAMSTool.load(self._parent, path, definition)
        elif _tooltype == "julia":
            return JuliaTool.load(self._parent, path, definition)
        elif _tooltype == 'executable':
            self._parent.msg_warning.emit("Executable tools not supported yet")
            return None
        else:
            self._parent.msg_warning.emit("Tool type <b>{}</b> not available".format(_tooltype))
            return None

    def add_data_store(self, name, description, references, x=0, y=0):
        """Add data store to project item model."""
        data_store = DataStore(self._parent, name, description, self, references, x, y)
        self._parent.project_refs.append(data_store)  # Save reference or signals don't stick
        self._parent.add_item_to_model("Data Stores", name, data_store)
        self._parent.msg.emit("Data Store <b>{0}</b> added to project.".format(name))

    def add_data_connection(self, name, description, references, x=0, y=0):
        """Add Data Connection to project item model."""
        data_connection = DataConnection(self._parent, name, description, self, references, x, y)
        self._parent.project_refs.append(data_connection)  # Save reference or signals don't stick
        self._parent.add_item_to_model("Data Connections", name, data_connection)
        self._parent.msg.emit("Data Connection <b>{0}</b> added to project.".format(name))

    def add_tool(self, name, description, tool_template, x=0, y=0):
        """Add Tool to project item model."""
        tool = Tool(self._parent, name, description, self, tool_template, x, y)
        self._parent.project_refs.append(tool)  # Save reference or signals don't stick
        self._parent.add_item_to_model("Tools", name, tool)
        self._parent.msg.emit("Tool <b>{0}</b> added to project.".format(name))

    def add_view(self, name, description, x=0, y=0, data="View data"):
        """Add View to project item model."""
        view = View(self._parent, name, description, self, x, y)
        view.set_data(data)
        self._parent.project_refs.append(view)  # Save reference or signals don't stick
        self._parent.add_item_to_model("Views", name, view)
        self._parent.msg.emit("View <b>{0}</b> added to project.".format(name))
        self._parent.msg_warning.emit("<b>Not implemented</b>. The functionality for View items is not "
                                      "implemented yet.")
