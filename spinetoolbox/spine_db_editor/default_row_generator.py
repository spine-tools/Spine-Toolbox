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
from PySide6.QtCore import QObject, Signal, Slot
from spinedb_api import Asterisk, DatabaseMapping
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
        self._selected_entity_byname: tuple[str, ...] | None = None
        self._selected_alternative: str | None = None

    @Slot(object)
    def update_defaults_from_entity_selection(self, entity_selection: EntitySelection) -> None:
        any_updates = False
        any_updates |= self._update_selected_entity_class(entity_selection)
        if any_updates:
            self.parameter_definition_default_row_updated.emit(
                DefaultRowData({"entity_class_name": self._selected_entity_class}, self._selected_db_map)
            )
        any_updates |= self._update_selected_entity(entity_selection)
        if not any_updates:
            return
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

    @Slot(object)
    def update_defaults_from_alternative_selection(self, alternative_selection: AlternativeSelection) -> None:
        default_db_maps = set()
        if alternative_selection is Asterisk:
            alternative = None
        else:
            alternative = None
            multiple_selected = object()
            for db_map, alternative_ids in alternative_selection.items():
                if len(alternative_ids) > 1:
                    alternative = multiple_selected
                    break
                alternative_id = next(iter(alternative_ids))
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
            db_map = next(iter(default_db_maps))
        else:
            db_map = self._selected_db_map
        row_data = DefaultRowData(
            {
                "entity_class_name": self._selected_entity_class,
                "entity_byname": self._selected_entity_byname,
                "alternative_name": alternative,
            },
            db_map,
        )
        self.parameter_value_default_row_updated.emit(row_data)
        self.entity_alternative_default_row_updated.emit(row_data)

    def _update_selected_entity_class(self, entity_selection: EntitySelection) -> bool:
        class_name = None
        default_db_map = None
        if entity_selection is not Asterisk:
            for db_map, class_selection in entity_selection.items():
                if len(class_selection) > 1:
                    class_name = None
                    default_db_map = None
                    break
                class_id = next(iter(class_selection))
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
        return True

    def _update_selected_entity(self, entity_selection: EntitySelection) -> bool:
        entity_byname = None
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
                    entity_id = next(iter(entity_ids))
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
        return True
