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

:authors: M. Marin (KTH)
:date:   31.1.2020
"""

import time
from PySide2.QtWidgets import QUndoCommand, QUndoStack


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

    def commands(self):
        return [self.command(idx) for idx in range(self.index())]


class AgedUndoCommand(QUndoCommand):
    def __init__(self, parent=None):
        """
        Args:
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self._age = -1

    def redo(self):
        super().redo()
        self._age = time.time()

    def undo(self):
        super().undo()
        self._age = time.time()

    @property
    def age(self):
        return self._age


class SpineDBMacro(AgedUndoCommand):
    """A command that just runs a series of SpineDBCommand's one after another, *waiting* for each one to finish
    before starting the next."""

    def __init__(self, cmd_iter, parent=None):
        super().__init__(parent=parent)
        self._cmd_iter = cmd_iter
        self._reverse_cmd_iter = None
        self._cmds = []
        self._completed_once = False

    def redo(self):
        super().redo()
        if self._completed_once:
            self._cmd_iter = iter(self._cmds)
        self._redo_next()

    def _redo_next(self):
        child = next(self._cmd_iter, None)
        if child is None:
            self._completed_once = True
            return
        if not self._completed_once:
            self._cmds.append(child)
        child.redo_complete_callback = lambda *args: self._redo_next()
        child.redo()

    def undo(self):
        super().undo()
        self._reverse_cmd_iter = reversed(self._cmds)
        self._undo_next()

    def _undo_next(self):
        child = next(self._reverse_cmd_iter, None)
        if child is None:
            return
        child.undo_complete_callback = lambda *args: self._undo_next()
        child.undo()


class SpineDBCommand(AgedUndoCommand):
    """Base class for all commands that modify a Spine DB."""

    def __init__(self, db_mngr, db_map, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(parent=parent)
        self.db_mngr = db_mngr
        self.db_map = db_map
        self._done_once = False
        self.redo_complete_callback = lambda *args: None
        self.undo_complete_callback = lambda *args: None

    def handle_undo_complete(self, data):
        """Calls the undo complete callback with the data from undo().
        Subclasses need to pass this as the callback to the function that modifies the db in undo()."""
        self.undo_complete_callback(data)

    def handle_redo_complete(self, data):
        """Calls the redo complete callback with the data from redo().
        Subclasses need to pass this as the callback to the function that modifies the db in redo()."""
        self.redo_complete_callback(data)
        if self._done_once:
            return
        self._done_once = True
        self._handle_first_redo_complete(data)

    def _handle_first_redo_complete(self, _):
        """Reimplement in subclasses to do stuff with the data from running redo() the first time."""
        raise NotImplementedError()


class AddItemsCommand(SpineDBCommand):
    _add_command_name = {
        "object_class": "add object classes",
        "object": "add objects",
        "relationship_class": "add relationship classes",
        "relationship": "add relationships",
        "entity_group": "add entity groups",
        "parameter_definition": "add parameter definitions",
        "parameter_value": "add parameter values",
        "parameter_value_list": "add parameter value lists",
        "list_value": "add parameter value list values",
        "alternative": "add alternative",
        "scenario": "add scenario",
        "feature": "add feature",
        "tool": "add tool",
        "tool_feature": "add tool features",
        "tool_feature_method": "add tool feature methods",
        "metadata": "add metadata",
        "entity_metadata": "add entity metadata",
        "parameter_value_metadata": "add parameter value metadata",
    }

    def __init__(self, db_mngr, db_map, data, item_type, parent=None, check=True):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to add
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        self.redo_db_map_data = {db_map: data}
        self.item_type = item_type
        self.undo_db_map_ids = None
        self._readd = False
        self._check = check
        self.setText(self._add_command_name.get(item_type, "add item") + f" to '{db_map.codename}'")

    def redo(self):
        super().redo()
        self.db_mngr.add_items(
            self.redo_db_map_data,
            self.item_type,
            readd=self._readd,
            check=self._check,
            callback=self.handle_redo_complete,
        )

    def undo(self):
        super().undo()
        self.db_mngr.do_remove_items(self.item_type, self.undo_db_map_ids, callback=self.handle_undo_complete)
        self._readd = True

    def _handle_first_redo_complete(self, db_map_data):
        if self.db_map not in db_map_data:
            self.setObsolete(True)
            return
        self.redo_db_map_data = db_map_data
        self.undo_db_map_ids = {db_map: {x["id"] for x in data} for db_map, data in db_map_data.items()}


class UpdateItemsCommand(SpineDBCommand):
    _update_command_name = {
        "object_class": "update object classes",
        "object": "update objects",
        "relationship_class": "update relationship classes",
        "relationship": "update relationships",
        "parameter_definition": "update parameter definitions",
        "parameter_value": "update parameter values",
        "parameter_value_list": "update parameter value lists",
        "list_value": "update parameter value list values",
        "alternative": "update alternatives",
        "scenario": "update scenarios",
        "feature": "update features",
        "tool": "update tools",
        "tool_feature": "update tool features",
        "tool_feature_method": "update tool feature methods",
        "metadata": "update metadata",
        "entity_metadata": "update entity metadata",
        "parameter_value_metadata": "update parameter value metadata",
    }

    def __init__(self, db_mngr, db_map, data, item_type, parent=None, check=True):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            data (list): list of dict-items to update
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not data:
            self.setObsolete(True)
        undo_data = [self.db_mngr.get_item(self.db_map, item_type, item["id"]).copy() for item in data]
        redo_data = [{**undo_item, **item} for undo_item, item in zip(undo_data, data)]
        if undo_data == redo_data:
            self.setObsolete(True)
        self.redo_db_map_data = {db_map: redo_data}
        self.undo_db_map_data = {db_map: undo_data}
        self.item_type = item_type
        self._check = check
        self.setText(self._update_command_name.get(item_type, "update item") + f" in '{db_map.codename}'")

    def redo(self):
        super().redo()
        self.db_mngr.update_items(
            self.redo_db_map_data, self.item_type, check=self._check, callback=self.handle_redo_complete
        )

    def undo(self):
        super().undo()
        self.db_mngr.update_items(
            self.undo_db_map_data, self.item_type, check=False, callback=self.handle_undo_complete
        )

    def _handle_first_redo_complete(self, db_map_data):
        if not db_map_data.get(self.db_map):
            self.setObsolete(True)
            return
        self.redo_db_map_data = db_map_data
        self._check = False


class RemoveItemsCommand(SpineDBCommand):
    def __init__(self, db_mngr, db_map, ids, item_type, parent=None):
        """
        Args:
            db_mngr (SpineDBManager): SpineDBManager instance
            db_map (DiffDatabaseMapping): DiffDatabaseMapping instance
            ids (set): set of ids to remove
            item_type (str): the item type
            parent (QUndoCommand, optional): The parent command, used for defining macros.
        """
        super().__init__(db_mngr, db_map, parent=parent)
        if not ids:
            self.setObsolete(True)
        self.redo_data = {db_map: ids}
        self.undo_data = {}
        self.item_type = item_type
        self.setText(f"remove {item_type} items from '{db_map.codename}'")

    def redo(self):
        super().redo()
        self.db_mngr.do_remove_items(self.item_type, self.redo_data, callback=self.handle_redo_complete)

    def undo(self):
        super().undo()
        self.db_mngr.add_items(self.undo_data, self.item_type, readd=True, callback=self.handle_undo_complete)

    def _handle_first_redo_complete(self, db_map_data):
        self.undo_data = db_map_data
