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
Contains ImporterExecutable, Importer's executable counterpart as well as support utilities.

:authors: A. Soininen (VTT)
:date:   1.4.2020
"""
import os
from PySide2.QtCore import QObject, QEventLoop, Signal, Slot
from spinetoolbox.config import PYTHON_EXECUTABLE
from spinetoolbox.executable_item import ExecutableItem
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.spine_io.gdx_utils import find_gams_directory
from . import importer_program


class ImporterExecutable(ExecutableItem, QObject):

    importing_finished = Signal()
    """Emitted after the separate import process has finished executing."""

    def __init__(self, name, settings, logs_dir, python_path, gams_path, cancel_on_error, logger):
        """
        Args:
            name (str): Importer's name
            settings (dict): import mappings
            logs_dir (str): path to the directory where logs should be stored
            python_path (str): path to the system's python executable
            gams_path (str): path to system's GAMS executable or empty string for the default path
            cancel_on_error (bool): if True, quit execution on import error
            logger (LoggerInterface): a logger
        """
        ExecutableItem.__init__(self, name, logger)
        QObject.__init__(self)
        self._settings = settings
        self._logs_dir = logs_dir
        self._python_path = python_path
        self._gams_path = gams_path
        self._cancel_on_error = cancel_on_error
        self._resources_from_downstream = list()
        self._importer_process = None
        self._importer_process_successful = None

    @staticmethod
    def item_type():
        """Returns ImporterExecutable's type identifier string."""
        return "Importer"

    def stop_execution(self):
        """Stops executing this ImporterExecutable."""
        super().stop_execution()
        if self._importer_process is None:
            return
        self._importer_process.kill()

    def _execute_backward(self, resources):
        """See base class."""
        self._resources_from_downstream = resources.copy()
        return True

    def _execute_forward(self, resources):
        """See base class."""
        absolute_paths = _files_from_resources(resources)
        absolute_path_settings = dict()
        for label in self._settings:
            absolute_path = absolute_paths.get(label)
            if absolute_path is not None:
                absolute_path_settings[absolute_path] = self._settings[label]
        source_settings = {"GdxConnector": {"gams_directory": self._gams_system_directory()}}
        # Collect arguments for the importer_program
        import_args = [
            list(absolute_paths.values()),
            absolute_path_settings,
            source_settings,
            [r.url for r in self._resources_from_downstream if r.type_ == "database"],
            self._logs_dir,
            self._cancel_on_error,
        ]
        if not self._prepare_importer_program(import_args):
            self._logger.msg_error.emit(f"Executing Importer {self.name} failed.")
            return False
        self._importer_process.start_execution()
        loop = QEventLoop()
        self.importing_finished.connect(loop.quit)
        # Wait for finished right here
        loop.exec_()
        # This should be executed after the import process has finished
        if not self._importer_process_successful:
            self._logger.msg_error.emit(f"Executing Importer {self.name} failed.")
        else:
            self._logger.msg_success.emit(f"Executing Importer {self.name} finished")
        return self._importer_process_successful

    def _prepare_importer_program(self, importer_args):
        """Prepares an execution manager instance for running
        importer_program.py in a QProcess.

        Args:
            importer_args (list): Arguments for the importer_program. Source file paths, their mapping specs,
                URLs downstream, logs directory, cancel_on_error

        Returns:
            bool: True if preparing the program succeeded, False otherwise.

        """
        program_path = os.path.abspath(importer_program.__file__)
        python_cmd = self._python_path if self._python_path else PYTHON_EXECUTABLE
        if not self._python_exists(python_cmd):
            return False
        self._importer_process = QProcessExecutionManager(self._logger, python_cmd, [program_path])
        self._importer_process.execution_finished.connect(self._handle_importer_program_process_finished)
        self._importer_process.data_to_inject = importer_args
        return True

    def _python_exists(self, program):
        """Checks that Python is set up correctly in Settings.
        This executes 'python -V' in a QProcess and if the process
        finishes successfully, the python is ready to be used.

        Args:
            program (str): Python executable that is currently set in Settings

        Returns:
            bool: True if Python is found, False otherwise
        """
        args = ["-V"]
        python_check_process = QProcessExecutionManager(self._logger, program, args, silent=True)
        python_check_process.start_execution()
        if not python_check_process.wait_for_process_finished(msecs=3000):
            self._logger.msg_error.emit(
                "Couldn't execute Python. Please check the <b>Python interpreter</b> option in Settings."
            )
            return False
        return True

    @Slot(int)
    def _handle_importer_program_process_finished(self, exit_code):
        """Handles the return value from importer program when it has finished.
        Emits a signal to indicate that this Importer has been executed.

        Args:
            exit_code (int): Process return value. 0: success, !0: failure
        """
        self._importer_process.execution_finished.disconnect()
        self._importer_process.deleteLater()
        self._importer_process = None
        self._importer_process_successful = exit_code == 0
        self.importing_finished.emit()

    def _gams_system_directory(self):
        """Returns GAMS system path from Toolbox settings or None if GAMS default is to be used."""
        path = self._gams_path
        if not path:
            path = find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path


def _files_from_resources(resources):
    """Returns a list of files available in given resources."""
    files = dict()
    for resource in resources:
        if resource.type_ == "file":
            files[resource.path] = resource.path
        elif resource.type_ == "transient_file":
            files[resource.metadata["label"]] = resource.path
    return files
