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
Widget for assisting the user in configuring tools, such as SpineModel.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

from PySide2.QtWidgets import QWidget, QApplication
from PySide2.QtGui import QCursor, QTextCursor
from PySide2.QtCore import Slot, Qt
import ui.tool_configuration_assistant
from config import TEXTBROWSER_SS
from tool_configuration_assistants import SpineModelConfigurationAssistant


class ToolConfigurationAssistantWidget(QWidget):
    """ A widget to assist the user in configuring external tools such as SpineModel.

    Attributes:
        toolbox (ToolboxUI): Parent widget.
    """
    def __init__(self, toolbox):
        """ Initialize class. """
        super().__init__(parent=toolbox, f=Qt.Window)
        self._toolbox = toolbox  # QWidget parent
        self.spine_model_config_asst = SpineModelConfigurationAssistant(toolbox)
        self.q_process = None
        # Set up the ui from Qt Designer files
        self.ui = ui.tool_configuration_assistant.Ui_PackagesForm()
        self.ui.setupUi(self)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.ui.textBrowser_spine_model.setStyleSheet(TEXTBROWSER_SS)
        self.connect_signals()
        self.check_spine_model_configuration()

    def connect_signals(self):
        """Connect signals."""
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
        """Run when the user clicks an anchor in SpineModel's text browser.
        Call the appropriate method on the Spine Model configuration assistant.
        """
        self.begin_spine_model_operation()
        if link == "Install SpineModel":
            self.add_spine_model_msg("Installing SpineModel. This operation can take a few moments...")
            self.q_process = self.spine_model_config_asst.install_spine_model()
            self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_installation_finished)
        elif link == "Install PyCall":
            self.add_spine_model_msg("Installing PyCall. This operation can take a few moments...")
            self.q_process = self.spine_model_config_asst.install_py_call()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_installation_finished)
        elif link == "Install spinedb_api in PyCall python":
            self.add_spine_model_msg("Installing spinedb_api. This operation can take a few moments...")
            self.q_process = self.spine_model_config_asst.install_spinedb_api()
            self.q_process.subprocess_finished_signal.connect(self._handle_spinedb_api_installation_finished)
        elif link == "Use same python as SpineToolbox":
            self.add_spine_model_msg("Reconfiguring PyCall to use the same python as Spine Toolbox. "
                                     "This operation can take a few moments...")
            self.q_process = self.spine_model_config_asst.reconfigure_py_call()
            self.q_process.subprocess_finished_signal.connect(self._handle_py_call_reconfiguration_finished)

    @Slot(int, name="_handle_spine_model_installation_finished")
    def _handle_spine_model_installation_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished installing SpineModel.
        Restart SpineModel configuration check.
        """
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed. "
                                           "Make sure that Julia is correctly installed and try again.")
            return
        self.add_spine_model_success_msg("SpineModel successfully installed.")
        self.end_spine_model_operation()
        self.check_spine_model_configuration()

    @Slot(int, name="_handle_py_call_installation_finished")
    def _handle_py_call_installation_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished installing PyCall.
        Restart SpineModel configuration check.
        """
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed. "
                                           "Make sure that Julia is correctly installed and try again.")
            return
        self.add_spine_model_success_msg("PyCall successfully installed.")
        self.end_spine_model_operation()
        self.check_spine_model_configuration()

    @Slot(int, name="_handle_spinedb_api_installation_finished")
    def _handle_spinedb_api_installation_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished installing spinedb_api.
        Restart SpineModel configuration check.
        """
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("Installation failed.")
            return
        self.add_spine_model_success_msg("spinedb_api successfully installed.")
        self.end_spine_model_operation()
        self.check_spine_model_configuration()

    @Slot(int, name="_handle_py_call_reconfiguration_finished")
    def _handle_py_call_reconfiguration_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished reconfiguring PyCall.
        Restart SpineModel configuration check.
        """
        if ret != 0:
            self.end_spine_model_operation()
            self.add_spine_model_error_msg("PyCall reconfiguration failed.")
            return
        self.add_spine_model_success_msg("PyCall successfully reconfigured.")
        self.end_spine_model_operation()
        self.check_spine_model_configuration()

    def check_spine_model_configuration(self):
        """Begin SpineModel configuration check, by checking if SpineModel is installed."""
        self.begin_spine_model_operation()
        self.add_spine_model_msg("<b>Checking SpineModel configuration.</b> This operation can take a few moments...")
        julia_version = self.spine_model_config_asst.julia_version()
        if julia_version is None:
            self.add_spine_model_error_msg("Unable to determine Julia version. "
                                           "Make sure that Julia is correctly installed and try again")
            self.end_spine_model_operation()
            return
        if julia_version > "0.6.4" or julia_version < "0.6.0":
            self.add_spine_model_error_msg("Julia version is {}. SpineModel.jl requires "
                                           "Julia version 0.6.x to be installed.".format(julia_version))
            self.end_spine_model_operation()
            return
        self.q_process = self.spine_model_config_asst.spine_model_installed_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_spine_model_installed_check_finished)

    @Slot(int, name="_handle_spine_model_installed_check_finished")
    def _handle_spine_model_installed_check_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished checking if SpineModel is installed.
        Continue SpineModel configuration check, by checking the python program used by PyCall.
        """
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            self.end_spine_model_operation()
            return
        if ret != 0:
            self.add_spine_model_error_msg("SpineModel couldn't be found.")
            anchor = "<a style='color:#99CCFF;' href='Install SpineModel'>here</a>"
            self.add_spine_model_msg("To install SpineModel, please click {0}.".format(anchor))
            self.end_spine_model_operation()
            return
        spine_model_version = self.q_process.output
        self.add_spine_model_msg("SpineModel version {} is correctly installed.".format(spine_model_version))
        self.q_process = self.spine_model_config_asst.py_call_program_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_py_call_program_check_finished)

    @Slot(int, name="_handle_py_call_program_check_finished")
    def _handle_py_call_program_check_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished checking the python program used by PyCall.
        Continue SpineModel configuration check, by checking if spinedb_api is installed.
        """
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed. Make sure that Julia is correctly installed and try again.")
            self.end_spine_model_operation()
            return
        if ret != 0:
            self.add_spine_model_error_msg("PyCall couldn't be found. ")
            anchor = "<a style='color:#99CCFF;' href='Install PyCall'>here</a>"
            self.add_spine_model_msg("To install PyCall, please click {0}.".format(anchor))
            self.end_spine_model_operation()
            return
        py_call_python_program = self.q_process.output
        self.add_spine_model_msg("PyCall is configured to use the python program at "
                                 "<b>{0}</b>".format(py_call_python_program))
        self.spine_model_config_asst.py_call_python_program = py_call_python_program
        self.q_process = self.spine_model_config_asst.spinedb_api_installed_check()
        self.q_process.subprocess_finished_signal.connect(self._handle_spinedb_api_installed_check_finished)

    @Slot(int, name="_handle_spinedb_api_installed_check_finished")
    def _handle_spinedb_api_installed_check_finished(self, ret):
        """Run when the Spine Model configuration assistant has finished checking if spinedb_api is installed.
        End SpineModel configuration check.
        """
        if self.q_process.process_failed_to_start:
            self.add_spine_model_error_msg("Check failed.")
            self.end_spine_model_operation()
            return
        if ret != 0:
            self.add_spine_model_error_msg("spinedb_api is not installed in PyCall's python.")
            anchor1 = "<a style='color:#99CCFF;' href='Install spinedb_api in PyCall python'>here</a>"
            anchor2 = "<a style='color:#99CCFF;' href='Use same python as SpineToolbox'>here</a>"
            self.add_spine_model_msg("You have two options:"
                                     "<ul><li>To install spinedb_api in PyCall's python, "
                                     "please click {0}.</li>"
                                     "<li>To reconfigure PyCall to use the same python as SpineToolbox, "
                                     "please click {1}.</li></ul>".format(anchor1, anchor2))
            self.end_spine_model_operation()
            return
        self.add_spine_model_msg("spinedb_api is correctly installed in PyCall's python.")
        self.add_spine_model_success_msg("<b>SpineModel is ready to use.</b>")
        self.end_spine_model_operation()

    def begin_spine_model_operation(self):
        QApplication.setOverrideCursor(QCursor(Qt.BusyCursor))

    def end_spine_model_operation(self):
        QApplication.restoreOverrideCursor()
