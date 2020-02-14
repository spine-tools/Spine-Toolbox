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
A widget for presenting basic information about the application.

:author: P. Savolainen (VTT)
:date: 14.12.2017
"""

from PySide2.QtWidgets import QWidget
from PySide2.QtCore import Qt, QPoint
from PySide2.QtGui import QTextCursor
import spinedb_api
import spine_engine
from spinetoolbox import __version__, __version_info__


class AboutWidget(QWidget):
    """About widget class."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        from ..ui import about

        super().__init__(parent=toolbox, f=Qt.Popup)  # Setting the parent inherits the stylesheet
        self._toolbox = toolbox
        # Set up the user interface from Designer file.
        self.ui = about.Ui_Form()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.Popup)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        full_version = (
            str(__version_info__.major)
            + "."
            + str(__version_info__.minor)
            + "."
            + str(__version_info__.micro)
            + "."
            + __version_info__.releaselevel
            + "."
            + str(__version_info__.serial)
        )
        self.ui.label_spine_toolbox.setText("Spine Toolbox<br/>v{0}<br/>{1}".format(__version__, full_version))
        self.ui.label_spinedb_api.setText("spinedb_api<br/>v{0}".format(spinedb_api.__version__))
        self.ui.label_spine_engine.setText("spine_engine<br/>v{0}".format(spine_engine.__version__))
        self.setup_license_text()
        self._mousePressPos = None
        self._mouseReleasePos = None
        self._mouseMovePos = None
        # Move About Popup to correct position
        pos = self.calc_pos()
        self.move(pos)

    def calc_pos(self):
        """Calculate the top-left corner position of this widget in relation to main window
        position and size in order to show about window in the middle of the main window."""
        mw_center = self.parent().frameGeometry().center()
        about_x = mw_center.x() - self.frameGeometry().width() / 2
        about_y = mw_center.y() - self.frameGeometry().height() / 2
        about_topleft = QPoint(about_x, about_y)
        return about_topleft

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

    def mousePressEvent(self, e):
        """Save mouse position at the start of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mousePressPos = e.globalPos()
        self._mouseMovePos = e.globalPos()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        """Save mouse position at the end of dragging.

        Args:
            e (QMouseEvent): Mouse event
        """
        if self._mousePressPos is not None:
            self._mouseReleasePos = e.globalPos()
            moved = self._mouseReleasePos - self._mousePressPos
            if moved.manhattanLength() > 3:
                e.ignore()
                return

    def mouseMoveEvent(self, e):
        """Moves the window when mouse button is pressed and mouse cursor is moved.

        Args:
            e (QMouseEvent): Mouse event
        """
        # logging.debug("MouseMoveEvent at pos:%s" % e.pos())
        # logging.debug("MouseMoveEvent globalpos:%s" % e.globalPos())
        currentpos = self.pos()
        globalpos = e.globalPos()
        diff = globalpos - self._mouseMovePos
        newpos = currentpos + diff
        self.move(newpos)
        self._mouseMovePos = globalpos
