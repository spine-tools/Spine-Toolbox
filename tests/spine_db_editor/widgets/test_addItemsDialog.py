######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for SpineDBEditor classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

import unittest
from unittest import mock
from tempfile import TemporaryDirectory
import logging
import sys
from PySide2.QtCore import QModelIndex
from PySide2.QtWidgets import QApplication
import spinetoolbox.resources_icons_rc  # pylint: disable=unused-import
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_manager import SpineDBManager
from spinetoolbox.spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from spinetoolbox.spine_db_editor.widgets.add_items_dialogs import AddObjectClassesDialog


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
        """Overridden method. Runs before each test. Makes instance of SpineDBEditor class."""
        with mock.patch("spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.restore_ui"):
            mock_settings = mock.Mock()
            mock_settings.value.side_effect = lambda *args, **kwargs: 0
            self._db_mngr = SpineDBManager(mock_settings, None)
            logger = mock.MagicMock()
            self._temp_dir = TemporaryDirectory()
            url = "sqlite:///" + self._temp_dir.name + "/db.sqlite"
            self._db_map = self._db_mngr.get_db_map(url, logger, codename="mock_db", create=True)
            self._db_editor = SpineDBEditor(self._db_mngr, {url: "mock_db"})

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.spine_db_editor.widgets.spine_db_editor.SpineDBEditor.save_window_state"
        ), mock.patch("spinetoolbox.spine_db_manager.QMessageBox"):
            self._db_editor.close()
        self._db_mngr.close_all_sessions()
        while not self._db_map.connection.closed:
            QApplication.processEvents()
        self._db_mngr.clean_up()
        self._db_editor.deleteLater()
        self._db_editor = None
        self._temp_dir.cleanup()

    def test_add_object_classes(self):
        """Test object classes are added through the manager when accepting the dialog."""
        dialog = AddObjectClassesDialog(self._db_editor, self._db_mngr, self._db_map)
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ['object_class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object_class name', 'databases')]
        values = ['fish', 'mock_db']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._commit_changes_to_database("Add object class.")
        data = self._db_mngr.query(self._db_map, "object_class_sq")
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].name, "fish")

    def test_do_not_add_object_classes_with_invalid_db(self):
        """Test object classes aren't added when the database is not correct."""
        dialog = AddObjectClassesDialog(self._db_editor, self._db_mngr, self._db_map)
        self._db_editor.msg_error = mock.NonCallableMagicMock()
        self._db_editor.msg_error.attach_mock(mock.MagicMock(), "emit")
        model = dialog.model
        header = model.header
        model.fetchMore(QModelIndex())
        self.assertEqual(header, ['object_class name', 'description', 'display icon', 'databases'])
        indexes = [model.index(0, header.index(field)) for field in ('object_class name', 'databases')]
        values = ['fish', 'gibberish']
        model.batch_set_data(indexes, values)
        dialog.accept()
        self._db_editor.msg_error.emit.assert_called_with("Invalid database 'gibberish' at row 1")

    def _commit_changes_to_database(self, commit_message):
        with mock.patch.object(self._db_editor, "_get_commit_msg") as commit_msg:
            commit_msg.return_value = commit_message
            with signal_waiter(self._db_mngr.session_committed) as waiter:
                self._db_editor.ui.actionCommit.trigger()
                waiter.wait()


if __name__ == '__main__':
    unittest.main()
