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

"""Contains LogMixin."""
from .helpers import format_log_message


class LogMixin:
    def add_log_message(self, filter_id, message):
        """Adds a message to the log document.

        Args:
            filter_id (str): filter identifier
            message (str): formatted message
        """
        self._toolbox.add_log_message(self.name, filter_id, message)

    def add_event_message(self, filter_id, msg_type, msg_text):
        """Adds a message to the log document.

        Args:
            filter_id (str): filter identifier
            msg_type (str): message type
            msg_text (str): message text
        """
        message = format_log_message(msg_type, msg_text)
        self.add_log_message(filter_id, message)

    def add_process_message(self, filter_id, msg_type, msg_text):
        """Adds a message to the log document.

        Args:
            filter_id (str): filter identifier
            msg_type (str): message type
            msg_text (str): message text
        """
        message = format_log_message(msg_type, msg_text, show_datetime=False)
        self.add_log_message(filter_id, message)
