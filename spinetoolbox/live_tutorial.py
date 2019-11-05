######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the GraphViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

from PySide2.QtCore import Qt, Slot, QStateMachine, QFinalState, QState
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDockWidget, QWidget
from .widgets.custom_qwidgets import OverlayWidget
from .widgets.toolbars import DraggableWidget


class LiveTutorial(QDockWidget):
    """A widget that shows a tutorial for Spine Toolbox."""

    def __init__(self, toolbox):
        """Initializes class.

        Args:
            toolbox (ToolboxUI)
        """
        super().__init__("Live tutorial", toolbox)
        self.setObjectName("Live tutorial")
        self.label_msg = QLabel(self)
        self.label_msg.setFont(QFont("arial,helvetica", 12))
        self.label_msg.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.label_msg.setWordWrap(True)
        self.button_right = QPushButton(self)
        self.button_left = QPushButton(self)
        button_container = QWidget(self)
        button_layout = QHBoxLayout(button_container)
        button_layout.addStretch()
        button_layout.addWidget(self.button_right)
        button_layout.addWidget(self.button_left)
        button_layout.addStretch()
        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.addStretch()
        layout.addWidget(self.label_msg)
        layout.addStretch()
        layout.addWidget(button_container)
        self.setWidget(widget)
        self.overlay1 = OverlayWidget(color=QColor(255, 0, 0, 128))
        self.overlay2 = OverlayWidget(color=QColor(255, 0, 0, 128))
        self.hide()
        self.machine = None
        self.run = None

    def show(self):
        self.setFloating(False)
        self.parent().addDockWidget(Qt.TopDockWidgetArea, self)
        self.setup()
        super().show()

    def _make_welcome(self):
        welcome = QState(self.run)
        begin = QState(welcome)
        finalize = QFinalState(welcome)
        welcome.setInitialState(begin)
        begin.assignProperty(self.label_msg, "text", "Welcome!")
        begin.assignProperty(self.button_right, "text", "Start")
        begin.assignProperty(self.button_right, "visible", True)
        begin.assignProperty(self.button_left, "visible", False)
        begin.addTransition(self.button_right.clicked, finalize)
        return welcome

    def _make_create_project(self):
        create_project = QState(self.run)
        open_file_menu = QState(create_project)
        select_new_project = QState(create_project)
        name_project = QState(create_project)
        finalize = QFinalState(create_project)

        open_file_menu.assignProperty(self.button_right, "visible", False)
        text = """
            <html><p>Let's start by creating a project.</p>
            <p>Press <b>Ctrl+N</b>, or select <b>File, New project...</b> from the main menu.</p>
            </html>
        """
        open_file_menu.assignProperty(self.label_msg, "text", text)
        menubar = self.parent().ui.menubar
        menu_file = self.parent().ui.menuFile
        open_file_menu.assignProperty(self.overlay1, "target", menubar)
        open_file_menu.assignProperty(self.overlay1, "rectangle", menubar.actionGeometry(menu_file.menuAction()))

        action_new = self.parent().ui.actionNew
        select_new_project.assignProperty(self.overlay1, "target", menu_file)
        select_new_project.assignProperty(self.overlay1, "rectangle", menu_file.actionGeometry(action_new))

        text = """
            <html><p>Give the new project a name, and press <b>Ok</b>.</p>
            </html>
        """
        name_project.assignProperty(self.label_msg, "text", text)
        name_project.assignProperty(self.overlay1, "target", None)

        create_project.setInitialState(open_file_menu)
        open_file_menu.addTransition(menu_file.aboutToShow, select_new_project)
        open_file_menu.addTransition(self.parent().ui.actionNew.triggered, name_project)
        select_new_project.addTransition(self.parent().ui.actionNew.triggered, name_project)
        name_project.addTransition(self.parent().windowTitleChanged, finalize)
        return create_project

    def _make_drop_icon_state(self, item_type, parent_state):
        category = {"Data Connection": "Data Connections", "Importer": "Importers"}[item_type]
        text = f"""
            <html><p>Let's add a {item_type} to our project.</p>
            <p>See the {item_type} icon in the toolbar (the one marked in red)?
            Drag and drop that icon onto the design view now.</p>
            </html>
        """
        state = QState(parent_state)
        state.assignProperty(self.label_msg, "text", text)
        state.assignProperty(self.button_right, "visible", False)
        state.assignProperty(self.parent().item_toolbar, "visible", True)
        for wg in self.parent().item_toolbar.findChildren(DraggableWidget):
            if wg.category == category:
                state.assignProperty(self.overlay1, "target", wg)
                state.assignProperty(wg, "enabled", True)
            else:
                state.assignProperty(wg, "enabled", False)
        state.assignProperty(self.overlay2, "target", self.parent().ui.graphicsView)
        return state

    def _make_add_item(self, item_type):
        add_item = QState(self.run)
        drop_icon = self._make_drop_icon_state(item_type, add_item)
        name_item = QState(add_item)
        finalize = QFinalState(add_item)
        text = f"""
            <html><p>Perfect!</p>
            <p>Give the {item_type} a name, and press <b>Ok</b>.</p>
            </html>
        """
        name_item.assignProperty(self.label_msg, "text", text)
        name_item.assignProperty(self.overlay1, "visible", False)
        name_item.assignProperty(self.overlay2, "visible", False)

        add_item.setInitialState(drop_icon)
        drop_icon.addTransition(self.parent().project_item_added, name_item)
        name_item.addTransition(self.parent().msg, finalize)
        return add_item

    def _make_open_dc_files(self):
        open_dc_files = QState(self.run)
        begin = QState(open_dc_files)
        finalize = QFinalState(open_dc_files)
        begin.entered.connect(self._create_dc_files)
        text = """
            <html><p>Good job!</p>
            <p>Now checkout the Data Connection references list. 
            Here you can include data files that you want to use in your project.
            <p>I've included a few ones for you. 
            Double click on one of them to open it in your registered program.</p>
            </html>
        """
        begin.assignProperty(self.label_msg, "text", text)
        begin.assignProperty(self.overlay1, "visible", True)
        properties_ui = self.parent().categories["Data Connections"]["properties_ui"]
        begin.assignProperty(self.parent().ui.dockWidget_item, "visible", True)
        begin.assignProperty(self.overlay1, "target", properties_ui.treeView_dc_references)
        begin.assignProperty(self.overlay1, "rectangle", None)

        open_dc_files.setInitialState(begin)
        begin.addTransition(properties_ui.treeView_dc_references.doubleClicked, finalize)
        return open_dc_files

    def setup(self):
        self.machine = QStateMachine(self)
        self.run = QState(self.machine)
        abort = self._make_abort()
        self.run.addTransition(self.visibilityChanged, abort)
        welcome = self._make_welcome()
        welcome.entered.connect(self._handle_welcome_entered)
        self.machine.setInitialState(self.run)
        self.run.setInitialState(welcome)
        self.machine.start()

    def _make_abort(self):
        abort = QState(self.run)
        dead = QFinalState(self.machine)
        for wg in self.parent().item_toolbar.findChildren(DraggableWidget):
            abort.assignProperty(wg, "enabled", True)
        abort.addTransition(dead)
        return abort

    def _handle_welcome_entered(self):
        welcome = self.sender()
        create_project = self._make_create_project()
        welcome.addTransition(welcome.finished, create_project)
        create_project.entered.connect(self._handle_create_project_entered)

    def _handle_create_project_entered(self):
        create_project = self.sender()
        add_dc = self._make_add_item("Data Connection")
        create_project.addTransition(create_project.finished, add_dc)
        add_dc.entered.connect(self._handle_add_dc_entered)

    def _handle_add_dc_entered(self):
        add_dc = self.sender()
        open_dc_files = self._make_open_dc_files()
        add_dc.addTransition(add_dc.finished, open_dc_files)
        open_dc_files.entered.connect(self._handle_open_dc_files_entered)

    def _handle_open_dc_files_entered(self):
        open_dc_files = self.sender()
        add_importer = self._make_add_item("Importer")
        open_dc_files.addTransition(open_dc_files.finished, add_importer)

    @Slot()
    def _create_dc_files(self):
        print(self.parent()._project)
