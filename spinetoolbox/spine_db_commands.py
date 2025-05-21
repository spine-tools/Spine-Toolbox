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

"""QUndoCommand subclasses for modifying the db."""
from __future__ import annotations
from collections.abc import Iterable
from contextlib import suppress
import time
from typing import TYPE_CHECKING, Optional
from PySide6.QtGui import QUndoCommand, QUndoStack
from spinedb_api import DatabaseMapping
from spinedb_api.exception import SpineDBAPIError
from spinedb_api.temp_id import TempId

if TYPE_CHECKING:
    from .spine_db_manager import SpineDBManager


class AgedUndoStack(QUndoStack):
    @property
    def redo_age(self) -> int:
        if self.canRedo():
            return self.command(self.index()).age
        return -1

    @property
    def undo_age(self) -> int:
        if self.canUndo():
            return self.command(self.index() - 1).age
        return -1


class AgedUndoCommand(QUndoCommand):
    def __init__(self, parent: Optional[QUndoCommand] = None, identifier: int = -1):
        """
        Args:
            parent: The parent command, used for defining macros.
            identifier: Command identifier, to identify whether succeeding commands can be merged.
        """
        super().__init__(parent=parent)
        self._age = -1
        self._id = identifier
        self._buddies: list[AgedUndoCommand] = []
        self.merged = False

    def id(self):
        return self._id

    def ours(self) -> Iterable[AgedUndoCommand]:
        yield self
        yield from self._buddies

    def mergeWith(self, command):
        if not isinstance(command, AgedUndoCommand):
            return False
        self._buddies += [x for x in command.ours() if not x.isObsolete()]
        command.merged = True
        return True

    def redo(self):
        if self.merged:
            return
        super().redo()
        for cmd in self._buddies:
            cmd.redo()
        self._age = time.time()

    def undo(self):
        if self.merged:
            return
        for cmd in reversed(self._buddies):
            cmd.undo()
        super().undo()
        self._age = time.time()

    @property
    def age(self) -> int:
        return self._age


class SpineDBCommand(AgedUndoCommand):
    """Base class for all commands that modify a Spine DB."""

    def __init__(self, db_mngr: SpineDBManager, db_map: DatabaseMapping, **kwargs):
        """
        Args:
            db_mngr: SpineDBManager instance
            db_map: DatabaseMapping instance
            **kwargs: Arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self.db_mngr = db_mngr
        self.db_map = db_map


class AddItemsCommand(SpineDBCommand):
    def __init__(
        self,
        db_mngr: SpineDBManager,
        db_map: DatabaseMapping,
        item_type: str,
        data: list[dict],
        check: bool = True,
        **kwargs,
    ):
        """
        Args:
            db_mngr: SpineDBManager instance
            db_map: DatabaseMapping instance
            data: list of dict-items to add
            item_type: the item type
            check: Whether to check data integrity.
        """
        super().__init__(db_mngr, db_map, **kwargs)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        self.redo_data = data
        self.undo_ids = None
        self._check = check
        self.setText(f"add {item_type} items to {db_mngr.name_registry.display_name(db_map.sa_url)}")

    def redo(self):
        super().redo()
        if self.undo_ids:
            self.db_mngr.do_restore_items(self.db_map, self.item_type, self.undo_ids)
            return
        data = self.db_mngr.do_add_items(self.db_map, self.item_type, self.redo_data, check=self._check)
        if not data:
            self.setObsolete(True)
            return
        self.undo_ids = {x["id"] for x in data}

    def undo(self):
        super().undo()
        self.db_mngr.do_remove_items(self.db_map, self.item_type, self.undo_ids, check=False)


class UpdateItemsCommand(SpineDBCommand):
    def __init__(
        self,
        db_mngr: SpineDBManager,
        db_map: DatabaseMapping,
        item_type: str,
        data: list[dict],
        check: bool = True,
        **kwargs,
    ):
        """
        Args:
            db_mngr: SpineDBManager instance
            db_map: DatabaseMapping instance
            item_type: the item type
            data: list of dict-items to update
            check: Whether to check data integrity.
            **kwargs: Arguments passed to the parent class.
        """
        super().__init__(db_mngr, db_map, **kwargs)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        self.redo_data = data
        table = db_map.mapped_table(item_type)
        self.undo_data = [table[item["id"]]._asdict() for item in data]
        self._check = check
        self.setText(f"update {item_type} items in {self.db_mngr.name_registry.display_name(db_map.sa_url)}")

    def redo(self):
        super().redo()
        self.redo_data = [
            x._asdict()
            for x in self.db_mngr.do_update_items(self.db_map, self.item_type, self.redo_data, check=self._check)
        ]
        if not self.redo_data:
            self.setObsolete(True)
            return
        self._check = False

    def undo(self):
        super().undo()
        self.db_mngr.do_update_items(self.db_map, self.item_type, self.undo_data, check=False)


class AddUpdateItemsCommand(SpineDBCommand):
    def __init__(
        self, db_mngr: SpineDBManager, db_map: DatabaseMapping, item_type: str, data: list[dict], text: str, **kwargs
    ):
        """
        Args:
            db_mngr: SpineDBManager instance
            db_map: DatabaseMapping instance
            item_type: the item type
            data: list of dict-items to add-update
            text: command text
            **kwargs: arguments passed to parent class
        """
        super().__init__(db_mngr, db_map, **kwargs)
        if not data:
            self.setObsolete(True)
        self.item_type = item_type
        self.new_data = data
        table = db_map.mapped_table(item_type)
        old_data = []
        for item in data:
            with suppress(SpineDBAPIError):
                old_data.append(table.find_item(item)._asdict())
        if self.new_data == old_data:
            self.setObsolete(True)
        self.old_data = {x["id"]: x for x in old_data}
        self.redo_restore_ids = None
        self.redo_update_data = None
        self.undo_remove_ids = None
        self.undo_update_data = None
        self.setText(text)
        # self.setText(f"update {item_type} items in {self.db_mngr.name_registry.display_name(db_map.sa_url)}")

    def redo(self):
        super().redo()
        if self.redo_restore_ids is None:
            added, updated = self.db_mngr.do_add_update_items(self.db_map, self.item_type, self.new_data)
            if not added and not updated:
                self.setObsolete(True)
                return
            self.redo_restore_ids = {x["id"] for x in added}
            self.redo_update_data = [x._asdict() for x in updated]
            self.undo_remove_ids = {x["id"] for x in added}
            self.undo_update_data = [self.old_data[id_] for id_ in {x["id"] for x in updated}]
            return
        if self.redo_restore_ids:
            self.db_mngr.do_restore_items(self.db_map, self.item_type, self.redo_restore_ids)
        if self.redo_update_data:
            self.db_mngr.do_update_items(self.db_map, self.item_type, self.redo_update_data, check=False)

    def undo(self):
        super().undo()
        if self.undo_remove_ids:
            self.db_mngr.do_remove_items(self.db_map, self.item_type, self.undo_remove_ids, check=False)
        if self.undo_update_data:
            self.db_mngr.do_update_items(self.db_map, self.item_type, self.undo_update_data, check=False)


class RemoveItemsCommand(SpineDBCommand):
    def __init__(
        self,
        db_mngr: SpineDBManager,
        db_map: DatabaseMapping,
        item_type: str,
        ids: set[TempId],
        check: bool = True,
        **kwargs,
    ):
        """
        Args:
            db_mngr: SpineDBManager instance
            db_map: DatabaseMapping instance
            item_type: the item type
            ids: set of ids to remove
            check: Whether to check data integrity.
            **kwargs: Arguments passed to the parent class.
        """
        super().__init__(db_mngr, db_map, **kwargs)
        if not ids:
            self.setObsolete(True)
        self.item_type = item_type
        self.ids = ids
        self._check = check
        self.setText(f"remove {item_type} items from {self.db_mngr.name_registry.display_name(db_map.sa_url)}")

    def redo(self):
        super().redo()
        items = self.db_mngr.do_remove_items(self.db_map, self.item_type, self.ids, check=self._check)
        if not items:
            self.setObsolete(True)
        self.ids = {x["id"] for x in items}
        self._check = False

    def undo(self):
        super().undo()
        self.db_mngr.do_restore_items(self.db_map, self.item_type, self.ids)
