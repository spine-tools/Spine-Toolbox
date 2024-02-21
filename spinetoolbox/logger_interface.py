######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""A logger interface."""
from PySide6.QtCore import QObject, Signal


class LoggerInterface(QObject):
    """
    Placeholder for signals that can be emitted to send messages to an output device.

    The signals should be connected to a concrete logging system.

    Currently, this is just a 'model interface'. ToolboxUI contains the same signals so it can be used
    as a drop-in replacement for this class.
    """

    msg = Signal(str)
    """Emits a notification message."""
    msg_success = Signal(str)
    """Emits a message on success"""
    msg_warning = Signal(str)
    """Emits a warning message."""
    msg_error = Signal(str)
    """Emits an error message."""
    msg_proc = Signal(str)
    """Emits a message originating from a subprocess (usually something printed to stdout)."""
    msg_proc_error = Signal(str)
    """Emits an error message originating from a subprocess (usually something printed to stderr)."""
    information_box = Signal(str, str)
    """Requests an 'information message box' (e.g. a message window) to be opened with a given title and message."""
    error_box = Signal(str, str)
    """Requests an 'error message box' to be opened with a given title and message."""
