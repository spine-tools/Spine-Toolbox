######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Unit tests for the ``open_project_dialog`` module."""
import unittest
from unittest import mock
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QPoint
from spinetoolbox.widgets.open_project_dialog import OpenProjectDialog


class TestOpenProjectDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_open_project_dialog(self):
        self._widget = QWidget()
        opw = OpenProjectDialog(DummyToolbox(self._widget))
        opw.go_root_action.trigger()
        opw.go_home_action.trigger()
        opw.go_documents_action.trigger()
        opw.go_desktop_action.trigger()
        with mock.patch(
            "spinetoolbox.widgets.open_project_dialog.OpenProjectDialogComboBoxContextMenu.get_action"
        ) as mock_cb_context_menu:
            mock_cb_context_menu.return_value = "Clear history"
            opw.show_context_menu(QPoint(0, 0))
            mock_cb_context_menu.assert_called()
        opw.close()

    def test_update_recents_remove_recents(self):
        self._widget = QWidget()
        with TemporaryDirectory() as temp_dir1:
            with TemporaryDirectory() as temp_dir2:
                opw = OpenProjectDialog(DummyToolbox(self._widget))
                opw.expand_and_resize(temp_dir1)
                # Add path
                opw.update_recents(temp_dir1, opw._qsettings)
                expected_str1 = temp_dir1
                self.assertEqual(expected_str1, opw._qsettings.recent_storages)
                # Add a second one
                opw.update_recents(temp_dir2, opw._qsettings)
                expected_str2 = f"{temp_dir2}" + "\n" + f"{temp_dir1}"
                self.assertEqual(expected_str2, opw._qsettings.recent_storages)
                # Try to add the same path again
                opw.update_recents(temp_dir2, opw._qsettings)
                self.assertEqual(expected_str2, opw._qsettings.recent_storages)
                # Remove the paths one by one
                opw.remove_directory_from_recents(temp_dir1, opw._qsettings)
                expected_str3 = temp_dir2
                self.assertEqual(expected_str3, opw._qsettings.recent_storages)
                opw.remove_directory_from_recents(temp_dir2, opw._qsettings)
                expected_str4 = ""
                self.assertEqual(expected_str4, opw._qsettings.recent_storages)


class DummyToolbox(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def qsettings(self):
        return MockQSettings()


class MockQSettings:
    """Fake QSettings class for testing the update of recent project storages in Custom Open Project Dialog."""

    def __init__(self):
        self.recent_storages = None

    # noinspection PyMethodMayBeStatic, PyPep8Naming
    def value(self, key, defaultValue=""):
        """Returns the default value"""
        if key == "appSettings/recentProjectStorages":
            return self.recent_storages
        return defaultValue

    # noinspection PyPep8Naming
    def setValue(self, key, value):
        """Returns without modifying anything."""
        if key == "appSettings/recentProjectStorages":
            self.recent_storages = value
        return

    def sync(self):
        return True
