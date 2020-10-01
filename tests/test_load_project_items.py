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
Unit tests for the :module:`spinetoolbox.load_project_items` module.

:author: A. Soininen (VTT)
:date:   8.5.2020
"""
import unittest
from unittest.mock import MagicMock
from PySide2.QtWidgets import QApplication
from spine_items.executable_item_base import ExecutableItemBase
from spinetoolbox.load_project_items import load_executable_items, load_item_specification_factories, load_project_items
from spine_items.project_item_factory import ProjectItemFactory
from spine_items.project_item_specification_factory import ProjectItemSpecificationFactory


class TestLoadProjectItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_load_project_items_finds_all_default_items(self):
        toolbox = MagicMock()
        categories, factories = load_project_items(toolbox)
        expected_categories = {
            "Data Connection": "Data Connections",
            "Data Store": "Data Stores",
            "Importer": "Importers",
            "Exporter": "Exporters",
            "Tool": "Tools",
            "View": "Views",
            "Combiner": "Manipulators",
            "Gimlet": "Tools",
        }
        self.assertEqual(categories, expected_categories)
        self.assertEqual(len(factories), 8)
        for item_type in expected_categories:
            self.assertIn(item_type, factories)
        for factory in factories.values():
            self.assertTrue(issubclass(factory, ProjectItemFactory))

    def test_load_item_specification_factories(self):
        factories = load_item_specification_factories()
        self.assertEqual(len(factories), 1)
        self.assertIn("Tool", factories)
        self.assertTrue(issubclass(factories["Tool"], ProjectItemSpecificationFactory))

    def test_item_factories_report_specification_support_correctly(self):
        toolbox = MagicMock()
        _, item_factories = load_project_items(toolbox)
        specification_factories = load_item_specification_factories()
        for item_type, item_factory in item_factories.items():
            if item_factory.supports_specifications():
                self.assertIn(item_type, specification_factories)
            else:
                self.assertNotIn(item_type, specification_factories)

    def test_load_executable_items(self):
        item_classes = load_executable_items()
        item_types = ("Data Connection", "Data Store", "Importer", "Exporter", "Tool", "View")
        for item_type in item_types:
            self.assertIn(item_type, item_classes)
        for item_class in item_classes.values():
            self.assertTrue(issubclass(item_class, ExecutableItemBase))


if __name__ == '__main__':
    unittest.main()
