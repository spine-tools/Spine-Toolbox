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
from itertools import product
import unittest
from spinedb_api import Array, to_database
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
)
from tests.mock_helpers import fetch_model
from ..helpers import TestBase


class TestCompoundParameterDefinitionModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "parameter_name",
            "valid types",
            "value_list_name",
            "default_value",
            "description",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter_definition(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 7)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "p", None, None, "None", None, self.db_codename]
        self.assertEqual(row, expected)

    def test_data_for_single_parameter_definition_in_multidimensional_entity_class(self):
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_map.fetch_all()
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 7)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "p", None, None, "None", None, self.db_codename]
        self.assertEqual(row, expected)

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
        self.assertEqual(model.rowCount(), 0)

    def test_index_name_returns_sane_label(self):
        self._db_map.add_entity_class(name="Object")
        value, value_type = to_database(Array([2.3]))
        self._db_map.add_parameter_definition(
            name="x", entity_class_name="Object", default_value=value, default_type=value_type
        )
        model = CompoundParameterDefinitionModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterDefinitionModel_db - x - Object")


class TestCompoundParameterValueModel(TestBase):
    def test_horizontal_header(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        expected_header = [
            "entity_class_name",
            "entity_byname",
            "parameter_name",
            "alternative_name",
            "value",
            "database",
        ]
        header = [model.headerData(i) for i in range(model.columnCount())]
        self.assertEqual(header, expected_header)

    def test_data_for_single_parameter(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_id": 1, "id": 1}]})
        self._db_mngr.add_items("entity", {self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        value, value_type = to_database(23.0)
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": value,
                        "type": value_type,
                        "entity_id": 1,
                        "entity_class_id": 1,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            },
        )
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["oc", "o", "p", "Base", "23.0", self.db_codename]
        self.assertEqual(row, expected)

    def test_data_for_single_parameter_in_multidimensional_entity(self):
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "oc", "id": 1}]})
        self._db_mngr.add_items("entity", {self._db_map: [{"name": "o", "class_id": 1, "id": 1}]})
        self._db_mngr.add_items("entity_class", {self._db_map: [{"name": "rc", "dimension_id_list": [1], "id": 2}]})
        self._db_mngr.add_items("parameter_definition", {self._db_map: [{"name": "p", "entity_class_id": 2, "id": 1}]})
        self._db_mngr.add_items(
            "entity", {self._db_map: [{"name": "r", "class_id": 2, "element_id_list": [1], "id": 2}]}
        )
        value, value_type = to_database(23.0)
        self._db_mngr.add_items(
            "parameter_value",
            {
                self._db_map: [
                    {
                        "parameter_definition_id": 1,
                        "value": value,
                        "type": value_type,
                        "entity_id": 2,
                        "entity_class_id": 2,
                        "alternative_id": 1,
                        "id": 1,
                    }
                ]
            },
        )
        self.assertEqual(model.rowCount(), 1)
        self.assertEqual(model.columnCount(), 6)
        row = [model.index(0, column).data() for column in range(model.columnCount())]
        expected = ["rc", "o", "p", "Base", "23.0", self.db_codename]
        self.assertEqual(row, expected)

    def test_index_name_returns_sane_label(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="x", entity_class_name="Object")
        self._db_map.add_entity(name="mysterious cube", entity_class_name="Object")
        value, value_type = to_database(Array([2.3]))
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mysterious cube",),
            parameter_definition_name="x",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        index = model.index(0, 3)
        self.assertEqual(model.index_name(index), "TestCompoundParameterValueModel_db - x - Base - mysterious cube")

    def test_removing_first_of_two_rows(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            value=value,
            type=value_type,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_in_base.remove()
        value_not_in_base.remove()
        expected = []
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_not_in_base.restore()
        value_in_base.restore()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_removing_second_of_two_uncommitted_rows(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            value=value,
            type=value_type,
        )
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_not_in_base.remove()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_restoring_removed_item_keeps_empty_row_last(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        value_not_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            value=value,
            type=value_type,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_in_base.remove()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_not_in_base.remove()
        self.assertEqual(model.rowCount(), 0)
        self.assertEqual(model.sub_models, [])

    def test_removing_value_from_another_alternative_that_is_selected_for_filtering_works(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        not_base_alternative = self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            value=value,
            type=value_type,
        )
        self._db_map.commit_session("Add data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        model.set_filter_alternative_ids({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_in_base.remove()
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_restoring_removed_value_from_another_alternative_that_is_selected_for_filtering_works(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        not_base_alternative = self._db_map.add_alternative(name="not-Base")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="not-Base",
            value=value,
            type=value_type,
        )
        self._db_map.commit_session("Add test data")
        model = CompoundParameterValueModel(self._db_editor, self._db_mngr, self._db_map)
        model.init_model()
        fetch_model(model)
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        model.set_filter_alternative_ids({self._db_map: {not_base_alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "not-Base", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_in_base.remove()
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        value_in_base.restore()
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_remove_every_other_row(self):
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_alternative(name="ctrl")
        self._db_map.add_alternative(name="alt")
        self._db_map.add_alternative(name="del")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="ctrl",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(23.0)
        alt_value = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="alt",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-23.0)
        del_value = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="del",
            value=value,
            type=value_type,
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
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        self._db_map.remove_items("parameter_value", alt_value["id"], del_value["id"])
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
            ["Object", "curious sphere", "X", "ctrl", "-2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_remove_item_from_another_entity_class_than_selected(self):
        object_class = self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        self._db_map.add_entity_class(name="Immaterial")
        self._db_map.add_parameter_definition(name="Y", entity_class_name="Immaterial")
        self._db_map.add_parameter_definition(name="Z", entity_class_name="Immaterial")
        self._db_map.add_entity(name="ghost", entity_class_name="Immaterial")
        value, value_type = to_database(-2.3)
        self._db_map.add_parameter_value(
            entity_class_name="Immaterial",
            entity_byname=("ghost",),
            parameter_definition_name="Y",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(23.0)
        z_value = self._db_map.add_parameter_value(
            entity_class_name="Immaterial",
            entity_byname=("ghost",),
            parameter_definition_name="Z",
            alternative_name="Base",
            value=value,
            type=value_type,
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
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        model.set_filter_class_ids({self._db_map: {object_class["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        z_value.remove()
        expected = [
            ["Object", "curious sphere", "X", "Base", "2.3", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])

    def test_remove_visible_and_hidden_items(self):
        alternative = self._db_map.add_alternative(name="alt")
        self._db_map.add_entity_class(name="Object")
        self._db_map.add_parameter_definition(name="X", entity_class_name="Object")
        self._db_map.add_entity(name="mystic cube", entity_class_name="Object")
        self._db_map.add_entity(name="curious sphere", entity_class_name="Object")
        value, value_type = to_database(2.3)
        spherical_value_in_base = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-2.3)
        spherical_value_in_alt = self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("curious sphere",),
            parameter_definition_name="X",
            alternative_name="alt",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(23.0)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="Base",
            value=value,
            type=value_type,
        )
        value, value_type = to_database(-23.0)
        self._db_map.add_parameter_value(
            entity_class_name="Object",
            entity_byname=("mystic cube",),
            parameter_definition_name="X",
            alternative_name="alt",
            value=value,
            type=value_type,
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
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        model.set_filter_alternative_ids({self._db_map: {alternative["id"]}})
        model.refresh()
        expected = [
            ["Object", "curious sphere", "X", "alt", "-2.3", self.db_codename],
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        self.assertEqual(model.columnCount(), 6)
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])
        spherical_value_in_base.remove()
        spherical_value_in_alt.remove()
        expected = [
            ["Object", "mystic cube", "X", "alt", "-23.0", self.db_codename],
        ]
        self.assertEqual(model.rowCount(), len(expected))
        for row, column in product(range(model.rowCount()), range(model.columnCount())):
            with self.subTest(row=row, column=column):
                self.assertEqual(model.index(row, column).data(), expected[row][column])


if __name__ == "__main__":
    unittest.main()
