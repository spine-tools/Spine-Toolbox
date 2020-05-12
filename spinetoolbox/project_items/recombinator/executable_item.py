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
Contains Recombinator's executable item as well as support utilities.

:authors: A. Soininen (VTT)
:date:   2.4.2020
"""

import os
import pathlib
from PySide2.QtCore import QObject, QEventLoop, Signal, Slot
from spinetoolbox.executable_item_base import ExecutableItemBase
from .item_info import ItemInfo
from . import recombinator_program
from ..shared.helpers import make_python_process


class ExecutableItem(ExecutableItemBase, QObject):

    recombination_finished = Signal()
    """Emitted after the separate recombinator process has finished executing."""

    def __init__(self, name, logs_dir, python_path, cancel_on_error, logger):
        """
        Args:
            name (str): item's name
            logs_dir (str): path to the directory where logs should be stored
            python_path (str): path to the system's python executable
            cancel_on_error (bool): if True, revert changes on error and move on
            logger (LoggerInterface): a logger
        """
        ExecutableItemBase.__init__(self, name, logger)
        QObject.__init__(self)
        self._resources_from_downstream = list()
        self._logs_dir = logs_dir
        self._python_path = python_path
        self._cancel_on_error = cancel_on_error
        self._recombinator_process = None
        self._recombinator_process_successful = None

    @staticmethod
    def item_type():
        """Returns Recombinator's type identifier string."""
        return ItemInfo.item_type()

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", item_dict["short name"])
        logs_dir = os.path.join(data_dir, "logs")
        python_path = app_settings.value("appSettings/pythonPath", defaultValue="")
        cancel_on_error = item_dict["cancel_on_error"]
        return cls(name, logs_dir, python_path, cancel_on_error, logger)

    def _execute_backward(self, resources):
        """See base class."""
        self._resources_from_downstream = resources.copy()
        return True

    @staticmethod
    def _urls_from_resources(resources):
        return [r.url for r in resources if r.type_ == "database"]

    def _execute_forward(self, resources):
        """See base class."""
        from_urls = self._urls_from_resources(resources)
        to_urls = self._urls_from_resources(self._resources_from_downstream)
        if not from_urls or not to_urls:
            # Moving on...
            return True
        recombinator_args = [from_urls, to_urls, self._logs_dir, self._cancel_on_error]
        if not self._prepare_recombinator_program(recombinator_args):
            self._logger.msg_error.emit(f"Executing Recombinator {self.name} failed.")
            return False
        self._recombinator_process.start_execution()
        loop = QEventLoop()
        self.recombination_finished.connect(loop.quit)
        # Wait for finished right here
        loop.exec_()
        # This should be executed after the import process has finished
        if not self._recombinator_process_successful:
            self._logger.msg_error.emit(f"Executing Recombinator {self.name} failed.")
        else:
            self._logger.msg_success.emit(f"Executing Recombinator {self.name} finished")
        return self._recombinator_process_successful

    def _prepare_recombinator_program(self, recombinator_args):
        """Prepares an execution manager instance for running
        recombinator_program.py in a QProcess.

        Args:
            importer_args (list): Arguments for the recombinator_program. From urls, to urls, logs directory

        Returns:
            bool: True if preparing the program succeeded, False otherwise.

        """
        self._recombinator_process = make_python_process(
            recombinator_program.__file__, recombinator_args, self._python_path, self._logger
        )
        if self._recombinator_process is None:
            return False
        self._recombinator_process.execution_finished.connect(self._handle_recombinator_program_process_finished)
        return True

    @Slot(int)
    def _handle_recombinator_program_process_finished(self, exit_code):
        """Handles the return value from recombinator_program.py when it has finished.
        Emits a signal to indicate that this Recombinator has been executed.

        Args:
            exit_code (int): Process return value. 0: success, !0: failure
        """
        self._recombinator_process.execution_finished.disconnect()
        self._recombinator_process.deleteLater()
        self._recombinator_process = None
        self._recombinator_process_successful = exit_code == 0
        self.recombination_finished.emit()
