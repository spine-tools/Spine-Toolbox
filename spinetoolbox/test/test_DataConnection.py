######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for Data Connection project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

from tempfile import TemporaryDirectory
import unittest

from PySide2.QtWidgets import QApplication

from ..project_items.data_connection.data_connection import DataConnection


class _MockProject:
    def __init__(self, temp_directory):
        self.project_dir = temp_directory


class _MockToolbox:
    class Message:
        def __init__(self):
            self.text = None

        def emit(self, text):
            self.text = text

    def __init__(self, project):
        self._project = project
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()

    def project(self):
        return self._project

    def reset_messages(self):
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()


class _MockItem:
    def __init__(self, item_type, name):
        self.item_type = item_type
        self.name = name


class TestDataConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            item = DataConnection(_MockToolbox(project), "name", "description", 0.0, 0.0)
            self.assertEqual(item.item_type, "Data Connection")
            item.data_dir_watcher.removePath(item.data_dir)

    def test_notify_destination(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            toolbox = _MockToolbox(project)
            item = DataConnection(toolbox, "name", "description", 0.0, 0.0)
            source_item = _MockItem("Data Interface", "source name")
            item.notify_destination(source_item)
            self.assertEqual(toolbox.msg.text, "Link established.")
            toolbox.reset_messages()
            source_item.item_type = "Data Store"
            item.notify_destination(source_item)
            self.assertEqual(toolbox.msg.text, "Link established.")
            toolbox.reset_messages()
            source_item.item_type = "Gdx Export"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>Gdx Export</b> and a <b>Data Connection</b> has not been implemented yet.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Tool"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Tool <b>source name</b> output files will be "
                "passed as references to item <b>name</b> after execution.",
            )
            toolbox.reset_messages()
            source_item.item_type = "View"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>View</b> and a <b>Data Connection</b> has not been implemented yet.",
            )
            item.data_dir_watcher.removePath(item.data_dir)

    def test_default_name_prefix(self):
        self.assertEqual(DataConnection.default_name_prefix(), "Data Connection")


if __name__ == '__main__':
    unittest.main()
