######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for TreeViewForm and GraphViewForm classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
from unittest import mock
import logging
import os
import sys
from PySide2.QtCore import QSettings
from PySide2.QtWidgets import QApplication, QToolButton
from widgets.tree_view_widget import TreeViewForm
from widgets.custom_qdialog import AddObjectClassesDialog


class TestAddItemsDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of TreeViewForm class."""
        with mock.patch("project.SpineToolboxProject") as mock_project, mock.patch(
            "spinedb_api.DiffDatabaseMapping"
        ) as mock_db_map:
            mock_project._toolbox._qsettings = QSettings("SpineProject", "Spine Toolbox")
            mock_project._toolbox._qsettings.setValue("appSettings/commitAtExit", "0")
            self.tree_view_form = TreeViewForm(mock_project, mock_db=mock_db_map)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.tree_view_form.close()
        self.tree_view_form.deleteLater()
        self.tree_view_form = None
        try:
            os.remove('mock_db.sqlite')
        except OSError:
            pass

    @unittest.skip("Test currently broken.")
    def test_empty_row_has_remove_row_button(self):
        """Test that the model is loaded with an empty row, and this row has a button to remove it in the last column.
        """
        dialog = AddObjectClassesDialog(self.tree_view_form)
        self.assertEqual(dialog.model.rowCount(), 1)
        self.assertEqual(dialog.model.columnCount(), 4)
        button_index = dialog.model.index(0, 3)
        button = dialog.table_view.indexWidget(button_index)
        self.assertTrue(isinstance(button, QToolButton))

    @unittest.skipIf(sys.platform.startswith("win"), "QApplication.clipboard() tests do not work on Windows")
    def test_paste_data(self):
        """Test that data is pasted and the model grows.
        """
        dialog = AddObjectClassesDialog(self.tree_view_form)
        self.assertEqual(dialog.model.rowCount(), 1)
        self.assertEqual(dialog.model.columnCount(), 3)
        model = dialog.model
        view = dialog.table_view
        header_index = model.horizontal_header_labels().index
        clipboard_text = "fish\ndog\ncat\nmouse\noctopus\nchicken\n"
        QApplication.clipboard().setText(clipboard_text)
        obj_cls_name_index = model.index(0, header_index('object class name'))
        view.setCurrentIndex(obj_cls_name_index)
        view.paste()
        self.assertEqual(model.rowCount(), 7)
        self.assertEqual(model.index(0, header_index('object class name')).data(), 'fish')
        self.assertEqual(model.index(1, header_index('object class name')).data(), 'dog')
        self.assertEqual(model.index(2, header_index('object class name')).data(), 'cat')
        self.assertEqual(model.index(3, header_index('object class name')).data(), 'mouse')
        self.assertEqual(model.index(4, header_index('object class name')).data(), 'octopus')
        self.assertEqual(model.index(5, header_index('object class name')).data(), 'chicken')


if __name__ == '__main__':
    unittest.main()
