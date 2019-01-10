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
Classes for package managers.

:authors: M. Marin (KTH)
:date:   10.1.2019
"""

import qsubprocess
from PySide2.QtCore import QObject, Signal, Slot
from config import JULIA_EXECUTABLE


class SpineModelPackageManager(QObject):

    check_finished = Signal(name="check_finished")
    installation_finished = Signal(name="installation_finished")
    msg = Signal("QString", name="msg")

    def __init__(self, toolbox):
        super().__init__(toolbox)
        self._toolbox = toolbox
        self.installation_process = None
        self.check_process = None
        self.check_stage = None
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        self.julia_program = "{0}".format(julia_exe)

    def check(self):
        self.check_stage = 'Checking if SpineModel.jl is installed'
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using SpineModel; println(ARGS[1]) catch; println(ARGS[2]) end;")
        args.append("True")
        args.append("False")
        self.check_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        self.check_process.subprocess_finished_signal.connect(self._handle_spine_model_check_advanced)
        self.check_process.start_process()

    @Slot(int, name="_handle_spine_model_check_finished")
    def _handle_spine_model_check_advanced(self, ret):
        """Run when current stage of check process has finished.

        Args:
            ret (int): Return code given by QSubProcess instance
        """
        if self.check_process.process_failed:
            self.msg.emit("\tCheck failed. Make sure that Julia is correctly installed and try again.")
            self.check_finished.emit()
            return
        if self.check_stage == 'Checking if SpineModel.jl is installed':
            self.msg.emit("SpineModel is correctly installed.")
            self.check_stage = 'Finding PyCall.pyprogramname'
            program = self.julia_program
            args = list()
            args.append("-e")
            args.append("try using PyCall; println(PyCall.pyprogramname) catch; println(ARGS[1]) end;")
            args.append("Not installed")
            self.check_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
            self.check_process.subprocess_finished_signal.connect(self._handle_spine_model_check_advanced)
            self.check_process.start_process()
        elif self.check_stage == 'Finding PyCall.pyprogramname':
            pyprogramname = self.check_process.output
            if pyprogramname == 'Not installed':
                self.msg.emit("PyCall is not installed.")
                self.check_finished.emit()
                return
            self.msg.emit("PyCall is configured to use the python program at \n\t{0}".format(pyprogramname))
            self.check_stage = "Checking if spinedatabase_api is installed"
            program = pyprogramname
            args = list()
            args.append("-m")
            args.append("pip")
            args.append("show")
            args.append("spinedatabase_api")
            self.check_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
            self.check_process.subprocess_finished_signal.connect(self._handle_spine_model_check_advanced)
            self.check_process.start_process()
        elif self.check_stage == 'Checking if spinedatabase_api is installed':
            check_process_output = self.check_process.output
            if not check_process_output:
                self.msg.emit("spinedatabase is not installed in PyCall's python.")
                self.check_finished.emit()
                return
            self.msg.emit("spinedatabase is correctly installed in PyCall's python")
            self.check_finished.emit()

    def install(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.clone(ARGS[1], ARGS[2]);")
        args.append("https://github.com/Spine-project/Spine-Model.git")
        args.append("SpineModel")
        self.installation_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        self.installation_process.subprocess_finished_signal.connect(self._handle_spine_model_installation_finished)
        self.installation_process.start_process()

    @Slot(int, name="_handle_spine_model_installation_finished")
    def _handle_spine_model_installation_finished(self, ret):
        """Run when installation process has finished.

        Args:
            ret (int): Return code given by QSubProcess instance
        """
        if self.installation_process.process_failed:
            self.msg.emit("\tInstallation failed. Make sure that Julia is correctly installed and try again.")
            self.check_finished.emit()
            return
        self.msg.emit("SpineModel.jl was successfully installed")
        self.installation_finished.emit()
