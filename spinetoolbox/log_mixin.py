######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""
Contains LogMixin.

:authors: M. Marin (ER)
:date:    9.12.2021
"""

from .widgets.custom_qtextbrowser import SignedTextDocument
from .helpers import format_log_message, add_message_to_document


class LogMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._log_document = None
        self._filter_log_documents = {}

    @property
    def log_document(self):
        return self._log_document

    @property
    def filter_log_documents(self):
        return self._filter_log_documents

    def _create_filter_log_document(self, filter_id):
        """Creates log document for a filter execution if none yet, and returns it

        Args:
            filter_id (str): filter identifier

        Returns:
            SignedTextDocument
        """
        if filter_id not in self._filter_log_documents:
            self._filter_log_documents[filter_id] = SignedTextDocument(self)
            if self._active:
                self._toolbox.ui.listView_log_executions.model().layoutChanged.emit()
        return self._filter_log_documents[filter_id]

    def _create_log_document(self):
        """Creates log document if none yet, and returns it

        Args:
            filter_id (str): filter identifier

        Returns:
            SignedTextDocument
        """
        if self._log_document is None:
            self._log_document = SignedTextDocument(self)
            if self._active:
                self._toolbox.override_item_log()
        return self._log_document

    def add_log_message(self, filter_id, message):
        """Adds a message to the log document.

        Args:
            filter_id (str): filter identifier
            message (str): formatted message
        """
        if filter_id:
            document = self._create_filter_log_document(filter_id)
        else:
            document = self._create_log_document()
        scrollbar = self._toolbox.ui.textBrowser_itemlog.verticalScrollBar()
        scrollbar_at_max = scrollbar.value() == scrollbar.maximum()
        add_message_to_document(document, message)
        if scrollbar_at_max:  # if scrollbar was at maximum before message was appended -> scroll to bottom
            self._toolbox.ui.textBrowser_itemlog.scroll_to_bottom()

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
