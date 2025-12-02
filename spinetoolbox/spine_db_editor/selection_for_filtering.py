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
from itertools import chain
from typing import TypeAlias
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, QObject, Signal, Slot
from spinedb_api import Asterisk, DatabaseMapping
from spinedb_api.helpers import AsteriskType
from spinedb_api.temp_id import TempId
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE, ITEM_ID_ROLE

AlternativeSelection: TypeAlias = dict[DatabaseMapping, set[TempId]] | AsteriskType
EntitySelection: TypeAlias = dict[DatabaseMapping, dict[TempId, set[TempId] | AsteriskType]] | AsteriskType
ScenarioSelection: TypeAlias = dict[DatabaseMapping, set[TempId]] | AsteriskType


class EntitySelectionForFiltering(QObject):
    entity_selection_changed = Signal(object)
    secondary_entity_selection_changed = Signal(object)

    def __init__(self, entity_tree_selection_model: QItemSelectionModel, parent: QObject | None):
        super().__init__(parent)
        self._selection_model = entity_tree_selection_model
        self._selection_model.selectionChanged.connect(self._update_class_or_entity_selection)
        self._current_entity_selection: EntitySelection = {}

    @Slot(QItemSelection, QItemSelection)
    def _update_class_or_entity_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        class_ids = {}
        entity_ids = {}
        selection = self._selection_model.selection().indexes()
        for index in _include_parents(selection):
            if index.column() != 0:
                continue
            if not index.parent().isValid():
                if self._current_entity_selection is not Asterisk:
                    self._current_entity_selection = Asterisk
                    self.entity_selection_changed.emit(Asterisk)
                return
            db_map_ids = index.data(ITEM_ID_ROLE)
            for db_map, item_id in db_map_ids.items():
                if item_id.item_type == "entity_class":
                    class_ids.setdefault(db_map, set()).add(item_id)
                else:
                    entity_ids.setdefault(db_map, set()).add(item_id)
        entity_selection = _collect_entity_selection_from_ids(class_ids, entity_ids)
        if entity_selection != self._current_entity_selection:
            self._current_entity_selection = entity_selection
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
    if len(entity_selection) > 1:
        _remove_surplus_entity_id_asterisks(entity_selection)
    return entity_selection


def _remove_surplus_entity_id_asterisks(entity_selection: EntitySelection) -> None:
    classes_with_non_asterisk_entity_selection = set()
    for db_map, class_selection in entity_selection.items():
        class_table = db_map.mapped_table("entity_class")
        for class_id, entity_ids in class_selection.items():
            if entity_ids is not Asterisk:
                classes_with_non_asterisk_entity_selection.add(class_table[class_id]["name"])
    for db_map, class_selection in entity_selection.items():
        class_table = db_map.mapped_table("entity_class")
        for class_id, entity_ids in class_selection.items():
            if entity_ids is Asterisk and class_table[class_id]["name"] in classes_with_non_asterisk_entity_selection:
                class_selection[class_id] = set()


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


class AlternativeSelectionForFiltering(QObject):
    alternative_selection_changed = Signal(object)

    def __init__(
        self,
        alternative_tree_selection_model: QItemSelectionModel,
        scenario_tree_selection_model: QItemSelectionModel,
        parent: QObject | None,
    ):
        super().__init__(parent)
        self._alternative_tree_selection_model = alternative_tree_selection_model
        self._alternative_tree_selection_model.selectionChanged.connect(self._update_alternative_selection)
        self._current_alternative_selection: AlternativeSelection = Asterisk
        self._scenario_tree_selection_model = scenario_tree_selection_model
        self._scenario_tree_selection_model.selectionChanged.connect(self._update_scenario_alternative_selection)
        self._current_scenario_alternative_selection: AlternativeSelection = Asterisk

    @Slot(QItemSelection, QItemSelection)
    def _update_alternative_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        alternative_selection = {}
        for index in self._alternative_tree_selection_model.selection().indexes():
            if index.column() != 0 or not index.parent().isValid():
                continue
            alternative_id = index.data(ITEM_ID_ROLE)
            if alternative_id is None:
                continue
            db_map = index.parent().data(DB_MAP_ROLE)
            alternative_selection.setdefault(db_map, set()).add(alternative_id)
        if not alternative_selection:
            alternative_selection = Asterisk
        if alternative_selection != self._current_alternative_selection:
            self._current_alternative_selection = alternative_selection
            self.alternative_selection_changed.emit(self._combined_selections())

    @Slot(QItemSelection, QItemSelection)
    def _update_scenario_alternative_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        alternative_selection = {}
        for index in self._scenario_tree_selection_model.selection().indexes():
            if index.column() != 0:
                continue
            scenario_index = index.parent()
            if not scenario_index.isValid():
                continue
            database_index = scenario_index.parent()
            if not database_index.isValid():
                continue
            db_map = database_index.data(DB_MAP_ROLE)
            alternative_ids = db_map.mapped_table("scenario")[scenario_index.data(ITEM_ID_ROLE)]["alternative_id_list"]
            row = index.row()
            if row == len(alternative_ids):
                continue
            alternative_selection.setdefault(db_map, set()).add(alternative_ids[row])
        if not alternative_selection:
            alternative_selection = Asterisk
        if alternative_selection != self._current_scenario_alternative_selection:
            self._current_scenario_alternative_selection = alternative_selection
            self.alternative_selection_changed.emit(self._combined_selections())

    def _combined_selections(self) -> AlternativeSelection:
        total_selection: AlternativeSelection = {}
        for selection in (self._current_alternative_selection, self._current_scenario_alternative_selection):
            if selection is Asterisk:
                continue
            for db_map, alternative_ids in selection.items():
                total_selection.setdefault(db_map, set()).update(alternative_ids)
        if not total_selection:
            total_selection = Asterisk
        return total_selection


class ScenarioSelectionForFiltering(QObject):
    scenario_selection_changed = Signal(object)

    def __init__(self, scenario_tree_selection_model: QItemSelectionModel, parent: QObject | None):
        super().__init__(parent)
        self._selection_model = scenario_tree_selection_model
        self._selection_model.selectionChanged.connect(self._update_scenario_selection)
        self._current_selection: ScenarioSelection = Asterisk

    @Slot(QItemSelection, QItemSelection)
    def _update_scenario_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        selection: ScenarioSelection = {}
        for index in self._selection_model.selectedIndexes():
            if index.column() != 0:
                continue
            parent_index = index.parent()
            if not parent_index.isValid() or parent_index.parent().isValid():
                continue
            db_map = parent_index.data(DB_MAP_ROLE)
            scenario_id = index.data(ITEM_ID_ROLE)
            selection.setdefault(db_map, set()).add(scenario_id)
        if not selection:
            selection = Asterisk
        if selection != self._current_selection:
            self._current_selection = selection
            self.scenario_selection_changed.emit(selection)
