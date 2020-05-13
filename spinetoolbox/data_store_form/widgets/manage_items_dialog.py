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
from PySide2.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPlainTextEdit,
    QDialogButtonBox,
    QHeaderView,
    QAction,
    QApplication,
    QGroupBox,
    QCheckBox,
)
from PySide2.QtCore import Slot, Qt, QTimer, Signal
from ...widgets.custom_editors import IconColorEditor
from ...widgets.custom_qtableview import CopyPasteTableView
from ...helpers import busy_effect


class ManageItemsDialog(QDialog):
    """A dialog with a CopyPasteTableView and a QDialogButtonBox. Base class for all
    dialogs to query user's preferences for adding/editing/managing data items.
    """

    def __init__(self, parent, db_mngr):
        """Init class.

        Args:
            parent (DataStoreForm): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.model = None
        self.table_view = CopyPasteTableView(self)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.verticalHeader().setDefaultSectionSize(parent.default_row_height)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def connect_signals(self):
        """Connect signals to slots."""
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.table_view.itemDelegate().data_committed.connect(self.set_model_data)
        self.model.dataChanged.connect(self._handle_model_data_changed)
        self.model.modelReset.connect(self._handle_model_reset)

    def resize_window_to_columns(self, height=None):
        if height is None:
            height = self.sizeHint().height()
        margins = self.layout().contentsMargins()
        self.resize(
            margins.left()
            + margins.right()
            + self.table_view.frameWidth() * 2
            + self.table_view.verticalHeader().width()
            + self.table_view.horizontalHeader().length(),
            height,
        )

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

    def create_object_pixmap(self, object_class_name):
        # TODO: create a better method in db_mngr so we don't need to access the icon_mngr attribute
        return self.db_mngr.icon_mngr.create_object_pixmap(object_class_name)


class CommitDialog(QDialog):
    """A dialog to query user's preferences for new commit.
    """

    def __init__(self, parent, *db_names):
        """Initialize class.

        Args:
            parent (QWidget): the parent widget
            db_names (str): database names
        """
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
        self.commit_msg = None
        self.setWindowTitle('Commit changes to {}'.format(",".join(db_names)))
        form = QVBoxLayout(self)
        form.setContentsMargins(4, 4, 4, 4)
        self.action_accept = QAction(self)
        self.action_accept.setShortcut(QApplication.translate("Dialog", "Ctrl+Return", None, -1))
        self.action_accept.triggered.connect(self.accept)
        self.action_accept.setEnabled(False)
        self.commit_msg_edit = QPlainTextEdit(self)
        self.commit_msg_edit.setPlaceholderText('Commit message \t(press Ctrl+Enter to commit)')
        self.commit_msg_edit.addAction(self.action_accept)
        button_box = QDialogButtonBox()
        button_box.addButton(QDialogButtonBox.Cancel)
        self.commit_button = button_box.addButton('Commit', QDialogButtonBox.AcceptRole)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        form.addWidget(self.commit_msg_edit)
        form.addWidget(button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.commit_msg_edit.textChanged.connect(self.receive_text_changed)
        self.receive_text_changed()

    @Slot()
    def receive_text_changed(self):
        """Called when text changes in the commit msg text edit.
        Enable/disable commit button accordingly."""
        self.commit_msg = self.commit_msg_edit.toPlainText()
        cond = self.commit_msg.strip() != ""
        self.commit_button.setEnabled(cond)
        self.action_accept.setEnabled(cond)


class SelectDBItemsDialog(QDialog):
    """A dialog to query a selection of dbs and items from the user."""

    _MARGIN = 3
    _ITEM_TYPES = (
        "object class",
        "relationship class",
        "parameter definition",
        "parameter tag",
        "parameter value list",
        "object",
        "relationship",
        "parameter value",
    )

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        db_maps_group_box = QGroupBox("Databases", top_widget)
        db_maps_layout = QVBoxLayout(db_maps_group_box)
        db_maps_layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        self.db_map_check_boxes = {db_map: QCheckBox(db_map.codename, db_maps_group_box) for db_map in self.db_maps}
        for check_box in self.db_map_check_boxes.values():
            check_box.stateChanged.connect(lambda _: QTimer.singleShot(0, self._set_item_check_box_enabled))
            check_box.setChecked(True)
            db_maps_layout.addWidget(check_box)
        items_group_box = QGroupBox("Items", top_widget)
        items_layout = QVBoxLayout(items_group_box)
        items_layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        self.item_check_boxes = {item_type: QCheckBox(item_type, items_group_box) for item_type in self._ITEM_TYPES}
        for check_box in self.item_check_boxes.values():
            check_box.stateChanged.connect(lambda _: QTimer.singleShot(0, self._set_item_check_box_states_in_cascade))
            items_layout.addWidget(check_box)
        top_layout.addWidget(db_maps_group_box)
        top_layout.addWidget(items_group_box)
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(top_widget)
        layout.addWidget(button_box)
        layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        self.setAttribute(Qt.WA_DeleteOnClose)

    @property
    def positive(self):
        """Returns a boolean indicating which check state (True or False) needs to be propagated in cascade
        across item check boxes. See ``_set_item_check_box_states_in_cascade``.
        """
        raise NotImplementedError()

    @Slot()
    def _set_item_check_box_enabled(self):
        """Set the enabled property on item check boxes depending on the state of db_map check boxes."""
        enabled = any([x.isChecked() for x in self.db_map_check_boxes.values()])
        for check_box in self.item_check_boxes.values():
            check_box.setEnabled(enabled)

    @Slot()
    def _set_item_check_box_states_in_cascade(self):
        """Set state of item check boxes in cascade."""
        if self.item_check_boxes["object class"].isChecked() is self.positive:
            self.item_check_boxes["object"].setChecked(self.positive)
            self.item_check_boxes["relationship class"].setChecked(self.positive)
        if (
            self.item_check_boxes["relationship class"].isChecked() is self.positive
            or self.item_check_boxes["object"].isChecked() is self.positive
        ):
            self.item_check_boxes["relationship"].setChecked(self.positive)
        if (
            self.item_check_boxes["relationship class"].isChecked() is self.positive
            and self.item_check_boxes["object class"].isChecked() is self.positive
        ):
            self.item_check_boxes["parameter definition"].setChecked(self.positive)
        if self.item_check_boxes["parameter definition"].isChecked() is self.positive or (
            self.item_check_boxes["relationship"].isChecked() is self.positive
            and self.item_check_boxes["object"].isChecked() is self.positive
        ):
            self.item_check_boxes["parameter value"].setChecked(self.positive)


class MassRemoveItemsDialog(SelectDBItemsDialog):
    """A dialog to query user's preferences for mass removing db items."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Mass remove items")

    @property
    def positive(self):
        return True

    def accept(self):
        db_map_typed_data = {
            db_map: {
                item_type: list(self.db_mngr.get_items(db_map, item_type))
                for item_type, check_box in self.item_check_boxes.items()
                if check_box.isChecked()
            }
            for db_map, check_box in self.db_map_check_boxes.items()
            if check_box.isChecked()
        }
        self.db_mngr.remove_items(db_map_typed_data)
        super().accept()


class GetItemsForExportDialog(SelectDBItemsDialog):
    """A dialog to let users chose items for JSON export."""

    data_submitted = Signal(object)

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (DataStoreForm)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Select items for export")
        for item_type in (
            "object class",
            "relationship class",
            "parameter definition",
            "parameter tag",
            "parameter value list",
        ):
            self.item_check_boxes[item_type].setChecked(True)

    @property
    def positive(self):
        return False

    def accept(self):
        super().accept()
        db_map_items_for_export = {
            db_map: [item_type for item_type, check_box in self.item_check_boxes.items() if check_box.isChecked()]
            for db_map, check_box in self.db_map_check_boxes.items()
            if check_box.isChecked()
        }
        db_map_ids_for_export = {}
        for db_map, item_types in db_map_items_for_export.items():
            item_ids = db_map_ids_for_export[db_map] = dict()
            if "object class" not in item_types:
                item_ids["object_class_ids"] = ()
            if "relationship class" not in item_types:
                item_ids["relationship_class_ids"] = ()
            if "object" not in item_types:
                item_ids["object_ids"] = ()
            if "relationship" not in item_types:
                item_ids["relationship_ids"] = ()
            if "parameter definition" not in item_types:
                item_ids["object_parameter_ids"] = item_ids["relationship_parameter_ids"] = ()
            if "parameter value" not in item_types:
                item_ids["object_parameter_value_ids"] = item_ids["relationship_parameter_value_ids"] = ()
            if "parameter value list" not in item_types:
                item_ids["parameter_value_list_ids"] = ()
        self.data_submitted.emit(db_map_ids_for_export)
