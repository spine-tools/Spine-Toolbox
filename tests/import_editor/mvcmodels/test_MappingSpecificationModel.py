######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""
Contains unit tests for Import editor's MappingSpecificationModel.
"""

import unittest
from unittest.mock import MagicMock
from PySide2.QtCore import Qt
from spinetoolbox.import_editor.mapping_colors import ERROR_COLOR
from spinetoolbox.import_editor.mvcmodels.mapping_specification_model import MappingSpecificationModel
from spinedb_api import item_mapping_from_dict


def _is_optional(index):
    optionals = ("Object metadata", "Relationship metadata", "Parameter value metadata", "Alternative names")
    return index.siblingAtColumn(0).data() in optionals


class TestMappingSpecificationModel(unittest.TestCase):
    def test_data_when_mapping_object_class_without_objects_or_parameters(self):
        undo_stack = MagicMock()
        model = MappingSpecificationModel(
            "source table",
            "mapping",
            item_mapping_from_dict({"map_type": "ObjectClass", "name": None, "object": None}),
            undo_stack,
        )
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_invalid_object_class_with_parameters(self):
        indexed_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": {'map_type': None},
            "parameter_type": "map",
            "value": {"map_type": None},
            "extra_dimensions": [{"map_type": None}],
        }
        mapping_dict = {
            "map_type": "ObjectClass",
            "name": None,
            "objects": None,
            "parameters": indexed_parameter_mapping_dict,
        }
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source table", "mapping 1", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 8)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object metadata")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        for row in range(8):
            index = model.index(row, 1)
            self.assertEqual(index.data(), "None")
            index = model.index(row, 2)
            self.assertEqual(index.data(), "")
            if not _is_optional(index):
                self.assertEqual(index.data(Qt.BackgroundRole), ERROR_COLOR)
                self.assertTrue(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_valid_object_class_with_pivoted_parameters(self):
        array_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": 2,
            "parameter_type": "array",
            "value": {"map_type": "row", "reference": 0},
        }
        mapping_dict = {"map_type": "ObjectClass", "name": 0, "objects": 1, "parameters": array_parameter_mapping_dict}
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source table", "mapping", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 7)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object metadata")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Pivoted")
        index = model.index(5, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(6, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), 0 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), 1 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(), 2 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(4, 2)
        self.assertEqual(index.data(), "Pivoted values")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(5, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(6, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_valid_object_class_with_parameters(self):
        indexed_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": {'map_type': 'column', 'reference': 99},
            "parameter_type": "map",
            "value": {"reference": 23, "map_type": "column"},
            "extra_dimensions": [{"reference": "fifth column", "map_type": "column"}],
        }
        mapping_dict = {
            "map_type": "ObjectClass",
            "parameters": indexed_parameter_mapping_dict,
            "name": {"reference": "class_name", "map_type": "constant"},
            "objects": {"reference": "object_name", "map_type": "constant"},
        }
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source table", "mapping 1", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 8)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object metadata")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(5, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(6, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(7, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "class_name")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), "object_name")
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 99 + 1)
        index = model.index(4, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 23 + 1)
        index = model.index(5, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(6, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(7, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_valid_object_class_with_nested_map(self):
        indexed_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": {'map_type': 'column', 'reference': 99},
            "parameter_type": "map",
            "value": {"reference": 23, "map_type": "column"},
            "extra_dimensions": [
                {"reference": "fifth column", "map_type": "column"},
                {"reference": "sixth column", "map_type": "column"},
            ],
        }
        mapping_dict = {
            "map_type": "ObjectClass",
            "parameters": indexed_parameter_mapping_dict,
            "name": {"reference": "class_name", "map_type": "constant"},
            "objects": {"reference": "object_name", "map_type": "constant"},
        }
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source table", "mapping", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 9)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object metadata")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Parameter index 2")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(8, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(5, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(6, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(7, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(8, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "class_name")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), "object_name")
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 99 + 1)
        index = model.index(4, 2)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 23 + 1)
        index = model.index(5, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(6, 2)
        self.assertEqual(index.data(), "sixth column")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(7, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(8, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_relationship_class_without_objects_or_parameters(self):
        undo_stack = MagicMock()
        model = MappingSpecificationModel(
            "source table name",
            "mapping",
            item_mapping_from_dict(
                {"map_type": "RelationshipClass", "name": None, "object_classes": None, "object": None}
            ),
            undo_stack,
        )
        self.assertEqual(model.rowCount(), 4)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Relationship class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object class names 1")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object names 1")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Relationship metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_invalid_relationship_class_with_parameters(self):
        indexed_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": {'map_type': None},
            "parameter_type": "map",
            "value": {"map_type": None},
            "extra_dimensions": [{"map_type": None}],
        }
        mapping_dict = {
            "map_type": "RelationshipClass",
            "name": None,
            "object_classes": None,
            "object": None,
            "parameters": indexed_parameter_mapping_dict,
        }
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source table", "mapping 1", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 9)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Relationship class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object class names 1")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object names 1")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Relationship metadata")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(8, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        for row in range(8):
            index = model.index(row, 1)
            self.assertEqual(index.data(), "None")
            index = model.index(row, 2)
            self.assertEqual(index.data(), "")
            if not _is_optional(index):
                self.assertEqual(index.data(Qt.BackgroundRole), ERROR_COLOR)
                self.assertTrue(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_multidimensional_relationship_class_with_parameters(self):
        indexed_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": {'map_type': 'column', 'reference': 99},
            "parameter_type": "map",
            "value": {"reference": 23, "map_type": "column"},
            "extra_dimensions": [{"reference": "fifth column", "map_type": "column"}],
        }
        mapping_dict = {
            "map_type": "RelationshipClass",
            "name": {"map_type": "constant", "reference": "relationship_class name"},
            "object_classes": [
                {"map_type": "column", "reference": "column header"},
                {"map_type": "constant", "reference": "second class"},
            ],
            "objects": [{"map_type": "column", "reference": 21}, {"map_type": "column", "reference": 22}],
            "parameters": indexed_parameter_mapping_dict,
        }
        undo_stack = MagicMock()
        model = MappingSpecificationModel("source_table", "mapping 1", item_mapping_from_dict(mapping_dict), undo_stack)
        self.assertEqual(model.rowCount(), 11)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Relationship class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object class names 1")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object class names 2")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Object names 1")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Object names 2")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Relationship metadata")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(8, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(9, 0)
        self.assertEqual(index.data(), "Alternative names")
        index = model.index(10, 0)
        self.assertEqual(index.data(), "Parameter value metadata")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(5, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(6, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(7, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(8, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(9, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(10, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "relationship_class name")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "column header")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "second class")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(), 21 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(4, 2)
        self.assertEqual(index.data(), 22 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(5, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(6, 2)
        self.assertEqual(index.data(), 99 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(7, 2)
        self.assertEqual(index.data(), 23 + 1)
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(8, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(9, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(10, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))


if __name__ == '__main__':
    unittest.main()
