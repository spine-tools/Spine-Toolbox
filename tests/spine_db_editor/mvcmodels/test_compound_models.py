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

"""Unit tests for the models in ``compound_models`` module."""
import gc
import pathlib
from tempfile import TemporaryDirectory
from unittest import mock
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication
import pytest
from spinedb_api import Array, Asterisk, Map, TimeSeriesVariableResolution
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.parameter_type_validation import ValidationKey
from spinetoolbox.spine_db_editor.mvcmodels.colors import FIXED_FIELD_COLOR
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundEntityAlternativeModel,
    CompoundEntityModel,
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from tests.mock_helpers import assert_table_model_data, assert_table_model_data_pytest, fetch_model
from ..helpers import TestBase


class TestCompoundParameterDefinitionModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        expected_header = [
            "class",
            "parameter name",
            "valid types",
            "value list",
            "default value",
            "description",
            "group",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)
        model.tear_down()

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "oc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["oc", "p", None, None, "None", None, None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_data_for_single_parameter_definition_in_multidimensional_entity_class(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "rc", "dimension_name_list": ["oc"]}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "rc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["rc", "p", None, None, "None", None, None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_model_updates_when_entity_class_is_removed(self):
        self._db_map.add_entity_class(name="oc1")
        self._db_map.add_parameter_definition(entity_class_name="oc1", name="x")
        entity_class_2 = self._db_map.add_entity_class(name="oc2")
        self._db_map.add_parameter_definition(entity_class_name="oc2", name="x")
        self._db_map.add_entity_class(name="rc", dimension_name_list=("oc1", "oc2"))
        self._db_map.add_parameter_definition(entity_class_name="rc", name="x")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        self.assertEqual(model.rowCount(), 3)
        model.set_entity_selection_for_filtering({self._db_map: {entity_class_2["id"]: Asterisk}})
        while model.rowCount() == 3:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(), 2)
        self._db_mngr.remove_items({self._db_map: {"entity_class": [entity_class_2["id"]]}})
        while model.rowCount() == 2:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(), 0)
        model.tear_down()

    def test_index_name_returns_sane_label(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="x", entity_class_name="Object", parsed_value=Array([2.3]))
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterDefinitionModel_db - Object - x")
        model.tear_down()

    def test_updating_definition_triggers_value_type_validation(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
            weight = self._db_map.add_parameter_definition(
                entity_class_name="Widget", name="weight", parsed_value="a lot"
            )
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            fetch_model(model)
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), weight["id"].private_id)], [True]),
            )
        expected = [["Widget", "weight", None, None, "a lot", None, None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            model.setData(model.index(0, 2), ("float",), Qt.ItemDataRole.EditRole)
            expected = [["Widget", "weight", "float", None, "a lot", None, None, self.db_codename]]
            assert_table_model_data(model, expected, self)
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), weight["id"].private_id)], [False]),
            )
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()
        model.tear_down()

    def test_restore_db_maps(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p1", "entity_class_name": "oc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["oc", "p1", None, None, "None", None, None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        with TemporaryDirectory() as tmp_dir:
            url = "sqlite:///" + str(pathlib.Path(tmp_dir, "other_db.sqlite"))
            logger = mock.MagicMock()
            db_map = self._db_mngr.get_db_map(url, logger, create=True)
            with db_map:
                db_map.add_entity_class(name="Object")
                db_map.add_parameter_definition(entity_class_name="Object", name="X", description="X marks the spot.")
            model.init_model()
            model.reset_db_maps([db_map])
            self.assertEqual(model.rowCount(), 0)
            self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p2", "entity_class_name": "oc"}]})
            fetch_model(model)
            expected = [["Object", "X", None, None, "None", "X marks the spot.", None, "other_db"]]
            assert_table_model_data(model, expected, self)
            self._db_mngr.close_session(url)
            gc.collect()
        model.tear_down()

    def test_signals_when_non_committed_data_is_added(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Gadget")
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="X")
            self._db_map.commit_session("Mark items as committed.")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        with (
            mock.patch.object(model, "non_committed_items_about_to_be_added") as begin_signal,
            mock.patch.object(model, "non_committed_items_added") as end_signal,
        ):
            fetch_model(model)
            begin_signal.emit.assert_not_called()
            end_signal.emit.assert_not_called()
        expected = [["Gadget", "X", None, None, "None", None, None, self.db_codename]]
        assert_table_model_data_pytest(model, expected)
        with (
            mock.patch.object(model, "non_committed_items_about_to_be_added") as begin_signal,
            mock.patch.object(model, "non_committed_items_added") as end_signal,
        ):
            self._db_mngr.add_items(
                "parameter_definition", {self._db_map: [{"entity_class_name": "Gadget", "name": "Y"}]}
            )
            while model.rowCount() == 1:
                QApplication.processEvents()
            begin_signal.emit.assert_called_once_with()
            end_signal.emit.assert_called_once_with()
        expected = [
            ["Gadget", "X", None, None, "None", None, None, self.db_codename],
            ["Gadget", "Y", None, None, "None", None, None, self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_set_auto_filter_in_default_value_column_with_empty_data_and_null_values(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Gadget")
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="X", parsed_value=None)
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="Y")
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="Z", parsed_value=None)
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        with signal_waiter(model.layoutChanged, timeout=3.0) as waiter:
            model.set_auto_filter("default_value", {"None"})
            waiter.wait()
        expected = [
            ["Gadget", "X", None, None, "None", None, None, self.db_codename],
            ["Gadget", "Y", None, None, "None", None, None, self.db_codename],
            ["Gadget", "Z", None, None, "None", None, None, self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_update_definitions_group(self):
        with self._db_map:
            self._db_map.add_parameter_group(name="Group B", color="beefaf", priority=23)
            self._db_map.add_entity_class(name="Gadget")
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="X")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            ["Gadget", "X", None, None, "None", None, None, self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        with signal_waiter(model.dataChanged) as waiter:
            model.batch_set_data([model.index(0, 6)], ["Group B"])
            waiter.wait()
            self.assertEqual(waiter.args, (model.index(0, 6), model.index(0, 6), []))
        expected = [
            ["Gadget", "X", None, None, "None", None, "Group B", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()


class TestCompoundParameterValueModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        expected_header = [
            "group",
            "class",
            "entity byname",
            "parameter name",
            "alternative",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)
        model.tear_down()

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "oc"}]})
        self._db_mngr.add_items("entity", {self._db_map: [{"name": "o", "entity_class_name": "oc"}]})
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "parameter_definition_name": "p",
                        "parsed_value": 23.0,
                        "entity_byname": ("o",),
                        "entity_class_name": "oc",
                        "alternative_name": "Base",
                    }
                ]
            },
        )
        while model.rowCount() == 0:
            QApplication.processEvents()
        expected = [[None, "oc", "o", "p", "Base", "23.0", self.db_codename]]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_data_for_single_parameter_in_multidimensional_entity(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("entity", {self._db_map: [{"name": "o", "entity_class_name": "oc"}]})
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "rc", "dimension_name_list": ["oc"]}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "rc"}]})
        self._db_mngr.add_items(
            "entity", {self._db_map: [{"name": "r", "entity_class_name": "rc", "element_name_list": ["o"]}]}
        )
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "parameter_definition_name": "p",
                        "parsed_value": 23.0,
                        "entity_byname": ("o",),
                        "entity_class_name": "rc",
                        "alternative_name": "Base",
                    }
                ]
            },
        )
        while model.rowCount() == 0:
            QApplication.processEvents()
        expected = [[None, "rc", "o", "p", "Base", "23.0", self.db_codename]]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_index_name_returns_sane_label(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="x", entity_class_name="Object")
        self._db_map.add_entity(name="mysterious cube", entity_class_name="Object")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mysterious cube",),
            parameter_definition_name="x",
            alternative_name="Base",
            parsed_value=Array([2.3]),
        )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(
            model.index_name(index), "TestCompoundParameterValueModel_db - Object - mysterious cube - x - Base"
        )
        model.tear_down()

    def test_removing_first_of_two_rows(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            parsed_value=-2.3,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        value_not_in_base.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = []
        assert_table_model_data(model, expected, self)
        value_not_in_base.restore()
        value_in_base.restore()
        while model.rowCount() == 0:
            QApplication.processEvents()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_removing_second_of_two_uncommitted_rows(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            parsed_value=-2.3,
        )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_not_in_base.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_restoring_removed_item_keeps_empty_row_last(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            parsed_value=-2.3,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_not_in_base.remove()
        while model.rowCount() == 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.sub_models, [])
        model.tear_down()

    def test_removing_value_from_another_alternative_that_is_selected_for_filtering_works(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        not_base_alternative = self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            parsed_value=-2.3,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_alternative_selection_for_filtering({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_restoring_removed_value_from_another_alternative_that_is_selected_for_filtering_works(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        not_base_alternative = self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            parsed_value=-2.3,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_alternative_selection_for_filtering({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            [None, "Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        assert_table_model_data(model, expected, self)
        value_in_base.restore()
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_remove_every_other_row(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="ctrl")
        self._db_map.add_alternative(name="alt")
        self._db_map.add_alternative(name="del")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="ctrl",
            parsed_value=-2.3,
        )
        alt_value = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="alt",
            parsed_value=23.0,
        )
        del_value = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="del",
            parsed_value=-23.0,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "alt", "23.0", self.db_codename],
            [None, "Object", "curious sphere", "X", "ctrl", "-2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "del", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        self._db_map.remove_items("parameter_value", alt_value["id"], del_value["id"])
        while model.rowCount() == 4:
            QApplication.processEvents()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "ctrl", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_remove_item_from_another_entity_class_than_selected(self):
        object_class = self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        self._db_map.add_entity_class(name="Immaterial")
        self._db_map.add_parameter_definition(name="Y", entity_class_name="Immaterial")
        self._db_map.add_parameter_definition(name="Z", entity_class_name="Immaterial")
        self._db_map.add_entity(name="ghost", entity_class_name="Immaterial")
        self._db_map.add_parameter_value(
            entity_class_name="Immaterial",
            entity_byname=("ghost",),
            parameter_definition_name="Y",
            alternative_name="Base",
            parsed_value=-2.3,
        )
        z_value = self._db_map.add_parameter_value(
            entity_class_name="Immaterial",
            entity_byname=("ghost",),
            parameter_definition_name="Z",
            alternative_name="Base",
            parsed_value=23.0,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Immaterial", "ghost", "Y", "Base", "-2.3", self.db_codename],
            [None, "Immaterial", "ghost", "Z", "Base", "23.0", self.db_codename],
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_entity_selection_for_filtering({self._db_map: {object_class["id"]: Asterisk}})
        model.refresh()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        z_value.remove()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_remove_visible_and_hidden_items(self):
        alternative = self._db_map.add_alternative(name="alt")
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_entity(name="mystic cube", entity_class_name="Object")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        spherical_value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        spherical_value_in_alt = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="alt",
            parsed_value=-2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=23.0,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="alt",
            parsed_value=-23.0,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            [None, "Object", "mystic cube", "X", "Base", "23.0", self.db_codename],
            [None, "Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_alternative_selection_for_filtering({self._db_map: {alternative["id"]}})
        model.refresh()
        expected = [
            [None, "Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            [None, "Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        spherical_value_in_base.remove()
        spherical_value_in_alt.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            [None, "Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_updates_when_not_all_entities_are_visible(self):
        self._db_map.add_alternative(name="alt")
        object_class = self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_entity(name="mystic cube", entity_class_name="Object")
        curious_sphere = self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        spherical_value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="alt",
            parsed_value=-2.3,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="Base",
            parsed_value=23.0,
        )
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="alt",
            parsed_value=-23.0,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            [None, "Object", "mystic cube", "X", "Base", "23.0", self.db_codename],
            [None, "Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_entity_selection_for_filtering({self._db_map: {object_class["id"]: {curious_sphere["id"]}}})
        model.refresh()
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            [None, "Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        with signal_waiter(model.dataChanged, timeout=1.0) as waiter:
            spherical_value_in_base.update(parsed_value=55.5)
            waiter.wait()
        self.assertEqual(
            waiter.args, (model.index(0, 0), model.index(0, model.columnCount() - 1), [Qt.ItemDataRole.DisplayRole])
        )
        expected = [
            [None, "Object", "curious sphere", "X", "Base", "55.5", self.db_codename],
            [None, "Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_updating_definition_triggers_value_type_validation(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
            self._db_map.add_entity(entity_class_name="Widget", name="gadget")
            weight = self._db_map.add_parameter_definition(entity_class_name="Widget", name="weight")
            weight_value = self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="weight",
                alternative_name="Base",
                parsed_value="a lot",
            )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            fetch_model(model)
            expected = [[None, "Widget", "gadget", "weight", "Base", "a lot", self.db_codename]]
            assert_table_model_data(model, expected, self)
            waiter.wait()
            args_as_dict = dict(zip(*waiter.args))
            self.assertEqual(
                args_as_dict,
                {
                    ValidationKey("parameter_value", id(self._db_map), weight_value["id"].private_id): True,
                },
            )
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            self._db_mngr.update_items(
                "parameter_definition", {self._db_map: [{"id": weight["id"], "parameter_type_list": ("float",)}]}
            )
            waiter.wait()
            args_as_dict = dict(zip(*waiter.args))
            self.assertEqual(
                args_as_dict,
                {
                    ValidationKey("parameter_value", id(self._db_map), weight_value["id"].private_id): False,
                },
            )
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()
        model.tear_down()

    def test_update_parameter_value(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
            self._db_map.add_entity(entity_class_name="Widget", name="gadget")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="weight")
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="weight",
                alternative_name="Base",
                parsed_value="a lot",
            )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            [None, "Widget", "gadget", "weight", "Base", "a lot", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        index = model.index(0, 5)
        self.assertTrue(model.batch_set_data([index], ["too much"]))
        expected = [
            [None, "Widget", "gadget", "weight", "Base", "too much", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_set_auto_filter_in_value_column(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
            self._db_map.add_entity(entity_class_name="Widget", name="gadget")
            self._db_map.add_entity(entity_class_name="Widget", name="object")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="number")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="string")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="map")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="time_series")
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="number",
                alternative_name="Base",
                parsed_value=2.3,
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="string",
                alternative_name="Base",
                parsed_value="a priceless value",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="map",
                alternative_name="Base",
                parsed_value=Map(["a", "b"], [3.2, 5.5]),
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("object",),
                parameter_definition_name="map",
                alternative_name="Base",
                parsed_value=Map(["c", "d"], [-3.2, -5.5]),
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="time_series",
                alternative_name="Base",
                parsed_value=TimeSeriesVariableResolution(
                    ["2025-12-06T16:00", "2025-12-06T18:30"], [-2.3, -3.2], ignore_year=False, repeat=False
                ),
            )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        with signal_waiter(model.layoutChanged, timeout=3.0) as waiter:
            model.set_auto_filter("value", {"2.3"})
            waiter.wait()
        expected = [
            [None, "Widget", "gadget", "number", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        with signal_waiter(model.layoutChanged, timeout=3.0) as waiter:
            model.set_auto_filter("value", {"Map"})
            waiter.wait()
        expected = [
            [None, "Widget", "gadget", "map", "Base", "Map", self.db_codename],
            [None, "Widget", "object", "map", "Base", "Map", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.tear_down()

    def test_adding_metadata_emits_data_changed(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "oc"}]})
        self._db_mngr.add_items("entity", {self._db_map: [{"name": "o", "entity_class_name": "oc"}]})
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "parameter_definition_name": "p",
                        "parsed_value": 23.0,
                        "entity_byname": ("o",),
                        "entity_class_name": "oc",
                        "alternative_name": "Base",
                    }
                ]
            },
        )
        self._db_mngr.add_items("metadata", {self._db_map: [{"name": "author", "value": "A. Uthor"}]})
        while model.rowCount() == 0:
            QApplication.processEvents()
        with signal_waiter(model.dataChanged) as waiter:
            self._db_mngr.add_items(
                "parameter_value_metadata",
                {
                    self._db_map: [
                        {
                            "entity_class_name": "oc",
                            "entity_byname": ("o",),
                            "parameter_definition_name": "p",
                            "alternative_name": "Base",
                            "metadata_name": "author",
                            "metadata_value": "A. Uthor",
                        }
                    ]
                },
            )
            waiter.wait()
            self.assertEqual(waiter.args, (model.index(0, 3), model.index(0, 3), [Qt.ItemDataRole.DisplayRole]))
        model.tear_down()

    def test_group_data(self):
        with self._db_map:
            self._db_map.add_parameter_group(name="Group A", color="102030", priority=3)
            self._db_map.add_parameter_group(name="Group B", color="090807", priority=2)
            self._db_map.add_entity_class(name="Widget")
            self._db_map.add_entity(entity_class_name="Widget", name="gadget")
            self._db_map.add_entity(entity_class_name="Widget", name="object")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="X", parameter_group_name="Group A")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="Y", parameter_group_name="Group B")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="N", parameter_group_name="Group A")
            self._db_map.add_parameter_definition(entity_class_name="Widget", name="P", parameter_group_name="Group B")
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="X",
                alternative_name="Base",
                parsed_value="too low",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="Y",
                alternative_name="Base",
                parsed_value="too high",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="N",
                alternative_name="Base",
                parsed_value="too few",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("gadget",),
                parameter_definition_name="P",
                alternative_name="Base",
                parsed_value="too many",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("object",),
                parameter_definition_name="X",
                alternative_name="Base",
                parsed_value="too much",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("object",),
                parameter_definition_name="Y",
                alternative_name="Base",
                parsed_value="not enough",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("object",),
                parameter_definition_name="N",
                alternative_name="Base",
                parsed_value="too large",
            )
            self._db_map.add_parameter_value(
                entity_class_name="Widget",
                entity_byname=("object",),
                parameter_definition_name="P",
                alternative_name="Base",
                parsed_value="too small",
            )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        fetch_model(model)
        expected = [
            ["Group B", "Widget", "gadget", "P", "Base", "too many", self.db_codename],
            ["Group B", "Widget", "gadget", "Y", "Base", "too high", self.db_codename],
            ["Group A", "Widget", "gadget", "N", "Base", "too few", self.db_codename],
            ["Group A", "Widget", "gadget", "X", "Base", "too low", self.db_codename],
            ["Group B", "Widget", "object", "P", "Base", "too small", self.db_codename],
            ["Group B", "Widget", "object", "Y", "Base", "not enough", self.db_codename],
            ["Group A", "Widget", "object", "N", "Base", "too large", self.db_codename],
            ["Group A", "Widget", "object", "X", "Base", "too much", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        expected = [
            [QColor("#090807"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#090807"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#102030"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#102030"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#090807"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#090807"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#102030"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
            [QColor("#102030"), FIXED_FIELD_COLOR, None, None, None, None, FIXED_FIELD_COLOR],
        ]
        assert_table_model_data(model, expected, self, Qt.ItemDataRole.BackgroundRole)
        model.tear_down()


class TestCompoundEntityAlternativeModel:
    def test_horizontal_header(self, db_mngr, db_map, parent_object):
        model = CompoundEntityAlternativeModel(parent_object, db_mngr, db_map)
        expected_header = [
            "class",
            "entity byname",
            "alternative",
            "active",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        assert header == expected_header
        model.tear_down()

    def test_data_for_single_entity_alternative(self, db_mngr, db_map, db_name, parent_object):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget")
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("gadget",), alternative_name="Base", active=True
            )
        model = CompoundEntityAlternativeModel(parent_object, db_mngr, db_map)
        fetch_model(model)
        expected = [["Widget", "gadget", "Base", True, db_name]]
        assert_table_model_data_pytest(model, expected)
        model.tear_down()

    def test_updating_byname_to_non_existing_entity_fails(self, db_editor, db_mngr, db_map, db_name, parent_object):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget")
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("gadget",), alternative_name="Base", active=True
            )
        model = CompoundEntityAlternativeModel(parent_object, db_mngr, db_map)
        fetch_model(model)
        expected = [["Widget", "gadget", "Base", True, db_name]]
        assert_table_model_data_pytest(model, expected)
        index = model.index(0, 1)
        db_editor.msg_error.disconnect(db_editor.err_msg.showMessage)
        with signal_waiter(db_editor.msg_error, timeout=1.0) as waiter:
            assert model.batch_set_data([index], [("non-existent",)])
            waiter.wait()
            assert waiter.args == (
                "<ul><li>From TestCompoundEntityAlternativeModel_db: <ul><li>no entity matching {'entity_class_name': 'Widget', 'entity_byname': ('non-existent',)}</li></ul></li></ul>",
            )
        model.tear_down()

    def test_auto_filter_need_not_be_updated(self, db_mngr, db_map, db_name, parent_object):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("clock",), alternative_name="Base", active=False
            )
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("calendar",), alternative_name="Base", active=True
            )
        model = CompoundEntityAlternativeModel(parent_object, db_mngr, db_map)
        fetch_model(model)
        with mock.patch.object(model, "column_filter_changed") as mock_signal:
            model.set_auto_filter("active", None)
            mock_signal.assert_not_called()
        with signal_waiter(model.layoutChanged) as waiter:
            model.set_auto_filter("active", {True})
            waiter.wait()
        expected = [
            ["Widget", "calendar", "Base", True, db_name],
        ]
        assert_table_model_data_pytest(model, expected)
        with mock.patch.object(model, "column_filter_changed") as mock_signal:
            model.set_auto_filter("active", {True})
            mock_signal.assert_not_called()
        model.tear_down()


@pytest.fixture()
def compound_entity_model(db_mngr, db_map, parent_object):
    model = CompoundEntityModel(parent_object, db_mngr, db_map)
    yield model
    model.tear_down()


class TestCompoundEntityModel:
    def test_horizontal_header(self, compound_entity_model):
        expected_header = [
            "class",
            "name",
            "byname",
            "description",
            "latitude",
            "longitude",
            "altitude",
            "shape name",
            "shape blob",
            "database",
        ]
        header = [compound_entity_model.headerData(i) for i in range(compound_entity_model.columnCount())]
        assert header == expected_header

    def test_data_for_single_entity_alternative(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget", description="Gadget is a widget.")
        fetch_model(compound_entity_model)
        expected = [["Widget", "gadget", "gadget", "Gadget is a widget.", None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_filtering_by_entity(self, compound_entity_model, db_map, db_name):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            db_map.add_entity(entity_class_name="Gadget", name="flashlight")
            microphone = db_map.add_entity(entity_class_name="Gadget", name="microphone")
        fetch_model(compound_entity_model)
        expected = [
            ["Gadget", "flashlight", "flashlight", None, None, None, None, None, None, db_name],
            ["Gadget", "microphone", "microphone", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)
        compound_entity_model.set_entity_selection_for_filtering({db_map: {gadget["id"]: {microphone["id"]}}})
        compound_entity_model.refresh()
        expected = [
            ["Gadget", "microphone", "microphone", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_filtering_by_scenario(self, compound_entity_model, db_map, db_name):
        with db_map:
            scenario = db_map.add_scenario(name="Scenario")
            db_map.add_scenario_alternative(scenario_name="Scenario", alternative_name="Base", rank=0)
            db_map.add_entity_class(name="Visible", active_by_default=True)
            db_map.add_entity(name="indeterminate_visible", entity_class_name="Visible")
            db_map.add_entity(name="active_visible", entity_class_name="Visible")
            db_map.add_entity_alternative(
                entity_class_name="Visible", entity_byname=("active_visible",), alternative_name="Base", active=True
            )
            db_map.add_entity(name="inactive_visible", entity_class_name="Visible")
            db_map.add_entity_alternative(
                entity_class_name="Visible", entity_byname=("inactive_visible",), alternative_name="Base", active=False
            )
            db_map.add_entity_class(name="Invisible", active_by_default=False)
            db_map.add_entity(name="indeterminate_invisible", entity_class_name="Invisible")
            db_map.add_entity(name="active_invisible", entity_class_name="Invisible")
            db_map.add_entity_alternative(
                entity_class_name="Invisible", entity_byname=("active_invisible",), alternative_name="Base", active=True
            )
            db_map.add_entity(name="inactive_invisible", entity_class_name="Invisible")
            db_map.add_entity_alternative(
                entity_class_name="Invisible",
                entity_byname=("inactive_invisible",),
                alternative_name="Base",
                active=False,
            )
        fetch_model(compound_entity_model)
        expected = [
            ["Visible", "active_visible", "active_visible", None, None, None, None, None, None, db_name],
            ["Visible", "inactive_visible", "inactive_visible", None, None, None, None, None, None, db_name],
            ["Visible", "indeterminate_visible", "indeterminate_visible", None, None, None, None, None, None, db_name],
            ["Invisible", "active_invisible", "active_invisible", None, None, None, None, None, None, db_name],
            ["Invisible", "inactive_invisible", "inactive_invisible", None, None, None, None, None, None, db_name],
            [
                "Invisible",
                "indeterminate_invisible",
                "indeterminate_invisible",
                None,
                None,
                None,
                None,
                None,
                None,
                db_name,
            ],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)
        compound_entity_model.set_scenario_selection_for_filtering({db_map: {scenario["id"]}})
        compound_entity_model.refresh()
        expected = [
            ["Visible", "active_visible", "active_visible", None, None, None, None, None, None, db_name],
            ["Visible", "indeterminate_visible", "indeterminate_visible", None, None, None, None, None, None, db_name],
            ["Invisible", "active_invisible", "active_invisible", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)
        compound_entity_model.set_scenario_selection_for_filtering({})
        compound_entity_model.refresh()
        assert compound_entity_model.rowCount() == 0

    def test_update_entity_with_location_and_shape_information(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            gadget = db_map.add_entity(entity_class_name="Widget", name="gadget")
        fetch_model(compound_entity_model)
        expected = [["Widget", "gadget", "gadget", None, None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(compound_entity_model, expected)
        gadget.update(lat=1.1, lon=2.2, alt=3.3, shape_name="region", shape_blob="{}")
        expected = [["Widget", "gadget", "gadget", None, "1.1", "2.2", "3.3", "region", "<geojson>", db_name]]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_update_entity_byname(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity_class(dimension_name_list=["Widget"])
            db_map.add_entity(entity_class_name="Widget__", entity_byname=("calendar",))
        fetch_model(compound_entity_model)
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget__", "calendar__", "calendar", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)
        index = compound_entity_model.index(2, 2)
        assert compound_entity_model.batch_set_data([index], [("clock",)])
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget__", "calendar__", "clock", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_set_auto_filter(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity_class(dimension_name_list=["Widget"])
            db_map.add_entity(entity_class_name="Widget__", entity_byname=("calendar",))
        fetch_model(compound_entity_model)
        with signal_waiter(compound_entity_model.layoutChanged) as waiter:
            compound_entity_model.set_auto_filter("entity_class_name", {"Widget__"})
            waiter.wait()
        expected = [["Widget__", "calendar__", "calendar", None, None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_set_auto_filter_to_all_selected(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(
                entity_class_name="Widget",
                name="clock",
            )
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity_class(dimension_name_list=["Widget"])
            db_map.add_entity(entity_class_name="Widget__", entity_byname=("calendar",))
        fetch_model(compound_entity_model)
        with signal_waiter(compound_entity_model.layoutChanged) as waiter:
            compound_entity_model.set_auto_filter("entity_class_name", {"Widget__"})
            waiter.wait()
        expected = [["Widget__", "calendar__", "calendar", None, None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(compound_entity_model, expected)
        with signal_waiter(compound_entity_model.layoutChanged) as waiter:
            compound_entity_model.set_auto_filter("entity_class_name", None)
            waiter.wait()
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget__", "calendar__", "calendar", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_set_auto_filter_in_shape_blob_column(self, compound_entity_model, db_map, db_name):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock", shape_blob='{"a": 1}')
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity(entity_class_name="Widget", name="tablet", shape_blob='{"b": []}')
        fetch_model(compound_entity_model)
        with signal_waiter(compound_entity_model.layoutChanged) as waiter:
            compound_entity_model.set_auto_filter("shape_blob", {"<geojson>"})
            waiter.wait()
        expected = [
            ["Widget", "clock", "clock", None, None, None, None, None, "<geojson>", db_name],
            ["Widget", "tablet", "tablet", None, None, None, None, None, "<geojson>", db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)

    def test_adding_entity_metadata_item_emits_data_changed_for_name_column(
        self, compound_entity_model, db_mngr, db_map, db_name, monkeypatch
    ):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_metadata(name="author", value="A. Uthor")
        fetch_model(compound_entity_model)
        with signal_waiter(compound_entity_model.dataChanged) as waiter:
            db_mngr.add_items(
                "entity_metadata",
                {
                    db_map: [
                        {
                            "entity_class_name": "Widget",
                            "entity_byname": ("clock",),
                            "metadata_name": "author",
                            "metadata_value": "A. Uthor",
                        }
                    ]
                },
            )
            waiter.wait()
            assert waiter.args == (
                compound_entity_model.index(0, 1),
                compound_entity_model.index(0, 1),
                [Qt.ItemDataRole.DisplayRole],
            )

    def test_adding_multiple_entity_metadata_items_emits_data_changed_for_name_column(
        self, compound_entity_model, db_mngr, db_map, db_name, monkeypatch
    ):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity(entity_class_name="Widget", name="tablet")
            db_map.add_metadata(name="author", value="A. Uthor")
        fetch_model(compound_entity_model)
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget", "tablet", "tablet", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(compound_entity_model, expected)
        with signal_waiter(compound_entity_model.dataChanged) as waiter:
            db_mngr.add_items(
                "entity_metadata",
                {
                    db_map: [
                        {
                            "entity_class_name": "Widget",
                            "entity_byname": ("clock",),
                            "metadata_name": "author",
                            "metadata_value": "A. Uthor",
                        },
                        {
                            "entity_class_name": "Widget",
                            "entity_byname": ("calendar",),
                            "metadata_name": "author",
                            "metadata_value": "A. Uthor",
                        },
                        {
                            "entity_class_name": "Widget",
                            "entity_byname": ("tablet",),
                            "metadata_name": "author",
                            "metadata_value": "A. Uthor",
                        },
                    ]
                },
            )
            waiter.wait()
            assert waiter.args == (
                compound_entity_model.index(0, 1),
                compound_entity_model.index(2, 1),
                [Qt.ItemDataRole.DisplayRole],
            )

    def test_removing_entity_metadata_item_emits_data_changed_for_name_column(
        self, compound_entity_model, db_mngr, db_map, db_name, monkeypatch
    ):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_metadata(name="author", value="A. Uthor")
        fetch_model(compound_entity_model)
        db_mngr.add_items(
            "entity_metadata",
            {
                db_map: [
                    {
                        "entity_class_name": "Widget",
                        "entity_byname": ("clock",),
                        "metadata_name": "author",
                        "metadata_value": "A. Uthor",
                    }
                ]
            },
        )
        with signal_waiter(compound_entity_model.dataChanged) as waiter:
            db_mngr.undo_stack[db_map].undo()
            waiter.wait()
            assert waiter.args == (
                compound_entity_model.index(0, 1),
                compound_entity_model.index(0, 1),
                [Qt.ItemDataRole.DisplayRole],
            )
