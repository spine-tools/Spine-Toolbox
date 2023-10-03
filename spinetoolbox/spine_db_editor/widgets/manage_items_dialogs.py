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
Classes for custom QDialogs to add edit and remove database items.
"""

from functools import reduce
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, QGridLayout
from PySide6.QtCore import Slot, Qt, QModelIndex
from PySide6.QtGui import QAction
from ...widgets.custom_editors import IconColorEditor
from ...widgets.custom_qtableview import CopyPasteTableView
from ...helpers import busy_effect, preferred_row_height


class ManageItemsDialogBase(QDialog):
    def __init__(self, parent, db_mngr):
        """Init class.

        Args:
            parent (SpineDBEditor): data store widget
            db_mngr (SpineDBManager)
        """
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.db_mngr = db_mngr
        self.table_view = self.make_table_view()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.horizontalHeader().setMinimumSectionSize(120)
        self.table_view.verticalHeader().setDefaultSectionSize(preferred_row_height(self))
        self._accept_action = QAction("OK", parent=self)
        self._accept_action.setShortcut("Ctrl+Return")
        self.addAction(self._accept_action)
        self.button_box = QDialogButtonBox(self)
        self.button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        layout = QGridLayout(self)
        layout.addWidget(self.table_view)
        layout.addWidget(self.button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def make_table_view(self):
        table_view = CopyPasteTableView(self)
        table_view.init_copy_and_paste_actions()
        return table_view

    def connect_signals(self):
        """Connect signals to slots."""
        self._accept_action.triggered.connect(self.accept)
        self.button_box.accepted.connect(self._accept_action.trigger)
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
            parent (SpineDBEditor): data store widget
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

    def make_db_map_ent_cls_lookup(self):
        return {
            db_map: {(x["name"], x["dimension_name_list"]): x for x in self.db_mngr.get_items(db_map, "entity_class")}
            for db_map in self.db_maps
        }

    def make_db_map_ent_cls_lookup_by_name(self):
        return {
            db_map: {x["name"]: x for x in self.db_mngr.get_items(db_map, "entity_class")} for db_map in self.db_maps
        }

    def entity_class_name_list(self, row):
        """Return a list of entity class names present in all databases selected for given row.
        Used by `ManageEntityClassesDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_maps = iter(self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps)
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

    def make_db_map_ent_lookup(self):
        return {
            db_map: {(x["class_id"], x["name"]): x for x in self.db_mngr.get_items(db_map, "entity")}
            for db_map in self.db_maps
        }

    def make_db_map_alt_id_lookup(self):
        return {
            db_map: {x["name"]: x["id"] for x in self.db_mngr.get_items(db_map, "alternative")}
            for db_map in self.db_maps
        }

    def alternative_name_list(self, row):
        """Return a list of alternative names present in all databases selected for given row.
        Used by `ManageEntitiesDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        return sorted(set(x for db_map in db_maps for x in self.db_map_alt_id_lookup[db_map]))

    def entity_name_list(self, row, column):
        """Return a list of entity names present in all databases selected for given row.
        Used by `ManageEntitiesDelegate`.
        """
        db_column = self.model.header.index('databases')
        db_names = self.model._main_data[row][db_column]
        db_maps = [self.keyed_db_maps[x] for x in db_names.split(",") if x in self.keyed_db_maps]
        ent_cls_key = (self.class_name, self.dimension_name_list)
        entity_name_lists = []
        for db_map in db_maps:
            entity_classes = self.db_map_ent_cls_lookup[db_map]
            if ent_cls_key not in entity_classes:
                continue
            ent_cls = entity_classes[ent_cls_key]
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
