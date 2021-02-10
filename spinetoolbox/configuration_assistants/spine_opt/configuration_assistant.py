######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

import subprocess
from PySide2.QtCore import Signal, Slot
from spinetoolbox.widgets.state_machine_widget import StateMachineWidget
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import busy_effect
from spine_engine.utils.helpers import get_julia_command


class SpineOptConfigurationAssistant(StateMachineWidget):

    _required_julia_version = "1.2.0"
    _preferred_spine_opt_version = "0.4.8"
    spine_opt_not_found = Signal()
    spine_opt_outdated = Signal()
    spine_opt_ready = Signal()
    process_failed = Signal()

    def __init__(self, toolbox):
        super().__init__("SpineOpt.jl", toolbox)
        self._toolbox = toolbox
        self.julia = None
        self.args = None
        self.julia_project = None
        self.julia_setup = None
        self.exec_mngr = None
        self.spine_opt_version = None
        self.checking_spine_opt_version = None
        self.prompt_to_install_spine_opt = None
        self.prompt_to_update_spine_opt = None
        self.installing_spine_opt = None
        self.updating_spine_opt = None
        self.report_failure = None
        self.report_spine_opt_ready = None
        self.button_left.clicked.connect(self.close)

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

    def _make_prompt_state(self, name, text=""):
        s = self._make_state(name)
        s.assignProperty(self.label_msg, "text", text)
        s.assignProperty(self.button_right, "visible", True)
        s.assignProperty(self.button_right, "text", "Ok")
        s.assignProperty(self.label_loader, "visible", False)
        s.assignProperty(self.button_left, "visible", True)
        s.assignProperty(self.button_left, "text", "Cancel")
        return s

    def _make_report_julia_not_found(self):
        return self._make_report_state(
            "report_julia_not_found",
            "<html><p>Unable to find Julia. Make sure that Julia is installed correctly and try again.</p></html>",
        )  # FIXME: Send them to julia downloads

    def _make_report_wrong_julia_version(self, julia_version):
        return self._make_report_state(
            "report_bad_julia_version",
            f"<html><p>SpineOpt.jl requires Julia version >= {self._required_julia_version}, "
            f"whereas current version is {julia_version}. "
            "Upgrade Julia and try again.</p></html>",
        )  # FIXME: Send them to julia downloads

    @busy_effect
    def find_julia_version(self):
        julia_command = get_julia_command(self._toolbox.qsettings())
        if julia_command is None:
            return None
        self.julia, *self.args = julia_command
        self.julia_project = self.args[0].split("--project=")[-1]
        self.args.append("-e")
        cmd = [self.julia, *self.args, 'println(VERSION)']
        try:
            p = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            return None
        return str(p.stdout, "utf-8").strip()

    @busy_effect
    def find_julia_project(self):
        cmd = [self.julia, *self.args, 'println(Base.active_project())']
        try:
            p = subprocess.run(cmd, capture_output=True, check=True)
        except subprocess.CalledProcessError:
            return None
        return str(p.stdout, "utf-8").strip()

    def _make_welcome(self):
        julia_version = self.find_julia_version()
        if julia_version is None:
            return self._make_report_julia_not_found()
        if version_parse(julia_version) < version_parse(self._required_julia_version):
            return self._make_report_wrong_julia_version(julia_version)
        self.julia_project = self.find_julia_project()
        self.julia_setup = (
            '<div style="text-align: left;">Your Julia setup:<ul>'
            f"<li>Executable: <b>{self.julia}</b></li>"
            f"<li>Project: <b>{self.julia_project}</b></li>"
            "</ul></div>"
        )
        self._welcome_text = (
            "<html><p>Welcome!</p>"
            "<p>This assistant will help you getting the right version of SpineOpt for Spine Toolbox.</p>"
            f"{self.julia_setup}</html>"
        )
        return super()._make_welcome()

    def _make_checking_spine_opt_version(self):
        return self._make_processing_state(
            "checking_spine_opt_version", "<html><p>Checking SpineOpt.jl version...</p></html>"
        )

    def _make_prompt_to_install_spine_opt(self):
        return self._make_prompt_state(
            "prompt_to_install_spine_opt",
            f"<html><p>SpineOpt is not installed. Do you want to install it?</>{self.julia_setup}</html>",
        )

    def _make_installing_spine_opt(self):
        return self._make_processing_state(
            "installing_spine_opt", "<html><p>Installing SpineOpt.jl... See Process log for messages</p></html>"
        )

    def _make_prompt_to_update_spine_opt(self):
        return self._make_prompt_state("prompt_to_update_spine_opt")

    def _update_prompt_to_update_spine_opt(self):
        self.prompt_to_update_spine_opt.assignProperty(
            self.label_msg,
            "text",
            f"<html><p>SpineOpt version {self.spine_opt_version} is installed, "
            f"however {self._preferred_spine_opt_version} is preferred.<p>"
            f"<p>Do you want to update SpineOpt?</p>{self.julia_setup}</html>",
        )

    def _make_updating_spine_opt(self):
        return self._make_processing_state(
            "updating_spine_opt", "<html><p>Updating SpineOpt.jl... See Process log for messages</p></html>"
        )

    def _make_report_failure(self):
        return self._make_report_state("report_failure", "<html><p>Failed!</p></html>")

    def _make_report_spine_opt_ready(self):
        return self._make_report_state(
            "report_spine_opt_ready", "<html><p>Done. SpineOpt.jl is ready to use.</p></html>"
        )

    @busy_effect
    def check_spine_opt_version(self):
        args = self.args.copy()
        args += [
            'import Pkg; '
            'pkgs = Pkg.TOML.parsefile(joinpath(dirname(Base.active_project()), "Manifest.toml")); '
            'spine_opt = get(pkgs, "SpineOpt", nothing); '
            'if spine_opt != nothing println(spine_opt[1]["version"]) end'
        ]
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia, args, silent=True)
        self.exec_mngr.execution_finished.connect(self._handle_check_spine_opt_version_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_check_spine_opt_version_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_check_spine_opt_version_finished)
        if ret != 0:
            self.process_failed.emit()
            return
        self.spine_opt_version = self.exec_mngr.process_output

        if not self.spine_opt_version:
            self.spine_opt_not_found.emit()
            return
        if version_parse(self.spine_opt_version) < version_parse(self._preferred_spine_opt_version):
            self.spine_opt_outdated.emit()
            return
        self.spine_opt_ready.emit()

    @Slot()
    def install_spine_opt(self):
        args = self.args.copy()
        args += [
            'using Pkg; '
            'Pkg.Registry.add(RegistrySpec(url="https://github.com/Spine-project/SpineJuliaRegistry.git")); '
            'Pkg.add("SpineOpt");'
        ]
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_opt_process_finished)
        self.exec_mngr.start_execution()

    @Slot()
    def update_spine_opt(self):
        args = self.args.copy()
        args += ['using Pkg; Pkg.update("SpineOpt")']
        self.exec_mngr = QProcessExecutionManager(self._toolbox, self.julia, args, semisilent=True)
        self.exec_mngr.execution_finished.connect(self._handle_spine_opt_process_finished)
        self.exec_mngr.start_execution()

    @Slot(int)
    def _handle_spine_opt_process_finished(self, ret):
        self.exec_mngr.execution_finished.disconnect(self._handle_spine_opt_process_finished)
        if ret != 0:
            self.process_failed.emit()
            return
        self.spine_opt_ready.emit()

    def set_up_machine(self):
        super().set_up_machine()
        # Create states
        self.checking_spine_opt_version = self._make_checking_spine_opt_version()
        self.prompt_to_install_spine_opt = self._make_prompt_to_install_spine_opt()
        self.prompt_to_update_spine_opt = self._make_prompt_to_update_spine_opt()
        self.installing_spine_opt = self._make_installing_spine_opt()
        self.updating_spine_opt = self._make_updating_spine_opt()
        self.report_spine_opt_ready = self._make_report_spine_opt_ready()
        self.report_failure = self._make_report_failure()
        # Add transitions
        # Prompt accepted
        self.welcome.addTransition(self.welcome.finished, self.checking_spine_opt_version)
        self.prompt_to_install_spine_opt.addTransition(self.button_right.clicked, self.installing_spine_opt)
        self.prompt_to_update_spine_opt.addTransition(self.button_right.clicked, self.updating_spine_opt)
        # SpineOpt not ready, need to do something
        self.checking_spine_opt_version.addTransition(self.spine_opt_not_found, self.prompt_to_install_spine_opt)
        self.checking_spine_opt_version.addTransition(self.spine_opt_outdated, self.prompt_to_update_spine_opt)
        # Ready
        self.checking_spine_opt_version.addTransition(self.spine_opt_ready, self.report_spine_opt_ready)
        self.installing_spine_opt.addTransition(self.spine_opt_ready, self.report_spine_opt_ready)
        self.updating_spine_opt.addTransition(self.spine_opt_ready, self.report_spine_opt_ready)
        # Failure
        self.checking_spine_opt_version.addTransition(self.process_failed, self.report_failure)
        self.installing_spine_opt.addTransition(self.process_failed, self.report_failure)
        self.updating_spine_opt.addTransition(self.process_failed, self.report_failure)
        # Connect signals
        # Launch the process when entering processing states
        self.checking_spine_opt_version.entered.connect(self.check_spine_opt_version)
        self.installing_spine_opt.entered.connect(self.install_spine_opt)
        self.updating_spine_opt.entered.connect(self.update_spine_opt)
        # Update msg
        self.spine_opt_outdated.connect(self._update_prompt_to_update_spine_opt)


def version_parse(version_str):
    return tuple(version_str.split("."))
