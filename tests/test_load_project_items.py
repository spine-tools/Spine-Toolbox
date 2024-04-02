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

"""Unit tests for the :module:`spinetoolbox.load_project_items` module."""
import unittest
from PySide6.QtWidgets import QApplication
from spinetoolbox.load_project_items import load_project_items
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory


class TestLoadProjectItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_load_project_items_finds_all_default_items(self):
        factories = load_project_items("spine_items")
        for factory in factories.values():
            self.assertTrue(issubclass(factory, ProjectItemFactory))


if __name__ == "__main__":
    unittest.main()
