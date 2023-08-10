######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""
from contextlib import contextmanager
from itertools import product
from collections import namedtuple
from PySide6.QtCore import QModelIndex, Qt, Slot, QTimer
from PySide6.QtGui import QAction, QIcon, QActionGroup
from PySide6.QtWidgets import QWidget

from spinedb_api.helpers import fix_name_ambiguity
from .custom_menus import TabularViewFilterMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from ...helpers import busy_effect, CharIconEngine, preferred_row_height, disconnect
from ..mvcmodels.pivot_table_models import (
    PivotTableSortFilterProxy,
    ParameterValuePivotTableModel,
    RelationshipPivotTableModel,
    IndexExpansionPivotTableModel,
    ScenarioAlternativePivotTableModel,
)
from ..mvcmodels.frozen_table_model import FrozenTableModel

# FIXME: only_visible=False???


class TabularViewMixin:
    """Provides the pivot table and its frozen table for the Database editor."""

    _PARAMETER_VALUE = "&Value"
    _INDEX_EXPANSION = "&Index"
    _RELATIONSHIP = "Re&lationship"
    _SCENARIO_ALTERNATIVE = "&Scenario"

    _PARAMETER = "parameter"
    _ALTERNATIVE = "alternative"
    _INDEX = "index"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pivot_table_models = {
            self._PARAMETER_VALUE: ParameterValuePivotTableModel(self),
            self._RELATIONSHIP: RelationshipPivotTableModel(self),
            self._INDEX_EXPANSION: IndexExpansionPivotTableModel(self),
            self._SCENARIO_ALTERNATIVE: ScenarioAlternativePivotTableModel(self),
        }
        self._pending_reload = False
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
        self.frozen_table_model = FrozenTableModel(self.db_mngr, self)
        self._disable_frozen_table_reload = False
        self.ui.pivot_table.setModel(self.pivot_table_proxy)
        self.ui.pivot_table.connect_spine_db_editor(self)
        self.ui.frozen_table.setModel(self.frozen_table_model)
        self.ui.frozen_table.verticalHeader().setDefaultSectionSize(preferred_row_height(self))

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
        self.ui.pivot_table.header_changed.connect(self._connect_pivot_table_header_signals)
        self.ui.frozen_table.header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.selectionModel().currentChanged.connect(self._change_selected_frozen_row)
        self.frozen_table_model.rowsInserted.connect(self._check_frozen_value_selected)
        self.frozen_table_model.rowsRemoved.connect(self._check_frozen_value_selected)
        self.frozen_table_model.columnsInserted.connect(self._make_inserted_frozen_headers)
        self.frozen_table_model.modelReset.connect(self._make_all_frozen_headers)
        self.frozen_table_model.selected_row_changed.connect(
            self._change_frozen_value, Qt.ConnectionType.QueuedConnection
        )
        self.pivot_action_group.triggered.connect(self._handle_pivot_action_triggered)
        self.ui.dockWidget_pivot_table.visibilityChanged.connect(self._handle_pivot_table_visibility_changed)
        self.db_mngr.items_updated.connect(self._reload_pivot_table_if_needed)

    def refresh_views(self):
        for table_view in (self.ui.pivot_table, self.ui.frozen_table):
            top_left = table_view.indexAt(table_view.rect().topLeft())
            bottom_right = table_view.indexAt(table_view.rect().bottomRight())
            if not bottom_right.isValid():
                model = table_view.model()
                bottom_right = table_view.model().index(model.rowCount() - 1, model.columnCount() - 1)
            table_view.model().dataChanged.emit(top_left, bottom_right)

    # FIXME MM: this should be called after modifications
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

    def _needs_to_update_headers(self, item_type, db_map_data):
        for db_map in self.db_maps:
            items = db_map_data.get(db_map)
            if not items:
                continue
            if self.current_input_type in (self._PARAMETER_VALUE, self._INDEX_EXPANSION):
                if item_type in ("object_class", "relationship_class"):
                    for item in items:
                        if item["id"] == self.current_class_id.get(db_map):
                            return True
                    if item_type == "object_class":
                        object_class_id_list = {
                            db_map_class_id.get(db_map) for db_map_class_id in self.current_object_class_id_list
                        }
                        for item in items:
                            if item["id"] in object_class_id_list:
                                return True
            elif self.current_input_type == self._RELATIONSHIP:
                if item_type == "relationship_class":
                    for item in items:
                        if item["id"] == self.current_class_id.get(db_map):
                            return True
                elif item_type == "object_class":
                    object_class_id_list = {
                        db_map_class_id.get(db_map) for db_map_class_id in self.current_object_class_id_list
                    }
                    for item in items:
                        if item["id"] in object_class_id_list:
                            return True
        return False

    @Slot(str, dict)
    def _reload_pivot_table_if_needed(self, item_type, db_map_data):
        if not self.pivot_table_model:
            return
        if self._needs_to_update_headers(item_type, db_map_data):
            self.do_reload_pivot_table()

    @Slot()
    def _connect_pivot_table_header_signals(self):
        """Connects signals of pivot table's header views."""
        self.ui.pivot_table.horizontalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.pivot_table.verticalHeader().header_dropped.connect(self.handle_header_dropped)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.current_class_id.clear()
        self.current_class_type = None
        self.current_class_name = None
        self.clear_pivot_table()

    @Slot(QModelIndex, object)
    def _set_model_data(self, index, value):
        self.pivot_table_proxy.setData(index, value)

    @property
    def current_object_class_id_list(self):
        if self.current_class_type == "object_class":
            return [self.current_class_id]
        current_object_class_id_list = [{} for _ in self.current_object_class_name_list]
        for db_map, class_id in self.current_class_id.items():
            relationship_class = self.db_mngr.get_item(db_map, "relationship_class", class_id)
            for k, id_ in enumerate(relationship_class["object_class_id_list"]):
                current_object_class_id_list[k][db_map] = id_
        return current_object_class_id_list

    @property
    def current_object_class_name_list(self):
        db_map, class_id = next(iter(self.current_class_id.items()))
        if self.current_class_type == "object_class":
            return [self.db_mngr.get_item(db_map, "object_class", class_id)["name"]]
        relationship_class = self.db_mngr.get_item(db_map, "relationship_class", class_id)
        return fix_name_ambiguity(relationship_class["object_class_name_list"])

    @property
    def current_object_class_ids(self):
        return dict(zip(self.current_object_class_name_list, self.current_object_class_id_list))

    @staticmethod
    def _is_class_index(index):
        """Returns whether the given tree index is a class index.

        Args:
            index (QModelIndex): index from object or relationship tree
        Returns:
            bool
        """
        return index.column() == 0 and not index.parent().parent().isValid()

    @Slot(QAction)
    def _handle_pivot_action_triggered(self, action):
        self.current_input_type = action.text()
        # NOTE: Changing the action also triggers a call to `_handle_pivot_table_visibility_changed`
        # with `visible = True`
        # See `SpineDBEditor` class.
        self.do_reload_pivot_table()

    @Slot(bool)
    def _handle_pivot_table_visibility_changed(self, visible):
        if not visible:
            for action in self.pivot_actions.values():
                action.setChecked(False)
            return
        if self._pending_reload:
            self.do_reload_pivot_table()

    @Slot(dict)
    def _handle_object_tree_selection_changed(self, selected_indexes):
        filter_class_ids, filter_entity_ids = super()._handle_object_tree_selection_changed(selected_indexes)
        current = self.ui.treeView_object.currentIndex()
        self._handle_entity_tree_current_changed(current)
        return filter_class_ids, filter_entity_ids

    @Slot(dict)
    def _handle_relationship_tree_selection_changed(self, selected_indexes):
        filter_class_ids, filter_entity_ids = super()._handle_relationship_tree_selection_changed(selected_indexes)
        current = self.ui.treeView_relationship.currentIndex()
        self._handle_entity_tree_current_changed(current)
        return filter_class_ids, filter_entity_ids

    def _handle_entity_tree_current_changed(self, current_index):
        self._update_class_attributes(current_index)
        if self.current_input_type != self._SCENARIO_ALTERNATIVE:
            self.do_reload_pivot_table()

    def _update_class_attributes(self, current_index):
        """Updates current class (type and id) and reloads pivot table for it."""
        current_class_item = self._get_current_class_item(current_index)
        if current_class_item is None:
            return
        class_id = current_class_item.db_map_ids
        if self.current_class_id == class_id:
            return
        self.current_class_id = class_id
        self.current_class_type = current_class_item.item_type
        self.current_class_name = current_class_item.display_data

    @staticmethod
    def _get_current_class_item(current_index):
        if not current_index.isValid():
            return None
        item = current_index.model().item_from_index(current_index)
        while item.item_type != "root":
            if item.item_type in ("object_class", "relationship_class"):
                return item
            item = item.parent_item
        return None

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
            tuple((db_map, id_) for id_ in rel["object_id_list"]) + (db_map,): get_id(db_map, rel)
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

    def _get_db_map_parameter_value_or_def_ids(self, item_type):
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
        db_map_ids = self._get_db_map_parameter_value_or_def_ids(item_type)
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
                for db_map, ids in self._get_db_map_parameter_value_or_def_ids("parameter_definition").items()
            }
        if db_map_alternative_ids is None:
            db_map_alternative_ids = {
                db_map: [(db_map, a["id"]) for a in self.db_mngr.get_items(db_map, "alternative")]
                for db_map in self.db_maps
            }
        if self.current_class_type == "relationship_class":
            db_map_entity_ids = {
                db_map: [tuple((db_map, id_) for id_ in e["object_id_list"]) for e in entities]
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
            tuple((db_map, id_) for id_ in x["object_id_list"])
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

    @busy_effect
    def do_reload_pivot_table(self):
        """Reloads pivot table."""
        if not self._can_build_pivot_table():
            return
        if not self.ui.dockWidget_pivot_table.isVisible():
            self._pending_reload = True
            return
        self.pivot_actions[self.current_input_type].setChecked(True)
        self.ui.dockWidget_frozen_table.setVisible(True)
        self._pending_reload = False
        pivot_table_model = self._pivot_table_models[self.current_input_type]
        if self.pivot_table_model is not pivot_table_model:
            self.pivot_table_model = pivot_table_model
            self.pivot_table_proxy.setSourceModel(self.pivot_table_model)
            self.pivot_table_model.modelReset.connect(self.make_pivot_headers)
            self.pivot_table_model.modelReset.connect(self.reload_frozen_table)
            self.pivot_table_model.frozen_values_added.connect(self._add_values_to_frozen_table)
            self.pivot_table_model.frozen_values_removed.connect(self._remove_values_from_frozen_table)
            delegate = self.pivot_table_model.make_delegate(self)
            self.ui.pivot_table.setItemDelegate(delegate)
        pivot = self.get_pivot_preferences()
        self.wipe_out_filter_menus()
        self.pivot_table_model.call_reset_model(pivot)
        self.pivot_table_proxy.clear_filter()

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
            self.pivot_table_model.modelReset.disconnect(self.make_pivot_headers)
            self.pivot_table_model.modelReset.disconnect(self.reload_frozen_table)
            self.pivot_table_model.frozen_values_added.disconnect(self._add_values_to_frozen_table)
            self.pivot_table_model.frozen_values_removed.disconnect(self._remove_values_from_frozen_table)
            self.pivot_table_model = None
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
            widget = self.create_header_widget(proxy_index.data(Qt.ItemDataRole.DisplayRole), "columns")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
        for index in top_indexes:
            proxy_index = self.pivot_table_proxy.mapFromSource(index)
            widget = self.create_header_widget(proxy_index.data(Qt.ItemDataRole.DisplayRole), "rows")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
        QTimer.singleShot(0, self._resize_pivot_header_columns)

    @Slot()
    def _resize_pivot_header_columns(self):
        if not self.pivot_table_model:
            return
        top_indexes, _ = self.pivot_table_model.top_left_indexes()
        for index in top_indexes:
            self.ui.pivot_table.resizeColumnToContents(index.column())

    @Slot(QModelIndex, int, int)
    def _make_inserted_frozen_headers(self, parent_index, first_column, last_column):
        """Turns the first row of columns in the frozen table into TabularViewHeaderWidgets.

        Args:
            parent_index (QModelIndex): frozen table column's parent index
            first_column (int): first inserted column
            last_column (int): last inserted column
        """
        self._make_frozen_headers(first_column, last_column)

    @Slot()
    def _make_all_frozen_headers(self):
        """Turns the first row of columns in the frozen table into TabularViewHeaderWidgets."""
        if self.frozen_table_model.rowCount() > 0:
            self._make_frozen_headers(0, self.frozen_table_model.columnCount() - 1)

    def _make_frozen_headers(self, first_column, last_column):
        horizontal_header = self.ui.frozen_table.horizontalHeader()
        for column in range(first_column, last_column + 1):
            index = self.frozen_table_model.index(0, column)
            widget = self.create_header_widget(index.data(Qt.ItemDataRole.DisplayRole), "frozen", with_menu=False)
            self.ui.frozen_table.setIndexWidget(index, widget)
            column_width = horizontal_header.sectionSize(column)
            header_width = widget.size().width()
            width = max(column_width, header_width)
            horizontal_header.resizeSection(column, width)

    @Slot(QModelIndex, int, int)
    def _check_frozen_value_selected(self, parent, first_row, last_row):
        """Ensures that at least one row is selected in frozen table when number of rows change."""
        if self.ui.frozen_table.currentIndex().isValid() or self.frozen_table_model.rowCount() < 2:
            return
        self.ui.frozen_table.setCurrentIndex(self.frozen_table_model.index(1, 0))

    def create_filter_menu(self, identifier):
        """Returns a filter menu for given given object_class identifier.

        Args:
            identifier (int)

        Returns:
            TabularViewFilterMenu
        """
        if identifier not in self.filter_menus:
            header = self.pivot_table_model.top_left_headers[identifier]
            if header.header_type == "parameter":
                item_type = "parameter_definition"
            elif header.header_type == "index":
                item_type = "parameter_value"
            else:
                item_type = header.header_type
            if header.header_type == "object":
                accepts_item = (
                    self.accepts_entity_item
                    if self.current_class_type == "object_class"
                    else lambda item, db_map: self.accepts_ith_member_object_item(header.rank, item, db_map)
                )
            elif header.header_type == "parameter":
                accepts_item = self.accepts_parameter_item
            else:
                accepts_item = None
            self.filter_menus[identifier] = menu = TabularViewFilterMenu(
                self, self.db_mngr, self.db_maps, item_type, accepts_item, identifier, show_empty=False
            )
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

    @Slot(QWidget, QWidget, str)
    def handle_header_dropped(self, dropped, catcher, position=""):
        """
        Updates pivots when a header is dropped.

        Args:
            dropped (TabularViewHeaderWidget): drag source widget
            catcher (TabularViewHeaderWidget or PivotTableHeaderView or FrozenTableView): drop target widget
            position (str): either "before", "after", or ""
        """
        top_indexes, left_indexes = self.pivot_table_model.top_left_indexes()
        rows = [index.data(Qt.ItemDataRole.DisplayRole) for index in top_indexes]
        columns = [index.data(Qt.ItemDataRole.DisplayRole) for index in left_indexes]
        list_options = {"columns": columns, "rows": rows, "frozen": self.frozen_table_model.headers}
        dropped_list = list_options[dropped.area]
        catcher_list = list_options[catcher.area]
        destination = self._get_insert_index(catcher_list, catcher, position)
        if dropped.area == "frozen" and catcher.area == "frozen":
            source = dropped_list.index(dropped.identifier)
            self.frozen_table_model.moveColumn(QModelIndex(), source, QModelIndex(), destination)
            self.pivot_table_model.set_frozen(self.frozen_table_model.headers)
            return
        if dropped.area == "frozen":
            source = dropped_list.index(dropped.identifier)
            self.frozen_table_model.remove_column(source)
        else:
            dropped_list.remove(dropped.identifier)
        if catcher.area == "frozen":
            values = set(self.pivot_table_model.model.index_values.get(dropped.identifier, []))
            self.frozen_table_model.insert_column_data(dropped.identifier, values, destination)
        else:
            catcher_list.insert(destination, dropped.identifier)
        frozen_value = self.frozen_table_model.get_frozen_value()
        frozen = self.frozen_table_model.headers
        with self._frozen_table_reload_disabled():
            self.pivot_table_model.set_pivot(rows, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(rows, columns, frozen, frozen_value)
        self.make_pivot_headers()

    @Slot(QModelIndex, QModelIndex)
    def _change_selected_frozen_row(self, current, previous):
        """Sets the frozen value from selection in frozen table."""
        if not current.isValid():
            return
        row = current.row()
        if row == 0:
            selection_model = self.ui.frozen_table.selectionModel()
            with disconnect(selection_model.currentChanged, self._change_selected_frozen_row):
                self.ui.frozen_table.setCurrentIndex(previous)
            return
        if row == previous.row():
            return
        with self._frozen_table_reload_disabled():
            self.frozen_table_model.set_selected(row)

    @Slot(str, set, bool)
    def change_filter(self, identifier, valid_values, has_filter):
        # None means everything passes
        self.pivot_table_proxy.set_filter(identifier, valid_values if has_filter else None)

    @Slot(set)
    def _add_values_to_frozen_table(self, frozen_values):
        """Adds values to frozen table.

        Args:
            frozen_values (set of tuple): values to add
        """
        self.frozen_table_model.add_values(frozen_values)

    @Slot(set)
    def _remove_values_from_frozen_table(self, frozen_values):
        """Removes values from frozen table.

        Args:
            frozen_values (set of tuple): values to remove
        """
        self.frozen_table_model.remove_values(frozen_values)

    @Slot()
    def reload_frozen_table(self):
        """Resets the frozen model according to new selection in entity trees."""
        if self._disable_frozen_table_reload or not self.pivot_table_model:
            return
        frozen = self.pivot_table_model.model.pivot_frozen
        self.frozen_table_model.set_headers(frozen)

    def find_frozen_values(self, frozen):
        """Returns a list of tuples containing unique values for the frozen indexes.

        Args:
            frozen (tuple): A tuple of currently frozen indexes

        Returns:
            list: frozen value
        """
        return list(dict.fromkeys(zip(*[self.pivot_table_model.model.index_values.get(k, []) for k in frozen])).keys())

    @Slot()
    def _change_frozen_value(self):
        """Updated frozen value according to selected row in Frozen table."""
        if self.pivot_table_model is None:
            # Happens at startup.
            return
        frozen_value = self.frozen_table_model.get_frozen_value()
        if not self.pivot_table_model.set_frozen_value(frozen_value):
            return
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(
            self.pivot_table_model.model.pivot_rows,
            self.pivot_table_model.model.pivot_columns,
            self.pivot_table_model.model.pivot_frozen,
            self.pivot_table_model.model.frozen_value,
        )

    def receive_session_rolled_back(self, db_maps):
        """Reacts to session rolled back event."""
        super().receive_session_rolled_back(db_maps)
        self.clear_pivot_table()

    def accepts_entity_item(self, item, db_map):
        return item["class_id"] == self.current_class_id.get(db_map)

    def accepts_parameter_item(self, item, db_map):
        return item["entity_class_id"] == self.current_class_id.get(db_map)

    def accepts_member_object_item(self, item, db_map):
        object_class_id_list = {x[db_map] for x in self.current_object_class_id_list}
        return item["class_id"] in object_class_id_list

    def accepts_ith_member_object_item(self, i, item, db_map):
        return item["class_id"] == self.current_object_class_id_list[i][db_map]

    @contextmanager
    def _frozen_table_reload_disabled(self):
        self._disable_frozen_table_reload = True
        try:
            yield
        finally:
            self._disable_frozen_table_reload = False
