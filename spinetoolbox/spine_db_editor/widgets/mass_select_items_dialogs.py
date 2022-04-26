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
    QPushButton,
)
from PySide2.QtCore import Slot, Qt, Signal


class MassSelectItemsDialog(QDialog):
    """A dialog to query a selection of dbs and items from the user."""

    _MARGIN = 3
    _ITEM_TYPES = (
        "object_class",
        "relationship_class",
        "parameter_value_list",
        "parameter_definition",
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
        "metadata",
        "entity_metadata",
        "parameter_value_metadata",
    )
    _COLUMN_COUNT = 3

    def __init__(self, parent, db_mngr, *db_maps):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
        """
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        db_maps_group_box = QGroupBox("Databases", top_widget)
        items_group_box = QGroupBox("Items", top_widget)
        top_layout.addWidget(db_maps_group_box)
        top_layout.addWidget(items_group_box)
        button_box = QDialogButtonBox(self)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(top_widget)
        layout.addWidget(button_box)
        self._ok_button = button_box.button(QDialogButtonBox.Ok)
        self.db_map_check_boxes = {db_map: QCheckBox(db_map.codename, db_maps_group_box) for db_map in self.db_maps}
        self.item_check_boxes = {item_type: QCheckBox(item_type, items_group_box) for item_type in self._ITEM_TYPES}
        self._add_check_boxes(db_maps_group_box, self.db_map_check_boxes)
        self._add_check_boxes(items_group_box, self.item_check_boxes)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def _add_check_boxes(self, group_box, check_boxes):
        check_boxes = list(check_boxes.values())
        layout = QVBoxLayout(group_box)
        buttons = QWidget()
        grid = QWidget()
        layout.addWidget(grid)
        layout.addWidget(buttons)
        layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        buttons_layout = QHBoxLayout(buttons)
        select_all = QPushButton("Select all")
        deselect_all = QPushButton("Deselect all")
        select_all.clicked.connect(lambda _=False, boxes=check_boxes: _batch_set_check_state(boxes, True))
        deselect_all.clicked.connect(lambda _=False, boxes=check_boxes: _batch_set_check_state(boxes, False))
        buttons_layout.addWidget(select_all)
        buttons_layout.addWidget(deselect_all)
        buttons_layout.addStretch()
        buttons_layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        grid_layout = QGridLayout(grid)
        grid_layout.setContentsMargins(self._MARGIN, self._MARGIN, self._MARGIN, self._MARGIN)
        for k, check_box in enumerate(check_boxes):
            check_box.stateChanged.connect(self._handle_check_box_state_changed)
            row = k // self._COLUMN_COUNT
            column = k % self._COLUMN_COUNT
            check_box.setChecked(True)
            grid_layout.addWidget(check_box, row, column)

    @Slot(int)
    def _handle_check_box_state_changed(self, _checked):
        self._ok_button.setEnabled(
            any(x.isChecked() for x in self.db_map_check_boxes.values())
            and any(x.isChecked() for x in self.item_check_boxes.values())
        )


def _batch_set_check_state(check_boxes, checked):
    for check_box in check_boxes:
        check_box.setChecked(checked)


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
                item_type: {x["id"] for x in self.db_mngr.get_items(db_map, item_type, only_visible=False)}
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
        """
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
