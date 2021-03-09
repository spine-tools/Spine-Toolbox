######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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
from PySide2.QtGui import QIcon
from spinedb_api.helpers import fix_name_ambiguity
from .custom_menus import TabularViewFilterMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...helpers import busy_effect, CharIconEngine
from ..mvcmodels.pivot_table_models import (
    PivotTableSortFilterProxy,
    ParameterValuePivotTableModel,
    RelationshipPivotTableModel,
    IndexExpansionPivotTableModel,
    ScenarioAlternativePivotTableModel,
)
from ..mvcmodels.frozen_table_model import FrozenTableModel


class TabularViewMixin:
    """Provides the pivot table and its frozen table for the DS form."""

    _PARAMETER_VALUE = "&Value"
    _INDEX_EXPANSION = "&Index"
    _RELATIONSHIP = "Re&lationship"
    _SCENARIO_ALTERNATIVE = "&Scenario"

    _PARAMETER = "parameter"
    _ALTERNATIVE = "alternative"
    _INDEX = "index"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pending_index = None
        # current state of ui
        self.current_class_item = None  # Current QModelIndex selected in one of the entity tree views
        self.current_class_type = None
        self.current_class_id = {}  # Mapping from db_map to class_id
        self.current_class_name = None
        self.current_input_type = self._PARAMETER_VALUE
        self.filter_menus = {}
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])
        self.pivot_action_group = QActionGroup(self)
        self.pivot_actions = {}
        self.populate_pivot_action_group()
        self.pivot_table_proxy = PivotTableSortFilterProxy()
        self.pivot_table_model = None
        self.frozen_table_model = FrozenTableModel(self)
        self.ui.pivot_table.setModel(self.pivot_table_proxy)
        self.ui.pivot_table.connect_spine_db_editor(self)
        self.ui.frozen_table.setModel(self.frozen_table_model)
        self.ui.frozen_table.verticalHeader().setDefaultSectionSize(self.default_row_height)

    def populate_pivot_action_group(self):
        self.pivot_actions = {
            input_type: self.pivot_action_group.addAction(QIcon(CharIconEngine(icon_code)), input_type)
            for input_type, icon_code in (
                (self._PARAMETER_VALUE, "\uf292"),
                (self._INDEX_EXPANSION, "\uf12c"),
                (self._RELATIONSHIP, "\uf1b3"),
                (self._SCENARIO_ALTERNATIVE, "\uf008"),
            )
        }
        for action in self.pivot_actions.values():
            action.setCheckable(True)

    def connect_signals(self):
        """Connects signals to slots."""
        super().connect_signals()
        self.ui.pivot_table.horizontalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.pivot_table.verticalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.selectionModel().currentChanged.connect(self.change_frozen_value)
        self.pivot_action_group.triggered.connect(self._handle_pivot_action_triggered)
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
        if self.current_class_type == "object_class":
            return [self.current_class_id]
        current_object_class_id_list = [{} for _ in self.current_object_class_name_list]
        for db_map, class_id in self.current_class_id.items():
            relationship_class = self.db_mngr.get_item(db_map, "relationship_class", class_id)
            for k, id_ in enumerate(relationship_class["object_class_id_list"].split(",")):
                current_object_class_id_list[k][db_map] = int(id_)
        return current_object_class_id_list

    @property
    def current_object_class_name_list(self):
        db_map, class_id = next(iter(self.current_class_id.items()))
        if self.current_class_type == "object_class":
            return [self.db_mngr.get_item(db_map, "object_class", class_id)["name"]]
        relationship_class = self.db_mngr.get_item(db_map, "relationship_class", class_id)
        return fix_name_ambiguity(relationship_class["object_class_name_list"].split(","))

    @property
    def current_object_class_ids(self):
        return dict(zip(self.current_object_class_name_list, self.current_object_class_id_list))

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
        if not visible:
            for action in self.pivot_actions.values():
                action.setChecked(False)
            return
        self.pivot_actions[self.current_input_type].setChecked(True)
        self.ui.dockWidget_frozen_table.setVisible(True)
        if self._pending_index is not None:
            QTimer.singleShot(100, lambda: self.reload_pivot_table(self._pending_index))

    @Slot(bool)
    def _handle_frozen_table_visibility_changed(self, visible):
        if visible:
            self.ui.dockWidget_pivot_table.show()

    @Slot(dict)
    def _handle_object_tree_selection_changed(self, selected_indexes):
        super()._handle_object_tree_selection_changed(selected_indexes)
        current = self.ui.treeView_object.currentIndex()
        self._handle_entity_tree_current_changed(current)

    @Slot(dict)
    def _handle_relationship_tree_selection_changed(self, selected_indexes):
        super()._handle_relationship_tree_selection_changed(selected_indexes)
        current = self.ui.treeView_relationship.currentIndex()
        self._handle_entity_tree_current_changed(current)

    def _handle_entity_tree_current_changed(self, current_index):
        if self.current_input_type == self._SCENARIO_ALTERNATIVE:
            return
        if not self.ui.dockWidget_pivot_table.isVisible():
            self._pending_index = current_index
            return
        self.reload_pivot_table(current_index=current_index)

    @staticmethod
    def _make_get_id(action):
        """Returns a function to compute the db_map-id tuple of an item."""
        return {"add": lambda db_map, x: (db_map, x["id"]), "remove": lambda db_map, x: None}[action]

    def _get_db_map_entities(self):
        """Returns a dict mapping db maps to a list of dict entity items in the current class.

        Returns:
            dict
        """
        entity_type = {"object_class": "object", "relationship_class": "relationship"}[self.current_class_type]
        return {
            db_map: self.db_mngr.get_items_by_field(db_map, entity_type, "class_id", class_id)
            for db_map, class_id in self.current_class_id.items()
        }

    def load_empty_relationship_data(self, db_map_class_objects=None):
        """Returns a dict containing all possible relationships in the current class.

        Args:
            db_map_class_objects (dict)

        Returns:
            dict: Key is db_map-object_id tuple, value is None.
        """
        if db_map_class_objects is None:
            db_map_class_objects = dict()
        if self.current_class_type == "object_class":
            return {}
        data = {}
        for db_map in self.db_maps:
            object_id_lists = []
            all_given_ids = set()
            for db_map_class_id in self.current_object_class_id_list:
                class_id = db_map_class_id.get(db_map)
                objects = self.db_mngr.get_items_by_field(db_map, "object", "class_id", class_id)
                ids = {item["id"]: None for item in objects}
                given_objects = db_map_class_objects.get(db_map, {}).get(class_id)
                if given_objects is not None:
                    given_ids = {item["id"]: None for item in given_objects}
                    ids.update(given_ids)
                    all_given_ids.update(given_ids.keys())
                object_id_lists.append(list(ids.keys()))
            db_map_data = {
                tuple((db_map, id_) for id_ in objects_ids) + (db_map,): None
                for objects_ids in product(*object_id_lists)
                if not all_given_ids or all_given_ids.intersection(objects_ids)
            }
            data.update(db_map_data)
        return data

    def load_full_relationship_data(self, db_map_relationships=None, action="add"):
        """Returns a dict of relationships in the current class.

        Args:
            db_map_relationships (dict)

        Returns:
            dict: Key is db_map-object id tuple, value is relationship id.
        """
        if self.current_class_type == "object_class":
            return {}
        if db_map_relationships is None:
            db_map_relationships = self._get_db_map_entities()
        get_id = self._make_get_id(action)
        return {
            tuple((db_map, int(id_)) for id_ in rel["object_id_list"].split(',')) + (db_map,): get_id(db_map, rel)
            for db_map, relationships in db_map_relationships.items()
            for rel in relationships
        }

    def load_relationship_data(self):
        """Returns a dict that merges empty and full relationship data.

        Returns:
            dict: Key is object id tuple, value is True if a relationship exists, False otherwise.
        """
        data = self.load_empty_relationship_data()
        data.update(self.load_full_relationship_data())
        return data

    def load_scenario_alternative_data(self, db_map_scenarios=None, db_map_alternatives=None):
        """Returns a dict containing all scenario alternatives.

        Returns:
            dict: Key is db_map-id tuple, value is None or rank.
        """
        if db_map_scenarios is None:
            db_map_scenarios = {db_map: self.db_mngr.get_items(db_map, "scenario") for db_map in self.db_maps}
        if db_map_alternatives is None:
            db_map_alternatives = {db_map: self.db_mngr.get_items(db_map, "alternative") for db_map in self.db_maps}
        data = {}
        for db_map in self.db_maps:
            scenario_alternative_ranks = {
                x["id"]: {
                    alt_id: k + 1
                    for k, alt_id in enumerate(self.db_mngr.get_scenario_alternative_id_list(db_map, x["id"]))
                }
                for x in db_map_scenarios.get(db_map, [])
            }
            alternative_ids = [x["id"] for x in db_map_alternatives.get(db_map, [])]
            db_map_data = {
                ((db_map, scen_id), (db_map, alt_id), db_map): alternative_ranks.get(alt_id)
                for scen_id, alternative_ranks in scenario_alternative_ranks.items()
                for alt_id in alternative_ids
            }
            data.update(db_map_data)
        return data

    def _get_parameter_value_or_def_ids(self, item_type):
        """Returns a dict mapping db maps to a list of integer parameter (value or def) ids from the current class.

        Args:
            item_type (str): either "parameter_value" or "parameter_definition"

        Returns:
            dict
        """
        class_id_field = {"object_class": "object_class_id", "relationship_class": "relationship_class_id"}[
            self.current_class_type
        ]
        return {
            db_map: [x["id"] for x in self.db_mngr.get_items_by_field(db_map, item_type, class_id_field, class_id)]
            for db_map, class_id in self.current_class_id.items()
        }

    def _get_db_map_parameter_values_or_defs(self, item_type):
        """Returns a dict mapping db maps to list of dict parameter (value or def) items from the current class.

        Args:
            item_type (str): either "parameter_value" or "parameter_definition"

        Returns:
            dict
        """
        db_map_ids = self._get_parameter_value_or_def_ids(item_type)
        return {
            db_map: [self.db_mngr.get_item(db_map, item_type, id_) for id_ in ids] for db_map, ids in db_map_ids.items()
        }

    def load_empty_parameter_value_data(
        self, db_map_entities=None, db_map_parameter_ids=None, db_map_alternative_ids=None
    ):
        """Returns a dict containing all possible combinations of entities and parameters for the current class
        in all db_maps.

        Args:
            db_map_entities (dict, optional): if given, only load data for these db maps and entities
            db_map_parameter_ids (dict, optional): if given, only load data for these db maps and parameter definitions
            db_map_alternative_ids (dict, optional): if given, only load data for these db maps and alternatives

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is None.
        """
        if db_map_entities is None:
            db_map_entities = self._get_db_map_entities()
        if db_map_parameter_ids is None:
            db_map_parameter_ids = {
                db_map: [(db_map, id_) for id_ in ids]
                for db_map, ids in self._get_parameter_value_or_def_ids("parameter_definition").items()
            }
        if db_map_alternative_ids is None:
            db_map_alternative_ids = {
                db_map: [(db_map, a["id"]) for a in self.db_mngr.get_items(db_map, "alternative")]
                for db_map in self.db_maps
            }
        if self.current_class_type == "relationship_class":
            db_map_entity_ids = {
                db_map: [tuple((db_map, int(id_)) for id_ in e["object_id_list"].split(',')) for e in entities]
                for db_map, entities in db_map_entities.items()
            }
        else:
            db_map_entity_ids = {
                db_map: [((db_map, e["id"]),) for e in entities] for db_map, entities in db_map_entities.items()
            }
        if not db_map_entity_ids:
            db_map_entity_ids = {
                db_map: [tuple((db_map, None) for _ in self.current_object_class_id_list)] for db_map in self.db_maps
            }
        if not db_map_parameter_ids:
            db_map_parameter_ids = {db_map: [(db_map, None)] for db_map in self.db_maps}
        return {
            entity_id + (parameter_id, alt_id, db_map): None
            for db_map in self.db_maps
            for entity_id in db_map_entity_ids.get(db_map, [])
            for parameter_id in db_map_parameter_ids.get(db_map, [])
            for alt_id in db_map_alternative_ids.get(db_map, [])
        }

    def load_full_parameter_value_data(self, db_map_parameter_values=None, action="add"):
        """Returns a dict of parameter values for the current class.

        Args:
            db_map_parameter_values (list, optional)
            action (str)

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is the parameter_value.
        """
        if db_map_parameter_values is None:
            db_map_parameter_values = self._get_db_map_parameter_values_or_defs("parameter_value")
        get_id = self._make_get_id(action)
        if self.current_class_type == "object_class":
            return {
                ((db_map, x["object_id"]), (db_map, x["parameter_id"]), (db_map, x["alternative_id"]), db_map): get_id(
                    db_map, x
                )
                for db_map, items in db_map_parameter_values.items()
                for x in items
            }
        return {
            tuple((db_map, int(id_)) for id_ in x["object_id_list"].split(','))
            + ((db_map, x["parameter_id"]), (db_map, x["alternative_id"]), db_map): get_id(db_map, x)
            for db_map, items in db_map_parameter_values.items()
            for x in items
        }

    def _indexes(self, value):
        if value is None:
            return []
        db_map, id_ = value
        return self.db_mngr.get_value_indexes(db_map, "parameter_value", id_)

    def load_empty_expanded_parameter_value_data(
        self, db_map_entities=None, db_map_parameter_ids=None, db_map_alternative_ids=None
    ):
        """Makes a dict of expanded parameter values for the current class.

        Args:
            db_map_parameter_values (list, optional)
            action (str)

        Returns:
            dict: mapping from unique value id tuple to value tuple
        """
        data = self.load_empty_parameter_value_data(db_map_entities, db_map_parameter_ids, db_map_alternative_ids)
        return {
            key[:-3] + ((None, index),) + key[-3:]: value
            for key, value in data.items()
            for index in self._indexes(value)
        }

    def load_full_expanded_parameter_value_data(self, db_map_parameter_values=None, action="add"):
        """Makes a dict of expanded parameter values for the current class.

        Args:
            db_map_parameter_values (list, optional)
            action (str)

        Returns:
            dict: mapping from unique value id tuple to value tuple
        """
        data = self.load_full_parameter_value_data(db_map_parameter_values, action)
        return {
            key[:-3] + ((None, index),) + key[-3:]: value
            for key, value in data.items()
            for index in self._indexes(value)
        }

    def load_parameter_value_data(self):
        """Returns a dict that merges empty and full parameter_value data.

        Returns:
            dict: Key is a tuple object_id, ..., parameter_id, value is the parameter_value or None if not specified.
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
        data = self.load_empty_expanded_parameter_value_data()
        data.update(self.load_full_expanded_parameter_value_data())
        return data

    def get_pivot_preferences(self):
        """Returns saved pivot preferences.

        Returns:
            tuple, NoneType: pivot tuple, or None if no preference stored
        """
        selection_key = (self.current_class_name, self.current_class_type, self.current_input_type)
        if selection_key in self.class_pivot_preferences:
            rows = self.class_pivot_preferences[selection_key].index
            columns = self.class_pivot_preferences[selection_key].columns
            frozen = self.class_pivot_preferences[selection_key].frozen
            frozen_value = self.class_pivot_preferences[selection_key].frozen_value
            return (rows, columns, frozen, frozen_value)
        return None

    def reload_pivot_table(self, current_index=None):
        """Updates current class (type and id) and reloads pivot table for it."""
        self._pending_index = None
        if current_index is not None:
            self.current_class_item = self._get_current_class_item(current_index)
        if self.current_class_item is None:
            self.current_class_id = {}
            self.clear_pivot_table()
            return
        class_id = self.current_class_item.db_map_ids
        if self.current_class_id == class_id:
            return
        self.clear_pivot_table()
        self.current_class_type = self.current_class_item.item_type
        self.current_class_id = class_id
        self.current_class_name = self.current_class_item.display_data
        self.do_reload_pivot_table()

    @staticmethod
    def _get_current_class_item(current_index):
        item = current_index.model().item_from_index(current_index)
        while item.item_type != "root":
            if item.item_type in ("object_class", "relationship_class"):
                return item
            item = item.parent_item
        return None

    @Slot("QAction")
    def _handle_pivot_action_triggered(self, action):
        self.current_input_type = action.text()
        if self.ui.pivot_table.isVisible():
            self.do_reload_pivot_table()

    @busy_effect
    def do_reload_pivot_table(self):
        """Reloads pivot table. """
        qApp.processEvents()  # pylint: disable=undefined-variable
        if not self._can_build_pivot_table():
            return
        self.pivot_table_model = {
            self._PARAMETER_VALUE: ParameterValuePivotTableModel,
            self._RELATIONSHIP: RelationshipPivotTableModel,
            self._INDEX_EXPANSION: IndexExpansionPivotTableModel,
            self._SCENARIO_ALTERNATIVE: ScenarioAlternativePivotTableModel,
        }[self.current_input_type](self)
        self.pivot_table_proxy.setSourceModel(self.pivot_table_model)
        delegate = self.pivot_table_model.make_delegate(self)
        self.ui.pivot_table.setItemDelegate(delegate)
        self.pivot_table_model.modelReset.connect(self.make_pivot_headers)
        pivot = self.get_pivot_preferences()
        self.wipe_out_filter_menus()
        self.pivot_table_model.call_reset_model(pivot)
        self.pivot_table_proxy.clear_filter()
        self.reload_frozen_table()

    def _can_build_pivot_table(self):
        if self.current_input_type != self._SCENARIO_ALTERNATIVE and not self.current_class_id:
            return False
        if self.current_input_type == self._RELATIONSHIP and self.current_class_type != "relationship_class":
            return False
        return True

    def clear_pivot_table(self):
        self.wipe_out_filter_menus()
        if self.pivot_table_model:
            self.pivot_table_model.clear_model()
            self.pivot_table_proxy.clear_filter()
        if self.frozen_table_model:
            self.frozen_table_model.clear_model()

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
            column_width = self.ui.frozen_table.horizontalHeader().sectionSize(column)
            header_width = widget.size().width()
            width = max(column_width, header_width)
            self.ui.frozen_table.horizontalHeader().resizeSection(column, width)

    def create_filter_menu(self, identifier):
        """Returns a filter menu for given given object_class identifier.

        Args:
            identifier (int)

        Returns:
            TabularViewFilterMenu
        """
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
        Returns a TabularViewHeaderWidget for given object_class identifier.

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
                self.ui.frozen_table.resizeColumnsToContents()
                self.make_frozen_headers()
            else:
                self.frozen_table_model.clear_model()
        frozen_value = self.get_frozen_value(self.ui.frozen_table.currentIndex())
        self.pivot_table_model.set_pivot(rows, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_input_type)
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
            (self.current_class_name, self.current_class_type, self.current_input_type)
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
        self.ui.frozen_table.resizeColumnsToContents()
        self.make_frozen_headers()
        if frozen_value in frozen_values:
            # update selected row
            ind = frozen_values.index(frozen_value)
            self.ui.frozen_table.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.frozen_table.selectRow(ind + 1)
            self.ui.frozen_table.selectionModel().blockSignals(False)
        else:
            # frozen value not found, remove selection
            self.ui.frozen_table.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.frozen_table.clearSelection()
            self.ui.frozen_table.selectionModel().blockSignals(False)

    def find_frozen_values(self, frozen):
        """Returns a list of tuples containing unique values (object ids) for the frozen indexes (object_class ids).

        Args:
            frozen (tuple(int)): A tuple of currently frozen indexes
        Returns:
            list(tuple(list(int)))
        """
        return list(dict.fromkeys(zip(*[self.pivot_table_model.model.index_values.get(k, []) for k in frozen])).keys())

    # TODO: Move this to the models?
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
        if self.pivot_table_model.receive_objects_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_relationships_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.pivot_table_model.receive_relationships_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_parameter_definitions_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.pivot_table_model.receive_parameter_definitions_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_alternatives_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.pivot_table_model.receive_alternatives_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_parameter_values_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.pivot_table_model.receive_parameter_values_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_scenarios_added_or_removed(self, db_map_data, action):
        if not self.pivot_table_model:
            return
        if self.pivot_table_model.receive_scenarios_added_or_removed(db_map_data, action):
            self.update_filter_menus(action)

    def receive_db_map_data_updated(self, db_map_data, get_class_id):
        if not self.pivot_table_model:
            return
        for db_map, items in db_map_data.items():
            for item in items:
                if get_class_id(item) == self.current_class_id.get(db_map):
                    self.refresh_table_view(self.ui.pivot_table)
                    self.refresh_table_view(self.ui.frozen_table)
                    self.make_pivot_headers()
                    return

    def receive_classes_updated(self, db_map_data):
        if not self.pivot_table_model:
            return
        for db_map, items in db_map_data.items():
            for item in items:
                if item["id"] == self.current_class_id.get(db_map):
                    self.do_reload_pivot_table()
                    return

    def receive_classes_removed(self, db_map_data):
        if not self.pivot_table_model:
            return
        for db_map, items in db_map_data.items():
            for item in items:
                if item["id"] == self.current_class_id.get(db_map):
                    self.current_class_type = None
                    self.current_class_id = {}
                    self.clear_pivot_table()
                    return

    def receive_alternatives_added(self, db_map_data):
        """Reacts to alternatives added event."""
        super().receive_alternatives_added(db_map_data)
        self.receive_alternatives_added_or_removed(db_map_data, action="add")

    def receive_scenarios_added(self, db_map_data):
        """Reacts to scenarios added event."""
        super().receive_scenarios_added(db_map_data)
        self.receive_scenarios_added_or_removed(db_map_data, action="add")

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

    def receive_alternatives_updated(self, db_map_data):
        """Reacts to alternatives updated event."""
        super().receive_alternatives_updated(db_map_data)
        if not self.pivot_table_model:
            return
        self.refresh_table_view(self.ui.pivot_table)
        self.refresh_table_view(self.ui.frozen_table)
        self.make_pivot_headers()

    def receive_object_classes_updated(self, db_map_data):
        """Reacts to object classes updated event."""
        super().receive_object_classes_updated(db_map_data)
        self.receive_classes_updated(db_map_data)

    def receive_relationship_classes_updated(self, db_map_data):
        """Reacts to relationship classes updated event."""
        super().receive_relationship_classes_updated(db_map_data)
        self.receive_classes_updated(db_map_data)

    def receive_objects_updated(self, db_map_data):
        """Reacts to objects updated event."""
        super().receive_objects_updated(db_map_data)
        self.receive_db_map_data_updated(db_map_data, get_class_id=lambda x: x["class_id"])

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

    def receive_scenarios_updated(self, db_map_data):
        super().receive_scenarios_updated(db_map_data)
        if not self.pivot_table_model:
            return
        self.pivot_table_model.receive_scenarios_updated(db_map_data)

    def receive_alternatives_removed(self, db_map_data):
        """Reacts to alternatives removed event."""
        super().receive_alternatives_removed(db_map_data)
        self.receive_alternatives_added_or_removed(db_map_data, action="remove")

    def receive_scenarios_removed(self, db_map_data):
        """Reacts to scenarios removed event."""
        super().receive_scenarios_removed(db_map_data)
        self.receive_scenarios_added_or_removed(db_map_data, action="remove")

    def receive_object_classes_removed(self, db_map_data):
        """Reacts to object classes removed event."""
        super().receive_object_classes_removed(db_map_data)
        self.receive_classes_removed(db_map_data)

    def receive_relationship_classes_removed(self, db_map_data):
        """Reacts to relationship classes remove event."""
        super().receive_relationship_classes_removed(db_map_data)
        self.receive_classes_removed(db_map_data)

    def receive_objects_removed(self, db_map_data):
        """Reacts to objects removed event."""
        super().receive_objects_removed(db_map_data)
        self.receive_objects_added_or_removed(db_map_data, action="remove")

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
