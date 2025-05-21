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

"""Unit tests for the `setup_focus_widgets` function in SpineDBEditor."""
import unittest
from unittest.mock import patch
from PySide6.QtCore import QEvent
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


class TestSetupFocusWidgets(DBEditorTestBase):
    def test_event_filter_handles_focus_events(self):
        """Test that the eventFilter method handles focus events."""
        focus_event = QEvent(QEvent.Type.FocusIn)
        filter_callback = self.spine_db_editor
        with patch.object(filter_callback, "eventFilter") as mock_event_filter:
            filter_callback.eventFilter(self.spine_db_editor.ui.tableView_parameter_value, focus_event)
            mock_event_filter.assert_called_once_with(self.spine_db_editor.ui.tableView_parameter_value, focus_event)
