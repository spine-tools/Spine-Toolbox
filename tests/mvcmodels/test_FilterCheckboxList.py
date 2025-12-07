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
from PySide6.QtCore import Qt
import pytest
from spinetoolbox.mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from tests.mock_helpers import assert_list_model_data_pytest


@pytest.fixture()
def data():
    yield ["a", "aa", "aaa", "b", "bb", "bbb"]


@pytest.fixture()
def model(parent_object):
    yield SimpleFilterCheckboxListModel(parent_object, show_empty=True)


@pytest.fixture()
def model_without_empty(parent_object):
    yield SimpleFilterCheckboxListModel(parent_object, show_empty=False)


class TestFilterCheckboxListModel:
    def test_set_list(self, model, data):
        model.set_list(data)
        assert model._data == sorted(data)
        assert model.data_set == set(data)
        assert model._selected == set(data)
        assert model.all_selected
        assert model.empty_selected
        expected = ["(Select all)", "(Empty)"] + data
        assert_list_model_data_pytest(model, expected)
        expected = len(expected) * [Qt.CheckState.Checked]
        assert_list_model_data_pytest(model, expected, Qt.ItemDataRole.CheckStateRole)

    def test_set_list_without_empty_option(self, model_without_empty, data):
        model_without_empty.set_list(data)
        assert model_without_empty._data == sorted(data)
        assert model_without_empty.data_set == set(data)
        assert model_without_empty._selected == set(data)
        assert model_without_empty.all_selected
        assert model_without_empty.empty_selected
        expected = ["(Select all)"] + data
        assert_list_model_data_pytest(model_without_empty, expected)
        expected = len(expected) * [Qt.CheckState.Checked]
        assert_list_model_data_pytest(model_without_empty, expected, Qt.ItemDataRole.CheckStateRole)

    def test_is_all_selected_when_all_selected(self, model, data):
        model.set_list(data)
        assert model._check_all_selected()

    def test_is_all_selected_when_not_all_selected(self, model, data):
        model.set_list(data)
        model._selected.discard("a")
        assert not model._check_all_selected()

    def test_is_all_selected_when_not_empty_selected(self, model, data):
        model.set_list(data)
        model.empty_selected = False
        assert not model._check_all_selected()

    def test_add_item_with_select_without_filter(self, model, data):
        new_item = ["aaaa"]
        model.set_list(data)
        model.add_items(new_item)
        assert model._data == data + new_item
        assert model.data_set == set(data + new_item)

    def test_add_item_without_select_without_filter(self, model, data):
        new_item = ["aaaa"]
        model.set_list(data)
        model.add_items(new_item, selected=set())
        assert not model.all_selected

    def test_click_select_all_when_all_selected(self, model, data):
        model.set_list(data)
        index = model.index(0, 0)
        model.handle_index_clicked(index)
        assert not model.all_selected
        assert model._selected == set()

    def test_click_selected_item(self, model, data):
        model.set_list(data)
        index = model.index(2, 0)
        model.handle_index_clicked(index)
        assert model._selected == set(data).difference({"a"})
        assert not model.all_selected

    def test_click_unselected_item(self, model, data):
        model.set_list(data)
        model._selected.discard("a")
        index = model.index(2, 0)
        model.handle_index_clicked(index)
        assert model._selected == set(data)
        assert model.all_selected

    def test_click_select_empty_when_selected(self, model, data):
        model.set_list(data)
        index = model.index(1, 0)
        model.handle_index_clicked(index)
        assert not model.empty_selected
        assert not model.all_selected

    def test_click_select_empty_when_unselected(self, model, data):
        model.set_list(data)
        model.empty_selected = False
        index = model.index(1, 0)
        model.handle_index_clicked(index)
        assert model.empty_selected
        assert model.all_selected

    def test_click_select_all_when_not_all_selected(self, model, data):
        model.set_list(data)
        index = model.index(2, 0)
        model.handle_index_clicked(index)
        index = model.index(0, 0)
        model.handle_index_clicked(index)
        assert model.all_selected
        assert model._selected == set(data)

    def test_set_filter_index(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        assert model._filter_index == [3, 4, 5]
        expected = ["(Select all)", "(Empty)", "(Add current selection to filter)"] + [
            data[i] for i in model._filter_index
        ]
        assert_list_model_data_pytest(model, expected)
        expected = [Qt.CheckState.Checked, Qt.CheckState.Checked, Qt.CheckState.Unchecked] + len(
            model._filter_index
        ) * [Qt.CheckState.Checked]
        assert_list_model_data_pytest(model, expected, Qt.ItemDataRole.CheckStateRole)

    def test_set_filter_index_without_empty_option(self, model_without_empty, data):
        model_without_empty.set_list(data)
        model_without_empty.set_filter("b")
        assert model_without_empty._filter_index == [3, 4, 5]
        expected = ["(Select all)", "(Add current selection to filter)"] + [
            data[i] for i in model_without_empty._filter_index
        ]
        assert_list_model_data_pytest(model_without_empty, expected)
        expected = [Qt.CheckState.Checked, Qt.CheckState.Unchecked] + len(model_without_empty._filter_index) * [
            Qt.CheckState.Checked
        ]
        assert_list_model_data_pytest(model_without_empty, expected, Qt.ItemDataRole.CheckStateRole)

    def test_add_to_selection_when_filter(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        assert not model._add_to_selection
        assert (
            model.data(model.index(len(model._action_rows) - 1, 0), Qt.ItemDataRole.CheckStateRole)
            == Qt.CheckState.Unchecked
        )

    def test_clicking_add_to_selection(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        index = model.index(2, 0)
        assert index.data() == "(Add current selection to filter)"
        assert index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Unchecked
        model.handle_index_clicked(index)
        assert index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked

    def test_clicking_add_to_selection_without_empty_option(self, model_without_empty, data):
        model_without_empty.set_list(data)
        model_without_empty.set_filter("b")
        index = model_without_empty.index(1, 0)
        assert index.data() == "(Add current selection to filter)"
        assert index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Unchecked
        model_without_empty.handle_index_clicked(index)
        assert index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked

    def test_selected_when_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        assert model._selected == set(data)
        assert model._selected_filtered == set(data[3:])

    def test_get_data_when_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        assert model.data(model.index(len(model._action_rows), 0)) == "b"

    def test_click_select_all_when_all_selected_and_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        index = model.index(0, 0)
        model.handle_index_clicked(index)
        assert not model.all_selected
        assert model._selected == set(data)
        assert model._selected_filtered == set()

    def test_click_select_all_when_all_not_selected_and_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        index = model.index(3, 0)
        model.handle_index_clicked(index)
        index = model.index(0, 0)
        model.handle_index_clicked(index)
        assert model.all_selected
        assert model._selected == set(data)
        assert model._selected_filtered == set(data[3:])

    def test_click_selected_item_when_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        index = model.index(len(model._action_rows), 0)
        model.handle_index_clicked(index)
        assert model._selected_filtered == set(data[4:])
        assert not model.all_selected

    def test_click_unselected_item_when_filtered(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        model._selected_filtered.discard("b")
        index = model.index(len(model._action_rows), 0)
        model.handle_index_clicked(index)
        assert model._selected_filtered == set(data[3:])
        assert model.all_selected

    def test_remove_filter(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        model.remove_filter()
        assert not model._is_filtered
        assert model._selected == set(data)
        assert model.rowCount() == 8

    def test_apply_filter_with_replace(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        model.apply_filter()
        assert not model._is_filtered
        assert model._selected == set(data[3:])
        assert model.rowCount() == 8
        assert not model.empty_selected

    def test_apply_filter_with_add(self, model, data):
        model.set_list(data)
        model.set_filter("b")
        model._add_to_selection = True
        model._selected_filtered.discard("bbb")
        model.apply_filter()
        assert not model._is_filtered
        assert model._selected == set(data[:5])
        assert model.rowCount() == 8
        assert not model.all_selected

    def test_add_item_with_select_with_filter_last(self, model, data):
        new_item = ["bbbb"]
        model.set_list(data)
        model.set_filter("b")
        model.add_items(new_item)
        assert model._data == sorted(data + new_item)
        assert model.data_set == set(data + new_item)
        assert model._filter_index == [3, 4, 5, 6]
        assert model._selected_filtered == set(data[3:] + new_item)
        assert model.data(model.index(3 + len(model._action_rows), 0)) == new_item[0]

    def test_add_item_with_select_with_filter_first(self, model, data):
        new_item = ["0b"]
        model.set_list(data)
        model.set_filter("b")
        model.add_items(new_item)
        assert model._filter_index == [3, 4, 5, 6]
        assert model.data(model.index(3 + len(model._action_rows), 0)) == new_item[0]

    def test_add_item_with_select_with_filter_middle(self, model, data):
        new_item = ["b1"]
        model.set_list(data)
        model.set_filter("b")
        model.add_items(new_item)
        assert model._filter_index == [3, 4, 5, 6]
        assert model.data(model.index(3 + len(model._action_rows), 0)) == new_item[0]

    def test_remove_items_data(self, model, data):
        items = set("a")
        model.set_list(data)
        model.remove_items(items)
        assert model._data == data[1:]
        assert model.data_set == set(data[1:])

    def test_remove_items_selected(self, model, data):
        items = set("a")
        model.set_list(data)
        model.remove_items(items)
        assert model._selected == set(data[1:])
        assert model.all_selected

    def test_remove_items_not_selected(self, model, data):
        items = set("a")
        model.set_list(data)
        model._selected.discard("a")
        model.all_selected = False
        model.remove_items(items)
        assert model._selected == set(data[1:])
        assert model.all_selected

    def test_remove_items_filtered_data(self, model, data):
        items = set("b")
        model.set_list(data)
        model.set_filter("b")
        model.remove_items(items)
        assert model._filter_index == [3, 4]
        assert model._selected_filtered == set(data[4:])

    def test_remove_items_filtered_data_middle(self, model, data):
        items = set("bb")
        model.set_list(data)
        model.set_filter("b")
        model.remove_items(items)
        assert model._filter_index == [3, 4]

    def test_remove_items_filtered_data_not_selected(self, model, data):
        items = set("b")
        model.set_list(data)
        model.set_filter("b")
        model._selected_filtered.discard("a")
        model.all_selected = False
        model.remove_items(items)
        assert model._selected_filtered == set(data[4:])
        assert model.all_selected

    def test_half_finished_expression_does_not_raise_exception(self, model, data):
        model.set_list(data)
        model.set_filter("[")
        assert [model.index(row, 0).data() for row in range(model.rowCount())] == ["(Select all)", "(Empty)"] + data

    def test_only_whitespaces_in_filter_expression_does_not_filter(self, model, data):
        model.set_list(data)
        model.set_filter("   ")
        assert [model.index(row, 0).data() for row in range(model.rowCount())] == ["(Select all)", "(Empty)"] + data
