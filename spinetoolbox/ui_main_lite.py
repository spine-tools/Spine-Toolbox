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
from PySide6.QtCore import Qt, Slot, QRect
from PySide6.QtWidgets import QMainWindow, QToolBar, QMenu, QComboBox, QProgressBar
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPainterPath, QTransform


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
        self.groups_model = QStandardItemModel()
        self.groups_combobox = QComboBox(self)
        self.groups_combobox.setModel(self.groups_model)
        self.progress_bar = QProgressBar(self)
        self.toolbar = self.make_toolbar()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.ui.graphicsView.set_ui(self)
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

    @property
    def active_ui_mode(self):
        return self.toolboxuibase.active_ui_mode

    @property
    def msg(self):
        return self.toolboxui.msg

    @property
    def msg_success(self):
        return self.toolboxui.msg_success

    @property
    def msg_error(self):
        return self.toolboxui.msg_error

    @property
    def msg_warning(self):
        return self.toolboxui.msg_warning

    @property
    def msg_proc(self):
        return self.toolboxui.msg_proc

    @property
    def msg_proc_error(self):
        return self.toolboxui.msg_proc_error

    def make_menubar(self):
        """Populates File and Help menus."""
        self.ui.menuFile.addAction(self.toolboxui.ui.actionOpen)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionOpen_recent)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionSave)
        self.ui.menuFile.addAction(self.toolboxui.ui.actionSave_As)
        self.ui.menuFile.addSeparator()
        self.ui.menuFile.addAction(self.ui.actionSwitch_to_design_mode)
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
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        tb.addAction(self.ui.actionExecute_group)
        tb.addWidget(self.groups_combobox)
        tb.addAction(self.ui.actionStop)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        tb.addWidget(self.progress_bar)
        tb.addSeparator()
        tb.addAction(self.ui.actionShow_event_log_console)
        tb.addAction(self.ui.actionSwitch_to_design_mode)
        return tb

    def connect_signals(self):
        """Connects signals to slots."""
        self.msg.connect(self.add_message)
        self.msg_success.connect(self.add_success_message)
        self.msg_error.connect(self.add_error_message)
        self.msg_warning.connect(self.add_warning_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_proc_error.connect(self.add_process_error_message)
        self.ui.actionExecute_group.triggered.connect(self.execute_group)
        self.ui.actionStop.triggered.connect(self.toolboxui._stop_execution)
        self.ui.actionShow_event_log_console.triggered.connect(self.show_event_log_and_console)
        self.ui.actionSwitch_to_design_mode.triggered.connect(self.switch_to_design_mode)
        self.groups_combobox.currentTextChanged.connect(self._select_group)

    def connect_project_signals(self):
        if not self.project:
            return
        self.project.project_execution_about_to_start.connect(lambda: self.progress_bar.reset())
        self.project.project_execution_finished.connect(self._set_progress_bar_finished)
        self.project.item_added.connect(self.toolboxui.set_icon_and_properties_ui)
        self.project.item_added.connect(self.ui.graphicsView.add_icon)
        self.project.connection_established.connect(self.ui.graphicsView.do_add_link)
        self.project.connection_updated.connect(self.ui.graphicsView.do_update_link)
        self.project.connection_about_to_be_removed.connect(self.ui.graphicsView.do_remove_link)
        self.project.jump_added.connect(self.ui.graphicsView.do_add_jump)
        self.project.jump_about_to_be_removed.connect(self.ui.graphicsView.do_remove_jump)
        self.project.group_added.connect(self.ui.graphicsView.add_group_on_scene)
        self.project.group_disbanded.connect(self.ui.graphicsView.remove_group_from_scene)

    def disconnect_project_signals(self):
        """Disconnects signals emitted by project."""
        if not self.project:
            return
        self.project.project_execution_about_to_start.disconnect()
        self.project.project_execution_finished.disconnect()
        self.project.item_added.disconnect()
        self.project.connection_established.disconnect()
        self.project.connection_updated.disconnect()
        self.project.connection_about_to_be_removed.disconnect()
        self.project.jump_added.disconnect()
        self.project.jump_about_to_be_removed.disconnect()
        self.project.group_added.disconnect()
        self.project.group_disbanded.disconnect()

    def switch_to_design_mode(self):
        """Switches the main window into design mode."""
        self.ui.graphicsView.scene().clearSelection()
        self.disconnect_project_signals()
        self.ui.graphicsView.scene().clear_icons_and_links()
        self.toolboxuibase.ui.stackedWidget.setCurrentWidget(self.toolboxui)
        self.toolboxuibase.reload_icons_and_links()
        self.toolboxuibase.active_ui_mode = "toolboxui"
        self.toolboxui.connect_project_signals()
        self.toolboxui.ui.graphicsView.reset_zoom()

    def populate_groups_model(self):
        """Populates group model."""
        items = [self.groups_model.item(i).text() for i in range(self.groups_model.rowCount())]
        if "Select a group..." not in items:
            i1 = QStandardItem("Select a group...")
            self.groups_model.appendRow(i1)
        if "All" not in items:
            i2 = QStandardItem("All")
            self.groups_model.appendRow(i2)
        for group_name, group in self.project.groups.items():
            if group_name not in items:
                item = QStandardItem(group_name)
                item.setData(group, Qt.ItemDataRole.UserRole)
                self.groups_model.appendRow(item)

    @Slot(str)
    def _select_group(self, group_name):
        """Selects a group with the given name."""
        self.ui.graphicsView.scene().clearSelection()
        if group_name == "Select a group...":
            return
        if group_name == "All":
            path = QPainterPath()
            path.addRect(self.ui.graphicsView.scene().sceneRect())
            self.ui.graphicsView.scene().setSelectionArea(path, QTransform())
            return
        group = self.project.groups[group_name]
        path = QPainterPath()
        path.addRect(group.rect())
        self.ui.graphicsView.scene().setSelectionArea(path, QTransform())

    def execute_group(self):
        """Executes a group."""
        if self.groups_combobox.currentIndex() == 0:
            return
        if self.groups_combobox.currentText() == "All":
            self.toolboxui._execute_project()
            return
        self.toolboxui._execute_selection()

    @Slot()
    def _set_progress_bar_finished(self):
        self.progress_bar.setValue(self.progress_bar.maximum())

    def show_event_log_and_console(self):
        print("Not implemented")

    def refresh_active_elements(self, active_project_item, active_link_item, selected_item_names):
        """Does something when scene selection has changed."""
        self.toolboxui._selected_item_names = selected_item_names

    def override_console_and_execution_list(self):
        """Does nothing."""
        return True

    def show_project_or_item_context_menu(self, global_pos, item):
        """Shows the Context menu for project or item in user mode."""
        print(f"Not implemented yet. item:{item}")

    def show_link_context_menu(self, pos, link):
        """Shows the Context menu for connection links in user mode.

        Args:
            pos (QPoint): Mouse position
            link (Link(QGraphicsPathItem)): The link in question
        """
        menu = QMenu(self)
        menu.addAction(self.toolboxui.ui.actionTake_link)
        action = menu.exec(pos)
        if action is self.toolboxui.ui.actionTake_link:
            self.ui.graphicsView.take_link(link)
        menu.deleteLater()

    @Slot(str)
    def add_message(self, msg):
        """Appends a regular message to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        return

    @Slot(str)
    def add_success_message(self, msg):
        """Appends a message with green text to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        return

    @Slot(str)
    def add_error_message(self, msg):
        """Appends a message with red color to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        print(f"[ERROR]:{msg}")

    @Slot(str)
    def add_warning_message(self, msg):
        """Appends a message with yellow (golden) color to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        print(f"[WARNING]:{msg}")

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        return

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to the Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        return
