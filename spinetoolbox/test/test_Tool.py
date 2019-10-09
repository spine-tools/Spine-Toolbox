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
Unit tests for Tool project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

from tempfile import TemporaryDirectory
import unittest

from PySide2.QtCore import QSettings

from ..project_items.tool.tool import Tool
from ..project import SpineToolboxProject
from ..mvcmodels.tool_specification_model import ToolSpecificationModel


class _MockToolbox:
    class Message:
        def __init__(self):
            self.text = None

        def emit(self, text):
            self.text = text

    def __init__(self, temp_directory):
        self._qsettings = QSettings()
        self._qsettings.setValue("appSettings/projectsDir", temp_directory)
        self.tool_specification_model = ToolSpecificationModel(self)
        self._project = SpineToolboxProject(self, "name", "description", temp_directory)
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()

    def project(self):
        return self._project

    def qsettings(self):
        return self._qsettings

    def reset_messages(self):
        self.msg = _MockToolbox.Message()
        self.msg_warning = _MockToolbox.Message()


class _MockItem:
    def __init__(self, item_type, name):
        self.item_type = item_type
        self.name = name


class TestTool(unittest.TestCase):
    def test_item_type(self):
        with TemporaryDirectory() as project_dir:
            toolbox = _MockToolbox(project_dir)
            item = Tool(toolbox, "name", "description", 0.0, 0.0)
            self.assertEqual(item.item_type, "Tool")

    def test_notify_destination(self):
        with TemporaryDirectory() as project_dir:
            toolbox = _MockToolbox(project_dir)
            item = Tool(toolbox, "name", "description", 0.0, 0.0)
            source_item = _MockItem("Data Connection", "source name")
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Tool <b>name</b> will look for input "
                "files from <b>source name</b>'s references and data directory.",
            )
            toolbox.reset_messages()
            source_item = _MockItem("Data Interface", "source name")
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>Data Interface</b> and a <b>Tool</b> has not been implemented yet.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Data Store"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Data Store <b>source name</b> reference will "
                "be passed to Tool <b>name</b> when executing.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Gdx Export"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg.text,
                "Link established. Gdx Export <b>source name</b> exported file will "
                "be passed to Tool <b>name</b> when executing.",
            )
            toolbox.reset_messages()
            source_item.item_type = "Tool"
            item.notify_destination(source_item)
            self.assertEqual(toolbox.msg.text, "Link established.")
            toolbox.reset_messages()
            source_item.item_type = "View"
            item.notify_destination(source_item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established. Interaction between a "
                "<b>View</b> and a <b>Tool</b> has not been implemented yet.",
            )


if __name__ == '__main__':
    unittest.main()
