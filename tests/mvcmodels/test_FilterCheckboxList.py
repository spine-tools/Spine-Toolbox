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

"""Unit tests for FilterCheckboxListModel class."""
import unittest
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinetoolbox.mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel


class TestFilterCheckboxListModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.model = SimpleFilterCheckboxListModel(None)
        self.data = ["a", "aa", "aaa", "b", "bb", "bbb"]

    def test_set_list(self):
        self.model.set_list(self.data)
        self.assertEqual(self.model._data, sorted(self.data))
        self.assertEqual(self.model._data_set, set(self.data))
        self.assertEqual(self.model._selected, set(self.data))
        self.assertTrue(self.model._all_selected)

    def test_is_all_selected_when_all_selected(self):
        self.model.set_list(self.data)
        self.assertTrue(self.model._check_all_selected())

    def test_is_all_selected_when_not_all_selected(self):
        self.model.set_list(self.data)
        self.model._selected.discard("a")
        self.assertFalse(self.model._check_all_selected())

    def test_is_all_selected_when_not_empty_selected(self):
        self.model.set_list(self.data)
        self.model._empty_selected = False
        self.assertFalse(self.model._check_all_selected())

    def test_add_item_with_select_without_filter(self):
        new_item = ["aaaa"]
        self.model.set_list(self.data)
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"
        ):
            self.model.add_items(new_item)
        self.assertEqual(self.model._data, self.data + new_item)
        self.assertEqual(self.model._data_set, set(self.data + new_item))

    def test_add_item_without_select_without_filter(self):
        new_item = ["aaaa"]
        self.model.set_list(self.data)
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"
        ):
            self.model.add_items(new_item, selected=False)
        self.assertFalse(self.model._all_selected)

    def test_click_select_all_when_all_selected(self):
        self.model.set_list(self.data)
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(0, 0)
            self.model._handle_index_clicked(index)
        self.assertFalse(self.model._all_selected)
        self.assertEqual(self.model._selected, set())

    def test_click_selected_item(self):
        self.model.set_list(self.data)
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(2, 0)
            self.model._handle_index_clicked(index)
        self.assertEqual(self.model._selected, set(self.data).difference({"a"}))
        self.assertFalse(self.model._all_selected)

    def test_click_unselected_item(self):
        self.model.set_list(self.data)
        self.model._selected.discard("a")
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(2, 0)
            self.model._handle_index_clicked(index)
        self.assertEqual(self.model._selected, set(self.data))
        self.assertTrue(self.model._all_selected)

    def test_click_select_empty_when_selected(self):
        self.model.set_list(self.data)
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(1, 0)
            self.model._handle_index_clicked(index)
        self.assertFalse(self.model._empty_selected)
        self.assertFalse(self.model._all_selected)

    def test_click_select_empty_when_unselected(self):
        self.model.set_list(self.data)
        self.model._empty_selected = False
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(1, 0)
            self.model._handle_index_clicked(index)
        self.assertTrue(self.model._empty_selected)
        self.assertTrue(self.model._all_selected)

    def test_click_select_all_when_not_all_selected(self):
        self.model.set_list(self.data)
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(2, 0)
            self.model._handle_index_clicked(index)
            index = self.model.index(0, 0)
            self.model._handle_index_clicked(index)
        self.assertTrue(self.model._all_selected)
        self.assertEqual(self.model._selected, set(self.data))

    def test_set_filter_index(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.assertEqual(self.model._filter_index, [3, 4, 5])

    def test_rowCount_when_filter(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.assertEqual(self.model.rowCount(), 3 + len(self.model._action_rows))

    def test_add_to_selection_when_filter(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.assertFalse(self.model._add_to_selection)
        self.assertEqual(
            self.model.data(self.model.index(len(self.model._action_rows) - 1, 0), Qt.ItemDataRole.CheckStateRole),
            Qt.CheckState.Unchecked,
        )

    def test_selected_when_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.assertEqual(self.model._selected, set(self.data))
        self.assertEqual(self.model._selected_filtered, set(self.data[3:]))

    def test_get_data_when_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.assertEqual(self.model.data(self.model.index(len(self.model._action_rows), 0)), "b")

    def test_data_works_when_show_empty_is_unset(self):
        self.model = SimpleFilterCheckboxListModel(None, show_empty=False)
        self.model.set_list(self.data)
        self.assertEqual(self.model.rowCount(), len(self.data) + 1)
        self.assertEqual(self.model.data(self.model.index(0, 0)), "(Select all)")
        self.assertEqual(self.model.data(self.model.index(0, 0), Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked)
        for index, expected in enumerate(self.data):
            model_index = self.model.index(index + 1, 0)
            self.assertEqual(self.model.data(model_index), expected)
            self.assertEqual(self.model.data(model_index, Qt.ItemDataRole.CheckStateRole), Qt.CheckState.Checked)

    def test_click_select_all_when_all_selected_and_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(0, 0)
            self.model._handle_index_clicked(index)
        self.assertFalse(self.model._all_selected)
        self.assertEqual(self.model._selected, set(self.data))
        self.assertEqual(self.model._selected_filtered, set())

    def test_click_select_all_when_all_not_selected_and_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(2, 0)
            self.model._handle_index_clicked(index)
            index = self.model.index(0, 0)
            self.model._handle_index_clicked(index)
        self.assertTrue(self.model._all_selected)
        self.assertEqual(self.model._selected, set(self.data))
        self.assertEqual(self.model._selected_filtered, set(self.data[3:]))

    def test_click_selected_item_when_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(len(self.model._action_rows), 0)
            self.model._handle_index_clicked(index)
        self.assertEqual(self.model._selected_filtered, set(self.data[4:]))
        self.assertFalse(self.model._all_selected)

    def test_click_unselected_item_when_filtered(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.model._selected_filtered.discard("b")
        with mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"):
            index = self.model.index(len(self.model._action_rows), 0)
            self.model._handle_index_clicked(index)
        self.assertEqual(self.model._selected_filtered, set(self.data[3:]))
        self.assertTrue(self.model._all_selected)

    def test_remove_filter(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.model.remove_filter()
        self.assertFalse(self.model._is_filtered)
        self.assertEqual(self.model._selected, set(self.data))
        self.assertEqual(self.model.rowCount(), 8)

    def test_apply_filter_with_replace(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.model.apply_filter()
        self.assertFalse(self.model._is_filtered)
        self.assertEqual(self.model._selected, set(self.data[3:]))
        self.assertEqual(self.model.rowCount(), 8)
        self.assertFalse(self.model._empty_selected)

    def test_apply_filter_with_add(self):
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.model._add_to_selection = True
        self.model._selected_filtered.discard("bbb")
        self.model.apply_filter()
        self.assertFalse(self.model._is_filtered)
        self.assertEqual(self.model._selected, set(self.data[:5]))
        self.assertEqual(self.model.rowCount(), 8)
        self.assertFalse(self.model._all_selected)

    def test_add_item_with_select_with_filter_last(self):
        new_item = ["bbbb"]
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"
        ):
            self.model.add_items(new_item)
        self.assertEqual(self.model._data, sorted(self.data + new_item))
        self.assertEqual(self.model._data_set, set(self.data + new_item))
        self.assertEqual(self.model._filter_index, [3, 4, 5, 6])
        self.assertEqual(self.model._selected_filtered, set(self.data[3:] + new_item))
        self.assertEqual(self.model.data(self.model.index(3 + len(self.model._action_rows), 0)), new_item[0])

    def test_add_item_with_select_with_filter_first(self):
        new_item = ["0b"]
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"
        ):
            self.model.add_items(new_item)
        self.assertEqual(self.model._filter_index, [3, 4, 5, 6])
        self.assertEqual(self.model.data(self.model.index(3 + len(self.model._action_rows), 0)), new_item[0])

    def test_add_item_with_select_with_filter_middle(self):
        new_item = ["b1"]
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endInsertRows"
        ), mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.dataChanged"
        ):
            self.model.add_items(new_item)
        self.assertEqual(self.model._filter_index, [3, 4, 5, 6])
        self.assertEqual(self.model.data(self.model.index(3 + len(self.model._action_rows), 0)), new_item[0])

    def test_remove_items_data(self):
        items = set("a")
        self.model.set_list(self.data)
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._data, self.data[1:])
        self.assertEqual(self.model._data_set, set(self.data[1:]))

    def test_remove_items_selected(self):
        items = set("a")
        self.model.set_list(self.data)
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._selected, set(self.data[1:]))
        self.assertTrue(self.model._all_selected)

    def test_remove_items_not_selected(self):
        items = set("a")
        self.model.set_list(self.data)
        self.model._selected.discard("a")
        self.model._all_selected = False
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._selected, set(self.data[1:]))
        self.assertTrue(self.model._all_selected)

    def test_remove_items_filtered_data(self):
        items = set("b")
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._filter_index, [3, 4])
        self.assertEqual(self.model._selected_filtered, set(self.data[4:]))

    def test_remove_items_filtered_data_middle(self):
        items = set("bb")
        self.model.set_list(self.data)
        self.model.set_filter("b")
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._filter_index, [3, 4])

    def test_remove_items_filtered_data_not_selected(self):
        items = set("b")
        self.model.set_list(self.data)
        self.model.set_filter("b")
        self.model._selected_filtered.discard("a")
        self.model._all_selected = False
        with mock.patch(
            "spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.beginResetModel"
        ), mock.patch("spinetoolbox.mvcmodels.filter_checkbox_list_model.SimpleFilterCheckboxListModel.endResetModel"):
            self.model.remove_items(items)
        self.assertEqual(self.model._selected_filtered, set(self.data[4:]))
        self.assertTrue(self.model._all_selected)

    def test_half_finished_expression_does_not_raise_exception(self):
        self.model.set_list(self.data)
        self.model.set_filter("[")
        self.assertEqual(
            [self.model.index(row, 0).data() for row in range(self.model.rowCount())],
            ["(Select all)", "(Empty)"] + self.data,
        )

    def test_only_whitespaces_in_filter_expression_does_not_filter(self):
        self.model.set_list(self.data)
        self.model.set_filter("   ")
        self.assertEqual(
            [self.model.index(row, 0).data() for row in range(self.model.rowCount())],
            ["(Select all)", "(Empty)"] + self.data,
        )


if __name__ == "__main__":
    unittest.main()
