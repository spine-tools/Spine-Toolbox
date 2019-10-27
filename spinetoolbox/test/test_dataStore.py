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
from unittest import mock
import shutil
import os
import logging
import sys
from PySide2.QtWidgets import QApplication, QMessageBox
from networkx import DiGraph
from spinedb_api import create_new_spine_database
from .mock_helpers import create_toolboxui_with_project
from ..widgets.tree_view_widget import TreeViewForm
from ..project_items.data_store.data_store import DataStore


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

    @classmethod
    def tearDownClass(cls):
        """Remove the file path."""
        pass

    def setUp(self):
        """Overridden method. Runs before each test. Makes instance of ToolboxUI class.
        Note: unittest_settings.conf is not actually saved because ui_main.closeEvent()
        is not called in tearDown().
        """
        self.toolbox = create_toolboxui_with_project()
        self.ds_properties_ui = self.toolbox.categories["Data Stores"]["properties_ui"]
        # Let's add a Data Store to the project here since all tests in this class need it
        item_dict = dict(name="DS", description="", x=0, y=0, url=None, reference=None)
        self.toolbox.project().add_project_items("Data Stores", item_dict)
        self.ds_index = self.toolbox.project_item_model.find_item("DS")
        self.ds = self.toolbox.project_item_model.project_item(self.ds_index)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.ds.tear_down()
        ds_db_path = os.path.join(self.ds.data_dir, "DS.sqlite")
        temp_db_path = os.path.join(self.ds.data_dir, "temp_db.sqlite")
        if os.path.exists(ds_db_path):
            try:
                os.remove(ds_db_path)
            except OSError as os_e:
                # logging.debug("Failed to remove {0}. Error:{1}".format(ds_db_path, os_e))
                pass
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except OSError as os_e:
                # logging.debug("Failed to remove {0}. Error:{1}".format(temp_db_path, os_e))
                pass
        try:
            shutil.rmtree(self.toolbox.project().project_dir)  # Remove project directory
        except OSError as e:
            # logging.debug("Failed to remove project directory. {0}".format(e))
            pass
        try:
            os.remove(self.toolbox.project().path)  # Remove project file
        except OSError:
            # logging.debug("Failed to remove project file")
            pass
        self.toolbox.deleteLater()
        self.toolbox = None
        self.ds_properties_ui = None

    def create_temp_db(self):
        """Let's create a real db to more easily test complicated stuff (such as opening a tree view)."""
        temp_db_path = os.path.join(self.ds.data_dir, "temp_db.sqlite")
        sqlite_url = "sqlite:///" + temp_db_path
        create_new_spine_database(sqlite_url)
        url = dict(dialect="sqlite", database="temp_db.sqlite")
        self.ds._url = self.ds.parse_url(url)  # Set an URL for the Data Store
        return temp_db_path

    def test_item_type(self):
        """Tests that the item type class variable is correct."""
        self.assertEqual(self.ds.item_type, "Data Store")

    def test_create_new_empty_spine_database(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with an empty Data Store and 'for Spine model' checkbox UNCHECKED.
        """
        cb_dialect = self.ds_properties_ui.comboBox_dialect  # Dialect comboBox
        le_db = self.ds_properties_ui.lineEdit_database  # Database lineEdit
        self.ds.activate()
        self.assertEqual(cb_dialect.currentText(), "")
        self.assertEqual(le_db.text(), "")
        # Assert that checkbox is unchecked
        self.assertFalse(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        expected_db_path = os.path.join(self.ds.data_dir, self.ds.name + ".sqlite")
        self.assertEqual(cb_dialect.currentText(), "sqlite")
        self.assertEqual(expected_db_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))

    def test_create_new_empty_spine_database2(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with a Data Store that already has an .sqlite db. Checkbox 'for Spine model' UNCHECKED.
        """
        cb_dialect = self.ds_properties_ui.comboBox_dialect  # Dialect comboBox
        le_db = self.ds_properties_ui.lineEdit_database  # Database lineEdit
        temp_path = self.create_temp_db()
        # Connect to an existing .sqlite db
        url = dict(dialect="sqlite", database=temp_path)
        self.ds._url = self.ds.parse_url(url)
        self.ds.activate()  # This loads the url into properties UI widgets
        # DS should now have "sqlite" selected in the combobox
        self.assertEqual("sqlite", cb_dialect.currentText())
        self.assertEqual(temp_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))  # temp_db.sqlite should exist in DS data_dir at this point
        # Assert that checkbox is unchecked
        self.assertFalse(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button. This overwrites the existing sqlite file!
        with mock.patch("spinetoolbox.project_items.data_store.data_store.QMessageBox") as mock_qmessagebox:
            mock_qmessagebox.exec_().return_value = QMessageBox.AcceptRole
            self.ds_properties_ui.toolButton_create_new_spine_db.click()
            mock_qmessagebox.assert_called_once()
        self.assertEqual("sqlite", cb_dialect.currentText())
        self.assertEqual(temp_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))

    def test_create_new_spine_database_for_spine_model(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with an empty Data Store and 'for Spine model' checkbox CHECKED.
        """
        cb_dialect = self.ds_properties_ui.comboBox_dialect  # Dialect comboBox
        le_db = self.ds_properties_ui.lineEdit_database  # Database lineEdit
        self.ds.activate()
        self.assertEqual(cb_dialect.currentText(), "")
        self.assertEqual(le_db.text(), "")
        # Check CheckBox and assert that it is checked
        self.ds_properties_ui.checkBox_for_spine_model.setChecked(True)
        self.assertTrue(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        expected_db_path = os.path.join(self.ds.data_dir, self.ds.name + ".sqlite")
        self.assertEqual(cb_dialect.currentText(), "sqlite")
        self.assertEqual(expected_db_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))

    def test_create_new_spine_database_for_spine_model2(self):
        """Test that a new Spine database is created when clicking on 'New Spine db tool button'
        with a Data Store that already has an URL. Checkbox 'for Spine model' CHECKED.
        """
        cb_dialect = self.ds_properties_ui.comboBox_dialect  # Dialect comboBox
        le_db = self.ds_properties_ui.lineEdit_database  # Database lineEdit
        temp_path = self.create_temp_db()
        # Connect to an existing .sqlite db
        url = dict(dialect="sqlite", database=temp_path)
        self.ds._url = self.ds.parse_url(url)
        self.ds.activate()  # This loads the url into properties UI widgets
        # DS should now have "sqlite" selected in the combobox
        self.assertEqual("sqlite", cb_dialect.currentText())
        self.assertEqual(temp_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))  # temp_db.sqlite should exist in DS data_dir at this point
        # Check CheckBox and assert that it is checked
        self.ds_properties_ui.checkBox_for_spine_model.setChecked(True)
        self.assertTrue(self.ds_properties_ui.checkBox_for_spine_model.isChecked())
        # Click New Spine db button. This overwrites the existing sqlite file!
        with mock.patch("spinetoolbox.project_items.data_store.data_store.QMessageBox") as mock_qmessagebox:
            mock_qmessagebox.exec_().return_value = QMessageBox.AcceptRole
            self.ds_properties_ui.toolButton_create_new_spine_db.click()
            mock_qmessagebox.assert_called_once()
        self.assertEqual("sqlite", cb_dialect.currentText())
        self.assertEqual(temp_path, le_db.text())
        self.assertTrue(os.path.exists(le_db.text()))

    def test_save_and_restore_selections(self):
        """Test that selections are saved and restored when
        deactivating a Data Store and activating it again."""
        # FIXME: For now it only tests the mysql dialect
        url = dict(dialect="mysql", database="sqlite:///mock_db.sqlite")
        self.ds._url = self.ds.parse_url(url)  # Set an URL for the Data Store
        self.ds.activate()
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
        self.ds.deactivate()
        self.ds.activate()
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

    @unittest.skip("Does not work on Travis or on Windows")
    def test_copy_db_url_to_clipboard(self):
        """Test that the database url from current selections is copied to clipboard."""
        QApplication.clipboard().clear()
        self.ds.activate()
        self.ds_properties_ui.toolButton_copy_url.click()
        # noinspection PyArgumentList
        clipboard_text = QApplication.clipboard().text()
        expected_url = "sqlite:///" + os.path.join(self.ds.data_dir, "DS.sqlite")
        self.assertEqual(expected_url, clipboard_text.strip())

    def test_open_treeview1(self):
        """Test that selecting the 'sqlite' dialect, browsing to an existing db file,
        and pressing open tree view works as expected.
        """
        temp_db_path = self.create_temp_db()
        self.ds.activate()
        self.assertIsNone(self.ds.tree_view_form)
        # Select the sqlite dialect
        self.ds_properties_ui.comboBox_dialect.activated[str].emit("sqlite")
        # Browse to an existing db file
        with mock.patch("spinetoolbox.project_items.data_store.data_store.QFileDialog") as mock_qfile_dialog:
            mock_qfile_dialog.getOpenFileName.side_effect = lambda *args: [temp_db_path]
            self.ds_properties_ui.toolButton_open_sqlite_file.click()
            mock_qfile_dialog.getOpenFileName.assert_called_once()
        # Open treeview
        self.ds_properties_ui.pushButton_ds_tree_view.click()
        self.assertIsInstance(self.ds.tree_view_form, TreeViewForm)
        expected_url = "sqlite:///" + temp_db_path
        self.assertEqual(expected_url, str(self.ds.tree_view_form.db_maps[0].db_url))
        self.ds.tree_view_form.close()
        # TODO: self.ds.tree_view_form is not None at this point. Should it be?

    def test_open_treeview2(self):
        """Test that selecting the 'sqlite' dialect, typing the path to an existing db file,
        and pressing open tree view works as expected.
        """
        temp_db_path = self.create_temp_db()
        self.ds.activate()
        self.assertIsNone(self.ds.tree_view_form)
        # Select the sqlite dialect
        self.ds_properties_ui.comboBox_dialect.activated[str].emit("sqlite")
        # Type the path to an existing db file
        self.ds_properties_ui.lineEdit_database.setText(temp_db_path)
        self.ds_properties_ui.lineEdit_database.editingFinished.emit()
        # Open treeview
        self.ds_properties_ui.pushButton_ds_tree_view.click()
        self.assertIsInstance(self.ds.tree_view_form, TreeViewForm)
        expected_url = "sqlite:///" + temp_db_path
        self.assertEqual(expected_url, str(self.ds.tree_view_form.db_maps[0].db_url))
        self.ds.tree_view_form.close()
        # TODO: self.ds.tree_view_form is not None at this point. Should it be?

    def test_notify_destination(self):
        class MockToolbox:
            class Message:
                def __init__(self):
                    self.text = None

                def emit(self, text):
                    self.text = text

            def __init__(self):
                self.msg = MockToolbox.Message()
                self.msg_warning = MockToolbox.Message()

            def reset_messages(self):
                self.msg = MockToolbox.Message()
                self.msg_warning = MockToolbox.Message()

        class MockItem:
            def __init__(self, item_type, name):
                self.item_type = item_type
                self.name = name

        toolbox = MockToolbox()
        self.ds._toolbox = toolbox
        source_item = MockItem("Data Connection", "source name")
        self.ds.notify_destination(source_item)
        self.assertEqual(toolbox.msg.text, "Link established.")
        toolbox.reset_messages()
        source_item.item_type = "Data Interface"
        self.ds.notify_destination(source_item)
        self.assertEqual(
            toolbox.msg.text,
            "Link established. Mappings generated by <b>source name</b> will be imported in <b>DS</b> when executing.",
        )
        toolbox.reset_messages()
        source_item.item_type = "Gdx Export"
        self.ds.notify_destination(source_item)
        self.assertEqual(
            toolbox.msg_warning.text,
            "Link established. Interaction between a "
            "<b>Gdx Export</b> and a <b>Data Store</b> has not been implemented yet.",
        )
        toolbox.reset_messages()
        source_item.item_type = "Tool"
        self.ds.notify_destination(source_item)
        self.assertEqual(toolbox.msg.text, "Link established.")
        toolbox.reset_messages()
        source_item.item_type = "View"
        self.ds.notify_destination(source_item)
        self.assertEqual(
            toolbox.msg_warning.text,
            "Link established. Interaction between a "
            "<b>View</b> and a <b>Data Store</b> has not been implemented yet.",
        )

    def test_default_name_prefix(self):
        self.assertEqual(DataStore.default_name_prefix(), "Data Store")

    def test_rename(self):
        """Tests renaming a Data Store with an existing sqlite db in it's data_dir."""
        cb_dialect = self.ds_properties_ui.comboBox_dialect  # Dialect comboBox
        le_db = self.ds_properties_ui.lineEdit_database  # Database lineEdit
        self.ds.activate()
        # Click New Spine db button
        self.ds_properties_ui.toolButton_create_new_spine_db.click()
        # Check that DS is connected to an existing DS.sqlite file that is in data_dir
        self.assertEqual("sqlite", cb_dialect.currentText())
        self.assertEqual(os.path.join(self.ds.data_dir, "DS.sqlite"), le_db.text())  # data_dir before rename
        self.assertTrue(os.path.exists(le_db.text()))
        expected_name = "ABC"
        expected_short_name = "abc"
        ret_val = self.ds.rename(expected_name)  # Do rename
        self.assertTrue(ret_val)
        # Check name
        self.assertEqual(expected_name, self.ds.name)  # item name
        self.assertEqual(expected_name, self.ds_properties_ui.label_ds_name.text())  # name label in props
        self.assertEqual(expected_name, self.ds.get_icon().name_item.text())  # name item on Design View
        # Check data_dir and logs_dir
        expected_data_dir = os.path.join(self.toolbox.project().project_dir, expected_short_name)
        expected_logs_dir = os.path.join(expected_data_dir, "logs")
        self.assertEqual(expected_data_dir, self.ds.data_dir)  # Check data dir
        self.assertEqual(expected_logs_dir, self.ds.logs_dir)  # Check logs dir
        # Check that the database path in properties has been updated
        expected_db_path = os.path.join(expected_data_dir, "DS.sqlite")
        self.assertEqual(expected_db_path, le_db.text())
        # Check that the db file has actually been moved
        self.assertTrue(os.path.exists(le_db.text()))
        # Check there's a dag containing a node with the new name and that no dag contains a node with the old name
        dag_with_new_node_name = self.toolbox.project().dag_handler.dag_with_node(expected_name)
        self.assertIsInstance(dag_with_new_node_name, DiGraph)
        dag_with_old_node_name = self.toolbox.project().dag_handler.dag_with_node("DS")
        self.assertIsNone(dag_with_old_node_name)


if __name__ == '__main__':
    unittest.main()
