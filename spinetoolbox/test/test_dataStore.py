######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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
import shutil
import os
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import Qt
from data_store import DataStore
from graphics_items import DataStoreImage
from ui_main import ToolboxUI
from PySide2.QtWidgets import QMessageBox
from spinedatabase_api import create_new_spine_database


class TestDataStore(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')

    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of ToolboxUI class.
        """
        # # Set logging level to Error to silence "Logging level: All messages" print
        logging.disable(level=logging.ERROR)  # Disable logging
        self.toolbox = ToolboxUI()
        self.toolbox.create_project("UnitTest Project", "")
        logging.disable(level=logging.NOTSET)  # Enable logging

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        shutil.rmtree(self.toolbox.project().project_dir)
        try:
            os.remove(self.toolbox.project().path)
        except OSError:
            pass
        self.toolbox = None

    def test_create_new_spine_database(self):
        """Test that a new Spine database is created when clicking on Spine-icon tool button.
        """
        with mock.patch("data_store.QFileDialog") as mock_file_dialog:
            data_store = DataStore(self.toolbox, "DS", "", dict(), 0, 0)
            file_path = os.path.join(data_store.data_dir, "mock_db.sqlite")
            mock_file_dialog.getSaveFileName.return_value = [file_path]
            data_store.activate()
            self.toolbox.ui.toolButton_new_spine.click()
            self.assertTrue(os.path.isfile(file_path), "mock_db.sqlite file not found.")
            sqlite_file = self.toolbox.ui.lineEdit_SQLite_file.text()
            self.assertEqual(sqlite_file, file_path)
            database = self.toolbox.ui.lineEdit_database.text()
            basename = os.path.basename(file_path)
            self.assertEqual(database, basename)

    def test_load_reference(self):
        """Test that reference is loaded into selections on Data Store creation,
        and then shown in the ui when Data Store is activated.
        """
        # FIXME: For now it only tests sqlite references
        file_path = os.path.join(self.toolbox.project().project_dir, "mock_db.sqlite")
        if not os.path.exists(file_path):
            with open(file_path, 'w'): pass
        url = "sqlite:///" + file_path
        create_new_spine_database(url)
        reference = dict(database="foo", username="bar", url=url)
        data_store = DataStore(self.toolbox, "DS", "", reference, 0, 0)
        data_store.activate()
        dialect = self.toolbox.ui.comboBox_dialect.currentText()
        database = self.toolbox.ui.lineEdit_database.text()
        username = self.toolbox.ui.lineEdit_username.text()
        self.assertEqual(dialect, 'sqlite')
        self.assertEqual(database, 'foo')
        self.assertEqual(username, 'bar')

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when deactivating a Data Store and activating it again.
        """
        # FIXME: For now it only tests the mysql dialect
        data_store = DataStore(self.toolbox, "DS", "", dict(), 0, 0)
        data_store.activate()
        self.toolbox.ui.comboBox_dialect.setCurrentText('mysql')
        self.toolbox.ui.lineEdit_host.setText('localhost')
        self.toolbox.ui.lineEdit_port.setText('8080')
        self.toolbox.ui.lineEdit_database.setText('foo')
        self.toolbox.ui.lineEdit_username.setText('bar')
        data_store.deactivate()
        data_store.activate()
        dialect = self.toolbox.ui.comboBox_dialect.currentText()
        host = self.toolbox.ui.lineEdit_host.text()
        port = self.toolbox.ui.lineEdit_port.text()
        database = self.toolbox.ui.lineEdit_database.text()
        username = self.toolbox.ui.lineEdit_username.text()
        self.assertEqual(dialect, 'mysql')
        self.assertEqual(host, 'localhost')
        self.assertEqual(port, '8080')
        self.assertEqual(database, 'foo')
        self.assertEqual(username, 'bar')

    def test_copy_db_url_to_clipboard(self):
        """Test that the database url from current selections is copied to clipboard.
        """
        # First create a DS with an sqlite db reference
        file_path = os.path.join(self.toolbox.project().project_dir, "mock_db.sqlite")
        if not os.path.exists(file_path):
            with open(file_path, 'w'): pass
        url = "sqlite:///" + file_path
        create_new_spine_database(url)
        reference = dict(database="foo", username="bar", url=url)
        data_store = DataStore(self.toolbox, "DS", "", reference, 0, 0)
        data_store.activate()
        self.toolbox.ui.toolButton_copy_db_url.click()
        clipboard_text = QApplication.clipboard().text()
        self.assertEqual(clipboard_text, url)


if __name__ == '__main__':
    unittest.main()
