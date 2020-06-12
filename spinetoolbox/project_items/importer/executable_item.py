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
Contains Importer's executable item as well as support utilities.

:authors: A. Soininen (VTT)
:date:   1.4.2020
"""
import os
import pathlib
from PySide2.QtCore import QObject, QEventLoop, Signal, Slot, QThread
from spinetoolbox.executable_item_base import ExecutableItemBase
from spinetoolbox.spine_io.gdx_utils import find_gams_directory
from .importer_worker import ImporterWorker
from .item_info import ItemInfo
from .utils import deserialize_mappings


class ExecutableItem(ExecutableItemBase, QObject):

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
            cancel_on_error (bool): if True, revert changes on error and quit
            logger (LoggerInterface): a logger
        """
        ExecutableItemBase.__init__(self, name, logger)
        QObject.__init__(self)
        self._settings = settings
        self._logs_dir = logs_dir
        self._python_path = python_path
        self._gams_path = gams_path
        self._cancel_on_error = cancel_on_error
        self._resources_from_downstream = list()
        self._worker = None
        self._worker_thread = None
        self._worker_succeded = None

    @staticmethod
    def item_type():
        """Returns ImporterExecutable's type identifier string."""
        return ItemInfo.item_type()

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
        if not self._settings:
            return True
        absolute_paths = _files_from_resources(resources)
        absolute_path_settings = dict()
        for label in self._settings:
            absolute_path = absolute_paths.get(label)
            if absolute_path is not None:
                absolute_path_settings[absolute_path] = self._settings[label]
        source_settings = {"GdxConnector": {"gams_directory": self._gams_system_directory()}}
        loop = QEventLoop()
        self._destroy_current_worker()
        self._worker = ImporterWorker(
            list(absolute_paths.values()),
            absolute_path_settings,
            source_settings,
            [r.url for r in self._resources_from_downstream if r.type_ == "database"],
            self._logs_dir,
            self._cancel_on_error,
            self._logger,
        )
        self._worker_thread = QThread()
        self._worker.moveToThread(self._worker_thread)
        self._worker.finished.connect(self._handle_worker_finished)
        self._worker.finished.connect(lambda _: loop.quit())
        self._worker_thread.started.connect(loop.exec_)
        self._worker_thread.started.connect(self._worker.do_work)
        self._worker_thread.start()
        if not self._worker_succeded:
            self._logger.msg_error.emit(f"Executing Importer {self.name} failed.")
        else:
            self._logger.msg_success.emit(f"Executing Importer {self.name} finished")
        return self._worker_succeded

    @Slot(int)
    def _handle_worker_finished(self, exit_code):
        self._destroy_current_worker()
        self._worker_succeded = exit_code == 0

    def _destroy_current_worker(self):
        """Runs when starting execution and after worker finishes.
        Destroys current worker and quits thread, if any.
        """
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait()
            self._worker_thread = None

    def _gams_system_directory(self):
        """Returns GAMS system path or None if GAMS default is to be used."""
        path = self._gams_path
        if not path:
            path = find_gams_directory()
        if path is not None and os.path.isfile(path):
            path = os.path.dirname(path)
        return path

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        settings = deserialize_mappings(item_dict["mappings"], project_dir)
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", item_dict["short name"])
        logs_dir = os.path.join(data_dir, "logs")
        python_path = app_settings.value("appSettings/pythonPath", defaultValue="")
        gams_path = app_settings.value("appSettings/gamsPath", defaultValue=None)
        cancel_on_error = item_dict["cancel_on_error"]
        return cls(name, settings, logs_dir, python_path, gams_path, cancel_on_error, logger)


def _files_from_resources(resources):
    """Returns a list of files available in given resources."""
    files = dict()
    for resource in resources:
        if resource.type_ == "file":
            files[resource.path] = resource.path
        elif resource.type_ == "transient_file":
            files[resource.metadata["label"]] = resource.path
    return files
