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

"""Unit tests for edit_or_remove_items_dialogs module."""
import unittest
from unittest import mock
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.widgets.edit_or_remove_items_dialogs import EditEntityClassesDialog
from tests.spine_db_editor.helpers import TestBase


class TestEditEntityClassesDialog(TestBase):
    def test_pasting_gibberish_to_active_by_default_column_gives_false(self):
        self._db_map.add_entity_class_item(name="Object")
        entity_tree = self._db_editor.ui.treeView_entity
        entity_model = entity_tree.model()
        entity_model.root_item.fetch_more()
        while not entity_model.root_item.children:
            QApplication.processEvents()
        self.assertEqual(len(entity_model.root_item.children), 1)
        dialog = EditEntityClassesDialog(self._db_editor, self._db_mngr, entity_model.root_item.children)
        model = dialog.model
        self._assert_table_contents(model, [["Object", None, None, False, "TestEditEntityClassesDialog_db"]])
        dialog.table_view.selectionModel().setCurrentIndex(
            model.index(0, 3), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "true"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(dialog.table_view.paste())
        self._assert_table_contents(model, [["Object", None, None, True, "TestEditEntityClassesDialog_db"]])
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "GIBBERISH"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(dialog.table_view.paste())
        self._assert_table_contents(model, [["Object", None, None, False, "TestEditEntityClassesDialog_db"]])

    def test_pasting_gibberish_to_display_icon_column_gives_none(self):
        self._db_map.add_entity_class_item(name="Object")
        entity_tree = self._db_editor.ui.treeView_entity
        entity_model = entity_tree.model()
        entity_model.root_item.fetch_more()
        while not entity_model.root_item.children:
            QApplication.processEvents()
        self.assertEqual(len(entity_model.root_item.children), 1)
        dialog = EditEntityClassesDialog(self._db_editor, self._db_mngr, entity_model.root_item.children)
        model = dialog.model
        self._assert_table_contents(model, [["Object", None, None, False, "TestEditEntityClassesDialog_db"]])
        dialog.table_view.selectionModel().setCurrentIndex(
            model.index(0, 2), QItemSelectionModel.SelectionFlag.ClearAndSelect
        )
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "23"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(dialog.table_view.paste())
        self._assert_table_contents(model, [["Object", None, 23, False, "TestEditEntityClassesDialog_db"]])
        mock_clipboard = mock.MagicMock()
        mock_clipboard.text.return_value = "GIBBERISH"
        with mock.patch("spinetoolbox.widgets.custom_qtableview.QApplication.clipboard") as clipboard:
            clipboard.return_value = mock_clipboard
            self.assertTrue(dialog.table_view.paste())
        self._assert_table_contents(model, [["Object", None, None, False, "TestEditEntityClassesDialog_db"]])

    def _assert_table_contents(self, model, expected):
        data_table = []
        for row in range(model.rowCount()):
            row_data = []
            for column in range(model.columnCount()):
                row_data.append(model.index(row, column).data())
            data_table.append(row_data)
        self.assertEqual(data_table, expected)


if __name__ == "__main__":
    unittest.main()
