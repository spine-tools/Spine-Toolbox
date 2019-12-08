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

import operator
from collections import namedtuple
from PySide2.QtCore import QItemSelection, Qt, Slot
from .custom_menus import PivotTableModelMenu, PivotTableHorizontalHeaderMenu
from .tabular_view_header_widget import TabularViewHeaderWidget
from .custom_menus import FilterMenu
from ..helpers import fix_name_ambiguity, tuple_itemgetter, busy_effect
from ..mvcmodels.pivot_table_models import PivotTableSortFilterProxy, PivotTableModel


class TabularViewMixin:
    """Provides the pivot table and its frozen table for the DS form."""

    # constant strings
    _RELATIONSHIP_CLASS = "relationship class"
    _OBJECT_CLASS = "object class"

    _DATA_VALUE = "Parameter value"
    _DATA_SET = "Relationship"

    _JSON_TIME_NAME = "json time"
    _PARAMETER_NAME = "parameter"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # current state of ui
        self.current_class_type = ''
        self.current_class_name = ''
        self.current_input_type = ''
        self.relationships = {}
        self.relationship_classes = {}
        self.object_classes = {}
        self.objects = {}
        self.parameters = {}
        self.parameter_values = {}
        self.relationship_tuple_key = ()
        self.original_index_names = {}
        self.filter_menus = {}
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])
        self.ui.comboBox_pivot_table_input_type.addItems([self._DATA_VALUE, self._DATA_SET])
        self.proxy_model = PivotTableSortFilterProxy()
        self.model = PivotTableModel(self)
        self.proxy_model.setSourceModel(self.model)
        self.ui.pivot_table.setModel(self.proxy_model)
        self.ui.pivot_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.pivot_table.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.pivot_table.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        # TODO: It's enough to pass self.ui.pivot_table to the constructors below
        self.pivot_table_menu = PivotTableModelMenu(self.model, self.proxy_model, self.ui.pivot_table)
        self._pivot_table_horizontal_header_menu = PivotTableHorizontalHeaderMenu(self.model, self.ui.pivot_table)

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
        self.model.index_entries_changed.connect(self.table_index_entries_changed)
        self.ui.pivot_table.horizontalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.pivot_table.verticalHeader().header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.header_dropped.connect(self.handle_header_dropped)
        self.ui.frozen_table.selectionModel().selectionChanged.connect(self.change_frozen_value)
        self.ui.comboBox_pivot_table_input_type.currentTextChanged.connect(self.refresh_pivot_table)
        self.ui.dockWidget_pivot_table.visibilityChanged.connect(self._handle_pivot_table_visibility_changed)
        self.ui.dockWidget_frozen_table.visibilityChanged.connect(self._handle_frozen_table_visibility_changed)

    def init_models(self):
        """Initializes models."""
        super().init_models()
        self.load_classes_and_parameter_definitions()
        self.load_objects()

    def commit_enabled(self):
        return super().commit_enabled() or self.model_has_changes()

    def current_object_class_list(self):
        return self.relationship_classes[self.current_class_name]["object_class_name_list"].split(',')

    def load_classes_and_parameter_definitions(self):
        self.object_classes = {oc["name"]: oc for oc in self.db_mngr.get_items(self.db_map, "object class")}
        self.relationship_classes = {rc["name"]: rc for rc in self.db_mngr.get_items(self.db_map, "relationship class")}
        self.parameters = {p["parameter_name"]: p for p in self.db_mngr.get_items(self.db_map, "parameter definition")}

    def load_objects(self):
        self.objects = {o["name"]: o for o in self.db_mngr.get_items(self.db_map, "object")}

    def load_relationships(self):
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            class_id = self.relationship_classes[self.current_class_name]["id"]
            self.relationships = {
                tuple(int(i) for i in r["object_id_list"].split(",")): r
                for r in self.db_mngr.get_items_by_field(self.db_map, "relationship", "class_id", class_id)
            }
            self.relationship_tuple_key = tuple(self.current_object_class_list())

    def _parameter_value_data(self):
        """Returns a list of dict items from the parameter value model
        corresponding to the currently selected class.

        Returns:
            list(dict)
        """
        entity_class = self.db_mngr.get_item_by_field(
            self.db_map, self.current_class_type, "name", self.current_class_name
        )
        model = {
            self._OBJECT_CLASS: self.object_parameter_value_model,
            self._RELATIONSHIP_CLASS: self.relationship_parameter_value_model,
        }[self.current_class_type]
        sub_model = None
        for sub_model in model.single_models:
            if (sub_model.db_map, sub_model.entity_class_id) == (self.db_map, entity_class["id"]):
                break
        else:
            return []
        if sub_model.canFetchMore():
            model._fetch_sub_model = sub_model
            model.fetchMore()
        ids = sub_model._main_data
        return [self.db_mngr.get_item(self.db_map, "parameter value", id_) for id_ in ids]

    def load_parameter_values(self):
        data = self._parameter_value_data()
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            parameter_values = {(d["object_id_list"], d["parameter_id"]): d["id"] for d in data}
            data = [
                d["object_name_list"].split(',') + [d["parameter_name"], d["id"]]
                for d in data
                if d["value"] is not None
            ]
            index_names = self.current_object_class_list()
            index_types = [str] * len(index_names)
        else:
            parameter_values = {(d["object_id"], d["parameter_id"]): d["id"] for d in data}
            data = [[d["object_name"], d["parameter_name"], d["id"]] for d in data if d["value"] is not None]
            index_names = [self.current_class_name]
            index_types = [str]
        index_names.extend([self._PARAMETER_NAME])
        index_types.extend([str])
        return data, index_names, index_types, parameter_values

    def load_set_data(self):
        marker = '\u274C'  # '\u2714'
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            data = [r["object_name_list"].split(',') + [marker] for r in self.relationships.values()]
            index_names = self.current_object_class_list()
            index_types = [str for _ in index_names]
        else:
            data = [
                [o["name"], marker]
                for o in self.objects.values()
                if o["class_id"] == self.object_classes[self.current_class_name]["id"]
            ]
            index_names = [self.current_class_name]
            index_types = [str]
        return data, index_names, index_types

    @Slot(bool)
    def commit_session(self, checked=False):
        """Commits session."""
        self.save_model()
        super().commit_session()

    @Slot(bool)
    def rollback_session(self, checked=False):
        super().rollback_session()
        self.refresh_pivot_table()

    def model_has_changes(self):
        """checks if PivotModel has any changes"""
        if self.model.model._edit_data:
            return True
        if self.model.model._deleted_data:
            return True
        if any(bool(v) for k, v in self.model.model._added_index_entries.items() if k != self._JSON_TIME_NAME):
            return True
        if any(bool(v) for k, v in self.model.model._deleted_index_entries.items() if k != self._JSON_TIME_NAME):
            return True
        if any(bool(v) for v in self.model.model._added_tuple_index_entries.values()):
            return True
        if any(bool(v) for v in self.model.model._deleted_tuple_index_entries.values()):
            return True
        return False

    @Slot(QItemSelection, QItemSelection)
    def change_frozen_value(self, selected, deselected):
        item = self.ui.frozen_table.get_selected_row()
        self.model.set_frozen_value(item)
        self.make_pivot_headers()
        # update pivot history
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(
            self.model.model.pivot_rows,
            self.model.model.pivot_columns,
            self.model.model.pivot_frozen,
            self.model.model.frozen_value,
        )

    def get_pivot_preferences(self, selection_key, index_names):
        if selection_key in self.class_pivot_preferences:
            # get previously used pivot
            rows = self.class_pivot_preferences[selection_key].index
            columns = self.class_pivot_preferences[selection_key].columns
            frozen = self.class_pivot_preferences[selection_key].frozen
            frozen_value = self.class_pivot_preferences[selection_key].frozen_value
        else:
            # use default pivot
            rows = [n for n in index_names if n != self._PARAMETER_NAME]
            columns = [self._PARAMETER_NAME] if self._PARAMETER_NAME in index_names else []
            frozen = []
            frozen_value = ()
        return rows, columns, frozen, frozen_value

    def _is_class_index(self, index, class_type):
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
            self.save_model()
            self.refresh_pivot_table()
            self.pivot_table_menu.relationship_tuple_key = self.relationship_tuple_key
            self.pivot_table_menu.class_type = self.current_class_type
        self.ui.dockWidget_frozen_table.setVisible(self.ui.dockWidget_pivot_table.isVisible())

    @Slot(bool)
    def _handle_frozen_table_visibility_changed(self, visible):
        if visible:
            self.ui.dockWidget_pivot_table.show()

    @Slot("QItemSelection", "QItemSelection")
    def _handle_entity_tree_selection_changed(self, selected, deselected):
        if self.ui.dockWidget_pivot_table.isVisible():
            self.save_model()
            self.refresh_pivot_table()
            self.pivot_table_menu.relationship_tuple_key = self.relationship_tuple_key
            self.pivot_table_menu.class_type = self.current_class_type

    def refresh_pivot_table(self):
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
            self.do_refresh_pivot_table(class_type, selected.data(Qt.DisplayRole))

    @busy_effect
    def do_refresh_pivot_table(self, class_type, class_name):
        """Refreshes pivot table.

        Args:
            class_type (str)
            class_name (str)
        """
        self.current_class_type = class_type
        self.current_class_name = class_name
        self.current_input_type = self.ui.comboBox_pivot_table_input_type.currentText()
        self.load_relationships()
        index_entries, tuple_entries, valid_index_values, used_index_entries = self.get_valid_entries_dicts()
        if self.current_input_type == self._DATA_SET:
            data, index_names, index_types = self.load_set_data()
            tuple_entries = {}
            valid_index_values = {}
            index_entries.pop(self._PARAMETER_NAME, None)
        else:
            data, index_names, index_types, self.parameter_values = self.load_parameter_values()
        # make names unique
        real_names = index_names
        unique_names = list(index_names)
        unique_names = fix_name_ambiguity(unique_names)
        self.original_index_names = {u: r for u, r in zip(unique_names, real_names)}
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            self.relationship_tuple_key = tuple(unique_names[: len(self.current_object_class_list())])
        # get pivot preference for current selection
        selection_key = (self.current_class_name, self.current_class_type, self.current_input_type)
        rows, columns, frozen, frozen_value = self.get_pivot_preferences(selection_key, unique_names)
        # update model and views
        self.model.set_data(
            data,
            unique_names,
            index_types,
            rows,
            columns,
            frozen,
            frozen_value,
            index_entries,
            valid_index_values,
            tuple_entries,
            used_index_entries,
            real_names,
        )
        self.proxy_model.clear_filter()
        self.update_filter_menus()
        self.update_frozen_table_to_model()
        self.make_pivot_headers()

    def get_valid_entries_dicts(self):
        """TODO: Try and explain this."""
        tuple_entries = {}
        used_index_entries = {}
        valid_index_values = {self._JSON_TIME_NAME: range(1, 9999999)}
        # used_index_entries[(self.PARAMETER_NAME,)] = set(
        #    p["parameter_name"] for p in self.db_mngr.get_items(self.db_map, "parameter definition")
        # )
        index_entries = {}
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            relationship_class = self.db_mngr.get_item_by_field(
                self.db_map, "relationship class", "name", self.current_class_name
            )
            object_class_names = tuple(relationship_class["object_class_name_list"].split(','))
            # used_index_entries[object_class_names] = set(
            #    o["name"] for o in self.db_mngr.get_items(self.db_map, "object")
            # )
            index_entries[self._PARAMETER_NAME] = set(
                p["parameter_name"]
                for p in self.db_mngr.get_items_by_field(
                    self.db_map, "parameter definition", "relationship_class_id", relationship_class["id"]
                )
            )
            tuple_entries[(self._PARAMETER_NAME,)] = set((i,) for i in index_entries[self._PARAMETER_NAME])
            for oc in self.db_mngr.get_items(self.db_map, "object class"):
                index_entries[oc["name"]] = set(
                    o["name"] for o in self.db_mngr.get_items_by_field(self.db_map, "object", "class_id", oc["id"])
                )
            unique_class_names = list(object_class_names)
            unique_class_names = fix_name_ambiguity(unique_class_names)
            tuple_entries[tuple(unique_class_names)] = set(
                tuple(r["object_name_list"].split(',')) for r in self.relationships.values()
            )
        else:
            object_class = self.db_mngr.get_item_by_field(self.db_map, "object class", "name", self.current_class_name)
            index_entries[self.current_class_name] = set(
                o["name"]
                for o in self.db_mngr.get_items_by_field(self.db_map, "object", "class_id", object_class["id"])
            )
            index_entries[self._PARAMETER_NAME] = set(
                p["parameter_name"]
                for p in self.db_mngr.get_items_by_field(
                    self.db_map, "parameter definition", "object_class_id", object_class["id"]
                )
            )
            tuple_entries[(self._PARAMETER_NAME,)] = set((i,) for i in index_entries[self._PARAMETER_NAME])
            tuple_entries[(self.current_class_name,)] = set((i,) for i in index_entries[self.current_class_name])
        return index_entries, tuple_entries, valid_index_values, used_index_entries

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

    def update_filter_menus(self):
        """Creates and stores filter menus for each object class.
        These menus are then attached to TabularViewHeaderWidgets as they move around (by drag-and-drop).
        The idea is that the TabularViewHeaderWidget remembers the filter.
        """
        self.filter_menus.clear()
        for unique_name, object_class_name in self.original_index_names.items():
            self.filter_menus[unique_name] = menu = FilterMenu(self)
            menu.set_filter_list(self.model.model.index_entries[object_class_name])
            menu.unique_name = unique_name
            menu.object_class_name = object_class_name
            menu.filterChanged.connect(self.change_filter)

    def make_pivot_headers(self):
        """
        Turns top left indexes in the pivot table into TabularViewHeaderWidget.
        """
        top_indexes, left_indexes = self.model.top_left_indexes()
        for index in left_indexes:
            proxy_index = self.proxy_model.mapFromSource(index)
            widget = self.create_header_widget(proxy_index.data(Qt.DisplayRole), "columns")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
        for index in top_indexes:
            proxy_index = self.proxy_model.mapFromSource(index)
            widget = self.create_header_widget(proxy_index.data(Qt.DisplayRole), "rows")
            self.ui.pivot_table.setIndexWidget(proxy_index, widget)
            self.ui.pivot_table.resizeColumnToContents(index.column())

    def make_frozen_headers(self):
        """
        Turns indexes in the first row of the frozen table into TabularViewHeaderWidget.
        """
        for column in range(self.ui.frozen_table.model.columnCount()):
            index = self.ui.frozen_table.model.index(0, column)
            widget = self.create_header_widget(index.data(Qt.DisplayRole), "frozen", with_menu=False)
            self.ui.frozen_table.setIndexWidget(index, widget)
            self.ui.frozen_table.resizeColumnToContents(column)

    def create_header_widget(self, unique_name, area, with_menu=True):
        """
        Returns a TabularViewHeaderWidget with given name.

        Args:
            unique_name (str)
            area (str)
            with_menu (bool)

        Returns:
            TabularViewHeaderWidget
        """
        if with_menu:
            menu = self.filter_menus[unique_name]
        else:
            menu = None
        widget = TabularViewHeaderWidget(unique_name, area, menu=menu, parent=self)
        widget.header_dropped.connect(self.handle_header_dropped)
        return widget

    @staticmethod
    def _get_insert_index(pivot_list, catcher, position):
        """Returns an index for inserting a new element in the given pivot list.

        Returns:
            int
        """
        if isinstance(catcher, TabularViewHeaderWidget):
            i = pivot_list.index(catcher.name)
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
        top_indexes, left_indexes = self.model.top_left_indexes()
        rows = [index.data() for index in top_indexes]
        columns = [index.data() for index in left_indexes]
        frozen = self.ui.frozen_table.headers
        dropped_list = {"columns": columns, "rows": rows, "frozen": frozen}[dropped.area]
        catcher_list = {"columns": columns, "rows": rows, "frozen": frozen}[catcher.area]
        dropped_list.remove(dropped.name)
        i = self._get_insert_index(catcher_list, catcher, position)
        catcher_list.insert(i, dropped.name)
        if dropped.area == "frozen" or catcher.area == "frozen":
            if frozen:
                frozen_values = self.find_frozen_values(frozen)
                self.ui.frozen_table.set_data(frozen_values, frozen)
                self.make_frozen_headers()
            else:
                self.ui.frozen_table.set_data([], [])
        frozen_value = self.ui.frozen_table.get_selected_row()
        self.model.set_pivot(rows, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_input_type)
        ] = self.PivotPreferences(rows, columns, frozen, frozen_value)
        self.make_pivot_headers()

    @Slot(object, set, bool)
    def change_filter(self, menu, valid, has_filter):
        if has_filter:
            self.proxy_model.set_filter(menu.unique_name, valid)
        else:
            self.proxy_model.set_filter(menu.unique_name, None)  # None means everything passes

    def update_frozen_table_to_model(self):
        frozen = self.model.model.pivot_frozen
        frozen_values = self.find_frozen_values(frozen)
        frozen_value = self.model.model.frozen_value
        self.ui.frozen_table.set_data(frozen_values, frozen)
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
        if not frozen:
            return []
        keys = tuple(self.model.model.index_names.index(i) for i in frozen)
        getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
        frozen_values = set(getter(key) for key in self.model.model._data)
        # add indexes without values
        for k, v in self.model.model.tuple_index_entries.items():
            if set(k).issuperset(frozen):
                position = [i for i, name in enumerate(k) if name in frozen]
                position_to_frozen = [frozen.index(name) for name in k if name in frozen]
                new_set = set()
                new_row = [None for _ in position]
                for line in v:
                    for i_k, i_frozen in zip(position, position_to_frozen):
                        new_row[i_frozen] = line[i_k]
                    new_set.add(tuple(new_row))
                frozen_values.update(new_set)
        return sorted(frozen_values)

    def delete_parameter_values(self, delete_values):
        values_to_delete = set()
        update_data = []
        # index to object classes
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            obj_ind = range(len(self.current_object_class_list()))
        else:
            obj_ind = [0]
        par_ind = len(obj_ind)
        index_ind = par_ind
        for k in delete_values.keys():
            obj_id = tuple(self.objects[k[i]]["id"] for i in obj_ind)
            if self.current_class_type == self._OBJECT_CLASS:
                obj_id = obj_id[0]
            else:
                obj_id = ",".join(map(str, obj_id))
            par_id = self.parameters[k[par_ind]]["id"]
            index = k[index_ind]
            key = (obj_id, par_id, index)
            if key in self.parameter_values:
                if self.current_input_type == self._DATA_VALUE:
                    # only delete values where only one field is populated
                    values_to_delete.append(self.parameter_values[key])
                else:
                    # remove value from parameter_value field but not entire row
                    update_data.append({"id": self.parameter_values[key], self.current_input_type: None})
        if values_to_delete:
            self.db_mngr.remove_items({self.db_map: {"parameter value list": values_to_delete}})
        if update_data:
            self.db_mngr.update_parameter_values({self.db_map: update_data})

    def delete_relationships(self, delete_relationships):
        relationships_to_delete = list()
        for del_rel in delete_relationships:
            if all(n in self.objects for n in del_rel):
                obj_ids = tuple(self.objects[n]["id"] for n in del_rel)
                if obj_ids in self.relationships:
                    relationships_to_delete.append(self.relationships.pop(obj_ids))
        if relationships_to_delete:
            self.db_mngr.remove_items({self.db_map: {"relationship": relationships_to_delete}})

    def delete_index_values_from_db(self, delete_indexes):
        if not delete_indexes:
            return
        object_names = []
        parameter_names = []
        # TODO: identify parameter and index and json time dimensions some other way.
        for k, on in delete_indexes.items():
            if k == self._PARAMETER_NAME:
                parameter_names += on
            elif k != self._JSON_TIME_NAME:
                object_names += on
        # find ids
        delete_objects = list()
        for on in object_names:
            if on in self.objects:
                delete_objects.append(self.objects[on])
                self.objects.pop(on)
        delete_parameters = list()
        for pn in parameter_names:
            if pn in self.parameters:
                parameter = self.parameters[pn]
                delete_parameters.append(parameter)
                self.parameters.pop(pn)
        if delete_objects:
            self.db_mngr.remove_items({self.db_map: {"object": delete_objects}})
        if delete_parameters:
            self.db_mngr.remove_items({self.db_map: {"parameter definition": delete_parameters}})

    def add_index_values_to_db(self, add_indexes):
        db_edited = False
        if not any(v for v in add_indexes.values()):
            return db_edited
        new_objects = []
        new_parameters = []
        # TODO: identify parameter and index and json time dimensions some other way.
        for k, on in add_indexes.items():
            if k == self._PARAMETER_NAME:
                if self.current_class_type == self._OBJECT_CLASS:
                    class_id = self.object_classes[self.current_class_name]["id"]
                    new_parameters += [{"name": n, "object_class_id": class_id} for n in on]
                else:
                    new_parameters += [
                        {"name": n, "relationship_class_id": self.relationship_classes[self.current_class_name]["id"]}
                        for n in on
                    ]
            elif k != self._JSON_TIME_NAME:
                new_objects += [{"name": n, "class_id": self.object_classes[k]["id"]} for n in on]
        if new_objects:
            self.db_mngr.add_objects({self.db_map: new_objects})
            db_edited = True
        if new_parameters:
            self.db_mngr.add_parameter_definitions({self.db_map: new_parameters})
            db_edited = True
        return db_edited

    def save_model_set(self):
        db_edited = False
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            # find all objects and insert new into db for each class in relationship
            rel_getter = operator.itemgetter(*range(len(self.current_object_class_list())))
            add_relationships = set(
                rel_getter(index) for index, value in self.model.model._edit_data.items() if value is None
            )
            delete_relationships = set(rel_getter(index) for index, value in self.model.model._deleted_data.items())
            self.current_object_class_list()
            add_objects = []
            for i, name in enumerate(self.current_object_class_list()):
                # only keep objects that has a relationship
                new = self.model.model._added_index_entries[name]
                new_data_set = set(r[i] for r in add_relationships)
                new = [n for n in new if n in new_data_set]
                add_objects.extend([{'name': n, 'class_id': self.object_classes[name]["id"]} for n in new])
            if add_objects:
                self.db_mngr.add_objects({self.db_map: add_objects})
                self.load_objects()
            if delete_relationships:
                ids = [tuple(self.objects[i]["id"] for i in rel) for rel in delete_relationships]
                relationships_to_delete = list()
                for deletable_id in ids:
                    if deletable_id in self.relationships:
                        deletable = self.relationships.pop(deletable_id)
                        relationships_to_delete.append(deletable)
                if relationships_to_delete:
                    self.db_mngr.remove_items({self.db_map: {"relationship": relationships_to_delete}})
            if add_relationships:
                ids = [(tuple(self.objects[i]["id"] for i in rel), '_'.join(rel)) for rel in delete_relationships]
                c_id = self.relationship_classes[self.current_class_name]["id"]
                insert_rels = [
                    {'object_id_list': r[0], 'name': r[1], 'class_id': c_id} for r in ids if r not in self.relationships
                ]
                if insert_rels:
                    self.db_mngr.add_relationships({self.db_map: insert_rels})
                    db_edited = True
        elif self.current_class_type == self._OBJECT_CLASS:
            # find removed and new objects, only keep indexes in data
            delete_objects = set(index[0] for index in self.model.model._deleted_data)
            add_objects = set(index[0] for index, value in self.model.model._edit_data.items() if value is None)
            if delete_objects:
                objects_to_delete = list()
                for name in delete_objects:
                    deletable = self.objects[name]
                    objects_to_delete.append(deletable)
                self.db_mngr.remove_items({self.db_map: {"object": objects_to_delete}})
                db_edited = True
            if add_objects:
                class_id = self.object_classes[self.current_class_name]["id"]
                add_objects = [{"name": o, "class_id": class_id} for o in add_objects]
                self.db_mngr.add_objects({self.db_map: add_objects})
                db_edited = True
        return db_edited

    def save_model(self):
        db_edited = False
        self.db_mngr.signaller.listeners[self].remove(self.db_map)
        if self.current_input_type == self._DATA_SET:
            db_edited = self.save_model_set()
            delete_indexes = self.model.model._deleted_index_entries
            self.delete_index_values_from_db(delete_indexes)
        elif self.current_input_type == self._DATA_VALUE:
            # save new objects and parameters
            add_indexes = self.model.model._added_index_entries
            obj_edited = self.add_index_values_to_db(add_indexes)
            if obj_edited:
                self.parameters = {
                    p["parameter_name"]: p for p in self.db_mngr.get_items(self.db_map, "parameter definition")
                }
                self.load_objects()

            delete_values = self.model.model._deleted_data
            data = self.model.model._edit_data
            data_value = self.model.model._data
            # delete values
            self.delete_parameter_values(delete_values)

            if self.current_class_type == self._RELATIONSHIP_CLASS:
                # add and remove relationships
                if self.relationship_tuple_key in self.model.model._deleted_tuple_index_entries:
                    delete_relationships = self.model.model._deleted_tuple_index_entries[self.relationship_tuple_key]
                    self.delete_relationships(delete_relationships)
                rel_edited = self.save_relationships()
                if rel_edited:
                    self.load_relationships()
            # save parameter values
            self.save_parameter_values(data, data_value)
            # delete objects and parameters
            delete_indexes = self.model.model._deleted_index_entries
            self.delete_index_values_from_db(delete_indexes)

        # update model
        self.model.model.clear_track_data()
        # reload classes, objects and parameters
        if db_edited:
            self.load_classes_and_parameter_definitions()
            self.load_objects()
        self.db_mngr.signaller.listeners[self].add(self.db_map)

    def save_parameter_values(self, data, data_value):
        new_data = []
        update_data = []

        # index to object classes
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            obj_ind = range(len(self.current_object_class_list()))
            id_field = "relationship_id"
        else:
            obj_ind = [0]
            id_field = "object_id"
        par_ind = len(obj_ind)
        for k in data.keys():
            obj_id = tuple(self.objects[k[i]]["id"] for i in obj_ind)
            par_id = self.parameters[k[par_ind]]["id"]
            db_id = None
            if self.current_class_type == self._RELATIONSHIP_CLASS:
                if obj_id in self.relationships:
                    db_id = self.relationships[obj_id]["id"]
                obj_id = ",".join(map(str, obj_id))
            else:
                obj_id = obj_id[0]
                db_id = obj_id
            key = (obj_id, par_id)
            if key in self.parameter_values:
                value_id = self.parameter_values[key]
                update_data.append({"id": value_id, self.current_input_type: data_value[k]})
            elif db_id:
                new_data.append(
                    {id_field: db_id, "parameter_definition_id": par_id, self.current_input_type: data_value[k]}
                )
        if new_data:
            self.db_mngr.add_parameter_values({self.db_map: new_data})
        if update_data:
            self.db_mngr.update_parameter_values({self.db_map: update_data})

    def save_relationships(self):
        new_rels = []
        db_edited = False
        if self.relationship_tuple_key in self.model.model._added_tuple_index_entries:
            # relationships added by tuple
            rels = self.model.model._added_tuple_index_entries[self.relationship_tuple_key]
            for rel in rels:
                if all(n in self.objects for n in rel):
                    obj_ids = tuple(self.objects[n]["id"] for n in rel)
                    if obj_ids not in self.relationships:
                        new_rels.append(
                            {
                                'object_id_list': obj_ids,
                                'class_id': self.relationship_classes[self.current_class_name]["id"],
                                'name': '_'.join(rel),
                            }
                        )
        # save relationships
        if new_rels:
            self.db_mngr.add_relationships({self.db_map: new_rels})
            db_edited = True
        return db_edited

    def receive_object_classes_added(self, db_map_data):
        """Reacts to object classes added event."""
        super().receive_object_classes_added(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_objects_added(self, db_map_data):
        """Reacts to objects added event."""
        super().receive_objects_added(db_map_data)
        self.load_objects()

    def receive_relationship_classes_added(self, db_map_data):
        """Reacts to relationship classes added."""
        super().receive_relationship_classes_added(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_relationships_added(self, db_map_data):
        """Reacts to relationships added event."""
        super().receive_relationships_added(db_map_data)
        self.load_relationships()

    def receive_parameter_definitions_added(self, db_map_data):
        """Reacts to parameter definitions added event."""
        super().receive_parameter_definitions_added(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_parameter_values_added(self, db_map_data):
        """Reacts to parameter values added event."""
        super().receive_parameter_values_added(db_map_data)
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.refresh_pivot_table()
                break

    def receive_object_classes_updated(self, db_map_data):
        """Reacts to object classes updated event."""
        super().receive_object_classes_updated(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_objects_updated(self, db_map_data):
        """Reacts to objects updated event."""
        super().receive_objects_updated(db_map_data)
        self.load_objects()

    def receive_relationship_classes_updated(self, db_map_data):
        """Reacts to relationship classes updated event."""
        super().receive_relationship_classes_updated(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_relationships_updated(self, db_map_data):
        """Reacts to relationships updated event."""
        super().receive_relationships_updated(db_map_data)
        self.load_relationships()

    def receive_parameter_definitions_updated(self, db_map_data):
        """Reacts to parameter definitions updated event."""
        super().receive_parameter_definitions_updated(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_parameter_values_updated(self, db_map_data):
        """Updates parameter values if they are included in the selected object/relationship class."""
        super().receive_parameter_values_updated(db_map_data)
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.refresh_pivot_table()
                break

    def receive_object_classes_removed(self, db_map_data):
        """Reacts to object classes removed event."""
        super().receive_object_classes_removed(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_objects_removed(self, db_map_data):
        """Reacts to objects removed event."""
        super().receive_objects_removed(db_map_data)
        self.load_objects()

    def receive_relationship_classes_removed(self, db_map_data):
        """Reacts to relationship classes remove event."""
        super().receive_relationship_classes_removed(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_relationships_removed(self, db_map_data):
        """Reacts to relationships removed event."""
        super().receive_relationships_removed(db_map_data)
        self.load_relationships()

    def receive_parameter_definitions_removed(self, db_map_data):
        """Reacts to parameter definitions removed event."""
        super().receive_parameter_definitions_removed(db_map_data)
        self.load_classes_and_parameter_definitions()

    def receive_parameter_values_removed(self, db_map_data):
        """Reacts to parameter values removed event."""
        super().receive_parameter_values_removed(db_map_data)
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Data Store view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.refresh_pivot_table()
                break

    def receive_session_committed(self, db_maps):
        """Reacts to session committed event."""
        super().receive_session_committed(db_maps)
        self.load_classes_and_parameter_definitions()

    def receive_session_rolled_back(self, db_maps):
        """Reacts to session rolled back event."""
        super().receive_session_rolled_back(db_maps)
        self.load_classes_and_parameter_definitions()
        self.refresh_pivot_table()

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event if 'X' is clicked.
        """
        if self.model_has_changes():
            self.save_model()
        super().closeEvent(event)
