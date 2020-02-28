######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the StateMachineWidget class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtCore import Property, Qt, QStateMachine, QFinalState, QState, QEventTransition, QEvent
from PySide2.QtGui import QFont, QMovie
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDockWidget, QWidget


class StateMachineWidget(QDockWidget):
    """A widget with a state machine."""

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
        self.label_loader = QLabel(self)
        self.label_loader.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        movie = QMovie(":/animated_gifs/ajax-loader.gif")
        movie.start()
        self.label_loader.setMovie(movie)
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
        layout.addWidget(self.label_loader)
        layout.addStretch()
        layout.addWidget(button_container)
        self.setWidget(widget)
        self.machine = None
        self.welcome = None
        self._welcome_text = "<html><p>Welcome!</p></html>"
        self._current_state = None
        self.setAttribute(Qt.WA_DeleteOnClose)

    def is_running(self):
        return self.machine and self.machine.isRunning()

    def show(self):
        self.setFloating(False)
        self.parent().addDockWidget(Qt.TopDockWidgetArea, self)
        if not self.isVisible():
            self.set_up_machine()
            self.machine.start()
        super().show()

    def _make_state(self, name):
        s = QState(self.machine)
        s.assignProperty(self, "current_state", name)
        return s

    def _make_welcome(self):
        welcome = self._make_state("welcome")
        begin = QState(welcome)
        finalize = QFinalState(welcome)
        welcome.setInitialState(begin)
        begin.assignProperty(self.label_msg, "text", self._welcome_text)
        begin.assignProperty(self.button_right, "text", "Start")
        begin.assignProperty(self.button_right, "visible", True)
        begin.assignProperty(self.label_loader, "visible", False)
        begin.assignProperty(self.button_left, "visible", False)
        begin.addTransition(self.button_right.clicked, finalize)
        return welcome

    def set_up_machine(self):
        self.machine = QStateMachine(self)
        self.welcome = self._make_welcome()
        self.machine.setInitialState(self.welcome)
        dead = QFinalState(self.machine)
        death = QEventTransition(self, QEvent.Close)
        death.setTargetState(dead)
        self.machine.addTransition(death)

    def get_current_state(self):
        return self._current_state

    def set_current_state(self, state):
        self._current_state = state

    current_state = Property(str, get_current_state, set_current_state)
