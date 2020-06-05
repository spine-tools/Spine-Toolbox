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
Helper functions and classes.

:authors: M. Marin (KTH)
:date:   12.5.2020
"""

import os
from spinetoolbox.config import PYTHON_EXECUTABLE
from spinetoolbox.execution_managers import QProcessExecutionManager
from spinetoolbox.helpers import deserialize_path, serialize_path


def make_python_process(program, args, python_path, logger):
    """Returns an execution manager instance for running the given program in a QProcess.

    Args:
        program (str): Path to the program file
        importer_args (list): Arguments for the program
        python_path (str): Python executable to check
        logger (LoggerInterface)

    Returns:
        QProcessExecutionManager
    """
    program_path = os.path.abspath(program)
    python_cmd = python_path if python_path else PYTHON_EXECUTABLE
    if not python_exists(python_cmd, logger):
        return None
    process = QProcessExecutionManager(logger, python_cmd, [program_path])
    process.data_to_inject = args
    return process


def python_exists(program, logger):
    """Checks that Python is set up correctly in Settings.
    This executes 'python -V' in a QProcess and if the process
    finishes successfully, the python is ready to be used.

    Args:
        program (str): Python executable to check
        logger (LoggerInterface)

    Returns:
        bool: True if Python is found, False otherwise
    """
    args = ["-V"]
    python_check_process = QProcessExecutionManager(logger, program, args, silent=True)
    python_check_process.start_execution()
    if not python_check_process.wait_for_process_finished(msecs=3000):
        logger.msg_error.emit("Couldn't execute Python. Please check the <b>Python interpreter</b> option in Settings.")
        return False
    return True


def serialize_checked_states(files, project_path):
    """Serializes file paths and adds a boolean value
    for each, which indicates whether the path is
    selected or not. Used in saving checked file states to
    project.json.

    Args:
        files (list): List of absolute file paths
        project_path (str): Absolute project directory path

    Returns:
        list: List of serialized paths with a boolean value
    """
    return [[serialize_path(item.label, project_path), item.selected] for item in files]


def deserialize_checked_states(serialized, project_path):
    """Reverse operation for serialize_checked_states above.
    Returns absolute file paths with their check state as boolean.

    Args:
        serialized (list): List of serialized paths with a boolean value
        project_path (str): Absolute project directory path

    Returns:
        dict: Dictionary with paths as keys and boolean check states as value
    """
    if not serialized:
        return dict()
    deserialized = dict()
    for serialized_label, checked in serialized:
        label = deserialize_path(serialized_label, project_path)
        deserialized[label] = checked
    return deserialized
