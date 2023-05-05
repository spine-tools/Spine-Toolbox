######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
QUndoCommand subclasses for modifying the db.
"""

import time
from PySide6.QtGui import QUndoCommand, QUndoStack


class AgedUndoStack(QUndoStack):
    @property
    def redo_age(self):
        if self.canRedo():
            return self.command(self.index()).age
        return -1

    @property
    def undo_age(self):
        if self.canUndo():
            return self.command(self.index() - 1).age
        return -1


class AgedUndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        """
        Args:
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self.parent = parent
        self._age = -1
        self.children = []

    def redo(self):
        super().redo()
        self._age = time.time()

    def undo(self):
        super().undo()
        self._age = time.time()

    @property
    def age(self):
        return self._age

    def check(self):
        if self.children and all(cmd.isObsolete() for cmd in self.children):
            self.setObsolete(True)

    def __del__(self):
        # TODO: try to make sure this works as intended. The idea is to fix a segfault at exiting the app
        # after running an 'import_data' command.
        if self.parent is not None:
            return
        while self.children:
            self.children.pop().parent = None


class SpineDBCommand(AgedUndoCommand):
    """Base class for all commands that modify a Spine DB."""

    def __init__(self, db_mngr, db_map, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
        """
        super().__init__(parent=parent)
        self.db_mngr = db_mngr
        self.db_map = db_map
        if isinstance(parent, AgedUndoCommand):
            # Stores a ref to this in the parent so Python doesn't delete it
            parent.children.append(self)


class AddItemsCommand(SpineDBCommand):
    _add_command_name = {
        "entity_class": "add entity classes",
        "entity": "add entities",
        "entity_group": "add entity groups",
        "parameter_definition": "add parameter definitions",
        "parameter_value": "add parameter values",
        "parameter_value_list": "add parameter value lists",
        "list_value": "add parameter value list values",
        "alternative": "add alternative",
        "scenario": "add scenario",
        "scenario_alternative": "add scenario alternative",
        "metadata": "add metadata",
        "entity_metadata": "add entity metadata",
        "parameter_value_metadata": "add parameter value metadata",
    }

    def __init__(self, db_mngr, db_map, item_type, data, check=True, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to add
            item_type (str): the item type
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        self.redo_data = data
        self.undo_ids = None
        self._check = check
        self.setText(self._add_command_name.get(item_type, "add item") + f" to '{db_map.codename}'")

    def redo(self):
        super().redo()
        if self.undo_ids:
            self.db_mngr.restore_items(self.db_map, self.item_type, self.undo_ids)
            return
        data = self.db_mngr.add_items(self.db_map, self.item_type, self.redo_data, check=self._check)
        if not data:
            self.setObsolete(True)
            return
        self.undo_ids = {x["id"] for x in data}

    def undo(self):
        super().undo()
        self.db_mngr.do_remove_items(self.db_map, self.item_type, self.undo_ids)


class UpdateItemsCommand(SpineDBCommand):
    _update_command_name = {
        "entity_class": "update entity classes",
        "entity": "update entities",
        "parameter_definition": "update parameter definitions",
        "parameter_value": "update parameter values",
        "parameter_value_list": "update parameter value lists",
        "list_value": "update parameter value list values",
        "alternative": "update alternatives",
        "scenario": "update scenarios",
        "scenario_alternative": "update scenario alternative",
        "metadata": "update metadata",
        "entity_metadata": "update entity metadata",
        "parameter_value_metadata": "update parameter value metadata",
    }

    def __init__(self, db_mngr, db_map, item_type, data, check=True, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            item_type (str): the item type
            data (list): list of dict-items to update
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        self.undo_data = [self.db_mngr.get_item(self.db_map, item_type, item["id"]).copy() for item in data]
        self.redo_data = [undo_item.updated(item) for undo_item, item in zip(self.undo_data, data)]
        if self.redo_data == self.undo_data:
            self.setObsolete(True)
        self._check = check
        self.setText(self._update_command_name.get(item_type, "update item") + f" in '{db_map.codename}'")

    def redo(self):
        super().redo()
        if not self.db_mngr.update_items(self.db_map, self.item_type, self.redo_data, check=self._check):
            self.setObsolete(True)
            return
        self._check = False

    def undo(self):
        super().undo()
        self.db_mngr.update_items(self.db_map, self.item_type, self.undo_data, check=False)


class RemoveItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, item_type, ids, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            item_type (str): the item type
            ids (set): set of ids to remove
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not ids:
            self.setObsolete(True)
        self.item_type = item_type
        self.ids = ids
        self.setText(f"remove {item_type} items from '{db_map.codename}'")

    def redo(self):
        super().redo()
        if not self.db_mngr.do_remove_items(self.db_map, self.item_type, self.ids):
            self.setObsolete(True)

    def undo(self):
        super().undo()
        self.db_mngr.restore_items(self.db_map, self.item_type, self.ids)
