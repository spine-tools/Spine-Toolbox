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
Unit tests for the helpers module.

:authors: A. Soininen (VTT)
:date:   23.3.2020
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from spinetoolbox.helpers import first_non_null, interpret_icon_id, make_icon_id, rename_dir


class TestHelpers(unittest.TestCase):
    def test_make_icon_id(self):
        icon_id = make_icon_id(3, 7)
        self.assertEqual(icon_id, 3 + (7 << 16))

    def test_interpret_icon_id(self):
        icon_code, color_code = interpret_icon_id(None)
        self.assertEqual(icon_code, 0xF1B2)
        self.assertEqual(color_code, 0)
        icon_code, color_code = interpret_icon_id(3 + (7 << 16))
        self.assertEqual(icon_code, 3)
        self.assertEqual(color_code, 7)

    def test_first_non_null(self):
        self.assertEqual(first_non_null([23]), 23)
        self.assertEqual(first_non_null([None, 23]), 23)

    def test_rename_dir(self):
        with TemporaryDirectory() as temp_dir:
            old_dir = Path(temp_dir, "old directory")
            old_dir.mkdir()
            file_in_dir = Path(old_dir, "file.fff")
            file_in_dir.touch()
            new_dir = Path(temp_dir, "new directory")
            logger = MagicMock()
            self.assertTrue(rename_dir(str(old_dir), str(new_dir), logger))
            self.assertFalse(old_dir.exists())
            self.assertTrue(new_dir.exists())
            files_in_new_dir = [path for path in new_dir.iterdir()]
            self.assertEqual(files_in_new_dir, [Path(new_dir, "file.fff")])

    def test_rename_dir_fails_if_target_exists(self):
        with TemporaryDirectory() as temp_dir:
            old_dir = Path(temp_dir, "old directory")
            old_dir.mkdir()
            new_dir = Path(temp_dir, "new directory")
            new_dir.mkdir()
            logger = MagicMock()
            self.assertFalse(rename_dir(str(old_dir), str(new_dir), logger))
            logger.information_box.emit.assert_called_once()
            self.assertTrue(old_dir.exists())
            self.assertTrue(new_dir.exists())


if __name__ == '__main__':
    unittest.main()
