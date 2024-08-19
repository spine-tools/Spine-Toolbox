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

"""Unit tests for ``custom_qgraphicsviews`` module."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QWidget
from spinetoolbox.spine_db_editor.widgets.custom_qgraphicsviews import EntityQGraphicsView
from tests.mock_helpers import TestCaseWithQApplication


class TestGraphOptionsOverlay(TestCaseWithQApplication):
    """Tests for the class GraphOptionsOverlay"""

    def setUp(self):
        self._parent = QWidget()
        self.graph = EntityQGraphicsView(self._parent)
        self.mock_editor = mock.MagicMock()
        self.graph.connect_spine_db_editor(self.mock_editor)

    def test_auto_build_consistent_between_overlay_and_context_menu(self):
        """Check that the overlay widget and the context menu are synced."""
        self.assertFalse(self.graph._options_overlay._auto_build_button.isChecked())
        self.assertFalse(self.graph.get_property("auto_build"))
        # Toggle from context menu.
        self.graph._options_overlay._auto_build_button.toggle()
        self.assertTrue(self.graph._options_overlay._auto_build_button.isChecked())
        self.assertTrue(self.graph.get_property("auto_build"))
        # Toggle from overlay.
        self.graph._properties["auto_build"]._action.trigger()
        self.assertFalse(self.graph.get_property("auto_build"))
        self.assertFalse(self.graph._options_overlay._auto_build_button.isChecked())

    def test_rebuild(self):
        """Test that the graph is rebuilt when the button is pressed."""
        self.mock_editor.rebuild_graph.assert_not_called()
        self.graph._options_overlay._rebuild_button.click()
        self.mock_editor.rebuild_graph.assert_called_once_with(force=True)


if __name__ == "__main__":
    unittest.main()
