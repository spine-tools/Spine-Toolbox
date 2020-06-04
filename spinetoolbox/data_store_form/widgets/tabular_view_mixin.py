######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains TabularViewMixin class.

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from itertools import product
from collections import namedtuple
from PySide2.QtCore import Qt, Slot, QTimer
from PySide2.QtWidgets import QActionGroup
from .custom_menus import TabularViewFilterMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...helpers import fix_name_ambiguity, busy_effect
from ...widgets.custom_qwidgets import TitleWidgetAction
from ..mvcmodels.pivot_table_models import (
    PivotTableSortFilterProxy,
    ParameterValuePivotTableModel,
    RelationshipPivotTableModel,
    IndexExpansionPivotTableModel,
)
from ..mvcmodels.frozen_table_model import FrozenTableModel
from .custom_delegates import RelationshipPivotTableDelegate, ParameterPivotTableDelegate


class TabularViewMixin:
    """Provides the pivot table and its frozen table for the DS form."""

    _PARAMETER_VALUE = "Parameter value"
    _INDEX_EXPANSION = "Index expansion"
    _RELATIONSHIP = "Relationship"

    _PARAMETER = "parameter"
    _INDEX = "index"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # current state of ui
        self.current = None  # Current QModelIndex selected in one of the entity tree views
        self.current_class_type = None
        self.current_class_id = None
        self.current_input_type = self._PARAMETER_VALUE
        self.filter_menus = {}
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])
        title_action = TitleWidgetAction("Input type", self)
        self.ui.menuPivot_table.addAction(title_action)
        self.input_type_action_group = QActionGroup(self)
        actions = {
            input_type: self.input_type_action_group.addAction(input_type)
            for input_type in [self._PARAMETER_VALUE, self._INDEX_EXPANSION, self._RELATIONSHIP]
        }
        for action in actions.values():
            action.setCheckable(True)
            self.ui.menuPivot_table.addAction(action)
        actions[self.current_input_type].setChecked(True)
        self.pivot_table_proxy = PivotTableSortFilterProxy()
        self.pivot_table_model = None
        self.frozen_table_model = FrozenTableModel(self)
        self.ui.pivot_table.setModel(self.pivot_table_proxy)
        self.ui.pivot_table.connect_data_store_form(self)
        self.ui.frozen_table.setModel(self.frozen_table_model)
        self.ui.frozen_table.verticalHeader().setDefaultSectionSize(self.default_row_height)

    def add_menu_actions(self):
        """Adds toggle view actions to View menu."""
        super().add_menu_actions()
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.ui.dockWidget_pivot_table.toggleViewAction())
        self.ui.menuView.addAction(self.ui.dockWidget_frozen_table.toggleViewAction())

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.treeView_object.selectionModel().currentChanged.connect(self._handle_entity_tree_current_changed)
        self.ui.treeView_relationship.selectionModel().currentChanged.connect(self._handle_entity_tree_current_changed)
        self.ui.pivot_table.horizontalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.pivot_table.verticalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.selectionModel().currentChanged.connect(self.change_frozen_value)
        self.input_type_action_group.triggered.connect(self.do_reload_pivot_table)
        self.ui.dockWidget_pivot_table.visibilityChanged.connect(self._handle_pivot_table_visibility_changed)
        self.ui.dockWidget_frozen_table.visibilityChanged.connect(self._handle_frozen_table_visibility_changed)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.clear_pivot_table()

    @Slot("QModelIndex", object)
    def _set_model_data(self, index, value):
        self.pivot_table_proxy.setData(index, value)

    @property
    def current_object_class_id_list(self):
        if self.current_class_type == "object class":
            return [self.current_class_id]
        relationship_class = self.db_mngr.get_item(self.db_map, "relationship class", self.current_class_id)
        return [int(id_) for id_ in relationship_class["object_class_id_list"].split(",")]

    @property
    def current_object_class_name_list(self):
        if self.current_class_type == "object class":
            return [self.db_mngr.get_item(self.db_map, "object class", self.current_class_id)["name"]]
        relationship_class = self.db_mngr.get_item(self.db_map, "relationship class", self.current_class_id)
        return fix_name_ambiguity(relationship_class["object_class_name_list"].split(","))

    @staticmethod
    def _is_class_index(index):
        """Returns whether or not the given tree index is a class index.

        Args:
            index (QModelIndex): index from object or relationship tree
        Returns:
            bool
        """
        return index.column() == 0 and not index.parent().parent().isValid()

    @Slot(bool)
    def _handle_pivot_table_visibility_changed(self, visible):
        if visible:
            self.reload_pivot_table()
            self.reload_frozen_table()
            self.ui.dockWidget_frozen_table.setVisible(True)

    @Slot(bool)
    def _handle_frozen_table_visibility_changed(self, visible):
        if visible:
            self.ui.dockWidget_pivot_table.show()

    @Slot("QModelIndex", "QModelIndex")
    def _handle_entity_tree_current_changed(self, current, previous):
        if self.ui.dockWidget_pivot_table.isVisible():
            self.reload_pivot_table(current=current)
            self.reload_frozen_table()

    def _get_entities(self, class_id=None, class_type=None):
        """Returns a list of dict items from the object or relationship tree model
        corresponding to the given class id.

        Args:
            class_id (int)
            class_type (str)

        Returns:
            list(dict)
        """
        if class_id is None:
            class_id = self.current_class_id
        if class_type is None:
            class_type = self.current_class_type
        entity_type = {"object class": "object", "relationship class": "relationship"}[class_type]
        return self.db_mngr.get_items_by_field(self.db_map, entity_type, "class_id", class_id)

    def load_empty_relationship_data(self, objects_per_class=None):
        """Returns a dict containing all possible relationships in the current class.

        Args:
            objects_per_class (dict)

        Returns:
            dict: Key is object id tuple, value is None.
        """
        if objects_per_class is None:
            objects_per_class = dict()
        if self.current_class_type == "object class":
            return {}
        object_id_sets = []
        for obj_cls_id in self.current_object_class_id_list:
            objects = objects_per_class.get(obj_cls_id, None)
            if objects is None:
                objects = self._get_entities(obj_cls_id, "object class")
            id_set = {item["id"]: None for item in objects}
            object_id_sets.append(list(id_set.keys()))
        return dict.fromkeys(product(*object_id_sets))

    def load_full_relationship_data(self, relationships=None, action="add"):
        """Returns a dict of relationships in the current class.

        Returns:
            dict: Key is object id tuple, value is relationship id.
        """
        if self.current_class_type == "object class":
            return {}
        if relationships is None:
            relationships = self._get_entities()
        get_id = {"add": lambda x: x["id"], "remove": lambda x: None}[action]
        return {tuple(int(id_) for id_ in x["object_id_list"].split(',')): get_id(x) for x in relationships}

    def load_relationship_data(self):
        """Returns a dict that merges empty and full relationship data.

        Returns:
            dict: Key is object id tuple, value is True if a relationship exists, False otherwise.
        """
        data = self.load_empty_relationship_data()
        data.update(self.load_full_relationship_data())
        return data

    def _get_parameter_value_or_def_ids(self, item_type):
        """Returns a list of integer ids from the parameter model
        corresponding to the currently selected class and the given item type.

        Args:
            item_type (str): either "parameter value" or "parameter definition"

        Returns:
            list(int)
        """
        class_id_field = {"object class": "object_class_id", "relationship class": "relationship_class_id"}[
            self.current_class_type
        ]
        return [
            x["id"]
            for x in self.db_mngr.get_items_by_field(self.db_map, item_type, class_id_field, self.current_class_id)
        ]

    def _get_parameter_values_or_defs(self, item_type):
        """Returns a list of dict items from the parameter model
        corresponding to the currently selected class and the given item type.

        Args:
            item_type (str): either "parameter value" or "parameter definition"

        Returns:
            list(dict)
        """
        ids = self._get_parameter_value_or_def_ids(item_type)
        return [self.db_mngr.get_item(self.db_map, item_type, id_) for id_ in ids]

    def load_empty_parameter_value_data(self, entities=None, parameter_ids=None):
        """Returns a dict containing all possible combinations of entities and parameters for the current class.

        Args:
            entities (list, optional): if given, only load data for these entities
            parameter_ids (set, optional): if given, only load data for these parameter definitions

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is None.
        """
        if entities is None:
            entities = self._get_entities()
        if parameter_ids is None:
            parameter_ids = self._get_parameter_value_or_def_ids("parameter definition")
        if self.current_class_type == "relationship class":
            entity_ids = [tuple(int(id_) for id_ in e["object_id_list"].split(',')) for e in entities]
        else:
            entity_ids = [(e["id"],) for e in entities]
        if not entity_ids:
            entity_ids = [tuple(None for _ in self.current_object_class_id_list)]
        if not parameter_ids:
            parameter_ids = [None]
        return {entity_id + (parameter_id,): None for entity_id in entity_ids for parameter_id in parameter_ids}

    def load_full_parameter_value_data(self, parameter_values=None, action="add"):
        """Returns a dict of parameter values for the current class.

        Args:
            parameter_values (list, optional)
            action (str)

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is the parameter value.
        """
        if parameter_values is None:
            parameter_values = self._get_parameter_values_or_defs("parameter value")
        get_id = {"add": lambda x: x["id"], "remove": lambda x: None}[action]
        if self.current_class_type == "object class":
            return {(x["object_id"], x["parameter_id"]): get_id(x) for x in parameter_values}
        return {
            tuple(int(id_) for id_ in x["object_id_list"].split(',')) + (x["parameter_id"],): get_id(x)
            for x in parameter_values
        }

    def load_parameter_value_data(self):
        """Returns a dict that merges empty and full parameter value data.

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is the parameter value or None if not specified.
        """
        data = self.load_empty_parameter_value_data()
        data.update(self.load_full_parameter_value_data())
        return data

    def load_expanded_parameter_value_data(self):
        """
        Returns all permutations of entities as well as parameter indexes and values for the current class.

        Returns:
            dict: Key is a tuple object_id, ..., index, while value is None.
        """
        data = self.load_parameter_value_data()
        return {
            key[:-1] + (index, key[-1]): id_
            for key, id_ in data.items()
            for index in self.db_mngr.get_value_indexes(self.db_map, "parameter value", id_)
        }

    def get_pivot_preferences(self):
        """Returns saved pivot preferences.

        Returns:
            tuple, NoneType: pivot tuple, or None if no preference stored
        """
        selection_key = (self.current_class_id, self.current_class_type, self.current_input_type)
        if selection_key in self.class_pivot_preferences:
            rows = self.class_pivot_preferences[selection_key].index
            columns = self.class_pivot_preferences[selection_key].columns
            frozen = self.class_pivot_preferences[selection_key].frozen
            frozen_value = self.class_pivot_preferences[selection_key].frozen_value
            return (rows, columns, frozen, frozen_value)
        return None

    @Slot(str)
    def reload_pivot_table(self, current=None):
        """Updates current class (type and id) and reloads pivot table for it."""
        if current is not None:
            self.current = current
        if self.current is None:
            return
        if self._is_class_index(self.current):
            item = self.current.model().item_from_index(self.current)
            class_id = item.db_map_id(self.db_map)
            if self.current_class_id == class_id:
                return
            self.current_class_type = item.item_type
            self.current_class_id = class_id
            self.do_reload_pivot_table()

    @busy_effect
    @Slot("QAction")
    def do_reload_pivot_table(self, action=None):
        """Reloads pivot table.
        """
        if self.current_class_id is None:
            return
        qApp.processEvents()  # pylint: disable=undefined-variable
        if action is None:
            action = self.input_type_action_group.checkedAction()
        self.current_input_type = action.text()
        self.pivot_table_model = {
            self._PARAMETER_VALUE: ParameterValuePivotTableModel,
            self._RELATIONSHIP: RelationshipPivotTableModel,
            self._INDEX_EXPANSION: IndexExpansionPivotTableModel,
        }[self.current_input_type](self)
        self.pivot_table_proxy.setSourceModel(self.pivot_table_model)
        delegate = {
            self._PARAMETER_VALUE: ParameterPivotTableDelegate,
            self._RELATIONSHIP: RelationshipPivotTableDelegate,
            self._INDEX_EXPANSION: ParameterPivotTableDelegate,
        }[self.current_input_type](self)
        self.ui.pivot_table.setItemDelegate(delegate)
        self.pivot_table_model.modelReset.connect(self.make_pivot_headers)
        if self.current_input_type == self._RELATIONSHIP and self.current_class_type != "relationship class":
            self.clear_pivot_table()
            return
        pivot = self.get_pivot_preferences()
        self.wipe_out_filter_menus()
        object_class_ids = dict(zip(self.current_object_class_name_list, self.current_object_class_id_list))
        self.pivot_table_model.call_reset_model(object_class_ids, pivot)
        self.pivot_table_proxy.clear_filter()

    def clear_pivot_table(self):
        self.wipe_out_filter_menus()
        if self.pivot_table_model:
            self.pivot_table_model.clear_model()
            self.pivot_table_proxy.clear_filter()

    def wipe_out_filter_menus(self):
        while self.filter_menus:
            _, menu = self.filter_menus.popitem()
            menu.wipe_out()

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
        QTimer.singleShot(0, self._resize_pivot_header_columns)

    @Slot()
    def _resize_pivot_header_columns(self):
        top_indexes, _ = self.pivot_table_model.top_left_indexes()
        for index in top_indexes:
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
        """Returns a filter menu for given given object class identifier.

        Args:
            identifier (int)

        Returns:
            TabularViewFilterMenu
        """
        _get_field = lambda *args: self.db_mngr.get_field(self.db_map, *args)
        if identifier not in self.filter_menus:
            pivot_top_left_header = self.pivot_table_model.top_left_headers[identifier]
            data_to_value = pivot_top_left_header.header_data
            self.filter_menus[identifier] = menu = TabularViewFilterMenu(
                self, identifier, data_to_value, show_empty=False
            )
            index_values = dict.fromkeys(self.pivot_table_model.model.index_values.get(identifier, []))
            index_values.pop(None, None)
            menu.set_filter_list(index_values.keys())
            menu.filterChanged.connect(self.change_filter)
        return self.filter_menus[identifier]

    def create_header_widget(self, identifier, area, with_menu=True):
        """
        Returns a TabularViewHeaderWidget for given object class identifier.

        Args:
            identifier (str)
            area (str)
            with_menu (bool)

        Returns:
            TabularViewHeaderWidget
        """
        menu = self.create_filter_menu(identifier) if with_menu else None
        widget = TabularViewHeaderWidget(identifier, area, menu=menu, parent=self)
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
                self.ui.frozen_table.resizeColumnsToContents()
            else:
                self.frozen_table_model.clear_model()
        frozen_value = self.get_frozen_value(self.ui.frozen_table.currentIndex())
        self.pivot_table_model.set_pivot(rows, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_id, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(rows, columns, frozen, frozen_value)
        self.make_pivot_headers()

    def get_frozen_value(self, index):
        """
        Returns the value in the frozen table corresponding to the given index.

        Args:
            index (QModelIndex)
        Returns:
            tuple
        """
        if not index.isValid():
            return tuple(None for _ in range(self.frozen_table_model.columnCount()))
        return self.frozen_table_model.row(index)

    @Slot("QModelIndex", "QModelIndex")
    def change_frozen_value(self, current, previous):
        """Sets the frozen value from selection in frozen table.
        """
        frozen_value = self.get_frozen_value(current)
        self.pivot_table_model.set_frozen_value(frozen_value)
        # store pivot preferences
        self.class_pivot_preferences[
            (self.current_class_id, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(
            self.pivot_table_model.model.pivot_rows,
            self.pivot_table_model.model.pivot_columns,
            self.pivot_table_model.model.pivot_frozen,
            self.pivot_table_model.model.frozen_value,
        )

    @Slot(str, set, bool)
    def change_filter(self, identifier, valid_values, has_filter):
        if has_filter:
            self.pivot_table_proxy.set_filter(identifier, valid_values)
        else:
            self.pivot_table_proxy.set_filter(identifier, None)  # None means everything passes

    def reload_frozen_table(self):
        """Resets the frozen model according to new selection in entity trees."""
        if not self.pivot_table_model:
            return
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
        self.ui.frozen_table.resizeColumnsToContents()

    def find_frozen_values(self, frozen):
        """Returns a list of tuples containing unique values (object ids) for the frozen indexes (object class ids).

        Args:
            frozen (tuple(int)): A tuple of currently frozen indexes
        Returns:
            list(tuple(list(int)))
        """
        return list(dict.fromkeys(zip(*[self.pivot_table_model.model.index_values.get(k, []) for k in frozen])).keys())

    # FIXME: Move this to the models
    @staticmethod
    def refresh_table_view(table_view):
        top_left = table_view.indexAt(table_view.rect().topLeft())
        bottom_right = table_view.indexAt(table_view.rect().bottomRight())
        if not bottom_right.isValid():
            model = table_view.model()
            bottom_right = table_view.model().index(model.rowCount() - 1, model.columnCount() - 1)
        table_view.model().dataChanged.emit(top_left, bottom_right)

    @Slot(str)
    def update_filter_menus(self, action):
        for identifier, menu in self.filter_menus.items():
            index_values = dict.fromkeys(self.pivot_table_model.model.index_values.get(identifier, []))
            index_values.pop(None, None)
            if action == "add":
                menu.add_items_to_filter_list(list(index_values.keys()))
            elif action == "remove":
                previous = menu._filter._filter_model._data_set
                menu.remove_items_from_filter_list(list(previous - index_values.keys()))
        self.reload_frozen_table()

    def receive_objects_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        items = db_map_data.get(self.db_map, set())
        if self.pivot_table_model.receive_objects_added_or_removed(items, action):
            self.update_filter_menus(action)

    def receive_relationships_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.current_class_type != "relationship class":
            return
        items = db_map_data.get(self.db_map, set())
        relationships = [x for x in items if x["class_id"] == self.current_class_id]
        if not relationships:
            return
        if self.pivot_table_model.receive_relationships_added_or_removed(relationships, action):
            self.update_filter_menus(action)

    def receive_parameter_definitions_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        items = db_map_data.get(self.db_map, set())
        parameters = [
            x for x in items if (x.get("object_class_id") or x.get("relationship_class_id")) == self.current_class_id
        ]
        if not parameters:
            return
        if self.pivot_table_model.receive_parameter_definitions_added_or_removed(parameters, action):
            self.update_filter_menus(action)

    def receive_parameter_values_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        items = db_map_data.get(self.db_map, set())
        parameter_values = [
            x for x in items if (x.get("object_class_id") or x.get("relationship_class_id")) == self.current_class_id
        ]
        if not parameter_values:
            return
        if self.pivot_table_model.receive_parameter_values_added_or_removed(parameter_values, action):
            self.update_filter_menus(action)

    def receive_db_map_data_updated(self, db_map_data, get_class_id):
        if not self.pivot_table_model:
            return
        items = db_map_data.get(self.db_map, set())
        for item in items:
            if get_class_id(item) == self.current_class_id:
                self.refresh_table_view(self.ui.pivot_table)
                self.refresh_table_view(self.ui.frozen_table)
                self.make_pivot_headers()
                break

    def receive_classes_removed(self, db_map_data):
        if not self.pivot_table_model:
            return
        items = db_map_data.get(self.db_map, set())
        for item in items:
            if item["id"] == self.current_class_id:
                self.current_class_type = None
                self.current_class_id = None
                self.clear_pivot_table()
                break

    def receive_objects_added(self, db_map_data):
        """Reacts to objects added event."""
        super().receive_objects_added(db_map_data)
        self.receive_objects_added_or_removed(db_map_data, action="add")

    def receive_relationships_added(self, db_map_data):
        """Reacts to relationships added event."""
        super().receive_relationships_added(db_map_data)
        self.receive_relationships_added_or_removed(db_map_data, action="add")

    def receive_parameter_definitions_added(self, db_map_data):
        """Reacts to parameter definitions added event."""
        super().receive_parameter_definitions_added(db_map_data)
        self.receive_parameter_definitions_added_or_removed(db_map_data, action="add")

    def receive_parameter_values_added(self, db_map_data):
        """Reacts to parameter values added event."""
        super().receive_parameter_values_added(db_map_data)
        self.receive_parameter_values_added_or_removed(db_map_data, action="add")

    def receive_object_classes_updated(self, db_map_data):
        """Reacts to object classes updated event."""
        super().receive_object_classes_updated(db_map_data)
        self.receive_db_map_data_updated(db_map_data, get_class_id=lambda x: x["id"])

    def receive_objects_updated(self, db_map_data):
        """Reacts to objects updated event."""
        super().receive_objects_updated(db_map_data)
        self.receive_db_map_data_updated(db_map_data, get_class_id=lambda x: x["class_id"])

    def receive_relationship_classes_updated(self, db_map_data):
        """Reacts to relationship classes updated event."""
        super().receive_relationship_classes_updated(db_map_data)
        self.receive_db_map_data_updated(db_map_data, get_class_id=lambda x: x["id"])

    def receive_relationships_updated(self, db_map_data):
        """Reacts to relationships updated event."""
        super().receive_relationships_updated(db_map_data)
        self.receive_db_map_data_updated(db_map_data, get_class_id=lambda x: x["class_id"])

    def receive_parameter_values_updated(self, db_map_data):
        """Reacts to parameter values added event."""
        super().receive_parameter_values_updated(db_map_data)
        self.receive_db_map_data_updated(
            db_map_data, get_class_id=lambda x: x.get("object_class_id") or x.get("relationship_class_id")
        )

    def receive_parameter_definitions_updated(self, db_map_data):
        """Reacts to parameter definitions updated event."""
        super().receive_parameter_definitions_updated(db_map_data)
        self.receive_db_map_data_updated(
            db_map_data, get_class_id=lambda x: x.get("object_class_id") or x.get("relationship_class_id")
        )

    def receive_object_classes_removed(self, db_map_data):
        """Reacts to object classes removed event."""
        super().receive_object_classes_removed(db_map_data)
        self.receive_classes_removed(db_map_data)

    def receive_objects_removed(self, db_map_data):
        """Reacts to objects removed event."""
        super().receive_objects_removed(db_map_data)
        self.receive_objects_added_or_removed(db_map_data, action="remove")

    def receive_relationship_classes_removed(self, db_map_data):
        """Reacts to relationship classes remove event."""
        super().receive_relationship_classes_removed(db_map_data)
        self.receive_classes_removed(db_map_data)

    def receive_relationships_removed(self, db_map_data):
        """Reacts to relationships removed event."""
        super().receive_relationships_removed(db_map_data)
        self.receive_relationships_added_or_removed(db_map_data, action="remove")

    def receive_parameter_definitions_removed(self, db_map_data):
        """Reacts to parameter definitions removed event."""
        super().receive_parameter_definitions_removed(db_map_data)
        self.receive_parameter_definitions_added_or_removed(db_map_data, action="remove")

    def receive_parameter_values_removed(self, db_map_data):
        """Reacts to parameter values removed event."""
        super().receive_parameter_values_removed(db_map_data)
        self.receive_parameter_values_added_or_removed(db_map_data, action="remove")

    def receive_session_rolled_back(self, db_maps):
        """Reacts to session rolled back event."""
        super().receive_session_rolled_back(db_maps)
        self.reload_pivot_table()
        self.reload_frozen_table()
