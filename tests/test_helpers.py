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
from sys import platform
from pathlib import Path
from tempfile import gettempdir, NamedTemporaryFile, TemporaryDirectory
import unittest
from unittest.mock import MagicMock
from spinetoolbox.helpers import (
    deserialize_path,
    rename_dir,
    serialize_path,
    serialize_url,
    first_non_null,
    interpret_icon_id,
    make_icon_id,
)


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

    def test_serialize_path_makes_relative_paths_from_paths_in_project_dir(self):
        with TemporaryDirectory() as path:
            project_dir = gettempdir()
            serialized = serialize_path(path, project_dir)
            expected_path = str(Path(path).relative_to(project_dir).as_posix())
            self.assertEqual(serialized, {"type": "path", "relative": True, "path": expected_path})

    def test_serialize_path_makes_absolute_paths_from_paths_not_in_project_dir(self):
        with TemporaryDirectory() as project_dir:
            with TemporaryDirectory() as path:
                serialized = serialize_path(path, project_dir)
                expected_path = str(Path(path).as_posix())
                self.assertEqual(serialized, {"type": "path", "relative": False, "path": expected_path})

    def test_serialize_url_makes_file_path_in_project_dir_relative(self):
        with NamedTemporaryFile(mode="r") as temp_file:
            url = "sqlite:///" + str(Path(temp_file.name).as_posix())
            project_dir = gettempdir()
            expected_path = str(Path(temp_file.name).relative_to(project_dir).as_posix())
            serialized = serialize_url(url, project_dir)
            self.assertEqual(
                serialized, {"type": "file_url", "relative": True, "path": expected_path, "scheme": "sqlite"}
            )

    def test_serialize_url_keeps_file_path_not_in_project_dir_absolute(self):
        with TemporaryDirectory() as project_dir:
            with NamedTemporaryFile(mode="r") as temp_file:
                expected_path = str(Path(temp_file.name).as_posix())
                if platform == "win32":
                    url = "sqlite:///" + expected_path
                else:
                    url = "sqlite://" + expected_path
                serialized = serialize_url(url, project_dir)
                self.assertEqual(
                    serialized, {"type": "file_url", "relative": False, "path": expected_path, "scheme": "sqlite"}
                )

    def test_serialize_url_with_non_file_urls(self):
        project_dir = gettempdir()
        url = "http://www.spine-model.org/"
        serialized = serialize_url(url, project_dir)
        self.assertEqual(serialized, {"type": "url", "relative": False, "path": url})

    def test_serialize_relative_url_with_query(self):
        with NamedTemporaryFile(mode="r") as temp_file:
            url = "sqlite:///" + str(Path(temp_file.name).as_posix()) + "?filter=kol"
            project_dir = gettempdir()
            expected_path = str(Path(temp_file.name).relative_to(project_dir).as_posix())
            serialized = serialize_url(url, project_dir)
            self.assertEqual(
                serialized,
                {
                    "type": "file_url",
                    "relative": True,
                    "path": expected_path,
                    "scheme": "sqlite",
                    "query": "filter=kol",
                },
            )

    def test_deserialize_path_with_relative_path(self):
        project_dir = gettempdir()
        serialized = {"type": "path", "relative": True, "path": "subdir/file.fat"}
        deserialized = deserialize_path(serialized, project_dir)
        self.assertEqual(deserialized, str(Path(project_dir, "subdir", "file.fat")))

    def test_deserialize_path_with_absolute_path(self):
        with TemporaryDirectory() as project_dir:
            serialized = {"type": "path", "relative": False, "path": str(Path(gettempdir(), "file.fat").as_posix())}
            deserialized = deserialize_path(serialized, project_dir)
            self.assertEqual(deserialized, str(Path(gettempdir(), "file.fat")))

    def test_deserialize_path_with_relative_file_url(self):
        project_dir = gettempdir()
        serialized = {"type": "file_url", "relative": True, "path": "subdir/database.sqlite", "scheme": "sqlite"}
        deserialized = deserialize_path(serialized, project_dir)
        expected = "sqlite:///" + str(Path(project_dir, "subdir", "database.sqlite"))
        self.assertEqual(deserialized, expected)

    def test_deserialize_path_with_absolute_file_url(self):
        with TemporaryDirectory() as project_dir:
            path = str(Path(gettempdir(), "database.sqlite").as_posix())
            serialized = {"type": "file_url", "relative": False, "path": path, "scheme": "sqlite"}
            deserialized = deserialize_path(serialized, project_dir)
            expected = "sqlite:///" + str(Path(gettempdir(), "database.sqlite"))
            self.assertEqual(deserialized, expected)

    def test_deserialize_path_with_non_file_url(self):
        project_dir = gettempdir()
        serialized = {"type": "url", "path": "http://www.spine-model.org/"}
        deserialized = deserialize_path(serialized, project_dir)
        self.assertEqual(deserialized, "http://www.spine-model.org/")

    def test_deserialize_relative_url_with_query(self):
        project_dir = gettempdir()
        serialized = {
            "type": "file_url",
            "relative": True,
            "path": "subdir/database.sqlite",
            "scheme": "sqlite",
            "query": "filter=kax",
        }
        deserialized = deserialize_path(serialized, project_dir)
        expected = "sqlite:///" + str(Path(project_dir, "subdir", "database.sqlite")) + "?filter=kax"
        self.assertEqual(deserialized, expected)


if __name__ == '__main__':
    unittest.main()
