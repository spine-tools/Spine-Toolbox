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
Exporter properties widget.

:author: A. Soininen (VTT)
:date:   25.9.2019
"""

from PySide2.QtWidgets import QWidget


class ExporterProperties(QWidget):
    """A main window widget to show Gdx Export item's properties."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): a main window instance
        """
        from ..ui.exporter_properties import Ui_Form

        super().__init__()
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Exporter")

    @property
    def ui(self):
        """The UI form of this widget."""
        return self._ui
