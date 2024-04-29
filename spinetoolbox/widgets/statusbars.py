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

"""Functions to make and handle QStatusBars."""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QStatusBar, QToolButton, QMenu
from PySide6.QtGui import QAction
from ..config import STATUSBAR_SS


class MainStatusBar(QStatusBar):
    """A status bar for the main toolbox window."""

    _ALL_RUNS = "All executions"

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI)
        """
        super().__init__(toolbox)
        self._toolbox = toolbox
        self.setStyleSheet(STATUSBAR_SS)
        self._executions_menu = QMenu(self)
        self.executions_button = QToolButton(self)
        self.reset_executions_button_text()
        self.executions_button.setMenu(self._executions_menu)
        self.executions_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.insertWidget(0, self.executions_button)
        self._executions_menu.aboutToShow.connect(self._populate_executions_menu)
        self._executions_menu.triggered.connect(self._select_execution)

    @Slot()
    def _populate_executions_menu(self):
        texts = [self._ALL_RUNS] + self._toolbox.execution_timestamps()
        self._executions_menu.clear()
        for text in texts:
            action = self._executions_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(text == self.executions_button.text())

    def reset_executions_button_text(self):
        self.executions_button.setText(self._ALL_RUNS)
        self.executions_button.setEnabled(False)

    @Slot(QAction)
    def _select_execution(self, action):
        text = action.text()
        self.executions_button.setText(text)
        if text == self._ALL_RUNS:
            self._toolbox.select_all_executions()
            return
        self._toolbox.select_execution(text)
