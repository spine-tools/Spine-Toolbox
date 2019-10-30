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
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.tree_view_widget import TreeViewForm
from spinetoolbox.widgets.custom_qdialog import AddObjectClassesDialog


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
        with mock.patch("spinetoolbox.project.SpineToolboxProject") as mock_project, mock.patch(
            "spinedb_api.DiffDatabaseMapping"
        ) as mock_db_map, mock.patch("spinetoolbox.widgets.tree_view_widget.TreeViewForm.restore_ui"):
            mock_db_map.codename = "mock_db"
            self.tree_view_form = TreeViewForm(mock_project, mock_db_map)
            self.mock_db_mngr = mock_project.db_mngr
            self.mock_db_map = mock_db_map

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.widgets.data_store_widget.DataStoreForm._prompt_close_and_commit"
        ) as mock_p_c_and_c, mock.patch(
            "spinetoolbox.widgets.tree_view_widget.TreeViewForm.save_window_state"
        ) as mock_save_w_s:
            mock_p_c_and_c.return_value = True
            self.tree_view_form.close()
            mock_p_c_and_c.assert_called_once()
            mock_save_w_s.assert_called_once()
        self.tree_view_form.deleteLater()
        self.tree_view_form = None
        try:
            os.remove('mock_db.sqlite')
        except OSError:
            pass

    def test_add_object_classes(self):
        """Test object classes are added through the manager when accepting the dialog."""
        dialog = AddObjectClassesDialog(self.tree_view_form, self.mock_db_mngr, self.mock_db_map)
        model = dialog.model
        header = model.header
        model.fetchMore()
        self.assertEqual(header, ['object class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object class name', 'databases')]
        values = ['fish', 'mock_db']
        model.batch_set_data(indexes, values)

        def _add_object_classes(db_map_data):
            self.assertTrue(self.mock_db_map in db_map_data)
            data = db_map_data[self.mock_db_map]
            self.assertEqual(len(data), 1)
            item = data[0]
            self.assertTrue("name" in item)
            self.assertEqual(item["name"], "fish")

        self.mock_db_mngr.add_object_classes.side_effect = _add_object_classes
        dialog.accept()
        self.mock_db_mngr.add_object_classes.assert_called_once()

    def test_do_not_add_object_classes_with_invalid_db(self):
        """Test object classes aren't added when the database is not correct."""
        dialog = AddObjectClassesDialog(self.tree_view_form, self.mock_db_mngr, self.mock_db_map)
        model = dialog.model
        header = model.header
        model.fetchMore()
        self.assertEqual(header, ['object class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object class name', 'databases')]
        values = ['fish', 'gibberish']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self.mock_db_mngr.add_object_classes.assert_not_called()


if __name__ == '__main__':
    unittest.main()
