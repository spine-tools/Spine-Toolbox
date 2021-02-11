######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the :module:`spinetoolbox.load_project_items` module.

:author: A. Soininen (VTT)
:date:   8.5.2020
"""
import unittest
from PySide2.QtWidgets import QApplication
from spinetoolbox.load_project_items import load_project_items
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory


class TestLoadProjectItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_load_project_items_finds_all_default_items(self):
        categories, factories = load_project_items()
        expected_categories = {
            "Data Connection": "Data Connections",
            "Data Transformer": "Manipulators",
            "Data Store": "Data Stores",
            "Importer": "Importers",
            "GdxExporter": "Exporters",
            "Tool": "Tools",
            "View": "Views",
            "Gimlet": "Tools",
        }
        self.assertEqual(categories, expected_categories)
        self.assertEqual(len(factories), len(expected_categories))
        for item_type in expected_categories:
            self.assertIn(item_type, factories)
        for factory in factories.values():
            self.assertTrue(issubclass(factory, ProjectItemFactory))


if __name__ == '__main__':
    unittest.main()
