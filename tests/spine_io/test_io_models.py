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

import csv
import os.path
from tempfile import TemporaryDirectory
import unittest
from spinetoolbox.spine_io.io_models import MappingPreviewModel, MappingSpecModel, _MAPPING_COLORS
from spinetoolbox.spine_io.type_conversion import value_to_convert_spec
from spinedb_api import Duration, DateTime, dict_to_map
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
            dict_to_map({"map_type": "ObjectClass", "name": {"map_type": "row", "value_reference": 0}})
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(*error_index)), "Not a valid number")

        # or if we add a mapping where there reading starts from a row bellow the error, the error should not be shown.
        mapping = MappingSpecModel(dict_to_map({"map_type": "ObjectClass", "read_start_row": 1}))
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
            dict_to_map({"map_type": "ObjectClass", "name": {"map_type": "row", "value_reference": 1}})
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(*error_index)), "Error")

    def test_mapping_column_colors(self):
        model = MappingPreviewModel()
        model.reset_model([[1, 2], [3, 4]])
        # column mapping
        mapping = MappingSpecModel(dict_to_map({"map_type": "ObjectClass", "name": 0}))
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])
        # row not showing color if the start reading row is specified
        mapping = MappingSpecModel(dict_to_map({"map_type": "ObjectClass", "name": 0, "read_start_row": 1}))
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), None)
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])
        # row not showing color if the row is pivoted
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "name": 0, "object": {"map_type": "row", "value_reference": 0}})
        )
        model.set_mapping(mapping)
        self.assertNotEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])

    def test_mapping_pivoted_colors(self):
        model = MappingPreviewModel()
        model.reset_model([[1, 2], [3, 4]])
        # row mapping
        mapping = MappingSpecModel(
            dict_to_map({"map_type": "ObjectClass", "object": {"map_type": "row", "value_reference": 0}})
        )
        model.set_mapping(mapping)
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(0, 1), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), None)
        # column not showing color if the columns is skipped
        mapping = MappingSpecModel(
            dict_to_map(
                {"map_type": "ObjectClass", "object": {"map_type": "row", "value_reference": 0}, "skip_columns": [0]}
            )
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
            dict_to_map({"map_type": "ObjectClass", "name": 0, "object": {"map_type": "row", "value_reference": 0}})
        )
        model.set_mapping(mapping)
        # no color showing where row and column mapping intersect
        self.assertEqual(model.data(model.index(0, 0), role=Qt.BackgroundColorRole), None)
        self.assertEqual(model.data(model.index(0, 1), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity"])
        self.assertEqual(model.data(model.index(1, 0), role=Qt.BackgroundColorRole), _MAPPING_COLORS["entity class"])
        self.assertEqual(model.data(model.index(1, 1), role=Qt.BackgroundColorRole), None)


if __name__ == '__main__':
    unittest.main()
