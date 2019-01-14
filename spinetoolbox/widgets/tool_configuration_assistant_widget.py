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
Widget for managing user packages.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

from PySide2.QtWidgets import QWidget, QStatusBar, QApplication
from PySide2.QtGui import QCursor, QTextCursor
from PySide2.QtCore import Slot, Qt
import ui.packages
from config import STATUSBAR_SS, TEXTBROWSER_SS
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
        self.q_process = None
        # Set up the ui from Qt Designer files
        self.ui = ui.packages.Ui_PackagesForm()
        self.ui.setupUi(self)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.textBrowser_spine_model.setStyleSheet(TEXTBROWSER_SS)
        self.statusbar = QStatusBar(self)
        self.statusbar.setFixedHeight(20)
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.horizontalLayout_statusbar_placeholder.addWidget(self.statusbar)
        self.connect_signals()

    def connect_signals(self):
        """Connect signals."""
        self.ui.pushButton_spine_model_check.clicked.connect(self.check_spine_model)
        self.ui.textBrowser_spine_model.anchorClicked.connect(self._handle_spine_model_anchor_clicked)

    def add_spine_model_msg(self, msg):
        """Append message to SpineModel log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:white;white-space: pre-wrap;'>"
        message = open_tag + msg + "</span><br>"
        self.ui.textBrowser_spine_model.moveCursor(QTextCursor.End)
        self.ui.textBrowser_spine_model.insertHtml(message)
        QApplication.processEvents()

    def add_spine_model_error_msg(self, msg):
        """Append error message to SpineModel log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:#ff3333;white-space: pre-wrap;'>"
        message = open_tag + msg + "</span><br>"
        self.ui.textBrowser_spine_model.moveCursor(QTextCursor.End)
        self.ui.textBrowser_spine_model.insertHtml(message)
        QApplication.processEvents()

    def add_spine_model_success_msg(self, msg):
        """Append success message to SpineModel log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:#00ff00;white-space: pre-wrap;'>"
        message = open_tag + msg + "</span><br>"
        self.ui.textBrowser_spine_model.moveCursor(QTextCursor.End)
        self.ui.textBrowser_spine_model.insertHtml(message)
        QApplication.processEvents()

    @Slot("QString", name="_handle_spine_model_anchor_clicked")
    def _handle_spine_model_anchor_clicked(self, link):
        self.begin_spine_model_operation()
        if link == "Install SpineModel":
            self.add_spine_model_msg("Installing SpineModel. This operation can take a few moments...")
            self.q_process = self.spine_model_pkg_mngr.install_spine_model()
            self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_installation_finished)
        elif link == "Install PyCall":
            self.add_spine_model_msg("Installing PyCall. This operation can take a few moments...")
            self.q_process = self.spine_model_pkg_mngr.install_py_call()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_installation_finished)
        elif link == "Install spinedatabase_api in PyCall python":
            self.add_spine_model_msg("Installing spinedatabase_api. This operation can take a few moments...")
            self.q_process = self.spine_model_pkg_mngr.install_spinedatabase_api()
            self.q_process.subprocess_finished_signal.connect(self._handle_spinedatabase_api_installation_finished)
        elif link == "Use same python as SpineToolbox":
            self.add_spine_model_msg("Reconfiguring PyCall to use the same python as Spine Toolbox. "
                                     "This operation can take a few moments...")
            self.q_process = self.spine_model_pkg_mngr.reconfigure_py_call()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_reconfiguration_finished)

    @Slot(int, name="_handle_spine_model_installation_finished")
    def _handle_spine_model_installation_finished(self, ret):
        if self.q_process.process_failed_to_start:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed. "
                                           "Make sure that Julia is correctly installed and try again.")
            return
        self.add_spine_model_success_msg("SpineModel succesfully installed.")
        self.end_spine_model_operation()

    @Slot(int, name="_handle_py_call_installation_finished")
    def _handle_py_call_installation_finished(self, ret):
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed. "
                                           "Make sure that Julia is correctly installed and try again.")
            return
        self.add_spine_model_success_msg("PyCall succesfully installed.")
        self.end_spine_model_operation()

    @Slot(int, name="_handle_spinedatabase_api_installation_finished")
    def _handle_spinedatabase_api_installation_finished(self, ret):
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed.")
            return
        self.add_spine_model_success_msg("spinedatabase_api succesfully installed.")
        self.end_spine_model_operation()

    @Slot(int, name="_handle_py_call_reconfiguration_finished")
    def _handle_py_call_reconfiguration_finished(self, ret):
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("PyCall reconfiguration failed.")
            return
        self.add_spine_model_success_msg("PyCall successfully reconfigured.")
        self.end_spine_model_operation()

    @Slot("bool", name="check_spine_model")
    def check_spine_model(self, checked=False):
        self.begin_spine_model_operation()
        self.add_spine_model_msg("Checking SpineModel. This operation can take a few moments...")
        self.q_process = self.spine_model_pkg_mngr.spine_model_installed_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_installed_check_finished)

    @Slot(int, name="_handle_spine_model_installed_check_finished")
    def _handle_spine_model_installed_check_finished(self, ret):
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            self.end_spine_model_operation()
            return
        if ret != 0:
            self.add_spine_model_error_msg("SpineModel.jl is not installed.")
            anchor = "<a style='color:#99CCFF;' href='Install SpineModel'>here</a>"
            self.add_spine_model_msg("You can install SpineModel by clicking {0}.".format(anchor))
            self.end_spine_model_operation()
            return
        spine_model_version = self.q_process.output
        self.add_spine_model_msg("SpineModel version {} is correctly installed.".format(spine_model_version))
        self.q_process = self.spine_model_pkg_mngr.py_call_program_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_py_call_program_check_finished)

    @Slot(int, name="_handle_py_call_program_check_finished")
    def _handle_py_call_program_check_finished(self, ret):
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            self.end_spine_model_operation()
            return
        if ret != 0:
            self.add_spine_model_error_msg("The PyCall module couldn't be found. ")
            anchor = "<a style='color:#99CCFF;' href='Install PyCall'>here</a>"
            self.add_spine_model_msg("You can install PyCall by clicking {0}.".format(anchor))
            self.end_spine_model_operation()
            return
        py_call_python_program = self.q_process.output
        self.add_spine_model_msg("PyCall is configured to use the python program at "
                                 "<b>{0}</b>".format(py_call_python_program))
        self.spine_model_pkg_mngr.py_call_python_program = py_call_python_program
        self.q_process = self.spine_model_pkg_mngr.spinedatabase_api_installed_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_spinedatabase_api_installed_check_finished)

    @Slot(int, name="_handle_spinedatabase_api_installed_check_finished")
    def _handle_spinedatabase_api_installed_check_finished(self, ret):
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed.")
            self.end_spine_model_operation()
            return
        py_call_python_program = self.spine_model_pkg_mngr.py_call_python_program
        if ret != 0:
            self.add_spine_model_error_msg("spinedatabase_api is not installed in PyCall's python.")
            anchor1 = "<a style='color:#99CCFF;' href='Install spinedatabase_api in PyCall python'>here</a>"
            anchor2 = "<a style='color:#99CCFF;' href='Use same python as SpineToolbox'>here</a>"
            self.add_spine_model_msg("You have two options:"
                                     "<ul><li>Install spinedatabase_api in PyCall's python, "
                                     "by clicking {0}.</li>"
                                     "<li>Reconfigure PyCall to use the same python as SpineToolbox, "
                                     "by clicking {1}.</li></ul>".format(anchor1, anchor2))
            self.end_spine_model_operation()
            return
        self.add_spine_model_msg("spinedatabase_api is correctly installed in PyCall's python.")
        self.add_spine_model_success_msg("All checks passed. SpineModel is ready to use.")
        self.end_spine_model_operation()

    def begin_spine_model_operation(self):
        self.ui.pushButton_spine_model_check.setEnabled(False)
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def end_spine_model_operation(self):
        self.ui.pushButton_spine_model_check.setEnabled(True)
        QApplication.restoreOverrideCursor()
