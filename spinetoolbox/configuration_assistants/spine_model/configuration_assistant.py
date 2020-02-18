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
Widget for assisting the user in configuring tools, such as SpineModel.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

import sys
from PySide2.QtCore import Signal, Slot, QState
from spinetoolbox.widgets.state_machine_widget import StateMachineWidget
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.config import JULIA_EXECUTABLE


class SpineModelConfigurationAssistant(StateMachineWidget):

    _required_julia_version = "1.1.0"
    julia_not_found = Signal()
    bad_julia_version_found = Signal()
    good_julia_version_found = Signal()
    spine_model_installed = Signal()
    spine_model_installation_failed = Signal()
    py_call_installation_needed = Signal()
    py_call_reconfiguration_needed = Signal()
    py_call_installed = Signal()
    py_call_process_failed = Signal()
    spine_model_ready = Signal()

    def __init__(self, toolbox):
        super().__init__("SpineModel.jl configuration assistant", toolbox)
        self._toolbox = toolbox
        self.exec_mngr = None
        self._py_call_program = None
        self._welcome_text = "Welcome! This assistant will help you configure Spine Toolbox for using SpineModel.jl"
        self.julia_exe = None
        self.julia_project_path = None
        self._julia_version = None
        self._julia_active_project = None
        self.button_left.clicked.connect(self.close)

    def _make_processing_state(self, text):
        s = QState(self.run)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", False)
        s.assignProperty(self.button_left, "visible", False)
        return s

    def _make_report_state(self, text):
        s = QState(self.run)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", False)
        s.assignProperty(self.button_left, "visible", True)
        s.assignProperty(self.button_left, "text", "Close")
        return s

    def _make_prompt_state(self, text):
        s = QState(self.run)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", True)
        s.assignProperty(self.button_right, "text", "Allow")
        s.assignProperty(self.button_left, "visible", True)
        s.assignProperty(self.button_left, "text", "Cancel")
        return s

    def _make_checking_julia_version(self):
        return self._make_processing_state("<html><p>Checking Julia version...</p></html>")

    def _make_report_julia_not_found(self):
        return self._make_report_state(
            "<html><p>Unable to find Julia. Make sure that Julia is installed correctly and try again.</p></html>"
        )

    def _make_report_bad_julia_version(self):
        return self._make_report_state(
            f"<html><p>SpineModel.jl requires Julia version >= 1.1.0, whereas current version is {self._julia_version}. "
            "Upgrade Julia and try again.</p></html>"
        )

    def _make_updating_spine_model(self):
        return self._make_processing_state("<html><p>Updating SpineModel.jl to the latest version...</p></html>")

    def _make_prompt_to_install_latest_spine_model(self):
        return self._make_prompt_state(
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p><p>Install the SpineModel.jl package</p>"
        )

    def _make_installing_latest_spine_model(self):
        return self._make_processing_state("<html><p>Installing latest SpineModel.jl...</p></html>")

    def _make_report_spine_model_installation_failed(self):
        return self._make_report_state(
            "<html><p>SpineModel.jl installation failed. See Process log for error messages.</p></html>"
        )

    def _make_checking_py_call_program(self):
        return self._make_processing_state("<html><p>Checking PyCall.jl's configuration...</p></html>")

    def _make_prompt_to_reconfigure_py_call(self):
        return self._make_prompt_state(
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p>"
            f"<p>Change the Python program used by PyCall.jl to {sys.executable}</p>"
        )

    def _make_prompt_to_install_py_call(self):
        return self._make_prompt_state(
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p>"
            "<p>Install the PyCall.jl package.</p>"
        )

    def _make_report_spine_model_ready(self):
        return self._make_report_state("<html><p>SpineModel.jl has been successfully configured.</p></html>")

    def _make_reconfiguring_py_call(self):
        return self._make_processing_state("<html><p>Reconfiguring PyCall.jl...</p></html>")

    def _make_installing_py_call(self):
        return self._make_processing_state("<html><p>Installing PyCall.jl...</p></html>")

    def _make_report_py_call_process_failed(self):
        return self._make_report_state(
            "<html><p>PyCall.jl installation/reconfiguration failed. See Process log for error messages.</p></html>"
        )

    @Slot()
    def _handle_welcome_finished(self):
        self._goto_state(self._make_checking_julia_version())
        self.julia_not_found.connect(self._goto_report_julia_not_found)
        self.bad_julia_version_found.connect(self._goto_report_bad_julia_version)
        self.good_julia_version_found.connect(self._goto_updating_spine_model)
        self.find_julia_version()

    @Slot()
    def _goto_report_julia_not_found(self):
        self._goto_state(self._make_report_julia_not_found())

    @Slot()
    def _goto_report_bad_julia_version(self):
        self._goto_state(self._make_report_bad_julia_version())

    @Slot()
    def _goto_updating_spine_model(self):
        self._goto_state(self._make_updating_spine_model())
        self.spine_model_installation_failed.connect(self._goto_prompt_to_install_latest_spine_model)
        self.spine_model_installed.connect(self._goto_checking_py_call_program)
        self.update_spine_model()

    @Slot()
    def _goto_prompt_to_install_latest_spine_model(self):
        self._goto_state(self._make_prompt_to_install_latest_spine_model())
        self.button_right.clicked.connect(self._goto_installing_latest_spine_model)

    @Slot()
    def _goto_checking_py_call_program(self):
        self._goto_state(self._make_checking_py_call_program())
        self.py_call_reconfiguration_needed.connect(self._goto_prompt_to_reconfigure_py_call)
        self.py_call_installation_needed.connect(self._goto_prompt_to_install_py_call)
        self.spine_model_ready.connect(self._goto_report_spine_model_ready)
        self.check_py_call_program()

    @Slot()
    def _goto_installing_latest_spine_model(self):
        self._goto_state(self._make_installing_latest_spine_model())
        self.spine_model_installed.connect(self._goto_checking_py_call_program)
        self.spine_model_installation_failed.connect(self._goto_report_spine_model_installation_failed)
        self.install_spine_model()

    @Slot()
    def _goto_prompt_to_reconfigure_py_call(self):
        self._goto_state(self._make_prompt_to_reconfigure_py_call())
        self.button_right.clicked.connect(self._goto_reconfiguring_py_call)

    @Slot()
    def _goto_prompt_to_install_py_call(self):
        self._goto_state(self._make_prompt_to_install_py_call())
        self.button_right.clicked.connect(self._goto_installing_py_call)

    @Slot()
    def _goto_report_spine_model_installation_failed(self):
        self._goto_state(self._make_report_spine_model_installation_failed())

    @Slot()
    def _goto_reconfiguring_py_call(self):
        self._goto_state(self._make_reconfiguring_py_call())
        self.spine_model_ready.connect(self._goto_report_spine_model_ready)
        self.py_call_process_failed.connect(self._goto_report_py_call_process_failed)
        self.reconfigure_py_call()

    @Slot()
    def _goto_installing_py_call(self):
        self._goto_state(self._make_installing_py_call())
        self.py_call_installed.connect(self._goto_checking_py_call_program)
        self.py_call_process_failed.connect(self._goto_report_py_call_process_failed)
        self.install_py_call()

    @Slot()
    def _goto_report_spine_model_ready(self):
        self._goto_state(self._make_report_spine_model_ready())

    @Slot()
    def _goto_report_py_call_process_failed(self):
        self._goto_state(self._make_report_py_call_process_failed())

    def find_julia_version(self):
        julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
        if julia_path != "":
            self.julia_exe = julia_path
        else:
            self.julia_exe = JULIA_EXECUTABLE
        self.julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
        if self.julia_project_path == "":
            self.julia_project_path = "@."
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, silent=True)
        exec_mngr.start_execution()
        if exec_mngr.wait_for_process_finished(msecs=5000):
            self._julia_version = exec_mngr.process_output
        if self._julia_version is None:
            self.julia_not_found.emit()
            return
        if self._julia_version < self._required_julia_version:
            self.bad_julia_version_found.emit()
            return
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("println(Base.active_project())")
        exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, silent=True)
        exec_mngr.start_execution()
        if exec_mngr.wait_for_process_finished(msecs=5000):
            self._julia_active_project = exec_mngr.process_output
        self.good_julia_version_found.emit()

    def update_spine_model(self):
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.update(ARGS[1]);")
        args.append("SpineModel")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_model_process_finished)
        self.exec_mngr.start_execution()

    def install_spine_model(self):
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.add(PackageSpec(url=ARGS[1])); Pkg.add(PackageSpec(url=ARGS[2]));")
        args.append("https://github.com/Spine-project/SpineInterface.jl.git")
        args.append("https://github.com/Spine-project/Spine-Model.git")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_model_process_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_spine_model_process_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_spine_model_process_finished)
        if ret == 0:
            self.spine_model_installed.emit()
        else:
            self.spine_model_installation_failed.emit()

    def check_py_call_program(self):
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using PyCall; println(PyCall.pyprogramname);")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, silent=True)
        self.exec_mngr.execution_finished.connect(self._handle_check_py_call_program_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_check_py_call_program_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_check_py_call_program_finished)
        if ret == 0:
            self._py_call_program = self.exec_mngr.process_output
            if self._py_call_program == sys.executable:
                self.spine_model_ready.emit()
            else:
                self.py_call_reconfiguration_needed.emit()
        else:
            self.py_call_installation_needed.emit()

    def reconfigure_py_call(self):
        """Returns execution manager for process that reconfigures PyCall to use given python program.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using PyCall; ENV[ARGS[1]] = ARGS[2]; using Pkg; Pkg.build(ARGS[3]);")
        args.append("PYTHON")
        args.append(sys.executable)
        args.append("PyCall")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_reconfigure_py_call_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_reconfigure_py_call_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_reconfigure_py_call_finished)
        if ret == 0:
            self.spine_model_ready.emit()
        else:
            self.py_call_process_failed.emit()

    def install_py_call(self):
        """Returns execution manager for process that installs PyCall in current julia version.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.add(ARGS[1]);")
        args.append("PyCall")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_install_py_call_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_install_py_call_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_install_py_call_finished)
        if ret == 0:
            self.py_call_installed.emit()
        else:
            self.py_call_process_failed.emit()
