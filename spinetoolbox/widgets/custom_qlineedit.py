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
Classes for custom line edits.

:author: M. Marin (KTH)
:date:   11.10.2018
"""

import os
from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QLineEdit


class CustomQLineEdit(QLineEdit):
    """A custom QLineEdit that accepts file drops and displays the path.

    Attributes:
        parent (QMainWindow): Parent for line edit widget (DataStoreWidget)
    """

    file_dropped = Signal("QString", name="file_dropped")

    def dragEnterEvent(self, event):
        """Accept a single file drop from the filesystem."""
        urls = event.mimeData().urls()
        if len(urls) > 1:
            event.ignore()
            return
        url = urls[0]
        if not url.isLocalFile():
            event.ignore()
            return
        if not os.path.isfile(url.toLocalFile()):
            event.ignore()
            return
        event.accept()
        event.setDropAction(Qt.LinkAction)

    def dragMoveEvent(self, event):
        """Accept event."""
        event.accept()

    def dropEvent(self, event):
        """Emit file_dropped signal with the file for the dropped url."""
        url = event.mimeData().urls()[0]
        self.file_dropped.emit(url.toLocalFile())
