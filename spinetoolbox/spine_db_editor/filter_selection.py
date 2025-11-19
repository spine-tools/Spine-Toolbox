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
from collections.abc import Iterable, Iterator
from copy import deepcopy
from typing import TypeAlias
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, QObject, Signal, Slot
from spinedb_api import Asterisk, DatabaseMapping
from spinedb_api.helpers import AsteriskType
from spinedb_api.temp_id import TempId
from spinetoolbox.mvcmodels.shared import ITEM_ID_ROLE

EntitySelection: TypeAlias = dict[DatabaseMapping, dict[TempId, set[TempId] | AsteriskType]] | AsteriskType


class FilterSelection(QObject):
    entity_selection_changed = Signal(object)
    secondary_entity_selection_changed = Signal(object)

    def __init__(self, entity_tree_selection_model: QItemSelectionModel, parent: QObject | None):
        super().__init__(parent)
        self._entity_tree_selection_model = entity_tree_selection_model
        self._entity_tree_selection_model.selectionChanged.connect(self._update_class_or_entity_selection)
        self._alternatives: dict[DatabaseMapping, set[TempId]] = {}
        self._scenario_alternatives: dict[DatabaseMapping, list[list[TempId]]] = {}
        self._current_entity_selection: EntitySelection = Asterisk

    @Slot(QItemSelection, QItemSelection)
    def _update_class_or_entity_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        class_ids = {}
        entity_ids = {}
        for index in _include_parents(self._entity_tree_selection_model.selection().indexes()):
            db_map_ids = index.data(ITEM_ID_ROLE)
            if not index.parent().isValid():
                self.entity_selection_changed.emit(Asterisk)
                return
            for db_map, item_id in db_map_ids.items():
                if item_id.item_type == "entity_class":
                    class_ids.setdefault(db_map, set()).add(item_id)
                else:
                    entity_ids.setdefault(db_map, set()).add(item_id)
        self._current_entity_selection = _collect_entity_selection_from_ids(class_ids, entity_ids)
        self.entity_selection_changed.emit(self._current_entity_selection)

    @Slot(object)
    def update_secondary_entity_selection(self, entity_ids: dict[DatabaseMapping, list[TempId]]) -> None:
        if not entity_ids:
            self.secondary_entity_selection_changed.emit(self._current_entity_selection)
            return
        entity_selection: EntitySelection = {}
        for db_map, ids in entity_ids.items():
            mapped_table = db_map.mapped_table("entity")
            for entity_id in ids:
                class_id = mapped_table[entity_id]["class_id"]
                entity_selection.setdefault(db_map, {}).setdefault(class_id, set()).add(entity_id)
        self.secondary_entity_selection_changed.emit(entity_selection)


def _collect_entity_selection_from_ids(
    class_ids: dict[DatabaseMapping, set[TempId]], entity_ids: dict[DatabaseMapping, set[TempId]]
) -> EntitySelection:
    entity_selection: EntitySelection = {}
    for db_map, ids in entity_ids.items():
        entity_table = db_map.mapped_table("entity")
        selection_by_class = entity_selection.setdefault(db_map, {})
        for entity_id in ids:
            entity = entity_table[entity_id]
            selection_by_class.setdefault(entity["class_id"], set()).add(entity_id)
    for db_map, ids in class_ids.items():
        selection_by_class = entity_selection.setdefault(db_map, {})
        for class_id in ids:
            if class_id in selection_by_class:
                continue
            selection_by_class[class_id] = Asterisk
    return entity_selection


def _include_parents(indexes: Iterable[QModelIndex]) -> Iterator[QModelIndex]:
    parents = {}
    for index in indexes:
        yield index
        parent = index.parent()
        if not parent.isValid() or parent.data() == "root":
            continue
        parents[(parent.row(), parent.column(), id(parent.internalPointer()))] = parent
    if parents:
        yield from _include_parents(parents.values())
