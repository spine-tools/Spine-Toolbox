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

"""Contains a class for the base main window of Spine Toolbox."""
import sys
import locale
from PySide6.QtCore import QSettings, Qt, Slot, Signal
from PySide6.QtWidgets import QMainWindow, QApplication, QStyleFactory, QMessageBox, QCheckBox
from PySide6.QtGui import QIcon, QUndoStack, QGuiApplication, QAction, QKeySequence
from .helpers import set_taskbar_icon, ensure_window_is_on_screen
from .ui_main import ToolboxUI
from .ui_main_lite import ToolboxUILite
from .link import JumpOrLink


class ToolboxUIBase(QMainWindow):
    """Class for the actual app main window."""

    def __init__(self):
        """Initializes top main window."""
        from .ui.mainwindowbase import Ui_MainWindowBase  # pylint: disable=import-outside-toplevel

        super().__init__(flags=Qt.WindowType.Window)
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.ui = Ui_MainWindowBase()
        self.ui.setupUi(self)
        self.show_nr_of_items = QAction(self)
        self.show_nr_of_items.setShortcut(QKeySequence(Qt.Modifier.CTRL.value | Qt.Key.Key_7.value))
        self.addAction(self.show_nr_of_items)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        set_taskbar_icon()
        self._set_app_style()
        self._set_error_mode()
        self._qsettings = QSettings("SpineProject", "Spine Toolbox", self)
        self._undo_stack = QUndoStack(self)
        self._toolboxui = ToolboxUI(self)
        self._toolboxui_lite = ToolboxUILite(self)
        self.ui.stackedWidget.addWidget(self.toolboxui)
        self.ui.stackedWidget.addWidget(self.toolboxui_lite)
        self.ui.stackedWidget.setCurrentWidget(self.toolboxui)
        self.show_datetime = self.update_datetime()
        self.restore_ui()
        self.connect_signals()
        self._active_ui_mode = "toolboxui"

    @property
    def toolboxui(self):
        return self._toolboxui

    @property
    def toolboxui_lite(self):
        return self._toolboxui_lite

    @property
    def qsettings(self):
        return self._qsettings

    @property
    def project(self):
        return self.toolboxui.project

    @property
    def undo_stack(self):
        return self._undo_stack

    @property
    def active_ui_window(self):
        return self.ui.stackedWidget.currentWidget()

    @property
    def active_ui_mode(self):
        return self._active_ui_mode

    @active_ui_mode.setter
    def active_ui_mode(self, tb):
        self._active_ui_mode = tb

    def connect_signals(self):
        """Connects signals to slots."""
        self.undo_stack.cleanChanged.connect(self.update_window_modified)
        self.show_nr_of_items.triggered.connect(self.nr_of_items)

    @staticmethod
    def _set_app_style():
        """Sets app style on Windows to 'windowsvista' or to a default if not available."""
        if sys.platform == "win32":
            if "windowsvista" not in QStyleFactory.keys():
                return
            QApplication.setStyle("windowsvista")

    @staticmethod
    def _set_error_mode():
        """Sets Windows error mode to show all error dialog boxes from subprocesses.

        See https://docs.microsoft.com/en-us/windows/win32/api/errhandlingapi/nf-errhandlingapi-seterrormode
        for documentation.
        """
        if sys.platform == "win32":
            import ctypes  # pylint: disable=import-outside-toplevel

            ctypes.windll.kernel32.SetErrorMode(0)

    def update_window_title(self):
        """Updates main window title."""
        if not self.project:
            self.setWindowTitle("Spine Toolbox")
            return
        self.setWindowTitle(f"{self.project.name} [{self.project.project_dir}][*] - Spine Toolbox")

    @Slot(bool)
    def update_window_modified(self, clean):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        self.setWindowModified(not clean)
        self.toolboxui.ui.actionSave.setDisabled(clean)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize", defaultValue="false")
        window_pos = self.qsettings.value("mainWindow/windowPosition", defaultValue="false")
        window_state = self.qsettings.value("mainWindow/windowState", defaultValue="false")
        window_state_lite = self.qsettings.value("mainWindowLite/windowState", defaultValue="false")
        hz_splitter = self.qsettings.value("mainWindowLite/horizontalSplitter", defaultValue="false")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue="false")  # returns str
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)  # number of screens on last exit
        # noinspection PyArgumentList
        n_screens_now = len(QGuiApplication.screens())  # Number of screens now
        original_size = self.size()
        # Note: cannot use booleans since Windows saves them as strings to registry
        if window_size != "false":
            self.resize(window_size)  # Expects QSize
        else:
            self.resize(1024, 800)
        if window_pos != "false":
            self.move(window_pos)  # Expects QPoint
        if window_state != "false":
            self.toolboxui.restoreState(window_state, version=1)  # Toolbar and dockWidget positions [QByteArray]
        if window_state_lite != "false":
            self.toolboxui_lite.restoreState(window_state_lite, version=1)
        if hz_splitter != "false":
            self.toolboxui_lite.ui.splitter.restoreState(hz_splitter)  # Splitter position
        if n_screens_now < int(n_screens):
            # There are less screens available now than on previous application startup
            # Move main window to position 0,0 to make sure that it is not lost on another screen that does not exist
            self.move(0, 0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == "true":
            self.setWindowState(Qt.WindowState.WindowMaximized)

    def reload_icons_and_links(self):
        """Reloads item icons and links on Design View when UI mode is changed."""
        if not self.project:
            return
        for item_name in self.project.all_item_names:
            self.active_ui_window.ui.graphicsView.add_icon(item_name)
        for connection in self.project.connections:
            self.active_ui_window.ui.graphicsView.do_add_link(connection)
            connection.link.update_icons()
        for jump in self.project.jumps:
            self.active_ui_window.ui.graphicsView.do_add_jump(jump)
            jump.jump_link.update_icons()
        for group in self.project.groups.values():
            self.active_ui_window.ui.graphicsView.add_group_on_scene(group)
            # TODO:
            # Remove all links from Groups. items contains wrong link icon references
            # Then find the new links from the scene and add them back to the group and to the links my_groups
            # ex_items = [for item in]
            # for item in group.items:
            #     if isinstance(item, JumpOrLink):
            #         print(item.name)
            #         item.my_groups.add(group)

    def connect_project_signals(self):
        """Connects project signals based on current UI mode."""
        self.active_ui_window.connect_project_signals()

    def clear_ui(self):
        """Clean UI to make room for a new or opened project."""
        self.toolboxui.activate_no_selection_tab()  # Clear properties widget
        self.toolboxui._restore_original_console()
        self.active_ui_window.ui.graphicsView.scene().clear_icons_and_links()  # Clear all items from scene
        self.toolboxui._shutdown_engine_kernels()
        self.toolboxui._close_consoles()

    def update_datetime(self):
        """Returns a boolean, which determines whether
        date and time is prepended to every Event Log message."""
        d = int(self.qsettings.value("appSettings/dateTime", defaultValue="2"))
        return d != 0

    def _tasks_before_exit(self):
        """Returns a list of tasks to perform before exiting the application.

        Possible tasks are:

        - `"prompt exit"`: prompt user if quitting is really desired
        - `"prompt save"`: prompt user if project should be saved before quitting
        - `"save"`: save project before quitting

        Returns:
            list: Zero or more tasks in a list
        """
        save_at_exit = (
            self.qsettings.value("appSettings/saveAtExit", defaultValue="prompt")
            if self.project is not None and not self.undo_stack.isClean()
            else None
        )
        if save_at_exit == "prompt":
            return ["prompt save"]
        show_confirm_exit = int(self.qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        tasks = []
        if show_confirm_exit == 2:
            tasks.append("prompt exit")
        if save_at_exit == "automatic":
            tasks.append("save")
        return tasks

    def _perform_pre_exit_tasks(self):
        """Prompts user to confirm quitting and saves the project if necessary.

        Returns:
            bool: True if exit should proceed, False if the process was cancelled
        """
        tasks = self._tasks_before_exit()
        for task in tasks:
            if task == "prompt exit":
                if not self._confirm_exit():
                    return False
            elif task == "prompt save":
                if not self._confirm_project_close():
                    return False
            elif task == "save":
                self.toolboxui.save_project()
        return True

    def _confirm_exit(self):
        """Confirms exiting from user.

        Returns:
            bool: True if exit should proceed, False if user cancelled
        """
        msg = QMessageBox(parent=self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Confirm exit")
        msg.setText("Are you sure you want to exit Spine Toolbox?")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msg.button(QMessageBox.StandardButton.Ok).setText("Exit")
        chkbox = QCheckBox()
        chkbox.setText("Do not ask me again")
        msg.setCheckBox(chkbox)
        answer = msg.exec()  # Show message box
        if answer == QMessageBox.StandardButton.Ok:
            # Update conf file according to checkbox status
            if not chkbox.isChecked():
                show_prompt = "2"  # 2 as in True
            else:
                show_prompt = "0"  # 0 as in False
            self.qsettings.setValue("appSettings/showExitPrompt", show_prompt)
            return True
        return False

    def _confirm_project_close(self):
        """Confirms exit from user and saves the project if requested.

        Returns:
            bool: True if exiting should proceed, False if user cancelled
        """
        msg = QMessageBox(parent=self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Confirm project close")
        msg.setText("Current project has unsaved changes.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        answer = msg.exec()
        if answer == QMessageBox.StandardButton.Cancel:
            return False
        if answer == QMessageBox.StandardButton.Save:
            self.toolboxui.save_project()
        return True

    def closeEvent(self, event):
        """Method for handling application exit event.

        Args:
             event (QCloseEvent): PySide6 event
        """
        # Show confirm exit message box
        exit_confirmed = self._perform_pre_exit_tasks()
        if not exit_confirmed:
            event.ignore()
            return
        if not self.toolboxui.undo_critical_commands():
            event.ignore()
            return
        # Save settings
        if self.project is None:
            self.qsettings.setValue("appSettings/previousProject", "")
        else:
            self.qsettings.setValue("appSettings/previousProject", self.project.project_dir)
            self.toolboxui.update_recent_projects()
        self.qsettings.setValue("appSettings/toolbarIconOrdering", self.toolboxui.items_toolbar.icon_ordering())
        self.qsettings.setValue("mainWindow/windowSize", self.size())
        self.qsettings.setValue("mainWindow/windowPosition", self.pos())
        self.qsettings.setValue("mainWindow/windowState", self.toolboxui.saveState(version=1))
        self.qsettings.setValue("mainWindow/windowMaximized", self.windowState() == Qt.WindowState.WindowMaximized)
        # ToolboxUI Lite settings
        self.qsettings.setValue("mainWindowLite/windowState", self.toolboxui_lite.saveState(version=1))
        self.qsettings.setValue("mainWindowLite/horizontalSplitter", self.toolboxui_lite.ui.splitter.saveState())
        # Save number of screens
        self.qsettings.setValue("mainWindow/n_screens", len(QGuiApplication.screens()))
        self.toolboxui._shutdown_engine_kernels()
        self.toolboxui._close_consoles()
        if self.project is not None:
            self.project.tear_down()
        for item_type in self.toolboxui.item_factories:
            for editor in self.toolboxui.get_all_multi_tab_spec_editors(item_type):
                editor.close()
        event.accept()

    def nr_of_items(self):
        """For debugging."""
        n_items = len(self.active_ui_window.ui.graphicsView.scene().items())
        print(f"Items on scene:{n_items}")

