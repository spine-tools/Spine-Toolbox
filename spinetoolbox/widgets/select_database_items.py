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

"""A widget and utilities to select database items."""
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QCheckBox, QWidget
from spinedb_api.db_mapping import DatabaseMapping


def add_check_boxes(check_boxes, checked_states, select_all_button, deselect_all_button, state_changed_slot, layout):
    """Adds check boxes to grid layout.

    Args:
        check_boxes (dict): mapping from label to QCheckBox
        checked_states (dict): mapping from label to checked state boolean
        select_all_button (QPushButton): the Select all button
        deselect_all_button (QPushButton): the Deselect all button
        state_changed_slot (Callable): slot to call when any checked state changes
        layout (QGridLayout): target layout
    """
    check_box_widgets = tuple(check_boxes.values())
    select_all_button.clicked.connect(lambda _=False: batch_set_check_state(check_box_widgets, True))
    deselect_all_button.clicked.connect(lambda _=False: batch_set_check_state(check_box_widgets, False))
    for k, (label, check_box) in enumerate(check_boxes.items()):
        check_box.stateChanged.connect(state_changed_slot)
        row = k // SelectDatabaseItems.COLUMN_COUNT
        column = k % SelectDatabaseItems.COLUMN_COUNT
        check_box.setChecked(checked_states.get(label, False))
        layout.addWidget(check_box, row, column)


def batch_set_check_state(boxes, checked):
    """Sets the checked state of multiple check boxes.

    Args:
        boxes (Iterable of QCheckBox): check boxes
        checked (bool): checked state
    """
    for check_box in boxes:
        check_box.setChecked(checked)


class SelectDatabaseItems(QWidget):
    """Widget that allows selecting database items."""

    checked_state_changed = Signal(int)
    COLUMN_COUNT = 3
    _DATA_ITEMS = (
        "entity",
        "entity_group",
        "parameter_value",
        "entity_metadata",
        "parameter_value_metadata",
    )
    _SCENARIO_ITEMS = ("alternative", "scenario", "scenario_alternative")

    def __init__(self, checked_states=None, parent=None):
        """
        Args:
            checked_states (dict, optional): mapping from item name to check state boolean
            parent (QWidget): parent widget
        """
        from ..ui.select_database_items import Ui_Form  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._ui.select_data_items_button.clicked.connect(self._select_data_items)
        self._ui.select_scenario_items_button.clicked.connect(self._select_scenario_items)
        checkable_item_types = tuple(type_ for type_ in DatabaseMapping.item_types() if type_ != "commit")
        checked_states = (
            checked_states if checked_states is not None else {item: False for item in checkable_item_types}
        )
        self._item_check_boxes = {item_type: QCheckBox(item_type, self) for item_type in checkable_item_types}
        add_check_boxes(
            self._item_check_boxes,
            checked_states,
            self._ui.select_all_button,
            self._ui.deselect_all_button,
            self.checked_state_changed,
            self._ui.item_grid_layout,
        )

    def checked_states(self):
        """Collects the checked states of database items.

        Returns:
            dict: mapping from item name to checked state boolean
        """
        return {item: box.isChecked() for item, box in self._item_check_boxes.items()}

    def any_checked(self):
        """Checks if any of the checkboxes is checked.

        Returns:
            bool: True if any check box is checked, False otherwise
        """
        return any(box.isChecked() for box in self._item_check_boxes.values())

    def any_structural_item_checked(self):
        non_structural_items = set(self._DATA_ITEMS + self._SCENARIO_ITEMS)
        structural_item_check_boxes = (
            widget for item_type, widget in self._item_check_boxes.items() if item_type not in non_structural_items
        )
        for check_box in structural_item_check_boxes:
            if check_box.isChecked():
                return True
        return False

    @Slot(bool)
    def _select_data_items(self, _=False):
        """Checks all data items."""
        for item_name in self._DATA_ITEMS:
            self._item_check_boxes[item_name].setChecked(True)

    @Slot(bool)
    def _select_scenario_items(self, _=False):
        """Checks all scenario items."""
        for item_name in self._SCENARIO_ITEMS:
            self._item_check_boxes[item_name].setChecked(True)
