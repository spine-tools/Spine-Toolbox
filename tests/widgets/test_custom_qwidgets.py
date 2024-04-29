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

"""Unit tests for the models in ``custom_qwidgets`` module."""
import unittest
from contextlib import contextmanager
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialogButtonBox
from spinetoolbox.widgets.custom_qwidgets import FilterWidget, SelectDatabaseItemsDialog
from spinetoolbox.mvcmodels.filter_checkbox_list_model import DataToValueFilterCheckboxListModel


class TestFilterWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._widget = FilterWidget(None, DataToValueFilterCheckboxListModel, None, str)
        self._widget.set_filter_list(["ei", "bii", "cii"])

    def tearDown(self):
        self._widget.close()
        self._widget.deleteLater()

    def test_set_filter_list(self):
        self.assertFalse(self._widget.has_filter())
        model = self._widget._ui_list.model()
        data = [model.index(row, 0).data() for row in range(model.rowCount())]
        self.assertEqual(data, ["(Select all)", "(Empty)", "ei", "bii", "cii"])
        checked = [model.index(row, 0).data(Qt.ItemDataRole.CheckStateRole).value for row in range(model.rowCount())]
        self.assertEqual(checked, 5 * [Qt.CheckState.Checked.value])
        self.assertEqual(self._widget._filter_state, ["ei", "bii", "cii"])
        self.assertIsNone(self._widget._filter_empty_state)

    def test_click_Empty_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(1, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.ItemDataRole.CheckStateRole).value for row in range(model.rowCount())]
        self.assertEqual(
            checked,
            [
                Qt.CheckState.Unchecked.value,
                Qt.CheckState.Unchecked.value,
                Qt.CheckState.Checked.value,
                Qt.CheckState.Checked.value,
                Qt.CheckState.Checked.value,
            ],
        )
        self.assertTrue(self._widget.has_filter())

    def test_click_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(2, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.ItemDataRole.CheckStateRole).value for row in range(model.rowCount())]
        self.assertEqual(
            checked,
            [
                Qt.CheckState.Unchecked.value,
                Qt.CheckState.Checked.value,
                Qt.CheckState.Unchecked.value,
                Qt.CheckState.Checked.value,
                Qt.CheckState.Checked.value,
            ],
        )
        self.assertTrue(self._widget.has_filter())

    def test_click_Select_All_item(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(0, 0))
        model = self._widget._ui_list.model()
        checked = [model.index(row, 0).data(Qt.ItemDataRole.CheckStateRole).value for row in range(model.rowCount())]
        self.assertEqual(checked, 5 * [Qt.CheckState.Unchecked.value])
        self.assertTrue(self._widget.has_filter())

    def test_save_state(self):
        model = self._widget._ui_list.model()
        self._widget._ui_list.clicked.emit(model.index(2, 0))
        self._widget.save_state()
        self.assertEqual(self._widget._filter_state, {"bii", "cii"})
        self.assertTrue(self._widget._filter_empty_state)


class TestSelectDatabaseItemsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_ok_button_text(self):
        text = "Do it!"
        with _select_database_items_dialog(None, text) as dialog:
            self.assertEqual(dialog._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).text(), text)

    def test_warning_label(self):
        with _select_database_items_dialog(None, None) as dialog:
            self.assertEqual(dialog._ui.warning_label.text(), "")
            dialog._item_check_boxes_widget._item_check_boxes["metadata"].setChecked(True)
            self.assertEqual(dialog._ui.warning_label.text(), "Warning! Structural data items selected.")


@contextmanager
def _select_database_items_dialog(checked_states, ok_button_text):
    dialog = SelectDatabaseItemsDialog(checked_states, ok_button_text)
    try:
        yield dialog
    finally:
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
