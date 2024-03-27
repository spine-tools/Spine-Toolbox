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
"""Contains widget and utils to notify users of the 0.8 update."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog


class UpgradeNotificationDialog(QDialog):
    def __init__(self, parent):
        """
        Args:
            parent (QWidget): parent widget
        """
        super().__init__(parent)
        from ..ui.upgrade_notification import Ui_Form

        self._ui = Ui_Form()
        self._ui.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setWindowTitle("Toolbox 0.8 upgrade information")
        self._ui.button_box.rejected.connect(self.close)
