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
Widget for assisting the user in configuring SpineOpt.jl.

:author: M. Marin (KTH)
:date:   9.1.2019
"""

import os
import json
from PySide2.QtCore import Signal, Slot
from spinetoolbox.widgets.state_machine_widget import StateMachineWidget
from spinetoolbox.widgets.kernel_editor import KernelEditor, find_julia_kernels, find_python_kernels
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import busy_effect, python_interpreter, resolve_julia_executable_from_path


class SpineOptConfigurationAssistant(StateMachineWidget):

    _required_julia_version = "1.1.0"
    py_call_program_check_needed = Signal()
    spine_opt_process_failed = Signal()
    py_call_installation_needed = Signal()
    py_call_reconfiguration_needed = Signal()
    py_call_process_failed = Signal()
    spine_opt_ready = Signal()

    def __init__(self, toolbox):
        super().__init__("SpineOpt.jl configuration assistant", toolbox)
        self._toolbox = toolbox
        self.exec_mngr = None
        self.julia_exe = None
        self.julia_project_path = None
        self._julia_version = None
        self._julia_active_project = None
        self._py_call_program = None
        self.julia_exe, self.julia_project_path = self.resolve_julia()
        self.python = self.resolve_python()
        self._welcome_text = (
            "<html><p>Welcome! This assistant will help you configure Spine Toolbox for using SpineOpt.jl<br><br>"
            "Your setup<br>"
            "Julia: <b>{0}</b><br>"
            "Julia Project: <b>{1}</b><br>"
            "Python for PyCall: <b>{2}</b>"
            "</p></html>".format(self.julia_exe, self.julia_project_path, self.python)
        )
        self.button_left.clicked.connect(self.close)

    def resolve_julia(self):
        """Returns Julia executable and project according to user's Settings."""
        use_embedded_julia = int(self._toolbox.qsettings().value("appSettings/useEmbeddedJulia", defaultValue="2"))
        if use_embedded_julia == 2:
            # If user has enabled the embedded Julia Console, we need to take julia exe and project from kernel specs
            # Read Julia kernel name from app settings
            kernel_name = self._toolbox.qsettings().value("appSettings/juliaKernel", defaultValue="")
            if not self.check_kernel_is_ok(kernel_name, "Julia"):
                return None, None
            julia_kernels = find_julia_kernels()
            kernel_deats = KernelEditor.get_kernel_deats(julia_kernels[kernel_name])
            julia_exe = kernel_deats["exe"]
            julia_project_path = kernel_deats["project"]
        else:
            julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
            if julia_path != "":
                julia_exe = julia_path
            else:
                julia_exe = resolve_julia_executable_from_path()
            if julia_exe == "":
                self._toolbox.msg_error.emit(
                    "Julia not found in PATH. Please select a valid Julia executable in Settings->Tools."
                )
                # Julia was not found in PATH
                return None, None
            julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
            if julia_project_path == "":
                julia_project_path = "@."
        return julia_exe, julia_project_path

    def resolve_python(self):
        """Returns the full path to Python interpreter according to user's Settings."""
        use_embedded_python = int(self._toolbox.qsettings().value("appSettings/useEmbeddedPython", defaultValue="2"))
        if use_embedded_python == 2:
            # Get Python interpreter from selected Python kernel
            python_kernel_name = self._toolbox.qsettings().value("appSettings/pythonKernel", defaultValue="")
            if not self.check_kernel_is_ok(python_kernel_name, "Python"):
                return None
            kernel_deats = KernelEditor.get_kernel_deats(find_python_kernels()[python_kernel_name])
            python_path = kernel_deats["exe"]
            return python_path
        else:
            return python_interpreter(self._toolbox.qsettings())

    def check_kernel_is_ok(self, kernel_name, prgm):
        """Checks that kernel spec is valid for the configuration assistant to continue.

        Args:
            kernel_name (str): Kernel name
            prgm (str): Either "Python" or "Julia", determines which kernel type to check

        Returns:
            bool: True if kernel is ok, False otherwise
        """
        if kernel_name == "":
            self._toolbox.msg_error.emit(f"No kernel selected. Go to Settings->Tools to select a {prgm} kernel")
            return False
        if prgm == "Python":
            kernels = find_python_kernels()
        else:
            kernels = find_julia_kernels()
        try:
            kernel_path = kernels[kernel_name]
        except KeyError:
            self._toolbox.msg_error.emit(
                f"Kernel <b>{kernel_name}</b> not found. Go to Settings->Tools and select another {prgm} kernel."
            )
            return False
        kernel_json = os.path.join(kernel_path, "kernel.json")
        if not os.path.exists(kernel_json):
            self._toolbox.msg_error.emit(f"Path <b>{kernel_json}</b> does not exist")
            return False
        if os.stat(kernel_json).st_size == 0:
            self._toolbox.msg_error.emit(f"File <b>{kernel_json}</b> is empty")
            return False
        with open(kernel_json, "r") as fh:
            try:
                kernel_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                self._toolbox.msg_error.emit(f"Error reading file <b>{kernel_json}</b> file. Invalid JSON.")
                return False
        return True

    @busy_effect
    def find_julia_version(self):
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, silent=True)
        exec_mngr.start_execution()
        if exec_mngr.wait_for_process_finished(msecs=5000):
            self._julia_version = exec_mngr.process_output
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("println(Base.active_project())")
        exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, silent=True)
        exec_mngr.start_execution()
        if exec_mngr.wait_for_process_finished(msecs=5000):
            self._julia_active_project = exec_mngr.process_output

    def _make_processing_state(self, name, text):
        s = self._make_state(name)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", False)
        s.assignProperty(self.label_loader, "visible", True)
        s.assignProperty(self.button_left, "visible", False)
        return s

    def _make_report_state(self, name, text):
        s = self._make_state(name)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", False)
        s.assignProperty(self.label_loader, "visible", False)
        s.assignProperty(self.button_left, "visible", True)
        s.assignProperty(self.button_left, "text", "Close")
        return s

    def _make_prompt_state(self, name, text):
        s = self._make_state(name)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", True)
        s.assignProperty(self.button_right, "text", "Allow")
        s.assignProperty(self.label_loader, "visible", False)
        s.assignProperty(self.button_left, "visible", True)
        s.assignProperty(self.button_left, "text", "Cancel")
        return s

    def _make_report_julia_not_found(self):
        return self._make_report_state(
            "report_julia_not_found",
            "<html><p>Unable to find Julia. Make sure that Julia is installed correctly and try again.</p></html>",
        )

    def _make_report_bad_julia_version(self):
        return self._make_report_state(
            "report_bad_julia_version",
            f"<html><p>SpineOpt.jl requires Julia version >= {self._required_julia_version}, "
            f"whereas current version is {self._julia_version}. "
            "Upgrade Julia and try again.</p></html>",
        )

    def _make_welcome(self):
        self.find_julia_version()
        # TODO: Report and abort if Julia or Python is None
        if self._julia_version is None:
            return self._make_report_julia_not_found()
        if self._julia_version < self._required_julia_version:
            return self._make_report_bad_julia_version()
        return super()._make_welcome()

    def _make_updating_spine_opt(self):
        return self._make_processing_state(
            "updating_spine_opt", "<html><p>Updating SpineOpt.jl to version 0.4.0...</p></html>"
        )

    def _make_prompt_to_install_latest_spine_opt(self):
        return self._make_prompt_state(
            "prompt_to_install_latest_spine_opt",
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p><p>Install the SpineOpt.jl package</p>",
        )

    def _make_installing_latest_spine_opt(self):
        return self._make_processing_state(
            "installing_latest_spine_opt", "<html><p>Installing SpineOpt.jl 0.4.0...</p></html>"
        )

    def _make_report_spine_opt_installation_failed(self):
        return self._make_report_state(
            "report_spine_opt_installation_failed",
            "<html><p>SpineOpt.jl installation failed. See Process log for error messages.</p></html>",
        )

    def _make_checking_py_call_program(self):
        return self._make_processing_state(
            "checking_py_call_program", "<html><p>Checking PyCall.jl's configuration...</p></html>"
        )

    def _make_prompt_to_reconfigure_py_call(self):
        return self._make_prompt_state(
            "prompt_to_reconfigure_py_call",
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p>"
            f"<p>Change the Python program used by PyCall.jl to {self.python}</p>",
        )

    def _make_prompt_to_install_py_call(self):
        return self._make_prompt_state(
            "prompt_to_install_py_call",
            "<html><p>Spine Toolbox needs to do the following modifications to the Julia project "
            f"at <b>{self._julia_active_project}</b>:</p>"
            "<p>Install the PyCall.jl package.</p>",
        )

    def _make_report_spine_opt_ready(self):
        return self._make_report_state(
            "report_spine_opt_ready", "<html><p>SpineOpt.jl has been successfully configured.</p></html>"
        )

    def _make_reconfiguring_py_call(self):
        return self._make_processing_state("reconfiguring_py_call", "<html><p>Reconfiguring PyCall.jl...</p></html>")

    def _make_installing_py_call(self):
        return self._make_processing_state("installing_py_call", "<html><p>Installing PyCall.jl...</p></html>")

    def _make_report_py_call_process_failed(self):
        return self._make_report_state(
            "report_py_call_process_failed",
            "<html><p>PyCall.jl installation/reconfiguration failed. See Process log for error messages.</p></html>",
        )

    @Slot()
    def update_spine_opt(self):
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        # args.append("using Pkg; Pkg.update(ARGS[1]);")
        # args.append("SpineOpt")
        args.append("using Pkg; Pkg.Registry.add(RegistrySpec(url=ARGS[1])); "
                    "Pkg.add(Pkg.PackageSpec(;name=ARGS[2], version=ARGS[3]));")
        args.append("https://github.com/Spine-project/SpineJuliaRegistry.git")
        args.append("SpineOpt")
        args.append("0.4.0")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_opt_process_finished)
        self.exec_mngr.start_execution()

    @Slot()
    def install_spine_opt(self):
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.Registry.add(RegistrySpec(url=ARGS[1])); "
                    "Pkg.add(Pkg.PackageSpec(;name=ARGS[2], version=ARGS[3]));")
        args.append("https://github.com/Spine-project/SpineJuliaRegistry.git")
        args.append("SpineOpt")
        args.append("0.4.0")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_opt_process_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_spine_opt_process_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_spine_opt_process_finished)
        if ret == 0:
            self.py_call_program_check_needed.emit()
        else:
            self.spine_opt_process_failed.emit()

    @Slot()
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
            if self._py_call_program == self.python:
                self.spine_opt_ready.emit()
            else:
                self.py_call_reconfiguration_needed.emit()
        else:
            self.py_call_installation_needed.emit()

    @Slot()
    def reconfigure_py_call(self):
        """Starts process that reconfigures PyCall to use selected Python interpreter."""
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using PyCall; ENV[ARGS[1]] = ARGS[2]; using Pkg; Pkg.build(ARGS[3]);")
        args.append("PYTHON")
        args.append(self.python)
        args.append("PyCall")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_reconfigure_py_call_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_reconfigure_py_call_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_reconfigure_py_call_finished)
        if ret == 0:
            self.spine_opt_ready.emit()
        else:
            self.py_call_process_failed.emit()

    @Slot()
    def install_py_call(self):
        """Starts process that installs PyCall in current julia version."""
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("ENV[ARGS[1]] = ARGS[2]; using Pkg; Pkg.add(ARGS[3]);")
        args.append("PYTHON")
        args.append(self.python)
        args.append("PyCall")
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia_exe, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_install_py_call_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_install_py_call_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_install_py_call_finished)
        if ret == 0:
            self.py_call_program_check_needed.emit()
        else:
            self.py_call_process_failed.emit()

    def set_up_machine(self):
        super().set_up_machine()
        # States
        updating_spine_opt = self._make_updating_spine_opt()
        prompt_to_install_latest_spine_opt = self._make_prompt_to_install_latest_spine_opt()
        installing_latest_spine_opt = self._make_installing_latest_spine_opt()
        report_spine_opt_installation_failed = self._make_report_spine_opt_installation_failed()
        checking_py_call_program = self._make_checking_py_call_program()
        prompt_to_reconfigure_py_call = self._make_prompt_to_reconfigure_py_call()
        prompt_to_install_py_call = self._make_prompt_to_install_py_call()
        report_spine_opt_ready = self._make_report_spine_opt_ready()
        reconfiguring_py_call = self._make_reconfiguring_py_call()
        installing_py_call = self._make_installing_py_call()
        report_py_call_process_failed = self._make_report_py_call_process_failed()
        # Transitions
        self.welcome.addTransition(self.welcome.finished, updating_spine_opt)
        updating_spine_opt.addTransition(self.spine_opt_process_failed, prompt_to_install_latest_spine_opt)
        updating_spine_opt.addTransition(self.py_call_program_check_needed, checking_py_call_program)
        prompt_to_install_latest_spine_opt.addTransition(self.button_right.clicked, installing_latest_spine_opt)
        installing_latest_spine_opt.addTransition(
            self.spine_opt_process_failed, report_spine_opt_installation_failed
        )
        installing_latest_spine_opt.addTransition(self.py_call_program_check_needed, checking_py_call_program)
        checking_py_call_program.addTransition(self.py_call_reconfiguration_needed, prompt_to_reconfigure_py_call)
        checking_py_call_program.addTransition(self.py_call_installation_needed, prompt_to_install_py_call)
        checking_py_call_program.addTransition(self.py_call_process_failed, report_py_call_process_failed)
        checking_py_call_program.addTransition(self.spine_opt_ready, report_spine_opt_ready)
        prompt_to_reconfigure_py_call.addTransition(self.button_right.clicked, reconfiguring_py_call)
        prompt_to_install_py_call.addTransition(self.button_right.clicked, installing_py_call)
        reconfiguring_py_call.addTransition(self.py_call_process_failed, report_py_call_process_failed)
        reconfiguring_py_call.addTransition(self.spine_opt_ready, report_spine_opt_ready)
        installing_py_call.addTransition(self.py_call_process_failed, report_py_call_process_failed)
        installing_py_call.addTransition(self.py_call_program_check_needed, checking_py_call_program)
        # Entered
        updating_spine_opt.entered.connect(self.update_spine_opt)
        checking_py_call_program.entered.connect(self.check_py_call_program)
        installing_latest_spine_opt.entered.connect(self.install_spine_opt)
        reconfiguring_py_call.entered.connect(self.reconfigure_py_call)
        installing_py_call.entered.connect(self.install_py_call)
