######################################################################################################################
# Copyright (C) 2017-2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Gdx Export item's settings window.

:author: A. Soininen (VTT)
:date:   9.9.2019
"""

from PySide2.QtCore import Slot
from PySide2.QtWidgets import QMainWindow, QWidget
from ui.gdx_export_settings import Ui_Form

class GdxExportSettings(QMainWindow):
    def __init__(self, parent):
        super().__init__(parent)
        central_widget = QWidget()
        ui = Ui_Form()
        ui.setupUi(central_widget)
        self.setCentralWidget(central_widget)
        self.setWindowTitle("Gdx Export settings")
        ui.button_box.rejected.connect(self.__cancel)

    @Slot()
    def __cancel(self):
        self.close()
