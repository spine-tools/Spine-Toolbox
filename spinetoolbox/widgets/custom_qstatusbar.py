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
Custom QWidgets for Filtering and Zooming.

:author: M. Marin (KTH)
:date:   2.11.2019
"""

from PySide2.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMenu,
    QToolButton,
    QTextEdit,
    QWidgetAction,
    QLabel,
    QStatusBar,
)
from PySide2.QtGui import QIcon
from ..helpers import get_datetime
from ..config import STATUSBAR_SS


class NotificationStatusBar(QStatusBar):
    def __init__(self, parent=None):
        """Init class.

        Args
            parent
        """
        super().__init__(parent)
        # Set up status bar and apply style sheet
        self.setFixedHeight(20)
        self.setSizeGripEnabled(False)
        self.setStyleSheet(STATUSBAR_SS)
        self.notification_button = NotificationButton(self)
        self.notification_label = QLabel()
        self.notification_count = 0
        self.addWidget(self.notification_button)
        self.addWidget(self.notification_label)

    def add_notification(self, msg):
        self.notification_button.add_notification(msg)
        self.notification_count += 1
        self.notification_label.setText(f"{self.notification_count} new notification(s)")

    def decrease_notification_count(self):
        self.notification_count -= 1
        msg = f"{self.notification_count} new notification(s)" if self.notification_count else ""
        self.notification_label.setText(msg)


class NotificationButton(QToolButton):
    """A border-less tool button that shows a notification message when hovered."""

    def __init__(self, parent=None):
        """Init class.

        Args
            parent
        """
        super().__init__(parent)
        self.setIcon(QIcon(":/icons/menu_icons/info-circle.svg"))
        self.setStyleSheet("QToolButton {border: 0px;}")
        self.setPopupMode(QToolButton.InstantPopup)
        self._menu = QMenu()
        self.setMenu(self._menu)
        self.setEnabled(True)

    def add_notification(self, msg):
        # Container
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        margin = 3
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(1)
        # Time and close button
        button_widget = QWidget(self)
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button = QToolButton()
        button.setIcon(QIcon(":/icons/menu_icons/times.svg"))
        button.setStyleSheet("QToolButton {border: 0px;}")
        time_str = get_datetime(show=True, date=False)
        time_label = QLabel(time_str)
        button_layout.addWidget(time_label)
        button_layout.addStretch()
        button_layout.addWidget(button)
        layout.addWidget(button_widget)
        # Text edit
        text_edit = QTextEdit(widget)
        text_edit.setHtml(msg)
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("QTextEdit {background-color: #19232D; color: #F0F0F0;}")
        fm = text_edit.fontMetrics()
        width = fm.width(msg)
        height = fm.height()
        line_count = width / text_edit.width()
        text_edit.setMaximumHeight(line_count * height)
        layout.addWidget(text_edit)
        # Action
        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        self._menu.addAction(action)
        sep = self._menu.addSeparator()
        button.clicked.connect(lambda checked=False, action=action, sep=sep: self._handle_action_closed(action, sep))
        self.setEnabled(True)

    def _handle_action_closed(self, action, sep):
        self._menu.removeAction(action)
        self._menu.removeAction(sep)
        self.parent().decrease_notification_count()
        self._menu.hide()
        self.setEnabled(bool(self._menu.actions()))
        self.click()
