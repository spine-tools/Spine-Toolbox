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

:author: A. Soininen (VTT)
:date:   12.7.2019
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, Mock
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import (
    DatabaseMapping,
    to_database,
    DateTime,
    Duration,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)
from spinedb_api.parameter_value import join_value_and_type
from spinedb_api import import_functions
from spinetoolbox.spine_db_manager import SpineDBManager


class TestParameterValueFormatting(unittest.TestCase):
    """Tests for parameter_value formatting in SpineDBManager."""

    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.db_mngr = SpineDBManager(None, None)
        self.db_mngr.get_item = Mock()

    def tearDown(self):
        self.db_mngr.close_all_sessions()
        self.db_mngr.clean_up()
        self.db_mngr.deleteLater()
        QApplication.processEvents()

    def get_value(self, role):
        mock_db_map = Mock()
        id_ = 0
        return self.db_mngr.get_value(mock_db_map, "parameter_value", id_, role)

    def test_plain_number_in_display_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "2.3")

    def test_plain_number_in_edit_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"2.3", None))

    def test_plain_number_in_tool_tip_role(self):
        value = 2.3
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_date_time_in_display_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "2019-07-12T16:00:00")

    def test_date_time_in_edit_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_date_time_in_tool_tip_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_duration_in_display_role(self):
        value = Duration("3Y")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "3Y")

    def test_duration_in_edit_role(self):
        value = Duration("2M")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_duration_in_tool_tip_role(self):
        value = Duration("13D")
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_time_pattern_in_display_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time pattern")

    def test_time_pattern_in_edit_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_pattern_in_tool_tip_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        self.assertIsNone(self.get_value(Qt.ToolTipRole))

    def test_time_series_in_display_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time series")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Time series")

    def test_time_series_in_edit_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_series_in_tool_tip_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", ["7 hours", "12 hours"], [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12 08:00:00, resolution: [7h, 12h], length: 3")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.return_value = dict(zip(("value", "type"), to_database(value)))
        formatted = self.get_value(Qt.ToolTipRole)
        self.assertEqual(formatted, "Start: 2019-07-12T08:00:00, resolution: variable, length: 2")

    def test_broken_value_in_display_role(self):
        value = b"dubbidubbidu"
        self.db_mngr.get_item.return_value = {"value": value, "type": None}
        formatted = self.get_value(Qt.DisplayRole)
        self.assertEqual(formatted, "Error")

    def test_broken_value_in_edit_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.return_value = {"value": value, "type": None}
        formatted = self.get_value(Qt.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"diibadaaba", None))

    def test_broken_value_in_tool_tip_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.return_value = {"value": value, "type": None}
        formatted = self.get_value(Qt.ToolTipRole)
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
                db_map_data,
                {db_map: [{"id": 1, "name": "my_metadata", "value": "Metadata value.", "commit_id": None}]},
            )

        db_map_data = {db_map: [{"name": "my_metadata", "value": "Metadata value."}]}
        self._db_mngr.add_items(db_map_data, "add_metadata", "metadata", callback=callback)

    def test_add_object_metadata(self):
        db_map = DatabaseMapping(self._db_url, create=True)
        import_functions.import_object_classes(db_map, ("my_class",))
        import_functions.import_objects(db_map, (("my_class", "my_object"),))
        import_functions.import_metadata(db_map, ('{"metaname": "metavalue"}',))
        db_map.commit_session("Add test data.")
        db_map.connection.close()

        def callback(db_map_data):
            self.assertEqual(
                db_map_data,
                {db_map: [{'entity_id': 1, 'metadata_id': 1, 'commit_id': None, 'id': 1}]},
            )

        db_map_data = {db_map: [{"entity_id": 1, "metadata_id": 1}]}
        self._db_mngr.add_items(db_map_data, "add_entity_metadata", "entity_metadata", callback=callback)


if __name__ == '__main__':
    unittest.main()
