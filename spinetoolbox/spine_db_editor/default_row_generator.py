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
from PySide6.QtCore import QModelIndex, QObject, Qt, Signal, Slot
from spinedb_api import Asterisk, DatabaseMapping
from spinedb_api.temp_id import TempId
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE, ITEM_ID_ROLE
from spinetoolbox.spine_db_editor.selection_for_filtering import AlternativeSelection, EntitySelection


@dataclass(frozen=True)
class DefaultRowData:
    default_data: dict[str, Any]
    default_db_map: DatabaseMapping | None


class DefaultRowGenerator(QObject):
    parameter_definition_default_row_updated = Signal(object)
    parameter_value_default_row_updated = Signal(object)
    entity_alternative_default_row_updated = Signal(object)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._selected_db_map: DatabaseMapping | None = None
        self._selected_entity_class: str | None = None
        self._selected_entity_class_id: TempId | None = None
        self._selected_entity_byname: tuple[str, ...] | None = None
        self._selected_entity_id: DatabaseMapping | None = None
        self._selected_alternative: str | None = None
        self._selected_alternative_id: DatabaseMapping | None = None

    @Slot(object)
    def update_defaults_from_entity_selection(self, entity_selection: EntitySelection) -> None:
        any_updates = False
        any_updates |= self._update_selected_entity_class(entity_selection)
        if any_updates:
            self._emit_definition_row_update()
        any_updates |= self._update_selected_entity(entity_selection)
        if not any_updates:
            return
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

    @Slot(object)
    def update_defaults_from_alternative_selection(self, alternative_selection: AlternativeSelection) -> None:
        default_db_maps = set()
        alternative_id = None
        if alternative_selection is Asterisk:
            alternative = None
        else:
            alternative = None
            multiple_selected = object()
            for db_map, alternative_ids in alternative_selection.items():
                if len(alternative_ids) > 1:
                    alternative = multiple_selected
                    break
                try:
                    alternative_id = next(iter(alternative_ids))
                except StopIteration:
                    continue
                name = db_map.alternative(id=alternative_id)["name"]
                if alternative is None:
                    alternative = name
                elif name != alternative:
                    alternative = multiple_selected
                    break
                default_db_maps.add(db_map)
            if alternative is multiple_selected or (
                self._selected_db_map is not None and self._selected_db_map not in default_db_maps
            ):
                alternative = None
        if alternative == self._selected_alternative:
            return
        self._selected_alternative = alternative
        if self._selected_db_map is None and default_db_maps:
            self._selected_db_map = next(iter(default_db_maps))
        self._selected_alternative_id = alternative_id
        self._emit_value_and_entity_alternative_row_update()

    def _update_selected_entity_class(self, entity_selection: EntitySelection) -> bool:
        class_name = None
        class_id = None
        default_db_map = None
        if entity_selection is not Asterisk:
            for db_map, class_selection in entity_selection.items():
                if len(class_selection) > 1:
                    class_name = None
                    default_db_map = None
                    break
                try:
                    class_id = next(iter(class_selection))
                except StopIteration:
                    continue
                name = db_map.entity_class(id=class_id)["name"]
                if class_name is None:
                    class_name = name
                    default_db_map = db_map
                elif name != class_name:
                    class_name = None
                    default_db_map = None
                    break
        if class_name == self._selected_entity_class and default_db_map is self._selected_db_map:
            return False
        self._selected_db_map = default_db_map
        self._selected_entity_class = class_name
        self._selected_entity_class_id = class_id if default_db_map is not None and class_name is not None else None
        return True

    def _update_selected_entity(self, entity_selection: EntitySelection) -> bool:
        entity_byname = None
        entity_id = None
        multiple_selected = object()
        if entity_selection is not Asterisk:
            for db_map, class_selection in entity_selection.items():
                if len(class_selection) > 1:
                    entity_byname = multiple_selected
                    break
                for class_id, entity_ids in class_selection.items():
                    if entity_ids is Asterisk or len(entity_ids) > 1:
                        entity_byname = multiple_selected
                        break
                    try:
                        entity_id = next(iter(entity_ids))
                    except StopIteration:
                        continue
                    byname = db_map.entity(id=entity_id)["entity_byname"]
                    if entity_byname is None:
                        entity_byname = byname
                    elif byname != entity_byname:
                        entity_byname = multiple_selected
                        break
                if entity_byname is multiple_selected:
                    break
            if entity_byname is multiple_selected:
                entity_byname = None
        if entity_byname == self._selected_entity_byname:
            return False
        self._selected_entity_byname = entity_byname
        self._selected_entity_id = entity_id if entity_byname is not None else None
        return True
