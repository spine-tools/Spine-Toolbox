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
Module for tool class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import logging
from metaobject import MetaObject
from widgets.sw_tool_widget import ToolSubWindowWidget
from PySide2.QtCore import Slot


class Tool(MetaObject):
    """Tool class.

    Attributes:
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
        tool_candidate (ToolCandidate): Tool of this Tool
    """
    def __init__(self, name, description, project, tool_candidate):
        super().__init__(name, description)
        self.item_type = "Tool"
        self._project = project
        self._widget = ToolSubWindowWidget(name, self.item_type)
        self._widget.set_name_label(name)
        self._tool = self.set_tool(tool_candidate)
        self.connect_signals()

    def connect_signals(self):
        """Connect this tool's signals to slots."""
        self._widget.ui.pushButton_details.clicked.connect(self.show_details)
        self._widget.ui.pushButton_execute.clicked.connect(self.execute)
        self._widget.ui.pushButton_x.clicked.connect(self.remove_tool)

    @Slot(name='show_details')
    def show_details(self):
        """Details button clicked."""
        logging.debug(self.name + " - Tool: " + str(self._tool))

    @Slot(name='execute')
    def execute(self):
        """Execute button clicked."""
        logging.debug("Executing: {0}".format(self.name))

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def tool(self):
        """Return Tool candidate."""
        return self._tool

    @Slot(name='remove_tool')
    def remove_tool(self):
        """Remove Tool from this Tool."""
        self._tool = self.set_tool(None)

    def set_tool(self, tool_candidate):
        """Set tool candidate for this Tool. Remove tool candidate by giving None as argument.

        Args:
            tool_candidate (ToolCandidate): Candidate for this Tool. None removes the candidate.

        Returns:
            ToolCandidate or None if no Tool Candidate set for this Tool.
        """
        if not tool_candidate:
            self._widget.ui.lineEdit_tool.setText("")
            self._widget.ui.lineEdit_tool_args.setText("")
            return None
        else:
            self._widget.ui.lineEdit_tool.setText(tool_candidate.name)
            self._widget.ui.lineEdit_tool_args.setText(tool_candidate.cmdline_args)
            return tool_candidate
