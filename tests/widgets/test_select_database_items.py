######################################################################################################################
# Copyright (C) 2017-2023 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for ``select_database_items`` module."""
from contextlib import contextmanager
import unittest
from spinedb_api import DatabaseMapping
from spinedb_api.mapped_items import ITEM_CLASS_BY_TYPE
from spinetoolbox.widgets.select_database_items import SelectDatabaseItems
from tests.mock_helpers import TestCaseWithQApplication


class TestSelectDatabaseItems(TestCaseWithQApplication):
    ITEMS = tuple(type_ for type_ in DatabaseMapping.item_types() if not ITEM_CLASS_BY_TYPE[type_].is_protected)

    def test_restore_previously_checked_states(self):
        stored_states = {"alternative": True, "entity": True}
        with _select_database_items(stored_states) as widget:
            expected = {**{item: False for item in self.ITEMS}, **stored_states}
            self.assertEqual(widget.checked_states(), expected)

    def test_any_checked(self):
        with _select_database_items(None) as widget:
            self.assertFalse(widget.any_checked())
            widget._item_check_boxes["parameter_value_metadata"].click()
            self.assertTrue(widget.any_checked())

    def test_any_structural_item_checked(self):
        stored_states = {item: True for item in SelectDatabaseItems._DATA_ITEMS + SelectDatabaseItems._SCENARIO_ITEMS}
        with _select_database_items(stored_states) as widget:
            self.assertFalse(widget.any_structural_item_checked())
            widget._item_check_boxes["list_value"].click()
            self.assertTrue(widget.any_structural_item_checked())

    def test_select_data_items(self):
        with _select_database_items({}) as widget:
            widget._ui.select_data_items_button.click()
            expected = {item: item in SelectDatabaseItems._DATA_ITEMS for item in self.ITEMS}
            self.assertEqual(widget.checked_states(), expected)

    def test_select_scenario_items(self):
        with _select_database_items({}) as widget:
            widget._ui.select_scenario_items_button.click()
            expected = {item: item in SelectDatabaseItems._SCENARIO_ITEMS for item in self.ITEMS}
            self.assertEqual(widget.checked_states(), expected)

    def test_select_structural_items(self):
        with _select_database_items({}) as widget:
            widget._ui.select_structural_items_button.click()
            expected = {item: item in SelectDatabaseItems._STRUCTURAL_ITEMS for item in self.ITEMS}
            self.assertEqual(widget.checked_states(), expected)

    def test_items_in_some_category(self):
        self.assertEqual(
            set(self.ITEMS)
            - set(SelectDatabaseItems._DATA_ITEMS)
            - set(SelectDatabaseItems._SCENARIO_ITEMS)
            - set(SelectDatabaseItems._STRUCTURAL_ITEMS),
            set(),
        )

    def test_no_categories_overlap(self):
        self.assertEqual(set(SelectDatabaseItems._DATA_ITEMS) & set(SelectDatabaseItems._SCENARIO_ITEMS), set())
        self.assertEqual(set(SelectDatabaseItems._DATA_ITEMS) & set(SelectDatabaseItems._STRUCTURAL_ITEMS), set())
        self.assertEqual(set(SelectDatabaseItems._SCENARIO_ITEMS) & set(SelectDatabaseItems._STRUCTURAL_ITEMS), set())


@contextmanager
def _select_database_items(checked_states):
    widget = SelectDatabaseItems(checked_states)
    try:
        yield widget
    finally:
        widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
