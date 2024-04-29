######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Items.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for FileListModel class."""
import unittest
from PySide6.QtWidgets import QApplication
from pathlib import Path
from spinetoolbox.mvcmodels.file_list_models import FileListModel
from spine_engine.project_item.project_item_resource import file_resource, file_resource_in_pack


class TestFileListModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._model = FileListModel()

    def tearDown(self):
        self._model.deleteLater()

    def test_duplicate_files(self):
        dupe1 = file_resource("item name", str(Path.cwd() / "path" / "to" / "other" / "file" / "A1"), "file label")
        dupe2 = file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file"))
        single_resources = [
            dupe1,
            dupe1,
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "A1"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "Worcestershire"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "file" / "Sriracha"), "file label"),
            file_resource("some name", str(Path.cwd() / "path" / "to" / "other" / "file" / "B12"), "file label"),
            file_resource("item name", str(Path.cwd() / "path" / "to" / "other" / "file" / "Sriracha"), "some label"),
        ]
        pack_resources = [
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "other" / "pack_file")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "some" / "pack_file")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file2")),
            dupe2,
            file_resource_in_pack("some name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file21")),
            file_resource_in_pack("item name", "pack label", str(Path.cwd() / "path" / "to" / "pack_file3")),
            dupe2,
        ]
        self._model.update(single_resources + pack_resources)
        results = self._model.duplicate_paths()
        expected = set()
        expected.add(str(dupe1.path))
        expected.add(str(dupe2.path))
        self.assertEqual(results, expected)
