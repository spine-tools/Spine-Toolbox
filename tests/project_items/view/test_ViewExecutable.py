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
Unit tests for ViewExecutable.

:author: A. Soininen (VTT)
:date:   6.4.2020
"""
import unittest
from unittest import mock
from spine_engine import ExecutionDirection
from spinetoolbox.project_items.view.executable_item import ExecutableItem


class TestViewExecutable(unittest.TestCase):
    def test_item_type(self):
        self.assertEqual(ExecutableItem.item_type(), "View")

    def test_from_dict(self):
        logger = mock.MagicMock()
        item_dict = {"type": "View", "description": "", "x": 0, "y": 0}
        item = ExecutableItem.from_dict(item_dict, "Viewer", "", None, dict(), logger)
        self.assertIsInstance(item, ExecutableItem)
        self.assertEqual("View", item.item_type())

    def test_stop_execution(self):
        executable = ExecutableItem(name="Viewer", logger=mock.MagicMock())
        with mock.patch("spinetoolbox.executable_item_base.ExecutableItemBase.stop_execution") as mock_stop_execution:
            executable.stop_execution()
            mock_stop_execution.assert_called_once()

    def test_execute_backward(self):
        executable = ExecutableItem("name", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    def test_execute_forward(self):
        executable = ExecutableItem("name", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    def test_output_resources_backward(self):
        executable = ExecutableItem("name", mock.MagicMock())
        self.assertEqual(executable.output_resources(ExecutionDirection.BACKWARD), [])

    def test_output_resources_forward(self):
        executable = ExecutableItem("name", mock.MagicMock())
        self.assertEqual(executable.output_resources(ExecutionDirection.FORWARD), [])


if __name__ == '__main__':
    unittest.main()
