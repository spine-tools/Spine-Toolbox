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
Contains Gimlet ExecutableItem class.

:author: P. Savolainen (VTT)
:date:   15.4.2020
"""

import os
import sys
import shutil
import pathlib
import uuid
from PySide2.QtCore import Signal, Slot, QObject, QEventLoop
from spinetoolbox.executable_item_base import ExecutableItemBase
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.project_items.shared import helpers
from spinetoolbox.helpers import shorten
from spinetoolbox.config import DEFAULT_WORK_DIR, GIMLET_WORK_DIR_NAME
from .item_info import ItemInfo
from .utils import SHELLS


class ExecutableItem(ExecutableItemBase, QObject):

    gimlet_finished = Signal()
    """Emitted after the Gimlet process has finished."""

    def __init__(self, name, logger, shell, cmd, work_dir, selected_files):
        """

        Args:
            name (str): Project item name
            logger (LoggerInterface): Logger instance
            shell (str): Shell name or empty string if no shell should be used
            cmd (list): Command to execute
            work_dir (str): Full path to work directory
            selected_files (list): List of file paths that were selected
        """
        ExecutableItemBase.__init__(self, name, logger)
        QObject.__init__(self)
        self.shell_name = shell
        self.cmd_list = cmd
        self._work_dir = work_dir
        self._gimlet_process = None
        self._resources = list()  # Predecessor resources
        self._successor_resources = list()
        self._selected_files = selected_files

    @staticmethod
    def item_type():
        """Returns Gimlet's type identifier string."""
        return ItemInfo.item_type()

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        shell_index = item_dict["shell_index"]
        shell = SHELLS[shell_index]
        cmd_list = helpers.split_cmdline_args(item_dict["cmd"])
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", shorten(name))
        if item_dict["work_dir_mode"]:  # Use 'default' work dir. i.e. data_dir/work
            work_dir = pathlib.Path(data_dir, GIMLET_WORK_DIR_NAME)
        else:  # Make unique work dir
            app_work_dir = app_settings.value("appSettings/workDir", defaultValue=DEFAULT_WORK_DIR)
            if not app_work_dir:
                app_work_dir = DEFAULT_WORK_DIR
            unique_dir_name = "{0}".format(shorten(name)) + "__" + uuid.uuid4().hex + "__toolbox"
            work_dir = os.path.join(app_work_dir, unique_dir_name)
        selected_files = helpers.deserialize_checked_states(item_dict.get("selections", list()), project_dir)
        selections = list()  # Selected files is a dict. Let's make a list.
        for path, boolean in selected_files.items():
            if boolean:
                selections.append(path)
        return cls(name, logger, shell, cmd_list, work_dir, selections)

    def stop_execution(self):
        """Stops executing this Gimlet."""
        self._logger.msg.emit(f"Stopping {self._name}")
        super().stop_execution()
        if self._gimlet_process is None:
            return
        self._gimlet_process.kill()

    def _execute_forward(self, resources):
        """See base class.

        Note: resources given here in args is not used. Files to be copied are
        given by the Gimlet project item based on user selections made in
        Gimlet properties.

        Args:
            resources (list): List of resources from direct predecessor items

        Returns:
            True if execution succeeded, False otherwise
        """
        if not self.cmd_list:
            self._logger.msg_warning.emit("No command to execute.")
            return False
        if sys.platform == "win32" and self.shell_name == "bash":
            self._logger.msg_warning.emit("Sorry, Bash shell is not supported on Windows.")
            return False
        elif sys.platform != "win32" and (self.shell_name == "cmd.exe" or self.shell_name == "powershell.exe"):
            self._logger.msg_warning.emit(f"Sorry, selected shell is not supported on your platform [{sys.platform}]")
            return False
        # Expand tags in command list
        expanded_cmd_list = self._expand_gimlet_tags(self.cmd_list, resources)
        if not self.shell_name:
            prgm = expanded_cmd_list.pop(0)
            self._gimlet_process = QProcessExecutionManager(self._logger, prgm, expanded_cmd_list)
        else:
            if self.shell_name == "cmd.exe":
                shell_prgm = "cmd.exe"
                expanded_cmd_list = ["/C"] + expanded_cmd_list
            elif self.shell_name == "powershell.exe":
                shell_prgm = "powershell.exe"
            elif self.shell_name == "bash":
                shell_prgm = "sh"
            else:
                self._logger.msg_error.emit(f"Unsupported shell: '{self.shell_name}'")
                return False
            self._gimlet_process = QProcessExecutionManager(self._logger, shell_prgm, expanded_cmd_list)
        # Copy selected files to work_dir
        if not self._copy_files(self._selected_files, self._work_dir):
            return False
        # Make work directory anchor with path as tooltip
        work_anchor = (
            "<a style='color:#99CCFF;' title='"
            + self._work_dir
            + "' href='file:///"
            + self._work_dir
            + "'>work directory</a>"
        )
        self._logger.msg.emit(f"*** Executing in <b>{work_anchor}</b> ***")
        self._gimlet_process.execution_finished.connect(self._handle_gimlet_process_finished)
        self._gimlet_process.start_execution(workdir=self._work_dir)
        loop = QEventLoop()
        self.gimlet_finished.connect(loop.quit)
        # Wait for finished right here
        loop.exec_()
        # Copy predecessor's resources so they can be passed to Gimlet's successors
        self._resources = resources.copy()
        # This is executed after the gimlet process has finished
        self._logger.msg_success.emit(f"Executing {self.name} finished")
        return True

    def _execute_backward(self, resources):
        """Executes this item in the backward direction."""
        self._successor_resources = resources.copy()
        return True

    def _output_resources_forward(self):
        """Returns output resources for forward execution.

        Returns:
            (list) List of ProjectItemResources.
        """
        return self._resources

    def _output_resources_backward(self):
        """Returns output resources for backward execution.
        The default implementation returns an empty list.

        Returns:
            (list) List of ProjectItemResources. Just an empty list for now.
        """
        return list()

    @Slot()
    def _handle_gimlet_process_finished(self):
        """Handles clean up after Gimlet process has finished.
        After clean up, emits a signal indicating that this
        project item execution is done.
        """
        self._gimlet_process.execution_finished.disconnect()
        self._gimlet_process.deleteLater()
        self._gimlet_process = None
        self._gimlet_process_successful = True
        self.gimlet_finished.emit()

    def _copy_files(self, files, work_dir):
        """Copies selected resources (files) to work directory.

        Args:
            files (list): List of full paths to files that will be copied to work dir
            work_dir (str): Full path to selected work dir

        Returns:
            bool: True when files were copied successfully, False when something went wrong
        """
        try:
            # Creates work_dir if it does not exist. Note: work_dir will be empty if len(files)==0.
            os.makedirs(work_dir, exist_ok=True)
        except OSError:
            self._logger.msg_error.emit(f"Creating directory <b>{work_dir}</b> failed")
            return False
        n_copied_files = 0
        for f in files:
            src_dir, name = os.path.split(f)
            dst_file = os.path.abspath(os.path.join(work_dir, name))
            try:
                # Copy file
                shutil.copyfile(f, dst_file)
                n_copied_files += 1
            except OSError:
                self._logger.msg_error.emit(f"\tCopying file <b>{f}</b> to <b>{dst_file}</b> failed")
                return False
        if n_copied_files == 0:
            self._logger.msg_warning.emit("\tNote: No files were copied")
        else:
            self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> file(s)")
        return True

    def _expand_gimlet_tags(self, cmd, resources):
        """Returns Gimlet's command as list with special tags expanded.

        Tags that will be replaced:

        - @@optional_inputs@@ expands to a space-separated list of Gimlet's optional input files
        - @@url:<Data Store name>@@ expands to the URL provided by a named data store
        - @@url_inputs@@ expands to a space-separated list of Gimlet's input database URLs
        - @@url_outputs@@ expands to a space-separated list of Gimlet's output database URLs

        Args:
            cmd (list): Command that may include tags that should be expanded
            resources (list): List of resources from direct predecessor items

        Returns:
            list: Expanded command
        """
        files = _file_paths_from_resources(resources)
        input_urls = _database_urls_from_resources(resources)
        output_urls = _database_urls_from_resources(self._successor_resources)
        tags_expanded, args = helpers.expand_tags(cmd, files, input_urls, output_urls)
        while tags_expanded:
            # Keep expanding until there is no tag left to expand.
            tags_expanded, args = helpers.expand_tags(args, files, input_urls, output_urls)
        return args


def _file_paths_from_resources(resources):
    """Pries file paths from resources.

    Args:
        resources (list): a list of ProjectItemResource objects

    Returns:
        list: List of file paths.
    """
    files = list()
    for resource in resources:
        if resource.type_ == "file":
            files.append(resource.path)
    return files


def _database_urls_from_resources(resources):
    """Pries database URLs and their providers' names from resources.

    Args:
        resources (list): a list of ProjectItemResource objects

    Returns:
        dict: a mapping from resource provider's name to a database URL.
    """
    urls = dict()
    for resource in resources:
        if resource.type_ == "database":
            urls[resource.provider.name] = resource.url
    return urls
