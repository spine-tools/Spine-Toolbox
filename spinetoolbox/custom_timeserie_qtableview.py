#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Spine Toolbox grid view

:author: P. Vennström (VTT)
:date:   1.11.2018
"""

from PySide2.QtWidgets import QApplication, QTableView, QVBoxLayout, \
    QComboBox, QListWidget, QAbstractItemView, QLabel, QMenu, QMainWindow, QDialog
from PySide2.QtCore import Qt, QModelIndex, Signal, QItemSelectionModel, Slot, \
    QPoint, QAbstractItemModel
from PySide2.QtGui import QStandardItemModel, QKeySequence, QDropEvent
from ui.tabular_view_form import Ui_MainWindow

from tabularview_models import PivotTableSortFilterProxy, PivotTableModel
from spinedatabase_api import DiffDatabaseMapping, SpineDBAPIError 
import json
import operator
from collections import namedtuple
from sqlalchemy.sql import literal_column

# TODO: connect to all add, delete relationship/object classes widgets to this.
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog

# constant strings
RELATIONSHIP_CLASS = "relationship"
OBJECT_CLASS = "object"

DATA_JSON = "json"
DATA_VALUE = "value"
DATA_SET = "set"

INDEX_NAME = "db index"
JSON_TIME_NAME = "json time"
PARAMETER_NAME = "db parameter"

# TODO: move to helper file
def tuple_itemgetter(itemgetter_func, num_indexes):
    """Change output of itemgetter to always be a tuple even for one index"""
    if num_indexes == 1:
        def g(item):
            return (itemgetter_func(item),)
        return g
    else:
        return itemgetter_func


def get_relationshipclass_json(db_map, name, field):
    # get parameter data
    query = db_map.relationship_parameter_value_list()
    query = query.filter(literal_column("relationship_class_name") == name)
    
    data = query.all()
    data_dict = {(r.object_id_list, r.parameter_id, r.index): r.id for r in data}
    if field == DATA_JSON:
        data = [[d.object_name_list, d.parameter_name, d.index, d.json] for d in data if d.json]
        data = unpack_json(data)
        labels = [PARAMETER_NAME, INDEX_NAME, JSON_TIME_NAME]
        label_types = [str, int, int]
    elif  field == DATA_VALUE:
        data = query.all()
        
        data = [[d.object_name_list, d.parameter_name, d.index, d.value] for d in data if d.value]
        labels = [PARAMETER_NAME, INDEX_NAME]
        label_types = [str, int]
    data = [d[0].split(",") + d[1:] for d in data]
    
    rel_class = db_map.relationship_class_list().\
        add_column(db_map.ObjectClass.name.label('object_class_name')).\
        filter(db_map.ObjectClass.id == db_map.RelationshipClass.object_class_id,
               db_map.RelationshipClass.name == name).\
        order_by(db_map.RelationshipClass.dimension).all()
    obj_class_names = [x.object_class_name for x in rel_class]
    org_names = [x.object_class_name for x in rel_class]
    obj_class_names = make_names_unique(obj_class_names)
    org_names = {new_name: org_name for new_name, org_name in zip(obj_class_names, org_names)}
    index_types = [str for _ in range(len(obj_class_names))]
    index_types = index_types + label_types
    index_names = obj_class_names + labels

    return data, index_names, index_types, data_dict, org_names


def unpack_json(data):
    expanded_data = []
    for d in data:
        json_array = json.loads(d[-1])
        json_index = list(range(1, len(json_array) + 1))
        new_data = [a + [b, c] for a, b, c in zip([d[:-1]]*len(json_array), json_index, json_array)]
        expanded_data = expanded_data + new_data
    return expanded_data


def get_object_class_parameter_values(db_map, class_name, field):
    query = db_map.parameter_value_list().\
        add_column(db_map.Parameter.name.label("parameter_name")).\
        add_column(db_map.ObjectClass.name.label("object_class_name")).\
        add_column(db_map.Object.name.label("object_name")).\
        join(db_map.Parameter, db_map.ObjectClass).\
        filter(db_map.ParameterValue.object_id != None,
               db_map.ParameterValue.object_id == db_map.Object.id,
               db_map.ObjectClass.name == class_name)
    data = []
    if field == DATA_VALUE:
        data = query.filter(db_map.ParameterValue.value != None).all()
        index_names = [class_name, PARAMETER_NAME, INDEX_NAME]
        index_types = [str, str, int]
        data_dict = {(d.object_id, d.parameter_id, d.index): d.id for d in data}
        data = [[d.object_name, d.parameter_name, d.index, d.value] for d in data if d.value]
    elif field == DATA_JSON:
        data = query.filter(db_map.ParameterValue.json != None).all()
        index_names = [class_name, PARAMETER_NAME, INDEX_NAME, JSON_TIME_NAME]
        index_types = [str, str, int, int]
        data_dict = {(d.object_id, d.parameter_id, d.index): d.id for d in data}
        data = [[d.object_name, d.parameter_name, d.index, d.json] for d in data if d.json]
        data = unpack_json(data)
    return data, index_names, index_types, data_dict

# TODO: change use of this function to existing in helpers or move to helpers
def make_names_unique(names):
    # appends number after repeted string in list
    name_dict = {}
    unique_names = []
    for n in names:
        if n in name_dict.keys():
            new_n = n + str(name_dict[n])
            name_dict[n] = name_dict[n] + 1
        else:
            name_dict[n] = 1
            new_n = n
        unique_names.append(new_n)
    return unique_names

# TODO: this is abit hacky, change to something else
class CheckableComboBox(QComboBox):
    listClosed = Signal(object)
    def __init__(self):
        super(CheckableComboBox, self).__init__()
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))
        self._changed = False
        self.column = ""
        
    def all_selected(self):
        return self.model().itemFromIndex(self.model().index(0, 0)).checkState() == Qt.Checked
    
    def set_state_all(self, state = Qt.Checked):
        for i in range(self.count()):
            self.model().itemFromIndex(self.model().index(i, 0)).setCheckState(state)

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if index.row() == 0:
            # select all is pressed
            self.handleSelectAllPressed()
            self._changed = True
            return
        
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
            # set "select all" to unchecked since atleast one is unchecked
            self.model().itemFromIndex(self.model().index(0, 0)).setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        self._changed = True
        
    def handleSelectAllPressed(self):
        if self.all_selected():
            set_all = Qt.Unchecked
        else:
            set_all = Qt.Checked
        self.set_state_all(set_all)
    
    def hidePopup(self):
        if not self._changed:
            super(CheckableComboBox, self).hidePopup()
            self.listClosed.emit(self)
        self._changed = False
        
    def add_items(self, inputList):
        count_before = self.count()
        for i, list_item in enumerate(inputList):
            self.addItem(str(list_item))
            item = self.model().item(i + count_before, 0)
            item.setCheckState(Qt.Checked)
            item.setData(list_item, Qt.UserRole)
    
    def setItemList(self, inputList):
        inputList = ["(select all)", None] + sorted(inputList)
        self.clear()
        self._not_checked = set()
        for (i, list_item) in enumerate(inputList):
            if list_item == None:
                self.addItem("(empty)")
            else:    
                self.addItem(str(list_item))
            item = self.model().item(i, 0)
            item.setCheckState(Qt.Checked)
            item.setData(list_item, Qt.UserRole)

# TODO: rename this class to something better
class TestListView(QListWidget):
    afterDrop = Signal(object, QDropEvent)
    allowedDragLists = []
    
    def __init__(self, parent=None):
        super(TestListView, self).__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropOverwriteMode(False)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        if event.source() == self or event.source() in self.allowedDragLists:
            event.accept()

    def dropEvent(self, event):
        if event.source() == self or event.source() in self.allowedDragLists:
            super(TestListView, self).dropEvent(event)
            self.afterDrop.emit(self, event)


class TableModel(QAbstractItemModel):
    def __init__(self, headers = [], data = []):
    # def __init__(self, tasks=[[]]):
        super(TableModel, self).__init__()
        self._data = data
        self._headers = headers
    
    def parent(self, child = QModelIndex()):
        return QModelIndex()

    def index(self, row, column, parent = QModelIndex()):
        return self.createIndex(row, column, parent)
    
    def set_data(self, data, headers):
        if data and len(data[0]) != len(headers):
            raise ValueError("'data[0]' must be same length as 'headers'")
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
        top_left = self.index(0, 0)
        bottom_right = self.index(self.rowCount(), self.columnCount())
        self.dataChanged.emit(top_left, bottom_right)

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        return len(self._headers)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self._headers[section]

    def row(self, index):
        if index.isValid():
            return self._data[index.row()]

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]


class FrozenTableView(QTableView):
    def __init__(self, parent=None):
        super(FrozenTableView, self).__init__(parent)
        self.model = TableModel()
        self.setSelectionBehavior(QAbstractItemView.SelectRows);
        self.setSelectionMode(QAbstractItemView.SingleSelection);
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)
        self.setModel(self.model)
        self.is_updating = False

    def clear(self):
        self.model.set_data([], [])
    
    def get_selected_row(self):
        if self.model.columnCount() == 0:
            return ()
        if self.model.rowCount() == 0:
            return tuple(None for _ in range(self.model.columnCount()))
        index = self.selectedIndexes()
        if not index:
            return tuple(None for _ in range(self.model.columnCount()))
        else:
            index = self.selectedIndexes()[0]
            return self.model.row(index)
    
    def set_data(self, headers, values):
        self.selectionModel().blockSignals(True) #prevent selectionChanged signal when updating
        self.model.set_data(values, headers)
        self.selectRow(0)
        self.selectionModel().blockSignals(False)


class CustomQTableView(QTableView):
    """Custom QTableView class with copy-paste functionality.

    Attributes:
        parent (QWidget): The parent of this view
    """

    def __init__(self, parent = None):
        """Initialize the class."""
        super().__init__(parent)
        # self.editing = False
        self.clipboard = QApplication.clipboard()
        self.clipboard_text = self.clipboard.text()
        self.clipboard.dataChanged.connect(self.clipboard_data_changed)

    @Slot(name="clipboard_data_changed")
    def clipboard_data_changed(self):
        self.clipboard_text = self.clipboard.text()

    def keyPressEvent(self, event):
        """Copy and paste to and from clipboard in Excel-like format."""
        if event.matches(QKeySequence.Copy):
            selection = self.selectionModel().selection()
            if not selection:
                super().keyPressEvent(event)
                return
            # Take only the first selection in case of multiple selection.
            first = selection.first()
            content = ""
            v_header = self.verticalHeader()
            h_header = self.horizontalHeader()
            for i in range(first.top(), first.bottom()+1):
                if v_header.isSectionHidden(i):
                    continue
                row = list()
                for j in range(first.left(), first.right()+1):
                    if h_header.isSectionHidden(j):
                        continue
                    row.append(str(self.model().index(i, j).data(Qt.DisplayRole)))
                content += "\t".join(row)
                content += "\n"
            self.clipboard.setText(content)
        elif event.matches(QKeySequence.Paste):
            if not self.clipboard_text:
                super().keyPressEvent(event)
                return
            top_left_index = self.currentIndex()
            if not top_left_index.isValid():
                super().keyPressEvent(event)
                return
            data = [line.split('\t') for line in self.clipboard_text.split('\n')[0:-1]]
            self.selectionModel().select(top_left_index, QItemSelectionModel.Select)
            self.model().paste_data(top_left_index, data)
        else:
            super().keyPressEvent(event)

class TabularViewForm(QMainWindow):
    """A widget to show and edit Spine objects in a data store.

    Attributes:
        data_store (DataStore): The DataStore instance that owns this form
        db_map (DatabaseMapping): The object relational database mapping
        database (str): The database name
    """

    def __init__(self):
        super().__init__(flags=Qt.Window)
        # TODO: the filter comboboxes are hacked togheter, might not work on all OS:s, build a panel with list that pops up instead.
        # TODO: change the list_select_class to something nicer
        # TODO: Maybe set the parent as ToolboxUI so that its stylesheet is inherited. This may need
        # reimplementing the window minimizing and maximizing actions as well as setting the window modality
        # NOTE: Alternatively, make this class inherit from QWidget rather than QMainWindow,
        # and implement the menubar by hand
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #self.ui.setupUi(self)
        
        self.db_map = DiffDatabaseMapping("sqlite:///C:/repos/spinetoolbox/projects/hydro_test/data/hydro.sqlite", "test")
        self.database = 'hydro.sqlite'
        
        # current state of ui
        self.current_class_type = ''
        self.current_class_name = ''
        self.current_value_type = ''
        self.relationships = []
        self.relationship_class = []
        self.object_classes = []
        self.objects = []
        self.parameters = []
        self.relationship_tuple_key = None
        self.original_index_names = {}
        self.filter = []
        
        # history of selected pivot
        self.class_pivot_preferences = {}
        self.PivotPreferences = namedtuple("PivotPreferences", ["index", "columns", "frozen", "frozen_value"])

        self.update_class_list()
        self.ui.comboBox_value_type.addItems([DATA_VALUE, DATA_JSON, DATA_SET])

        # set allowed drop for pivot index lists
        self.ui.list_index.allowedDragLists = [self.ui.list_column,self.ui.list_frozen]
        self.ui.list_column.allowedDragLists = [self.ui.list_index,self.ui.list_frozen]
        self.ui.list_frozen.allowedDragLists = [self.ui.list_index,self.ui.list_column]

        # pivot model and filterproxy
        self.proxy_model = PivotTableSortFilterProxy()
        self.model = PivotTableModel([], ["temp"], [str])
        self.proxy_model.setSourceModel(self.model)
        self.ui.pivot_table.setModel(self.proxy_model)

        # context menu for pivot_table
        self.rcMenu=QMenu(self.ui.pivot_table)
        delete_row = self.rcMenu.addAction('Delete rows')
        delete_col = self.rcMenu.addAction('Delete columns')
        self.delete_index_action = self.rcMenu.addAction('Delete columns')
        self.delete_relationship_action = self.rcMenu.addAction('Delete relationships')
        self.ui.pivot_table.setContextMenuPolicy(Qt.CustomContextMenu)
        
        # connect signals
        self.ui.pivot_table.customContextMenuRequested.connect(self.onRightClick)
        delete_row.triggered.connect(self.delete_row)
        delete_col.triggered.connect(self.delete_col)
        self.delete_index_action.triggered.connect(self.delete_index_values)
        self.delete_relationship_action.triggered.connect(self.delete_relationship_values)
        self.ui.list_index.afterDrop.connect(self.change_pivot)
        self.ui.list_column.afterDrop.connect(self.change_pivot)
        self.ui.list_frozen.afterDrop.connect(self.change_pivot)
        self.model.indexEntriesChanged.connect(self.table_index_entries_changed)
        self.ui.table_frozen.selectionModel().selectionChanged.connect(self.change_frozen_value)
        self.ui.comboBox_value_type.currentTextChanged.connect(self.select_data)
        self.ui.list_select_class.itemClicked.connect(self.change_class)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        
        # update models to data
        self.select_data()
    
    def update_class_list(self):
        """update list_select_class with all object classes and relationship classes""" 
        oc = sorted(set([OBJECT_CLASS + ': ' + oc.name for oc in self.db_map.object_class_list().all()]))
        rc = sorted(set([RELATIONSHIP_CLASS + ': ' + oc.name for oc in self.db_map.wide_relationship_class_list().all()]))
        self.ui.list_select_class.addItems(oc + rc)
        self.ui.list_select_class.setCurrentItem(self.ui.list_select_class.item(0))
    
    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes():
            self.msg.emit("Nothing to commit yet.")
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
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
    
    def rollback_session(self):
        try:
            self.db_map.rollback_session()
            #self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        self.select_data()
    
    def change_frozen_value(self, newSelection):
        item = self.ui.table_frozen.get_selected_row()
        self.model.set_frozen_value(item)
        # update pivot history
        self.class_pivot_preferences[(self.current_class_name, self.current_class_type, self.current_value_type)] = self.PivotPreferences(self.model.pivot_index, self.model.pivot_columns, self.model.pivot_frozen, self.model.frozen_value)

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
        if not self.model._edit_data and not self.model._data_deleted:
            return {}, set()
        # extract edited keys without time index
        edited_keys = set(k[:-1] for k in self.model._edit_data)
        edited_keys.update(set(k[:-1] for k in self.model._data_deleted))
        # find data for edited keys.
        edited_data = {k:[] for k in edited_keys}
        for k in self.model._data:
            if k[:-1] in edited_data:
                edited_data[k[:-1]].append([k[-1] ,self.model._data[k]])
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

    def delete_object_parameter_values(self, delete_values):
        if not delete_values:
            return
        delete_ids = set()
        for k in delete_values:
            if k[0] in self.objects and k[1] in self.parameters:
                obj_id = self.objects[k[0]].id
                par_id = self.parameters[k[1]].id
                index = k[2]
                key = (obj_id, par_id, index)
                if key in self.parameter_values:
                    delete_ids.add(self.parameter_values[key])
                    self.parameter_values.pop(key, None)
        if delete_ids:
            self.db_map.remove_items(parameter_value_ids = delete_ids)
    
    def delete_relationship_parameter_values(self, delete_values):
        if not delete_values:
            return
        num_classes = len(self.relationship_class)
        delete_ids = set()
        for k in delete_values:
            if all(k[i] in self.objects for i in range(num_classes)) and k[num_classes] in self.parameters:
                obj_ids = tuple(self.objects[k[i]].id for i in range(num_classes))
                obj_ids = ",".join(map(str,obj_ids))
                par_id = self.parameters[k[num_classes]].id
                index = k[num_classes+1]
                key = (obj_ids, par_id, index)
                if key in self.parameter_values:
                    delete_ids.add(self.parameter_values[key])
                    self.parameter_values.pop(key, None)
        if delete_ids:
            self.db_map.remove_items(parameter_value_ids = delete_ids)

    def delete_relationships(self):
        if not self.relationship_tuple_key in self.model.deleted_tuple_index_entries:
            return
        delete_ids = set()
        for del_rel in self.model.deleted_tuple_index_entries[self.relationship_tuple_key]:
            if all(n in self.objects for n in del_rel):
                obj_ids = tuple(self.objects[n].id for n in del_rel)
                if obj_ids in self.relationships:
                    delete_ids.add(self.relationships[obj_ids].id)
                    self.relationships.pop(obj_ids, None)
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
            elif k not in [INDEX_NAME, JSON_TIME_NAME]:
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
        if not add_indexes:
            return
        class_type = self.current_class_type
        new_objects = []
        new_parameters = []
        #TODO: identify parameter and index and json time dimensions some other way.
        for k, on in add_indexes.items():
            if len(k) != 1:
                continue
            k = k[0]
            if k == PARAMETER_NAME:
                if class_type == OBJECT_CLASS:
                    class_id = next(iter(self.object_classes.values())).id
                    new_parameters += [{"name": n[0], "object_class_id": class_id} for n in on]
                else:
                    new_parameters += [{"name": n[0], "relationship_class_id": self.relationship_class[0].id} for n in on]
            elif k not in [INDEX_NAME, JSON_TIME_NAME]:
                new_objects += [{"name": n[0], "class_id": self.object_classes[self.original_index_names[k]].id} for n in on]
        if new_objects:
            new_objects = self.db_map.add_objects(*new_objects)
            new_objects = {o.name: o for o in new_objects}
            self.objects = {**self.objects, **new_objects}
        if new_parameters:
            new_parameters = self.db_map.add_parameters(*new_parameters)
            new_parameters = {o.name: o for o in new_parameters}
            self.parameters = {**self.parameters, **new_parameters}

    def save_model_set(self):
        class_type = self.current_class_type
        if class_type == RELATIONSHIP_CLASS:
            data_relationships = set(self.model._data.keys())
            # find all objects and insert new into db for each class in relationship
            add_objects = []
            for i, rc in enumerate(self.relationship_class):
                db_objects = set(o.name for o in self.objects.values() if o.class_id == rc.object_class_id)
                data_objects = set(objects[i] for objects in data_relationships)
                add = data_objects.difference(db_objects)
                add_objects = add_objects + [{"name": o, "class_id": rc.object_class_id} for o in add]
            if add_objects:
                new_objects = self.db_map.add_objects(*add_objects)
                new_objects = {o.name: o for o in new_objects}
                self.objects = {**self.objects, **new_objects}
            data_relationships = {tuple(self.objects[o].id for o in objects): objects for objects in data_relationships}
            db_relationships = set(self.relationships.keys())
            delete_relationships = db_relationships.difference(set(data_relationships.keys()))
            add_relationships = set(data_relationships.keys()).difference(db_relationships)
            if delete_relationships:
                delete_ids = set(self.relationships[r].id for r in delete_relationships)
                for r in delete_relationships:
                    self.relationships.pop(r, None)
                self.db_map.remove_items(relationship_ids=delete_ids)
            if add_relationships:
                insert_rels = []
                for ids in add_relationships:
                    name = '_'.join(data_relationships[ids])
                    insert_rels.append({'object_id_list': ids, 'name': name, 'class_id': self.relationship_class[0].id})
                new_rels = self.db_map.add_wide_relationships(*insert_rels)
                new_rels = {tuple(int(i) for i in r.object_id_list.split(",")): r for r in new_rels.all()}
                self.relationships = {**self.relationships, **new_rels}
            
        elif class_type == OBJECT_CLASS:
            # find removed and new objects
            data_objects = set(o[0] for o in self.model._data.keys())
            db_objects = set(self.objects.keys())
            delete_objects = db_objects.difference(data_objects)
            add_objects = data_objects.difference(db_objects)
            if delete_objects:
                delete_ids = set(self.objects[name].id for name in delete_objects)
                for o in delete_objects:
                    self.objects.pop(o, None)
                self.db_map.remove_items(object_ids=delete_ids)
            if add_objects:
                class_id = next(iter(self.object_classes.values())).id
                add_objects = [{"name": o, "class_id": class_id} for o in add_objects]
                new_objects = self.db_map.add_objects(*add_objects)
                new_objects = {o.name: o for o in new_objects}
                self.objects = {**self.objects, **new_objects}
        self.model._edit_data = {}

    def save_model(self):
        parameter_type = self.current_value_type
        class_type = self.current_class_type
        if parameter_type == DATA_SET:
            self.save_model_set()
            return
        # delete and add new index values
        delete_indexes = self.model.deleted_index_entries
        add_indexes = self.model.added_tuple_index_entries
        self.delete_index_values_from_db(delete_indexes)
        self.add_index_values_to_db(add_indexes)
        # get data from model
        if parameter_type == DATA_VALUE:
            delete_values = self.model._data_deleted
            data = self.model._edit_data
            data_value = self.model._data
        elif parameter_type == DATA_JSON:
            data_value, delete_values = self.pack_dict_json()
            data = data_value
        #save and delete values
        if class_type == OBJECT_CLASS:
            self.delete_object_parameter_values(delete_values)
            self.save_object_parameter_values( data, data_value, parameter_type)
        else:
            self.delete_relationships()
            self.delete_relationship_parameter_values(delete_values)
            self.save_relationships()
            self.save_relationship_parameter_values(data, data_value, parameter_type)
        #update model
        self.model._edit_data = {}
        self.model._data_deleted = set()

    def save_object_parameter_values(self, data, data_value, parameter_type):
        new_data = []
        update_data = []
        # edited data, updated and new
        for k in data.keys():
            obj_id = self.objects[k[0]].id
            par_id = self.parameters[k[1]].id
            index = k[2]
            key = (obj_id, par_id, index)
            if key in self.parameter_values:
                value_id = self.parameter_values[key]
                update_data.append({"id": value_id, parameter_type: data_value[k]})
            else:
                new_data.append({"object_id": obj_id,"parameter_id": par_id, parameter_type: data_value[k]})
        if new_data:
            new_parameter_values = self.db_map.add_parameter_values(*new_data)
            new_parameter_values = {(d.object_id, d.parameter_id, d.index): d.id for d in new_parameter_values}
            self.parameter_values = {**self.parameter_values, **new_parameter_values}
        if update_data:
            self.db_map.update_parameter_values(*update_data)

    def save_relationships(self):
        new_rels = []
        added_rels = set()
        if self.relationship_tuple_key in self.model.added_tuple_index_entries:
            # relationships added by tuple
            rels = self.model.added_tuple_index_entries[self.relationship_tuple_key]
            for rel in rels:
                if all(n in self.objects for n in rel):
                    obj_ids = tuple(self.objects[n].id for n in rel)
                    if obj_ids not in self.relationships:
                        added_rels.add(obj_ids)
                        new_rels.append({'object_id_list': obj_ids, 'class_id': self.relationship_class[0].id, 'name': '_'.join(rel)})
        # relationships added by data
        indexes = tuple(self.model._index_ind[n] for n in self.relationship_tuple_key)
        getter = tuple_itemgetter(operator.itemgetter(*indexes), len(indexes))
        for keys in self.model._edit_data.keys():
            rel = getter(keys)
            if all(n in self.objects for n in rel):
                obj_ids = tuple(self.objects[n].id for n in rel)
                if obj_ids not in added_rels and obj_ids not in self.relationships:
                    new_rels.append({'object_id_list': obj_ids, 'class_id': self.relationship_class[0].id, 'name': '_'.join(rel)})
        # save relationships
        if new_rels:
            new_rels = self.db_map.add_wide_relationships(*new_rels)
            new_rels = {tuple(int(i) for i in r.object_id_list.split(",")): r for r in new_rels.all()}
            self.relationships = {**self.relationships, **new_rels}

    def save_relationship_parameter_values(self, data, data_value, parameter_type):
        num_classes = len(self.relationship_class)
        new_data = []
        update_data = []
        rel_id_dict = {}
        # edited data, updated and new
        for k in data.keys():
            if all(k[i] in self.objects for i in range(num_classes)):
                obj_ids = tuple(self.objects[k[i]].id for i in range(num_classes))
                par_id = self.parameters[k[num_classes]].id
                index = k[num_classes+1]
                key = (",".join(map(str,obj_ids)), par_id, index)
                if obj_ids in self.relationships:
                    rel_id = self.relationships[obj_ids].id
                    rel_id_dict[rel_id] = ",".join(map(str,obj_ids))
                    if key in self.parameter_values:
                        value_id = self.parameter_values[key]
                        update_data.append({"id": value_id, parameter_type: data_value[k]})
                    else:
                        new_data.append({"relationship_id": rel_id,"parameter_id": par_id, parameter_type: data_value[k]})
        if new_data:
            new_parameter_values = self.db_map.add_parameter_values(*new_data)
            new_parameter_values = {(rel_id_dict[r.relationship_id], r.parameter_id, r.index): r.id for r in new_parameter_values}
            self.parameter_values = {**self.parameter_values, **new_parameter_values}
        if update_data:
            self.db_map.update_parameter_values(*update_data)

    def update_filters_to_new_model(self):
        new_names = list(self.model.index_entries)
        for i, name in enumerate(new_names):
            if i < len(self.filter):
                # filter exists, update
                cblist = self.filter[i]
                cblist[1].setText(name + ':')
                cblist[0].column = name
            else:
                # doesn't exist, create new
                cblist = self.create_filter_combobox(name)
                self.filter.append(cblist)
                self.ui.h_layout_filter.addLayout(cblist[2])
            # update items in combobox
            cblist[0].setItemList(self.model.index_entries[name])
        # delete unused filters
        for i in reversed(range(len(new_names), max(len(new_names), len(self.filter)))):
            cblist = self.filter.pop(i)
            self.ui.h_layout_filter.removeItem(cblist[2])
            cblist[2].removeWidget(cblist[0])
            cblist[2].removeWidget(cblist[1])
            cblist[0].deleteLater()
            cblist[1].deleteLater()
            cblist[2].deleteLater()

    def update_pivot_lists_to_new_model(self):
        self.ui.list_index.clear()
        self.ui.list_column.clear()
        self.ui.list_frozen.clear()
        self.ui.list_index.addItems(self.model.pivot_index)
        self.ui.list_column.addItems(self.model.pivot_columns)
        self.ui.list_frozen.addItems(self.model.pivot_frozen)
    
    def update_frozen_table_to_model(self):
        frozen = self.model.pivot_frozen
        frozen_values = self.find_frozen_values(frozen)
        frozen_value = self.model.frozen_value
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

    def select_data(self, text = ""):
        class_type, class_name = self.get_selected_class()
        self.current_class_type = class_type
        self.current_class_name = class_name
        self.current_value_type = self.ui.comboBox_value_type.currentText()
        if not class_type or not class_name or not self.current_value_type:
            return
        valid_index_values = {}
        valid_index_values[INDEX_NAME] = range(1,9999999)
        valid_index_values[JSON_TIME_NAME] = range(1,9999999)
        tuple_entries = {}
        self.original_index_names = {}
        self.relationship_tuple_key = None
        if class_type == OBJECT_CLASS:
            # get object class data
            self.relationship_class = None
            self.relationships = None
            oc = self.db_map.single_object_class(name = class_name).first()
            self.object_classes = {oc.name: oc}
            self.objects = {o.name: o for o in self.db_map.object_list(class_id = oc.id).all()}
            if self.current_value_type == DATA_SET:
                index_names = [class_name]
                index_types = [str]
                data = [[o.name, 'x'] for o in self.objects.values()]
                data_dict = {}
                self.parameters = {}
            else:
                self.parameters = {p.name: p for p in self.db_map.parameter_list(object_class_id = oc.id).all()}
                tuple_entries[(class_name,)] = set((o.name,) for o in self.objects.values())
                tuple_entries[(PARAMETER_NAME,)] = set((p.name,) for p in self.parameters.values())
                data, index_names, index_types, data_dict = get_object_class_parameter_values(self.db_map, class_name, self.current_value_type)
            self.original_index_names = {n: n for n in index_names}
        elif class_type == RELATIONSHIP_CLASS:
            # get relationship class data
            self.relationship_class = self.db_map.relationship_class_list().filter(self.db_map.RelationshipClass.name == class_name).order_by(self.db_map.RelationshipClass.dimension).all()
            self.relationships = {tuple(int(i) for i in r.object_id_list.split(",")): r for r in self.db_map.wide_relationship_list(class_id = self.relationship_class[0].id).all()}
            self.object_classes = {oc.name: oc for oc in self.db_map.object_class_list().filter(self.db_map.ObjectClass.id.in_(r.object_class_id for r in self.relationship_class)).all()}
            if self.current_value_type == DATA_SET:
                oc_id_2_name = {oc.id: oc.name for oc in self.object_classes.values()}
                index_names = [oc_id_2_name[rc.object_class_id] for rc in self.relationship_class]
                self.original_index_names = index_names
                index_names = make_names_unique(index_names)
                index_types = [str for _ in index_names]
                self.relationship_tuple_key = tuple(index_names[:len(self.relationship_class)])
                data = [r.object_name_list.split(',') + ['x'] for r in self.relationships.values()]
                data_dict = {}
                self.parameters = {}
                self.objects = {}
                for oc in self.object_classes.values():
                    objects = {o.name: o for o in self.db_map.object_list(class_id = oc.id).all()}
                    self.objects = {**self.objects, **objects}
                    tuple_entries[(oc.name,)] = set((o.name,) for o in objects.values())
            else:
                self.parameters = {p.name: p for p in self.db_map.parameter_list(relationship_class_id = self.relationship_class[0].id).all()}
                tuple_entries[(PARAMETER_NAME,)] = set((p.name,) for p in self.parameters.values())
                data, index_names, index_types, data_dict, org_names = get_relationshipclass_json(self.db_map, class_name, self.current_value_type)
                self.relationship_tuple_key = tuple(index_names[:len(self.relationship_class)])
                self.original_index_names = org_names
                tuple_entries[self.relationship_tuple_key] = set(tuple(r.object_name_list.split(",")) for r in self.relationships.values())
                self.objects = {}
                for oc in self.object_classes.values():
                    objects = {o.name: o for o in self.db_map.object_list(class_id = oc.id).all()}
                    self.objects = {**self.objects, **objects}
            
        self.parameter_values = data_dict
        selection_key = (self.current_class_name, self.current_class_type, self.current_value_type)
        if selection_key in self.class_pivot_preferences:
            # get previously used pivot
            index = self.class_pivot_preferences[selection_key].index
            columns = self.class_pivot_preferences[selection_key].columns
            frozen = self.class_pivot_preferences[selection_key].frozen
            frozen_value = self.class_pivot_preferences[selection_key].frozen_value
        else:
            # use default pivot
            index = [n for n in index_names if n not in [PARAMETER_NAME, INDEX_NAME]]
            columns = [PARAMETER_NAME] if PARAMETER_NAME in index_names else []
            frozen = [INDEX_NAME] if INDEX_NAME in index_names else []
            frozen_value = (1,) if frozen else ()
        # update model and views
        self.model.set_new_data(data, index_names, index_types, index, columns, frozen, frozen_value, valid_index_values, tuple_entries)
        self.proxy_model.clear_filter()
        self.update_filters_to_new_model()
        self.update_pivot_lists_to_new_model()
        self.update_frozen_table_to_model()
    
    def delete_row(self):
        self.proxy_model.delete_row_col(self.ui.pivot_table.selectedIndexes(), "row")

    def delete_col(self):
        self.proxy_model.delete_row_col(self.ui.pivot_table.selectedIndexes(), "column")

    def delete_index_values(self):
        indexes = [self.proxy_model.mapToSource(i) for i in self.ui.pivot_table.selectedIndexes()]
        delete_dict = {}
        for i in indexes:
            index_name = None
            if self.model.index_in_column_headers(i):
                value = self.model.data(i)
                if value:
                    index_name = self.model.pivot_columns[i.row()]
            elif self.model.index_in_row_headers(i):
                value = self.model.data(i)
                if value:
                    index_name = self.model.pivot_index[i.column()]
            if index_name:
                if index_name in delete_dict:
                    delete_dict[index_name].add(value)
                else:
                    delete_dict[index_name] = set([value])
        self.model.delete_index_values(delete_dict)
    
    def delete_relationship_values(self):
        if not self.current_class_type == RELATIONSHIP_CLASS:
            return
        indexes = [self.proxy_model.mapToSource(i) for i in self.ui.pivot_table.selectedIndexes()]
        pos = [self.model._index_ind[n] for n in self.relationship_tuple_key]
        getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
        delete_dict = {self.relationship_tuple_key: set()}
        for i in indexes:
            if self.model.index_in_column_headers(i) or self.model.index_in_row_headers(i):
                key = self.model.get_key(i)
                key = getter(key)
                if all(key):
                    delete_dict[self.relationship_tuple_key].add(key)
        self.model.delete_tuple_index_values(delete_dict)

    def onRightClick(self, QPos=None):
        class_type = self.current_class_type
        indexes = [self.proxy_model.mapToSource(i) for i in self.ui.pivot_table.selectedIndexes()]
        self.delete_index_action.setText("Delete index values")
        self.delete_index_action.setEnabled(False)
        self.delete_relationship_action.setText("Delete relationships")
        self.delete_relationship_action.setEnabled(False)
        if len(indexes) > 1:
            if (any(self.model.index_in_column_headers(i) for i in indexes) or
                any(self.model.index_in_row_headers(i) for i in indexes)):
                self.delete_index_action.setText("Delete selected index values")
                self.delete_index_action.setEnabled(True)
                if class_type == RELATIONSHIP_CLASS:
                    self.delete_relationship_action.setText("Delete selected relationships")
                    self.delete_relationship_action.setEnabled(True)
                
        elif len(indexes) == 1:
            index = indexes[0]
            if self.model.index_in_column_headers(index):
                value = self.model.data(index)
                if value:
                    index_name = self.model.pivot_columns[index.row()]
                    self.delete_index_action.setText("Delete {}: {}".format(index_name, value))
                    self.delete_index_action.setEnabled(True)
            elif self.model.index_in_row_headers(index):
                value = self.model.data(index)
                if value:
                    index_name = self.model.pivot_index[index.column()]
                    self.delete_index_action.setText("Delete {}: {}".format(index_name, value))
                    self.delete_index_action.setEnabled(True)
            if class_type == RELATIONSHIP_CLASS and (self.model.index_in_column_headers(index) or self.model.index_in_row_headers(index)):
                pos = [self.model._index_ind[n] for n in self.relationship_tuple_key]
                getter = tuple_itemgetter(operator.itemgetter(*pos), len(pos))
                key = self.model.get_key(index)
                key = getter(key)
                if all(key):
                    self.delete_relationship_action.setText("Delete relationship: {}".format(", ".join(key)))
                    self.delete_relationship_action.setEnabled(True)
            
        parent=self.sender()
        pPos=parent.mapToGlobal(QPoint(5, 20))
        mPos=pPos+QPos
        self.rcMenu.move(mPos)
        self.rcMenu.show()

    def table_index_entries_changed(self, parent, deleted_enties, added_entries):
        for flist in self.filter:
            f = flist[0]
            if f.column in deleted_enties:
                for i in reversed(range(1,f.count())):
                    if f.itemData(i, Qt.UserRole) in deleted_enties[f.column]:
                        f.removeItem(i)
            if f.column in added_entries:
                f.add_items(list(added_entries[f.column]))
                self.change_filter(f)

    def add_filter_comboboxes(self, data, index_names):
        for i, name in enumerate(index_names):
            cblist = self.create_filter_combobox(name)
            self.filter.append(cblist)
            self.ui.h_layout_filter.addLayout(cblist[2])
            cblist[0].setItemList(set([d[i] for d in data]))
            
    
    def create_filter_combobox(self, name):
        cb = CheckableComboBox()
        cb.column = name
        cb.listClosed.connect(self.change_filter)
        l = QLabel(name + ":")
        l.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        hb = QVBoxLayout()
        hb.addWidget(l)
        hb.addWidget(cb)
        return [cb, l, hb]
            
    def change_filter(self, parent):
        column = parent.column
        checked_items = []
        for i in range(parent.count()):
            if parent.itemData(i, Qt.CheckStateRole) and parent.itemText(i) != "(select all)":
                checked_items.append(parent.itemData(i, Qt.UserRole))
        self.proxy_model.set_filter(column, checked_items)
    
    def change_pivot(self, parent, event):
        # TODO: when getting items from the list that was source of drop 
        # the droped item is not removed, ugly solution is to filter the other list
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
            if len(frozen) == 1 and frozen[0] == INDEX_NAME and not frozen_values:
                frozen_values = [(1,)]
            self.ui.table_frozen.set_data(frozen, frozen_values)
            for i in range(self.ui.table_frozen.model.columnCount()):
                self.ui.table_frozen.resizeColumnToContents(i)
        elif not frozen and parent == self.ui.list_frozen or event.source() == self.ui.list_frozen:
            self.ui.table_frozen.set_data([], [])
        frozen_value = self.ui.table_frozen.get_selected_row()
        self.model.setPivot(index, columns, frozen, frozen_value)
        # save current pivot
        self.class_pivot_preferences[(self.current_class_name, self.current_class_type, self.current_value_type)] = self.PivotPreferences(index, columns, frozen, frozen_value)
    
    def find_frozen_values(self, frozen):
        if not frozen:
            return []
        keys = tuple(self.model._index_ind[i] for i in frozen)
        getter = tuple_itemgetter(operator.itemgetter(*keys), len(keys))
        frozen_values = set(getter(key) for key in self.model._data)
        # add indexes without values
        for k, v in self.model.tuple_index_entries.items():
            if INDEX_NAME in frozen and INDEX_NAME not in k:
                # add default value for index named INDEX_NAME = 1
                k = k + (INDEX_NAME,)
                v = [line + (1,) for line in v]
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

    def closeEvent(self, event=None):
        self.db_map.close()
        if event:
            event.accept()

if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    w = TabularViewForm()
    w.show()
    sys.exit(app.exec_())