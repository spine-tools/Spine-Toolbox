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
Unit tests for DataStore class.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
import shutil
import os
from unittest import mock
import logging
import sys
from test.mock_helpers import MockQWidget, qsettings_value_side_effect
from PySide2.QtWidgets import QApplication, QWidget
from ui_main import ToolboxUI
from spinedb_api import create_new_spine_database


# noinspection PyUnusedLocal
class TestDataStore(unittest.TestCase):
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
        """Overridden method. Runs before each test. Makes instance of ToolboxUI class.
        Note: unittest_settings.conf is not actually saved because ui_main.closeEvent()
        is not called in tearDown().
        """
        with mock.patch("ui_main.JuliaREPLWidget") as mock_julia_repl, mock.patch(
            "ui_main.PythonReplWidget"
        ) as mock_python_repl, mock.patch("ui_main.QSettings.value") as mock_qsettings_value:
            # Replace Julia REPL Widget with a QWidget so that the DeprecationWarning from qtconsole is not printed
            mock_julia_repl.return_value = QWidget()
            mock_python_repl.return_value = MockQWidget()
            mock_qsettings_value.side_effect = qsettings_value_side_effect
            self.toolbox = ToolboxUI()
            self.toolbox.create_project("UnitTest Project", "")
            self.ds_properties_ui = self.toolbox.categories["Data Stores"]["properties_ui"]

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        try:
            shutil.rmtree(self.toolbox.project().project_dir)  # Remove project directory
        except OSError:
            pass
        try:
            os.remove(self.toolbox.project().path)  # Remove project file
        except OSError:
            pass
        self.toolbox.deleteLater()
        self.toolbox = None
        self.ds_properties_ui = None

    def test_create_new_empty_spine_database(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with an empty Data Store and 'for Spine model' checkbox UNCHECKED.
        """
        item = dict(name="DS", description="", x=0, y=0, url=None, reference=None)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        dialect_box = self.ds_properties_ui.comboBox_dialect
        db_line_edit = self.ds_properties_ui.lineEdit_database
        self.assertEqual(dialect_box.currentText(), "")
        self.assertEqual(db_line_edit.text(), "")
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        self.assertEqual(dialect_box.currentText(), "sqlite")
        expected_db_path = os.path.join(data_store.data_dir, data_store.name + ".sqlite")
        self.assertEqual(expected_db_path, db_line_edit.text())
        self.assertTrue(os.path.exists(db_line_edit.text()))
        self.assertTrue(os.path.isfile(db_line_edit.text()))

    def test_create_new_empty_spine_database2(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with a Data Store that already has an URL. Checkbox 'for Spine model' UNCHECKED.
        """
        # Set the url together with the item
        url = dict(dialect="sqlite", database="temp.sqlite")
        item = dict(name="DS", description="", x=0, y=0, url=url)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        dialect_box = self.ds_properties_ui.comboBox_dialect
        db_line_edit = self.ds_properties_ui.lineEdit_database
        self.assertEqual(dialect_box.currentText(), "sqlite")
        self.assertEqual(db_line_edit.text(), "temp.sqlite")
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        self.assertEqual(dialect_box.currentText(), "sqlite")
        expected_db_path = os.path.join(data_store.data_dir, "temp.sqlite")
        self.assertEqual(expected_db_path, db_line_edit.text())
        self.assertTrue(os.path.exists(db_line_edit.text()))
        self.assertTrue(os.path.isfile(db_line_edit.text()))

    def test_create_new_spine_database_for_spine_model(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with an empty Data Store and 'for Spine model' checkbox CHECKED.
        """
        item = dict(name="DS", description="", x=0, y=0, url=None, reference=None)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        dialect_box = self.ds_properties_ui.comboBox_dialect
        db_line_edit = self.ds_properties_ui.lineEdit_database
        self.assertEqual(dialect_box.currentText(), "")
        self.assertEqual(db_line_edit.text(), "")
        # Check CheckBox
        self.ds_properties_ui.checkBox_for_spine_model.setChecked(True)
        self.assertTrue(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        self.assertEqual(dialect_box.currentText(), "sqlite")
        expected_db_path = os.path.join(data_store.data_dir, data_store.name + ".sqlite")
        self.assertEqual(expected_db_path, db_line_edit.text())
        self.assertTrue(os.path.exists(db_line_edit.text()))
        self.assertTrue(os.path.isfile(db_line_edit.text()))

    def test_create_new_spine_database_for_spine_model2(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with a Data Store that already has an URL. Checkbox 'for Spine model' CHECKED.
        """
        # Set the url together with the item
        url = dict(dialect="sqlite", database="temp.sqlite")
        item = dict(name="DS", description="", x=0, y=0, url=url)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        dialect_box = self.ds_properties_ui.comboBox_dialect
        db_line_edit = self.ds_properties_ui.lineEdit_database
        self.assertEqual(dialect_box.currentText(), "sqlite")
        self.assertEqual(db_line_edit.text(), "temp.sqlite")
        # Check CheckBox
        self.ds_properties_ui.checkBox_for_spine_model.setChecked(True)
        self.assertTrue(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        self.assertEqual(dialect_box.currentText(), "sqlite")
        expected_db_path = os.path.join(data_store.data_dir, "temp.sqlite")
        self.assertEqual(expected_db_path, db_line_edit.text())
        self.assertTrue(os.path.exists(db_line_edit.text()))
        self.assertTrue(os.path.isfile(db_line_edit.text()))

    def test_load_reference(self):
        """Test that reference is loaded into selections on Data Store creation,
        and then shown in the ui when Data Store is activated.
        """
        # FIXME: For now it only tests sqlite references
        file_path = os.path.join(self.toolbox.project().project_dir, "mock_db.sqlite")
        if not os.path.exists(file_path):
            with open(file_path, 'w'):
                pass
        url = "sqlite:///" + file_path
        create_new_spine_database(url)
        item = dict(name="DS", description="", url=url, x=0, y=0)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        dialect = self.ds_properties_ui.comboBox_dialect.currentText()
        database = os.path.basename(self.ds_properties_ui.lineEdit_database.text())
        username = self.ds_properties_ui.lineEdit_username.text()
        self.assertEqual(dialect, 'sqlite')
        self.assertEqual(database, 'mock_db.sqlite')
        self.assertEqual(username, '')

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when deactivating a Data Store and activating it again.
        """
        # FIXME: For now it only tests the mysql dialect
        item = dict(name="DS", description="", url="sqlite:///mock_db.sqlite", x=0, y=0)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        self.ds_properties_ui.comboBox_dialect.activated[str].emit('mysql')
        self.ds_properties_ui.lineEdit_host.setText('localhost')
        self.ds_properties_ui.lineEdit_port.setText('8080')
        self.ds_properties_ui.lineEdit_database.setText('foo')
        self.ds_properties_ui.lineEdit_username.setText('bar')
        self.ds_properties_ui.lineEdit_host.editingFinished.emit()
        self.ds_properties_ui.lineEdit_host.editingFinished.emit()
        self.ds_properties_ui.lineEdit_port.editingFinished.emit()
        self.ds_properties_ui.lineEdit_database.editingFinished.emit()
        self.ds_properties_ui.lineEdit_username.editingFinished.emit()
        data_store.deactivate()
        data_store.activate()
        dialect = self.ds_properties_ui.comboBox_dialect.currentText()
        host = self.ds_properties_ui.lineEdit_host.text()
        port = self.ds_properties_ui.lineEdit_port.text()
        database = self.ds_properties_ui.lineEdit_database.text()
        username = self.ds_properties_ui.lineEdit_username.text()
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
            with open(file_path, 'w'):
                pass
        url = "sqlite:///" + file_path
        create_new_spine_database(url)
        item = dict(name="DS", description="", url=url, x=0, y=0)
        self.toolbox.project().add_project_items("Data Stores", item)  # Create Data Store to project
        ind = self.toolbox.project_item_model.find_item("DS")
        data_store = self.toolbox.project_item_model.project_item(ind)  # Find item from project item model
        data_store.activate()
        self.ds_properties_ui.toolButton_copy_url.click()
        # noinspection PyArgumentList
        clipboard_text = QApplication.clipboard().text()
        self.assertEqual(clipboard_text, url)


if __name__ == '__main__':
    unittest.main()
