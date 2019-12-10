######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains TabularViewForm class and some related constants.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from collections import namedtuple
from PySide2.QtCore import Qt, Slot
from .custom_menus import FilterMenu, PivotTableModelMenu, PivotTableHorizontalHeaderMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from .custom_delegates import PivotTableDelegate
from ..helpers import fix_name_ambiguity, busy_effect
from ..mvcmodels.pivot_table_models import PivotTableSortFilterProxy, PivotTableModel
from ..mvcmodels.frozen_table_model import FrozenTableModel


class TabularViewMixin:
    """Provides the pivot table and its frozen table for the DS form."""

    # constant strings
    _RELATIONSHIP_CLASS = "relationship class"
    _OBJECT_CLASS = "object class"

    _INPUT_VALUE = "Parameter value"
    _INPUT_ENTITY = "Entity"

    _PARAMETER_NAME = "parameter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # current state of ui
        self.current_class_type = ''
        self.current_class_id = ''
        self.current_input_type = self._INPUT_VALUE
        self.relationships = {}
        self.object_classes = {}
        self.objects = {}
        self.filter_menus = {}
        self.index_values = {}  # Maps index id to a sorted set of values for that index
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])
        self.ui.comboBox_pivot_table_input_type.addItems([self._INPUT_VALUE, self._INPUT_ENTITY])
        self.pivot_table_proxy = PivotTableSortFilterProxy()
        self.pivot_table_model = PivotTableModel(self)
        self.pivot_table_proxy.setSourceModel(self.pivot_table_model)
        self.frozen_table_model = FrozenTableModel(self)
        self.ui.pivot_table.setModel(self.pivot_table_proxy)
        self.ui.frozen_table.setModel(self.frozen_table_model)
        self.ui.pivot_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.pivot_table.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.frozen_table.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.pivot_table.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.pivot_table_menu = PivotTableModelMenu(self)

        self._pivot_table_horizontal_header_menu = PivotTableHorizontalHeaderMenu(
            self.pivot_table_model, self.ui.pivot_table
        )

    @Slot(dict, dict)
    def table_index_entries_changed(self, added_entries, deleted_entries):
        """
        Updates the filter menus whenever objects are added or removed.
        """
        for menu in self.filter_menus.values():
            if menu.object_class_name in deleted_entries:
                menu.remove_items_from_filter_list(deleted_entries[menu.object_class_name])
            if menu.object_class_name in added_entries:
                menu.add_items_to_filter_list(added_entries[menu.object_class_name])

    def is_value_input_type(self):
        return self.current_input_type == self._INPUT_VALUE

    def setup_delegates(self):
        """Sets delegates for tables."""
        super().setup_delegates()
        delegate = PivotTableDelegate(self)
        self.ui.pivot_table.setItemDelegate(delegate)
        delegate.parameter_value_editor_requested.connect(self.show_parameter_value_editor)
        delegate.data_committed.connect(self._set_model_data)

    @Slot("QModelIndex", object)
    def _set_model_data(self, index, value):
        self.pivot_table_proxy.setData(index, value)

    def add_toggle_view_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_toggle_view_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_pivot_table.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_frozen_table.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.treeView_object.selectionModel().selectionChanged.connect(self._handle_entity_tree_selection_changed)
        self.ui.treeView_relationship.selectionModel().selectionChanged.connect(
            self._handle_entity_tree_selection_changed
        )
        self.ui.pivot_table.customContextMenuRequested.connect(self.pivot_table_menu.request_menu)
        self.ui.pivot_table.horizontalHeader().customContextMenuRequested.connect(
            self._pivot_table_horizontal_header_menu.request_menu
        )
        # TODO: self.pivot_table_model.index_entries_changed.connect(self.table_index_entries_changed)
        self.pivot_table_model.modelReset.connect(self.make_pivot_headers)
        self.ui.pivot_table.horizontalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.pivot_table.verticalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.selectionModel().currentChanged.connect(self.change_frozen_value)
        self.ui.comboBox_pivot_table_input_type.currentTextChanged.connect(self.reload_pivot_table)
        self.ui.dockWidget_pivot_table.visibilityChanged.connect(self._handle_pivot_table_visibility_changed)
        self.ui.dockWidget_frozen_table.visibilityChanged.connect(self._handle_frozen_table_visibility_changed)

    def _new_relationship_parameter_value(self, object_ids, value):
        """Returns a new parameter value item to insert to the db.

        Args:
            object_ids (tuple(int)):
            value
        Returns:
            dict
        """
        object_id_list = ",".join([str(id_) for id_ in object_ids])
        relationships = self.db_mngr.get_items(self.db_map, "relationship")
        relationship = next(
            iter(
                rel
                for rel in relationships
                if rel["class_id"] == self.current_class_id and rel["object_id_list"] == object_id_list
            )
        )
        return dict(relationship_id=relationship["id"], value=value)

    def add_parameter_value(self, id_tuple, value):
        """
        Args:
            id_tuple (tuple(int)): object_ids + parameter_id
            value
        """
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            item = self._new_relationship_parameter_value(id_tuple[:-1], value)
        else:
            object_id = id_tuple[0]
            item = dict(object_id=object_id, value=value)
        parameter_id = id_tuple[-1]
        item["parameter_definition_id"] = parameter_id
        self.db_mngr.add_parameter_values({self.db_map: [item]})

    def update_parameter_value(self, id_, value):
        """
        Args:
            id_ (int)
            value
        """
        db_map_data = {self.db_map: [dict(id=id_, value=value)]}
        self.db_mngr.update_parameter_values(db_map_data)

    @Slot(bool)
    def rollback_session(self, checked=False):
        super().rollback_session()
        self.reload_pivot_table()

    def current_object_class_id_list(self):
        if self.current_class_type == self._OBJECT_CLASS:
            return [self.current_class_id]
        relationship_class = self.db_mngr.get_item(self.db_map, "relationship class", self.current_class_id)
        return [int(id_) for id_ in relationship_class["object_class_id_list"].split(",")]

    def current_object_class_name_list(self):
        if self.current_class_type == self._OBJECT_CLASS:
            return [self.db_mngr.get_item(self.db_map, "object class", self.current_class_id)["name"]]
        relationship_class = self.db_mngr.get_item(self.db_map, "relationship class", self.current_class_id)
        return fix_name_ambiguity(relationship_class["object_class_name_list"].split(","))

    @staticmethod
    def _is_class_index(index, class_type):
        """Returns whether or not the given index is a class index.

        Args:
            index (QModelIndex): index from object or relationship tree
            class_type (str)
        Returns:
            bool
        """
        return index.column() == 0 and index.model().item_from_index(index).item_type == class_type

    @Slot(bool)
    def _handle_pivot_table_visibility_changed(self, visible):
        if visible:
            self.reload_pivot_table()
            self.reload_frozen_table()
        self.ui.dockWidget_frozen_table.setVisible(self.ui.dockWidget_pivot_table.isVisible())

    @Slot(bool)
    def _handle_frozen_table_visibility_changed(self, visible):
        if visible:
            self.ui.dockWidget_pivot_table.show()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_entity_tree_selection_changed(self, selected, deselected):
        if self.ui.dockWidget_pivot_table.isVisible():
            self.reload_pivot_table()
            self.reload_frozen_table()

    def _get_parameter_data(self, item_type):
        """Returns a list of dict items from the parameter model
        corresponding to the currently selected class and the given item type.

        Args:
            item_type (str): either "parameter value" or "parameter definition"

        Returns:
            list(dict)
        """
        entity_class = self.db_mngr.get_item(self.db_map, self.current_class_type, self.current_class_id)
        model = {
            self._OBJECT_CLASS: {
                "parameter value": self.object_parameter_value_model,
                "parameter definition": self.object_parameter_definition_model,
            },
            self._RELATIONSHIP_CLASS: {
                "parameter value": self.relationship_parameter_value_model,
                "parameter definition": self.relationship_parameter_definition_model,
            },
        }[self.current_class_type][item_type]
        sub_models = [
            m for m in model.single_models if (m.db_map, m.entity_class_id) == (self.db_map, entity_class["id"])
        ]
        if not sub_models:
            return []
        for m in sub_models:
            if m.canFetchMore():
                model._fetch_sub_model = m
                model.fetchMore()
        ids = [id_ for m in sub_models for id_ in m._main_data]
        return [self.db_mngr.get_item(self.db_map, item_type, id_) for id_ in ids]

    def _get_entities(self):
        """Returns a list of dict items from the object or relationship tree model
        corresponding to the currently selected class.

        Returns:
            list(dict)
        """
        entity_class = self.db_mngr.get_item(self.db_map, self.current_class_type, self.current_class_id)
        model = {self._OBJECT_CLASS: self.object_tree_model, self._RELATIONSHIP_CLASS: self.relationship_tree_model}[
            self.current_class_type
        ]
        entity_class_item = next(model.root_item.find_children_by_id(self.db_map, entity_class["id"]))
        if entity_class_item.can_fetch_more():
            entity_class_item.fetch_more()
        return [item.db_map_data(self.db_map) for item in entity_class_item.find_children_by_id(self.db_map, True)]

    def get_parameter_value_data(self):
        """Returns a dict with parameter value data for resetting the pivot table model.

        Returns:
            dict
        """
        parameter_values = self._get_parameter_data("parameter value")
        parameter_ids = {x["id"] for x in self._get_parameter_data("parameter definition")}
        entities = self.get_entity_data().keys()
        data = {entity + (parameter_id,): None for entity in entities for parameter_id in parameter_ids}
        if self.current_class_type == self._OBJECT_CLASS:
            data.update({(x["object_id"], x["parameter_id"]): x["id"] for x in parameter_values})
            return data
        data.update(
            {
                tuple(int(id_) for id_ in x["object_id_list"].split(',')) + (x["parameter_id"],): x["id"]
                for x in parameter_values
            }
        )
        return data

    def get_entity_data(self):
        """Returns a dict with entity data for resetting the pivot table model.

        Returns:
            dict
        """
        entities = self._get_entities()
        marker = '\u274C'
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            return {tuple(int(id_) for id_ in e["object_id_list"].split(',')): marker for e in entities}
        return {(e["id"],): marker for e in entities}

    def get_pivot_preferences(self, selection_key):
        """Returns saved or default pivot preferences.

        Args:
            selection_key (tuple(int,str,str)): Tuple of class id, class type, and input type.

        Returns
            list: indexes in rows
            list: indexes in columns
            list: frozen indexes
            tuple: selection in frozen table
        """
        if selection_key in self.class_pivot_preferences:
            # get previously used pivot
            rows = self.class_pivot_preferences[selection_key].index
            columns = self.class_pivot_preferences[selection_key].columns
            frozen = self.class_pivot_preferences[selection_key].frozen
            frozen_value = self.class_pivot_preferences[selection_key].frozen_value
        else:
            # use default pivot
            length = len(self.current_object_class_id_list())
            rows = list(range(length))
            columns = [-1] if self.current_input_type == self._INPUT_VALUE else []
            frozen = []
            frozen_value = ()
        return rows, columns, frozen, frozen_value

    def reload_pivot_table(self):
        """Refreshes pivot table."""
        if self._selection_source == self.ui.treeView_object:
            selected = self.ui.treeView_object.selectionModel().currentIndex()
            class_type = self._OBJECT_CLASS
        elif self._selection_source == self.ui.treeView_relationship:
            selected = self.ui.treeView_relationship.selectionModel().currentIndex()
            class_type = self._RELATIONSHIP_CLASS
        else:
            return
        if self._is_class_index(selected, class_type):
            self.current_class_type = class_type
            selected_item = selected.model().item_from_index(selected)
            self.current_class_id = selected_item.db_map_id(self.db_map)
            self.do_refresh_pivot_table()

    @busy_effect
    def do_refresh_pivot_table(self):
        """Refreshes pivot table.
        """
        self.current_input_type = self.ui.comboBox_pivot_table_input_type.currentText()
        length = len(self.current_object_class_id_list())
        index_ids = tuple(range(length))  # NOTE: the index id is just the index in the current object class id list
        if self.current_input_type == self._INPUT_VALUE:
            data = self.get_parameter_value_data()
            index_ids += (-1,)  # NOTE: -1 is the index id of the 'parameter' index
        else:
            data = self.get_entity_data()
        if not data:
            self.index_values = {id_: [] for id_ in index_ids}
        else:
            data_keys = list(zip(*data.keys()))
            self.index_values = {id_: data_keys[k] for k, id_ in enumerate(index_ids)}
        # get pivot preference for current selection
        selection_key = (self.current_class_id, self.current_class_type, self.current_input_type)
        rows, columns, frozen, frozen_value = self.get_pivot_preferences(selection_key)
        self.filter_menus.clear()
        self.pivot_table_model.reset_model(data, index_ids, rows, columns, frozen, frozen_value)
        self.pivot_table_proxy.clear_filter()

    @Slot()
    def make_pivot_headers(self):
        """
        Turns top left indexes in the pivot table into TabularViewHeaderWidget.
        """
        top_indexes, left_indexes = self.pivot_table_model.top_left_indexes()
        for index in left_indexes:
            proxy_index = self.pivot_table_proxy.mapFromSource(index)
            widget = self.create_header_widget(proxy_index.data(Qt.DisplayRole), "columns")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
        for index in top_indexes:
            proxy_index = self.pivot_table_proxy.mapFromSource(index)
            widget = self.create_header_widget(proxy_index.data(Qt.DisplayRole), "rows")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
            self.ui.pivot_table.resizeColumnToContents(index.column())

    def make_frozen_headers(self):
        """
        Turns indexes in the first row of the frozen table into TabularViewHeaderWidget.
        """
        for column in range(self.frozen_table_model.columnCount()):
            index = self.frozen_table_model.index(0, column)
            widget = self.create_header_widget(index.data(Qt.DisplayRole), "frozen", with_menu=False)
            self.ui.frozen_table.setIndexWidget(index, widget)
            self.ui.frozen_table.horizontalHeader().resizeSection(column, widget.size().width())

    def create_filter_menu(self, identifier):
        """Returns a filter menu for given given object class disambiguated name.

        Args:
            identifier (int)

        Returns:
            FilterMenu
        """
        if identifier not in self.filter_menus:
            item_type = "parameter definition" if identifier == -1 else "object"
            self.filter_menus[identifier] = menu = FilterMenu(self, identifier, item_type)
            menu.set_filter_list(sorted(set(self.index_values[identifier])))
            menu.filterChanged.connect(self.change_filter)
        return self.filter_menus[identifier]

    def create_header_widget(self, identifier, area, with_menu=True):
        """
        Returns a TabularViewHeaderWidget for given object class disambiguated name.

        Args:
            identifier (int)
            area (str)
            with_menu (bool)

        Returns:
            TabularViewHeaderWidget
        """
        if with_menu:
            menu = self.create_filter_menu(identifier)
        else:
            menu = None
        if identifier == -1:
            name = self._PARAMETER_NAME
        else:
            name = self.current_object_class_name_list()[identifier]
        widget = TabularViewHeaderWidget(identifier, name, area, menu=menu, parent=self)
        widget.header_dropped.connect(self.handle_header_dropped)
        return widget

    @staticmethod
    def _get_insert_index(pivot_list, catcher, position):
        """Returns an index for inserting a new element in the given pivot list.

        Returns:
            int
        """
        if isinstance(catcher, TabularViewHeaderWidget):
            i = pivot_list.index(catcher.identifier)
            if position == "after":
                i += 1
        else:
            i = 0
        return i

    @Slot(object, object, str)
    def handle_header_dropped(self, dropped, catcher, position=""):
        """
        Updates pivots when a header is dropped.

        Args:
            dropped (TabularViewHeaderWidget)
            catcher (TabularViewHeaderWidget, PivotTableHeaderView, FrozenTableView)
            position (str): either "before", "after", or ""
        """
        top_indexes, left_indexes = self.pivot_table_model.top_left_indexes()
        rows = [index.data(Qt.DisplayRole) for index in top_indexes]
        columns = [index.data(Qt.DisplayRole) for index in left_indexes]
        frozen = self.frozen_table_model.headers
        dropped_list = {"columns": columns, "rows": rows, "frozen": frozen}[dropped.area]
        catcher_list = {"columns": columns, "rows": rows, "frozen": frozen}[catcher.area]
        dropped_list.remove(dropped.identifier)
        i = self._get_insert_index(catcher_list, catcher, position)
        catcher_list.insert(i, dropped.identifier)
        if dropped.area == "frozen" or catcher.area == "frozen":
            if frozen:
                frozen_values = self.find_frozen_values(frozen)
                self.frozen_table_model.reset_model(frozen_values, frozen)
                self.make_frozen_headers()
            else:
                self.frozen_table_model.reset_model([], [])
        frozen_value = self.get_frozen_value(self.ui.frozen_table.currentIndex())
        self.pivot_table_model.set_pivot(rows, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_id, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(rows, columns, frozen, frozen_value)
        self.make_pivot_headers()

    def get_frozen_value(self, index):
        if not index.isValid():
            return tuple(None for _ in range(self.frozen_table_model.columnCount()))
        return self.frozen_table_model.row(index)

    @Slot("QModelIndex", "QModelIndex")
    def change_frozen_value(self, current, previous):
        """Sets the frozen value from selection in frozen table.
        """
        frozen_value = self.get_frozen_value(current)
        self.pivot_table_model.set_frozen_value(frozen_value)
        # update pivot history
        self.class_pivot_preferences[
            (self.current_class_id, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(
            self.pivot_table_model.model.pivot_rows,
            self.pivot_table_model.model.pivot_columns,
            self.pivot_table_model.model.pivot_frozen,
            self.pivot_table_model.model.frozen_value,
        )

    @Slot(int, set, bool)
    def change_filter(self, identifier, valid, has_filter):
        if has_filter:
            self.pivot_table_proxy.set_filter(identifier, valid)
        else:
            self.pivot_table_proxy.set_filter(identifier, None)  # None means everything passes

    def reload_frozen_table(self):
        """Resets the frozen model according to new selection in entity trees."""
        frozen = self.pivot_table_model.model.pivot_frozen
        frozen_value = self.pivot_table_model.model.frozen_value
        frozen_values = self.find_frozen_values(frozen)
        self.frozen_table_model.reset_model(frozen_values, frozen)
        self.make_frozen_headers()
        if frozen_value in frozen_values:
            # update selected row
            ind = frozen_values.index(frozen_value)
            self.ui.frozen_table.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.frozen_table.selectRow(ind)
            self.ui.frozen_table.selectionModel().blockSignals(False)
        else:
            # frozen value not found, remove selection
            self.ui.frozen_table.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.frozen_table.clearSelection()
            self.ui.frozen_table.selectionModel().blockSignals(False)

    def find_frozen_values(self, frozen):
        """Returns a list of tuples containing unique values for the frozen indexes.

        Args:
            frozen (tuple): A tuple of currently frozen indexes
        Returns:
            list(tuple)
        """
        return sorted(set(zip(*[self.index_values[k] for k in frozen])))

    def refresh_pivot_table_view(self):
        top_left = self.ui.pivot_table.indexAt(self.ui.pivot_table.rect().topLeft())
        bottom_right = self.ui.pivot_table.indexAt(self.ui.pivot_table.rect().bottomRight())
        self.pivot_table_proxy.dataChanged.emit(top_left, bottom_right)

    def receive_object_classes_added(self, db_map_data):
        """Reacts to object classes added event."""
        super().receive_object_classes_added(db_map_data)

    def receive_objects_added(self, db_map_data):
        """Reacts to objects added event."""
        super().receive_objects_added(db_map_data)

    def receive_relationship_classes_added(self, db_map_data):
        """Reacts to relationship classes added."""
        super().receive_relationship_classes_added(db_map_data)

    def receive_relationships_added(self, db_map_data):
        """Reacts to relationships added event."""
        super().receive_relationships_added(db_map_data)

    def receive_parameter_definitions_added(self, db_map_data):
        """Reacts to parameter definitions added event."""
        super().receive_parameter_definitions_added(db_map_data)

    def receive_parameter_values_added(self, db_map_data):
        """Reacts to parameter values added event."""
        super().receive_parameter_values_added(db_map_data)
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        items = db_map_data[self.db_map]
        for item in items:
            class_id = item.get("object_class_id") or item.get("relationship_class_id")
            if class_id == self.current_class_id:
                self.reload_pivot_table()
                break

    def receive_object_classes_updated(self, db_map_data):
        """Reacts to object classes updated event."""
        super().receive_object_classes_updated(db_map_data)

    def receive_objects_updated(self, db_map_data):
        """Reacts to objects updated event."""
        super().receive_objects_updated(db_map_data)
        items = db_map_data[self.db_map]
        for item in items:
            class_id = item["class_id"]
            if class_id == self.current_class_id:
                self.refresh_pivot_table_view()
                break

    def receive_relationship_classes_updated(self, db_map_data):
        """Reacts to relationship classes updated event."""
        super().receive_relationship_classes_updated(db_map_data)

    def receive_relationships_updated(self, db_map_data):
        """Reacts to relationships updated event."""
        super().receive_relationships_updated(db_map_data)

    def receive_parameter_values_updated(self, db_map_data):
        """Reacts to parameter values added event."""
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        items = db_map_data[self.db_map]
        for item in items:
            class_id = item.get("object_class_id") or item.get("relationship_class_id")
            if class_id == self.current_class_id:
                self.refresh_pivot_table_view()
                break

    def receive_parameter_definitions_updated(self, db_map_data):
        """Reacts to parameter definitions updated event."""
        super().receive_parameter_definitions_updated(db_map_data)

    def receive_object_classes_removed(self, db_map_data):
        """Reacts to object classes removed event."""
        super().receive_object_classes_removed(db_map_data)

    def receive_objects_removed(self, db_map_data):
        """Reacts to objects removed event."""
        super().receive_objects_removed(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        """Reacts to relationship classes remove event."""
        super().receive_relationship_classes_removed(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        """Reacts to relationships removed event."""
        super().receive_relationships_removed(db_map_data)

    def receive_parameter_definitions_removed(self, db_map_data):
        """Reacts to parameter definitions removed event."""
        super().receive_parameter_definitions_removed(db_map_data)

    def receive_parameter_values_removed(self, db_map_data):
        """Reacts to parameter values removed event."""
        super().receive_parameter_values_removed(db_map_data)
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        items = db_map_data[self.db_map]
        for item in items:
            class_id = item.get("object_class_id") or item.get("relationship_class_id")
            if class_id == self.current_class_id:
                self.refresh_pivot_table_view()
                break
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.reload_pivot_table()
                break

    def receive_session_committed(self, db_maps):
        """Reacts to session committed event."""
        super().receive_session_committed(db_maps)

    def receive_session_rolled_back(self, db_maps):
        """Reacts to session rolled back event."""
        super().receive_session_rolled_back(db_maps)
        self.reload_pivot_table()
        self.reload_frozen_table()
