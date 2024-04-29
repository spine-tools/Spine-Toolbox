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
from PySide6.QtWidgets import QCheckBox, QDialogButtonBox, QWidget
from PySide6.QtCore import Signal, Slot
from spinetoolbox.widgets.custom_qwidgets import SelectDatabaseItemsDialog
from spinetoolbox.widgets.select_database_items import add_check_boxes


class _SelectDatabases(QWidget):
    """A widget that shows checkboxes for each database."""

    checked_state_changed = Signal(int)

    def __init__(self, db_maps, checked_states, parent):
        """
        Args:
            db_maps (tuple of DatabaseMapping): database maps
            checked_states (dict, optional): mapping from item name to check state boolean
            parent (QWidget): parent widget
        """
        super().__init__(parent)
        from ..ui.select_databases import Ui_Form  # pylint: disable=import-outside-toplevel

        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self._check_boxes = {db_map: QCheckBox(db_map.codename, self) for db_map in db_maps}
        add_check_boxes(
            self._check_boxes,
            checked_states,
            self._ui.select_all_button,
            self._ui.deselect_all_button,
            self.checked_state_changed,
            self._ui.databases_grid_layout,
        )

    def checked_states(self):
        """Collects the checked states of databases.

        Returns:
            dict: mapping from database mapping to checked state boolean
        """
        return {db_map: box.isChecked() for db_map, box in self._check_boxes.items()}

    def any_checked(self):
        """Checks if any of the checkboxes is checked.

        Returns:
            bool: True if any check box is checked, False otherwise
        """
        return any(box.isChecked() for box in self._check_boxes.values())


class MassSelectItemsDialog(SelectDatabaseItemsDialog):
    """A dialog to query a selection of dbs and items from the user."""

    state_storing_requested = Signal(dict)

    def __init__(self, parent, db_mngr, *db_maps, stored_state, ok_button_text):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_mngr (SpineDBManager): database manager
            *db_maps: the dbs to select items from
            stored_state (dict, Optional): widget's previous state
            ok_button_text (str, optional): alternative label for the OK button
        """
        super().__init__(stored_state["items"] if stored_state is not None else None, ok_button_text, parent)
        self._db_mngr = db_mngr
        database_checked_states = (
            stored_state["databases"] if stored_state is not None else {db_map: True for db_map in db_maps}
        )
        self._database_check_boxes_widget = _SelectDatabases(tuple(db_maps), database_checked_states, self)
        self._database_check_boxes_widget.checked_state_changed.connect(self._handle_check_box_state_changed)
        self._ui.root_layout.insertWidget(0, self._database_check_boxes_widget)

    @Slot(int)
    def _handle_check_box_state_changed(self, _checked):
        """Enables or disables the OK button."""
        super()._handle_check_box_state_changed(_checked)
        if self._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).isEnabled():
            self._ui.button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
                self._database_check_boxes_widget.any_checked()
            )

    def accept(self):
        super().accept()
        state = {
            "databases": self._database_check_boxes_widget.checked_states(),
            "items": self._item_check_boxes_widget.checked_states(),
        }
        self.state_storing_requested.emit(state)


class MassRemoveItemsDialog(MassSelectItemsDialog):
    """A dialog to query user's preferences for mass removing db items."""

    def __init__(self, parent, db_mngr, *db_maps, stored_state=None):
        """Initialize class.

        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
            stored_state (dict, Optional): widget's previous state
        """
        super().__init__(parent, db_mngr, *db_maps, stored_state=stored_state, ok_button_text="Purge")
        self.setWindowTitle("Purge items")

    def accept(self):
        super().accept()
        item_checked_states = self._item_check_boxes_widget.checked_states()
        database_checked_states = self._database_check_boxes_widget.checked_states()
        db_map_purge_data = {
            db_map: {item_type for item_type, checked in item_checked_states.items() if checked}
            for db_map, is_checked in database_checked_states.items()
            if is_checked
        }
        self._db_mngr.purge_items(db_map_purge_data)


class MassExportItemsDialog(MassSelectItemsDialog):
    """A dialog to let users chose items for JSON export."""

    _warn_checked_non_data_items = False
    data_submitted = Signal(object)

    def __init__(self, parent, db_mngr, *db_maps, stored_state=None):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
            stored_state (dict, Optional): widget's previous state
        """
        super().__init__(parent, db_mngr, *db_maps, stored_state=stored_state, ok_button_text="Export")
        self.setWindowTitle("Export items")

    def accept(self):
        super().accept()
        item_checked_states = self._item_check_boxes_widget.checked_states()
        checked_items = [item_type for item_type, checked in item_checked_states.items() if checked]
        database_checked_states = self._database_check_boxes_widget.checked_states()
        db_map_items_for_export = {
            db_map: checked_items for db_map, is_checked in database_checked_states.items() if is_checked
        }
        self.data_submitted.emit(db_map_items_for_export)
