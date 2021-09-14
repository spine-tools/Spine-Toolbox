######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains jump properties widget's business logic.

:author: A. Soininen (VTT)
:date:   23.6.2021
"""
from PySide2.QtCore import Slot
from PySide2.QtWidgets import QWidget
from ..project_commands import SetJumpConditionCommand


class JumpPropertiesWidget(QWidget):
    """Widget for jump link properties."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.jump_properties import Ui_Form

        super().__init__(toolbox)
        self._toolbox = toolbox
        self._jump_link = None
        self._condition_updates_enabled = True
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        toolbox.ui.tabWidget_item_properties.addTab(self, "Loop properties")
        self._ui.condition_edit.set_lexer_name("python")

    def set_link(self, link):
        """Hooks the widget to given link, so that user actions are reflected in the link's configuration.

        Args:
            link (JumpLink): link to hook into
        """
        self._jump_link = link
        self._ui.condition_edit.setPlainText(link.jump.condition)
        self._ui.link_name_label.setText(f"Loop from {link.jump.source} to {link.jump.destination}")
        self._ui.condition_edit.setEnabled(True)
        self._ui.condition_edit.textChanged.connect(self._change_condition)

    def unset_link(self):
        """Releases the widget from any links."""
        self._ui.condition_edit.textChanged.disconnect(self._change_condition)
        self._jump_link = None
        self._ui.condition_edit.clear()
        self._ui.condition_edit.setEnabled(False)

    def set_condition(self, jump, condition):
        if self._condition_updates_enabled and self._jump_link is not None and jump is self._jump_link.jump:
            self._ui.condition_edit.textChanged.disconnect(self._change_condition)
            self._ui.condition_edit.setPlainText(condition)
            self._ui.condition_edit.textChanged.connect(self._change_condition)
        jump.condition = condition

    @Slot()
    def _change_condition(self):
        """Stores jump condition to link."""
        condition = self._ui.condition_edit.toPlainText()
        self._condition_updates_enabled = False
        self._toolbox.undo_stack.push(SetJumpConditionCommand(self, self._jump_link.jump, condition))
        self._condition_updates_enabled = True
