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
from PySide6.QtWidgets import QListWidgetItem
import webbrowser


class StartupBoxWidget(QWidget):
    project_load_requested = Signal(str)
    project_opener = Signal(str)
    recent_projects = Signal(str)
    new_project_opener = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent, f=Qt.WindowType.Window)
        self._ui = Ui_Form()
        self._ui.setupUi(self)




        # Connect the clicked signal of open project button
        self._ui.pushButton_8.clicked.connect(self.open_project_startbox)

        # Connect the clicked signal of open project button
        self._ui.pushButton_9.clicked.connect(self.open_new_project_startbox)

        # Connect the signal of recent projects
        self.open_recent()

        # Connect the clicked signal of each button to a specific slot
        self._ui.pushButton_3.clicked.connect(self.open_tutorial1)
        self._ui.pushButton_7.clicked.connect(self.open_tutorial5)

        # Connect the clicked button to open the link1
        self._ui.pushButton.clicked.connect(self.open_link1)

        # Connect the clicked button to open the link2
        self._ui.pushButton_2.clicked.connect(self.open_link2)

        # Connect the clicked button to open the link3
        self._ui.pushButton_4.clicked.connect(self.open_link3)

        # Connect the clicked button to open the link4
        self._ui.pushButton_5.clicked.connect(self.open_link4)

    def set_changelog_diff(self, diff_list):
        # Add diff_list items to listWidget_2
        for item in diff_list:
            self._ui.listWidget_2.addItem(item)



    @Slot()
    def open_project_startbox(self):
        # Execute the open_project function in the ui_main.py
        self.project_opener.emit(self)

    def open_new_project_startbox(self):
        # Execute the open_project function in the ui_main.py
        self.new_project_opener.emit(self)



    def open_recent(self):
        # Access qsettings from the parent object
        recents = self.parent().qsettings().value("appSettings/recentProjects", defaultValue=None)
        if recents:
            recents = str(recents)
            recents_list = recents.split("\n")
            for entry in recents_list:
                name, filepath = entry.split("<>")
                # Add only the name to the list widget
                item = QListWidgetItem(name)
                self._ui.listWidget.addItem(item)

                # Storing filepath as an attribute of the item
                item.filepath = filepath
                # Storing filepath as data
                item.setData(Qt.UserRole, filepath)

        # Connect the itemClicked signal to the open_selected_tutorial function
        self._ui.listWidget.itemClicked.connect(self.open_selected_tutorial)

    @Slot()
    def open_selected_tutorial(self):
        item = self._ui.listWidget.currentItem()
        path = item.data(Qt.UserRole)
        self.project_load_requested.emit(path)



    def open_link1(self):
        print("Open link")
        webbrowser.open_new_tab("https://spine-toolbox.readthedocs.io/en/latest/getting_started.html")

    def open_link2(self):
        print("Open link")
        webbrowser.open_new_tab("https://github.com/energy-modelling-workbench/spine-data-model#spine-data-model")

    def open_link3(self):
        print("Open link")
        webbrowser.open_new_tab("https://spine-toolbox.readthedocs.io/en/latest/getting_started.html#adding-a-data-connection-item-to-the-project")

    def open_link4(self):
        print("Open link")
        webbrowser.open_new_tab("https://spine-toolbox.readthedocs.io/en/latest/executing_projects.html")



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