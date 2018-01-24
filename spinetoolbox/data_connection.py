#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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

import random
import logging
from metaobject import MetaObject
from widgets.subwindow_widget import SubWindowWidget
from PySide2.QtCore import Slot


class DataConnection(MetaObject):
    """Data Connection class.

    Attributes:
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
    """
    def __init__(self, name, description, project):
        super().__init__(name, description)
        self.item_type = "Data Connection"
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

    @Slot(name='edit_clicked')
    def edit_clicked(self):
        """Edit button clicked."""
        logging.debug(self.name + " Data: " + str(self._data))

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
