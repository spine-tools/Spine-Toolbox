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
Contains the GraphViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtCore import Qt, Signal, QStateMachine, QFinalState, QState, QEventTransition, QEvent
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDockWidget, QWidget


class StateMachineWidget(QDockWidget):
    """A widget with a state machine."""

    _advanced = Signal()

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
        self.machine = None
        self.run = None
        self._welcome_text = "Welcome!"
        self.active_state = None
        self.setAttribute(Qt.WA_DeleteOnClose)

    def is_running(self):
        return self.machine and self.machine.isRunning()

    def show(self):
        self.setFloating(False)
        self.parent().addDockWidget(Qt.TopDockWidgetArea, self)
        if not self.isVisible():
            self.setup()
        super().show()

    def _make_welcome(self):
        welcome = QState(self.run)
        begin = QState(welcome)
        finalize = QFinalState(welcome)
        welcome.setInitialState(begin)
        begin.assignProperty(self.label_msg, "text", self._welcome_text)
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
        self.active_state = self._make_welcome()
        self.active_state.finished.connect(self._handle_welcome_finished)
        self.machine.setInitialState(self.run)
        self.run.setInitialState(self.active_state)
        self.machine.start()

    def _handle_welcome_finished(self):
        raise NotImplementedError()

    def _goto_state(self, state):
        self.active_state.addTransition(self._advanced, state)
        self.active_state = state
        self._advanced.emit()
