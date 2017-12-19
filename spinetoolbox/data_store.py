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
Module for data store class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   18.12.2017
"""

import random
import logging
from metaobject import MetaObject
from widgets.subwindow_widget import SubWindowWidget
from PySide2.QtCore import Slot


class DataStore(MetaObject):
    """Data Store class.

    Attributes:
        parent (QWidget): Parent of data stores widget
        name (str): Object name
        description (str): Object description
    """
    def __init__(self, parent, name, description):
        super().__init__(name, description)
        self._widget = SubWindowWidget(parent, name)
        self._data = random.randint(1, 100)
        self._widget.update_name_label(name + " " + str(random.randint(1, 10)))
        self._widget.update_data_label("Data:" + str(self._data))
        self.connect_signals()

    def connect_signals(self):
        """Connect this data store's signals to slots."""
        self._widget.edit_button.clicked.connect(self.edit_clicked)

    def widget(self):
        return self._widget

    @Slot(name='edit_clicked')
    def edit_clicked(self):
        """Edit button clicked."""
        logging.debug(self.name + " Data: " + str(self._data))
