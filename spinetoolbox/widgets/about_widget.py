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
A widget for presenting basic information about the application.

@author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
@date 14.12.2017
"""

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor
import ui.about


class AboutWidget(QWidget):
    """About QWidget class."""

    def __init__(self, parent, version):
        """Initializes About widget.

        Params:
            parent (QWidget): Parent widget
            version (str): Application version number
        """
        self._parent = parent
        super().__init__(f=Qt.Window)
        # Set up the user interface from Designer file.
        self.ui = ui.about.Ui_Form()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.CustomizeWindowHint)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.label_version_str.setText("v{0}".format(version))
        self.setup_license_text()

    def setup_license_text(self):
        """Add license to QTextBrowser."""
        license_html = """<p align="center">GNU Lesser General Public License</p>
              <p>This program is free software: you can redistribute it \
              and/or modify it under the terms of the GNU Lesser General Public \
              License as published by the Free Software Foundation, either \
              version 3 of the License, or (at your option) any later version. </p>\
              <p>This program is distributed in the hope that it will be useful, but \
              WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY \
              or FITNESS FOR A PARTICULAR PURPOSE.</p> \
              <p> See the GNU Lesser General Public License for more details. \
              You should have received a copy of the GNU Lesser General Public \
              License along with this program. If not, see
              <a href="http://www.gnu.org/licenses/">http://www.gnu.org/licenses/</a>.</p>"""
        self.ui.textBrowser.insertHtml(license_html)
        self.ui.textBrowser.moveCursor(QTextCursor.Start)

    def keyPressEvent(self, e):
        """Close form when Escape, Enter, Return, or Space bar keys are pressed.

        Args:
            e (QKeyEvent): Received key press event.
        """
        if e.key() == Qt.Key_Escape or e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return or e.key() == Qt.Key_Space:
            self.close()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
