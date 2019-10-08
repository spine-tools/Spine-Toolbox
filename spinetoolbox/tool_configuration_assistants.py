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

from PySide2.QtCore import QObject, Signal
from .config import JULIA_EXECUTABLE
from .helpers import busy_effect
from . import qsubprocess


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
        if julia_path != "":
            self.julia_exe = julia_path
        else:
            self.julia_exe = JULIA_EXECUTABLE
        self.julia_project_path = self._toolbox.qsettings().value("appSettings/juliaProjectPath", defaultValue="")
        if self.julia_project_path == "":
            self.julia_project_path = "@."
        self._julia_version = None
        self._julia_active_project = None
        self.find_out_julia_version_and_project()

    @busy_effect
    def find_out_julia_version_and_project(self):
        args = list()
        args.append("-e")
        args.append("println(VERSION)")
        q_process = qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=True)
        q_process.start_process()
        if q_process.wait_for_finished(msecs=5000):
            self._julia_version = q_process.output
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("println(Base.active_project())")
        q_process = qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=True)
        q_process.start_process()
        if q_process.wait_for_finished(msecs=5000):
            self._julia_active_project = q_process.output

    def julia_version(self):
        """Return current julia version."""
        return self._julia_version

    def julia_active_project(self):
        """Return current julia active project."""
        return self._julia_active_project

    def spine_model_version_check(self):
        """Return qsubprocess that checks current version of SpineModel.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.update(ARGS[1]);")
        args.append("SpineModel")
        return qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=True)

    def py_call_program_check(self):
        """Return qsubprocess that checks the python program used by PyCall in current julia version.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using PyCall; println(PyCall.pyprogramname);")
        return qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=True)

    def install_spine_model(self):
        """Return qsubprocess that installs SpineModel in current julia version.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.add(PackageSpec(url=ARGS[1])); Pkg.add(PackageSpec(url=ARGS[2]));")
        args.append("https://github.com/Spine-project/SpineInterface.jl.git")
        args.append("https://github.com/Spine-project/Spine-Model.git")
        return qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=False)

    def install_py_call(self):
        """Return qsubprocess that installs PyCall in current julia version.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using Pkg; Pkg.add(ARGS[1]);")
        args.append("PyCall")
        return qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=False)

    def reconfigure_py_call(self, pyprogramname):
        """Return qsubprocess that reconfigure PyCall to use given python program.
        """
        args = list()
        args.append(f"--project={self.julia_project_path}")
        args.append("-e")
        args.append("using PyCall; ENV[ARGS[1]] = ARGS[2]; using Pkg; Pkg.build(ARGS[3]);")
        args.append("PYTHON")
        args.append(pyprogramname)
        args.append("PyCall")
        return qsubprocess.QSubProcess(self._toolbox, self.julia_exe, args, silent=True)
