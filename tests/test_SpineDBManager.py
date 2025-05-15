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
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import (
    DateTime,
    Duration,
    TimePattern,
    TimeSeriesFixedResolution,
    TimeSeriesVariableResolution,
    import_functions,
    to_database,
)
from spinedb_api.parameter_value import Map, ParameterValueFormatError, from_database, join_value_and_type
from spinedb_api.spine_io.importers.excel_reader import get_mapped_data_from_xlsx
from spinetoolbox.fetch_parent import FlexibleFetchParent
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_manager import SpineDBManager
from tests.mock_helpers import TestCaseWithQApplication


class TestParameterValueFormatting(TestCaseWithQApplication):
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

    def setUp(self):
        app_settings = MagicMock()
        self.db_mngr = SpineDBManager(app_settings, None, synchronous=True)
        logger = MagicMock()
        self._db_map = self.db_mngr.get_db_map("sqlite://", logger, create=True)
        self._db_map.add_entity_class_item(name="Object")
        self._db_map.add_parameter_definition_item(name="x", entity_class_name="Object")
        self._db_map.add_entity_item(name="thing", entity_class_name="Object")

    def tearDown(self):
        self.db_mngr.close_all_sessions()
        self.db_mngr.clean_up()
        self.db_mngr.deleteLater()
        QApplication.processEvents()

    def _add_value(self, value, alternative="Base"):
        db_value, value_type = to_database(value)
        item, error = self._db_map.add_parameter_value_item(
            entity_class_name="Object",
            entity_byname=("thing",),
            parameter_definition_name="x",
            alternative_name=alternative,
            value=db_value,
            type=value_type,
        )
        self.assertIsNone(error)
        return item

    def test_plain_number_in_display_role(self):
        value = 2.3
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2.3")

    def test_plain_number_in_edit_role(self):
        value = 2.3
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"2.3", None))

    def test_plain_number_in_tool_tip_role(self):
        value = 2.3
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertIsNone(formatted)

    def test_date_time_in_display_role(self):
        value = DateTime("2019-07-12T16:00")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "2019-07-12T16:00:00")

    def test_date_time_in_edit_role(self):
        value = DateTime("2019-07-12T16:00")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_date_time_in_tool_tip_role(self):
        value = DateTime("2019-07-12T16:00")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertIsNone(formatted)

    def test_duration_in_display_role(self):
        value = Duration("3Y")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "3Y")

    def test_duration_in_edit_role(self):
        value = Duration("2M")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_duration_in_tool_tip_role(self):
        value = Duration("13D")
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertIsNone(formatted)

    def test_time_pattern_in_display_role(self):
        value = TimePattern(["M1-12"], [5.0])
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time pattern")

    def test_time_pattern_in_edit_role(self):
        value = TimePattern(["M1-12"], [5.0])
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_pattern_in_tool_tip_role(self):
        value = TimePattern(["M1-12"], [5.0])
        item = self._add_value(value)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertIsNone(formatted)

    def test_time_series_in_display_role(self):
        self._db_map.add_alternative_item(name="fixed_resolution")
        self._db_map.add_alternative_item(name="variable_resolution")
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        item = self._add_value(value, "fixed_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        item = self._add_value(value, "variable_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Time series")

    def test_time_series_in_edit_role(self):
        self._db_map.add_alternative_item(name="fixed_resolution")
        self._db_map.add_alternative_item(name="variable_resolution")
        value = TimeSeriesFixedResolution("2019-07-12T08:00", "7 hours", [1.1, 2.2, 3.3], False, False)
        item = self._add_value(value, "fixed_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        item = self._add_value(value, "variable_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(*to_database(value)))

    def test_time_series_in_tool_tip_role(self):
        self._db_map.add_alternative_item(name="fixed_resolution")
        self._db_map.add_alternative_item(name="variable_resolution")
        value = TimeSeriesFixedResolution("2019-07-12T08:00", ["7 hours", "12 hours"], [1.1, 2.2, 3.3], False, False)
        item = self._add_value(value, "fixed_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "<qt>Start: 2019-07-12 08:00:00<br>resolution: [7h, 12h]<br>length: 3</qt>")
        value = TimeSeriesVariableResolution(["2019-07-12T08:00", "2019-07-12T16:00"], [0.0, 100.0], False, False)
        item = self._add_value(value, "variable_resolution")
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertEqual(formatted, "<qt>Start: 2019-07-12T08:00:00<br>resolution: variable<br>length: 2</qt>")

    def test_broken_value_in_display_role(self):
        value = b"dubbidubbidu"
        item, error = self._db_map.add_parameter_value_item(
            entity_class_name="Object",
            entity_byname=("thing",),
            parameter_definition_name="x",
            alternative_name="Base",
            value=value,
            type="float",
        )
        self.assertIsNone(error)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.DisplayRole)
        self.assertEqual(formatted, "Error")

    def test_broken_value_in_edit_role(self):
        value = b"diibadaaba"
        item, error = self._db_map.add_parameter_value_item(
            entity_class_name="Object",
            entity_byname=("thing",),
            parameter_definition_name="x",
            alternative_name="Base",
            value=value,
            type="str",
        )
        self.assertIsNone(error)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.EditRole)
        self.assertEqual(formatted, join_value_and_type(b"diibadaaba", None))

    def test_broken_value_in_tool_tip_role(self):
        value = b"diibadaaba"
        item, error = self._db_map.add_parameter_value_item(
            entity_class_name="Object",
            entity_byname=("thing",),
            parameter_definition_name="x",
            alternative_name="Base",
            value=value,
            type="duration",
        )
        self.assertIsNone(error)
        formatted = self.db_mngr.get_value(self._db_map, item, Qt.ItemDataRole.ToolTipRole)
        self.assertTrue(formatted.startswith("<qt>Could not decode the value"))


class TestAddItems(TestCaseWithQApplication):
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
        db_map_data = {db_map: [{"name": "my_metadata", "value": "Metadata value."}]}
        self._db_mngr.add_items("metadata", db_map_data)
        metadata_id = db_map.metadata(name="my_metadata", value="Metadata value.")["id"]
        self.assertEqual(
            self._db_mngr.get_item(db_map, "metadata", metadata_id).resolve(),
            {"name": "my_metadata", "value": "Metadata value.", "id": None},
        )

    def test_add_object_metadata(self):
        db_map = self._db_mngr.get_db_map(self._db_url, None, create=True)
        with db_map:
            import_functions.import_entity_classes(db_map, ("my_class",))
            import_functions.import_entities(db_map, (("my_class", "my_object"),))
            import_functions.import_metadata(db_map, ('{"metaname": "metavalue"}',))
            db_map.commit_session("Add test data.")
            entity_id = db_map.entity(entity_class_name="my_class", name="my_object")["id"]
            metadata_id = db_map.metadata(name="metaname", value="metavalue")["id"]

        db_map_data = {db_map: [{"entity_id": entity_id, "metadata_id": metadata_id}]}
        self._db_mngr.add_items("entity_metadata", db_map_data)
        entity_metadata_id = db_map.entity_metadata(
            entity_class_name="my_class",
            entity_byname=("my_object",),
            metadata_name="metaname",
            metadata_value="metavalue",
        )["id"]
        self.assertEqual(
            self._db_mngr.get_item(db_map, "entity_metadata", entity_metadata_id)._asdict(),
            {"entity_id": entity_id, "metadata_id": metadata_id, "id": entity_metadata_id},
        )


class TestDoRestoreItems(TestCaseWithQApplication):
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

    def test_restore_entity_class(self):
        db_map = self._db_mngr.get_db_map(self._db_url, self._logger, create=True)
        entity_class, error = db_map.add_entity_class_item(name="Gadget")
        self.assertIsNone(error)
        class_item = self._db_mngr.get_item(db_map, "entity_class", entity_class["id"])
        self.assertIs(entity_class, class_item)
        self._db_mngr.remove_items({db_map: {"entity_class": {entity_class["id"]}}})
        self.assertFalse(class_item.is_valid())
        self._db_mngr.do_restore_items(db_map, "entity_class", {entity_class["id"]})
        self.assertTrue(class_item.is_valid())


class TestImportExportData(TestCaseWithQApplication):
    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        logger = MagicMock()
        self.editor = MagicMock()
        self._temp_dir = TemporaryDirectory()
        url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
        self._db_map = self._db_mngr.get_db_map(url, logger, create=True)
        self._db_mngr.name_registry.register(url, "test_import_export_data_db")

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
        self._db_mngr.import_data({self._db_map: mapped_data}, command_text="Import Excel data")
        self._db_map.commit_session("imported items")
        with self._db_map:
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
                {self._db_map: {"parameter_value_lists": [("list_1", "first value"), ("list_1", "second value")]}},
                "import value lists",
            )
            waiter.wait()
        value_lists = self._db_map.get_items("parameter_value_list")
        list_values = self._db_map.get_items("list_value")
        self.assertEqual(len(value_lists), 1)
        value_list = value_lists[0]
        self.assertEqual(value_list["name"], "list_1")
        self.assertEqual(
            [(from_database(x["value"], x["type"]), x["index"]) for x in list_values],
            [("first value", 0), ("second value", 1)],
        )


class TestDuplicateEntity(TestCaseWithQApplication):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.db_codename = cls.__name__ + "_db"

    def setUp(self):
        self._db_mngr = SpineDBManager(QSettings(), None)
        logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, self.db_codename)

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


class TestUpdateExpandedParameterValues(TestCaseWithQApplication):
    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "test_update_expanded_parameter_values_db")

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


class TestRemoveScenarioAlternative(TestCaseWithQApplication):
    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "test_remove_scenario_alternative_db")

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def _assert_success(self, result):
        item, error = result
        self.assertIsNone(error)
        return item

    def test_removing_scenario_alternative_and_committing(self):
        """Test that removing non-rank 1 scenario alternative works."""
        scenario = self._assert_success(self._db_map.add_scenario_item(name="scenario"))
        base = self._db_map.get_alternative_item(name="Base")
        next_level = self._assert_success(self._db_map.add_alternative_item(name="Next level"))
        _ = self._assert_success(
            self._db_map.add_scenario_alternative_item(scenario_id=scenario["id"], alternative_id=base["id"], rank=1)
        )
        scen_alt_2 = self._assert_success(
            self._db_map.add_scenario_alternative_item(
                scenario_id=scenario["id"], alternative_id=next_level["id"], rank=2
            )
        )
        self._db_mngr.commit_session("Added data.", self._db_map)
        db_map_scen_alt_data = {
            self._db_map: [{"alternative_id_list": [scen_alt_2["alternative_id"]], "id": scenario["id"]}]
        }
        db_map_typed_data_to_rm = {self._db_map: {"scenario": set()}}
        self._db_mngr.error_msg = MagicMock()
        self._db_mngr.set_scenario_alternatives(db_map_scen_alt_data)
        self._db_mngr.remove_items(db_map_typed_data_to_rm)
        self._db_mngr.commit_session("Remove scenario alternative", self._db_map)
        self._db_mngr.error_msg.emit.assert_not_called()


class TestFindCascadingItems(TestCaseWithQApplication):
    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "test_database")

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_find_cascading_entity_classes(self):
        self._db_mngr.add_items(
            "entity_class",
            {
                self._db_map: [
                    {"name": "O1"},
                    {"name": "O2"},
                    {"name": "O3"},
                    {"name": "O4"},
                    {"dimension_name_list": ["O1"]},
                    {"dimension_name_list": ["O2"]},
                    {"dimension_name_list": ["O3"]},
                    {"dimension_name_list": ["O1", "O2"]},
                    {"dimension_name_list": ["O1", "O3"]},
                    {"dimension_name_list": ["O2", "O3"]},
                    {"dimension_name_list": ["O1", "O2", "O3"]},
                ]
            },
        )
        o1_id = self._db_map.entity_class(name="O1")["id"]
        data = {
            db_map: [c["name"] for c in values]
            for db_map, values in self._db_mngr.find_cascading_entity_classes({self._db_map: [o1_id]}).items()
        }
        self.assertEqual(len(data), 1)
        self.assertCountEqual(data[self._db_map], ["O1__", "O1__O2", "O1__O3", "O1__O2__O3"])
        o4_id = self._db_map.entity_class(name="O4")["id"]
        self.assertEqual(self._db_mngr.find_cascading_entity_classes({self._db_map: [o4_id]}), {})
        o1__o2_id = self._db_map.entity_class(name="O1__O2")["id"]
        self.assertEqual(self._db_mngr.find_cascading_entity_classes({self._db_map: [o1__o2_id]}), {})
        self._db_mngr.remove_items({self._db_map: {"entity_class": {o1__o2_id}}})
        data = {
            db_map: [c["name"] for c in values]
            for db_map, values in self._db_mngr.find_cascading_entity_classes({self._db_map: [o1_id]}).items()
        }
        self.assertEqual(len(data), 1)
        self.assertCountEqual(data[self._db_map], ["O1__", "O1__O3", "O1__O2__O3"])

    def test_find_cascading_entities(self):
        self._db_mngr.add_items(
            "entity_class",
            {
                self._db_map: [
                    {"name": "O1"},
                    {"name": "O2"},
                    {"name": "O3"},
                    {"name": "O4"},
                    {"dimension_name_list": ["O1"]},
                    {"dimension_name_list": ["O2"]},
                    {"dimension_name_list": ["O3"]},
                    {"dimension_name_list": ["O1", "O2"]},
                    {"dimension_name_list": ["O1", "O3"]},
                    {"dimension_name_list": ["O2", "O3"]},
                    {"dimension_name_list": ["O1", "O2", "O3"]},
                ]
            },
        )
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "O1", "name": "o11"},
                    {"entity_class_name": "O1", "name": "o12"},
                    {"entity_class_name": "O1", "name": "o13"},
                    {"entity_class_name": "O2", "name": "o21"},
                    {"entity_class_name": "O3", "name": "o31"},
                    {"entity_class_name": "O1__O2", "element_name_list": ("o11", "o21")},
                    {"entity_class_name": "O1__O2", "element_name_list": ("o12", "o21")},
                    {"entity_class_name": "O2__O3", "element_name_list": ("o21", "o31")},
                ]
            },
        )
        o13_id = self._db_map.entity(entity_class_name="O1", name="o13")["id"]
        self.assertEqual(self._db_mngr.find_cascading_entities({self._db_map: [o13_id]}), {})
        o11_id = self._db_map.entity(entity_class_name="O1", name="o11")["id"]
        data = {
            db_map: [c["name"] for c in values]
            for db_map, values in self._db_mngr.find_cascading_entities({self._db_map: [o11_id]}).items()
        }
        self.assertEqual(len(data), 1)
        self.assertEqual(data[self._db_map], ["o11__o21"])
        o11__o21_id = self._db_map.entity(entity_class_name="O1__O2", entity_byname=("o11", "o21"))["id"]
        self._db_mngr.remove_items({self._db_map: {"entity": {o11__o21_id}}})
        self.assertEqual(self._db_mngr.find_cascading_entities({self._db_map: [o11_id]}), {})

    def test_find_cascading_parameter_definitions(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "O1"}, {"name": "O2"}, {"name": "O3"}]})
        self._db_mngr.add_items(
            "parameter_definition",
            {self._db_map: [{"entity_class_name": "O1", "name": "p11"}, {"entity_class_name": "O2", "name": "p21"}]},
        )
        o3_id = self._db_map.entity_class(name="O3")["id"]
        self.assertEqual(self._db_mngr.find_cascading_parameter_definitions({self._db_map: [o3_id]}), {})
        o1_id = self._db_map.entity_class(name="O1")["id"]
        data = {
            db_map: [d["name"] for d in definitions]
            for db_map, definitions in self._db_mngr.find_cascading_parameter_definitions(
                {self._db_map: [o1_id]}
            ).items()
        }
        self.assertEqual(len(data), 1)
        self.assertCountEqual(data[self._db_map], ["p11"])
        p11_id = self._db_map.parameter_definition(entity_class_name="O1", name="p11")["id"]
        self._db_mngr.remove_items({self._db_map: {"parameter_definition": [p11_id]}})
        self.assertEqual(self._db_mngr.find_cascading_parameter_definitions({self._db_map: [o1_id]}), {})

    def test_find_cascading_parameter_values_by_entity(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "O1"}, {"name": "O2"}, {"name": "O3"}]})
        self._db_mngr.add_items(
            "parameter_definition",
            {
                self._db_map: [
                    {"entity_class_name": "O1", "name": "p11"},
                    {"entity_class_name": "O2", "name": "p21"},
                    {"entity_class_name": "O3", "name": "p31"},
                ]
            },
        )
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "O1", "name": "o11"},
                    {"entity_class_name": "O1", "name": "o12"},
                    {"entity_class_name": "O2", "name": "o21"},
                    {"entity_class_name": "O3", "name": "o31"},
                ]
            },
        )
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "entity_class_name": "O1",
                        "entity_byname": ("o11",),
                        "parameter_definition_name": "p11",
                        "alternative_name": "Base",
                        "parsed_value": 2.3,
                    },
                    {
                        "entity_class_name": "O1",
                        "entity_byname": ("o12",),
                        "parameter_definition_name": "p11",
                        "alternative_name": "Base",
                        "parsed_value": -2.3,
                    },
                    {
                        "entity_class_name": "O2",
                        "entity_byname": ("o21",),
                        "parameter_definition_name": "p21",
                        "alternative_name": "Base",
                        "parsed_value": "yes",
                    },
                ]
            },
        )
        o31_id = self._db_map.entity(entity_class_name="O3", name="o31")["id"]
        self.assertEqual(self._db_mngr.find_cascading_parameter_values_by_entity({self._db_map: [o31_id]}), {})
        o11_id = self._db_map.entity(entity_class_name="O1", name="o11")["id"]
        data = {
            db_map: [
                (
                    value["entity_class_name"],
                    value["entity_byname"],
                    value["parameter_definition_name"],
                    value["alternative_name"],
                    value["parsed_value"],
                )
                for value in values
            ]
            for db_map, values in self._db_mngr.find_cascading_parameter_values_by_entity(
                {self._db_map: [o11_id]}
            ).items()
        }
        self.assertEqual(data, {self._db_map: [("O1", ("o11",), "p11", "Base", 2.3)]})
        value_id = self._db_map.parameter_value(
            entity_class_name="O1", entity_byname=("o11",), parameter_definition_name="p11", alternative_name="Base"
        )["id"]
        self._db_mngr.remove_items({self._db_map: {"parameter_value": [value_id]}})
        self.assertEqual(self._db_mngr.find_cascading_parameter_values_by_entity({self._db_map: [o11_id]}), {})

    def test_find_cascading_scenario_alternatives_by_scenario(self):
        self._db_mngr.add_items("scenario", {self._db_map: [{"name": "S1"}, {"name": "S2"}]})
        s1_id = self._db_map.scenario(name="S1")["id"]
        self._db_mngr.add_items("alternative", {self._db_map: [{"name": "a1"}]})
        a1_id = self._db_map.alternative(name="a1")["id"]
        self._db_mngr.set_scenario_alternatives({self._db_map: [{"id": s1_id, "alternative_id_list": [a1_id]}]})
        s2_id = self._db_map.scenario(name="S2")["id"]
        self.assertEqual(self._db_mngr.find_cascading_scenario_alternatives_by_scenario({self._db_map: [s2_id]}), {})
        data = {
            db_map: [(sa["scenario_name"], sa["alternative_name"]) for sa in sas]
            for db_map, sas in self._db_mngr.find_cascading_scenario_alternatives_by_scenario(
                {self._db_map: [s1_id]}
            ).items()
        }
        self.assertEqual(data, {self._db_map: [("S1", "a1")]})
        sa_id = self._db_map.scenario_alternative(scenario_name="S1", alternative_name="a1", rank=0)["id"]
        self._db_mngr.remove_items({self._db_map: {"scenario_alternative": {sa_id}}})
        self.assertEqual(self._db_mngr.find_cascading_scenario_alternatives_by_scenario({self._db_map: [s1_id]}), {})

    def test_find_groups_by_entity(self):
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "O1"}]})
        self._db_mngr.add_items(
            "entity",
            {
                self._db_map: [
                    {"entity_class_name": "O1", "name": "o1"},
                    {"entity_class_name": "O1", "name": "o2"},
                    {"entity_class_name": "O1", "name": "o3"},
                ]
            },
        )
        self._db_mngr.add_items(
            "entity_group", {self._db_map: [{"entity_class_name": "O1", "group_name": "o1", "member_name": "o2"}]}
        )
        o3_id = self._db_map.entity(entity_class_name="O1", name="o3")["id"]
        self.assertEqual(self._db_mngr.find_groups_by_entity({self._db_map: [o3_id]}), {})
        o1_id = self._db_map.entity(entity_class_name="O1", name="o1")["id"]
        data = {
            db_map: [(g["group_name"], g["member_name"]) for g in groups]
            for db_map, groups in self._db_mngr.find_groups_by_entity({self._db_map: [o1_id]}).items()
        }
        self.assertEqual(data, {self._db_map: [("o1", "o2")]})
        group_id = self._db_map.entity_group(group_name="o1", member_name="o2", entity_class_name="O1")["id"]
        self._db_mngr.remove_items({self._db_map: {"entity_group": {group_id}}})
        self.assertEqual(self._db_mngr.find_groups_by_entity({self._db_map: [o1_id]}), {})


class TestCommitSession(TestCaseWithQApplication):
    def setUp(self):
        mock_settings = MagicMock()
        mock_settings.value.side_effect = lambda *args, **kwargs: 0
        self._db_mngr = SpineDBManager(mock_settings, None)
        self._logger = MagicMock()
        self._db_map = self._db_mngr.get_db_map("sqlite://", self._logger, create=True)
        self._db_mngr.name_registry.register(self._db_map.sa_url, "test_database")

    def tearDown(self):
        self._db_mngr.close_all_sessions()
        while not self._db_map.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()

    def test_nothing_to_commit_is_not_error(self):
        error_listener = MagicMock()
        self._db_mngr.register_listener(error_listener, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "O1"}]})
        class_id = self._db_map.entity_class(name="O1")["id"]
        self._db_mngr.remove_items({self._db_map: {"entity_class": [class_id]}})
        self.assertEqual(self._db_mngr.commit_session("Nothing to commit.", self._db_map), [])
        error_listener.receive_error_msg.assert_not_called()


if __name__ == "__main__":
    unittest.main()
