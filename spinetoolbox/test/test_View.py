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
Unit tests for View project item.

:author: A. Soininen (VTT)
:date:   4.10.2019
"""

from tempfile import TemporaryDirectory
import unittest

from PySide2.QtWidgets import QApplication

from ..project_items.view.view import View


class _MockProject:
    def __init__(self, temp_directory):
        self.project_dir = temp_directory


class _MockToolbox:
    def __init__(self, project):
        self._project = project

    def project(self):
        return self._project


class TestView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_item_type(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            item = View(_MockToolbox(project), "name", "description", 0.0, 0.0)
            self.assertEqual(item.item_type, "View")


if __name__ == '__main__':
    unittest.main()
