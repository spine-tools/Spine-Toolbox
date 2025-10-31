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
from PySide6.QtWidgets import QApplication
from spinedb_api import Array
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.parameter_type_validation import ValidationKey
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
        model.init_model()
        expected_header = [
            "class",
            "parameter name",
            "valid types",
            "value list",
            "default value",
            "description",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "oc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["oc", "p", None, None, "None", None, self.db_codename]]
        assert_table_model_data(model, expected, self)

    def test_data_for_single_parameter_definition_in_multidimensional_entity_class(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "rc", "dimension_name_list": ["oc"]}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_name": "rc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["rc", "p", None, None, "None", None, self.db_codename]]
        assert_table_model_data(model, expected, self)

    def test_model_updates_when_entity_class_is_removed(self):
        self._db_map.add_entity_class(name="oc1")
        self._db_map.add_parameter_definition(entity_class_name="oc1", name="x")
        entity_class_2 = self._db_map.add_entity_class(name="oc2")
        self._db_map.add_parameter_definition(entity_class_name="oc2", name="x")
        self._db_map.add_entity_class(name="rc", dimension_name_list=("oc1", "oc2"))
        self._db_map.add_parameter_definition(entity_class_name="rc", name="x")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self.assertEqual(model.rowCount(), 3)
        model.set_filter_class_ids({self._db_map: {entity_class_2["id"]}})
        model.refresh()
        self.assertEqual(model.rowCount(), 2)
        self._db_mngr.remove_items({self._db_map: {"entity_class": [entity_class_2["id"]]}})
        while model.rowCount() == 2:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(), 0)

    def test_index_name_returns_sane_label(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="x", entity_class_name="Object", parsed_value=Array([2.3]))
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterDefinitionModel_db - Object - x")

    def test_updating_definition_triggers_value_type_validation(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Widget")
            weight = self._db_map.add_parameter_definition(
                entity_class_name="Widget", name="weight", parsed_value="a lot"
            )
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            fetch_model(model)
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), weight["id"].private_id)], [True]),
            )
        expected = [["Widget", "weight", None, None, "a lot", None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            model.setData(model.index(0, 2), ("float",), Qt.ItemDataRole.EditRole)
            expected = [["Widget", "weight", "float", None, "a lot", None, self.db_codename]]
            assert_table_model_data(model, expected, self)
            waiter.wait()
            self.assertEqual(
                waiter.args,
                ([ValidationKey("parameter_definition", id(self._db_map), weight["id"].private_id)], [False]),
            )
        while self._db_mngr.parameter_type_validator._sent_task_count != 0:
            QApplication.processEvents()

    def test_restore_db_maps(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc"}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p1", "entity_class_name": "oc"}]})
        while model.rowCount() != 1:
            QApplication.processEvents()
        expected = [["oc", "p1", None, None, "None", None, self.db_codename]]
        assert_table_model_data(model, expected, self)
        with TemporaryDirectory() as tmp_dir:
            url = "sqlite:///" + str(pathlib.Path(tmp_dir, "other_db.sqlite"))
            logger = mock.MagicMock()
            db_map = self._db_mngr.get_db_map(url, logger, create=True)
            with db_map:
                db_map.add_entity_class(name="Object")
                db_map.add_parameter_definition(entity_class_name="Object", name="X", description="X marks the spot.")
            model.reset_db_maps([db_map])
            model.init_model()
            self.assertEqual(model.rowCount(), 0)
            self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p2", "entity_class_name": "oc"}]})
            fetch_model(model)
            expected = [["Object", "X", None, None, "None", "X marks the spot.", "other_db"]]
            assert_table_model_data(model, expected, self)
            self._db_mngr.close_session(url)
            gc.collect()

    def test_signals_when_non_committed_data_is_added(self):
        with self._db_map:
            self._db_map.add_entity_class(name="Gadget")
            self._db_map.add_parameter_definition(entity_class_name="Gadget", name="X")
            self._db_map.commit_session("Mark items as committed.")
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        with (
            mock.patch.object(model, "non_committed_items_about_to_be_added") as begin_signal,
            mock.patch.object(model, "non_committed_items_added") as end_signal,
        ):
            fetch_model(model)
            begin_signal.emit.assert_not_called()
            end_signal.emit.assert_not_called()
        expected = [["Gadget", "X", None, None, "None", None, self.db_codename]]
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
            ["Gadget", "X", None, None, "None", None, self.db_codename],
            ["Gadget", "Y", None, None, "None", None, self.db_codename],
        ]
        assert_table_model_data_pytest(model, expected)


class TestCompoundParameterValueModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "class",
            "entity byname",
            "parameter name",
            "alternative",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
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
        expected = [["oc", "o", "p", "Base", "23.0", self.db_codename]]
        assert_table_model_data(model, expected, self)

    def test_data_for_single_parameter_in_multidimensional_entity(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
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
        expected = [["rc", "o", "p", "Base", "23.0", self.db_codename]]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(
            model.index_name(index), "TestCompoundParameterValueModel_db - Object - mysterious cube - x - Base"
        )

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
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
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_not_in_base.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_not_in_base.remove()
        while model.rowCount() == 1:
            QApplication.processEvents()
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.sub_models, [])

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_filter_alternative_ids({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_filter_alternative_ids({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        value_in_base.remove()
        assert_table_model_data(model, expected, self)
        value_in_base.restore()
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "alt", "23.0", self.db_codename],
            ["Object", "curious sphere", "X", "ctrl", "-2.3", self.db_codename],
            ["Object", "curious sphere", "X", "del", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        self._db_map.remove_items("parameter_value", alt_value["id"], del_value["id"])
        while model.rowCount() == 4:
            QApplication.processEvents()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "ctrl", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Immaterial", "ghost", "Y", "Base", "-2.3", self.db_codename],
            ["Immaterial", "ghost", "Z", "Base", "23.0", self.db_codename],
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_filter_class_ids({self._db_map: {object_class["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        z_value.remove()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            ["Object", "mystic cube", "X", "Base", "23.0", self.db_codename],
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_filter_alternative_ids({self._db_map: {alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        spherical_value_in_base.remove()
        spherical_value_in_alt.remove()
        while model.rowCount() == 2:
            QApplication.processEvents()
        expected = [
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            ["Object", "mystic cube", "X", "Base", "23.0", self.db_codename],
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        model.set_filter_entity_ids({(self._db_map, object_class["id"]): {curious_sphere["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        with signal_waiter(model.dataChanged, timeout=1.0) as waiter:
            spherical_value_in_base.update(parsed_value=55.5)
            waiter.wait()
        self.assertEqual(
            waiter.args, (model.index(0, 0), model.index(0, model.columnCount() - 1), [Qt.ItemDataRole.DisplayRole])
        )
        expected = [
            ["Object", "curious sphere", "X", "Base", "55.5", self.db_codename],
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)

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
        model.init_model()
        with signal_waiter(self._db_mngr.parameter_type_validator.validated, timeout=5.0) as waiter:
            fetch_model(model)
            expected = [["Widget", "gadget", "weight", "Base", "a lot", self.db_codename]]
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
        model.init_model()
        fetch_model(model)
        expected = [
            ["Widget", "gadget", "weight", "Base", "a lot", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)
        index = model.index(0, 4)
        self.assertTrue(model.batch_set_data([index], ["too much"]))
        expected = [
            ["Widget", "gadget", "weight", "Base", "too much", self.db_codename],
        ]
        assert_table_model_data(model, expected, self)


class TestCompoundEntityAlternativeModel:
    def test_horizontal_header(self, db_mngr, db_map, db_editor):
        model = CompoundEntityAlternativeModel(db_editor, db_mngr, db_map)
        model.init_model()
        expected_header = [
            "class",
            "entity byname",
            "alternative",
            "active",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        assert header == expected_header

    def test_data_for_single_entity_alternative(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget")
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("gadget",), alternative_name="Base", active=True
            )
        model = CompoundEntityAlternativeModel(db_editor, db_mngr, db_map)
        model.init_model()
        fetch_model(model)
        expected = [["Widget", "gadget", "Base", True, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_updating_byname_to_non_existing_entity_fails(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget")
            db_map.add_entity_alternative(
                entity_class_name="Widget", entity_byname=("gadget",), alternative_name="Base", active=True
            )
        model = CompoundEntityAlternativeModel(db_editor, db_mngr, db_map)
        model.init_model()
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


class TestCompoundEntityModel:
    def test_horizontal_header(self, db_mngr, db_map, db_editor):
        model = CompoundEntityModel(db_editor, db_mngr, db_map)
        model.init_model()
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
        header = [model.headerData(i) for i in range(model.columnCount())]
        assert header == expected_header

    def test_data_for_single_entity_alternative(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="gadget", description="Gadget is a widget.")
        model = CompoundEntityModel(db_editor, db_mngr, db_map)
        model.init_model()
        fetch_model(model)
        expected = [["Widget", "gadget", "gadget", "Gadget is a widget.", None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_filtering_by_entity(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            flashlight = db_map.add_entity(entity_class_name="Gadget", name="flashlight")
            microphone = db_map.add_entity(entity_class_name="Gadget", name="microphone")
        model = CompoundEntityModel(db_editor, db_mngr, db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Gadget", "flashlight", "flashlight", None, None, None, None, None, None, db_name],
            ["Gadget", "microphone", "microphone", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(model, expected)
        model.set_filter_entity_ids({(db_map, gadget["id"]): {microphone["id"]}})
        model.refresh()
        expected = [
            ["Gadget", "microphone", "microphone", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_update_entity_with_location_and_shape_information(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            db_map.add_entity_class(name="Widget")
            gadget = db_map.add_entity(entity_class_name="Widget", name="gadget")
        model = CompoundEntityModel(db_editor, db_mngr, db_map)
        model.init_model()
        fetch_model(model)
        expected = [["Widget", "gadget", "gadget", None, None, None, None, None, None, db_name]]
        assert_table_model_data_pytest(model, expected)
        gadget.update(lat=1.1, lon=2.2, alt=3.3, shape_name="region", shape_blob="{}")
        expected = [["Widget", "gadget", "gadget", None, "1.1", "2.2", "3.3", "region", "<geojson>", db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_update_entity_byname(self, db_mngr, db_map, db_name, db_editor):
        with db_map:
            db_map.add_entity_class(name="Widget")
            db_map.add_entity(entity_class_name="Widget", name="clock")
            db_map.add_entity(entity_class_name="Widget", name="calendar")
            db_map.add_entity_class(dimension_name_list=["Widget"])
            db_map.add_entity(entity_class_name="Widget__", entity_byname=("calendar",))
        model = CompoundEntityModel(db_editor, db_mngr, db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget__", "calendar__", "calendar", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(model, expected)
        index = model.index(2, 2)
        assert model.batch_set_data([index], [("clock",)])
        expected = [
            ["Widget", "calendar", "calendar", None, None, None, None, None, None, db_name],
            ["Widget", "clock", "clock", None, None, None, None, None, None, db_name],
            ["Widget__", "calendar__", "clock", None, None, None, None, None, None, db_name],
        ]
        assert_table_model_data_pytest(model, expected)
