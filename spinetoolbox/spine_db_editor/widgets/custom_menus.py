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

"""Classes for custom context menus and pop-up menus."""
from collections.abc import Callable, Iterator
from typing import Any, Hashable
from PySide6.QtCore import QPoint, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QWidget
from spinedb_api import DatabaseMapping, IndexedValue
from spinedb_api.db_mapping_base import PublicItem
from spinedb_api.helpers import ItemType
from spinedb_api.temp_id import TempId
from ...database_display_names import NameRegistry
from ...fetch_parent import FlexibleFetchParent
from ...helpers import CustomPopupMenu, DBMapPublicItems
from ...mvcmodels.filter_checkbox_list_model import SimpleFilterCheckboxListModel
from ...spine_db_manager import SpineDBManager
from ...widgets.custom_menus import FilterMenuBase
from ..mvcmodels.compound_models import CompoundStackedModel
from ..mvcmodels.lazy_filter_checkbox_list_model import LazyFilterCheckboxListModel
from ..mvcmodels.utils import field_index
from .tabular_view_header_widget import TabularViewHeaderWidget


class AutoFilterMenu(FilterMenuBase[str]):
    filter_changed = Signal(str, object)

    def __init__(self, parent: QWidget | None, model: CompoundStackedModel, field: str):
        super().__init__(parent)
        self._set_up(SimpleFilterCheckboxListModel(self, show_empty=True))
        self._source_model = model
        self._field: str = field
        self._field_index: int = field_index(field, model.field_map)
        self._display_value_to_edit_data: dict[str, Hashable] | None = None
        self.aboutToShow.connect(self._populate_data)

    def set_filter_accepted_values(self, accepted_values: set[str]) -> None:
        self._apply_filter_with_condition(lambda x: x in accepted_values)

    def set_filter_rejected_values(self, rejected_values: set[str]) -> None:
        self._apply_filter_with_condition(lambda x: x not in rejected_values)

    def _apply_filter_with_condition(self, condition: Callable[[str], bool]) -> None:
        self._populate_data()
        self.filter.model().filter_by_condition(condition)
        self.filter.apply_filter()

    @Slot()
    def _populate_data(self) -> None:
        if self._field in self._source_model.FIELDS_REQUIRING_FILTER_DATA_CONVERSION:
            self._display_value_to_edit_data = self._source_model.auto_filter_data_map(self._field_index)
            filter_data = [x for x in self._display_value_to_edit_data if x]
        else:
            filter_data = self._source_model.auto_filter_data_list(self._field_index)
        self.filter.model().set_list(filter_data, all_selected=True)

    def emit_filter_changed(self, valid_values: set[str | None]) -> None:
        """
        Builds auto filter and emits signal.

        Args:
            valid_values: Values accepted by the filter.
        """
        if self.filter.model().all_selected:
            self.filter_changed.emit(self._field, None)
            return
        if self._display_value_to_edit_data is not None:
            if None in valid_values:
                if None not in self._display_value_to_edit_data:
                    valid_values.remove(None)
                if "" in self._display_value_to_edit_data:
                    valid_values.add("")
            values = {self._display_value_to_edit_data[value] for value in valid_values}
        else:
            if None in valid_values:
                valid_values.add("")
            values = valid_values
        self.filter_changed.emit(self._field, values)


class TabularViewFilterMenuBase(FilterMenuBase):

    filter_changed = Signal(str, set, bool)

    def __init__(self, parent: QWidget | None, identifier: str):
        """
        Args:
            parent: parent widget
            identifier: header identifier
        """
        super().__init__(parent)
        self.anchor: TabularViewHeaderWidget | None = None
        self._identifier = identifier

    def showEvent(self, event):
        if self.anchor is not None:
            if self.anchor.area == "rows":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(0, self.anchor.height())
            elif self.anchor.area == "columns":
                pos = self.anchor.mapToGlobal(QPoint(0, 0)) + QPoint(self.anchor.width(), 0)
            else:
                raise RuntimeError(f"Unknown anchor area '{self.anchor.area}'")
            self.move(pos)
        super().showEvent(event)


class TabularViewDBItemFilterMenu(TabularViewFilterMenuBase):
    """Filter menu to use together with FilterWidget in TabularViewMixin."""

    def __init__(
        self,
        parent: QWidget | None,
        db_mngr: SpineDBManager,
        db_maps: list[DatabaseMapping],
        item_type: ItemType,
        accepts_item: Callable[[PublicItem, DatabaseMapping], bool],
        identifier: str,
        show_empty: bool = True,
    ):
        """
        Args:
            parent: parent widget
            db_mngr: database manager
            db_maps: database mappings
            item_type: database item type to filter
            accepts_item: callable that returns True when database item is accepted
            identifier: header identifier
            show_empty: if True, an empty row will be added to the end of the item list
        """
        super().__init__(parent, identifier)
        self._db_mngr = db_mngr
        self._item_type = item_type
        self._menu_data = {}
        fetch_parent = FlexibleFetchParent(
            self._item_type,
            handle_items_added=self._handle_items_added,
            handle_items_removed=self._handle_items_removed,
            accepts_item=accepts_item,
            owner=self,
            chunk_size=None,
        )
        filter_model = LazyFilterCheckboxListModel(self, db_mngr, db_maps, fetch_parent, show_empty=show_empty)
        self._set_up(filter_model)

    def _handle_items_added(self, db_map_data: DBMapPublicItems) -> None:
        to_add = set()
        for db_map, items in db_map_data.items():
            for item in items:
                for display_value, value in self._get_values(db_map, item):
                    to_add.add(display_value)
                    self._menu_data.setdefault(display_value, set()).add(value)
        self.add_items_to_filter_list(to_add)

    def _get_values(
        self, db_map: DatabaseMapping, item
    ) -> Iterator[tuple[str, tuple[DatabaseMapping, TempId] | tuple[None, Any]]]:
        if self._item_type == "parameter_value":
            if isinstance(item, PublicItem):
                for index in self._db_mngr.get_value_indexes(db_map, "parameter_value", item["id"]):
                    yield str(index), (None, index)
            else:
                if isinstance(item.parsed_value, IndexedValue):
                    for index in item.parsed_value.indexes:
                        yield str(index), (None, index)
                else:
                    yield "", (None, "")
        else:
            yield item["name"], (db_map, item["id"])

    def _handle_items_removed(self, db_map_data: DBMapPublicItems) -> None:
        for db_map, items in db_map_data.items():
            for item in items:
                for display_value, value in self._get_values(db_map, item):
                    self._menu_data.get(display_value, set()).discard(value)
        to_remove = {display_value for display_value, data in self._menu_data.items() if not data}
        for display_value in to_remove:
            del self._menu_data[display_value]
        self.remove_items_from_filter_list(to_remove)

    def emit_filter_changed(self, valid_values):
        valid_values = {db_map_id for v in valid_values for db_map_id in self._menu_data[v]}
        self.filter_changed.emit(self._identifier, valid_values, self.filter.has_filter())


class TabularViewDatabaseNameFilterMenu(TabularViewFilterMenuBase):
    """Filter menu to filter database names in Pivot table."""

    def __init__(
        self,
        parent: QWidget | None,
        db_maps: list[DatabaseMapping],
        identifier: str,
        db_name_registry: NameRegistry,
        show_empty: bool = True,
    ):
        """
        Args:
            parent: parent widget
            db_maps: database mappings
            identifier: header identifier
            db_name_registry: database display name registry
            show_empty: if True, an empty row will be added to the end of the item list
        """
        super().__init__(parent, identifier)
        filter_model = SimpleFilterCheckboxListModel(self, show_empty=show_empty)
        self._set_up(filter_model)
        self.filter.set_filter_list(list(db_name_registry.display_name_iter(db_maps)))

    def emit_filter_changed(self, valid_values):
        """See base class."""
        self.filter_changed.emit(self._identifier, valid_values, self.filter.has_filter())


class RecentDatabasesPopupMenu(CustomPopupMenu):
    """Recent databases menu embedded to 'File-Open recent' QAction."""

    load_url_requested = Signal(str, str)
    clear_url_history_requested = Signal()

    def __init__(self, parent: QWidget | None):
        super().__init__(parent=parent)
        self.setToolTipsVisible(True)
        self._separator = self.addSeparator()
        self._clear_action = self.add_action(
            "Clear",
            lambda: self.clear_url_history_requested.emit(),
            icon=QIcon(":icons/menu_icons/trash-alt.svg"),
        )

    def update_history(self, history: list[tuple[str, str]]) -> None:
        self._clear_action.setEnabled(bool(history))
        for action in self.actions():
            if action is self._separator:
                break
            self.removeAction(action)
        for row in history:
            url, name = row
            action = QAction(name)
            action.setToolTip(url)
            action.triggered.connect(lambda _, url=url, name=name: self.load_url_requested.emit(url, name))
            self.insertAction(self._separator, action)


class DocksMenu(QMenu):
    """Menu that houses the toggles for the dock widgets."""

    def __init__(self, parent, db_editor):
        """
        Args:
            parent (SpineDBEditor): Parent widget of this menu (SpineDBEditor)
        """
        super().__init__(parent=parent)
        self.db_editor = db_editor
        self._add_actions()

    def _add_actions(self):
        """Adds actions to the menu"""
        reset_docks_action = QAction("Reset docks", self)
        reset_docks_action.triggered.connect(self.db_editor.reset_docks)
        self.addAction(reset_docks_action)
        self.addAction(self.db_editor.ui.dockWidget_entity_tree.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_entity_tree.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_parameter_value.toggleViewAction())
        self.addAction(self.db_editor.ui.dockWidget_parameter_definition.toggleViewAction())
        self.addAction(self.db_editor.ui.dockWidget_entity_alternative.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_pivot_table.toggleViewAction())
        self.addAction(self.db_editor.ui.dockWidget_frozen_table.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_entity_graph.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_parameter_value_list.toggleViewAction())
        self.addAction(self.db_editor.ui.alternative_dock_widget.toggleViewAction())
        self.addAction(self.db_editor.ui.scenario_dock_widget.toggleViewAction())
        self.addAction(self.db_editor.ui.metadata_dock_widget.toggleViewAction())
        self.addAction(self.db_editor.ui.item_metadata_dock_widget.toggleViewAction())
        self.addSeparator()
        self.addAction(self.db_editor.ui.dockWidget_exports.toggleViewAction())
