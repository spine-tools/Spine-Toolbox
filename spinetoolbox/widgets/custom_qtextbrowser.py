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
Class for a custom QTextBrowser to add options to context menu.

:author: P. Savolainen (VTT)
:date:   6.2.2018
"""

from PySide2.QtWidgets import QTextBrowser, QAction


class CustomQTextBrowser(QTextBrowser):
    """Custom QTextBrowser class.

    Attributes:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent):
        super().__init__(parent=parent)
        # self._parent = parent  # Is this needed?

    def contextMenuEvent(self, event):
        """Reimplemented method to add a clear action into the default context menu.

        Args:
            event (QContextMenuEvent): Received event
        """
        clear_action = QAction("Clear", self)
        # noinspection PyUnresolvedReferences
        clear_action.triggered.connect(lambda: self.clear())
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        menu.addAction(clear_action)
        menu.exec_(event.globalPos())
