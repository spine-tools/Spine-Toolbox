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

"""Contains the MultiTabSpecEditor class."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu
from .multi_tab_window import MultiTabWindow


class MultiTabSpecEditor(MultiTabWindow):
    def __init__(self, toolbox, item_type):
        super().__init__(toolbox.qsettings(), f"{item_type}SpecEditor")
        self.setStyleSheet(toolbox.styleSheet())
        self._toolbox = toolbox
        self.item_type = item_type
        self.setWindowTitle(f"{item_type} specification editor".capitalize())
        icon = QIcon(self._toolbox.item_factories[item_type].icon())
        self.setWindowIcon(icon)

    def _make_other(self):
        return MultiTabSpecEditor(self._toolbox, self.item_type)

    def _make_new_tab(self, *args, **kwargs):
        tab = self._toolbox.item_factories[self.item_type].make_specification_editor(self._toolbox, *args, **kwargs)
        tab.setAttribute(Qt.WA_DeleteOnClose, True)
        return tab

    def _connect_tab_signals(self, tab):
        """Connects spec editor window (tab) signals.

        Args:
            tab (SpecificationEditorWindowBase): Specification editor window

        Returns:
            bool: True if ok, False otherwise
        """
        if not super()._connect_tab_signals(tab):
            return False
        tab.spec_toolbar().close_action.triggered.connect(self.handle_close_request_from_tab)
        return True

    def _disconnect_tab_signals(self, index):
        """Disconnects signals of spec editor window (tab) in given index.

        Args:
            index (int): Tab index

        Returns:
            bool: True if ok, False otherwise
        """
        if not super()._disconnect_tab_signals(index):
            return False
        tab = self.tab_widget.widget(index)
        tab.spec_toolbar().close_action.triggered.disconnect(self.handle_close_request_from_tab)
        return True

    @property
    def new_tab_title(self):
        return "<unnamed specification>"

    def show_plus_button_context_menu(self, global_pos):
        model = self._toolbox.filtered_spec_factory_models[self.item_type]
        specs = set(model.specifications()) - {tab.specification for tab in self.all_tabs()}
        if not specs:
            return
        other_index_by_spec = {}
        for other in self.others():
            for index, tab in enumerate(other.all_tabs()):
                other_index_by_spec[tab.specification] = (other, index)
        menu = QMenu(self)
        for spec in specs:
            other_index = other_index_by_spec.get(spec)
            if other_index is None:
                # Spec is not open on another multi tab editor, so open it here
                slot = lambda spec=spec: self.add_new_tab(spec)
            else:
                # Spec is open on another multi tab editor, so bring it here
                other, index = other_index
                slot = lambda other=other, index=index: other.move_tab(index, self)
            menu.addAction(spec.name, slot)
        menu.popup(global_pos)
        menu.aboutToHide.connect(menu.deleteLater)
