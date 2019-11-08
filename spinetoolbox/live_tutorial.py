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
Contains the GraphViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import os
from PySide2.QtCore import Qt, QStateMachine, QFinalState, QState, QEventTransition, QEvent
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDockWidget, QWidget
from .widgets.custom_qwidgets import OverlayWidget
from .config import APPLICATION_PATH


class LiveTutorial(QDockWidget):
    """A widget that shows a tutorial for Spine Toolbox."""

    _overlay_color = QColor(255, 140, 0, 128)
    _tutorial_data_path = os.path.join(APPLICATION_PATH, "../tutorial")

    def __init__(self, window_title, parent):
        """Initializes class.

        Args:
            window_title (str)
            parent (QMainWindow)
        """
        super().__init__(window_title, parent)
        self.setObjectName(window_title)
        self.label_msg = QLabel(self)
        self.label_msg.setFont(QFont("arial,helvetica", 12))
        self.label_msg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.label_msg.setWordWrap(True)
        self.button_left = QPushButton(self)
        self.button_right = QPushButton(self)
        button_container = QWidget(self)
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.button_left)
        button_layout.addWidget(self.button_right)
        button_layout.addStretch()
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.addStretch()
        layout.addWidget(self.label_msg)
        layout.addStretch()
        layout.addWidget(button_container)
        self.setWidget(widget)
        self.overlay1 = OverlayWidget(color=self._overlay_color)
        self.overlay2 = OverlayWidget(color=self._overlay_color)
        self.hide()
        self.machine = None
        self.run = None

    def is_running(self):
        return self.machine and self.machine.isRunning()

    def show(self):
        self.setFloating(False)
        self.parent().addDockWidget(Qt.TopDockWidgetArea, self)
        self.setup()
        super().show()

    def _make_welcome(self):
        welcome = QState(self.run)
        begin = QState(welcome)
        finalize = QFinalState(welcome)
        welcome.setInitialState(begin)
        begin.assignProperty(self.label_msg, "text", "Welcome!")
        begin.assignProperty(self.button_right, "text", "Start")
        begin.assignProperty(self.button_right, "visible", True)
        begin.assignProperty(self.button_left, "visible", False)
        begin.addTransition(self.button_right.clicked, finalize)
        return welcome

    def _make_abort(self):
        abort = QState(self.run)
        dead = QFinalState(self.machine)
        abort.addTransition(dead)
        return abort

    def setup(self):
        self.machine = QStateMachine(self)
        self.run = QState(self.machine)
        abort = self._make_abort()
        transition = QEventTransition(self, QEvent.Close)
        transition.setTargetState(abort)
        self.run.addTransition(transition)
        welcome = self._make_welcome()
        welcome.entered.connect(self._handle_welcome_entered)
        self.machine.setInitialState(self.run)
        self.run.setInitialState(welcome)
        self.machine.start()

    def _handle_welcome_entered(self):
        raise NotImplementedError()
