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
from collections import defaultdict
from itertools import chain
import unittest
from spinedb_api import import_data
from spinetoolbox.spine_db_editor.mvcmodels.grouped_parameter_value_model import GroupedParameterValueModel
from spinetoolbox.spine_db_editor.mvcmodels.grouped_parameter_value_proxy_model import GroupedParameterValueProxyModel
from tests.spine_db_editor.helpers import TestWithDBManager


class TestGroupedParameterValueProxyModel(TestWithDBManager):
    def setUp(self):
        super().setUp()
        self._source_model = GroupedParameterValueModel(self._db_mngr, self._db_mngr)
        self._proxy_model = GroupedParameterValueProxyModel(self._db_mngr)
        self._proxy_model.setSourceModel(self._source_model)

    def test_map_from_source_with_ungrouped_data(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value(self._db_map, "X")
        self._source_model.load_data({self._db_map: class_ids})
        ungrouped_index = self._source_model.index(0, 0)
        proxy_index = self._proxy_model.mapFromSource(ungrouped_index)
        self.assertEqual(proxy_index.row(), 0)
        self.assertEqual(proxy_index.column(), 0)

    def test_map_from_source_with_grouped_data(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 3/Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Group 2/Y")
        _add_value(self._db_map, "Group 3/Z")
        self._source_model.load_data({self._db_map: class_ids})
        for row in range(3):
            with self.subTest(row=row):
                grouped_index = self._source_model.index(row, 0)
                proxy_index = self._proxy_model.mapFromSource(grouped_index)
                self.assertEqual(proxy_index.row(), row)
                self.assertEqual(proxy_index.column(), 0)

    def test_map_from_source_with_ungrouped_data_in_beginning(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Z")
        _add_value(self._db_map, "X")
        _add_value(self._db_map, "Group 1/Y")
        _add_value(self._db_map, "Group 2/Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [2, 0, 1]
        for row in range(3):
            with self.subTest(row=row):
                grouped_index = self._source_model.index(row, 0)
                proxy_index = self._proxy_model.mapFromSource(grouped_index)
                self.assertEqual(proxy_index.row(), expected_rows[row])
                self.assertEqual(proxy_index.column(), 0)

    def test_map_from_source_with_ungrouped_data_in_middle(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Y")
        _add_value(self._db_map, "Group 2/Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [0, 2, 1]
        for row in range(3):
            with self.subTest(row=row):
                grouped_index = self._source_model.index(row, 0)
                proxy_index = self._proxy_model.mapFromSource(grouped_index)
                self.assertEqual(proxy_index.row(), expected_rows[row])
                self.assertEqual(proxy_index.column(), 0)

    def test_map_from_source_with_ungrouped_data_in_end(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Group 2/Y")
        _add_value(self._db_map, "Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [0, 1, 2]
        for row in range(3):
            with self.subTest(row=row):
                grouped_index = self._source_model.index(row, 0)
                proxy_index = self._proxy_model.mapFromSource(grouped_index)
                self.assertEqual(proxy_index.row(), expected_rows[row])
                self.assertEqual(proxy_index.column(), 0)

    def test_map_to_source_with_ungrouped_data(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value(self._db_map, "X")
        self._source_model.load_data({self._db_map: class_ids})
        ungrouped_proxy_index = self._proxy_model.index(0, 0)
        source_index = self._proxy_model.mapToSource(ungrouped_proxy_index)
        self.assertEqual(source_index.row(), 0)
        self.assertEqual(source_index.column(), 0)

    def test_map_to_source_with_grouped_data(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 3/Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Group 2/Y")
        _add_value(self._db_map, "Group 3/Z")
        self._source_model.load_data({self._db_map: class_ids})
        for row in range(3):
            with self.subTest(row=row):
                grouped_index = self._proxy_model.index(row, 0)
                source_index = self._proxy_model.mapToSource(grouped_index)
                self.assertEqual(source_index.row(), row)
                self.assertEqual(source_index.column(), 0)

    def test_map_to_source_with_ungrouped_data_in_beginning(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Z")
        _add_value(self._db_map, "X")
        _add_value(self._db_map, "Group 1/Y")
        _add_value(self._db_map, "Group 2/Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [1, 2, 0]
        for row in range(3):
            with self.subTest(row=row):
                grouped_proxy_index = self._proxy_model.index(row, 0)
                source_index = self._proxy_model.mapToSource(grouped_proxy_index)
                self.assertEqual(source_index.row(), expected_rows[row])
                self.assertEqual(source_index.column(), 0)

    def test_map_to_source_with_ungrouped_data_in_middle(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Y")
        _add_value(self._db_map, "Group 2/Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [0, 2, 1]
        for row in range(3):
            with self.subTest(row=row):
                grouped_proxy_index = self._proxy_model.index(row, 0)
                source_index = self._proxy_model.mapToSource(grouped_proxy_index)
                self.assertEqual(source_index.row(), expected_rows[row])
                self.assertEqual(source_index.column(), 0)

    def test_map_to_source_with_ungrouped_data_in_end(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Group 2/Y")
        _add_value(self._db_map, "Z")
        self._source_model.load_data({self._db_map: class_ids})
        expected_rows = [0, 1, 2]
        for row in range(3):
            with self.subTest(row=row):
                grouped_proxy_index = self._proxy_model.index(row, 0)
                source_index = self._proxy_model.mapToSource(grouped_proxy_index)
                self.assertEqual(source_index.row(), expected_rows[row])
                self.assertEqual(source_index.column(), 0)

    def test_map_to_source_value_indexes(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value(self._db_map, "X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Y")
        _add_value(self._db_map, "Y")
        self._source_model.load_data({self._db_map: class_ids})
        root_proxy_index = self._proxy_model.index(0, 0)
        self.assertIsNone(root_proxy_index.data())
        self.assertEqual(self._proxy_model.rowCount(root_proxy_index), 2)
        data = []
        for row in range(self._proxy_model.rowCount(root_proxy_index)):
            row_data = []
            for column in range(self._proxy_model.columnCount(root_proxy_index)):
                index = self._proxy_model.index(row, column, root_proxy_index)
                row_data.append(index.data())
            data.append(row_data)
        self.assertEqual(
            data,
            [
                ["Object", "spoon", "X", "Base", "2.3", self.db_codename],
                ["Object", "spoon", "Y", "Base", "2.3", self.db_codename],
            ],
        )

    def test_map_to_source_value_indexes_with_groups(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 1/X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 2/Y")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group 3/Z")
        _add_value(self._db_map, "Group 1/X")
        _add_value(self._db_map, "Group 2/Y")
        _add_value(self._db_map, "Group 3/Z")
        self._source_model.load_data({self._db_map: class_ids})
        self.assertEqual(self._proxy_model.rowCount(), 3)
        expected_groups = ["Group 1", "Group 2", "Group 3"]
        expected_parameters = ["X", "Y", "Z"]
        for proxy_root_row in range(self._proxy_model.rowCount()):
            root_proxy_index = self._proxy_model.index(proxy_root_row, 0)
            self.assertEqual(root_proxy_index.data(), expected_groups[proxy_root_row])
            self.assertEqual(self._proxy_model.rowCount(root_proxy_index), 1)
            data = []
            for row in range(self._proxy_model.rowCount(root_proxy_index)):
                row_data = []
                for column in range(self._proxy_model.columnCount(root_proxy_index)):
                    index = self._proxy_model.index(row, column, root_proxy_index)
                    row_data.append(index.data())
                data.append(row_data)
            self.assertEqual(
                data, [["Object", "spoon", expected_parameters[proxy_root_row], "Base", "2.3", self.db_codename]]
            )

    def test_model_data(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group/X")
        _add_value(self._db_map, "Group/X")
        self._source_model.load_data({self._db_map: class_ids})
        self.assertEqual(self._proxy_model.rowCount(), 1)
        self.assertEqual(self._proxy_model.columnCount(), 6)
        for column in range(1, 6):
            no_entry_group_index = self._proxy_model.index(0, column)
            self.assertEqual(self._proxy_model.rowCount(no_entry_group_index), 0)
        group_index = self._proxy_model.index(0, 0)
        self.assertEqual(group_index.data(), "Group")
        self.assertEqual(self._proxy_model.rowCount(group_index), 1)
        self.assertEqual(self._proxy_model.columnCount(group_index), 6)
        for column, expected in enumerate(["Object", "spoon", "X", "Base", "2.3"]):
            index = self._proxy_model.index(0, column, group_index)
            self.assertEqual(self._proxy_model.data(index), expected)

    def test_model_data_with_groups_and_ungrouped_values(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        self._db_map.add_parameter_definition(entity_class_name="Object", name="X")
        _add_value(self._db_map, "X")
        self._db_map.add_parameter_definition(entity_class_name="Object", name="Group/Y")
        _add_value(self._db_map, "Group/Y")
        self._source_model.load_data({self._db_map: class_ids})
        self.assertEqual(self._proxy_model.rowCount(), 2)
        self.assertEqual(self._proxy_model.columnCount(), 6)
        for row in range(2):
            for column in range(1, 6):
                no_entry_group_index = self._proxy_model.index(row, column)
                self.assertEqual(self._proxy_model.rowCount(no_entry_group_index), 0)
        group_index = self._proxy_model.index(0, 0)
        self.assertEqual(group_index.data(), "Group")
        self.assertEqual(self._proxy_model.rowCount(group_index), 1)
        self.assertEqual(self._proxy_model.columnCount(group_index), 6)
        for column, expected in enumerate(["Object", "spoon", "Y", "Base", "2.3"]):
            index = self._proxy_model.index(0, column, group_index)
            self.assertEqual(self._proxy_model.data(index), expected)
        ungroup_index = self._proxy_model.index(1, 0)
        self.assertEqual(ungroup_index.data(), None)
        self.assertEqual(self._proxy_model.rowCount(ungroup_index), 1)
        self.assertEqual(self._proxy_model.columnCount(ungroup_index), 6)
        for column, expected in enumerate(["Object", "spoon", "X", "Base", "2.3"]):
            index = self._proxy_model.index(0, column, ungroup_index)
            self.assertEqual(self._proxy_model.data(index), expected)

    def test_model_data_with_greater_groups_and_ungrouped_values(self):
        class_ids = _add_class_and_entity_and_parameter(self._db_map)
        groups = ["Group", None, "Group"]
        parameters = ["X", "Y", "Z"]
        for group, parameter in zip(groups, parameters):
            parameter_name = f"{group}/{parameter}" if group is not None else parameter
            self._db_map.add_parameter_definition(entity_class_name="Object", name=parameter_name)
            _add_value(self._db_map, parameter_name)
        self._source_model.load_data({self._db_map: class_ids})
        self.assertEqual(self._proxy_model.rowCount(), len(set(groups)))
        self.assertEqual(self._proxy_model.columnCount(), 6)
        for row in range(self._proxy_model.rowCount()):
            for column in range(1, 6):
                no_entry_group_index = self._proxy_model.index(row, column)
                self.assertEqual(self._proxy_model.rowCount(no_entry_group_index), 0)
        expected_groups, expected_parameters = _sort_groups_and_parameters(groups, parameters)
        for group_row in range(self._proxy_model.rowCount()):
            group_index = self._proxy_model.index(group_row, 0)
            self.assertEqual(group_index.data(), expected_groups.pop(0))
            for parameter_row in range(self._proxy_model.rowCount(group_index)):
                row = []
                for column in range(self._proxy_model.columnCount(group_index)):
                    index = self._proxy_model.index(parameter_row, column, group_index)
                    row.append(index.data())
                self.assertEqual(row, ["Object", "spoon", expected_parameters.pop(0), "Base", "2.3", self.db_codename])

    def test_crash(self):
        input_data = {
            "entity_classes": [["Unit", [], None, 280743389491829, True]],
            "entities": [
                ["Unit", "coal_plant", None],
                ["Unit", "dyson_sphere", None],
                ["Unit", "antimatter_plant", None],
                ["Unit", "linear_accelerator", None],
            ],
            "parameter_definitions": [
                ["Unit", "Group 1/X", None, None, None],
                ["Unit", "Group 1/Y", None, None, None],
                ["Unit", "Group 1/Z", None, None, None],
                ["Unit", "Group 2/P", None, None, None],
                ["Unit", "Group 2/Q", None, None, None],
                ["Unit", "Group 2/R", None, None, None],
                ["Unit", "Group 3/I", None, None, None],
                ["Unit", "Group 3/J", None, None, None],
                ["Unit", "Group 3/K", None, None, None],
                ["Unit", "var1", None, None, None],
                ["Unit", "var2", None, None, None],
                ["Unit", "var3", None, None, None],
                ["Unit", "var4", None, None, None],
                ["Unit", "var5", None, None, None],
                ["Unit", "var6", None, None, None],
                ["Unit", "var7", None, None, None],
                ["Unit", "var8", None, None, None],
            ],
            "parameter_values": [
                ["Unit", "antimatter_plant", "Group 1/X", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "Group 1/Z", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "Group 1/X", 2.3, "alt2"],
                ["Unit", "antimatter_plant", "Group 1/Y", 2.3, "alt2"],
                ["Unit", "antimatter_plant", "Group 1/X", 2.3, "Base"],
                ["Unit", "antimatter_plant", "Group 2/P", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "Group 2/Q", 2.3, "alt4"],
                ["Unit", "antimatter_plant", "Group 2/R", 2.3, "alt2"],
                ["Unit", "antimatter_plant", "var1", 2.3, "Base"],
                ["Unit", "antimatter_plant", "var2", 2.3, "Base"],
                ["Unit", "antimatter_plant", "var3", 2.3, "alt3"],
                ["Unit", "antimatter_plant", "var4", 2.3, "alt3"],
                ["Unit", "antimatter_plant", "var5", 2.3, "Base"],
                ["Unit", "antimatter_plant", "var6", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "var7", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "Group 3/J", 2.3, "alt1"],
                ["Unit", "antimatter_plant", "Group 3/K", 2.3, "alt2"],
                ["Unit", "antimatter_plant", "Group 3/K", 2.3, "alt3"],
            ],
            "alternatives": [["Base", "Base alternative"], ["alt1", ""], ["alt2", ""], ["alt3", ""], ["alt4", ""]],
        }
        _, errors = import_data(self._db_map, **input_data)
        self.assertEqual(errors, [])
        unit = self._db_map.entity_class(name="Unit")
        self._source_model.load_data({self._db_map: [unit["id"]]})
        expected_groups = ["Group 1", "Group 2", "Group 3", None]
        expected_parameters = [
            "X",
            "Z",
            "X",
            "Y",
            "X",
            "P",
            "Q",
            "R",
            "J",
            "K",
            "K",
            "var1",
            "var2",
            "var3",
            "var4",
            "var5",
            "var6",
            "var7",
        ]
        expected_alternatives = [
            "alt1",
            "alt1",
            "alt2",
            "alt2",
            "Base",
            "alt1",
            "alt4",
            "alt2",
            "alt1",
            "alt2",
            "alt3",
            "Base",
            "Base",
            "alt3",
            "alt3",
            "Base",
            "alt1",
            "alt1",
        ]
        for group_row in range(self._proxy_model.rowCount()):
            group_index = self._proxy_model.index(group_row, 0)
            self.assertEqual(group_index.data(), expected_groups.pop(0))
            for parameter_row in range(self._proxy_model.rowCount(group_index)):
                row = []
                for column in range(self._proxy_model.columnCount(group_index)):
                    index = self._proxy_model.index(parameter_row, column, group_index)
                    row.append(index.data())
                with self.subTest(parameter_row=parameter_row):
                    self.assertEqual(
                        row,
                        [
                            "Unit",
                            "antimatter_plant",
                            expected_parameters.pop(0),
                            expected_alternatives.pop(0),
                            "2.3",
                            self.db_codename,
                        ],
                    )
        self.assertEqual(expected_groups, [])
        self.assertEqual(expected_parameters, [])
        self.assertEqual(expected_alternatives, [])


def _add_class_and_entity_and_parameter(db_map):
    entity_class = db_map.add_entity_class(name="Object")
    db_map.add_entity(entity_class_name="Object", name="spoon")
    return [entity_class["id"]]


def _add_value(db_map, parameter_name):
    db_map.add_parameter_value(
        entity_class_name="Object",
        entity_byname=("spoon",),
        parameter_definition_name=parameter_name,
        alternative_name="Base",
        parsed_value=2.3,
    )


def _sort_groups_and_parameters(groups, parameters):
    sorted_groups = defaultdict(list)
    no_group_parameters = []
    for group, parameter in zip(groups, parameters):
        if group is not None:
            sorted_groups[group].append(parameter)
        else:
            no_group_parameters.append(parameter)
    sorted_groups[None] = no_group_parameters
    return list(sorted_groups), list(chain(*sorted_groups.values()))


if __name__ == "__main__":
    unittest.main()
