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
Module for view class.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   19.12.2017
"""

import logging
import os
from metaobject import MetaObject
from widgets.view_subwindow_widget import ViewWidget
from PySide2.QtCore import Slot
from graphics_items import ViewImage
from helpers import create_dir


class View(MetaObject):
    """View class.

    Attributes:
        parent (ToolboxUI): QMainWindow instance
        name (str): Object name
        description (str): Object description
        project (SpineToolboxProject): Project
    """
    def __init__(self, parent, name, description, project, x, y):
        super().__init__(name, description)
        self._parent = parent
        self.item_type = "View"
        self.item_category = "Views"
        self._project = project
        self._data = "data"
        self._widget = ViewWidget(self.item_type)
        self._widget.set_type_label(self.item_type)
        self._widget.set_name_label(name)
        self._widget.set_data_label(self._data)
        # Create View project directory
        self.data_dir = os.path.join(self._project.project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._parent.msg_error.emit("[OSError] Creating directory {0} failed."
                                        " Check permissions.".format(self.data_dir))
        self._graphics_item = ViewImage(self._parent, x - 35, y - 35, 70, 70, self.name)
        self.connect_signals()

    def connect_signals(self):
        """Connect this view's signals to slots."""
        self._widget.ui.pushButton_info.clicked.connect(self.info_clicked)

    def set_icon(self, icon):
        """Set icon."""
        self._graphics_item = icon

    def get_icon(self):
        """Returns the item representing this data connection in the scene."""
        return self._graphics_item

    def get_widget(self):
        """Returns the graphical representation (QWidget) of this object."""
        return self._widget

    @Slot(name='info_clicked')
    def info_clicked(self):
        """Info button clicked."""
        logging.debug(self.name + " - " + str(self._data))

    def set_data(self, d):
        """Set data and update widgets representation of data."""
        self._data = d
        self._widget.set_data_label("Data:" + str(self._data))

    def get_data(self):
        """Returns data of object."""
        return self._data
