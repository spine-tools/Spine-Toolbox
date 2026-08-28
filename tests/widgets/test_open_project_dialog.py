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

import os
import json
from unittest import mock
from PySide6.QtCore import QPoint, QDir, QModelIndex
from PySide6.QtWidgets import QDialog
from spinetoolbox.widgets.open_project_dialog import OpenProjectDialog
from spinetoolbox.config import LATEST_PROJECT_VERSION


class TestOpenProjectDialog:
    def test_open_project_dialog(self, application, parent_widget_with_settings, tmp_path):
        # Add two dirs to recentProjectStorages. (one that exists and one that doesn't)
        temp_dir1 = tmp_path / "dir1"
        temp_dir1.mkdir()
        recents_list = [str(temp_dir1), "/some/projects"]
        recents = "\n".join(recents_list)
        parent_widget_with_settings.qsettings().setValue("appSettings/recentProjectStorages", recents)
        opw = OpenProjectDialog(parent_widget_with_settings)
        assert opw.ui.comboBox_current_path.count() == 2
        assert opw.ui.comboBox_current_path.currentText() == str(temp_dir1)
        opw.go_root_action.trigger()
        opw.go_home_action.trigger()
        opw.go_documents_action.trigger()
        opw.go_desktop_action.trigger()
        # Selecting non-existing path from the combobox should remove it from qsettings
        opw.ui.comboBox_current_path.setCurrentIndex(1)
        entries = parent_widget_with_settings.qsettings().value("appSettings/recentProjectStorages")
        assert entries == str(temp_dir1)
        opw.ui.comboBox_current_path.setCurrentIndex(0)
        assert opw.ui.comboBox_current_path.currentText() == str(temp_dir1)
        # Clear recent project storages
        with mock.patch(
            "spinetoolbox.widgets.open_project_dialog.OpenProjectDialogComboBoxContextMenu.get_action"
        ) as mock_cb_context_menu:
            mock_cb_context_menu.return_value = "Clear history"
            opw.show_context_menu(QPoint(0, 0))
            mock_cb_context_menu.assert_called()
        assert os.path.samefile(opw.ui.comboBox_current_path.currentText(), QDir.rootPath())
        opw.close()

    def test_update_recents_remove_recents(self, parent_widget_with_settings, tmp_path):
        temp_dir1 = tmp_path / "dir1"
        temp_dir2 = tmp_path / "dir2"
        temp_dir1.mkdir()
        temp_dir2.mkdir()
        opw = OpenProjectDialog(parent_widget_with_settings)
        opw.expand_and_resize(str(temp_dir1))
        # Add path
        opw.update_recents(str(temp_dir1), opw._qsettings)
        assert opw._qsettings.value("appSettings/recentProjectStorages") == str(temp_dir1)
        # Add second path
        opw.update_recents(str(temp_dir2), opw._qsettings)
        assert opw._qsettings.value("appSettings/recentProjectStorages") == f"{temp_dir2}\n{temp_dir1}"
        # Add same path again
        opw.update_recents(str(temp_dir2), opw._qsettings)
        assert opw._qsettings.value("appSettings/recentProjectStorages") == f"{temp_dir2}\n{temp_dir1}"
        # Remove first path
        opw.remove_directory_from_recents(str(temp_dir1), opw._qsettings)
        assert opw._qsettings.value("appSettings/recentProjectStorages") == str(temp_dir2)
        # Remove second path
        opw.remove_directory_from_recents(str(temp_dir2), opw._qsettings)
        assert opw._qsettings.value("appSettings/recentProjectStorages") == ""

    def test_open_project(self, parent_widget_with_settings, tmp_path):
        opw = OpenProjectDialog(parent_widget_with_settings)
        # Test that invalid indexes don't call done
        with mock.patch.object(opw, "done") as mock_done:
            opw.open_project(QModelIndex())
        mock_done.assert_not_called()
        # Create a valid QModelIndex mock
        valid_index = mock.Mock(spec=QModelIndex)
        valid_index.isValid.return_value = True
        # Test that non-project directories don't call done
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        with mock.patch.object(opw, "selection", return_value=str(project_dir)):
            with mock.patch.object(opw, "done") as mock_done:
                opw.open_project(valid_index)
        mock_done.assert_not_called()
        # Test that valid project directories call done
        project_dict = {"project": {"version": LATEST_PROJECT_VERSION}}
        (project_dir / ".spinetoolbox").mkdir()
        (project_dir / ".spinetoolbox" / "project.json").write_text(json.dumps(project_dict))
        with mock.patch.object(opw, "selection", return_value=str(project_dir)):
            with mock.patch.object(opw, "done") as mock_done:
                opw.open_project(valid_index)
        mock_done.assert_called_once_with(QDialog.DialogCode.Accepted)

    @mock.patch("spinetoolbox.widgets.open_project_dialog.Notification")
    def test_done_nonexistent_path(self, mock_notification, parent_widget_with_settings):
        opw = OpenProjectDialog(parent_widget_with_settings)
        with mock.patch.object(opw, "selection", return_value="/does/not/exist"):
            opw.done(QDialog.DialogCode.Accepted)
        mock_notification.assert_called_once_with(opw, "Path does not exist")

    @mock.patch("spinetoolbox.widgets.open_project_dialog.Notification")
    def test_done_not_a_project(self, mock_notification, parent_widget_with_settings, tmp_path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        opw = OpenProjectDialog(parent_widget_with_settings)
        with mock.patch.object(opw, "selection", return_value=str(project_dir)):
            opw.done(QDialog.DialogCode.Accepted)
        mock_notification.assert_called_once_with(opw, "Not a valid Spine Toolbox project")

    @mock.patch("spinetoolbox.widgets.open_project_dialog.Notification")
    @mock.patch("spinetoolbox.widgets.open_project_dialog.load_project_dict")
    def test_done_missing_version(
        self,
        mock_load_project_dict,
        mock_notification,
        parent_widget_with_settings,
        tmp_path,
    ):
        project_dir = tmp_path / "project"
        (project_dir / ".spinetoolbox").mkdir(parents=True)
        (project_dir / ".spinetoolbox" / "project.json").write_text("{}")
        mock_load_project_dict.return_value = {}
        opw = OpenProjectDialog(parent_widget_with_settings)
        with mock.patch.object(opw, "selection", return_value=str(project_dir)):
            opw.done(QDialog.DialogCode.Accepted)
        mock_notification.assert_called_once()
        assert "Version info missing" in mock_notification.call_args[0][1]

    @mock.patch("spinetoolbox.widgets.open_project_dialog.Notification")
    @mock.patch("spinetoolbox.widgets.open_project_dialog.load_project_dict")
    def test_done_incompatible_version(self, mock_load_project_dict, mock_notification, parent_widget_with_settings, tmp_path):
        project_dir = tmp_path / "project"
        (project_dir / ".spinetoolbox").mkdir(parents=True)
        (project_dir / ".spinetoolbox" / "project.json").write_text("{}")
        mock_load_project_dict.return_value = {"project": {"version": LATEST_PROJECT_VERSION + 1}}
        opw = OpenProjectDialog(parent_widget_with_settings)
        with mock.patch.object(opw, "selection", return_value=str(project_dir)):
            opw.done(QDialog.DialogCode.Accepted)
        mock_notification.assert_called_once()
        assert "Cannot open project" in mock_notification.call_args[0][1]

    @mock.patch("spinetoolbox.widgets.open_project_dialog.load_project_dict")
    def test_done_valid_project(self, mock_load_project_dict, parent_widget_with_settings,tmp_path):
        project_dir = tmp_path / "project"
        (project_dir / ".spinetoolbox").mkdir(parents=True)
        project_json = (project_dir / ".spinetoolbox" / "project.json")
        project_json.write_text(json.dumps({"project": {"version": LATEST_PROJECT_VERSION}}))
        mock_load_project_dict.return_value = {"project": {"version": LATEST_PROJECT_VERSION}}
        opw = OpenProjectDialog(parent_widget_with_settings)
        with (
            mock.patch.object(opw, "selection", return_value=str(project_dir)),
            mock.patch.object(opw, "update_recents") as mock_update_recents
        ):
            opw.done(QDialog.DialogCode.Accepted)
        mock_update_recents.assert_called_once()
