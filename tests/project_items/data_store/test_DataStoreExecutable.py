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
Unit tests for DataStoreExecutable.

:author: A. Soininen
:date:   6.4.2020
"""
import unittest
from unittest import mock
from spine_engine import ExecutionDirection
from spinetoolbox.project_items.data_store.data_store_executable import DataStoreExecutable


class TestDataStoreExecutable(unittest.TestCase):
    def test_item_type(self):
        self.assertEqual(DataStoreExecutable.item_type(), "Data Store")

    def test_execute_backward(self):
        executable = DataStoreExecutable("name", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    def test_execute_forward(self):
        executable = DataStoreExecutable("name", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    def test_output_resources_backward(self):
        executable = DataStoreExecutable("name", "sqlite:///database.sqlite", mock.MagicMock())
        resources = executable.output_resources(ExecutionDirection.BACKWARD)
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource.type_, "database")
        self.assertEqual(resource.url, "sqlite:///database.sqlite")
        self.assertEqual(resource.metadata, {})

    def test_output_resources_forward(self):
        executable = DataStoreExecutable("name", "sqlite:///database.sqlite", mock.MagicMock())
        resources = executable.output_resources(ExecutionDirection.FORWARD)
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource.type_, "database")
        self.assertEqual(resource.url, "sqlite:///database.sqlite")
        self.assertEqual(resource.metadata, {})


if __name__ == '__main__':
    unittest.main()
