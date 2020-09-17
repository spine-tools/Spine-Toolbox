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
import tempfile
import unittest
from unittest import mock
from spine_engine import ExecutionDirection
from spinetoolbox.project_items.data_store.executable_item import ExecutableItem


class TestDataStoreExecutable(unittest.TestCase):
    def test_item_type(self):
        self.assertEqual(ExecutableItem.item_type(), "Data Store")

    def test_from_dict(self):
        name = "Output Data Store"
        item_dict = {
            "type": "Data Store", "description": "", "x": 0, "y": 0,
            "url": {
                "dialect": "sqlite",
                "username": "",
                "password": "",
                "host": "",
                "port": "",
                "database": {
                    "type": "path",
                    "relative": True,
                    "path": ".spinetoolbox/items/output_data_store/Data Store 2.sqlite"
                }
            }
        }
        logger = mock.MagicMock()
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch("spinetoolbox.project_items.data_store.executable_item.convert_to_sqlalchemy_url") as mock_convert_url:
                mock_convert_url.return_value = "database.sqlite"
                item = ExecutableItem.from_dict(item_dict, name, temp_dir, None, dict(), logger)
                mock_convert_url.assert_called_once()
                self.assertIsInstance(item, ExecutableItem)
                self.assertEqual("Data Store", item.item_type())
                self.assertEqual("database.sqlite", item._url)

    def test_stop_execution(self):
        executable = ExecutableItem("name", "", mock.MagicMock())
        with mock.patch("spinetoolbox.executable_item_base.ExecutableItemBase.stop_execution") as mock_stop_execution:
            executable.stop_execution()
            mock_stop_execution.assert_called_once()

    def test_execute_backward(self):
        executable = ExecutableItem("name", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.BACKWARD))

    def test_execute_forward(self):
        executable = ExecutableItem("name", "", mock.MagicMock())
        self.assertTrue(executable.execute([], ExecutionDirection.FORWARD))

    def test_output_resources_backward(self):
        executable = ExecutableItem("name", "sqlite:///database.sqlite", mock.MagicMock())
        resources = executable.output_resources(ExecutionDirection.BACKWARD)
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource.type_, "database")
        self.assertEqual(resource.url, "sqlite:///database.sqlite")
        self.assertEqual(resource.metadata, {})

    def test_output_resources_forward(self):
        executable = ExecutableItem("name", "sqlite:///database.sqlite", mock.MagicMock())
        resources = executable.output_resources(ExecutionDirection.FORWARD)
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource.type_, "database")
        self.assertEqual(resource.url, "sqlite:///database.sqlite")
        self.assertEqual(resource.metadata, {})


if __name__ == '__main__':
    unittest.main()
