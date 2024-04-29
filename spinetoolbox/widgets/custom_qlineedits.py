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

"""Contains a custom line edit."""
from PySide6.QtWidgets import QLineEdit
from .custom_qwidgets import UndoRedoMixin


class PropertyQLineEdit(UndoRedoMixin, QLineEdit):
    """A custom QLineEdit for Project Item Properties."""

    def setText(self, text):
        """Overridden to prevent the cursor going to the end whenever the user is still editing.
        This happens because we set the text programmatically in undo/redo implementations.
        """
        pos = self.cursorPosition()
        super().setText(text)
        self.setCursorPosition(pos)
