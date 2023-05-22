######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for :class:`SpecificationEditorWindowBase` and its supports.
"""
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import call, MagicMock, patch, PropertyMock
from PySide6.QtGui import QColor, QUndoStack
from PySide6.QtWidgets import QApplication
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from spinetoolbox.project_item.project_item import ProjectItem
from spinetoolbox.project_item.project_item_factory import ProjectItemFactory
from spinetoolbox.project_item_icon import ProjectItemIcon
from spinetoolbox.project_item.specification_editor_window import (
    ChangeSpecPropertyCommand,
    SpecificationEditorWindowBase,
)
from tests.mock_helpers import clean_up_toolbox, create_toolboxui_with_project


class TestChangeSpecPropertyCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_init(self):
        undo_stack = QUndoStack()
        callback = MagicMock()
        command = ChangeSpecPropertyCommand(callback, "new", "old", "test command")
        undo_stack.push(command)
        self.assertEqual(command.text(), "test command")
        callback.assert_called_once_with("new")
        undo_stack.deleteLater()

    def test_undo(self):
        undo_stack = QUndoStack()
        callback = MagicMock()
        command = ChangeSpecPropertyCommand(callback, "new", "old", "test command")
        undo_stack.push(command)
        undo_stack.undo()
        callback.assert_has_calls((call("new"), call("old")))
        undo_stack.deleteLater()


class TestSpecificationEditorWindowBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)

    def tearDown(self):
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def test_init(self):
        with patch.object(SpecificationEditorWindowBase, "_make_ui") as mock_make_ui, patch.object(
            SpecificationEditorWindowBase, "settings_group", new_callable=PropertyMock
        ) as mock_settings_group:
            mock_settings_group.return_value = "settings group"
            window = SpecificationEditorWindowBase(self._toolbox)
            mock_make_ui.assert_called_once()
            self.assertEqual(window.windowTitle(), "")
            self.assertIsNone(window.specification)
            self.assertIsNone(window.item)
            window.deleteLater()

    def test_init_with_existing_specification(self):
        with patch.object(SpecificationEditorWindowBase, "_make_ui"), patch.object(
            SpecificationEditorWindowBase, "settings_group", new_callable=PropertyMock
        ) as mock_settings_group:
            mock_settings_group.return_value = "settings group"
            specification = ProjectItemSpecification("spec name", "spec description")
            window = SpecificationEditorWindowBase(self._toolbox, specification)
            self.assertIs(window.specification, specification)
            self.assertEqual(window.windowTitle(), "spec name")
            self.assertEqual(window._spec_toolbar.name(), "spec name")
            self.assertEqual(window._spec_toolbar.description(), "spec description")
            window.deleteLater()

    def test_save_specification(self):
        with patch.object(SpecificationEditorWindowBase, "_make_ui"), patch.object(
            SpecificationEditorWindowBase, "settings_group", new_callable=PropertyMock
        ) as mock_settings_group, patch.object(
            SpecificationEditorWindowBase, "_make_new_specification"
        ) as mock_make_specification, patch.object(
            ProjectItemSpecification, "save"
        ) as mock_save:
            mock_settings_group.return_value = "settings group"
            specification = ProjectItemSpecification("spec name", "spec description")
            mock_make_specification.return_value = specification
            mock_save.return_value = {}
            window = SpecificationEditorWindowBase(self._toolbox)
            window._spec_toolbar._line_edit_name.setText("spec name")
            window._spec_toolbar._line_edit_name.editingFinished.emit()
            window._spec_toolbar.save_action.trigger()
            mock_save.assert_called_once()
            window.deleteLater()

    def test_make_new_specification_for_item(self):
        with patch.object(SpecificationEditorWindowBase, "_make_ui"), patch.object(
            SpecificationEditorWindowBase, "settings_group", new_callable=PropertyMock
        ) as mock_settings_group, patch.object(
            SpecificationEditorWindowBase, "_make_new_specification"
        ) as mock_make_specification, patch.object(
            ProjectItemSpecification, "save"
        ) as mock_save:
            mock_settings_group.return_value = "settings group"
            specification = ProjectItemSpecification("spec name", "spec description", "Mock")
            mock_make_specification.return_value = specification
            mock_save.return_value = {}
            project_item = _MockProjectItem("item name", "item description", 0.0, 0.0, self._toolbox.project())
            project_item._toolbox = self._toolbox
            window = SpecificationEditorWindowBase(self._toolbox, item=project_item)
            self.assertIs(window.item, project_item)
            window._spec_toolbar._line_edit_name.setText("spec name")
            window._spec_toolbar._line_edit_name.editingFinished.emit()
            window._spec_toolbar.save_action.trigger()
            self.assertIs(project_item.specification(), specification)
            window.deleteLater()

    def test_rename_specification_for_item(self):
        with patch.object(SpecificationEditorWindowBase, "_make_ui"), patch.object(
            SpecificationEditorWindowBase, "settings_group", new_callable=PropertyMock
        ) as mock_settings_group, patch.object(
            SpecificationEditorWindowBase, "_make_new_specification"
        ) as mock_make_specification, patch.object(
            ProjectItemSpecification, "save"
        ) as mock_save, patch.object(
            ProjectItemFactory, "make_icon"
        ) as mock_make_icon:
            mock_settings_group.return_value = "settings group"
            mock_make_icon.return_value = ProjectItemIcon(
                self._toolbox, ":/icons/item_icons/hammer.svg", QColor("white")
            )
            self._toolbox.item_factories["Mock"] = ProjectItemFactory()
            self._toolbox._item_properties_uis["Mock"] = MagicMock()
            specification = ProjectItemSpecification("spec name", "spec description", "Mock")
            project_item = _MockProjectItem("item name", "item description", 0.0, 0.0, self._toolbox.project())
            project_item._toolbox = self._toolbox
            project_item.set_specification(specification)
            self._toolbox.project().add_item(project_item)
            window = SpecificationEditorWindowBase(self._toolbox, item=project_item)
            mock_make_specification.side_effect = lambda name, exiting: ProjectItemSpecification(
                name, window._spec_toolbar.description(), "Mock"
            )
            mock_save.return_value = {}
            window._spec_toolbar._line_edit_name.setText("new spec name")
            window._spec_toolbar._line_edit_name.editingFinished.emit()
            window._spec_toolbar.save_action.trigger()
            item_specification = project_item.specification()
            self.assertEqual(item_specification.name, "new spec name")
            window.deleteLater()


class _MockProjectItem(ProjectItem):
    _toolbox = None

    @staticmethod
    def item_type():
        return "Mock"

    @staticmethod
    def item_category():
        return "Tools"


if __name__ == "__main__":
    unittest.main()
