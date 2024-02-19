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

"""
Provides OptionsDialog.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QButtonGroup, QRadioButton, QPushButton, QFrame, QStyle
from PySide6.QtCore import Slot, Qt


class OptionsDialog(QDialog):
    """A dialog with options."""

    def __init__(self, parent, title, text, option_to_action, notes=None, preferred=None):
        """
        Args:
            parent (QWidget): the parent widget
            title (srt): title of the window
            text (str): text to show to the user
            option_to_action (dict): mapping option string to corresponding action to return
            preferred (int,optional): preselected option if any
        """
        super().__init__(parent)
        if notes is None:
            notes = {}
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle(title)
        layout = QVBoxLayout(self)
        if option_to_action:
            text += "<br><p>What do you want to do?"
        text_label = QLabel(text)
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        options_frame = QFrame()
        options_layout = QVBoxLayout(options_frame)
        self.button_group = QButtonGroup()
        for i, o in enumerate(option_to_action):
            note = notes.get(o)
            if i == preferred:
                o += " (RECOMMENDED)"
            option_button = QRadioButton(o)
            options_layout.addWidget(option_button)
            self.button_group.addButton(option_button, id=i)
            if note is not None:
                note_label = QLabel(note)
                note_label.setWordWrap(True)
                indent = sum(
                    self.style().pixelMetric(pm)
                    for pm in (
                        QStyle.PixelMetric.PM_ExclusiveIndicatorWidth,
                        QStyle.PixelMetric.PM_RadioButtonLabelSpacing,
                    )
                )
                note_label.setIndent(indent)
                font = note_label.font()
                font.setPointSize(font.pointSize() - 1)
                note_label.setFont(font)
                note_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
                options_layout.addWidget(note_label)
        layout.addWidget(options_frame)
        self.ok_button = QPushButton("Ok")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        if preferred is not None:
            self.button_group.button(preferred).setChecked(True)
        self.button_group.idToggled.connect(self._update_ok_button_enabled)
        self._update_ok_button_enabled()

    @classmethod
    def get_action(cls, parent, title, text, option_to_action, notes=None, preferred=None):
        obj = cls(parent, title, text, option_to_action, notes=notes, preferred=preferred)
        obj.exec()
        if obj.result() != QDialog.Accepted:
            return None
        id_ = obj.button_group.checkedId()
        if id_ == -1:
            return None
        option = list(option_to_action)[id_]
        return option_to_action[option]

    @Slot(int)
    def _update_ok_button_enabled(self, _id=None):
        self.ok_button.setEnabled(not self.button_group.buttons() or self.button_group.checkedButton() is not None)
