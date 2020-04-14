######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Tool plugin.

:author: M. Marin (KTH)
:date:   12.9.2019
"""

import os
from PySide2.QtCore import QUrl
from PySide2.QtGui import QDesktopServices
from spinetoolbox.project_tree_item import CategoryProjectTreeItem
from .tool import Tool
from .tool_icon import ToolIcon
from .tool_specifications import JuliaTool, PythonTool, GAMSTool, ExecutableTool
from .widgets.tool_properties_widget import ToolPropertiesWidget
from .widgets.tool_specification_widget import ToolSpecificationWidget
from .widgets.add_tool_widget import AddToolWidget
from .widgets.custom_menus import ToolSpecificationMenu


class ToolCategory(CategoryProjectTreeItem):
    def __init__(self, toolbox, settings, logger):
        super().__init__(toolbox, settings, logger, "Tools", "Some meaningful description.")

    def make_properties_ui(self):
        return ToolPropertiesWidget(self._toolbox).ui

    @staticmethod
    def rank():
        return 2

    @staticmethod
    def icon():
        return ":/icons/project_item_icons/hammer.svg"

    @staticmethod
    def item_type():
        return "Tool"

    @property
    def item_maker(self):
        return Tool

    @property
    def icon_maker(self):
        return ToolIcon

    @property
    def add_form_maker(self):
        return AddToolWidget

    @staticmethod
    def supports_specifications():
        return True

    def make_specification_form(self, spec):
        return ToolSpecificationWidget(self._toolbox, spec)

    def make_specification_menu(self, ind):
        return ToolSpecificationMenu(self._toolbox, ind)

    def load_specification(self, definition, def_path):
        """See base class."""
        includes_main_path = definition.get("includes_main_path", ".")
        path = os.path.normpath(os.path.join(os.path.dirname(def_path), includes_main_path))
        try:
            _tooltype = definition["tooltype"].lower()
        except KeyError:
            self._logger.msg_error.emit(
                "No tool type defined in tool definition file. Supported types "
                "are 'python', 'gams', 'julia' and 'executable'"
            )
            return None
        spec = self._do_load_specification(_tooltype, path, definition)
        if not spec:
            return None
        spec.set_def_path(def_path)
        return spec

    def _do_load_specification(self, _tooltype, path, definition):
        if _tooltype == "julia":
            return JuliaTool.load(path, definition, self._settings, self._toolbox.julia_repl, self._logger)
        if _tooltype == "python":
            return PythonTool.load(path, definition, self._settings, self._toolbox.python_repl, self._logger)
        if _tooltype == "gams":
            return GAMSTool.load(path, definition, self._settings, self._logger)
        if _tooltype == "executable":
            return ExecutableTool.load(path, definition, self._settings, self._logger)
        self._logger.msg_warning.emit("Tool type <b>{}</b> not available".format(_tooltype))
        return None

    def open_main_program_file(self, spec):
        """Open the tool specification's main program file in the default editor.

        Args:
            spec (ToolSpecification)
        """
        file_path = os.path.join(spec.path, spec.includes[0])
        # Check if file exists first. openUrl may return True even if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            self._logger.msg_error.emit("Tool main program file <b>{0}</b> not found.".format(file_path))
            return
        ext = os.path.splitext(os.path.split(file_path)[1])[1]
        if ext in [".bat", ".exe"]:
            self._logger.msg_warning.emit(
                "Sorry, opening files with extension <b>{0}</b> not supported. "
                "Please open the file manually.".format(ext)
            )
            return
        main_program_url = "file:///" + file_path
        # Open Tool specification main program file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(main_program_url, QUrl.TolerantMode))
        if not res:
            filename, file_extension = os.path.splitext(file_path)
            self._logger.msg_error.emit(
                "Unable to open Tool specification main program file {0}. "
                "Make sure that <b>{1}</b> "
                "files are associated with an editor. E.g. on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(filename, file_extension)
            )
