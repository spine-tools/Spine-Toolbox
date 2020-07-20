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
Contains unit tests for io_models.py.
"""

import unittest
from spinetoolbox.spine_io.io_models import MappingPreviewModel, MappingSpecModel, _ERROR_COLOR, _MAPPING_COLORS
from spinetoolbox.spine_io.type_conversion import value_to_convert_spec
from spinedb_api import dict_to_map
from PySide2.QtCore import Qt


class TestMappingPreviewModel(unittest.TestCase):
    def test_column_type_checking(self):
        model = MappingPreviewModel()
        model.reset_model([["1", "0h", "2018-01-01 00:00"], ["2", "1h", "2018-01-01 00:00"]])
        model.set_type(0, value_to_convert_spec('float'))
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})
        model.set_type(1, value_to_convert_spec('duration'))
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})
        model.set_type(2, value_to_convert_spec('datetime'))
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})

    def test_row_type_checking(self):
        model = MappingPreviewModel()
        model.reset_model(
            [["1", "1", "1.1"], ["2h", "1h", "2h"], ["2018-01-01 00:00", "2018-01-01 00:00", "2018-01-01 00:00"]]
        )
        model.set_type(0, value_to_convert_spec('float'), orientation=Qt.Vertical)
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})
        model.set_type(1, value_to_convert_spec('duration'), orientation=Qt.Vertical)
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})
        model.set_type(2, value_to_convert_spec('datetime'), orientation=Qt.Vertical)
        self.assertEqual(model._column_type_errors, {})
        self.assertEqual(model._row_type_errors, {})

    def test_column_type_checking_produces_error(self):
        model = MappingPreviewModel()
        model.reset_model([["Not a valid number", "2.4"], ["1", "3"]])
        model.set_type(0, value_to_convert_spec('float'))
        error_index = (0, 0)
        self.assertEqual(len(model._column_type_errors), 1)
        self.assertEqual(model._row_type_errors, {})
        self.assertTrue(error_index in model._column_type_errors)
        self.assertEqual(model.data(model.index(*error_index)), "Error")

        # if we add a pivoted mapping for the row with the error, the error should not be shown
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": {"map_type": "row", "value_reference": 0}}),
            "connector's name",
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(*error_index)), "Not a valid number")

        # or if we add a mapping where there reading starts from a row bellow the error, the error should not be shown.
        mapping = MappingSpecModel(dict_to_map({"map_type": "ObjectClass", "read_start_row": 1}), "connector's name")
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(*error_index)), "Not a valid number")

    def test_row_type_checking_produces_error(self):
        model = MappingPreviewModel()
        model.reset_model([["1", "2.4"], ["Not a valid number", "3"]])
        model.set_type(1, value_to_convert_spec('float'), orientation=Qt.Vertical)
        error_index = (1, 0)
        self.assertEqual(len(model._row_type_errors), 1)
        self.assertEqual(model._column_type_errors, {})
        self.assertTrue(error_index in model._row_type_errors)
        # Error should only be shown if we have a pivot mapping on that row.
        self.assertEqual(model.data(model.index(*error_index)), "Not a valid number")

        # if we add mapping error should be shown.
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": {"map_type": "row", "value_reference": 1}}),
            "connector's name",
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(*error_index)), "Error")

    def test_mapping_column_colors(self):
        model = MappingPreviewModel()
        model.reset_model([[1, 2], [3, 4]])
        # column mapping
        mapping = MappingSpecModel(dict_to_map({"map_type": "ObjectClass", "name": 0}), "connector's name")
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])
        # row not showing color if the start reading row is specified
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": 0, "read_start_row": 1}), "connecto's name"
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), None)
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])
        # row not showing color if the row is pivoted
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": 0, "object": {"map_type": "row", "value_reference": 0}}),
            "connector's name",
        )
        model.set_mapping(mapping)
        self.assertNotEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])

    def test_mapping_pivoted_colors(self):
        model = MappingPreviewModel()
        model.reset_model([[1, 2], [3, 4]])
        # row mapping
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "object": {"map_type": "row", "value_reference": 0}}),
            "connector's name",
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(0, 1), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), None)
        # column not showing color if the columns is skipped
        mapping = MappingSpecModel(
            dict_to_map(
                {"map_type": "ObjectClass", "object": {"map_type": "row", "value_reference": 0}, "skip_columns": [0]}
            ),
            "connector's name",
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), None)
        self.assertEqual(model.data(model.index(0, 1), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), None)

    def test_mapping_column_and_pivot_colors(self):
        model = MappingPreviewModel()
        model.reset_model([[1, 2], [3, 4]])
        # row mapping
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": 0, "object": {"map_type": "row", "value_reference": 0}}),
            "connector's name",
        )
        model.set_mapping(mapping)
        # no color showing where row and column mapping intersect
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), None)
        self.assertEqual(model.data(model.index(0, 1), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity_class"])
        self.assertEqual(model.data(model.index(1, 1), role=Qt.BackgroundColorRole), None)


class TestMappingSpecModel(unittest.TestCase):
    def test_data_when_mapping_object_class_without_objects_or_parameters(self):
        model = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": None, "object": None}), "connector's name"
        )
        self.assertEqual(model.rowCount(), 2)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundColorRole), _ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
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
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 5)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        for row in range(5):
            index = model.index(row, 1)
            self.assertEqual(index.data(), "None")
            index = model.index(row, 2)
            self.assertEqual(index.data(), "")
            self.assertEqual(index.data(Qt.BackgroundColorRole), _ERROR_COLOR)
            self.assertTrue(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_valid_object_class_with_pivoted_parameters(self):
        array_parameter_mapping_dict = {
            "map_type": "parameter",
            "name": 2,
            "parameter_type": "array",
            "value": {"map_type": "row", "reference": 0},
        }
        mapping_dict = {"map_type": "ObjectClass", "name": 0, "objects": 1, "parameters": array_parameter_mapping_dict}
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 4)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Pivoted")
        index = model.index(0, 2)
        self.assertEqual(index.data(), 0)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), 1)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(), "Pivoted values")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
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
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 5)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "class_name")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), "object_name")
        index = model.index(2, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 99)
        index = model.index(3, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 23)
        index = model.index(4, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
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
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 6)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Object class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object names")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter index 2")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "Constant")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(3, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(4, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(5, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "class_name")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), "object_name")
        index = model.index(2, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 99)
        index = model.index(3, 2)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        self.assertEqual(index.data(), 23)
        index = model.index(4, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(5, 2)
        self.assertEqual(index.data(), "sixth column")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))

    def test_data_when_mapping_relationship_class_without_objects_or_parameters(self):
        model = MappingSpecModel(
            dict_to_map({"map_type": "RelationshipClass", "name": None, "object_classes": None, "object": None}),
            "connector's name",
        )
        self.assertEqual(model.rowCount(), 3)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Relationship class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object class names 1")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object names 1")
        index = model.index(0, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(1, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(2, 1)
        self.assertEqual(index.data(), "None")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundColorRole), _ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundColorRole), _ERROR_COLOR)
        self.assertTrue(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
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
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 6)
        self.assertEqual(model.columnCount(), 3)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "Relationship class names")
        index = model.index(1, 0)
        self.assertEqual(index.data(), "Object class names 1")
        index = model.index(2, 0)
        self.assertEqual(index.data(), "Object names 1")
        index = model.index(3, 0)
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(4, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(5, 0)
        self.assertEqual(index.data(), "Parameter index 1")
        for row in range(6):
            index = model.index(row, 1)
            self.assertEqual(index.data(), "None")
            index = model.index(row, 2)
            self.assertEqual(index.data(), "")
            self.assertEqual(index.data(Qt.BackgroundColorRole), _ERROR_COLOR)
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
        model = MappingSpecModel(dict_to_map(mapping_dict), "connector's name")
        self.assertEqual(model.rowCount(), 8)
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
        self.assertEqual(index.data(), "Parameter names")
        index = model.index(6, 0)
        self.assertEqual(index.data(), "Parameter values")
        index = model.index(7, 0)
        self.assertEqual(index.data(), "Parameter index 1")
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
        self.assertEqual(index.data(), "Column")
        index = model.index(6, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(7, 1)
        self.assertEqual(index.data(), "Column")
        index = model.index(0, 2)
        self.assertEqual(index.data(), "relationship_class name")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(1, 2)
        self.assertEqual(index.data(), "column header")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(2, 2)
        self.assertEqual(index.data(), "second class")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(3, 2)
        self.assertEqual(index.data(), 21)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(4, 2)
        self.assertEqual(index.data(), 22)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(5, 2)
        self.assertEqual(index.data(), 99)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(6, 2)
        self.assertEqual(index.data(), 23)
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))
        index = model.index(7, 2)
        self.assertEqual(index.data(), "fifth column")
        self.assertEqual(index.data(Qt.BackgroundColorRole), None)
        self.assertFalse(index.data(Qt.ToolTipRole))


if __name__ == '__main__':
    unittest.main()
