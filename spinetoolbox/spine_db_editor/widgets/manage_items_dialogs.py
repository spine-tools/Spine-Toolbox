######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Classes for custom QDialogs to add edit and remove database items."""
from functools import reduce, cached_property
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, QGridLayout
from PySide6.QtCore import Slot, Qt, QModelIndex
from PySide6.QtGui import QAction
from ..mvcmodels.entity_tree_item import EntityClassItem
from spinetoolbox.spine_db_editor.widgets.custom_editors import IconColorEditor
from ...widgets.custom_qtableview import CopyPasteTableView
from ...helpers import busy_effect, preferred_row_height, DB_ITEM_SEPARATOR


class DialogWithButtons(QDialog):
    def __init__(self, parent, db_mngr):
        """
        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.db_mngr = db_mngr
        self._accept_action = QAction("OK", parent=self)
        self._accept_action.setShortcut("Ctrl+Return")
        self.addAction(self._accept_action)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.setAttribute(Qt.WA_DeleteOnClose)
        QGridLayout(self)

    def showEvent(self, ev):
        super().showEvent(ev)
        self._populate_layout()

    def _populate_layout(self):
        self.layout().addWidget(self.button_box)

    def connect_signals(self):
        """Connect signals to slots."""
        self._accept_action.triggered.connect(self.accept)
        self.button_box.accepted.connect(self._accept_action.trigger)
        self.button_box.rejected.connect(self.reject)


class DialogWithTableAndButtons(DialogWithButtons):
    def __init__(self, parent, db_mngr):
        """
        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent, db_mngr)
        self.table_view = self.make_table_view()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setMinimumSectionSize(120)
        self.table_view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))

    def _populate_layout(self):
        self.layout().addWidget(self.table_view)
        super()._populate_layout()

    def showEvent(self, ev):
        super().showEvent(ev)
        self.resize_window_to_columns()

    def make_table_view(self):
        raise NotImplementedError()

    def resize_window_to_columns(self, height=None):
        self.table_view.resizeColumnsToContents()
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


class ManageItemsDialog(DialogWithTableAndButtons):
    """A dialog with a CopyPasteTableView and a QDialogButtonBox. Base class for all
    dialogs to query user's preferences for adding/editing/managing data items.
    """

    def __init__(self, parent, db_mngr):
        """
        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent, db_mngr)
        self.model = None

    def make_table_view(self):
        table_view = CopyPasteTableView(self)
        table_view.init_copy_and_paste_actions()
        return table_view

    def connect_signals(self):
        """Connect signals to slots."""
        super().connect_signals()
        try:
            self.table_view.itemDelegate().data_committed.connect(self.set_model_data)
        except AttributeError:
            pass
        self.model.dataChanged.connect(self._handle_model_data_changed)
        self.model.modelReset.connect(self._handle_model_reset)

    @Slot(QModelIndex, QModelIndex, list)
    def _handle_model_data_changed(self, top_left, bottom_right, roles):
        """Reimplement in subclasses to handle changes in model data."""

    @Slot(QModelIndex, object)
    def set_model_data(self, index, data):
        """Update model data."""
        if data is None:
            return
        self.model.setData(index, data, Qt.ItemDataRole.EditRole)

    @Slot()
    def _handle_model_reset(self):
        """Resize columns and form."""
        self.table_view.resizeColumnsToContents()
        self.resize_window_to_columns()


class GetEntityClassesMixin:
    """Provides a method to retrieve entity classes for AddEntitiesDialog and AddEntityClassesDialog."""

    @cached_property
    def db_map_ent_cls_lookup(self):
        return {
            db_map: {
                tuple(x[k] for k in EntityClassItem.visual_key): x
                for x in self.db_mngr.get_items(db_map, "entity_class")
            }
            for db_map in self.db_maps
        }

    @cached_property
    def db_map_ent_cls_lookup_by_name(self):
        return {
            db_map: {x["name"]: x for x in self.db_mngr.get_items(db_map, "entity_class")} for db_map in self.db_maps
        }

    def entity_class_name_list(self, row):
        """Return a list of entity class names present in all databases selected for given row.
        Used by `ManageEntityClassesDelegate`.
        """
        db_column = self.model.header.index("databases")
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        return self._entity_class_name_list_from_db_maps(*db_maps)

    def _entity_class_name_list_from_db_maps(self, *db_maps):
        db_maps = iter(db_maps)
        db_map = next(db_maps, None)
        if not db_map:
            return []
        # Initalize list from first db_map
        entity_class_name_list = list(self.db_map_ent_cls_lookup_by_name[db_map])
        # Update list from remaining db_maps
        for db_map in db_maps:
            entity_class_name_list = [
                name for name in self.db_map_ent_cls_lookup_by_name[db_map] if name in entity_class_name_list
            ]
        return sorted(entity_class_name_list)


class GetEntitiesMixin:
    """Provides a method to retrieve entities for AddEntitiesDialog and EditEntitiesDialog."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entity_class = None
        self._class_key = None

    @property
    def class_key(self):
        return self._class_key

    @property
    def dimension_name_list(self):
        return self.entity_class["dimension_name_list"]

    @property
    def class_name(self):
        return self.entity_class["name"]

    @class_key.setter
    def class_key(self, class_key):
        self._class_key = class_key
        entity_classes = (self.db_map_ent_cls_lookup[db_map].get(self.class_key) for db_map in self.db_maps)
        self.entity_class = next((x for x in entity_classes if x is not None), None)

    @cached_property
    def db_map_ent_lookup(self):
        db_map_ent_lookup = {}
        for db_map in self.db_maps:
            ent_lookup = db_map_ent_lookup.setdefault(db_map, {})
            for x in self.db_mngr.get_items(db_map, "entity"):
                byname = DB_ITEM_SEPARATOR.join(x["entity_byname"])
                ent_lookup[x["class_id"], byname] = ent_lookup[x["superclass_id"], byname] = x
        return db_map_ent_lookup

    @cached_property
    def db_map_alt_id_lookup(self):
        return {
            db_map: {x["name"]: x["id"] for x in self.db_mngr.get_items(db_map, "alternative")}
            for db_map in self.db_maps
        }

    def alternative_name_list(self, row):
        """Return a list of alternative names present in all databases selected for given row.
        Used by `ManageEntitiesDelegate`.
        """
        db_column = self.model.header.index("databases")
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        return sorted(set(x for db_map in db_maps for x in self.db_map_alt_id_lookup[db_map]))

    def entity_name_list(self, row, column):
        """Return a list of entity names present in all databases selected for given row.
        Used by `ManageEntitiesDelegate`.
        """
        db_column = self.model.header.index("databases")
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        entity_name_lists = []
        for db_map in db_maps:
            entity_classes = self.db_map_ent_cls_lookup[db_map]
            if self.class_key not in entity_classes:
                continue
            ent_cls = entity_classes[self.class_key]
            dimension_id_list = ent_cls["dimension_id_list"]
            dimension_id = dimension_id_list[column]
            entities = self.db_map_ent_lookup[db_map]
            entity_name_lists.append([name for (class_id, name) in entities if class_id == dimension_id])
        if not entity_name_lists:
            return []
        return sorted(reduce(lambda x, y: set(x) & set(y), entity_name_lists))


class ShowIconColorEditorMixin:
    """Provides methods to show an `IconColorEditor` upon request."""

    @busy_effect
    def show_icon_color_editor(self, index):
        editor = IconColorEditor(self)
        editor.set_data(index.data(Qt.ItemDataRole.DisplayRole))
        editor.accepted.connect(lambda index=index, editor=editor: self.set_model_data(index, editor.data()))
        editor.show()
