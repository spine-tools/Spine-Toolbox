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
Unit tests for ProjectItemModel class.

:author: A. Soininen (VTT)
:date:   14.10.2019
"""

from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from spinetoolbox.mvcmodels.project_item_model import ProjectItemModel
from spinetoolbox.project_item import CategoryProjectItem, ProjectItem, RootProjectItem


class _MockProject:
    def __init__(self, temp_directory):
        self.project_dir = temp_directory
        self.items_dir = temp_directory


class _MockToolbox:
    def __init__(self, project):
        self._project = project

    def project(self):
        return self._project


class TestProjectItemModel(unittest.TestCase):
    def test_category_of_item(self):
        with TemporaryDirectory() as project_dir:
            project = _MockProject(project_dir)
            toolbox = _MockToolbox(project)
            root = RootProjectItem()
            category = CategoryProjectItem("category", "category description", None, MagicMock(), None, None)
            root.add_child(category)
            model = ProjectItemModel(toolbox, root)
            self.assertEqual(model.category_of_item("nonexistent item"), None)
            item = ProjectItem(toolbox, "item", "item description", 0.0, 0.0)
            category.add_child(item)
            found_category = model.category_of_item("item")
            self.assertEqual(found_category.name, category.name)


if __name__ == '__main__':
    unittest.main()
