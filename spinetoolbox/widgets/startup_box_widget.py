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

"""Classes for startup box opening and signals connection."""
from PySide6.QtWidgets import QWidget, QPushButton
from PySide6.QtCore import Qt, Slot, Signal
from spinetoolbox.ui.startup_box import Ui_Form


class StartupBoxWidget(QWidget):
    project_load_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent, f=Qt.WindowType.Window)
        self._ui = Ui_Form()
        self._ui.setupUi(self)

        # Connect the clicked signal of each button to a specific slot
        self._ui.pushButton_3.clicked.connect(self.open_tutorial1)
        self._ui.pushButton_4.clicked.connect(self.open_tutorial2)
        self._ui.pushButton_5.clicked.connect(self.open_tutorial3)
        self._ui.pushButton_6.clicked.connect(self.open_tutorial4)
        self._ui.pushButton_7.clicked.connect(self.open_tutorial5)

    @Slot()
    def open_tutorial1(self):
        print("Open 1st tutorial")
        path_to_project = "C:\\Users\ErmannoLoCascio\Desktop\eScience - Mopo\spine_projects\Simple Tutorial 4"
        self.project_load_requested.emit(path_to_project)

    @Slot()
    def open_tutorial2(self):
        path_to_project = "C:\\Users\ErmannoLoCascio\Desktop\eScience - Mopo\spine_projects\Simple Tutorial 2"
        self.project_load_requested.emit(path_to_project)

    @Slot()
    def open_tutorial3(self):
        path_to_project = "C:\\Users\ErmannoLoCascio\Desktop\eScience - Mopo\spine_projects\Simple Tutorial 3"
        self.project_load_requested.emit(path_to_project)

    @Slot()
    def open_tutorial4(self):
        path_to_project = "C:\\Users\ErmannoLoCascio\Desktop\eScience - Mopo\spine_projects\Simple Tutorial 4"
        self.project_load_requested.emit(path_to_project)

    @Slot()
    def open_tutorial5(self):
        path_to_project = "C:\\Users\ErmannoLoCascio\Desktop\eScience - Mopo\spine_projects\Simple Tutorial 5"
        self.project_load_requested.emit(path_to_project)
