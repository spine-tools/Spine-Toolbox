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

"""Contains a class for the user mode main window of Spine Toolbox."""
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QMainWindow, QToolBar
from .project_item_icon import ProjectItemIcon
from .link import JumpOrLink


class ToolboxUILite(QMainWindow):
    """Class for the user mode main window functions."""

    def __init__(self, toolboxuibase):
        """Initializes application and main window."""
        from .ui.mainwindowlite import Ui_MainWindowLite  # pylint: disable=import-outside-toplevel

        super().__init__(parent=toolboxuibase, flags=Qt.WindowType.Window)
        self.toolboxuibase = toolboxuibase
        self.ui = Ui_MainWindowLite()
        self.ui.setupUi(self)
        self.make_menubar()
        self.ui.graphicsView.set_ui(self)
        # self.ui.toolButton_execute_project.setDefaultAction(self.ui.actionExecute_project)
        self.ui.toolButton_execute_group.setDefaultAction(self.ui.actionExecute_group)
        self.ui.toolButton_stop.setDefaultAction(self.ui.actionStop)
        self.ui.toolButton_to_expert_mode.setDefaultAction(self.ui.actionSwitch_to_expert_mode)
        self.ui.toolButton_show_event_log.setDefaultAction(self.ui.actionShow_event_log_console)
        self.ui.comboBox_groups.addItems(["All", "Group 1", "Group 2", "Group 3"])
        # self.toolbar = self.make_toolbar()
        self.connect_signals()

    @property
    def toolboxui(self):
        return self.toolboxuibase.toolboxui

    @property
    def qsettings(self):
        return self.toolboxuibase.qsettings

    @property
    def project(self):
        return self.toolboxui.project

    @property
    def undo_stack(self):
        return self.toolboxuibase.undo_stack

    def make_menubar(self):
        """Populates File and Help menus."""
        self.ui.menuFile.addAction(self.toolboxui.ui.actionOpen)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionOpen_recent)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionSave)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionSave_As)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionSwitch_to_expert_mode)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionSettings)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.toolboxui.ui.actionQuit)
        self.ui.menuHelp.addAction(self.toolboxui.ui.actionUser_Guide)
        self.ui.menuHelp.addAction(self.toolboxui.ui.actionGitHub)
        self.ui.menuHelp.addSeparator()
        self.ui.menuHelp.addAction(self.toolboxui.ui.actionAbout_Qt)
        self.ui.menuHelp.addAction(self.toolboxui.ui.actionAbout)

    def make_toolbar(self):
        """Makes and returns a Toolbar for user mode UI."""
        tb = QToolBar(self)
        tb.addAction(self.toolboxui.ui.actionExecute_project)
        return tb

    def connect_signals(self):
        """Connects signals to slots."""
        self.ui.actionSwitch_to_expert_mode.triggered.connect(self.switch_to_expert_mode)
        # self.ui.actionExecute_project.triggered.connect(self.toolboxui._execute_project)
        self.ui.actionExecute_group.triggered.connect(self.execute_group)
        self.ui.actionStop.triggered.connect(self.toolboxui._stop_execution)

    def connect_project_signals(self):
        if not self.project:
            return
        self.project.item_added.connect(self.toolboxui.set_icon_and_properties_ui)
        self.project.item_added.connect(self.ui.graphicsView.add_icon)
        self.project.connection_established.connect(self.ui.graphicsView.do_add_link)
        self.project.connection_updated.connect(self.ui.graphicsView.do_update_link)
        self.project.connection_about_to_be_removed.connect(self.ui.graphicsView.do_remove_link)
        self.project.jump_added.connect(self.ui.graphicsView.do_add_jump)
        self.project.jump_about_to_be_removed.connect(self.ui.graphicsView.do_remove_jump)

    def disconnect_project_signals(self):
        """Disconnects signals emitted by project."""
        if not self.project:
            return
        self.project.item_added.disconnect()
        self.project.connection_established.disconnect()
        self.project.connection_updated.disconnect()
        self.project.connection_about_to_be_removed.disconnect()
        self.project.jump_added.disconnect()
        self.project.jump_about_to_be_removed.disconnect()

    def switch_to_expert_mode(self):
        """Switches the main window into expert mode."""
        self.disconnect_project_signals()
        self.ui.graphicsView.scene().clear_icons_and_links()
        self.toolboxuibase.ui.stackedWidget.setCurrentWidget(self.toolboxui)
        self.toolboxuibase.reload_icons_and_links()
        self.toolboxui.connect_project_signals()
        self.toolboxui.ui.graphicsView.reset_zoom()

    def execute_group(self):
        if self.ui.comboBox_groups.currentText() == "All":
            for i in self.ui.graphicsView.scene().items():
                if isinstance(i, ProjectItemIcon) or isinstance(i, JumpOrLink):
                    i.setSelected(True)
            self.toolboxui._execute_project()
            return
        print(f"Executing {self.ui.comboBox_groups.currentText()}")

    def open_project(self):
        """Slot for opening projects in user mode."""

    def refresh_active_elements(self, active_project_item, active_link_item, selected_item_names):
        """Does something when scene selection has changed."""
        return True

    def override_console_and_execution_list(self):
        """Does nothing."""
        return True
