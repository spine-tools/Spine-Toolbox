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
import unittest
from PySide6.QtCore import Qt
from spinetoolbox.spine_db_editor.mvcmodels.grouped_parameter_value_model import GroupedParameterValueModel
from tests.spine_db_editor.helpers import TestWithDBManager


class TestGroupedParameterValueModel(TestWithDBManager):

    def setUp(self):
        super().setUp()
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)

    def test_row_count(self):
        self.assertEqual(self._model.rowCount(), 0)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value_to_spoon(self._db_map, "X", "Base")
        _add_value_to_spoon(self._db_map, "X", "alt1")
        self._model.load_data({self._db_map: class_ids})
        self.assertEqual(self._model.rowCount(), 1)
        group_index = self._model.index(0, 0)
        self.assertEqual(self._model.rowCount(group_index), 2)
        value_index = self._model.index(0, 0, group_index)
        self.assertEqual(self._model.rowCount(value_index), 0)
        for surplus_group_column in range(1, self._model.columnCount()):
            with self.subTest(column=surplus_group_column):
                group_index = self._model.index(0, surplus_group_column)
                self.assertEqual(self._model.rowCount(group_index), 0)

    def test_column_count(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        self.assertEqual(self._model.columnCount(), 6)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value_to_spoon(self._db_map, "X", "Base")
        _add_value_to_spoon(self._db_map, "X", "alt1")
        self._model.load_data({self._db_map: class_ids})
        group_index = self._model.index(0, 0)
        self.assertEqual(self._model.columnCount(group_index), 6)

    def test_get_display_data_for_no_groups(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value_to_spoon(self._db_map, "X", "Base")
        _add_value_to_spoon(self._db_map, "X", "alt1")
        self._model.load_data({self._db_map: class_ids})
        expected = [
            ["Object", "spoon", "X", "Base", "2.3", self.db_codename],
            ["Object", "spoon", "X", "alt1", "2.3", self.db_codename],
        ]
        group_index = self._model.index(0, 0)
        self.assertEqual(self._model.data(group_index), None)
        data = []
        for row in range(self._model.rowCount(group_index)):
            data_row = []
            for column in range(self._model.columnCount(group_index)):
                index = self._model.index(row, column, group_index)
                data_row.append(self._model.data(index))
            data.append(data_row)
        self.assertEqual(data, expected)

    def test_get_display_data_for_groups(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value_to_spoon(self._db_map, "X", "Base")
        _add_value_to_spoon(self._db_map, "X", "alt1")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="first group/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="first group/Z")
        _add_value_to_spoon(self._db_map, "first group/Y", "Base")
        _add_value_to_spoon(self._db_map, "first group/Z", "Base")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="second group/P")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="second group/Q")
        _add_value_to_spoon(self._db_map, "second group/P", "Base")
        _add_value_to_spoon(self._db_map, "second group/Q", "Base")
        self._model.load_data({self._db_map: class_ids})
        groups = {None, "first group", "second group"}
        expected = {
            None: [
                ["Object", "spoon", "X", "Base", "2.3", self.db_codename],
                ["Object", "spoon", "X", "alt1", "2.3", self.db_codename],
            ],
            "first group": [
                ["Object", "spoon", "Y", "Base", "2.3", self.db_codename],
                ["Object", "spoon", "Z", "Base", "2.3", self.db_codename],
            ],
            "second group": [
                ["Object", "spoon", "P", "Base", "2.3", self.db_codename],
                ["Object", "spoon", "Q", "Base", "2.3", self.db_codename],
            ],
        }
        for group_row in range(self._model.rowCount()):
            group_index = self._model.index(group_row, 0)
            group_name = self._model.data(group_index)
            self.assertIn(group_name, groups)
            groups.remove(group_name)
            expected_data = expected[group_name]
            data = []
            for row in range(self._model.rowCount(group_index)):
                data_row = []
                for column in range(self._model.columnCount(group_index)):
                    index = self._model.index(row, column, group_index)
                    data_row.append(self._model.data(index))
                data.append(data_row)
            self.assertEqual(data, expected_data)

    def test_get_display_data_for_unsorted_groups(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="group/X")
        _add_value_to_spoon(self._db_map, "group/X", "Base")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Y")
        _add_value_to_spoon(self._db_map, "Y", "Base")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="group/Z")
        _add_value_to_spoon(self._db_map, "group/Z", "Base")
        self._model.load_data({self._db_map: class_ids})
        groups = {None, "group"}
        expected = {
            "group": [
                ["Object", "spoon", "X", "Base", "2.3", self.db_codename],
                ["Object", "spoon", "Z", "Base", "2.3", self.db_codename],
            ],
            None: [
                ["Object", "spoon", "Y", "Base", "2.3", self.db_codename],
            ],
        }
        for group_row in range(self._model.rowCount()):
            group_index = self._model.index(group_row, 0)
            group_name = self._model.data(group_index)
            self.assertIn(group_name, groups)
            groups.remove(group_name)
            expected_data = expected[group_name]
            data = []
            for row in range(self._model.rowCount(group_index)):
                data_row = []
                for column in range(self._model.columnCount(group_index)):
                    index = self._model.index(row, column, group_index)
                    data_row.append(self._model.data(index))
                data.append(data_row)
            self.assertEqual(data, expected_data)

    def test_horizontal_header_display_data(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        headers = [
            self._model.headerData(section, Qt.Orientation.Horizontal) for section in range(self._model.columnCount())
        ]
        self.assertEqual(
            headers, ["entity_class_name", "entity_byname", "parameter_name", "alternative_name", "value", "database"]
        )

    def test_vertical_header_display_data(self):
        self._model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        class_ids = _add_base_data(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value_to_spoon(self._db_map, "X", "Base")
        _add_value_to_spoon(self._db_map, "X", "alt1")
        self._model.load_data({self._db_map: class_ids})
        for row in range(self._model.rowCount()):
            self.assertIsNone(self._model.headerData(row, Qt.Orientation.Vertical))


def _add_base_data(db_map):
    db_map.add_alternative(name="alt1")
    entity_class = db_map.add_entity_class(name="Object")
    db_map.add_entity(entity_class_name="Object", name="spoon")
    return [entity_class["id"]]


def _add_value_to_spoon(db_map, parameter_name, alternative_name):
    db_map.add_parameter_value(
        entity_class_name="Object",
        entity_byname=("spoon",),
        parameter_definition_name=parameter_name,
        alternative_name=alternative_name,
        parsed_value=2.3,
    )


if __name__ == "__main__":
    unittest.main()
