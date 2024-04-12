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
from spinetoolbox.spine_db_editor.helpers import string_to_bool, string_to_display_icon


class TestStringToDisplayIcon(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertEqual(string_to_display_icon("23"), 23)
        self.assertIsNone(string_to_display_icon(""))
        self.assertIsNone(string_to_display_icon("rubbish"))


class TestStringToBool(unittest.TestCase):
    def test_converts_correctly(self):
        self.assertTrue(string_to_bool("true"))
        self.assertTrue(string_to_bool("TRUE"))
        self.assertFalse(string_to_bool("false"))
        self.assertFalse(string_to_bool(""))


if __name__ == "__main__":
    unittest.main()
