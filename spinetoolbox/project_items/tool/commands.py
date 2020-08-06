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
Undo/redo commands for the Tool project item.

:authors: M. Marin (KTH)
:date:   5.5.2020
"""
from spinetoolbox.project_commands import SpineToolboxCommand


class UpdateToolExecuteInWorkCommand(SpineToolboxCommand):
    def __init__(self, tool, execute_in_work):
        """Command to update Tool execute_in_work setting.

        Args:
            tool (Tool): the Tool
            execute_in_work (bool): True or False
        """
        super().__init__()
        self.tool = tool
        self.execute_in_work = execute_in_work
        self.setText(f"change execute in work setting of {tool.name}")

    def redo(self):
        self.tool.do_update_execution_mode(self.execute_in_work)

    def undo(self):
        self.tool.do_update_execution_mode(not self.execute_in_work)


class UpdateToolCmdLineArgsCommand(SpineToolboxCommand):
    def __init__(self, tool, cmd_line_args):
        """Command to update Tool command line args.

        Args:
            tool (Tool): the Tool
            cmd_line_args (list): list of str args
        """
        super().__init__()
        self.tool = tool
        self.redo_cmd_line_args = cmd_line_args
        self.undo_cmd_line_args = self.tool.cmd_line_args
        self.setText(f"change command line arguments of {tool.name}")

    def redo(self):
        self.tool.update_tool_cmd_line_args(self.redo_cmd_line_args)

    def undo(self):
        self.tool.update_tool_cmd_line_args(self.undo_cmd_line_args)
