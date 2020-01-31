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
Unit tests for the Excel export module.

:author: P. Vennström (VTT), A. Soininen (VTT)
:date:   31.1.2020
"""

import unittest
from spinetoolbox.spine_io.exporters.excel import _unstack_list_of_tuples


class TestExcelExport(unittest.TestCase):
    def test_unstack_list_of_tuples(self):
        """Test transformation of unpivoted table into a pivoted table"""

        fieldnames = ["col1", "col2", "pivot_col1", "pivot_col2"]
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0, 1]
        value_name_col = 2
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot_col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot_col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot_col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot_col2", "pivot_col2_v3"],
        ]

        data_out = [
            ["col1_v1", "col2_v1", "pivot_col1_v1", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col1_v2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", None, "pivot_col2_v3"],
        ]

        test_data_out, new_headers = _unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(test_data_out, data_out)
        self.assertEqual(new_headers, fieldnames)

    def test_unstack_list_of_tuples_with_bad_names(self):
        """
        Test transformation of unpivoted table into a pivoted table
        when column to pivot has name not supported by namedtuple
        """

        fieldnames = ["col1", "col2", "pivot col1", "pivot col2"]
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0, 1]
        value_name_col = 2
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot col2", "pivot_col2_v3"],
        ]

        data_out = [
            ["col1_v1", "col2_v1", "pivot_col1_v1", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col1_v2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", None, "pivot_col2_v3"],
        ]

        test_data_out, new_headers = _unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(test_data_out, data_out)
        self.assertEqual(new_headers, fieldnames)

    def test_unstack_list_of_tuples_multiple_pivot_cols(self):
        """
        Test transformation of unpivoted table into a pivoted table
        with multiple pivot columns.
        """
        headers = ["col1", "col2", "parameter", "value"]
        key_cols = [0]
        value_name_col = [1, 2]
        value_col = 3
        data_in = [
            ["col1_v1", "col2_v1", "pivot_col1", "pivot_col1_v1"],
            ["col1_v2", "col2_v2", "pivot_col1", "pivot_col1_v2"],
            ["col1_v1", "col2_v1", "pivot_col2", "pivot_col2_v1"],
            ["col1_v2", "col2_v2", "pivot_col2", "pivot_col2_v2"],
            ["col1_v3", "col2_v3", "pivot_col2", "pivot_col2_v3"],
        ]

        headers_out = [
            "col1",
            ("col2_v1", "pivot_col1"),
            ("col2_v1", "pivot_col2"),
            ("col2_v2", "pivot_col1"),
            ("col2_v2", "pivot_col2"),
            ("col2_v3", "pivot_col2"),
        ]
        data_out = [
            ["col1_v1", "pivot_col1_v1", "pivot_col2_v1", None, None, None],
            ["col1_v2", None, None, "pivot_col1_v2", "pivot_col2_v2", None],
            ["col1_v3", None, None, None, None, "pivot_col2_v3"],
        ]

        test_data_out, test_header_out = _unstack_list_of_tuples(data_in, headers, key_cols, value_name_col, value_col)

        self.assertEqual(data_out, test_data_out)
        self.assertEqual(headers_out, test_header_out)


if __name__ == '__main__':
    unittest.main()
