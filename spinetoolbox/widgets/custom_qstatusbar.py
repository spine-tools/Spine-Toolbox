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

from PySide2.QtWidgets import QWidget, QVBoxLayout, QMenu, QToolButton, QWidgetAction, QLabel, QStatusBar
from PySide2.QtGui import QIcon
from .custom_qtextbrowser import CustomQTextBrowser
from ..helpers import get_datetime
from ..config import STATUSBAR_SS, TEXTBROWSER_SS


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

    def reset_notification_count(self):
        self.notification_count = 0
        self.notification_label.setText("")


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
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        margin = 3
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(1)
        self.text_edit = CustomQTextBrowser(widget)
        self.text_edit.setStyleSheet(TEXTBROWSER_SS)
        layout.addWidget(self.text_edit)
        action = QWidgetAction(self)
        action.setDefaultWidget(widget)
        self._menu.addAction(action)
        self._menu.aboutToHide.connect(self.parent().reset_notification_count)

    def add_notification(self, msg):
        open_tag = "<p><span style='color:white; white-space: pre;'>"
        date_str = get_datetime(show=True, date=False)
        message = open_tag + date_str + msg + "</span></p>"
        self.text_edit.append(message)
