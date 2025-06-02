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

"""Unit tests for Database editor's ``helpers`` module."""
import unittest
from unittest import mock
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from spinetoolbox.spine_db_editor.helpers import (
    bool_to_string,
    group_to_string,
    input_string_to_int,
    optional_to_string,
    parameter_value_to_string,
    string_to_bool,
    string_to_display_icon,
    string_to_group,
    string_to_parameter_value,
)


class TestStringToDisplayIcon(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertEqual(string_to_display_icon("23"), 23)
        self.assertIsNone(string_to_display_icon(""))
        self.assertIsNone(string_to_display_icon("rubbish"))


class TestBoolToString(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertEqual(bool_to_string(True), "true")
        self.assertEqual(bool_to_string(False), "false")


class TestStringToBool(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertTrue(string_to_bool("true"))
        self.assertTrue(string_to_bool("TRUE"))
        self.assertFalse(string_to_bool("false"))
        self.assertFalse(string_to_bool(""))
        self.assertTrue(string_to_bool(b"true"))
        self.assertFalse(string_to_bool(b"false"))


class TestOptionalToString(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertIsNone(optional_to_string(None))
        self.assertEqual(optional_to_string(23), "23")


class TestGroupsToString(unittest.TestCase):
    def test_functionality(self):
        self.assertIsNone(group_to_string(()))
        self.assertEqual(group_to_string(("item1",)), "item1")
        self.assertEqual(group_to_string(("item1", "item2")), "item1" + DB_ITEM_SEPARATOR + "item2")


class TestStringToGroup(unittest.TestCase):
    def test_functionality(self):
        self.assertEqual(string_to_group(""), ())
        self.assertEqual(string_to_group("item"), ("item",))
        self.assertEqual(string_to_group("item,"), ("item",))
        self.assertEqual(string_to_group("item1, item2"), ("item1", "item2"))
        self.assertEqual(string_to_group("item1" + DB_ITEM_SEPARATOR + "item2"), ("item1", "item2"))


class TestParameterValueToString(unittest.TestCase):
    def test_non_numeric_values(self):
        self.assertEqual(parameter_value_to_string("is_string"), "is_string")
        self.assertEqual(parameter_value_to_string(True), "true")
        self.assertEqual(parameter_value_to_string(False), "false")

    def test_numeric_values(self):
        self.assertEqual(parameter_value_to_string(23), str(23))
        with mock.patch("spinetoolbox.spine_db_editor.helpers.locale.str") as mock_str:
            mock_str.side_effect = lambda x: str(x).replace(".", ",")
            self.assertEqual(parameter_value_to_string(2.3), "2,3")


class TestStringToParameterValue(unittest.TestCase):
    def test_booleans(self):
        self.assertTrue(string_to_parameter_value("true"))
        self.assertFalse(string_to_parameter_value("false"))

    def test_non_numeric_values(self):
        self.assertEqual(string_to_parameter_value("random text"), "random text")

    def test_numeric_values(self):
        with mock.patch("spinetoolbox.spine_db_editor.helpers.locale.atof") as mock_atof:
            mock_atof.side_effect = lambda x: float(x.replace(",", "."))
            self.assertEqual(string_to_parameter_value("2,3"), 2.3)
            self.assertEqual(string_to_parameter_value("2.3"), 2.3)
        self.assertEqual(string_to_parameter_value("2.3"), 2.3)


class TestInputStringToInt(unittest.TestCase):
    def test_numeric_values(self):
        self.assertEqual(input_string_to_int("23"), 23)
        self.assertEqual(input_string_to_int("23.0"), 23)
        self.assertEqual(input_string_to_int("2.49"), 2)
        self.assertEqual(input_string_to_int("2.51"), 3)
        with mock.patch("spinetoolbox.spine_db_editor.helpers.locale.atof") as mock_atof:
            mock_atof.side_effect = lambda x: float(x.replace(",", "."))
            self.assertEqual(input_string_to_int("2,3"), 2)

    def test_raises_value_error(self):
        with self.assertRaises(ValueError):
            input_string_to_int("aaa")


if __name__ == "__main__":
    unittest.main()
