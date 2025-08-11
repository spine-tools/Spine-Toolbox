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

"""A widget for editing project settings."""
import pathlib
import shutil
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QWidget
from spinetoolbox.file_size_aggregator import AggregatorProcess
from spinetoolbox.helpers import display_byte_size
from spinetoolbox.project import SpineToolboxProject
from spinetoolbox.project_settings import ProjectSettings


class ProjectSettingsDialog(QDialog):
    """Dialog for managing the settings of a project."""

    def __init__(self, parent: QWidget, project: SpineToolboxProject):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._project = project

        from ..ui.project_settings_dialog import Ui_Form

        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle("Project Settings")
        self._ui.name_line_edit.setText(self._project.name)
        self._ui.description_text_edit.setPlainText(self._project.description)
        self._ui.enable_execute_all_check_box.setChecked(self._project.settings.enable_execute_all)
        self._ui.delete_item_files_button.clicked.connect(self._clean_item_directories)
        self._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self.accept)
        self._ui.button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.reject)
        self._file_size_aggregator = AggregatorProcess(self)
        self._file_size_aggregator.aggregated.connect(self._update_path_sizes)
        self._temp_item_paths: list[pathlib.Path] = []
        self._start_item_directory_size_aggregation()

    @property
    def description(self) -> str:
        return self._ui.description_text_edit.toPlainText().strip()

    def _start_item_directory_size_aggregation(self) -> None:
        self._temp_item_paths = sum(
            (item.temporary_paths_in_item_directory() for item in self._project.get_items()), []
        )
        self._ui.item_directory_size_label.setText(f"Calculating...")
        self._file_size_aggregator.start_aggregating(self._temp_item_paths)

    @Slot(int)
    def _update_path_sizes(self, size: int) -> None:
        number, unit = display_byte_size(size)
        self._ui.item_directory_size_label.setText(f"Temporary files in item directories: {number}{unit}")

    @Slot(bool)
    def _clean_item_directories(self, _: bool = True) -> None:
        message_box = QMessageBox(
            QMessageBox.Icon.Warning,
            "Confirm item directory cleanup",
            "All temporary content in item directories will be deleted. Are you sure?",
            parent=self,
        )
        yes_button = message_box.addButton("Delete all content", QMessageBox.ButtonRole.YesRole)
        cancel_button = message_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
        message_box.setDefaultButton(cancel_button)
        message_box.exec_()
        if message_box.clickedButton() is yes_button:
            for path in self._temp_item_paths:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.is_file():
                    path.unlink()
            self._start_item_directory_size_aggregation()

    def accept(self) -> None:
        super().accept()
        updates = {}
        description = self.description
        if description != self._project.description:
            updates["description"] = description
        enable_execute_all = self._ui.enable_execute_all_check_box.isChecked()
        if enable_execute_all != self._project.settings.enable_execute_all:
            updates["settings"] = ProjectSettings(enable_execute_all)
        if updates:
            self._project.update_settings(**updates)

    def closeEvent(self, event: QCloseEvent) -> None:
        super().closeEvent(event)
        self._file_size_aggregator.tear_down()
