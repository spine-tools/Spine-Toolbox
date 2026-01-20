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
from typing import ClassVar, Literal
from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoCommand, QUndoStack
from spinetoolbox.pydantic_models.consumer_replay import (
    CommandBase,
    MoveItem,
    build_command_list,
    set_superseded_commands_obsolete,
)


class DummyCommand(CommandBase):
    version: ClassVar[int] = 1
    type: Literal["dummy"] = "dummy"
    data: str = ""


class DummyIcon:
    def __init__(self):
        self.pos = None

    def set_pos_without_bumping(self, pos):
        self.pos = pos


class DummyItem:
    def __init__(self):
        self.icon = DummyIcon()

    def get_icon(self):
        return self.icon


class DummyProject:
    def __init__(self):
        self.items = {}

    def add_item(self, name, item):
        self.items[name] = item

    def get_item(self, name):
        return self.items[name]


class TestMoveItem:
    def test_is_superseded_by(self):
        move_item = MoveItem(item_name="A", x=2.3, y=3.2)
        assert not move_item.is_superseded_by(DummyCommand())
        assert not move_item.is_superseded_by(MoveItem(item_name="B", x=2.3, y=3.2))
        assert move_item.is_superseded_by(MoveItem(item_name="A", x=-2.3, y=-3.2))

    def test_replay(self):
        move_item = MoveItem(item_name="A", x=2.3, y=3.2)
        project = DummyProject()
        project_item = DummyItem()
        project.add_item("A", project_item)
        move_item.replay(project)
        assert project.items["A"].icon.pos == QPointF(2.3, 3.2)

    def test_replay_returns_gracefully_if_item_isnt_found(self):
        move_item = MoveItem(item_name="A", x=2.3, y=3.2)
        project = DummyProject()
        project_item = DummyItem()
        project.add_item("B", project_item)
        move_item.replay(project)
        assert project.items["B"].icon.pos is None


class ReplayableCommand(QUndoCommand):
    def __init__(self, commands):
        super().__init__("")
        self.commands = commands

    def to_replay_commands(self):
        return self.commands


class TestBuildCommandList:
    def test_command_without_replay_creation_method_is_ignored(self, parent_object):
        undo_stack = QUndoStack(parent_object)
        undo_stack.push(QUndoCommand())
        assert build_command_list(undo_stack, 0) == []

    def test_single_replayable_command(self, parent_object):
        undo_stack = QUndoStack(parent_object)
        undo_stack.push(ReplayableCommand([DummyCommand(data="xy")]))
        assert build_command_list(undo_stack, 0) == [DummyCommand(data="xy")]

    def test_obsolete_command_is_ignored(self, parent_object):
        undo_stack = QUndoStack(parent_object)
        command = ReplayableCommand([DummyCommand()])
        undo_stack.push(command)
        command.setObsolete(True)
        assert build_command_list(undo_stack, 0) == []

    def test_only_commands_until_stack_index_get_included(self, parent_object):
        undo_stack = QUndoStack(parent_object)
        undo_stack.push(ReplayableCommand([DummyCommand(data="1")]))
        undo_stack.push(ReplayableCommand([DummyCommand(data="2")]))
        undo_stack.push(ReplayableCommand([DummyCommand(data="3")]))
        undo_stack.setIndex(2)
        assert build_command_list(undo_stack, 0) == [DummyCommand(data="1"), DummyCommand(data="2")]

    def test_list_starts_from_first_consumer_index(self, parent_object):
        undo_stack = QUndoStack(parent_object)
        undo_stack.push(ReplayableCommand([DummyCommand(data="1")]))
        undo_stack.push(ReplayableCommand([DummyCommand(data="2")]))
        undo_stack.push(ReplayableCommand([DummyCommand(data="3")]))
        assert build_command_list(undo_stack, 1) == [DummyCommand(data="2"), DummyCommand(data="3")]


class TestSetSupersededCommandsObsolete:
    def test_empty_command_list(self):
        commands = []
        set_superseded_commands_obsolete(commands)
        assert commands == []

    def test_single_command(self):
        commands = [MoveItem(item_name="A", x=2.3, y=3.2)]
        set_superseded_commands_obsolete(commands)
        assert commands == [MoveItem(item_name="A", x=2.3, y=3.2)]

    def test_nothing_supersedes(self):
        commands = [MoveItem(item_name="A", x=2.3, y=3.2), MoveItem(item_name="B", x=3.2, y=2.3)]
        set_superseded_commands_obsolete(commands)
        assert commands == [MoveItem(item_name="A", x=2.3, y=3.2), MoveItem(item_name="B", x=3.2, y=2.3)]

    def test_commands_supersede_each_other(self):
        commands = [MoveItem(item_name="A", x=2.3, y=3.2), MoveItem(item_name="A", x=3.2, y=2.3)]
        set_superseded_commands_obsolete(commands)
        assert commands == [
            MoveItem(item_name="A", x=2.3, y=3.2, is_obsolete=True),
            MoveItem(item_name="A", x=3.2, y=2.3),
        ]

    def test_interleaved_commands(self):
        commands = [
            MoveItem(item_name="A", x=2.3, y=3.2),
            MoveItem(item_name="B", x=-2.3, y=-3.2),
            MoveItem(item_name="A", x=3.2, y=2.3),
            MoveItem(item_name="B", x=-3.2, y=-2.3),
        ]
        set_superseded_commands_obsolete(commands)
        assert commands == [
            MoveItem(item_name="A", x=2.3, y=3.2, is_obsolete=True),
            MoveItem(item_name="B", x=-2.3, y=-3.2, is_obsolete=True),
            MoveItem(item_name="A", x=3.2, y=2.3),
            MoveItem(item_name="B", x=-3.2, y=-2.3),
        ]
