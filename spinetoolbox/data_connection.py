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
Module for data connection class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import logging
from metaobject import MetaObject
from widgets.subwindow_widget import SubWindowWidget
from PySide2.QtCore import Slot


class DataConnection(MetaObject):
    """Data Connection class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
    """
    def __init__(self, parent, name, description, project):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "Data Connection"
        self.item_category = "Data Connections"
        self._project = project
        self._data = list()
        self._widget = SubWindowWidget(name, self.item_type)
        self._widget.set_type_label(self.item_type)
        self._widget.set_name_label(name)
        self._widget.set_data_label("Data")
        self.connect_signals()

    def connect_signals(self):
        """Connect this data connection's signals to slots."""
        self._widget.ui.pushButton_edit.clicked.connect(self.edit_clicked)
        self._widget.ui.pushButton_connections.clicked.connect(self.show_connections)

    @Slot(name='edit_clicked')
    def edit_clicked(self):
        """Edit button clicked."""
        logging.debug(self.name + " Data: " + str(self._data))

    @Slot(name="show_connections")
    def show_connections(self):
        """Show connections of this item."""
        inputs = self._parent.connection_model.input_items(self.name)
        outputs = self._parent.connection_model.output_items(self.name)
        self._parent.msg.emit("<br/><b>{0}</b>".format(self.name))
        self._parent.msg.emit("Input items")
        if not inputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in inputs:
                self._parent.msg_warning.emit("{0}".format(item))
        self._parent.msg.emit("Output items")
        if not outputs:
            self._parent.msg_warning.emit("None")
        else:
            for item in outputs:
                self._parent.msg_warning.emit("{0}".format(item))

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    def set_data(self, d):
        """Set data and update widgets representation of data."""
        self._data = d
        self._widget.set_data_label("Data:" + str(self._data))

    def get_data(self):
        """Returns data of object."""
        return self._data
