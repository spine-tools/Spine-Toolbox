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

from .helpers import MessageType


class LogMixin:

    def add_event_message(self, filter_id: str, msg_type: MessageType, msg_text: str) -> None:
        """Adds a message to the log document.

        Args:
            filter_id: filter identifier
            msg_type: message type
            msg_text: message text
        """
        self._toolbox.add_log_message(self.name, filter_id, msg_type, msg_text)

    def add_process_message(self, filter_id: str, msg_type: MessageType, msg_text: str) -> None:
        """Adds a message to the log document.

        Args:
            filter_id: filter identifier
            msg_type: message type
            msg_text: message text
        """
        self._toolbox.add_log_message(self.name, filter_id, msg_type, msg_text)
