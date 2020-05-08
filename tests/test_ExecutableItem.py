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
Unit tests for ExecutableItem.

:author: A. Soininen (VTT)
:date:   6.4.2020
"""
import unittest
from unittest import mock
from spine_engine import ExecutionDirection
from spinetoolbox.executable_item_base import ExecutableItemBase


class TestExecutableItem(unittest.TestCase):
    def test_name(self):
        item = ExecutableItemBase("name", mock.MagicMock())
        self.assertEqual(item.name, "name")

    def test_execute_backward(self):
        resources = [3, 5, 7]
        item = ExecutableItemBase("name", mock.MagicMock())
        item.item_type = mock.MagicMock(return_value="Executable item")
        item._execute_backward = mock.MagicMock(return_value="return value")
        item._execute_forward = mock.MagicMock()
        self.assertEqual(item.execute(resources, ExecutionDirection.BACKWARD), "return value")
        item._execute_backward.assert_called_once_with(resources)
        item._execute_forward.assert_not_called()

    def test_execute_forward(self):
        resources = [3, 5, 7]
        item = ExecutableItemBase("name", mock.MagicMock())
        item.item_type = mock.MagicMock(return_value="Executable item")
        item._execute_backward = mock.MagicMock()
        item._execute_forward = mock.MagicMock(return_value="return value")
        self.assertEqual(item.execute(resources, ExecutionDirection.FORWARD), "return value")
        item._execute_backward.assert_not_called()
        item._execute_forward.assert_called_once_with(resources)

    def test_output_resources_backward(self):
        item = ExecutableItemBase("name", mock.MagicMock())
        item._output_resources_backward = mock.MagicMock(return_value=[3, 5, 7])
        item._output_resources_forward = mock.MagicMock()
        self.assertEqual(item.output_resources(ExecutionDirection.BACKWARD), [3, 5, 7])
        item._output_resources_backward.assert_called_once_with()
        item._output_resources_forward.assert_not_called()

    def test_output_resources_forward(self):
        item = ExecutableItemBase("name", mock.MagicMock())
        item._output_resources_backward = mock.MagicMock()
        item._output_resources_forward = mock.MagicMock(return_value=[3, 5, 7])
        self.assertEqual(item.output_resources(ExecutionDirection.FORWARD), [3, 5, 7])
        item._output_resources_backward.assert_not_called()
        item._output_resources_forward.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
