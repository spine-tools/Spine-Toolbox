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
Contains unit tests for Import editor's MappingListModel.
"""
import unittest
from PySide2.QtWidgets import QUndoStack
from spinedb_api import ObjectClassMapping
from spinetoolbox.import_editor.mvcmodels.mapping_list_model import MappingListModel
from spinetoolbox.import_editor.mvcmodels.mapping_specification_model import MappingSpecificationModel


class TestMappingListModel(unittest.TestCase):
    def test_construction(self):
        undo_stack = QUndoStack()
        specification = MappingSpecificationModel("table_name", "mapping_name", ObjectClassMapping(), undo_stack)
        model = MappingListModel([specification], "table", undo_stack)
        self.assertEqual(model.rowCount(), 1)
        index = model.index(0, 0)
        self.assertEqual(index.data(), "mapping_name")

    def test_setData(self):
        undo_stack = QUndoStack()
        specification = MappingSpecificationModel("table_name", "mapping_name", ObjectClassMapping(), undo_stack)
        model = MappingListModel([specification], "table", undo_stack)
        index = model.index(0, 0)
        model.setData(index, "new_name")
        index = model.index(0, 0)
        self.assertEqual(index.data(), "new_name")


if __name__ == '__main__':
    unittest.main()
