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
Classes for custom QDialogs to add edit and remove database items.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from PySide2.QtWidgets import (
    QWidget,
    QDialog,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QDialogButtonBox,
    QGroupBox,
    QCheckBox,
)
from PySide2.QtCore import Slot, Qt, QTimer, Signal


class MassSelectItemsDialog(QDialog):
    """A dialog to query a selection of dbs and items from the user."""

    _MARGIN = 3
    _ITEM_TYPES = (
        "object_class",
        "relationship_class",
        "parameter_value_list",
        "parameter_definition",
        "parameter_tag",
        "parameter_definition_tag",
        "object",
        "relationship",
        "entity_group",
        "parameter_value",
        "alternative",
        "scenario",
        "scenario_alternative",
        "feature",
        "tool",
        "tool_feature",
        "tool_feature_method",
    )
    _COLUMN_COUNT = 2

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (SpineDBEditor)
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
        items_layout = QGridLayout(items_group_box)
        items_layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        self.item_check_boxes = {item_type: QCheckBox(item_type, items_group_box) for item_type in self._ITEM_TYPES}
        for k, check_box in enumerate(self.item_check_boxes.values()):
            row = k // self._COLUMN_COUNT
            column = k % self._COLUMN_COUNT
            check_box.setChecked(True)
            items_layout.addWidget(check_box, row, column)
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

    @Slot()
    def _set_item_check_box_enabled(self):
        """Set the enabled property on item check boxes depending on the state of db_map check boxes."""
        enabled = any([x.isChecked() for x in self.db_map_check_boxes.values()])
        for check_box in self.item_check_boxes.values():
            check_box.setEnabled(enabled)


class MassRemoveItemsDialog(MassSelectItemsDialog):
    """A dialog to query user's preferences for mass removing db items."""

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Purge items")

    def accept(self):
        super().accept()
        db_map_typed_data = {
            db_map: {
                item_type: {x["id"] for x in self.db_mngr.get_items(db_map, item_type)}
                for item_type, check_box in self.item_check_boxes.items()
                if check_box.isChecked()
            }
            for db_map, check_box in self.db_map_check_boxes.items()
            if check_box.isChecked()
        }
        self.db_mngr.remove_items(db_map_typed_data)


class MassExportItemsDialog(MassSelectItemsDialog):
    """A dialog to let users chose items for JSON export."""

    data_submitted = Signal(object)

    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class.

        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent, db_mngr, *db_maps)
        self.setWindowTitle("Export items")

    def accept(self):
        super().accept()
        db_map_items_for_export = {
            db_map: [item_type for item_type, check_box in self.item_check_boxes.items() if check_box.isChecked()]
            for db_map, check_box in self.db_map_check_boxes.items()
            if check_box.isChecked()
        }
        self.data_submitted.emit(db_map_items_for_export)
