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
import pathlib
from unittest import mock
from PySide6.QtWidgets import QDialogButtonBox
from spinetoolbox.widgets.project_settings_dialog import ProjectSettingsDialog


class TestProjectSettingsDialog:
    def test_name(self, spine_toolbox_with_project, parent_widget):
        project = spine_toolbox_with_project.project()
        project.description = "A very interesting and useful project."
        dialog = ProjectSettingsDialog(parent_widget, project)
        assert dialog._ui.name_line_edit.text() == project.name
        dialog.close()

    def test_description(self, spine_toolbox_with_project, parent_widget):
        project = spine_toolbox_with_project.project()
        project.description = "A very interesting and useful project."
        dialog = ProjectSettingsDialog(parent_widget, project)
        assert dialog._ui.description_text_edit.toPlainText() == "A very interesting and useful project."
        dialog._ui.description_text_edit.setPlainText("Changed the description.")
        dialog._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).click()
        assert dialog.isHidden()
        assert project.description == "Changed the description."
        dialog.close()

    def test_disable_execute_all_action(self, spine_toolbox_with_project, parent_widget):
        project = spine_toolbox_with_project.project()
        assert project.settings.enable_execute_all
        dialog = ProjectSettingsDialog(parent_widget, project)
        assert dialog._ui.enable_execute_all_check_box.isChecked()
        dialog._ui.enable_execute_all_check_box.setChecked(False)
        dialog._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).click()
        assert dialog.isHidden()
        assert not project.settings.enable_execute_all
        dialog.close()

    def test_item_directory_cleanup(self, spine_toolbox_with_project, parent_widget):
        project = spine_toolbox_with_project.project()
        dialog = ProjectSettingsDialog(parent_widget, project)
        item_dir = pathlib.Path(project.items_dir, "imaginary_item")
        item_dir.mkdir()
        data_file = item_dir / "tmp_data.data"
        data_file.touch()
        dialog._temp_item_paths = [data_file]
        with mock.patch("spinetoolbox.widgets.project_settings_dialog.QMessageBox") as message_box_constructor:
            message_box = mock.MagicMock()
            message_box_constructor.return_value = message_box
            button = mock.MagicMock()
            message_box.addButton.return_value = button
            message_box.clickedButton.return_value = button
            dialog._ui.delete_item_files_button.click()
        assert not data_file.exists()
        assert item_dir.exists()
        dialog.close()
