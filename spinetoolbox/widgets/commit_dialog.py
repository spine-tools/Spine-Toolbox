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

"""Classes for custom QDialogs to add edit and remove database items."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QDialogButtonBox, QApplication
from PySide6.QtCore import Slot, Qt
from PySide6.QtGui import QAction


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new commit."""

    def __init__(self, parent, *db_names):
        """
        Args:
            parent (QWidget): the parent widget
            db_names (Iterable of str): database names
        """
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle("Commit changes to {}".format(",".join(db_names)))
        form = QVBoxLayout(self)
        form.setContentsMargins(4, 4, 4, 4)
        self.action_accept = QAction(self)
        self.action_accept.setShortcut(QApplication.translate("Dialog", "Ctrl+Return", None, -1))
        self.action_accept.triggered.connect(self.accept)
        self.action_accept.setEnabled(True)
        self.commit_msg = "Updated"
        self.commit_msg_edit = QPlainTextEdit(self)
        self.commit_msg_edit.setPlainText(self.commit_msg)
        self.commit_msg_edit.selectAll()
        self.commit_msg_edit.addAction(self.action_accept)
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.commit_button = button_box.addButton("Commit", QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        form.addWidget(self.commit_msg_edit)
        form.addWidget(button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.commit_msg_edit.textChanged.connect(self.receive_text_changed)
        self.receive_text_changed()

    @Slot()
    def receive_text_changed(self):
        """Called when text changes in the commit msg text edit.
        Enable/disable commit button accordingly."""
        self.commit_msg = self.commit_msg_edit.toPlainText()
        cond = self.commit_msg.strip() != ""
        self.commit_button.setEnabled(cond)
        self.action_accept.setEnabled(cond)
