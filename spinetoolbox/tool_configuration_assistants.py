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
Classes for tool configuration assistants.

:authors: M. Marin (KTH)
:date:   10.1.2019
"""

import sys
import os
import qsubprocess
from PySide2.QtCore import QObject, Signal, Slot
from config import JULIA_EXECUTABLE


class SpineModelConfigurationAssistant(QObject):

    check_finished = Signal(name="check_finished")
    installation_finished = Signal(name="installation_finished")
    msg = Signal("QString", name="msg")

    def __init__(self, toolbox):
        super().__init__(toolbox)
        self._toolbox = toolbox
        julia_dir = self._toolbox._config.get("settings", "julia_path")
        if not julia_dir == '':
            julia_exe = os.path.join(julia_dir, JULIA_EXECUTABLE)
        else:
            julia_exe = JULIA_EXECUTABLE
        self.julia_program = "{0}".format(julia_exe)
        self.py_call_python_program = None

    def spine_model_installed_check(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; using SpineModel; println(Pkg.installed()[ARGS[1]]);")
        args.append("SpineModel")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def py_call_program_check(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("using PyCall; println(PyCall.pyprogramname);")
        args.append("")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def spinedatabase_api_installed_check(self):
        program = self.py_call_python_program
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("show")
        args.append("spinedatabase_api")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def install_spine_model(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.clone(ARGS[1], ARGS[2]);")
        args.append("https://github.com/Spine-project/Spine-Model.git")
        args.append("SpineModel")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=False)
        q_process.start_process()
        return q_process

    def install_py_call(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.add(ARGS[1]);")
        args.append("PyCall")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=False)
        q_process.start_process()
        return q_process

    def install_spinedatabase_api(self):
        program = self.py_call_python_program
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("install")
        args.append("git+https://github.com/Spine-project/Spine-Database-API.git")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=False)
        q_process.start_process()
        return q_process

    def reconfigure_py_call(self):
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("using PyCall; ENV[ARGS[1]] = ARGS[2]; try using Pkg catch; end; Pkg.build(ARGS[3])")
        args.append("PYTHON")
        args.append(sys.executable)
        args.append("PyCall")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process
