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
Classes for custom QDialogs to add edit and remove database items.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from functools import reduce
from PySide2.QtWidgets import QDialog, QGridLayout, QDialogButtonBox, QHeaderView, QCheckBox, QWidget, QHBoxLayout
from PySide2.QtCore import Slot, Qt
from ...widgets.custom_editors import IconColorEditor
from ...widgets.custom_qtableview import CopyPasteTableView
from ...helpers import busy_effect
from ...mvcmodels.minimal_table_model import MinimalTableModel
from ...mvcmodels.empty_row_model import EmptyRowModel
from ...mvcmodels.compound_table_model import CompoundWithEmptyTableModel
from .custom_delegates import ManageParameterTagsDelegate


class ManageItemsDialogBase(QDialog):
    def __init__(self, parent, db_mngr):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.table_view = self.make_table_view()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(parent.default_row_height)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QGridLayout(self)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def make_table_view(self):
        return CopyPasteTableView(self)

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

    def resize_window_to_columns(self, height=None):
        if height is None:
            height = self.sizeHint().height()
        slack = 64
        margins = self.layout().contentsMargins()
        self.resize(
            slack
            + margins.left()
            + margins.right()
            + self.table_view.frameWidth() * 2
            + self.table_view.verticalHeader().width()
            + self.table_view.horizontalHeader().length(),
            height,
        )


class ManageItemsDialog(ManageItemsDialogBase):
    """A dialog with a CopyPasteTableView and a QDialogButtonBox. Base class for all
    dialogs to query user's preferences for adding/editing/managing data items.
    """

    def __init__(self, parent, db_mngr):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent, db_mngr)
        self.model = None

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        try:
            self.table_view.itemDelegate().data_committed.connect(self.set_model_data)
        except AttributeError:
            pass
        self.model.dataChanged.connect(self._handle_model_data_changed)
        self.model.modelReset.connect(self._handle_model_reset)

    @Slot("QModelIndex", "QModelIndex", "QVector")
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        """Reimplement in subclasses to handle changes in model data."""

    @Slot("QModelIndex", "QVariant")
    def set_model_data(self, index, data):
        """Update model data."""
        if data is None:
            return
        self.model.setData(index, data, Qt.EditRole)

    @Slot()
    def _handle_model_reset(self):
        """Resize columns and form."""
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()


class GetObjectClassesMixin:
    """Provides a method to retrieve object classes for AddObjectsDialog and AddRelationshipClassesDialog.
    """

    def make_db_map_obj_cls_lookup(self):
        return {
            db_map: {x["name"]: x for x in self.db_mngr.get_items(db_map, "object class")} for db_map in self.db_maps
        }

    def object_class_name_list(self, row):
        """Return a list of object class names present in all databases selected for given row.
        Used by `ManageObjectsDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_maps = iter(self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps)
        db_map = next(db_maps, None)
        if not db_map:
            return []
        # Initalize list from first db_map
        object_class_name_list = list(self.db_map_obj_cls_lookup[db_map])
        # Update list from remaining db_maps
        for db_map in db_maps:
            object_class_name_list = [x for x in self.db_map_obj_cls_lookup[db_map] if x in object_class_name_list]
        return object_class_name_list


class GetObjectsMixin:
    """Provides a method to retrieve objects for AddRelationshipsDialog and EditRelationshipsDialog.
    """

    def make_db_map_obj_lookup(self):
        return {
            db_map: {(x["class_id"], x["name"]): x for x in self.db_mngr.get_items(db_map, "object")}
            for db_map in self.db_maps
        }

    def make_db_map_rel_cls_lookup(self):
        return {
            db_map: {
                (x["name"], x["object_class_name_list"]): x
                for x in self.db_mngr.get_items(db_map, "relationship class")
            }
            for db_map in self.db_maps
        }

    def object_name_list(self, row, column):
        """Return a list of object names present in all databases selected for given row.
        Used by `ManageRelationshipsDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        rel_cls_key = (self.class_name, self.object_class_name_list)
        object_name_lists = []
        for db_map in db_maps:
            relationship_classes = self.db_map_rel_cls_lookup[db_map]
            if rel_cls_key not in relationship_classes:
                continue
            rel_cls = relationship_classes[rel_cls_key]
            object_class_id_list = rel_cls["object_class_id_list"]
            object_class_id_list = [int(x) for x in object_class_id_list.split(",")]
            object_class_id = object_class_id_list[column]
            objects = self.db_map_obj_lookup[db_map]
            object_name_lists.append([name for (class_id, name) in objects if class_id == object_class_id])
        if not object_name_lists:
            return []
        return list(reduce(lambda x, y: set(x) & set(y), object_name_lists))


class ShowIconColorEditorMixin:
    """Provides methods to show an `IconColorEditor` upon request.
    """

    @busy_effect
    def show_icon_color_editor(self, index):
        editor = IconColorEditor(self)
        editor.set_data(index.data(Qt.DisplayRole))
        editor.accepted.connect(lambda index=index, editor=editor: self.set_model_data(index, editor.data()))
        editor.show()

    def create_object_pixmap(self, index):
        db_map = next(iter(self.all_db_maps(index.row())), None)
        if db_map is None:
            return None
        object_class_name = index.data(Qt.DisplayRole)
        return self.db_mngr.icon_mngr[db_map].create_object_pixmap(object_class_name)


class ManageParameterTagsDialog(ManageItemsDialog):
    """A dialog to query user's preferences for managing parameter tags.
    """

    def __init__(self, parent, db_mngr, *db_maps):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager): the manager to do the removal
            db_maps (iter): DiffDatabaseMapping instances
        """
        super().__init__(parent, db_mngr)
        self.db_maps = db_maps
        self.keyed_db_maps = {db_map.codename: db_map for db_map in db_maps}
        self.setWindowTitle("Manage parameter tags")
        header = ['parameter tag', 'description', 'databases', 'remove']
        self.model = CompoundWithEmptyTableModel(self, header=header)
        self.table_view.setModel(self.model)
        self.table_view.setItemDelegate(ManageParameterTagsDelegate(self))
        self.connect_signals()
        self.orig_data = list()
        model_data = list()
        tag_dict = {}
        for db_map in self.db_maps:
            for parameter_tag in self.db_mngr.get_items(db_map, "parameter tag"):
                tag_dict.setdefault(parameter_tag["tag"], {})[db_map] = parameter_tag
        self.items = list(tag_dict.values())
        for item in self.items:
            parameter_tag = list(item.values())[0]
            tag = parameter_tag["tag"]
            description = parameter_tag["description"]
            remove = None
            db_names = ",".join([db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in item])
            row_data = [tag, description]
            self.orig_data.append(row_data.copy())
            row_data.extend([db_names, remove])
            model_data.append(row_data)
        db_names = ",".join(self.keyed_db_maps.keys())
        self.filled_model = MinimalTableModel(self, header=header)
        self.empty_model = EmptyRowModel(self, header=header)
        self.model.sub_models += [self.filled_model, self.empty_model]
        self.model.connect_model_signals()
        self.filled_model.reset_model(model_data)
        self.empty_model.set_default_row(**{'databases': db_names})
        # Create checkboxes
        column = self.model.header.index('remove')
        for row in range(0, self.filled_model.rowCount()):
            index = self.model.index(row, column)
            check_box = QCheckBox(self)
            widget = QWidget(self)
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addStretch()
            layout.addWidget(check_box)
            layout.addStretch()
            self.table_view.setIndexWidget(index, widget)
        self._handle_model_reset()

    def all_databases(self, row):
        """Returns a list of db names available for a given row.
        Used by delegates.
        """
        if row < self.filled_model.rowCount():
            item = self.items[row]
            return [db_name for db_name, db_map in self.keyed_db_maps.items() if db_map in item]
        return self.keyed_db_maps.keys()

    @Slot()
    def accept(self):
        """Collect info from dialog and try to update, remove, add items."""
        # Update and remove
        db_map_data_to_upd = {}
        db_map_typed_data_to_rm = {}
        for i in range(self.filled_model.rowCount()):
            tag, description, db_names, _ = self.filled_model.row_data(i)
            if db_names is None:
                db_names = ""
            db_name_list = db_names.split(",")
            try:
                db_maps = [self.keyed_db_maps[x] for x in db_name_list]
            except KeyError as e:
                self.parent().msg_error.emit("Invalid database {0} at row {1}".format(e, i + 1))
                return
            # Remove
            check_box = self.table_view.indexWidget(self.model.index(i, self.model.header.index('remove')))
            if check_box.isChecked():
                for db_map in db_maps:
                    parameter_tag = self.items[i][db_map]
                    db_map_typed_data_to_rm.setdefault(db_map, {}).setdefault("parameter tag", []).append(parameter_tag)
                continue
            if not tag:
                self.parent().msg_error.emit("Tag missing at row {}".format(i + 1))
                return
            # Update
            if [tag, description] != self.orig_data[i]:
                for db_map in db_maps:
                    parameter_tag = self.items[i][db_map]
                    item = {'id': parameter_tag["id"], 'tag': tag, 'description': description}
                    db_map_data_to_upd.setdefault(db_map, []).append(item)
        # Insert
        db_map_data_to_add = {}
        offset = self.filled_model.rowCount()
        for i in range(self.empty_model.rowCount() - 1):  # last row will always be empty
            tag, description, db_names, _ = self.empty_model.row_data(i)
            if db_names is None:
                db_names = ""
            db_name_list = db_names.split(",")
            try:
                db_maps = [self.keyed_db_maps[x] for x in db_name_list]
            except KeyError as e:
                self.parent().msg_error.emit("Invalid database {0} at row {1}".format(e, offset + i + 1))
                return
            if not tag:
                self.parent().msg_error.emit("Tag missing at row {0}".format(offset + i + 1))
                return
            for db_map in db_maps:
                item = {'tag': tag, 'description': description}
                db_map_data_to_add.setdefault(db_map, []).append(item)
        if db_map_typed_data_to_rm:
            self.db_mngr.remove_items(db_map_typed_data_to_rm)
        if db_map_data_to_upd:
            self.db_mngr.update_parameter_tags(db_map_data_to_upd)
        if db_map_data_to_add:
            self.db_mngr.add_parameter_tags(db_map_data_to_add)
        super().accept()
