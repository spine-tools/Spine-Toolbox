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
from __future__ import annotations
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal, Union
from pydantic import Field
from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoStack
from spine_engine.pydantic_models.models import VersionedModel

if TYPE_CHECKING:
    from ..project import SpineToolboxProject


class CommandBase(VersionedModel):
    is_obsolete: bool = Field(default=False, exclude=True)

    def is_superseded_by(self, later_command: CommandBase) -> bool:
        return False

    def replay(self, project: SpineToolboxProject) -> None:
        raise NotImplementedError()


class MoveItem(CommandBase):
    version: ClassVar[int] = 1
    type: Literal["move_item"] = "move_item"
    item_name: str
    x: float
    y: float

    def is_superseded_by(self, later_command: CommandBase) -> bool:
        return isinstance(later_command, MoveItem) and self.item_name == later_command.item_name

    def replay(self, project: SpineToolboxProject) -> None:
        try:
            item = project.get_item(self.item_name)
        except KeyError:
            return
        item.get_icon().set_pos_without_bumping(QPointF(self.x, self.y))


Command = Annotated[Union[MoveItem], Field(discriminator="type")]


class CommandStack(VersionedModel):
    version: ClassVar[int] = 1
    commands: list[Command]


def build_command_list(undo_stack: QUndoStack, first_consumer_index: int) -> list[Command]:
    commands = []
    for command_i in range(first_consumer_index, undo_stack.index()):
        undo_command = undo_stack.command(command_i)
        if undo_command.isObsolete() or not hasattr(undo_command, "to_replay_commands"):
            continue
        commands += undo_command.to_replay_commands()
    return commands


def set_superseded_commands_obsolete(commands: list[Command]) -> None:
    for i, command in enumerate(reversed(commands[1:])):
        if command.is_obsolete:
            continue
        for previous_command in reversed(commands[: -i - 1]):
            if not previous_command.is_obsolete and previous_command.is_superseded_by(command):
                previous_command.is_obsolete = True
