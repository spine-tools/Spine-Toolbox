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
A logger interface.

:authors: A. Soininen (VTT)
:date:   16.1.2020
"""

from PySide2.QtCore import QObject, Signal


class LoggingSignals(QObject):
    """
    Placeholder for signals that can be emitted to send messages to an output device.

    The signals should be connected to a concrete logging system.

    Currently, this is just a 'model interface'. ToolboxUI contains the same signals so it can be used
    instead of this class.
    """

    msg = Signal(str)
    """Emits a notification message."""
    msg_warning = Signal(str)
    """Emits a warning message."""
    msg_error = Signal(str)
    """Emits an error message."""
    dialog = Signal(str, str)
    """Requests an 'information dialog' to be opened with a given title and message"""
