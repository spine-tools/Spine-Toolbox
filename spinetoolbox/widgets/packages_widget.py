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
Widget for controlling user packages.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

from PySide2.QtWidgets import QWidget, QStatusBar, QApplication
from PySide2.QtGui import QCursor
from PySide2.QtCore import Slot, Qt
import ui.packages
from config import STATUSBAR_SS
from package_managers import SpineModelPackageManager


class PackagesWidget(QWidget):
    """ A widget to manage user's external packages such as SpineModel.

    Attributes:
        toolbox (ToolboxUI): Parent widget.
    """
    def __init__(self, toolbox):
        """ Initialize class. """
        super().__init__(parent=toolbox, f=Qt.Window)
        self._toolbox = toolbox  # QWidget parent
        self.spine_model_pkg_mngr = SpineModelPackageManager(toolbox)
        # Set up the ui from Qt Designer files
        self.ui = ui.packages.Ui_PackagesForm()
        self.ui.setupUi(self)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals."""
        self.ui.pushButton_spine_model_check.clicked.connect(self.check_spine_model)
        self.ui.pushButton_spine_model_install.clicked.connect(self.install_spine_model)
        self.spine_model_pkg_mngr.msg.connect(self._handle_spine_model_msg)
        self.spine_model_pkg_mngr.check_finished.connect(self._handle_spine_model_check_finished)
        self.spine_model_pkg_mngr.installation_finished.connect(self._handle_spine_model_installation_finished)

    @Slot("QString", name="_handle_spine_model_msg")
    def _handle_spine_model_msg(self, msg):
        self.ui.textBrowser_spine_model.append(msg)

    @Slot("bool", name="check_spine_model")
    def check_spine_model(self, checked=False):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.ui.pushButton_spine_model_check.setEnabled(False)
        self.ui.textBrowser_spine_model.append("Checking SpineModel...\n"
                                               "This operation can take up to a couple of minutes...")
        self.spine_model_pkg_mngr.check()

    @Slot(name="_handle_spine_model_check_finished")
    def _handle_spine_model_check_finished(self):
        QApplication.restoreOverrideCursor()
        self.ui.pushButton_spine_model_check.setEnabled(True)

    @Slot("bool", name="check_spine_model")
    def install_spine_model(self, checked=False):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.ui.pushButton_spine_model_install.setEnabled(False)
        self.ui.textBrowser_spine_model.append("Installing SpineModel...\n"
                                               "This operation can take up to a couple of minutes...")
        self.spine_model_pkg_mngr.install()

    @Slot(name="_handle_spine_model_check_finished")
    def _handle_spine_model_installation_finished(self):
        QApplication.restoreOverrideCursor()
        self.ui.pushButton_spine_model_install.setEnabled(True)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()
