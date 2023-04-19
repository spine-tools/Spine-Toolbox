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
Unit tests for the spine_db_manager module.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    DatabaseMapping,
    to_database,
    DateTime,
    Duration,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)
from spinedb_api.parameter_value import join_value_and_type, from_database
from spinedb_api import import_functions
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import signal_waiter


def _make_get_item_side_effect(value, type_):
    def _get_item(db_map, item_type, id_, only_visible=True):
        if item_type != "parameter_value":
            return {}
        return {"value": value, "type": type_, "list_value_id": None}

    return _get_item


class TestParameterValueFormatting(unittest.TestCase):
    """Tests for parameter_value formatting in SpineDBManager."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.db_mngr = SpineDBManager(None, None)
        self.db_mngr.get_item = MagicMock()

    def tearDown(self):
        self.db_mngr.close_all_sessions()
        self.db_mngr.clean_up()
        self.db_mngr.deleteLater()
        QApplication.processEvents()

    def get_value(self, role):
        mock_db_map = MagicMock()
        id_ = 0
        return self.db_mngr.get_value(mock_db_map, "parameter_value", id_, role)

    def test_plain_number_in_display_role(self):
        value = 2.3
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2.3")

    def test_plain_number_in_edit_role(self):
        value = 2.3
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"2.3", None))

    def test_plain_number_in_tool_tip_role(self):
        value = 2.3
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_date_time_in_display_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2019-07-12T16:00:00")

    def test_date_time_in_edit_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_date_time_in_tool_tip_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_duration_in_display_role(self):
        value = Duration("3Y")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "3Y")

    def test_duration_in_edit_role(self):
        value = Duration("2M")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_duration_in_tool_tip_role(self):
        value = Duration("13D")
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_time_pattern_in_display_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time pattern")

    def test_time_pattern_in_edit_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_pattern_in_tool_tip_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_time_series_in_display_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")

    def test_time_series_in_edit_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_series_in_tool_tip_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", ["7 hours", "12 hours"], [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12 08:00:00, resolution: [7h, 12h], length: 3")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12T08:00:00, resolution: variable, length: 2")

    def test_broken_value_in_display_role(self):
        value = b"dubbidubbidu"
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Error")

    def test_broken_value_in_edit_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"diibadaaba", None))

    def test_broken_value_in_tool_tip_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.side_effect = _make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertTrue(formatted.startswith('Could not decode the value'))


class TestAddItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        db_path = Path(self._temp_dir.name, "db.sqlite")
        self._db_url = "sqlite:///" + str(db_path)
        self._db_mngr = SpineDBManager(None, None)
        self._logger = MagicMock()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        # Database connection may still be open. Retry cleanup until it succeeds.
        running = True
        while running:
            QApplication.processEvents()
            try:
                self._temp_dir.cleanup()
            except NotADirectoryError:
                pass
            else:
                running = False

    def test_add_metadata(self):
        db_map = self._db_mngr.get_db_map(self._db_url, self._logger, create=True)

        def callback(db_map_data):
            self.assertEqual(
                db_map_data, {db_map: [{"id": 1, "name": "my_metadata", "value": "Metadata value.", "commit_id": 2}]}
            )

        db_map_data = {db_map: [{"name": "my_metadata", "value": "Metadata value."}]}
        self._db_mngr.add_items(db_map_data, "metadata", callback=callback)

    def test_add_object_metadata(self):
        db_map = DatabaseMapping(self._db_url, create=True)
        import_functions.import_object_classes(db_map, ("my_class",))
        import_functions.import_objects(db_map, (("my_class", "my_object"),))
        import_functions.import_metadata(db_map, ('{"metaname": "metavalue"}',))
        db_map.commit_session("Add test data.")
        db_map.connection.close()

        def callback(db_map_data):
            self.assertEqual(db_map_data, {db_map: [{'entity_id': 1, 'metadata_id': 1, 'commit_id': None, 'id': 1}]})

        db_map_data = {db_map: [{"entity_id": 1, "metadata_id": 1}]}
        self._db_mngr.add_items(db_map_data, "entity_metadata", callback=callback)


class TestImportData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        logger = MagicMock()
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
        self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._temp_dir.cleanup()

    def test_import_parameter_value_lists(self):
        with signal_waiter(
            self._db_mngr.items_added, condition=lambda item_type, _: item_type == "list_value"
        ) as waiter:
            self._db_mngr.import_data(
                {self._db_map: {"parameter_value_lists": [["list_1", "first value"], ["list_1", "second value"]]}}
            )
            waiter.wait()
        value_lists = self._db_mngr.get_items(self._db_map, "parameter_value_list")
        list_values = self._db_mngr.get_items(self._db_map, "list_value")
        self.assertEqual(len(value_lists), 1)
        value_list = value_lists[0]
        index_to_id = dict(zip(value_list["value_id_list"], value_list["value_index_list"]))
        values = len(index_to_id) * [None]
        for row in list_values:
            value = from_database(row["value"], row["type"])
            values[index_to_id[row["id"]]] = value
        self.assertEqual(values, ["first value", "second value"])


class TestOpenDBEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._temp_dir = TemporaryDirectory()
        db_path = Path(self._temp_dir.name, "db.sqlite")
        self._db_url = "sqlite:///" + str(db_path)
        self._db_mngr = SpineDBManager(QSettings(), None)
        self._logger = MagicMock()

    def test_open_db_editor(self):
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        self.assertFalse(editors)
        self._db_mngr.open_db_editor({self._db_url: "test"})
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        self.assertEqual(len(editors), 1)
        self._db_mngr.open_db_editor({self._db_url: "test"})
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        self.assertEqual(len(editors), 1)
        self._db_mngr.open_db_editor({self._db_url: "not_the_same"})
        self.assertEqual(len(editors), 1)
        editor = editors[0]
        self.assertEqual(editor.tab_widget.count(), 2)
        for editor in self._db_mngr.get_all_multi_spine_db_editors():
            QApplication.processEvents()
            editor.close()

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        self._db_mngr.clean_up()
        # Database connection may still be open. Retry cleanup until it succeeds.
        running = True
        while running:
            QApplication.processEvents()
            try:
                self._temp_dir.cleanup()
            except NotADirectoryError:
                pass
            else:
                running = False


if __name__ == '__main__':
    unittest.main()
