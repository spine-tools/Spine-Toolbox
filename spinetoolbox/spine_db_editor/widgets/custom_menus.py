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
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu
from spinedb_api import IndexedValue
from spinedb_api.db_mapping_base import PublicItem
from ...fetch_parent import FlexibleFetchParent
from ...helpers import DB_ITEM_SEPARATOR, CustomPopupMenu
from ...mvcmodels.filter_checkbox_list_model import LazyFilterCheckboxListModel, SimpleFilterCheckboxListModel
from ...widgets.custom_menus import FilterMenuBase


class AutoFilterMenu(FilterMenuBase):
    filterChanged = Signal(str, object)

    def __init__(self, parent, db_mngr, db_maps, item_type, field, show_empty=True):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_mngr (SpineDBManager)
            db_maps (Sequence of DatabaseMapping)
            item_type (str)
            field (str): the field name
            show_empty (bool)
        """
        super().__init__(parent)
        self._item_type = item_type
        self._db_mngr = db_mngr
        self._field = field
        self._menu_data = {}  # Maps display value to set of (db map, entity_class_id, actual value) tuples
        fetch_parent = FlexibleFetchParent(
            self._item_type,
            handle_items_added=self._handle_items_added,
            handle_items_removed=self._handle_items_removed,
            owner=self,
            chunk_size=None,
        )
        self._set_up(LazyFilterCheckboxListModel, self, db_mngr, db_maps, fetch_parent, show_empty=show_empty)

    def set_filter_accepted_values(self, accepted_values):
        if self._filter._filter_model.canFetchMore(None):
            self._filter._filter_model.fetchMore(None)
        self._filter._filter_model.filter_by_condition(lambda x: x in accepted_values)
        self._filter._apply_filter()

    def set_filter_rejected_values(self, rejected_values):
        if self._filter._filter_model.canFetchMore(None):
            self._filter._filter_model.fetchMore(None)
        self._filter._filter_model.filter_by_condition(lambda x: x not in rejected_values)
        self._filter._apply_filter()

    def _get_value(self, item, db_map):
        if self._field == "database":
            return self._db_mngr.name_registry.display_name(db_map.sa_url)
        return item[self._field]

    def _get_display_value(self, item, db_map):
        if self._field in ("value", "default_value"):
            return self._db_mngr.get_value(db_map, item, role=Qt.ItemDataRole.DisplayRole)
        if self._field == "entity_byname":
            return DB_ITEM_SEPARATOR.join(item[self._field])
        return self._get_value(item, db_map) or "(empty)"

    def _handle_items_added(self, db_map_data):
        to_add = set()
        for db_map, items in db_map_data.items():
            for item in items:
                display_value = self._get_display_value(item, db_map)
                value = self._get_value(item, db_map)
                to_add.add(display_value)
                self._menu_data.setdefault(display_value, set()).add((db_map, item["entity_class_id"], value))
        self.add_items_to_filter_list(to_add)

    def _handle_items_removed(self, db_map_data):
        for db_map, items in db_map_data.items():
            for item in items:
                display_value = self._get_display_value(item, db_map)
                value = self._get_value(item, db_map)
                self._menu_data.get(display_value, set()).discard((db_map, item["entity_class_id"], value))
        to_remove = {display_value for display_value, data in self._menu_data.items() if not data}
        for display_value in to_remove:
            del self._menu_data[display_value]
        self.remove_items_from_filter_list(to_remove)

    def _build_auto_filter(self, valid_values):
        """
        Builds the auto filter given valid values.

        Args:
            valid_values (Sequence): Values accepted by the filter.

        Returns:
            dict: mapping (db_map, entity_class_id) to set of valid values
        """
        if not self._filter.has_filter():
            return {}  # All-pass
        if not valid_values:
            return None  # You shall not pass
        auto_filter = {}
        for display_value in valid_values:
            for db_map, entity_class_id, value in self._menu_data[display_value]:
                auto_filter.setdefault((db_map, entity_class_id), set()).add(value)
        return auto_filter

    def emit_filter_changed(self, valid_values):
        """
        Builds auto filter and emits signal.

        Args:
            valid_values (Sequence): Values accepted by the filter.
        """
        auto_filter = self._build_auto_filter(valid_values)
        self.filterChanged.emit(self._field, auto_filter)


class TabularViewFilterMenuBase(FilterMenuBase):

    filterChanged = Signal(str, set, bool)

    def __init__(self, parent, identifier):
        """
        Args:
            parent (SpineDBEditor): parent widget
            identifier (str): header identifier
        """
        super().__init__(parent)
        self.anchor = parent
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

    def __init__(self, parent, db_mngr, db_maps, item_type, accepts_item, identifier, show_empty=True):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_mngr (SpineDBManager): database manager
            db_maps (Sequence of DatabaseMapping): database mappings
            item_type (str): database item type to filter
            accepts_item (Callable): callable that returns True when database item is accepted
            identifier (str): header identifier
            show_empty (bool): if True, an empty row will be added to the end of the item list
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
        self._set_up(LazyFilterCheckboxListModel, self, db_mngr, db_maps, fetch_parent, show_empty=show_empty)

    def _handle_items_added(self, db_map_data):
        to_add = set()
        for db_map, items in db_map_data.items():
            for item in items:
                for display_value, value in self._get_values(db_map, item):
                    to_add.add(display_value)
                    self._menu_data.setdefault(display_value, set()).add(value)
        self.add_items_to_filter_list(to_add)

    def _get_values(self, db_map, item):
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

    def _handle_items_removed(self, db_map_data):
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
        self.filterChanged.emit(self._identifier, valid_values, self._filter.has_filter())


class TabularViewDatabaseNameFilterMenu(TabularViewFilterMenuBase):
    """Filter menu to filter database names in Pivot table."""

    def __init__(self, parent, db_maps, identifier, db_name_registry, show_empty=True):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_maps (Sequence of DatabaseMapping): database mappings
            identifier (str): header identifier
            db_name_registry (NameRegistry): database display name registry
            show_empty (bool): if True, an empty row will be added to the end of the item list
        """
        super().__init__(parent, identifier)
        self._set_up(SimpleFilterCheckboxListModel, self, show_empty=show_empty)
        self._filter.set_filter_list(list(db_name_registry.display_name_iter(db_maps)))

    def emit_filter_changed(self, valid_values):
        """See base class."""
        self.filterChanged.emit(self._identifier, valid_values, self._filter.has_filter())


class RecentDatabasesPopupMenu(CustomPopupMenu):
    """Recent databases menu embedded to 'File-Open recent' QAction."""

    def __init__(self, parent):
        """
        Args:
            parent (SpineDBEditor): Parent widget of this menu (SpineDBEditor)
        """
        super().__init__(parent=parent)
        self._parent = parent
        self.setToolTipsVisible(True)
        self.add_recent_dbs()
        self.addSeparator()
        self.add_action(
            "Clear",
            self.clear_recents,
            enabled=self.has_recents(),
            icon=QIcon(":icons/menu_icons/trash-alt.svg"),
        )

    def has_recents(self):
        """Returns True if there are recent DBs."""
        return bool(self._parent._history)

    def add_recent_dbs(self):
        """Adds opened db maps top recently opened. Adds them to the QMenu as QActions."""
        for row in self._parent._history:
            for name, url in row.items():
                self.add_action(
                    name,
                    lambda name=name, url=url: self._parent.load_db_urls({url: name}),
                    tooltip=url,
                )

    @Slot(bool)
    def clear_recents(self):
        """Slot to clear the history of the db editor."""
        self._parent._history = []


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
