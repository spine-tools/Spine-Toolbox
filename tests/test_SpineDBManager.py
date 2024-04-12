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

"""Unit tests for the spine_db_manager module."""
import time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    to_database,
    DateTime,
    Duration,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
)
from spinedb_api.parameter_value import join_value_and_type, from_database, Map, ParameterValueFormatError
from spinedb_api import import_functions
from spinedb_api.spine_io.importers.excel_reader import get_mapped_data_from_xlsx
from spinetoolbox.fetch_parent import FlexibleFetchParent

from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.helpers import signal_waiter


class TestParameterValueFormatting(unittest.TestCase):
    """Tests for parameter_value formatting in SpineDBManager."""

    @staticmethod
    def _make_get_item_side_effect(value, type_):
        def _get_item(db_map, item_type, id_, only_visible=True):
            if item_type != "parameter_value":
                return {}
            try:
                parsed_value = from_database(value, type_=type_)
            except ParameterValueFormatError as error:
                parsed_value = error
            return {"parsed_value": parsed_value, "value": value, "type": type_, "list_value_id": None}

        return _get_item

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
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2.3")

    def test_plain_number_in_edit_role(self):
        value = 2.3
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"2.3", None))

    def test_plain_number_in_tool_tip_role(self):
        value = 2.3
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_date_time_in_display_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2019-07-12T16:00:00")

    def test_date_time_in_edit_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_date_time_in_tool_tip_role(self):
        value = DateTime("2019-07-12T16:00")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_duration_in_display_role(self):
        value = Duration("3Y")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "3Y")

    def test_duration_in_edit_role(self):
        value = Duration("2M")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_duration_in_tool_tip_role(self):
        value = Duration("13D")
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_time_pattern_in_display_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time pattern")

    def test_time_pattern_in_edit_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_pattern_in_tool_tip_role(self):
        value = TimePattern(["M1-12"], [5.0])
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        self.assertIsNone(self.get_value(Qt.ItemDataRole.ToolTipRole))

    def test_time_series_in_display_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")

    def test_time_series_in_edit_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_series_in_tool_tip_role(self):
        value = TimeSeriesFixedResolution("2019-07-12T08:00", ["7 hours", "12 hours"], [1.1, 2.2, 3.3], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "<qt>Start: 2019-07-12 08:00:00<br>resolution: [7h, 12h]<br>length: 3</qt>")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(*to_database(value))
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "<qt>Start: 2019-07-12T08:00:00<br>resolution: variable<br>length: 2</qt>")

    def test_broken_value_in_display_role(self):
        value = b"dubbidubbidu"
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Error")

    def test_broken_value_in_edit_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"diibadaaba", None))

    def test_broken_value_in_tool_tip_role(self):
        value = b"diibadaaba"
        self.db_mngr.get_item.side_effect = self._make_get_item_side_effect(value, None)
        formatted = self.get_value(Qt.ItemDataRole.ToolTipRole)
        self.assertTrue(formatted.startswith("<qt>Could not decode the value"))


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
        db_map_data = {db_map: [{"name": "my_metadata", "value": "Metadata value.", "id": 1}]}
        self._db_mngr.add_items("metadata", db_map_data)
        self.assertEqual(
            self._db_mngr.get_item(db_map, "metadata", 1).resolve(),
            {"name": "my_metadata", "value": "Metadata value.", "id": 1},
        )

    def test_add_object_metadata(self):
        db_map = self._db_mngr.get_db_map(self._db_url, None, create=True)
        import_functions.import_object_classes(db_map, ("my_class",))
        import_functions.import_objects(db_map, (("my_class", "my_object"),))
        import_functions.import_metadata(db_map, ('{"metaname": "metavalue"}',))
        db_map.commit_session("Add test data.")
        db_map.close()
        db_map_data = {db_map: [{"entity_id": 1, "metadata_id": 1, "id": 1}]}
        self._db_mngr.add_items("entity_metadata", db_map_data)
        self.assertEqual(
            self._db_mngr.get_item(db_map, "entity_metadata", 1).resolve(), {"entity_id": 1, "metadata_id": 1, "id": 1}
        )


class TestImportExportData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        logger = MagicMock()
        self.editor = MagicMock()
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
        self._db_map = self._db_mngr.get_db_map(url, logger, codename="database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._temp_dir.cleanup()

    def test_export_then_import_time_series_parameter_value(self):
        file_path = str(Path(self._temp_dir.name) / "test.xlsx")
        data = {
            "entity_classes": [("A", (), None, None, False)],
            "entities": [("A", "aa", None)],
            "parameter_definitions": [("A", "test1", None, None, None)],
            "parameter_values": [
                (
                    "A",
                    "aa",
                    "test1",
                    {
                        "type": "time_series",
                        "index": {
                            "start": "2000-01-01 00:00:00",
                            "resolution": "1h",
                            "ignore_year": False,
                            "repeat": False,
                        },
                        "data": [0.0, 1.0, 2.0, 4.0, 8.0, 0.0],
                    },
                    "Base",
                )
            ],
            "alternatives": [("Base", "Base alternative")],
        }
        self._db_mngr.export_to_excel(file_path, data, self.editor)
        mapped_data, errors = get_mapped_data_from_xlsx(file_path)
        self.assertEqual(errors, [])
        self._db_mngr.import_data({self._db_map: mapped_data})
        self._db_map.commit_session("imported items")
        value = self._db_map.query(self._db_map.entity_parameter_value_sq).one()
        time_series = from_database(value.value, value.type)
        expected_result = TimeSeriesVariableResolution(
            (
                "2000-01-01T00:00:00",
                "2000-01-01T01:00:00",
                "2000-01-01T02:00:00",
                "2000-01-01T03:00:00",
                "2000-01-01T04:00:00",
                "2000-01-01T05:00:00",
            ),
            (0.0, 1.0, 2.0, 4.0, 8.0, 0.0),
            False,
            False,
        )
        self.assertEqual(time_series, expected_result)

    def test_export_empty_data_does_not_traceback_because_there_is_nothing_to_commit(self):
        file_path = str(Path(self._temp_dir.name) / "test.xlsx")
        data = {}
        self._db_mngr.export_to_excel(file_path, data, self.editor)
        mapped_data, errors = get_mapped_data_from_xlsx(file_path)
        self.assertEqual(errors, [])
        self.assertEqual(mapped_data, {"alternatives": ["Base"]})

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
        self.assertEqual(value_list["name"], "list_1")
        self.assertEqual(
            [(from_database(x["value"], x["type"]), x["index"]) for x in list_values],
            [("first value", 0), ("second value", 1)],
        )


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
        self._db_mngr.open_db_editor({self._db_url: "test"}, reuse_existing_editor=True)
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        self.assertEqual(len(editors), 1)
        self._db_mngr.open_db_editor({self._db_url: "test"}, reuse_existing_editor=True)
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        self.assertEqual(len(editors), 1)
        self._db_mngr.open_db_editor({self._db_url: "not_the_same"}, reuse_existing_editor=True)
        self.assertEqual(len(editors), 1)
        editor = editors[0]
        self.assertEqual(editor.tab_widget.count(), 1)
        # Finally try to open the first tab again
        self._db_mngr.open_db_editor({self._db_url: "test"}, reuse_existing_editor=True)
        editors = list(self._db_mngr.get_all_multi_spine_db_editors())
        editor = editors[0]
        self.assertEqual(editor.tab_widget.count(), 1)
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


class TestDuplicateEntity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_codename = cls.__name__ + "_db"
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._db_mngr = SpineDBManager(QSettings(), None)
        logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, codename=self.db_codename, create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def _assert_success(self, result):
        item, error = result
        self.assertIsNone(error)
        return item

    def test_duplicates_parameter_values_and_entity_alternatives(self):
        self._assert_success(self._db_map.add_alternative_item(name="low highs"))
        self._assert_success(self._db_map.add_entity_class_item(name="Widget"))
        self._assert_success(self._db_map.add_parameter_definition_item(name="x", entity_class_name="Widget"))
        self._assert_success(self._db_map.add_entity_item(name="capital W", entity_class_name="Widget"))
        self._assert_success(
            self._db_map.add_entity_alternative_item(
                entity_class_name="Widget", entity_byname=("capital W",), alternative_name="Base", active=False
            )
        )
        self._assert_success(
            self._db_map.add_entity_alternative_item(
                entity_class_name="Widget", entity_byname=("capital W",), alternative_name="low highs", active=True
            )
        )
        value, value_type = to_database(2.3)
        self._assert_success(
            self._db_map.add_parameter_value_item(
                entity_class_name="Widget",
                parameter_definition_name="x",
                entity_byname=("capital W",),
                alternative_name="low highs",
                type=value_type,
                value=value,
            )
        )
        self._db_mngr.duplicate_entity("capital W", "lower case w", "Widget", [self._db_map])
        entities = self._db_map.get_entity_items()
        self.assertEqual(len(entities), 2)
        self.assertEqual({e["name"] for e in entities}, {"capital W", "lower case w"})
        self.assertEqual({e["entity_class_name"] for e in entities}, {"Widget"})
        entity_alternatives = self._db_map.get_entity_alternative_items()
        self.assertEqual(len(entity_alternatives), 4)
        self.assertEqual(
            {(ea["entity_byname"], ea["alternative_name"], ea["active"]) for ea in entity_alternatives},
            {
                (("capital W",), "Base", False),
                (("capital W",), "low highs", True),
                (("lower case w",), "Base", False),
                (("lower case w",), "low highs", True),
            },
        )
        values = self._db_map.get_parameter_value_items()
        self.assertEqual(len(values), 2)
        self.assertEqual({v["entity_class_name"] for v in values}, {"Widget"})
        self.assertEqual({v["parameter_definition_name"] for v in values}, {"x"})
        self.assertEqual({v["entity_byname"] for v in values}, {("capital W",), ("lower case w",)})
        self.assertEqual({v["alternative_name"] for v in values}, {"low highs"})


class TestUpdateExpandedParameterValues(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, codename="database", create=True)

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_updating_indexed_value_changes_the_unparsed_value_in_database(self):
        self._db_map.add_entity_class_item(name="Gadget")
        self._db_map.add_parameter_definition_item(name="x", entity_class_name="Gadget")
        self._db_map.add_entity_item(name="biometer", entity_class_name="Gadget")
        value, value_type = to_database(Map(["a"], ["b"]))
        value_item, error = self._db_map.add_parameter_value_item(
            entity_class_name="Gadget",
            entity_byname=("biometer",),
            parameter_definition_name="x",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        self.assertIsNone(error)
        items_updated = MagicMock()
        fetch_parent = FlexibleFetchParent("parameter_value", handle_items_updated=items_updated)
        self._db_mngr.register_fetch_parent(self._db_map, fetch_parent)
        self._db_mngr.fetch_more(self._db_map, fetch_parent)
        new_value, new_type = to_database("c")
        update_item = {"id": value_item["id"], "index": "a", "value": new_value, "type": new_type}
        self._db_mngr.update_expanded_parameter_values({self._db_map: [update_item]})
        wait_start = time.monotonic()
        while not items_updated.called:
            QApplication.processEvents()
            if time.monotonic() - wait_start > 2.0:
                self.fail("timeout while waiting for update signal")
        updated_item = self._db_map.get_parameter_value_item(id=value_item["id"])
        update_value = from_database(updated_item["value"], updated_item["type"])
        self.assertEqual(update_value, Map(["a"], ["c"]))


if __name__ == "__main__":
    unittest.main()
