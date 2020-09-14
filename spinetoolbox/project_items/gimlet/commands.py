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
Undo/redo commands for the Gimlet project item.

:authors: P. Savolainen (VTT)
:date:   30.4.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateShellCheckBoxCommand(SpineToolboxCommand):
    """Command to update Gimlet shell check box state."""

    def __init__(self, gimlet, use_shell):
        """

        Args:
            gimlet (spinetoolbox.project_items.gimlet.gimlet.Gimlet): The Gimlet issuing the command
            use_shell (bool): New check box state
        """
        super().__init__()
        self._gimlet = gimlet
        self._redo_use_shell = use_shell
        self._undo_use_shell = not use_shell
        self.setText(f"change {gimlet.name} shell check box state")

    def redo(self):
        self._gimlet.toggle_shell_state(self._redo_use_shell)

    def undo(self):
        self._gimlet.toggle_shell_state(self._undo_use_shell)


class UpdateShellComboboxCommand(SpineToolboxCommand):
    """Command to update Gimlet shell combobox state."""

    def __init__(self, gimlet, new_index):
        """

        Args:
            gimlet (spinetoolbox.project_items.gimlet.gimlet.Gimlet): The Gimlet issuing the command
            new_index (int): New combobox index
        """
        super().__init__()
        self._gimlet = gimlet
        self._redo_combobox_index = new_index
        self._undo_combobox_index = self._gimlet.shell_index  # Previous index
        self.setText(f"change {gimlet.name} shell combobox selection")

    def redo(self):
        self._gimlet.set_shell_combobox_index(self._redo_combobox_index)

    def undo(self):
        self._gimlet.set_shell_combobox_index(self._undo_combobox_index)


class UpdatecmdCommand(SpineToolboxCommand):
    """Command to update Gimlet command line edit."""

    def __init__(self, gimlet, txt):
        """

        Args:
            gimlet (spinetoolbox.project_items.gimlet.gimlet.Gimlet): The Gimlet issuing the command
            txt (str): New text in command line edit after editing is finished
        """
        super().__init__()
        self._gimlet = gimlet
        self._redo_cmd = txt
        self._undo_cmd = self._gimlet.cmd
        self.setText(f"change command in {gimlet.name}")

    def redo(self):
        self._gimlet.set_command(self._redo_cmd)

    def undo(self):
        self._gimlet.set_command(self._undo_cmd)


class UpdateWorkDirModeCommand(SpineToolboxCommand):
    def __init__(self, gimlet, work_dir_mode):
        """Command to update Gimlet work_in_dir setting.

        Args:
            gimlet (Gimlet): The Gimlet
            work_dir_mode (bool): True or False
        """
        super().__init__()
        self._gimlet = gimlet
        self._work_dir_mode = work_dir_mode
        self.setText(f"change work dir mode setting of {gimlet.name}")

    def redo(self):
        self._gimlet.update_work_dir_mode(self._work_dir_mode)

    def undo(self):
        self._gimlet.update_work_dir_mode(not self._work_dir_mode)
