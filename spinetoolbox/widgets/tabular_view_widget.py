######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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
from PySide2.QtWidgets import QMainWindow, QDialog, QPushButton, QMessageBox, QCheckBox
from PySide2.QtCore import Qt, QSettings
from PySide2.QtGui import QIcon, QGuiApplication
from sqlalchemy.sql import literal_column
from spinedb_api import SpineDBAPIError
from ui.tabular_view_form import Ui_MainWindow
from widgets.custom_menus import FilterMenu, PivotTableModelMenu
from helpers import fix_name_ambiguity, tuple_itemgetter
# TODO: connect to all add, delete relationship/object classes widgets to this.
from widgets.custom_qdialog import CommitDialog
from tabularview_models import PivotTableSortFilterProxy, PivotTableModel
from config import MAINWINDOW_SS

# TODO: How about moving these constants to config.py?
ParameterValue = namedtuple('ParameterValue',['id','has_value'])

# constant strings
RELATIONSHIP_CLASS = "relationship"
OBJECT_CLASS = "object"

DATA_JSON = "json"
DATA_VALUE = "value"
DATA_SET = "set"

JSON_TIME_NAME = "json time"
PARAMETER_NAME = "db parameter"


# TODO: Move to helpers.py?
def unpack_json(data):
    expanded_data = []
    for d in data:
        json_array = json.loads(d[-1])
        json_index = list(range(1, len(json_array) + 1))
        new_data = [a + [b, c] for a, b, c in zip([d[:-1]]*len(json_array), json_index, json_array)]
        expanded_data = expanded_data + new_data
    return expanded_data


class TabularViewForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DatabaseMapping): The object relational database mapping
        database (str): The database name
    """
    def __init__(self, data_store, db_map, database):
        super().__init__(flags=Qt.Window)
        # TODO: change the list_select_class to something nicer
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStyleSheet(MAINWINDOW_SS)
        # settings
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.settings_key = 'tabularViewWidget'

        # database
        self.db_map = db_map
        self.database = database
        self._data_store = data_store

        # current state of ui
        self.current_class_type = ''
        self.current_class_name = ''
        self.current_value_type = ''
        self.relationships = []
        self.relationship_class = []
        self.object_classes = []
        self.objects = []
        self.parameters = []
        self.relationship_tuple_key = ()
        self.original_index_names = {}
        self.filter_buttons = []
        self.filter_menus = []

        # history of selected pivot
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])

        # available settings for values
        self.ui.comboBox_value_type.addItems([DATA_VALUE, DATA_SET])

        # set allowed drop for pivot index lists
        self.ui.list_index.allowedDragLists = [self.ui.list_column,self.ui.list_frozen]
        self.ui.list_column.allowedDragLists = [self.ui.list_index,self.ui.list_frozen]
        self.ui.list_frozen.allowedDragLists = [self.ui.list_index,self.ui.list_column]

        # pivot model and filterproxy
        self.proxy_model = PivotTableSortFilterProxy()
        self.model = PivotTableModel()
        self.proxy_model.setSourceModel(self.model)
        self.ui.pivot_table.setModel(self.proxy_model)
        self.ui.pivot_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pivot_table_menu = PivotTableModelMenu(self.model, self.proxy_model, self.ui.pivot_table)

        # connect signals
        self.ui.pivot_table.customContextMenuRequested.connect(self.pivot_table_menu.request_menu)
        self.ui.list_index.afterDrop.connect(self.change_pivot)
        self.ui.list_column.afterDrop.connect(self.change_pivot)
        self.ui.list_frozen.afterDrop.connect(self.change_pivot)
        self.model.index_entries_changed.connect(self.table_index_entries_changed)
        self.ui.table_frozen.selectionModel().selectionChanged.connect(self.change_frozen_value)
        self.ui.comboBox_value_type.currentTextChanged.connect(self.select_data)
        self.ui.list_select_class.itemClicked.connect(self.change_class)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.menuSession.aboutToShow.connect(self.set_session_menu_enable)

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
        if self.current_class_type == RELATIONSHIP_CLASS:
            class_id = self.relationship_classes[self.current_class_name].id
            self.relationships = {tuple(int(i) for i in r.object_id_list.split(",")): r
                                  for r in self.db_map.wide_relationship_list(class_id = class_id).all()}
            self.relationship_tuple_key = tuple(self.relationship_classes[self.current_class_name].object_class_name_list.split(','))

    def load_parameter_values(self):
        if self.current_class_type == RELATIONSHIP_CLASS:
            query = self.db_map.relationship_parameter_value_list()
            query = query.filter(literal_column("relationship_class_name") == self.current_class_name)
            data = query.all()
            parameter_values = {(r.object_id_list, r.parameter_id): r.id for r in data}
            data = [d.object_name_list.split(',') + [d.parameter_name, d.value]
                    for d in data if d.value is not None]
            index_names = self.current_object_class_list()
            index_types = [str] * len(index_names)
        else:
            query = self.db_map.object_parameter_value_list()
            query = query.filter(literal_column("object_class_name") == self.current_class_name)
            data = query.all()
            parameter_values = {(r.object_id, r.parameter_id): r.id for r in data}
            data = [[d.object_name, d.parameter_name, d.value]
                    for d in data if d.value is not None]
            index_names = [self.current_class_name]
            index_types = [str]
        index_names.extend([PARAMETER_NAME])
        index_types.extend([str])
        if self.current_value_type == DATA_JSON:
            data = unpack_json(data)
            index_names = index_names + [JSON_TIME_NAME]
            index_types = index_types + [int]
        return data, index_names, index_types, parameter_values

    def current_object_class_list(self):
        return self.relationship_classes[self.current_class_name].object_class_name_list.split(',')

    def get_set_data(self):
        if self.current_class_type == RELATIONSHIP_CLASS:
            data = [r.object_name_list.split(',') + ['x'] for r in self.relationships.values()]
            index_names = self.current_object_class_list()
            index_types = [str for _ in index_names]
        else:
            data = [[o.name, 'x'] for o in self.objects.values()
                    if o.class_id == self.object_classes[self.current_class_name].id]
            index_names = [self.current_class_name]
            index_types = [str]
        return data, index_names, index_types

    def update_class_list(self):
        """update list_select_class with all object classes and relationship classes"""
        oc = sorted(set([OBJECT_CLASS + ': ' + oc.name for oc in self.object_classes.values()]))
        rc = sorted(set([RELATIONSHIP_CLASS + ': ' + oc.name for oc in self.relationship_classes.values()]))
        self.ui.list_select_class.addItems(oc + rc)
        self.ui.list_select_class.setCurrentItem(self.ui.list_select_class.item(0))

    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes() and not self.model_has_changes():
            #self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    def commit_session(self, commit_msg):
        self.save_model()
        try:
            self.db_map.commit_session(commit_msg)
            #self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError:
            #self.msg_error.emit(e.msg)
            return

    def rollback_session(self):
        try:
            self.db_map.rollback_session()
            #self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError:
            #self.msg_error.emit(e.msg)
            return
        self.select_data()

    def model_has_changes(self):
        """checks if PivotModel has any changes"""
        if self.model.model._edit_data:
            return True
        if self.model.model._deleted_data:
            return True
        if any(len(v) > 0 for k, v in self.model.model._added_index_entries.items() if k not in [JSON_TIME_NAME]):
            return True
        if any(len(v) > 0 for k, v in self.model.model._deleted_index_entries.items() if k not in [JSON_TIME_NAME]):
            return True
        if any(len(v) > 0 for k, v in self.model.model._added_tuple_index_entries.items()):
            return True
        if any(len(v) > 0 for k, v in self.model.model._deleted_tuple_index_entries.items()):
            return True
        return False

    def change_frozen_value(self, newSelection):
        item = self.ui.table_frozen.get_selected_row()
        self.model.set_frozen_value(item)
        # update pivot history
        self.class_pivot_preferences[(self.current_class_name, self.current_class_type, self.current_value_type)] = self.PivotPreferences(self.model.model.pivot_rows, self.model.model.pivot_columns, self.model.model.pivot_frozen, self.model.model.frozen_value)

    def get_selected_class(self):
        if self.ui.list_select_class.currentItem():
            text = self.ui.list_select_class.currentItem().text()
            text = text.split(': ')
            return text[0], text[1]
        return None, None

    def pack_dict_json(self):
        """Pack down values with json_index into a json_array"""
        # TODO: can this be made a bit faster?
        # pack last index of dict to json
        if not self.model.model._edit_data and not self.model.model._deleted_data:
            return {}, set()
        # extract edited keys without time index
        edited_keys = set(k[:-1] for k in self.model.model._edit_data.keys())
        edited_keys.update(set(k[:-1] for k in self.model.model._deleted_data.keys()))
        # find data for edited keys.
        edited_data = {k:[] for k in edited_keys}
        for k in self.model.model._data:
            if k[:-1] in edited_data:
                edited_data[k[:-1]].append([k[-1] ,self.model.model._data[k]])
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
            for i in range(1,v[-1][0]+1):
                if v[v_ind][0] == i:
                    json_values.append(v[v_ind][1])
                    v_ind = v_ind + 1
                else:
                    json_values.append(0)
            packed_data[k] = json.dumps(json_values)

        return packed_data, empty_keys

    def delete_parameter_values(self, delete_values):
        delete_ids = set()
        update_data = []
        # index to object classes
        if self.current_class_type == RELATIONSHIP_CLASS:
            obj_ind = range(len(self.current_object_class_list()))
        else:
            obj_ind = [0]
        par_ind = len(obj_ind)
        index_ind = par_ind + 1
        for k in delete_values.keys():
            obj_id = tuple(self.objects[k[i]].id for i in obj_ind)
            if self.current_class_type == OBJECT_CLASS:
                obj_id = obj_id[0]
            else:
                obj_id = ",".join(map(str,obj_id))
            par_id = self.parameters[k[par_ind]].id
            index = k[index_ind]
            key = (obj_id, par_id, index)
            if key in self.parameter_values:
                if self.current_value_type == DATA_VALUE:
                    # only delete values where only one field is populated
                    delete_ids.add(self.parameter_values[key])
                else:
                    # remove value from parameter_value field but not entire row
                    update_data.append({"id": self.parameter_values[key], self.current_value_type: None})
        if delete_ids:
            self.db_map.remove_items(parameter_value_ids = delete_ids)
        if update_data:
            self.db_map.update_parameter_values(*update_data)

    def delete_relationships(self, delete_relationships):
        delete_ids = set()
        for del_rel in delete_relationships:
            if all(n in self.objects for n in del_rel):
                obj_ids = tuple(self.objects[n].id for n in del_rel)
                if obj_ids in self.relationships:
                    delete_ids.add(self.relationships[obj_ids].id)
                    self.relationships.pop(obj_ids)
        if delete_ids:
            self.db_map.remove_items(relationship_ids = delete_ids)

    def delete_index_values_from_db(self, delete_indexes):
        if not delete_indexes:
            return
        object_names = []
        parameter_names = []
        #TODO: identify parameter and index and json time dimensions some other way.
        for k, on in delete_indexes.items():
            if k == PARAMETER_NAME:
                parameter_names += on
            elif k not in [JSON_TIME_NAME]:
                object_names += on
        #find ids
        delete_obj_ids = set()
        for on in object_names:
            if on in self.objects:
                delete_obj_ids.add(self.objects[on].id)
                self.objects.pop(on)
        delete_par_ids = set()
        for pn in parameter_names:
            if pn in self.parameters:
                delete_par_ids.add(self.parameters[pn].id)
                self.parameters.pop(pn)
        if delete_obj_ids:
            self.db_map.remove_items(object_ids=delete_obj_ids)
        if delete_par_ids:
            self.db_map.remove_items(parameter_ids=delete_par_ids)


    def add_index_values_to_db(self, add_indexes):
        db_edited = False
        if not any(v for v in add_indexes.values()):
            return db_edited
        new_objects = []
        new_parameters = []
        #TODO: identify parameter and index and json time dimensions some other way.
        for k, on in add_indexes.items():
            if k == PARAMETER_NAME:
                if self.current_class_type == OBJECT_CLASS:
                    class_id = self.object_classes[self.current_class_name].id
                    new_parameters += [{"name": n, "object_class_id": class_id} for n in on]
                else:
                    new_parameters += [{"name": n, "relationship_class_id": self.relationship_classes[self.current_class_name].id} for n in on]
            elif k not in [JSON_TIME_NAME]:
                new_objects += [{"name": n, "class_id": self.object_classes[k].id} for n in on]
        if new_objects:
            self.db_map.add_objects(*new_objects)
            db_edited = True
        if new_parameters:
            self.db_map.add_parameter_definitions(*new_parameters)
            db_edited = True
        return db_edited

    def save_model_set(self):
        db_edited = False
        if self.current_class_type == RELATIONSHIP_CLASS:
            # find all objects and insert new into db for each class in relationship
            rel_getter = operator.itemgetter(*range(len(self.current_object_class_list())))
            add_relationships = set(rel_getter(index) for index, value in self.model.model._edit_data.items() if value is None)
            delete_relationships = set(rel_getter(index) for index, value in self.model.model._deleted_data.items())
            self.current_object_class_list()
            add_objects = []
            for i, name in enumerate(self.current_object_class_list()):
                #only keep objects that has a relationship
                new = self.model.model._added_index_entries[name]
                new_data_set = set(r[i] for r in add_relationships)
                new = [n for n in new if n in new_data_set]
                add_objects.extend([{'name': n, 'class_id': self.object_classes[name].id} for n in new])
            if add_objects:
                self.db_map.add_objects(*add_objects)
                self.load_objects()
            if delete_relationships:
                ids = [tuple(self.objects[i].id for i in rel) for rel in delete_relationships]
                delete_ids = set(self.relationships[r].id for r in ids if r in self.relationships)
                for r in delete_ids:
                    self.relationships.pop(r, None)
                if delete_ids:
                    self.db_map.remove_items(relationship_ids=delete_ids)
            if add_relationships:
                ids = [(tuple(self.objects[i].id for i in rel),'_'.join(rel))
                       for rel in delete_relationships]
                c_id = self.relationship_classes[self.current_class_name].id
                insert_rels = [{'object_id_list': r[0], 'name': r[1], 'class_id': c_id}
                               for r in ids if r not in self.relationships]
                if insert_rels:
                    self.db_map.add_wide_relationships(*insert_rels)
                    db_edited = True
        elif self.current_class_type == OBJECT_CLASS:
            # find removed and new objects, only keep indexes in data
            delete_objects = set(index[0] for index in self.model.model._deleted_data.keys())
            add_objects = set(index[0] for index, value in self.model.model._edit_data.items() if value is None)
            if delete_objects:
                delete_ids = set(self.objects[name].id for name in delete_objects)
                self.db_map.remove_items(object_ids=delete_ids)
                db_edited = True
            if add_objects:
                class_id = self.object_classes[self.current_class_name].id
                add_objects = [{"name": o, "class_id": class_id} for o in add_objects]
                self.db_map.add_objects(*add_objects)
                db_edited = True
        return db_edited

    def save_model(self):
        db_edited = False
        if self.current_value_type == DATA_SET:
            db_edited = self.save_model_set()
            delete_indexes = self.model.model._deleted_index_entries
            self.delete_index_values_from_db(delete_indexes)
        elif self.current_value_type in [DATA_JSON, DATA_VALUE]:
            # save new objects and parameters
            add_indexes = self.model.model._added_index_entries
            obj_edited = self.add_index_values_to_db(add_indexes)
            if obj_edited:
                self.parameters = {p.name: p for p in self.db_map.parameter_definition_list().all()}
                self.load_objects()

            if self.current_value_type == DATA_VALUE:
                delete_values = self.model.model._deleted_data
                data = self.model.model._edit_data
                data_value = self.model.model._data
            elif self.current_value_type == DATA_JSON:
                data_value, delete_values = self.pack_dict_json()
                delete_values = {k:None for k in delete_values}
                data = data_value
            # delete values
            self.delete_parameter_values(delete_values)

            if self.current_class_type == RELATIONSHIP_CLASS:
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

    def save_parameter_values(self, data, data_value):
        new_data = []
        update_data = []
        # index to object classes
        if self.current_class_type == RELATIONSHIP_CLASS:
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
            if self.current_class_type == RELATIONSHIP_CLASS:
                if obj_id in self.relationships:
                    db_id = self.relationships[obj_id].id
                obj_id = ",".join(map(str,obj_id))
            else:
                obj_id = obj_id[0]
                db_id = obj_id
            key = (obj_id, par_id)
            if key in self.parameter_values:
                value_id = self.parameter_values[key]
                update_data.append({"id": value_id, self.current_value_type: data_value[k]})
            elif db_id:
                new_data.append({id_field: db_id, "parameter_id": par_id,
                                 self.current_value_type: data_value[k]})
        if new_data:
            self.db_map.add_parameter_values(*new_data)
        if update_data:
            self.db_map.update_parameter_values(*update_data)

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
                        new_rels.append({'object_id_list': obj_ids, 'class_id': self.relationship_classes[self.current_class_name].id, 'name': '_'.join(rel)})
        # save relationships
        if new_rels:
            self.db_map.add_wide_relationships(*new_rels)
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
            self.ui.table_frozen.selectionModel().blockSignals(True) #prevent selectionChanged signal when updating
            self.ui.table_frozen.selectRow(ind)
            self.ui.table_frozen.selectionModel().blockSignals(False)
        else:
            # frozen value not found, remove selection
            self.ui.table_frozen.selectionModel().blockSignals(True) #prevent selectionChanged signal when updating
            self.ui.table_frozen.clearSelection()
            self.ui.table_frozen.selectionModel().blockSignals(False)

    def change_class(self):
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
            rows = [n for n in index_names if n not in [PARAMETER_NAME]]
            columns = [PARAMETER_NAME] if PARAMETER_NAME in index_names else []
            frozen = []
            frozen_value = ()
        return rows, columns, frozen, frozen_value

    def get_valid_entries_dicts(self):
        tuple_entries = {}
        used_index_entries = {}
        valid_index_values = {JSON_TIME_NAME: range(1,9999999)}
        #used_index_entries[(PARAMETER_NAME,)] = set(p.name for p in self.parameters.values())
        index_entries = {}
        if self.current_class_type == RELATIONSHIP_CLASS:
            object_class_names = tuple(self.relationship_classes[self.current_class_name].object_class_name_list.split(','))
            #used_index_entries[object_class_names] = set(o.name for o in self.objects.values())
            index_entries[PARAMETER_NAME] = set(p.name for p in self.parameters.values() if p.relationship_class_id == self.relationship_classes[self.current_class_name].id)
            tuple_entries[(PARAMETER_NAME,)] = set((i,) for i in index_entries[PARAMETER_NAME])
            for oc in object_class_names:
                index_entries[oc] = set(o.name for o in self.objects.values() if o.class_id == self.object_classes[oc].id)
            unique_class_names = list(object_class_names)
            fix_name_ambiguity(unique_class_names)
            tuple_entries[tuple(unique_class_names)] = set(tuple(r.object_name_list.split(',')) for r in self.relationships.values())
        else:
            #used_index_entries[(self.current_class_name,)] = set(o.name for o in self.objects.values())
            index_entries[self.current_class_name] = set(o.name for o in self.objects.values() if o.class_id == self.object_classes[self.current_class_name].id)
            index_entries[PARAMETER_NAME] = set(p.name for p in self.parameters.values() if p.object_class_id == self.object_classes[self.current_class_name].id)
            tuple_entries[(PARAMETER_NAME,)] = set((i,) for i in index_entries[PARAMETER_NAME])
            tuple_entries[(self.current_class_name,)] = set((i,) for i in index_entries[self.current_class_name])

        return index_entries, tuple_entries, valid_index_values, used_index_entries

    def select_data(self, text = ""):
        class_type, class_name = self.get_selected_class()
        self.current_class_type = class_type
        self.current_class_name = class_name
        self.current_value_type = self.ui.comboBox_value_type.currentText()
        self.load_relationships()
        index_entries, tuple_entries, valid_index_values, used_index_entries = self.get_valid_entries_dicts()
        if self.current_value_type == DATA_SET:
            data, index_names, index_types = self.get_set_data()
            tuple_entries = {}
            valid_index_values = {}
            index_entries.pop(PARAMETER_NAME, None)
        else:
            data, index_names, index_types, parameter_values = self.load_parameter_values()
            self.parameter_values = parameter_values

        # make names unique
        real_names = index_names
        unique_names = list(index_names)
        fix_name_ambiguity(unique_names)
        self.original_index_names = {u: r for u, r in zip(unique_names, real_names)}
        if self.current_class_type == RELATIONSHIP_CLASS:
            self.relationship_tuple_key = tuple(unique_names[:len(self.current_object_class_list())])
        # get pivot preference for current selection
        selection_key = (self.current_class_name, self.current_class_type, self.current_value_type)
        rows, columns, frozen, frozen_value = self.get_pivot_preferences(selection_key, unique_names)
        # update model and views
        self.model.set_data(data, unique_names, index_types, rows, columns,
                            frozen, frozen_value, index_entries, valid_index_values, tuple_entries, used_index_entries, real_names)
        self.proxy_model.clear_filter()
        self.update_filters_to_new_model()
        self.update_pivot_lists_to_new_model()
        self.update_frozen_table_to_model()

    def table_index_entries_changed(self, added_entries, deleted_enties):
        for button, menu in zip(self.filter_buttons, self.filter_menus):
            name = button.text()
            if name in deleted_enties:
                menu.remove_items_from_filter_list(deleted_enties[name])
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
        self.class_pivot_preferences[(self.current_class_name, self.current_class_type, self.current_value_type)] = self.PivotPreferences(index, columns, frozen, frozen_value)

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

    def show_commit_session_prompt(self):
        """Shows the commit session message box."""
        qsettings = self._data_store._toolbox.qsettings()
        commit_at_exit = int(qsettings.value("appSettings/commitAtExit", defaultValue="1"))
        if commit_at_exit == 0:
            # Don't commit session and don't show message box
            return
        elif commit_at_exit == 1:  # Default
            # Show message box
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Commit pending changes")
            msg.setText("The current session has uncommitted changes. Do you want to commit them now?")
            msg.setInformativeText("WARNING: If you choose not to commit, all changes will be lost.")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            chk = chkbox.checkState()
            if answer == QMessageBox.Yes:
                self.show_commit_session_dialog()
                if chk == 2:
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "2")
            else:
                if chk == 2:
                    # Save preference
                    qsettings.setValue("appSettings/commitAtExit", "0")
        elif commit_at_exit == 2:
            # Commit session and don't show message box
            self.show_commit_session_dialog()
        else:
            qsettings.setValue("appSettings/commitAtExit", "1")
        return

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
        #restore splitters
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
        self.qsettings.setValue("{}/windowMaximized".format(self.settings_key), self.windowState() == Qt.WindowMaximized)
        self.qsettings.setValue(
            "{}/splitterSelectTable".format(self.settings_key),
            self.ui.splitter_3.saveState())
        self.qsettings.setValue(
            "{}/splitterTableFilter".format(self.settings_key),
            self.ui.splitter_2.saveState())
        self.qsettings.setValue(
            "{}/splitterPivotFrozen".format(self.settings_key),
            self.ui.splitter.saveState())

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # show commit dialog if pending changes
        if self.db_map.has_pending_changes() or self.model_has_changes():
            self.show_commit_session_prompt()
        # save ui state
        self.save_ui()
        if event:
            event.accept()
