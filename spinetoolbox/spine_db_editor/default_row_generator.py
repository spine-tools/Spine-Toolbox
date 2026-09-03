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
from dataclasses import dataclass
from typing import Any
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, QObject, Qt, Signal, Slot
from spinedb_api import DatabaseMapping, SpineDBAPIError
from spinedb_api.temp_id import TempId
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE, ITEM_ID_ROLE


@dataclass(frozen=True)
class DefaultRowData:
    default_data: dict[str, Any]
    default_db_map: DatabaseMapping | None


class DefaultRowGenerator(QObject):
    parameter_definition_default_row_updated = Signal(object)
    parameter_value_default_row_updated = Signal(object)
    entity_alternative_default_row_updated = Signal(object)

    def __init__(
        self,
        entity_tree_selection_model: QItemSelectionModel,
        alternative_selection_model: QItemSelectionModel,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._entity_tree_selection_model = entity_tree_selection_model
        self._entity_tree_selection_model.selectionChanged.connect(self._update_defaults_from_entity_selection)
        self._alternative_selection_model = alternative_selection_model
        self._alternative_selection_model.selectionChanged.connect(self._update_defaults_from_alternative_selection)
        self._selected_db_map: DatabaseMapping | None = None
        self._selected_entity_class: str | None = None
        self._selected_entity_class_id: TempId | None = None
        self._selected_entity_byname: tuple[str, ...] | None = None
        self._selected_entity_id: DatabaseMapping | None = None
        self._selected_alternative: str | None = None
        self._selected_alternative_id: DatabaseMapping | None = None

    @Slot(QItemSelection, QItemSelection)
    def _update_defaults_from_entity_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        if not self._update_selected_class_and_entity():
            return
        self._emit_definition_row_update()
        self._emit_value_and_entity_alternative_row_update()

    def _emit_definition_row_update(self):
        self.parameter_definition_default_row_updated.emit(
            DefaultRowData({"entity_class_name": self._selected_entity_class}, self._selected_db_map)
        )

    def _emit_value_and_entity_alternative_row_update(self):
        row_data = DefaultRowData(
            {
                "entity_class_name": self._selected_entity_class,
                "entity_byname": self._selected_entity_byname,
                "alternative_name": self._selected_alternative,
            },
            self._selected_db_map,
        )
        self.parameter_value_default_row_updated.emit(row_data)
        self.entity_alternative_default_row_updated.emit(row_data)

    @Slot(QModelIndex, QModelIndex, list)
    def entity_or_class_updated(
        self, top_left: QModelIndex, bottom_right: QModelIndex, roles: list[Qt.ItemDataRole]
    ) -> None:
        if (roles and Qt.ItemDataRole.DisplayRole not in roles) or self._selected_db_map is None:
            return
        try:
            entity = self._selected_db_map.mapped_table("entity")[self._selected_entity_id]
        except KeyError:
            byname_updated = False
        else:
            byname = entity["entity_byname"]
            byname_updated = byname != self._selected_entity_byname
            if byname_updated:
                self._selected_entity_byname = byname
        try:
            entity_class = self._selected_db_map.mapped_table("entity_class")[self._selected_entity_class_id]
        except KeyError:
            class_name_updated = False
        else:
            class_name = entity_class["name"]
            class_name_updated = class_name != self._selected_entity_class
            if class_name_updated:
                self._selected_entity_class = class_name
                self._emit_definition_row_update()
        if class_name_updated or byname_updated:
            self._emit_value_and_entity_alternative_row_update()

    @Slot(QModelIndex, QModelIndex, list)
    def alternative_updated(
        self, top_left: QModelIndex, bottom_right: QModelIndex, roles: list[Qt.ItemDataRole]
    ) -> None:
        if (roles and Qt.ItemDataRole.DisplayRole not in roles) or self._selected_db_map is None:
            return
        try:
            alternative = self._selected_db_map.mapped_table("alternative")[self._selected_alternative_id]
        except KeyError:
            return
        name = alternative["name"]
        if name != self._selected_alternative:
            self._selected_alternative = name
            self._emit_value_and_entity_alternative_row_update()

    @Slot(QItemSelection, QItemSelection)
    def _update_defaults_from_alternative_selection(self, selected: QItemSelection, deselected: QItemSelection) -> None:
        alternative_name = None
        alternative_ids = []
        alternative_id = None
        selection = [index for index in self._alternative_selection_model.selection().indexes() if index.column() == 0]
        if selection:
            selected_alternative = None
            multiple_names_selected = object()
            selected_ids = []
            for index in selection:
                db_map_index = index.parent()
                if db_map_index.isValid():
                    selected_id = index.data(ITEM_ID_ROLE)
                    if selected_id is None:
                        continue
                    selected_ids.append((db_map_index.data(DB_MAP_ROLE), index.data(ITEM_ID_ROLE)))
                    if selected_alternative is None:
                        selected_alternative = index.data()
                    elif index.data() != selected_alternative:
                        selected_alternative = multiple_names_selected
                        break
            if selected_alternative is not multiple_names_selected:
                alternative_name = selected_alternative
                alternative_ids = selected_ids
        any_updates = False
        if alternative_ids:
            if self._selected_db_map is None:
                default_i = 0
                self._selected_db_map = alternative_ids[default_i][0]
            else:
                try:
                    default_i = [i[0] for i in alternative_ids].index(self._selected_db_map)
                except ValueError:
                    return
            any_updates = True
            alternative_id = alternative_ids[default_i][1]
        if alternative_name != self._selected_alternative:
            self._selected_alternative = alternative_name
            self._selected_alternative_id = alternative_id
            any_updates = True
        if any_updates:
            self._emit_value_and_entity_alternative_row_update()

    def _update_selected_class_and_entity(self) -> bool:
        class_name = None
        class_id = None
        entity_byname = None
        entity_id = None
        default_db_map = None
        selection = [
            index
            for index in self._entity_tree_selection_model.selection().indexes()
            if index.column() == 0 and index.parent().isValid()
        ]
        if len(selection) == 1:
            index = selection[0]
            db_map_ids = index.data(ITEM_ID_ROLE)
            default_db_map, item_id = next(iter(db_map_ids.items()))
            if item_id.item_type == "entity_class":
                class_name = default_db_map.entity_class(id=item_id)["name"]
                class_id = item_id
            else:
                entity = default_db_map.entity(id=item_id)
                class_name = entity["entity_class_name"]
                class_id = entity["class_id"]
                entity_byname = entity["entity_byname"]
                entity_id = item_id
        elif len(selection) > 1:
            for index in selection:
                db_map_ids = index.data(ITEM_ID_ROLE)
                db_map, item_id = next(iter(db_map_ids.items()))
                if item_id.item_type == "entity_class":
                    if class_name is not None:
                        class_name = None
                        class_id = None
                        default_db_map = None
                        break
                    class_name = db_map.entity_class(id=item_id)["name"]
                    class_id = item_id
                    default_db_map = db_map
                elif item_id.item_type == "entity":
                    entity_item = db_map.entity(id=item_id)
                    entity_class_name = entity_item["entity_class_name"]
                    if class_name is not None and entity_class_name != class_name:
                        class_name = None
                        class_id = None
                        default_db_map = None
                        break
                    class_name = entity_class_name
                    class_id = entity_item["class_id"]
                    default_db_map = db_map
        if (
            class_name == self._selected_entity_class
            and default_db_map is self._selected_db_map
            and entity_byname == self._selected_entity_byname
        ):
            return False
        self._selected_db_map = default_db_map
        self._selected_entity_class = class_name
        self._selected_entity_class_id = class_id if class_name is not None else None
        self._selected_entity_byname = entity_byname
        self._selected_entity_id = entity_id if entity_byname is not None else None
        return True

    @Slot(object)
    def update_defaults_from_secondary_entity_selection(self, entity_ids: dict[DatabaseMapping, list[TempId]]) -> None:
        if not entity_ids:
            self._update_defaults_from_entity_selection(QItemSelection(), QItemSelection())
            return
        class_name = None
        class_id = None
        entity_byname = None
        entity_id = None
        default_db_map = None
        for db_map, ids in entity_ids.items():
            entity_table = db_map.mapped_table("entity")
            multiple_selected = False
            for current_id in ids:
                entity = entity_table[current_id]
                if entity_byname is None:
                    default_db_map = db_map
                    entity_byname = entity["entity_byname"]
                    entity_id = current_id
                    class_name = entity["entity_class_name"]
                    class_id = entity["class_id"]
                elif entity_byname != entity["entity_byname"] or class_name != entity["entity_class_name"]:
                    class_name = None
                    class_id = None
                    entity_byname = None
                    entity_id = None
                    default_db_map = None
                    multiple_selected = True
                    break
            if multiple_selected:
                break
        if class_name != self._selected_entity_class or default_db_map is not self._selected_db_map:
            self._selected_db_map = default_db_map
            self._ensure_alternative_in_default_db_map()
            self._selected_entity_class = class_name
            self._selected_entity_class_id = class_id if class_name is not None else None
            self._emit_definition_row_update()
        if entity_byname != self._selected_entity_byname:
            self._selected_entity_byname = entity_byname
            self._selected_entity_id = entity_id if entity_byname is not None else None
            self._emit_value_and_entity_alternative_row_update()

    def _ensure_alternative_in_default_db_map(self):
        if self._selected_db_map is None or self._selected_alternative_id is None:
            return
        try:
            alternative = self._selected_db_map.alternative(id=self._selected_alternative_id)
        except SpineDBAPIError:
            forget_selected = True
        else:
            forget_selected = alternative["name"] != self._selected_alternative
        if forget_selected:
            self._selected_alternative = None
            self._selected_alternative_id = None
