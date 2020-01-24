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
Contains a notification widget.

:author: P. Savolainen (VTT)
:date: 12.12.2019
"""

import logging
from PySide2.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide2.QtCore import Qt, Slot, QTimer, QPropertyAnimation, Property


class Notification(QWidget):
    """Custom pop-up notification widget with fade-in and fade-out effect."""

    def __init__(self, parent, txt, width=120, height=70):
        """

        Args:
            parent (QWidget): Parent widget
            txt (str): Text to display in notification
            width (int): Widget width
            height (int): Widget height
        """
        super().__init__()
        self.setWindowFlags(Qt.Popup)
        self.setParent(parent)
        self._parent = parent
        self.w = width
        self.h = height
        self.label = QLabel(txt)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        layout = QHBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setFixedSize(self.w, self.h)
        ss = "QWidget{background-color: #ffc2b3;" "border-width: 2px;" "border-color: #ffebe6;" \
             "border-style: groove; border-radius: 16px;}"
        self.setStyleSheet(ss)
        self.setAttribute(Qt.WA_DeleteOnClose)
        # Get combobox size and position to calculate the position for the pop-up
        combobox_pos = self._parent.ui.comboBox_current_path.pos()
        combobox_size = self._parent.ui.comboBox_current_path.size()
        x = combobox_pos.x() + combobox_size.width() - self.width()
        y = combobox_pos.y() + combobox_size.height() - self.height()
        self.move(x, y)  # Move to top-right corner of the combobox
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.effect.setOpacity(0.0)
        self._opacity = 0.0
        # Fade in animation
        self.fade_in_anim = QPropertyAnimation(self, b"opacity")
        self.fade_in_anim.setDuration(1000)
        self.fade_in_anim.setStartValue(0.0)
        self.fade_in_anim.setEndValue(0.9)
        self.fade_in_anim.valueChanged.connect(self.update_opacity)
        self.fade_in_anim.finished.connect(self.start_self_destruction_timer)
        # Fade out animation
        self.fade_out_animation = QPropertyAnimation(self, b"opacity")
        self.fade_out_animation.setDuration(1000)
        self.fade_out_animation.setStartValue(0.9)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.valueChanged.connect(self.update_opacity)
        self.fade_out_animation.finished.connect(self.close)
        # Start fade in animation
        self.fade_in_anim.start(QPropertyAnimation.DeleteWhenStopped)

    def start_self_destruction_timer(self):
        """Determines the time this widget is fully visible."""
        QTimer.singleShot(2000, self.start_self_destruction)

    def get_opacity(self):
        """opacity getter."""
        return self._opacity

    def set_opacity(self, op):
        """opacity setter."""
        self._opacity = op

    @Slot(float)
    def update_opacity(self, value):
        """Updates graphics effect opacity."""
        self.effect.setOpacity(value)

    def start_self_destruction(self):
        """Starts fade-out animation and closing of the notification."""
        self.fade_out_animation.start(QPropertyAnimation.DeleteWhenStopped)

    opacity = Property(float, get_opacity, set_opacity)
