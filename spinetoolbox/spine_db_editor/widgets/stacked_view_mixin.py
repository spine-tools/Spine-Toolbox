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

"""Contains the StackedViewMixin class."""
from typing import Optional
from PySide6.QtCore import QAbstractItemModel, QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, Slot
from PySide6.QtGui import QColor
from spinedb_api import DatabaseMapping
from spinedb_api.temp_id import TempId
from ...helpers import preferred_row_height
from ...mvcmodels.shared import ITEM_ROLE
from ..default_row_generator import DefaultRowData, DefaultRowGenerator
from ..empty_table_size_hint_provider import EmptyTableSizeHintProvider
from ..mvcmodels.compound_models import (
    CompoundEntityAlternativeModel,
    CompoundEntityModel,
    CompoundParameterDefinitionModel,
    CompoundParameterValueModel,
    CompoundStackedModel,
)
from ..mvcmodels.empty_models import (
    EmptyEntityAlternativeModel,
    EmptyModelBase,
    EmptyParameterDefinitionModel,
    EmptyParameterValueModel,
)
from ..selection_for_filtering import AlternativeSelection, EntitySelection, ScenarioSelection
from ..stacked_table_seam import StackedTableSeam
from .custom_qwidgets import AddedEntitiesPopup
from .element_name_list_editor import ElementNameListEditor


class StackedViewMixin:
    """Provides stacked parameter tables for the Spine db editor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parameter_value_model = CompoundParameterValueModel(self, self.db_mngr)
        self.parameter_definition_model = CompoundParameterDefinitionModel(self, self.db_mngr)
        self.entity_alternative_model = CompoundEntityAlternativeModel(self, self.db_mngr)
        self.entity_model = CompoundEntityModel(self, self.db_mngr)
        self._all_stacked_models = {
            self.parameter_value_model: self.ui.tableView_parameter_value,
            self.parameter_definition_model: self.ui.tableView_parameter_definition,
            self.entity_alternative_model: self.ui.tableView_entity_alternative,
            self.entity_model: self.ui.entity_table_view,
        }
        self._dock_by_item_type = {}
        for model, view in self._all_stacked_models.items():
            view.setModel(model)
            dock = view.parent().parent()
            self._dock_by_item_type[model.item_type] = dock
            view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
            horizontal_header = view.horizontalHeader()
            horizontal_header.setSectionsMovable(True)
            view.connect_spine_db_editor(self)
        self.empty_parameter_definition_model = EmptyParameterDefinitionModel(self.db_mngr, self)
        self.empty_parameter_value_model = EmptyParameterValueModel(self.db_mngr, self)
        self.empty_entity_alternative_model = EmptyEntityAlternativeModel(self.db_mngr, self)
        self._all_empty_models = {
            self.empty_parameter_definition_model: self.ui.empty_parameter_definition_table_view,
            self.empty_parameter_value_model: self.ui.empty_parameter_value_table_view,
            self.empty_entity_alternative_model: self.ui.empty_entity_alternative_table_view,
        }
        for model, view in self._all_empty_models.items():
            view.setModel(model)
            view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
            view.connect_spine_db_editor(self)
            view.request_replace_undo_redo_actions.connect(self._replace_undo_redo_actions)
            view.request_reset_undo_redo_actions.connect(self.update_undo_redo_actions)
        self._seams: list[StackedTableSeam] = []
        self._resize_hint_providers: list[EmptyTableSizeHintProvider] = []
        for top_table, bottom_table in (
            (self.ui.tableView_parameter_value, self.ui.empty_parameter_value_table_view),
            (self.ui.tableView_parameter_definition, self.ui.empty_parameter_definition_table_view),
            (self.ui.tableView_entity_alternative, self.ui.empty_entity_alternative_table_view),
        ):
            self._seams.append(StackedTableSeam(top_table, bottom_table))
            size_hint_provider = EmptyTableSizeHintProvider(top_table, bottom_table)
            self._resize_hint_providers.append(size_hint_provider)
            bottom_table.set_size_hint_provider(size_hint_provider)
        for contents_widget, empty_table_view in (
            (self.ui.parameter_value_contents_widget, self.ui.empty_parameter_value_table_view),
            (self.ui.parameter_definition_contents_widget, self.ui.empty_parameter_definition_table_view),
            (self.ui.entity_alternative_contents_widget, self.ui.empty_entity_alternative_table_view),
        ):
            contents_widget.height_changed.connect(lambda: empty_table_view.updateGeometry())
        self._entity_ids_with_visible_values: dict[DatabaseMapping, set[TempId]] | None = {}
        self._default_row_generator = DefaultRowGenerator(self)

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        empty_model_item_types = ("parameter_definition", "parameter_value", "entity_alternative")
        for item_type in empty_model_item_types:
            table_view = getattr(self.ui, "tableView_" + item_type)
            visible_header = table_view.horizontalHeader()
            update_slot = getattr(self, "_update_empty_" + item_type + "_header_section_size")
            visible_header.sectionResized.connect(update_slot)
            move_slot = getattr(self, "_move_empty_" + item_type + "_header_section")
            visible_header.sectionMoved.connect(move_slot)
            visible_scroll_bar = getattr(self.ui, "empty_" + item_type + "_table_view").horizontalScrollBar()
            invisible_scroll_bar = table_view.horizontalScrollBar()
            visible_scroll_bar.valueChanged.connect(invisible_scroll_bar.setValue)
            invisible_scroll_bar.valueChanged.connect(visible_scroll_bar.setValue)
        for model in self._all_stacked_models:
            model.column_filter_changed.connect(self._handle_column_filters)
        self.parameter_value_model.layoutChanged.connect(self._handle_value_model_layout_changed)
        self.parameter_value_model.rowsInserted.connect(self._handle_values_inserted)
        self.empty_parameter_value_model.entities_added.connect(self._notify_about_added_entities)
        self.empty_entity_alternative_model.entities_added.connect(self._notify_about_added_entities)
        self._default_row_generator.parameter_definition_default_row_updated.connect(
            self._set_default_parameter_definition_data
        )
        self._default_row_generator.parameter_value_default_row_updated.connect(self._set_default_parameter_value_data)
        self._default_row_generator.entity_alternative_default_row_updated.connect(
            self._set_default_entity_alternative_data
        )

    def init_models(self):
        """Initializes models."""
        super().init_models()
        for model in self._all_stacked_models:
            model.reset_db_maps(self.db_maps)
            model.init_model()
        for model in self._all_empty_models:
            model.reset_db_maps(self.db_maps)
            self._set_stacked_model_default_data(DefaultRowData({}, None), model)

    @Slot(QModelIndex, object, object)
    def show_element_name_list_editor(self, index: QModelIndex, entity_class_id: TempId, db_map: DatabaseMapping):
        """Shows the element name list editor."""
        entity_class = self.db_mngr.get_item(db_map, "entity_class", entity_class_id)
        dimension_id_list = entity_class.get("dimension_id_list", ())
        dimension_names = []
        entity_byname_lists = []
        for id_ in dimension_id_list:
            dimension_name = self.db_mngr.get_item(db_map, "entity_class", id_).get("name")
            entity_name_list = [
                x["entity_byname"]
                for k in ("class_id", "superclass_id")
                for x in self.db_mngr.get_items_by_field(db_map, "entity", k, id_)
            ]
            dimension_names.append(dimension_name)
            entity_byname_lists.append(entity_name_list)
        entity_byname = index.data(Qt.ItemDataRole.EditRole)
        if entity_byname is not None:
            entity = db_map.get_item(
                "entity",
                entity_class_name=entity_class["name"],
                entity_byname=tuple(entity_byname),
            )
            current_element_byname_list = entity["element_byname_list"] if entity else []
        else:
            current_element_byname_list = []
        editor = ElementNameListEditor(self, index, dimension_names, entity_byname_lists, current_element_byname_list)
        editor.show()

    @Slot(object)
    def _set_default_parameter_definition_data(self, default_data: DefaultRowData) -> None:
        self._set_stacked_model_default_data(default_data, self.empty_parameter_definition_model)

    @Slot(object)
    def _set_default_parameter_value_data(self, default_data: DefaultRowData) -> None:
        self._set_stacked_model_default_data(default_data, self.empty_parameter_value_model)

    @Slot(object)
    def _set_default_entity_alternative_data(self, default_data: DefaultRowData) -> None:
        self._set_stacked_model_default_data(default_data, self.empty_entity_alternative_model)

    def _set_stacked_model_default_data(self, default_data: DefaultRowData, model: EmptyModelBase) -> None:
        if default_data.default_db_map is not None:
            db_map = default_data.default_db_map
        else:
            db_map = self.db_maps[0]
        database_name = self.db_mngr.name_registry.display_name(db_map.sa_url)
        model.set_default_row(database=database_name, **default_data.default_data)
        model.set_rows_to_default(model.rowCount() - 1)
        model.db_map = db_map

    def clear_all_filters(self):
        for model in self._all_stacked_models:
            model.clear_auto_filter()
        trees = [self.ui.treeView_entity, self.ui.scenario_tree_view, self.ui.alternative_tree_view]
        for tree in trees:
            tree.selectionModel().clearSelection()

    @Slot(object)
    def _set_entity_selection_filter_for_stacked_tables(self, entity_selection: EntitySelection) -> None:
        for model in self._all_stacked_models:
            model.set_entity_selection_for_filtering(entity_selection)
        self._entity_ids_with_visible_values = None

    @Slot(object)
    def _set_alternative_selection_filter_for_stacked_tables(self, alternative_selection: AlternativeSelection) -> None:
        for model in (self.parameter_value_model, self.entity_alternative_model):
            model.set_alternative_selection_for_filtering(alternative_selection)

    @Slot(object)
    def _set_scenario_selection_filter_for_stacekd_tables(self, scenario_selection: ScenarioSelection) -> None:
        self.entity_model.set_scenario_selection_for_filtering(scenario_selection)

    @Slot(QModelIndex, int, int)
    def _handle_values_inserted(self, parent: QModelIndex, first: int, last: int) -> None:
        self._clear_table_related_caches()

    @Slot(list, QAbstractItemModel.LayoutChangeHint)
    def _handle_value_model_layout_changed(
        self, parents: list[QPersistentModelIndex], hint: QAbstractItemModel.LayoutChangeHint
    ) -> None:
        self._clear_table_related_caches()

    def _clear_table_related_caches(self) -> None:
        self._entity_ids_with_visible_values = None

    def _recalculate_entity_ids_with_visible_values(self) -> None:
        entity_ids = {}
        for row in range(self.parameter_value_model.rowCount()):
            index = self.parameter_value_model.index(row, 0)
            value_item = self.parameter_value_model.data(index, ITEM_ROLE)
            entity_ids.setdefault(value_item.db_map, set()).add(value_item["entity_id"])
        self._entity_ids_with_visible_values = entity_ids

    @Slot(int, int, int)
    def _update_empty_parameter_definition_header_section_size(self, logical_index, old_size, new_size):
        header = self.ui.empty_parameter_definition_table_view.horizontalHeader()
        header.resizeSection(logical_index, new_size)

    @Slot(int, int, int)
    def _move_empty_parameter_definition_header_section(self, logical_index, old_visual_index, new_visual_index):
        header = self.ui.empty_parameter_definition_table_view.horizontalHeader()
        header.moveSection(old_visual_index, new_visual_index)

    @Slot(int, int, int)
    def _update_empty_parameter_value_header_section_size(self, logical_index, old_size, new_size):
        header = self.ui.empty_parameter_value_table_view.horizontalHeader()
        header.resizeSection(logical_index, new_size)

    @Slot(int, int, int)
    def _move_empty_parameter_value_header_section(self, logical_index, old_visual_index, new_visual_index):
        header = self.ui.empty_parameter_value_table_view.horizontalHeader()
        header.moveSection(old_visual_index, new_visual_index)

    @Slot(int, int, int)
    def _update_empty_entity_alternative_header_section_size(self, logical_index, old_size, new_size):
        header = self.ui.empty_entity_alternative_table_view.horizontalHeader()
        header.resizeSection(logical_index, new_size)

    @Slot(int, int, int)
    def _move_empty_entity_alternative_header_section(self, logical_index, old_visual_index, new_visual_index):
        header = self.ui.empty_entity_alternative_table_view.horizontalHeader()
        header.moveSection(old_visual_index, new_visual_index)

    @Slot(object)
    def _notify_about_added_entities(self, added_entities) -> None:
        popup = AddedEntitiesPopup(self, self.db_mngr.name_registry, added_entities)
        popup.show()

    @Slot(QAbstractTableModel)
    def _handle_column_filters(self, model: CompoundStackedModel) -> None:
        dock = self._dock_by_item_type[model.item_type]
        table_name = self.table_name_from_item_type[model.item_type]
        if not any(model.column_filters.values()):
            dock.setWindowTitle(table_name)
            self.set_dock_tab_color(dock, None)
            return
        self.set_dock_tab_color(dock, QColor("paleturquoise"))
        table_name += (
            f" [COLUMN FILTERS: {', '.join([name for name, active in model.column_filters.items() if active])}]"
        )
        dock.setWindowTitle(table_name)

    def tear_down(self):
        if not super().tear_down():
            return False
        for model in self._all_stacked_models:
            model.stop_invalidating_filter()
        return True

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            for view in self._all_empty_models.values():
                view.request_replace_undo_redo_actions.disconnect(self._replace_undo_redo_actions)
                view.request_reset_undo_redo_actions.disconnect(self.update_undo_redo_actions)
