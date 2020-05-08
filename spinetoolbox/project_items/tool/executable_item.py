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
Contains Tool's executable item and support functionality.

:authors: A. Soininen (VTT)
:date:   30.3.2020
"""

import datetime
import fnmatch
import glob
import os.path
import pathlib
import shutil
import time
import uuid
from PySide2.QtCore import QEventLoop, Slot
from spinetoolbox.config import DEFAULT_WORK_DIR, TOOL_OUTPUT_DIR
from spinetoolbox.executable_item_base import ExecutableItemBase
from spinetoolbox.project_item_resource import ProjectItemResource
from .item_info import ItemInfo
from .utils import (
    file_paths_from_resources,
    find_file,
    find_last_output_files,
    flatten_file_path_duplicates,
    is_pattern,
)


class ExecutableItem(ExecutableItemBase):
    """Tool project item's executable parts."""

    def __init__(self, name, work_dir, output_dir, tool_specification, cmd_line_args, logger):
        """
        Args:
            name (str): item's name
            work_dir (str): an absolute path to Spine Toolbox work directory
                or None if the Tool should not execute in work directory
            output_dir (str): path to the directory where output files should be archived
            tool_specification (ToolSpecification): a tool specification
            cmd_line_args (list): a list of command line argument to pass to the tool instance
            logger (LoggerInterface): a logger
        """
        super().__init__(name, logger)
        self._work_dir = work_dir
        self._output_dir = output_dir
        self._tool_specification = tool_specification
        self._cmd_line_args = cmd_line_args
        self._downstream_resources = list()
        self._tool_instance = None
        self._last_return_code = None

    @staticmethod
    def item_type():
        """Returns the item's type identifier string."""
        return ItemInfo.item_type()

    def execution_finished(self, execution_token, return_code, execution_dir):
        """Handles things after execution has finished."""
        self._last_return_code = return_code
        # Disconnect instance finished signal
        self._tool_instance.instance_finished.disconnect(execution_token.handle_execution_finished)
        if return_code == 0:
            self._logger.msg_success.emit(f"Tool <b>{self._name}</b> execution finished")
        else:
            self._logger.msg_error.emit(f"Tool <b>{self._name}</b> execution failed")
        self._handle_output_files(return_code, execution_dir)
        self._tool_instance = None

    def stop_execution(self):
        """Stops executing this Tool."""
        super().stop_execution()
        if self._tool_instance is not None and self._tool_instance.is_running():
            self._tool_instance.terminate_instance()
            self._tool_instance = None

    def _copy_input_files(self, paths, execution_dir):
        """
        Copies input files from given paths to work or source directory, depending on
        where the Tool specification requires them to be.

        Args:
            paths (dict): key is path to destination file, value is path to source file
            execution_dir (str): absolute path to the execution directory

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        n_copied_files = 0
        for dst, src_path in paths.items():
            if not os.path.exists(src_path):
                self._logger.msg_error.emit(f"\tFile <b>{src_path}</b> does not exist")
                return False
            # Join work directory path to dst (dst is the filename including possible subfolders, e.g. 'input/f.csv')
            dst_path = os.path.abspath(os.path.join(execution_dir, dst))
            # Create subdirectories if necessary
            dst_subdir, _ = os.path.split(dst)
            if not dst_subdir:
                # No subdirectories to create
                self._logger.msg.emit(f"\tCopying <b>{src_path}</b>")
            else:
                # Create subdirectory structure to work or source directory
                work_subdir_path = os.path.abspath(os.path.join(execution_dir, dst_subdir))
                if not os.path.exists(work_subdir_path):
                    try:
                        os.makedirs(work_subdir_path, exist_ok=True)
                    except OSError:
                        self._logger.msg_error.emit(f"[OSError] Creating directory <b>{work_subdir_path}</b> failed.")
                        return False
                self._logger.msg.emit(f"\tCopying <b>{src_path}</b> into subdirectory <b>{os.path.sep}{dst_subdir}</b>")
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                self._logger.msg_error.emit(f"Copying file <b>{src_path}</b> to <b>{dst_path}</b> failed")
                self._logger.msg_error.emit(f"{e}")
                if e.errno == 22:
                    msg = (
                        "The reason might be:\n"
                        "[1] The destination file already exists and it cannot be "
                        "overwritten because it is locked by Julia or some other application.\n"
                        "[2] You don't have the necessary permissions to overwrite the file.\n"
                        "To solve the problem, you can try the following:\n[1] Execute the Tool in work "
                        "directory.\n[2] If you are executing a Julia Tool with Julia 0.6.x, upgrade to "
                        "Julia 0.7 or newer.\n"
                        "[3] Close any other background application(s) that may have locked the file.\n"
                        "And try again.\n"
                    )
                    self._logger.msg_warning.emit(msg)
                return False
        self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> input file(s)")
        return True

    def _copy_optional_input_files(self, paths):
        """
        Copies optional input files from given paths to work or source directory, depending on
        where the Tool specification requires them to be.

        Args:
            paths (dict): key is the source path, value is the destination path
        """
        n_copied_files = 0
        for src_path, dst_path in paths.items():
            try:
                shutil.copyfile(src_path, dst_path)
                n_copied_files += 1
            except OSError as e:
                self._logger.msg_error.emit(f"Copying optional file <b>{src_path}</b> to <b>{dst_path}</b> failed")
                self._logger.msg_error.emit(f"{e}")
                if e.errno == 22:
                    msg = (
                        "The reason might be:\n"
                        "[1] The destination file already exists and it cannot be "
                        "overwritten because it is locked by Julia or some other application.\n"
                        "[2] You don't have the necessary permissions to overwrite the file.\n"
                        "To solve the problem, you can try the following:\n[1] Execute the Tool in work "
                        "directory.\n[2] If you are executing a Julia Tool with Julia 0.6.x, upgrade to "
                        "Julia 0.7 or newer.\n"
                        "[3] Close any other background application(s) that may have locked the file.\n"
                        "And try again.\n"
                    )
                    self._logger.msg_warning.emit(msg)
        self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> optional input file(s)")

    def _copy_output_files(self, target_dir, execution_dir):
        """Copies Tool specification output files from work directory to given target directory.

        Args:
            target_dir (str): Destination directory for Tool specification output files
            execution_dir (str): path to the execution directory

        Returns:
            tuple: Contains two lists. The first list contains paths to successfully
            copied files. The second list contains paths (or patterns) of Tool specification
            output files that were not found.

        Raises:
            OSError: If creating a directory fails.
        """
        failed_files = list()
        saved_files = list()
        for pattern in self._tool_specification.outputfiles:
            # Create subdirectories if necessary
            dst_subdir, fname_pattern = os.path.split(pattern)
            target = os.path.abspath(os.path.join(target_dir, dst_subdir))
            if not os.path.exists(target):
                try:
                    os.makedirs(target, exist_ok=True)
                except OSError:
                    self._logger.msg_error.emit(f"[OSError] Creating directory <b>{target}</b> failed.")
                    continue
                self._logger.msg.emit(f"\tCreated result subdirectory <b>{os.path.sep}{dst_subdir}</b>")
            # Check for wildcards in pattern
            if is_pattern(pattern):
                for fname_path in glob.glob(os.path.abspath(os.path.join(execution_dir, pattern))):
                    # fname_path is a full path
                    fname = os.path.split(fname_path)[1]  # File name (no path)
                    dst = os.path.abspath(os.path.join(target, fname))
                    full_fname = os.path.join(dst_subdir, fname)
                    try:
                        shutil.copyfile(fname_path, dst)
                        saved_files.append((full_fname, dst))
                    except OSError:
                        self._logger.msg_error.emit(f"[OSError] Copying pattern {fname_path} to {dst} failed")
                        failed_files.append(full_fname)
            else:
                output_file = os.path.abspath(os.path.join(execution_dir, pattern))
                if not os.path.isfile(output_file):
                    failed_files.append(pattern)
                    continue
                dst = os.path.abspath(os.path.join(target, fname_pattern))
                try:
                    shutil.copyfile(output_file, dst)
                    saved_files.append((pattern, dst))
                except OSError:
                    self._logger.msg_error.emit(f"[OSError] Copying output file {output_file} to {dst} failed")
                    failed_files.append(pattern)
        return saved_files, failed_files

    def _copy_program_files(self, execution_dir):
        """Copies Tool specification source files to base directory."""
        # Make work directory anchor with path as tooltip
        work_anchor = "<a style='color:#99CCFF;' title='{0}' href='file:///{0}'>work directory</a>".format(
            execution_dir
        )
        self._logger.msg.emit(
            f"*** Copying Tool specification <b>{self._tool_specification.name}</b> program files to {work_anchor} ***"
        )
        n_copied_files = 0
        for source_pattern in self._tool_specification.includes:
            dir_name, file_pattern = os.path.split(source_pattern)
            src_dir = os.path.join(self._tool_specification.path, dir_name)
            dst_dir = os.path.join(execution_dir, dir_name)
            # Create the destination directory
            try:
                os.makedirs(dst_dir, exist_ok=True)
            except OSError:
                self._logger.msg_error.emit(f"Creating directory <b>{dst_dir}</b> failed")
                return False
            # Copy file if necessary
            if file_pattern:
                for src_file in glob.glob(os.path.abspath(os.path.join(src_dir, file_pattern))):
                    dst_file = os.path.abspath(os.path.join(dst_dir, os.path.basename(src_file)))
                    try:
                        shutil.copyfile(src_file, dst_file)
                        n_copied_files += 1
                    except OSError:
                        self._logger.msg_error.emit(f"\tCopying file <b>{src_file}</b> to <b>{dst_file}</b> failed")
                        return False
        if n_copied_files == 0:
            self._logger.msg_warning.emit("Warning: No files copied")
        else:
            self._logger.msg.emit(f"\tCopied <b>{n_copied_files}</b> file(s)")
        return True

    def _create_input_dirs(self, execution_dir):
        """Iterates items in required input files and check
        if there are any directories to create. Create found
        directories directly to work or source directory.

        Args:
            execution_dir (str): the execution directory

        Returns:
            bool: True if the operation was successful, False otherwiseBoolean variable depending on success
        """
        for required_path in self._tool_specification.inputfiles:
            path, filename = os.path.split(required_path)
            if filename:
                continue
            path_to_create = os.path.join(execution_dir, path)
            try:
                os.makedirs(path_to_create, exist_ok=True)
            except OSError:
                self._logger.msg_error.emit(f"[OSError] Creating directory {path_to_create} failed. Check permissions.")
                return False
            self._logger.msg.emit(f"\tDirectory <b>{os.path.sep}{path}</b> created")
        return True

    def _create_output_dirs(self, execution_dir):
        """Makes sure that work directory has the necessary output directories for Tool output files.
        Checks only "outputfiles" list. Alternatively you can add directories to "inputfiles" list
        in the tool definition file.

        Args:
            execution_dir (str): a path to the execution directory

        Returns:
            bool: True for success, False otherwise.

        Raises:
            OSError: If creating an output directory to work fails.
        """
        for out_file_path in self._tool_specification.outputfiles:
            dirname = os.path.split(out_file_path)[0]
            if not dirname:
                continue
            dst_dir = os.path.join(execution_dir, dirname)
            try:
                os.makedirs(dst_dir, exist_ok=True)
            except OSError:
                self._logger.msg_error.emit(f"Creating work output directory '{dst_dir}' failed")
                return False
        return True

    def _execute_backward(self, resources):
        """Stores resources for forward execution."""
        self._downstream_resources = resources.copy()
        return True

    def _execute_forward(self, resources):
        """
        Executes the Tool according to the Tool specification.

        Before launching the tool script in a separate instance,
        prepares the execution environment by creating all necessary directories
        and copying input files where needed.
        After execution archives the output files.

        Args:
            resources (list): a list of resources from direct predecessor items
        Returns:
            True if execution succeeded, False otherwise
        """
        if self._tool_specification is None:
            self._logger.msg_warning.emit(f"Tool <b>{self.name}</b> has no Tool specification to execute")
            return False
        execution_dir = _execution_directory(self._work_dir, self._tool_specification)
        if execution_dir is None:
            return False
        if self._work_dir is not None:
            work_or_source = "work"
            # Make work directory anchor with path as tooltip
            work_anchor = (
                "<a style='color:#99CCFF;' title='"
                + execution_dir
                + "' href='file:///"
                + execution_dir
                + "'>work directory</a>"
            )
            self._logger.msg.emit(
                f"*** Copying Tool specification <b>{self._tool_specification.name}"
                f"</b> source files to {work_anchor} ***"
            )
            if not self._copy_program_files(execution_dir):
                self._logger.msg_error.emit("Copying program files to base directory failed.")
                return False
        else:
            work_or_source = "source"
        # Make source directory anchor with path as tooltip
        anchor = (
            f"<a style='color:#99CCFF;' title='{execution_dir}'"
            f"href='file:///{execution_dir}'>{work_or_source} directory</a>"
        )
        self._logger.msg.emit(
            f"*** Executing Tool specification <b>{self._tool_specification.name}</b> in {anchor} ***"
        )
        # Find required input files for ToolInstance (if any)
        if self._tool_specification.inputfiles:
            self._logger.msg.emit("*** Checking Tool specification requirements ***")
            n_dirs, n_files = _count_files_and_dirs(self._tool_specification.inputfiles)
            if n_files > 0:
                self._logger.msg.emit("*** Searching for required input files ***")
                file_paths = flatten_file_path_duplicates(
                    self._find_input_files(resources), self._logger, log_duplicates=True
                )
                not_found = [k for k, v in file_paths.items() if v is None]
                if not_found:
                    self._logger.msg_error.emit(f"Required file(s) <b>{', '.join(not_found)}</b> not found")
                    return False
                self._logger.msg.emit(f"*** Copying input files to {work_or_source} directory ***")
                # Copy input files to ToolInstance work or source directory
                if not self._copy_input_files(file_paths, execution_dir):
                    self._logger.msg_error.emit("Copying input files failed. Tool execution aborted.")
                    return False
            if n_dirs > 0:
                self._logger.msg.emit(f"*** Creating input subdirectories to {work_or_source} directory ***")
                if not self._create_input_dirs(execution_dir):
                    # Creating directories failed -> abort
                    self._logger.msg_error.emit("Creating input subdirectories failed. Tool execution aborted.")
                    return False
        optional_file_copy_paths = dict()
        if self._tool_specification.inputfiles_opt:
            self._logger.msg.emit("*** Searching for optional input files ***")
            optional_file_paths = self._find_optional_input_files(resources)
            for k, v in optional_file_paths.items():
                self._logger.msg.emit(f"\tFound <b>{len(v)}</b> files matching pattern <b>{k}</b>")
            optional_file_copy_paths = self._optional_output_destination_paths(optional_file_paths, execution_dir)
            self._copy_optional_input_files(optional_file_copy_paths)
        if not self._create_output_dirs(execution_dir):
            self._logger.msg_error.emit("Creating output subdirectories failed. Tool execution aborted.")
            return False
        input_database_urls = _database_urls_from_resources(resources)
        output_database_urls = _database_urls_from_resources(self._downstream_resources)
        self._tool_instance = self._tool_specification.create_tool_instance(execution_dir)

        try:
            self._tool_instance.prepare(
                list(optional_file_copy_paths.values()), input_database_urls, output_database_urls, self._cmd_line_args
            )
        except RuntimeError as error:
            self._logger.msg_error.emit(f"Failed to prepare tool instance: {error}")
            return False
        execution_token = _ExecutionToken(self, execution_dir)
        self._tool_instance.instance_finished.connect(execution_token.handle_execution_finished)
        self._logger.msg.emit(f"*** Starting instance of Tool specification <b>{self._tool_specification.name}</b> ***")
        # Wait for finished right here
        loop = QEventLoop()
        self._tool_instance.instance_finished.connect(loop.quit)
        self._tool_instance.execute()
        if self._tool_instance.is_running():
            loop.exec_()
        return self._last_return_code == 0

    def _find_input_files(self, resources):
        """
        Iterates required input  files in tool specification and looks for them in the given resources.

        Args:
            resources (list): resources available

        Returns:
            Dictionary mapping required files to path where they are found, or to None if not found
        """
        file_paths = dict()
        for required_path in self._tool_specification.inputfiles:
            _, filename = os.path.split(required_path)
            if not filename:
                # It's a directory
                continue
            file_paths[required_path] = find_file(filename, resources)
        return file_paths

    def _find_optional_input_files(self, resources):
        """
        Tries to find optional input files from previous project items in the DAG.

        Args:
            resources (list): resources available

        Returns:
            dict: Dictionary of optional input file paths or an empty dictionary if no files found. Key is the
                optional input item and value is a list of paths that matches the item.
        """
        file_paths = dict()
        paths_in_resources = file_paths_from_resources(resources)
        for file_path in self._tool_specification.inputfiles_opt:
            _, pattern = os.path.split(file_path)
            if not pattern:
                # It's a directory -> skip
                continue
            found_files = _find_files_in_pattern(pattern, paths_in_resources)
            if not found_files:
                self._logger.msg_warning.emit(f"\tNo files matching pattern <b>{pattern}</b> found")
            else:
                file_paths[file_path] = found_files
        return file_paths

    def _handle_output_files(self, return_code, execution_dir):
        """Copies Tool specification output files from work directory to result directory.

        Args:
            return_code (int): Tool specification process return value
            execution_dir (str): path to the execution directory
        """
        output_dir_timestamp = _create_output_dir_timestamp()  # Get timestamp when tool finished
        # Create an output folder with timestamp and copy output directly there
        if return_code != 0:
            result_path = os.path.abspath(os.path.join(self._output_dir, 'failed', output_dir_timestamp))
        else:
            result_path = os.path.abspath(os.path.join(self._output_dir, output_dir_timestamp))
        try:
            os.makedirs(result_path, exist_ok=True)
        except OSError:
            self._logger.msg_error.emit(
                "\tError creating timestamped output directory. "
                "Tool specification output files not copied. Please check directory permissions."
            )
            return
        # Make link to output folder
        result_anchor = (
            f"<a style='color:#BB99FF;' title='{result_path}'" f"href='file:///{result_path}'>results directory</a>"
        )
        self._logger.msg.emit(f"*** Archiving output files to {result_anchor} ***")
        if self._tool_specification.outputfiles:
            saved_files, failed_files = self._copy_output_files(result_path, execution_dir)
            if not saved_files:
                # If no files were saved
                self._logger.msg_error.emit("\tNo files saved")
            else:
                # If there are saved files
                # Split list into filenames and their paths
                filenames, _ = zip(*saved_files)
                self._logger.msg.emit("\tThe following output files were saved to results directory")
                for filename in filenames:
                    self._logger.msg.emit(f"\t\t<b>{filename}</b>")
            if failed_files:
                # If saving some or all files failed
                self._logger.msg_warning.emit("\tThe following output files were not found")
                for failed_file in failed_files:
                    failed_fname = os.path.split(failed_file)[1]
                    self._logger.msg_warning.emit(f"\t\t<b>{failed_fname}</b>")
        else:
            tip_anchor = (
                "<a style='color:#99CCFF;' title='When you add output files to the Tool specification,\n "
                "they will be archived into results directory. Also, output files are passed to\n "
                "subsequent project items.' href='#'>Tip</a>"
            )
            self._logger.msg_warning.emit(f"\tNo output files defined for this Tool specification. {tip_anchor}")

    def _optional_output_destination_paths(self, paths, execution_dir):
        """
        Returns a dictionary telling where optional output files should be copied to before execution.

        Args:
            paths (dict): key is the optional file name pattern, value is a list of paths to source files
            execution_dir (str): a path to the execution directory
        Returns:
            dict: a map from source path to destination path
        """
        destination_paths = dict()
        for dst, src_paths in paths.items():
            for src_path in src_paths:
                if not os.path.exists(src_path):
                    self._logger.msg_error.emit(f"\tFile <b>{src_path}</b> does not exist")
                    continue
                # Get file name that matched the search pattern
                _, dst_fname = os.path.split(src_path)
                # Check if the search pattern included subdirectories (e.g. 'input/*.csv')
                # This means that /input/ directory should be created to work (or source) directory
                # before copying the files
                dst_subdir, _search_pattern = os.path.split(dst)
                if not dst_subdir:
                    # No subdirectories to create
                    self._logger.msg.emit(f"\tCopying optional file <b>{dst_fname}</b>")
                    dst_path = os.path.abspath(os.path.join(execution_dir, dst_fname))
                else:
                    # Create subdirectory structure to work or source directory
                    work_subdir_path = os.path.abspath(os.path.join(execution_dir, dst_subdir))
                    if not os.path.exists(work_subdir_path):
                        try:
                            os.makedirs(work_subdir_path, exist_ok=True)
                        except OSError:
                            self._logger.msg_error.emit(
                                f"[OSError] Creating directory <b>{work_subdir_path}</b> failed."
                            )
                            continue
                    self._logger.msg.emit(
                        f"\tCopying optional file <b>{dst_fname}</b> into subdirectory <b>{os.path.sep}{dst_subdir}</b>"
                    )
                    dst_path = os.path.abspath(os.path.join(work_subdir_path, dst_fname))
                destination_paths[src_path] = dst_path
        return destination_paths

    def _output_resources_forward(self):
        """
        Returns a list of resources, i.e. the output files produced by the tool.

        Returns the files that were actually created during the execution.
        The URL points to the archive directory.

        Returns:
            list: a list of Tool's output resources
        """
        resources = list()
        last_output_files = find_last_output_files(self._tool_specification.outputfiles, self._output_dir)
        for out_file_label in self._tool_specification.outputfiles:
            latest_files = last_output_files.get(out_file_label, list())
            for out_file in latest_files:
                file_url = pathlib.Path(out_file.path).as_uri()
                metadata = {"label": out_file.label}
                resource = ProjectItemResource(self, "transient_file", url=file_url, metadata=metadata)
                resources.append(resource)
        return resources

    @classmethod
    def from_dict(cls, item_dict, name, project_dir, app_settings, specifications, logger):
        """See base class."""
        execute_in_work = item_dict["execute_in_work"]
        if execute_in_work:
            work_dir = app_settings.value("appSettings/workDir", defaultValue=DEFAULT_WORK_DIR)
            if not work_dir:
                work_dir = DEFAULT_WORK_DIR
        else:
            work_dir = None
        data_dir = pathlib.Path(project_dir, ".spinetoolbox", "items", item_dict["short name"])
        output_dir = pathlib.Path(data_dir, TOOL_OUTPUT_DIR)
        specification_name = item_dict["tool"]
        if not specification_name:
            logger.msg_error.emit(f"<b>{name}<b>: No tool specification defined. Unable to execute.")
            return None
        try:
            specification = specifications[specification_name]
        except KeyError as missing_specification:
            logger.msg_error.emit(f"Cannot find tool specification '{missing_specification}'.")
            return None
        cmd_line_args = item_dict["cmd_line_args"]
        return cls(name, work_dir, output_dir, specification, cmd_line_args, logger)


def _count_files_and_dirs(paths):
    """
    Counts the number of files and directories in given paths.

    Args:
        paths (list): list of paths

    Returns:
        Tuple containing the number of required files and directories.
    """
    n_dir = 0
    n_file = 0
    for path in paths:
        _, filename = os.path.split(path)
        if not filename:
            n_dir += 1
        else:
            n_file += 1
    return n_dir, n_file


def _create_output_dir_timestamp():
    """ Creates a new timestamp string that is used as Tool output
    directory.

    Returns:
        Timestamp string or empty string if failed.
    """
    try:
        # Create timestamp
        stamp = datetime.datetime.fromtimestamp(time.time())
    except OverflowError:
        return ""
    extension = stamp.strftime('%Y-%m-%dT%H.%M.%S')
    return extension


def _database_urls_from_resources(resources):
    """
    Pries database URLs and their providers' names from resources.

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


def _execution_directory(work_dir, tool_specification):
    """
    Returns the path to the execution directory, depending on ``execute_in_work``.

    If ``execute_in_work`` is ``True``, a new unique path will be returned.
    Otherwise, the main program file path from tool specification is returned.

    Returns:
        str: a full path to next basedir
    """
    if work_dir is not None:
        basedir = os.path.join(work_dir, _unique_dir_name(tool_specification))
        return basedir
    return tool_specification.path


def _find_files_in_pattern(pattern, available_file_paths):
    """
    Returns a list of files that match the given pattern.

    Args:
        pattern (str): file pattern
        available_file_paths (list): list of available file paths from upstream items
    Returns:
        list: List of (full) paths
    """
    extended_pattern = os.path.join("*", pattern)  # Match all absolute paths.
    return fnmatch.filter(available_file_paths, extended_pattern)


def _unique_dir_name(tool_specification):
    """Builds a unique name for Tool's work directory."""
    return tool_specification.short_name + "__" + uuid.uuid4().hex + "__toolbox"


class _ExecutionToken:
    """
    A token that acts as a callback after the tool process has finished execution.
    """

    def __init__(self, tool_executable, execution_dir):
        """
        Args:
            tool_executable (ExecutableItem): the object that has initiated the execution
            execution_dir (str): absolute path to the execution working directory
        """
        self._tool_executable = tool_executable
        self._execution_dir = execution_dir

    @Slot(int)
    def handle_execution_finished(self, return_code):
        """
        Handles Tool specification execution finished.

        Args:
            return_code (int): Process exit code
        """
        self._tool_executable.execution_finished(self, return_code, self._execution_dir)
