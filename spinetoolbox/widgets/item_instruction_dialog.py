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

"""A dialog for editing the User Mode instruction of a project item."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QWidget


class ItemInstructionDialog(QDialog):
    def __init__(self, parent: QWidget, item_name: str, text: str):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        from ..ui.item_instruction_dialog import Ui_Form

        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setWindowTitle(f"Instruction for {item_name}")
        self._ui.instruction_text_edit.setPlainText(text)
        self._ui.button_box.accepted.connect(self.accept)
        self._ui.button_box.rejected.connect(self.reject)

    @property
    def text(self) -> str:
        return self._ui.instruction_text_edit.toPlainText().strip()
