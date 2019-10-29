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
Unit tests for ProjectItem base class.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

from tempfile import TemporaryDirectory
import unittest

from spinetoolbox.project_item import ProjectItem


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
        self.msg_warning = _MockToolbox.Message()

    def project(self):
        return self._project


class TestProjectItem(unittest.TestCase):
    def test_notify_destination(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            toolbox = _MockToolbox(project)
            item = ProjectItem(toolbox, "item_type", "name", "description", 0.0, 0.0)
            item.notify_destination(item)
            self.assertEqual(
                toolbox.msg_warning.text,
                "Link established."
                " Interaction between a <b>item_type</b> and a <b>item_type</b> has not been implemented yet.",
            )


if __name__ == '__main__':
    unittest.main()
