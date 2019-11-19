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

import json
import operator
from collections import namedtuple
from PySide2.QtWidgets import QListWidget, QMainWindow, QMessageBox, QPushButton, QTableView
from PySide2.QtCore import QItemSelection, Qt, QTimer, QSettings, Slot
from PySide2.QtGui import QDropEvent, QIcon, QGuiApplication
from sqlalchemy.sql import literal_column
from spinedb_api import from_database, DateTime, Duration, ParameterValueFormatError, TimePattern, TimeSeries
from .custom_menus import FilterMenu, PivotTableModelMenu, PivotTableHorizontalHeaderMenu
from .parameter_value_editor import ParameterValueEditor
from ..helpers import fix_name_ambiguity, tuple_itemgetter, busy_effect
from ..mvcmodels.pivot_table_models import PivotTableSortFilterProxy, PivotTableModel
from ..config import MAINWINDOW_SS

# TODO: Move to helpers.py?
def unpack_json(data):
    expanded_data = []
    for d in data:
        json_array = json.loads(d[-1])
        json_index = list(range(1, len(json_array) + 1))
        new_data = [a + [b, c] for a, b, c in zip([d[:-1]] * len(json_array), json_index, json_array)]
        expanded_data = expanded_data + new_data
    return expanded_data


class TabularViewForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store."""

    # constant strings
    _RELATIONSHIP_CLASS = "relationship"
    _OBJECT_CLASS = "object"

    _DATA_JSON = "json"
    _DATA_VALUE = "value"
    _DATA_SET = "set"

    _JSON_TIME_NAME = "json time"
    _PARAMETER_NAME = "db parameter"

    def __init__(self, project, db_url):
        """
        Args:
            project (SpineToolboxProject): The project instance that owns this form
            db_url (str): The url to view
        """
        from ..ui.tabular_view_form import Ui_MainWindow

        super().__init__(flags=Qt.Window)
        # TODO: change the list_select_class to something nicer
        # Setup UI from Qt Designer file
        self.db_url = db_url
        self.db_mngr = project.db_mngr
        url, codename = self.db_url
        self.db_map = self.db_mngr.get_db_map_for_listener(self, url, codename=codename)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        # settings
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.settings_key = 'tabularViewWidget'

        # database
        self.database = self.db_map.codename
        self._project = project

        # current state of ui
        self.current_class_type = ''
        self.current_class_name = ''
        self.current_value_type = ''
        self.relationships = []
        self.relationship_class = []
        self.object_classes = []
        self.objects = []
        self.parameters = []
        self.parameter_values = {}
        self.relationship_tuple_key = ()
        self.original_index_names = {}
        self.filter_buttons = []
        self.filter_menus = []

        # history of selected pivot
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])

        # available settings for values
        self.ui.comboBox_value_type.addItems([self._DATA_VALUE, self._DATA_SET])

        # set allowed drop for pivot index lists
        self.ui.list_index.allowedDragLists = [self.ui.list_column, self.ui.list_frozen]
        self.ui.list_column.allowedDragLists = [self.ui.list_index, self.ui.list_frozen]
        self.ui.list_frozen.allowedDragLists = [self.ui.list_index, self.ui.list_column]

        # pivot model and filterproxy
        self.proxy_model = PivotTableSortFilterProxy()
        self.model = PivotTableModel()
        self.proxy_model.setSourceModel(self.model)
        self.ui.pivot_table.setModel(self.proxy_model)
        self.ui.pivot_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pivot_table_menu = PivotTableModelMenu(self.model, self.proxy_model, self.ui.pivot_table)
        table_header = self.ui.pivot_table.horizontalHeader()
        table_header.setContextMenuPolicy(Qt.CustomContextMenu)
        self._pivot_table_horizontal_header_menu = PivotTableHorizontalHeaderMenu(self.model, self.ui.pivot_table)

        # connect signals
        self.ui.pivot_table.customContextMenuRequested.connect(self.pivot_table_menu.request_menu)
        table_header.customContextMenuRequested.connect(self._pivot_table_horizontal_header_menu.request_menu)
        self.ui.list_index.afterDrop.connect(self.change_pivot)
        self.ui.list_column.afterDrop.connect(self.change_pivot)
        self.ui.list_frozen.afterDrop.connect(self.change_pivot)
        self.model.index_entries_changed.connect(self.table_index_entries_changed)
        self.ui.table_frozen.selectionModel().selectionChanged.connect(self.change_frozen_value)
        self.ui.comboBox_value_type.currentTextChanged.connect(self.select_data)
        self.ui.list_select_class.currentItemChanged.connect(self.change_class)
        self.ui.actionCommit.triggered.connect(self.commit_session)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.menuSession.aboutToShow.connect(self.set_session_menu_enable)

        # override `edit` virtual function in `pivot_table`
        self.ui.pivot_table.edit = self.pivot_table_edit

        # load db data
        self.load_class_data()
        self.load_objects()
        self.update_class_list()

        # Set window title
        self.setWindowTitle("Data store tabular view    -- {} --".format(self.database))

        # restore previous ui state
        self.restore_ui()

        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    @busy_effect
    def pivot_table_edit(self, index, trigger, event):
        """Starts editing the item at index from pivot_table.
        If the index contains some 'complex' parameter value,
        we open the parameter value editor window instead.
        """
        # pylint: disable=bad-super-call
        if not super(QTableView, self.ui.pivot_table).edit(index, trigger, event):
            return False
        if self.model.index_in_data(index):
            try:
                value = from_database(index.data(role=Qt.EditRole))
            except ParameterValueFormatError:
                value = None
            if isinstance(value, (DateTime, Duration, TimePattern, TimeSeries)) or value is None:
                # Close the normal editor and show the `ParameterValueEditor` instead
                self.ui.pivot_table.closePersistentEditor(index)
                editor = ParameterValueEditor(index, value=value, parent_widget=self)
                editor.show()
        return True

    @Slot()
    def set_session_menu_enable(self):
        """Checks if session can commit or rollback and updates session menu actions"""
        if not self.db_map.has_pending_changes() and not self.model_has_changes():
            # nothing new to commit
            self.ui.actionCommit.setDisabled(True)
            self.ui.actionRollback.setDisabled(True)
        else:
            self.ui.actionCommit.setEnabled(True)
            self.ui.actionRollback.setEnabled(True)

    def load_class_data(self):
        self.object_classes = {oc.name: oc for oc in self.db_map.object_class_list().all()}
        self.relationship_classes = {rc.name: rc for rc in self.db_map.wide_relationship_class_list().all()}
        self.parameters = {p.name: p for p in self.db_map.parameter_definition_list().all()}

    def load_objects(self):
        self.objects = {o.name: o for o in self.db_map.object_list().all()}

    def load_relationships(self):
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            class_id = self.relationship_classes[self.current_class_name].id
            self.relationships = {
                tuple(int(i) for i in r.object_id_list.split(",")): r
                for r in self.db_map.wide_relationship_list(class_id=class_id).all()
            }
            self.relationship_tuple_key = tuple(
                self.relationship_classes[self.current_class_name].object_class_name_list.split(',')
            )

    def load_parameter_values(self):
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            query = self.db_map.relationship_parameter_value_list()
            query = query.filter(literal_column("relationship_class_name") == self.current_class_name)
            data = query.all()
            parameter_values = {(r.object_id_list, r.parameter_id): r.id for r in data}
            data = [d.object_name_list.split(',') + [d.parameter_name, d.value] for d in data if d.value is not None]
            index_names = self.current_object_class_list()
            index_types = [str] * len(index_names)
        else:
            query = self.db_map.object_parameter_value_list()
            query = query.filter(literal_column("object_class_name") == self.current_class_name)
            data = query.all()
            parameter_values = {(r.object_id, r.parameter_id): r.id for r in data}
            data = [[d.object_name, d.parameter_name, d.value] for d in data if d.value is not None]
            index_names = [self.current_class_name]
            index_types = [str]
        index_names.extend([self._PARAMETER_NAME])
        index_types.extend([str])
        if self.current_value_type == self._DATA_JSON:
            data = unpack_json(data)
            index_names.append(self._JSON_TIME_NAME)
            index_types = index_types + [int]
        return data, index_names, index_types, parameter_values

    def current_object_class_list(self):
        return self.relationship_classes[self.current_class_name].object_class_name_list.split(',')

    def get_set_data(self):
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            data = [r.object_name_list.split(',') + ['x'] for r in self.relationships.values()]
            index_names = self.current_object_class_list()
            index_types = [str for _ in index_names]
        else:
            data = [
                [o.name, 'x']
                for o in self.objects.values()
                if o.class_id == self.object_classes[self.current_class_name].id
            ]
            index_names = [self.current_class_name]
            index_types = [str]
        return data, index_names, index_types

    def update_class_list(self):
        """update list_select_class with all object classes and relationship classes"""
        oc = sorted(set(self._OBJECT_CLASS + ': ' + oc.name for oc in self.object_classes.values()))
        rc = sorted(set(self._RELATIONSHIP_CLASS + ': ' + oc.name for oc in self.relationship_classes.values()))
        self.ui.list_select_class.addItems(oc + rc)
        self.ui.list_select_class.setCurrentItem(self.ui.list_select_class.item(0))

    @Slot(bool)
    def commit_session(self, checked=False):
        self.save_model()
        self.db_mngr.commit_session(self.db_map)

    @Slot(bool)
    def rollback_session(self, checked=False):
        self.db_mngr.rollback_session(self.db_map)
        self.select_data()

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
        item = self.ui.table_frozen.get_selected_row()
        self.model.set_frozen_value(item)
        # update pivot history
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_value_type)
        ] = self.PivotPreferences(
            self.model.model.pivot_rows,
            self.model.model.pivot_columns,
            self.model.model.pivot_frozen,
            self.model.model.frozen_value,
        )

    def _get_selected_class(self):
        """Returns the type and name of the currently selected object/relationship class."""
        selected = self.ui.list_select_class.currentItem()
        if selected:
            text = selected.text()
            class_type, class_name = text.split(': ')
            return class_type, class_name
        return None, None

    def pack_dict_json(self):
        """Pack down values with json_index into a json_array"""
        # TODO: can this be made a bit faster?
        # pack last index of dict to json
        if not self.model.model._edit_data and not self.model.model._deleted_data:
            return {}, set()
        # extract edited keys without time index
        edited_keys = set(k[:-1] for k in self.model.model._edit_data)
        edited_keys.update(set(k[:-1] for k in self.model.model._deleted_data))
        # find data for edited keys.
        edited_data = {k: [] for k in edited_keys}
        for k in self.model.model._data:
            if k[:-1] in edited_data:
                edited_data[k[:-1]].append([k[-1], self.model.model._data[k]])
        # pack into json
        keyfunc = operator.itemgetter(0)
        packed_data = {}
        empty_keys = set()
        for k, v in edited_data.items():
            if not v:
                # no values found
                empty_keys.add(k)
                continue
            v = sorted(v, key=keyfunc)
            json_values = []
            # create list of values from index 1 to end index.
            # if value for index doesn't exist replace with zero.
            v_ind = 0
            for i in range(1, v[-1][0] + 1):
                if v[v_ind][0] == i:
                    json_values.append(v[v_ind][1])
                    v_ind = v_ind + 1
                else:
                    json_values.append(0)
            packed_data[k] = json.dumps(json_values)

        return packed_data, empty_keys

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
            obj_id = tuple(self.objects[k[i]].id for i in obj_ind)
            if self.current_class_type == self._OBJECT_CLASS:
                obj_id = obj_id[0]
            else:
                obj_id = ",".join(map(str, obj_id))
            par_id = self.parameters[k[par_ind]].id
            index = k[index_ind]
            key = (obj_id, par_id, index)
            if key in self.parameter_values:
                if self.current_value_type == self._DATA_VALUE:
                    # only delete values where only one field is populated
                    values_to_delete.append(self.parameter_values[key]._asdict())
                else:
                    # remove value from parameter_value field but not entire row
                    update_data.append({"id": self.parameter_values[key], self.current_value_type: None})
        if values_to_delete:
            self.db_mngr.remove_items({self.db_map: {"parameter value list": values_to_delete}})
        if update_data:
            self.db_mngr.update_parameter_values({self.db_map: update_data})

    def delete_relationships(self, delete_relationships):
        relationships_to_delete = list()
        for del_rel in delete_relationships:
            if all(n in self.objects for n in del_rel):
                obj_ids = tuple(self.objects[n].id for n in del_rel)
                if obj_ids in self.relationships:
                    relationships_to_delete.append(self.relationships.pop(obj_ids)._asdict())
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
                delete_objects.append(self.objects[on]._asdict())
                self.objects.pop(on)
        delete_parameters = list()
        for pn in parameter_names:
            if pn in self.parameters:
                # Need to convert the parameter definition structs to something the other data store views understand.
                parameter = self.parameters[pn]._asdict()
                parameter["parameter_name"] = parameter.pop("name")
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
                    class_id = self.object_classes[self.current_class_name].id
                    new_parameters += [{"name": n, "object_class_id": class_id} for n in on]
                else:
                    new_parameters += [
                        {"name": n, "relationship_class_id": self.relationship_classes[self.current_class_name].id}
                        for n in on
                    ]
            elif k != self._JSON_TIME_NAME:
                new_objects += [{"name": n, "class_id": self.object_classes[k].id} for n in on]
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
                add_objects.extend([{'name': n, 'class_id': self.object_classes[name].id} for n in new])
            if add_objects:
                self.db_mngr.add_objects({self.db_map: add_objects})
                self.load_objects()
            if delete_relationships:
                ids = [tuple(self.objects[i].id for i in rel) for rel in delete_relationships]
                relationships_to_delete = list()
                for deletable_id in ids:
                    if deletable_id in self.relationships:
                        deletable = self.relationships.pop(deletable_id)._asdict()
                        relationships_to_delete.append(deletable)
                if relationships_to_delete:
                    self.db_mngr.remove_items({self.db_map: {"relationship": relationships_to_delete}})
            if add_relationships:
                ids = [(tuple(self.objects[i].id for i in rel), '_'.join(rel)) for rel in delete_relationships]
                c_id = self.relationship_classes[self.current_class_name].id
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
                    deletable = self.objects[name]._asdict()
                    objects_to_delete.append(deletable)
                self.db_mngr.remove_items({self.db_map: {"object": objects_to_delete}})
                db_edited = True
            if add_objects:
                class_id = self.object_classes[self.current_class_name].id
                add_objects = [{"name": o, "class_id": class_id} for o in add_objects]
                self.db_mngr.add_objects({self.db_map: add_objects})
                db_edited = True
        return db_edited

    def save_model(self):
        db_edited = False
        self.db_mngr.remove_db_map_listener(self.db_map, self)
        if self.current_value_type == self._DATA_SET:
            db_edited = self.save_model_set()
            delete_indexes = self.model.model._deleted_index_entries
            self.delete_index_values_from_db(delete_indexes)
        elif self.current_value_type in [self._DATA_JSON, self._DATA_VALUE]:
            # save new objects and parameters
            add_indexes = self.model.model._added_index_entries
            obj_edited = self.add_index_values_to_db(add_indexes)
            if obj_edited:
                self.parameters = {p.name: p for p in self.db_map.parameter_definition_list().all()}
                self.load_objects()

            if self.current_value_type == self._DATA_VALUE:
                delete_values = self.model.model._deleted_data
                data = self.model.model._edit_data
                data_value = self.model.model._data
            elif self.current_value_type == self._DATA_JSON:
                data_value, delete_values = self.pack_dict_json()
                delete_values = {k: None for k in delete_values}
                data = data_value
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
            self.load_class_data()
            self.load_objects()
        self.db_mngr.signaller.add_db_map_listener(self.db_map, self)

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
            obj_id = tuple(self.objects[k[i]].id for i in obj_ind)
            par_id = self.parameters[k[par_ind]].id
            db_id = None
            if self.current_class_type == self._RELATIONSHIP_CLASS:
                if obj_id in self.relationships:
                    db_id = self.relationships[obj_id].id
                obj_id = ",".join(map(str, obj_id))
            else:
                obj_id = obj_id[0]
                db_id = obj_id
            key = (obj_id, par_id)
            if key in self.parameter_values:
                value_id = self.parameter_values[key]
                update_data.append({"id": value_id, self.current_value_type: data_value[k]})
            elif db_id:
                new_data.append(
                    {id_field: db_id, "parameter_definition_id": par_id, self.current_value_type: data_value[k]}
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
                    obj_ids = tuple(self.objects[n].id for n in rel)
                    if obj_ids not in self.relationships:
                        new_rels.append(
                            {
                                'object_id_list': obj_ids,
                                'class_id': self.relationship_classes[self.current_class_name].id,
                                'name': '_'.join(rel),
                            }
                        )
        # save relationships
        if new_rels:
            self.db_mngr.add_relationships({self.db_map: new_rels})
            db_edited = True
        return db_edited

    def update_pivot_lists_to_new_model(self):
        self.ui.list_index.clear()
        self.ui.list_column.clear()
        self.ui.list_frozen.clear()
        self.ui.list_index.addItems(self.model.model.pivot_rows)
        self.ui.list_column.addItems(self.model.model.pivot_columns)
        self.ui.list_frozen.addItems(self.model.model.pivot_frozen)

    def update_frozen_table_to_model(self):
        frozen = self.model.model.pivot_frozen
        frozen_values = self.find_frozen_values(frozen)
        frozen_value = self.model.model.frozen_value
        self.ui.table_frozen.set_data(frozen, frozen_values)
        if frozen_value in frozen_values:
            # update selected row
            ind = frozen_values.index(frozen_value)
            self.ui.table_frozen.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.table_frozen.selectRow(ind)
            self.ui.table_frozen.selectionModel().blockSignals(False)
        else:
            # frozen value not found, remove selection
            self.ui.table_frozen.selectionModel().blockSignals(True)  # prevent selectionChanged signal when updating
            self.ui.table_frozen.clearSelection()
            self.ui.table_frozen.selectionModel().blockSignals(False)

    @Slot("QListWidgetItem", "QListWidgetItem")
    def change_class(self, current, previous):
        self.save_model()
        self.select_data()
        self.pivot_table_menu.relationship_tuple_key = self.relationship_tuple_key
        self.pivot_table_menu.class_type = self.current_class_type

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

    def get_valid_entries_dicts(self):
        tuple_entries = {}
        used_index_entries = {}
        valid_index_values = {self._JSON_TIME_NAME: range(1, 9999999)}
        # used_index_entries[(self.PARAMETER_NAME,)] = set(p.name for p in self.parameters.values())
        index_entries = {}
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            object_class_names = tuple(
                self.relationship_classes[self.current_class_name].object_class_name_list.split(',')
            )
            # used_index_entries[object_class_names] = set(o.name for o in self.objects.values())
            index_entries[self._PARAMETER_NAME] = set(
                p.name
                for p in self.parameters.values()
                if p.relationship_class_id == self.relationship_classes[self.current_class_name].id
            )
            tuple_entries[(self._PARAMETER_NAME,)] = set((i,) for i in index_entries[self._PARAMETER_NAME])
            for oc in object_class_names:
                index_entries[oc] = set(
                    o.name for o in self.objects.values() if o.class_id == self.object_classes[oc].id
                )
            unique_class_names = list(object_class_names)
            unique_class_names = fix_name_ambiguity(unique_class_names)
            tuple_entries[tuple(unique_class_names)] = set(
                tuple(r.object_name_list.split(',')) for r in self.relationships.values()
            )
        else:
            index_entries[self.current_class_name] = set(
                o.name for o in self.objects.values() if o.class_id == self.object_classes[self.current_class_name].id
            )
            index_entries[self._PARAMETER_NAME] = set(
                p.name
                for p in self.parameters.values()
                if p.object_class_id == self.object_classes[self.current_class_name].id
            )
            tuple_entries[(self._PARAMETER_NAME,)] = set((i,) for i in index_entries[self._PARAMETER_NAME])
            tuple_entries[(self.current_class_name,)] = set((i,) for i in index_entries[self.current_class_name])

        return index_entries, tuple_entries, valid_index_values, used_index_entries

    @Slot(str)
    def select_data(self, text=""):
        class_type, class_name = self._get_selected_class()
        if class_type is None or class_name is None:
            return
        self.current_class_type = class_type
        self.current_class_name = class_name
        self.current_value_type = self.ui.comboBox_value_type.currentText()
        self.load_relationships()
        index_entries, tuple_entries, valid_index_values, used_index_entries = self.get_valid_entries_dicts()
        if self.current_value_type == self._DATA_SET:
            data, index_names, index_types = self.get_set_data()
            tuple_entries = {}
            valid_index_values = {}
            index_entries.pop(self._PARAMETER_NAME, None)
        else:
            data, index_names, index_types, parameter_values = self.load_parameter_values()
            self.parameter_values = parameter_values

        # make names unique
        real_names = index_names
        unique_names = list(index_names)
        unique_names = fix_name_ambiguity(unique_names)
        self.original_index_names = {u: r for u, r in zip(unique_names, real_names)}
        if self.current_class_type == self._RELATIONSHIP_CLASS:
            self.relationship_tuple_key = tuple(unique_names[: len(self.current_object_class_list())])
        # get pivot preference for current selection
        selection_key = (self.current_class_name, self.current_class_type, self.current_value_type)
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
        self.update_filters_to_new_model()
        self.update_pivot_lists_to_new_model()
        self.update_frozen_table_to_model()

    @Slot(dict, dict)
    def table_index_entries_changed(self, added_entries, deleted_entries):
        for button, menu in zip(self.filter_buttons, self.filter_menus):
            name = button.text()
            if name in deleted_entries:
                menu.remove_items_from_filter_list(deleted_entries[name])
            if name in added_entries:
                menu.add_items_to_filter_list(added_entries[name])

    def update_filters_to_new_model(self):
        new_names = list(self.model.model.index_entries.keys())
        for i, name in enumerate(new_names):
            if i < len(self.filter_buttons):
                # filter exists, update
                self.filter_buttons[i].setText(name)
            else:
                # doesn't exist, create new
                button, menu = self.create_filter_widget(name)
                self.filter_buttons.append(button)
                self.filter_menus.append(menu)
                self.ui.h_layout_filter.addWidget(button)
            # update items in combobox
            self.filter_menus[i].set_filter_list(self.model.model.index_entries[name])
        # delete unused filters
        for i in reversed(range(len(new_names), max(len(new_names), len(self.filter_buttons)))):
            button = self.filter_buttons.pop(i)
            menu = self.filter_menus.pop(i)
            self.ui.h_layout_filter.removeWidget(button)
            button.deleteLater()
            menu.deleteLater()

    def create_filter_widget(self, name):
        button = QPushButton(name)
        menu = FilterMenu(button)
        menu.filterChanged.connect(self.change_filter)
        button.setMenu(menu)
        return button, menu

    def change_filter(self, menu, valid, has_filter):
        checked_items = set()
        name = self.filter_buttons[self.filter_menus.index(menu)].text()
        if has_filter:
            checked_items = valid
        self.proxy_model.set_filter(name, checked_items)

    @Slot(QListWidget, QDropEvent)
    def change_pivot(self, parent, event):
        # TODO: when getting items from the list that was source of drop
        # the dropped item is not removed, ugly solution is to filter the other list
        index = [self.ui.list_index.item(x).text() for x in range(self.ui.list_index.count())]
        columns = [self.ui.list_column.item(x).text() for x in range(self.ui.list_column.count())]
        frozen = [self.ui.list_frozen.item(x).text() for x in range(self.ui.list_frozen.count())]

        if parent == self.ui.list_index:
            frozen = [x for x in frozen if x not in index]
            columns = [x for x in columns if x not in index]
        elif parent == self.ui.list_column:
            frozen = [x for x in frozen if x not in columns]
            index = [x for x in index if x not in columns]
        elif parent == self.ui.list_frozen:
            columns = [x for x in columns if x not in frozen]
            index = [x for x in index if x not in frozen]

        if frozen and parent == self.ui.list_frozen or event.source() == self.ui.list_frozen:
            frozen_values = self.find_frozen_values(frozen)
            self.ui.table_frozen.set_data(frozen, frozen_values)
            for i in range(self.ui.table_frozen.model.columnCount()):
                self.ui.table_frozen.resizeColumnToContents(i)
        elif not frozen and parent == self.ui.list_frozen or event.source() == self.ui.list_frozen:
            self.ui.table_frozen.set_data([], [])
        frozen_value = self.ui.table_frozen.get_selected_row()
        self.model.set_pivot(index, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[
            (self.current_class_name, self.current_class_type, self.current_value_type)
        ] = self.PivotPreferences(index, columns, frozen, frozen_value)

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

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("{0}/windowSize".format(self.settings_key))
        window_pos = self.qsettings.value("{0}/windowPosition".format(self.settings_key))
        window_maximized = self.qsettings.value("{0}/windowMaximized".format(self.settings_key), defaultValue='false')
        n_screens = self.qsettings.value("{0}/n_screens".format(self.settings_key), defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        # restore splitters
        splitters = [self.ui.splitter_3, self.ui.splitter_2, self.ui.splitter]
        splitter_keys = ["/splitterSelectTable", "/splitterTableFilter", "/splitterPivotFrozen"]
        splitter_states = [self.qsettings.value(s) for s in (self.settings_key + p for p in splitter_keys)]
        for state, splitter in zip(splitter_states, splitters):
            if state:
                splitter.restoreState(state)

    def save_ui(self):
        """Saves UI state"""
        # save qsettings
        self.qsettings.setValue("{}/windowSize".format(self.settings_key), self.size())
        self.qsettings.setValue("{}/windowPosition".format(self.settings_key), self.pos())
        self.qsettings.setValue(
            "{}/windowMaximized".format(self.settings_key), self.windowState() == Qt.WindowMaximized
        )
        self.qsettings.setValue("{}/splitterSelectTable".format(self.settings_key), self.ui.splitter_3.saveState())
        self.qsettings.setValue("{}/splitterTableFilter".format(self.settings_key), self.ui.splitter_2.saveState())
        self.qsettings.setValue("{}/splitterPivotFrozen".format(self.settings_key), self.ui.splitter.saveState())

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QCloseEvent): Closing event if 'X' is clicked.
        """
        # show commit dialog if pending changes
        if self.model_has_changes():
            self.save_model()
        if not self.db_mngr.remove_db_map_listener(self.db_map, self):
            event.ignore()
            return
        # save ui state
        self.save_ui()
        event.accept()

    def receive_object_classes_added(self, db_map_data):
        """Reacts to object classes added event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_objects_added(self, db_map_data):
        """Reacts to objects added event."""
        self.load_objects()

    def receive_relationship_classes_added(self, db_map_data):
        """Reacts to relationship classes added."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_relationships_added(self, db_map_data):
        """Reacts to relationships added event."""
        self.load_relationships()

    def receive_parameter_definitions_added(self, db_map_data):
        """Reacts to parameter definitions added event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_parameter_values_added(self, db_map_data):
        """Reacts to parameter values added event."""
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Tabular view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.select_data()
                break

    def receive_parameter_value_lists_added(self, db_map_data):
        """Does nothing as we don't care about parameter value lists here."""

    def receive_parameter_tags_added(self, db_map_data):
        """Does nothing as we don't care about parameter tags here."""

    def receive_object_classes_updated(self, db_map_data):
        """Reacts to object classes updated event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_objects_updated(self, db_map_data):
        """Reacts to objects updated event."""
        self.load_objects()

    def receive_relationship_classes_updated(self, db_map_data):
        """Reacts to relationship classes updated event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_relationships_updated(self, db_map_data):
        """Reacts to relationships updated event."""
        self.load_relationships()

    def receive_parameter_definitions_updated(self, db_map_data):
        """Reacts to parameter definitions updated event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_parameter_values_updated(self, db_map_data):
        """Updates parameter values if they are included in the selected object/relationship class."""
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Tabular view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.select_data()
                break

    def receive_parameter_value_lists_updated(self, db_map_data):
        """Does nothing as we don't care about parameter value lists here."""

    def receive_parameter_tags_updated(self, db_map_data):
        """Does nothing as we don't care about parameter tags here."""

    def receive_object_classes_removed(self, db_map_data):
        """Reacts to object classes removed event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_objects_removed(self, db_map_data):
        """Reacts to objects removed event."""
        self.load_objects()

    def receive_relationship_classes_removed(self, db_map_data):
        """Reacts to relationship classes remove event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_relationships_removed(self, db_map_data):
        """Reacts to relationships removed event."""
        self.load_relationships()

    def receive_parameter_definitions_removed(self, db_map_data):
        """Reacts to parameter definitions removed event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_parameter_values_removed(self, db_map_data):
        """Reacts to parameter values removed event."""
        if len(db_map_data) > 1 or self.db_map not in db_map_data:
            raise RuntimeError("Tabular view received parameter value update from wrong database.")
        changed_data = db_map_data[self.db_map]
        for changes in changed_data:
            class_name = (
                changes["object_class_name"] if "object_class_name" in changes else changes["relationship_class_name"]
            )
            if class_name == self.current_class_name:
                self.select_data()
                break

    def receive_parameter_value_lists_removed(self, db_map_data):
        """Does nothing as we don't care about parameter value lists here."""

    def receive_parameter_tags_removed(self, db_map_data):
        """Does nothing as we don't care about parameter tags here."""

    def receive_session_committed(self, db_maps):
        """Reacts to session committed event."""
        self.load_class_data()
        self.ui.list_select_class.clear()
        self.update_class_list()

    def receive_session_rolled_back(self, db_maps):
        """Reacts to session rolled back event."""
        self.load_class_data()
        self.ui.list_select_class.blockSignals(True)
        self.ui.list_select_class.clear()
        self.update_class_list()
        self.ui.list_select_class.blockSignals(False)
        self.select_data()

    def receive_session_closed(self, db_maps):
        """Reacts to session closed event."""
        if self.db_map in db_maps:
            QMessageBox.critical(
                self,
                "Connection closed",
                f"The connection to {self.db_map.codename} has been closed by an external action."
                f" This form will now close.",
            )
            QTimer.singleShot(0, self.close)
