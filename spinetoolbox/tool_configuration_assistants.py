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
Classes for tool configuration assistants.

:authors: M. Marin (KTH)
:date:   10.1.2019
"""

import sys
import qsubprocess
from PySide2.QtCore import QObject, Signal
from config import JULIA_EXECUTABLE


class SpineModelConfigurationAssistant(QObject):
    """Configuration assistant for SpineModel.jl.

    Attributes:
        toolbox (ToolboxUI): QMainWindow instance
    """

    check_finished = Signal(name="check_finished")
    installation_finished = Signal(name="installation_finished")
    msg = Signal("QString", name="msg")

    def __init__(self, toolbox):
        """Init class."""
        super().__init__(toolbox)
        self._toolbox = toolbox
        julia_path = self._toolbox.qsettings().value("appSettings/juliaPath", defaultValue="")
        if not julia_path == "":
            julia_exe = julia_path
        else:
            julia_exe = JULIA_EXECUTABLE
        self.julia_program = "{0}".format(julia_exe)
        self.py_call_python_program = None

    def julia_version(self):
        """Return current julia version."""
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        if not q_process.wait_for_finished(msecs=5000):
            return None
        return q_process.output

    def spine_model_installed_check(self):
        """Start qsubprocess that checks if SpineModel is installed in current julia version.
        Return the qsubprocess.
        """
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; using SpineModel; println(Pkg.installed()[ARGS[1]]);")
        args.append("SpineModel")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def py_call_program_check(self):
        """Start qsubprocess that checks the python program used by PyCall in current julia version.
        Return the qsubprocess.
        """
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("using PyCall; println(PyCall.pyprogramname);")
        args.append("")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def spinedb_api_installed_check(self):
        """Start qsubprocess that checks if spinedb_api is installed in PyCall's python.
        Return the qsubprocess.
        """
        program = self.py_call_python_program
        args = list()
        args.append("-m")
        args.append("pip")
        args.append("show")
        args.append("spinedb_api")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=True)
        q_process.start_process()
        return q_process

    def install_spine_model(self):
        """Start qsubprocess that installs SpineModel in current julia version.
        Return the qsubprocess.
        """
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
        """Start qsubprocess that installs PyCall in current julia version.
        Return the qsubprocess.
        """
        program = self.julia_program
        args = list()
        args.append("-e")
        args.append("try using Pkg catch; end; Pkg.add(ARGS[1]);")
        args.append("PyCall")
        q_process = qsubprocess.QSubProcess(self._toolbox, program, args, silent=False)
        q_process.start_process()
        return q_process

    def install_spinedb_api(self):
        """Start qsubprocess that installs spinedb_api in PyCall's python.
        Return the qsubprocess.
        """
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
        """Start qsubprocess that reconfigure PyCall to point to Spine Toolbox's python.
        Return the qsubprocess.
        """
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
