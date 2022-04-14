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
from PySide2.QtCore import Slot, QItemSelection
from .properties_widget import PropertiesWidgetBase
from ..project_commands import SetJumpConditionCommand, UpdateJumpCmdLineArgsCommand
from ..mvcmodels.file_list_models import FileListModel, JumpCommandLineArgsModel
from spine_engine.project_item.project_item_resource import LabelArg


class JumpPropertiesWidget(PropertiesWidgetBase):
    """Widget for jump link properties."""

    def __init__(self, toolbox, base_color=None):
        """
        Args:
            toolbox (ToolboxUI): The toolbox instance where this widget should be embedded
        """
        from ..ui.jump_properties import Ui_Form

        super().__init__(toolbox, base_color=base_color)
        self._cmd_line_args_model = JumpCommandLineArgsModel(self)
        self._input_file_model = FileListModel(header_label="Available resources", draggable=True)
        self._jump = None
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.treeView_cmd_line_args.setModel(self._cmd_line_args_model)
        self._ui.treeView_input_files.setModel(self._input_file_model)
        self._ui.condition_edit.set_lexer_name("python")
        self._ui.condition_edit.textChanged.connect(self._change_condition)
        self._ui.toolButton_remove_arg.clicked.connect(self._remove_arg)
        self._ui.toolButton_add_arg.clicked.connect(self._add_args)
        self._cmd_line_args_model.args_updated.connect(self._push_update_cmd_line_args_command)
        self._ui.treeView_cmd_line_args.selectionModel().selectionChanged.connect(
            self._update_remove_args_button_enabled
        )
        self._ui.treeView_input_files.selectionModel().selectionChanged.connect(self._update_add_args_button_enabled)

    @Slot(QItemSelection, QItemSelection)
    def _update_add_args_button_enabled(self, _selected, _deselected):
        self._do_update_add_args_button_enabled()

    def _do_update_add_args_button_enabled(self):
        enabled = self._ui.treeView_input_files.selectionModel().hasSelection()
        self._ui.toolButton_add_arg.setEnabled(enabled)

    @Slot(QItemSelection, QItemSelection)
    def _update_remove_args_button_enabled(self, _selected, _deselected):
        self._do_update_remove_args_button_enabled()

    def _do_update_remove_args_button_enabled(self):
        enabled = self._ui.treeView_cmd_line_args.selectionModel().hasSelection()
        self._ui.toolButton_remove_arg.setEnabled(enabled)

    def set_link(self, jump):
        """Hooks the widget to given jump link, so that user actions are reflected in the jump link's configuration.

        Args:
            jump (LoggingJump): link to hook into
        """
        self._jump = jump
        self._ui.condition_edit.setPlainText(self._jump.condition)
        self._toolbox.label_item_name.setText(f"<b>Loop {self._jump.jump_link.name}</b>")
        self._input_file_model.update(self._jump.resources)
        self._populate_cmd_line_args_model()
        self._do_update_add_args_button_enabled()
        self._do_update_remove_args_button_enabled()

    def unset_link(self):
        """Releases the widget from any links."""
        self._jump = None

    def set_condition(self, jump, condition):
        jump.condition = condition
        if jump is self._jump and self._ui.condition_edit.toPlainText() != condition:
            self._ui.condition_edit.setPlainText(condition)

    def update_cmd_line_args(self, jump, cmd_line_args):
        jump.cmd_line_args = cmd_line_args
        if jump is self._jump and self._cmd_line_args_model.args != cmd_line_args:
            self._populate_cmd_line_args_model()

    def _populate_cmd_line_args_model(self):
        self._cmd_line_args_model.reset_model(self._jump.cmd_line_args)

    @Slot()
    def _change_condition(self):
        """Stores jump condition to link."""
        condition = self._ui.condition_edit.toPlainText()
        if self._jump.condition == condition:
            return
        self._toolbox.undo_stack.push(SetJumpConditionCommand(self, self._jump, condition))

    @Slot(list)
    def _push_update_cmd_line_args_command(self, cmd_line_args):
        if self._jump.cmd_line_args == cmd_line_args:
            return
        self._toolbox.undo_stack.push(UpdateJumpCmdLineArgsCommand(self, self._jump, cmd_line_args))

    @Slot(bool)
    def _remove_arg(self, _=False):
        removed_rows = [index.row() for index in self._ui.treeView_cmd_line_args.selectedIndexes()]
        cmd_line_args = [arg for row, arg in enumerate(self._jump.cmd_line_args) if row not in removed_rows]
        self._push_update_cmd_line_args_command(cmd_line_args)

    @Slot(bool)
    def _add_args(self, _=False):
        new_args = [LabelArg(index.data()) for index in self._ui.treeView_input_files.selectedIndexes()]
        self._push_update_cmd_line_args_command(self._jump.cmd_line_args + new_args)
