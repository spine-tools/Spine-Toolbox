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
import unittest
from contextlib import contextmanager
from PySide6.QtWidgets import QApplication
from spinetoolbox.widgets.select_database_items import SelectDatabaseItems


class TestSelectDatabaseItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_restore_previously_checked_states(self):
        stored_states = {"feature": True, "entity": True}
        with _select_database_items(stored_states) as widget:
            self.assertEqual(
                widget.checked_states(),
                {
                    "alternative": False,
                    "entity_group": False,
                    "entity_metadata": False,
                    "list_value": False,
                    "metadata": False,
                    "entity": True,
                    "entity_class": False,
                    "superclass_subclass": False,
                    "entity_alternative": False,
                    "parameter_definition": False,
                    "parameter_value": False,
                    "parameter_value_list": False,
                    "parameter_value_metadata": False,
                    "scenario": False,
                    "scenario_alternative": False,
                },
            )

    def test_any_checked(self):
        with _select_database_items(None) as widget:
            self.assertFalse(widget.any_checked())
            widget._item_check_boxes["parameter_value_metadata"].click()
            self.assertTrue(widget.any_checked())

    def test_any_structural_item_checked(self):
        stored_states = {
            "object": True,
            "relationship": True,
            "entity_group": True,
            "parameter_value": True,
            "entity_metadata": True,
            "parameter_value_metadata": True,
            "scenario": True,
            "alternative": True,
            "scenario_alternative": True,
        }
        with _select_database_items(stored_states) as widget:
            self.assertFalse(widget.any_structural_item_checked())
            widget._item_check_boxes["list_value"].click()
            self.assertTrue(widget.any_structural_item_checked())


@contextmanager
def _select_database_items(checked_states):
    widget = SelectDatabaseItems(checked_states)
    try:
        yield widget
    finally:
        widget.deleteLater()


if __name__ == "__main__":
    unittest.main()
