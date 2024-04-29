######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""A widget for presenting basic information about the application."""
import os
import sys
import platform
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, Slot
from PySide6.QtGui import QTextCursor
import spinetoolbox
import spinedb_api
import spine_engine
import spine_items


class AboutWidget(QWidget):
    """About widget class."""

    def __init__(self, toolbox):
        """

        Args:
            toolbox (ToolboxUI): QMainWindow instance
        """
        from ..ui import about  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolbox, f=Qt.Popup)  # Setting the parent inherits the stylesheet
        self._toolbox = toolbox
        # Set up the user interface from Designer file.
        self.ui = about.Ui_Form()
        self.ui.setupUi(self)
        self.ui.toolButton_copy_to_clipboard.clicked.connect(self.copy_to_clipboard)
        self.setWindowFlags(Qt.WindowType.Popup)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        full_version = (
            str(spinetoolbox.__version_info__.major)
            + "."
            + str(spinetoolbox.__version_info__.minor)
            + "."
            + str(spinetoolbox.__version_info__.micro)
            + "-"
            + spinetoolbox.__version_info__.releaselevel
            + "."
            + str(spinetoolbox.__version_info__.serial)
        )
        self.v_spinetoolbox = spinetoolbox.__version__
        self.v_spinedb_api = spinedb_api.__version__
        self.v_spine_engine = spine_engine.__version__
        self.v_spine_items = spine_items.__version__
        self.import_path_spinetoolbox, _ = os.path.split(spinetoolbox.__file__)
        self.import_path_spinedb_api, _ = os.path.split(spinedb_api.__file__)
        self.import_path_spine_engine, _ = os.path.split(spine_engine.__file__)
        self.import_path_spine_items, _ = os.path.split(spine_items.__file__)
        self.ui.label_spine_toolbox.setText(f"Spine Toolbox<br/>{self.v_spinetoolbox}")
        self.ui.label_spine_toolbox.setToolTip(f"{self.import_path_spinetoolbox}")
        self.ui.label_spinedb_api.setText(f"spinedb_api<br/>{self.v_spinedb_api}")
        self.ui.label_spinedb_api.setToolTip(self.import_path_spinedb_api)
        self.ui.label_spine_engine.setText(f"spine_engine<br/>{self.v_spine_engine}")
        self.ui.label_spine_engine.setToolTip(self.import_path_spine_engine)
        self.ui.label_spine_items.setText(f"spine_items<br/>{self.v_spine_items}")
        self.ui.label_spine_items.setToolTip(self.import_path_spine_items)
        self.ui.label_python.setText(f"Python {platform.python_version()}")
        self.ui.label_python.setToolTip(sys.executable)
        self.setup_license_text()
        self._mousePressPos = None
        self._mouseReleasePos = None
        self._mouseMovePos = None
        # Move About Popup to correct position
        pos = self.calc_pos()
        self.move(pos)

    @Slot(bool)
    def copy_to_clipboard(self, _):
        """Copies package and Python info to clipboard."""
        QApplication.clipboard().setText(
            f"spinetoolbox {self.v_spinetoolbox}\n"
            f"spinetoolbox import path {self.import_path_spinetoolbox}\n\n"
            f"spinedb_api {self.v_spinedb_api}\n"
            f"spinedb_api import path {self.import_path_spinedb_api}\n\n"
            f"spine_engine {self.v_spine_engine}\n"
            f"spine_engine import path {self.import_path_spine_engine}\n\n"
            f"spine_items {self.v_spine_items}\n"
            f"spine_items import path {self.import_path_spine_items}\n\n"
            f"Python {sys.version}\n"
            f"sys.executable {sys.executable}\n"
        )

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
        self.ui.textBrowser.moveCursor(QTextCursor.MoveOperation.Start)

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
        currentpos = self.pos()
        globalpos = e.globalPos()
        diff = globalpos - self._mouseMovePos
        newpos = currentpos + diff
        self.move(newpos)
        self._mouseMovePos = globalpos
