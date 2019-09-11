######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget for assisting the user in configuring tools, such as SpineModel.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

import sys
from PySide2.QtWidgets import QWidget, QApplication, QMessageBox
from PySide2.QtGui import QCursor, QTextCursor
from PySide2.QtCore import Slot, Qt
import ui.tool_configuration_assistant
from config import TEXTBROWSER_SS
from tool_configuration_assistants import SpineModelConfigurationAssistant


class ToolConfigurationAssistantWidget(QWidget):
    """ A widget to assist the user in configuring external tools such as SpineModel.

    Attributes:
        toolbox (ToolboxUI): Parent widget.
        autorun (bool): whether or not to start configuration process at form load
    """

    def __init__(self, toolbox, autorun=True):
        """ Initialize class. """
        super().__init__(parent=toolbox, f=Qt.Window)
        self._toolbox = toolbox  # QWidget parent
        self.spine_model_config_asst = SpineModelConfigurationAssistant(toolbox)
        self.q_process = None
        self.py_call_installed = False  # Whether or not PyCall has been installed
        # Set up the ui from Qt Designer files
        self.ui = ui.tool_configuration_assistant.Ui_PackagesForm()
        self.ui.setupUi(self)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.textBrowser_spine_model.setStyleSheet(TEXTBROWSER_SS)
        self.connect_signals()
        if autorun:
            self.configure_spine_model()

    def connect_signals(self):
        """Connect signals."""

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

    def configure_spine_model(self):
        """Run when form loads. Check SpineModel version."""
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))
        self.add_spine_model_msg("<b>Configuring SpineModel...</b> This operation can take a few moments...")
        julia_version = self.spine_model_config_asst.julia_version()
        if julia_version is None:
            self.add_spine_model_error_msg(
                "Unable to determine Julia version. Make sure that Julia is correctly installed and try again"
            )
            QApplication.restoreOverrideCursor()
        elif julia_version < "1.1.0":
            self.add_spine_model_error_msg(
                "SpineModel.jl requires Julia version >= 1.1.0, whereas current version is {}.".format(julia_version)
            )
            QApplication.restoreOverrideCursor()
        else:
            self.q_process = self.spine_model_config_asst.spine_model_version_check()
            self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_version_check_finished)
            self.q_process.start_process()

    @Slot(int, name="_handle_spine_model_version_check_finished")
    def _handle_spine_model_version_check_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished checking SpineModel version.
        Install SpineModel if not found, otherwise check the python program used by PyCall.
        """
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            QApplication.restoreOverrideCursor()
        elif ret != 0:
            if not self.get_permission("Spine Model not installed", "Install the SpineModel package."):
                self.add_spine_model_error_msg("Aborted by the user")
                QApplication.restoreOverrideCursor()
            else:
                self.add_spine_model_msg("Installing SpineModel. This operation can take a few moments...")
                self.q_process = self.spine_model_config_asst.install_spine_model()
                self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_installation_finished)
                self.q_process.start_process()
        else:
            self.add_spine_model_msg("SpineModel is correctly installed.")
            self.q_process = self.spine_model_config_asst.py_call_program_check()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_program_check_finished)
            self.q_process.start_process()

    @Slot(int, name="_handle_spine_model_installation_finished")
    def _handle_spine_model_installation_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished installing SpineModel.
        Check the python program used by PyCall.
        """
        if self.q_process.process_failed_to_start or ret != 0:
            self.add_spine_model_error_msg(
                "Spine Model installation failed. Make sure that Julia is correctly installed and try again."
            )
            QApplication.restoreOverrideCursor()
        else:
            self.add_spine_model_success_msg("SpineModel successfully installed.")
            self.q_process = self.spine_model_config_asst.py_call_program_check()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_program_check_finished)
            self.q_process.start_process()

    @Slot(int, name="_handle_py_call_program_check_finished")
    def _handle_py_call_program_check_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished checking the python program used by PyCall.
        Install PyCall if not found, otherwise reconfigure PyCall to use same python as Spine Toolbox if it's not
        the case.
        """
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            QApplication.restoreOverrideCursor()
        elif ret != 0:
            if self.py_call_installed:
                self.py_call_installed = False
                py_call_program_check_err = self.q_process.error_output
                self.add_spine_model_error_msg(
                    "Unable to determine the python program used by PyCall: {}.".format(py_call_program_check_err)
                )
                QApplication.restoreOverrideCursor()
            elif not self.get_permission("PyCall not installed", "Install the PyCall package."):
                self.add_spine_model_error_msg("Aborted by the user")
                QApplication.restoreOverrideCursor()
            else:
                self.add_spine_model_msg("Installing PyCall. This operation can take a few moments...")
                self.q_process = self.spine_model_config_asst.install_py_call()
                self.q_process.subprocess_finished_signal.connect(self._handle_py_call_installation_finished)
                self.q_process.start_process()
        else:
            py_call_python_program = self.q_process.output
            self.add_spine_model_msg(
                "PyCall is configured to use the python program at " "<b>{0}</b>".format(py_call_python_program)
            )
            if py_call_python_program != sys.executable:
                if not self.get_permission(
                    "Wrong PyCall configuration", f"Configure Pycall to use the Python program at {sys.executable}."
                ):
                    self.add_spine_model_error_msg("Aborted by the user")
                    QApplication.restoreOverrideCursor()
                else:
                    self.add_spine_model_msg(
                        "Reconfiguring PyCall to use the python program at {0}. "
                        "This operation can take a few moments...".format(sys.executable)
                    )
                    self.q_process = self.spine_model_config_asst.reconfigure_py_call(sys.executable)
                    self.q_process.subprocess_finished_signal.connect(self._handle_py_call_reconfiguration_finished)
                    self.q_process.start_process()
            else:
                self.add_spine_model_success_msg("<b>SpineModel is ready to use.</b>")
                QApplication.restoreOverrideCursor()

    @Slot(int, name="_handle_py_call_installation_finished")
    def _handle_py_call_installation_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished installing PyCall.
        Check the python program used by PyCall.
        """
        if self.q_process.process_failed_to_start or ret != 0:
            self.py_call_installed = False
            self.add_spine_model_error_msg(
                "PyCall installation failed. Make sure that Julia is correctly installed and try again."
            )
            QApplication.restoreOverrideCursor()
        else:
            self.py_call_installed = True
            self.add_spine_model_success_msg("PyCall successfully installed.")
            self.q_process = self.spine_model_config_asst.py_call_program_check()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_program_check_finished)
            self.q_process.start_process()

    @Slot(int, name="_handle_py_call_reconfiguration_finished")
    def _handle_py_call_reconfiguration_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished reconfiguring PyCall.
        End Spine Model configuration.
        """
        if self.q_process.process_failed_to_start or ret != 0:
            self.add_spine_model_error_msg("PyCall reconfiguration failed.")
        else:
            self.add_spine_model_success_msg("PyCall successfully reconfigured.")
            self.add_spine_model_success_msg("<b>SpineModel is ready to use.</b>")
        QApplication.restoreOverrideCursor()

    def get_permission(self, title, action):
        """Ask user's permission to perform an action and return True if granted."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle(title)
        msg.setText(
            "Spine Toolbox needs to do the following modifications to the Julia project at <b>{0}</b>:"
            "<p>{1}".format(self.spine_model_config_asst.julia_active_project(), action)
        )
        allow_button = msg.addButton("Allow", QMessageBox.YesRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec_()  # Show message box
        return msg.clickedButton() == allow_button

    def closeEvent(self, event=None):
        """Handle close widget.

        Args:
             event (QEvent): PySide2 event
        """
        QApplication.restoreOverrideCursor()
        if event:
            event.accept()
