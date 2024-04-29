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

"""Unit tests for AddProjectItemWidget."""
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QColor
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory
from spinetoolbox.widgets.add_project_item_widget import AddProjectItemWidget
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox


class TestAddProjectItemWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self._temp_dir = TemporaryDirectory()
        with patch("spinetoolbox.ui_main.JumpPropertiesWidget") as mock_jump_props_widget, patch(
            "spinetoolbox.ui_main.load_project_items"
        ) as mock_load_project_items:
            mock_jump_props_widget.return_value = QWidget()
            mock_load_project_items.return_value = {TestProjectItem.item_type(): TestItemFactory}
            self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_name_field_initially_selected(self):
        widget = AddProjectItemWidget(self._toolbox, 0.0, 0.0, class_=TestProjectItem)
        self.assertEqual(widget.ui.lineEdit_name.selectedText(), "TestItemType")

    def test_find_item_is_used_to_create_prefix(self):
        widget = AddProjectItemWidget(self._toolbox, 0.0, 0.0, class_=TestProjectItem)
        self.assertEqual(widget.ui.lineEdit_name.text(), "TestItemType")


class TestAddProjectItemWidgetWithSpecifications(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self._temp_dir = TemporaryDirectory()
        with patch("spinetoolbox.ui_main.JumpPropertiesWidget") as mock_jump_props_widget, patch(
            "spinetoolbox.ui_main.load_project_items"
        ) as mock_load_project_items, patch(
            "spinetoolbox.ui_main.load_item_specification_factories"
        ) as mock_load_specification_factories:
            mock_jump_props_widget.return_value = QWidget()
            mock_load_project_items.return_value = {TestProjectItem.item_type(): TestItemFactory}
            mock_load_specification_factories.return_value = {TestProjectItem.item_type(): TestSpecificationFactory}
            self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_specifications_combo_box_enabled_if_item_supports_specifications(self):
        widget = AddProjectItemWidget(self._toolbox, 0.0, 0.0, class_=TestProjectItem)
        self.assertTrue(widget.ui.comboBox_specification.isEnabled())


class TestProjectItem(ProjectItem):
    def __init__(self, project):
        super().__init__("item name", "item description", 0.0, 0.0, project)

    @staticmethod
    def item_type():
        return "TestItemType"

    @property
    def executable_class(self):
        raise NotImplementedError()

    @staticmethod
    def from_dict(name, item_dict, toolbox, project):
        return TestProjectItem(project)

    def update_name_label(self):
        return


class TestItemFactory(ProjectItemFactory):
    @staticmethod
    def item_class():
        return TestProjectItem

    @staticmethod
    def icon():
        return ""

    @staticmethod
    def icon_color():
        return QColor()

    @staticmethod
    def make_add_item_widget(toolbox, x, y, specification):
        return MagicMock()

    @staticmethod
    def make_icon(toolbox):
        return MagicMock()

    @staticmethod
    def make_item(name, item_dict, toolbox, project):
        return TestProjectItem(project)

    @staticmethod
    def make_properties_widget(toolbox):
        """
        Creates the item's properties tab widget.

        Returns:
            QWidget: item's properties tab widget
        """
        return MagicMock()

    @staticmethod
    def make_specification_menu(parent, index):
        return MagicMock()

    @staticmethod
    def show_specification_widget(toolbox, specification=None, **kwargs):
        return MagicMock()


class TestSpecificationFactory:
    pass


if __name__ == "__main__":
    unittest.main()
