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
Unit tests for PivotModel class.

:author: P. Vennström (VTT)
:date:   3.12.2018
"""

import unittest
from unittest import mock
from PySide2.QtCore import Qt
from mvcmodels.tabularview_models import FilterCheckboxListModel


class TestPivotModel(unittest.TestCase):
    def setUp(self):
        self.data = ['a', 'aa', 'aaa', 'b', 'bb', 'bbb']

    def test_init_model(self):
        FilterCheckboxListModel()

    def test_set_list(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        self.assertEqual(model._data, sorted(self.data))
        self.assertEqual(model._data_set, set(self.data))
        self.assertEqual(model._selected, set(self.data))
        self.assertTrue(model._all_selected)

    def test_is_all_selected_when_all_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        self.assertTrue(model._is_all_selected())

    def test_is_all_selected_when_not_all_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model._selected.discard('a')
        self.assertFalse(model._is_all_selected())

    def test_is_all_selected_when_not_empty_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model._empty_selected = False
        self.assertFalse(model._is_all_selected())

    def test_add_item_with_select_without_filter(self):
        new_item = ['aaaa']
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginInsertRows") as bir, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endInsertRows"
        ) as eir, mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            model.add_item(new_item)
        self.assertEqual(model._data, sorted(self.data + new_item))
        self.assertEqual(model._data_set, set(self.data + new_item))

    def test_add_item_without_select_without_filter(self):
        new_item = ['aaaa']
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginInsertRows") as bir, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endInsertRows"
        ) as eir, mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            model.add_item(new_item, selected=False)
        self.assertFalse(model._all_selected)

    def test_click_select_all_when_all_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(0, 0)
            model.click_index(index)
        self.assertFalse(model._all_selected)
        self.assertEqual(model._selected, set())

    def test_click_selected_item(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
        self.assertEqual(model._selected, set(self.data).difference(set(['a'])))
        self.assertFalse(model._all_selected)

    def test_click_unselected_item(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model._selected.discard('a')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
        self.assertEqual(model._selected, set(self.data))
        self.assertTrue(model._all_selected)

    def test_click_select_empty_when_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(1, 0)
            model.click_index(index)
        self.assertFalse(model._empty_selected)
        self.assertFalse(model._all_selected)

    def test_click_select_empty_when_unselected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model._empty_selected = False
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(1, 0)
            model.click_index(index)
        self.assertTrue(model._empty_selected)
        self.assertTrue(model._all_selected)

    def test_click_select_all_when_not_all_selected(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
            index = model.index(0, 0)
            model.click_index(index)
        self.assertTrue(model._all_selected)
        self.assertEqual(model._selected, set(self.data))

    def test_set_filter_index(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        self.assertEqual(model._filter_index, [3, 4, 5])

    def test_rowCount_when_filter(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        self.assertEqual(model.rowCount(), 5)

    def test_add_to_selection_when_filter(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        self.assertFalse(model._add_to_selection)
        self.assertFalse(model.data(model.index(1, 0), Qt.CheckStateRole))

    def test_selected_when_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        self.assertEqual(model._selected, set(self.data))
        self.assertEqual(model._selected_filtered, set(self.data[3:]))

    def test_get_data_when_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        self.assertEqual(model.data(model.index(2, 0)), 'b')

    def test_click_select_all_when_all_selected_and_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(0, 0)
            model.click_index(index)
        self.assertFalse(model._all_selected)
        self.assertEqual(model._selected, set(self.data))
        self.assertEqual(model._selected_filtered, set())

    def test_click_select_all_when_all_not_selected_and_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
            index = model.index(0, 0)
            model.click_index(index)
        self.assertTrue(model._all_selected)
        self.assertEqual(model._selected, set(self.data))
        self.assertEqual(model._selected_filtered, set(self.data[3:]))

    def test_click_selected_item_when_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
        self.assertEqual(model._selected_filtered, set(self.data[4:]))
        self.assertFalse(model._all_selected)

    def test_click_unselected_item_when_filtered(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        model._selected_filtered.discard('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            index = model.index(2, 0)
            model.click_index(index)
        self.assertEqual(model._selected_filtered, set(self.data[3:]))
        self.assertTrue(model._all_selected)

    def test_remove_filter(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        model.remove_filter()
        self.assertFalse(model._is_filtered)
        self.assertEqual(model._selected, set(self.data))
        self.assertEqual(model.rowCount(), 8)

    def test_apply_filter_with_replace(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        model.apply_filter()
        self.assertFalse(model._is_filtered)
        self.assertEqual(model._selected, set(self.data[3:]))
        self.assertEqual(model.rowCount(), 8)
        self.assertFalse(model._empty_selected)

    def test_apply_filter_with_add(self):
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        model._add_to_selection = True
        model._selected_filtered.discard('bbb')
        model.apply_filter()
        self.assertFalse(model._is_filtered)
        self.assertEqual(model._selected, set(self.data[:5]))
        self.assertEqual(model.rowCount(), 8)
        self.assertFalse(model._all_selected)

    def test_add_item_with_select_with_filter_last(self):
        new_item = ['bbbb']
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginInsertRows") as bir, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endInsertRows"
        ) as eir, mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            model.add_item(new_item)
        self.assertEqual(model._data, sorted(self.data + new_item))
        self.assertEqual(model._data_set, set(self.data + new_item))
        self.assertEqual(model._filter_index, [3, 4, 5, 6])
        self.assertEqual(model._selected_filtered, set(self.data[3:] + new_item))
        self.assertEqual(model.data(model.index(3 + 2, 0)), new_item[0])

    def test_add_item_with_select_with_filter_first(self):
        new_item = ['0b']
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginInsertRows") as bir, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endInsertRows"
        ) as eir, mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            model.add_item(new_item)
        self.assertEqual(model._filter_index, [0, 4, 5, 6])
        self.assertEqual(model.data(model.index(0 + 2, 0)), new_item[0])

    def test_add_item_with_select_with_filter_middle(self):
        new_item = ['b1']
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginInsertRows") as bir, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endInsertRows"
        ) as eir, mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.dataChanged") as dc:
            model.add_item(new_item)
        self.assertEqual(model._filter_index, [3, 4, 5, 6])
        self.assertEqual(model.data(model.index(1 + 2, 0)), new_item[0])

    def test_remove_items_data(self):
        items = set('a')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._data, self.data[1:])
        self.assertEqual(model._data_set, set(self.data[1:]))

    def test_remove_items_selected(self):
        items = set('a')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._selected, set(self.data[1:]))
        self.assertTrue(model._all_selected)

    def test_remove_items_not_selected(self):
        items = set('a')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model._selected.discard('a')
        model._all_selected = False
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._selected, set(self.data[1:]))
        self.assertTrue(model._all_selected)

    def test_remove_items_filtered_data(self):
        items = set('b')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._filter_index, [3, 4])
        self.assertEqual(model._selected_filtered, set(self.data[4:]))

    def test_remove_items_filtered_data_midle(self):
        items = set('bb')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._filter_index, [3, 4])

    def test_remove_items_filtered_data_not_selected(self):
        items = set('b')
        model = FilterCheckboxListModel()
        model.set_list(self.data)
        model.set_filter('b')
        model._selected_filtered.discard('a')
        model._all_selected = False
        with mock.patch("mvcmodels.tabularview_models.FilterCheckboxListModel.beginResetModel") as br, mock.patch(
            "mvcmodels.tabularview_models.FilterCheckboxListModel.endResetModel"
        ) as er:
            model.remove_items(items)
        self.assertEqual(model._selected_filtered, set(self.data[4:]))
        self.assertTrue(model._all_selected)


if __name__ == '__main__':
    unittest.main()
