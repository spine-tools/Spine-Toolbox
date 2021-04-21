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
Contains the MultiTabSpecEditor class.

:author: M. Marin (KTH)
:date:   12.12.2020
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from .multi_tab_window import MultiTabWindow


class MultiTabSpecEditor(MultiTabWindow):
    def __init__(self, toolbox, item_type):
        super().__init__(toolbox.qsettings(), f"{item_type}SpecEditor")
        self._toolbox = toolbox
        self.item_type = item_type
        self.setWindowTitle(f"{item_type} specification editor".capitalize())
        icon = QIcon(self._toolbox.item_factories[item_type].icon())
        self.setWindowIcon(icon)

    def _make_other(self):
        return MultiTabSpecEditor(self._toolbox, self.item_type)

    def others(self):
        return [w for w in self._toolbox.get_all_multi_tab_spec_editors(self.item_type) if w is not self]

    def _make_new_tab(self, *args, **kwargs):
        tab = self._toolbox.item_factories[self.item_type].make_specification_editor(self._toolbox, *args, **kwargs)
        tab.setAttribute(Qt.WA_DeleteOnClose, True)
        return tab

    def show_plus_button_context_menu(self, global_pos):
        pass
