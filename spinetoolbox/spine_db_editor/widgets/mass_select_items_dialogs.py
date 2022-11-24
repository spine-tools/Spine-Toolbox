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

:author: M. Marin (KTH)
:date:   13.5.2018
"""

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QCheckBox
from PySide6.QtCore import Slot, Qt, Signal
from spinetoolbox.widgets.select_database_items import add_check_boxes, SelectDatabaseItems


class MassSelectItemsDialog(QDialog):
    """A dialog to query a selection of dbs and items from the user."""

    state_storing_requested = Signal(dict)

    def __init__(self, parent, db_mngr, *db_maps, stored_state=None):
        """
        Args:
            parent (SpineDBEditor): parent widget
            db_mngr (SpineDBManager): database manager
            *db_maps: the dbs to select items from
            stored_state (dict, Optional): widget's previous state
        """
        from ..ui.select_database_items_dialog import Ui_Dialog  # pylint: disable=import-outside-toplevel

        super().__init__(parent)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self._database_checked_states = (
            stored_state["databases"]
            if stored_state is not None
            else {db_map.codename: True for db_map in self.db_maps}
        )
        self._ui = Ui_Dialog()
        self._ui.setupUi(self)
        item_state = stored_state["items"] if stored_state is not None else None
        self._item_check_boxes_widget = SelectDatabaseItems(item_state, self)
        self._item_check_boxes_widget.checked_state_changed.connect(self._handle_check_box_state_changed)
        self._ui.root_layout.insertWidget(1, self._item_check_boxes_widget)
        self._ok_button = self._ui.button_box.button(QDialogButtonBox.Ok)
        self._db_map_check_boxes = {db_map: QCheckBox(db_map.codename, self) for db_map in self.db_maps}
        check_boxes = {box.text(): box for box in self._db_map_check_boxes.values()}
        add_check_boxes(
            check_boxes,
            self._database_checked_states,
            self._ui.select_all_button,
            self._ui.deselect_all_button,
            self._handle_check_box_state_changed,
            self._ui.databases_grid_layout,
        )

    @Slot(int)
    def _handle_check_box_state_changed(self, _checked):
        self._ok_button.setEnabled(
            any(x.isChecked() for x in self._db_map_check_boxes.values())
            and self._item_check_boxes_widget.any_checked()
        )

    def accept(self):
        super().accept()
        state = {"databases": self._database_checked_states, "items": self._item_check_boxes_widget.checked_states()}
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
        super().__init__(parent, db_mngr, *db_maps, stored_state=stored_state)
        self.setWindowTitle("Purge items")

    def accept(self):
        super().accept()
        item_checked_states = self._item_check_boxes_widget.checked_states()
        db_map_purge_data = {
            db_map: {item_type for item_type, checked in item_checked_states.items() if checked}
            for db_map, check_box in self._db_map_check_boxes.items()
            if check_box.isChecked()
        }
        self.db_mngr.purge_items(db_map_purge_data)


class MassExportItemsDialog(MassSelectItemsDialog):
    """A dialog to let users chose items for JSON export."""

    data_submitted = Signal(dict)

    def __init__(self, parent, db_mngr, *db_maps, stored_state=None):
        """
        Args:
            parent (SpineDBEditor)
            db_mngr (SpineDBManager)
            db_maps (DiffDatabaseMapping): the dbs to select items from
            stored_state (dict, Optional): widget's previous state
        """
        super().__init__(parent, db_mngr, *db_maps, stored_state=stored_state)
        self.setWindowTitle("Export items")

    def accept(self):
        super().accept()
        item_checked_states = self._item_check_boxes_widget.checked_states()
        checked_items = [item_type for item_type, checked in item_checked_states.items() if checked]
        db_map_items_for_export = {
            db_map: checked_items for db_map, check_box in self._db_map_check_boxes.items() if check_box.isChecked()
        }
        self.data_submitted.emit(db_map_items_for_export)
