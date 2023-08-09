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

"""
Contains ToolboxUI class.
"""

import os
import sys
import locale
import logging
import json
import pathlib
from zipfile import ZipFile
import numpy as np
from PySide6.QtCore import (
    QByteArray,
    QItemSelection,
    QMimeData,
    QModelIndex,
    QPoint,
    Qt,
    Signal,
    Slot,
    QSettings,
    QUrl,
    QEvent,
)
from PySide6.QtGui import QDesktopServices, QGuiApplication, QKeySequence, QIcon, QCursor, QWindow, QAction, QUndoStack
from PySide6.QtWidgets import (
    QMainWindow,
    QApplication,
    QErrorMessage,
    QFileDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
    QCheckBox,
    QDockWidget,
    QWidget,
    QLabel,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QHBoxLayout,
)
from spine_engine.load_project_items import load_item_specification_factories
from spine_items.category import CATEGORIES, CATEGORY_DESCRIPTIONS
from .project_item_icon import ProjectItemIcon
from .load_project_items import load_project_items
from .mvcmodels.project_tree_item import CategoryProjectTreeItem, RootProjectTreeItem
from .mvcmodels.project_item_model import ProjectItemModel
from .mvcmodels.project_item_specification_models import ProjectItemSpecificationModel, FilteredSpecificationModel
from .mvcmodels.filter_execution_model import FilterExecutionModel
from .project_settings import ProjectSettings
from .widgets.set_description_dialog import SetDescriptionDialog
from .widgets.multi_tab_spec_editor import MultiTabSpecEditor
from .widgets.about_widget import AboutWidget
from .widgets.custom_menus import RecentProjectsPopupMenu, KernelsPopupMenu
from .widgets.settings_widget import SettingsWidget
from .widgets.custom_qwidgets import ToolBarWidgetAction
from .widgets.jupyter_console_widget import JupyterConsoleWidget
from .widgets.persistent_console_widget import PersistentConsoleWidget
from .widgets import toolbars
from .widgets.open_project_widget import OpenProjectDialog
from .widgets.jump_properties_widget import JumpPropertiesWidget
from .widgets.link_properties_widget import LinkPropertiesWidget
from .project import SpineToolboxProject
from .spine_db_manager import SpineDBManager
from .spine_db_editor.widgets.multi_spine_db_editor import MultiSpineDBEditor
from .spine_engine_manager import make_engine_manager
from .config import MAINWINDOW_SS, DEFAULT_WORK_DIR, ONLINE_DOCUMENTATION_URL
from .helpers import (
    create_dir,
    ensure_window_is_on_screen,
    set_taskbar_icon,
    supported_img_formats,
    recursive_overwrite,
    ChildCyclingKeyPressFilter,
    open_url,
    busy_effect,
    format_log_message,
    color_from_index,
    load_specification_from_file,
    load_specification_local_data,
    same_path,
    solve_connection_file,
    unique_name,
)
from .project_commands import (
    AddSpecificationCommand,
    ReplaceSpecificationCommand,
    RemoveSpecificationCommand,
    RenameProjectItemCommand,
    SpineToolboxCommand,
    SaveSpecificationAsCommand,
    AddProjectItemsCommand,
    RemoveAllProjectItemsCommand,
    RemoveProjectItemsCommand,
)
from .plugin_manager import PluginManager
from .link import JumpLink, Link, LINK_COLOR, JUMP_COLOR
from .project_item.logging_connection import LoggingConnection, LoggingJump
from spinetoolbox.server.engine_client import EngineClient, RemoteEngineInitFailed, ClientSecurityModel
from .kernel_fetcher import KernelFetcher


class ToolboxUI(QMainWindow):
    """Class for application main GUI functions."""

    # Signals to comply with the spinetoolbox.logger_interface.LoggerInterface interface.
    msg = Signal(str)
    msg_success = Signal(str)
    msg_error = Signal(str)
    msg_warning = Signal(str)
    msg_proc = Signal(str)
    msg_proc_error = Signal(str)
    information_box = Signal(str, str)
    error_box = Signal(str, str)
    # The rest of the msg_* signals should be moved to LoggerInterface in the long run.
    jupyter_console_requested = Signal(object, str, str, str, dict)
    kernel_shutdown = Signal(object, str)
    persistent_console_requested = Signal(object, str, tuple, str)

    def __init__(self):
        """Initializes application and main window."""
        from .ui.mainwindow import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(flags=Qt.Window)
        self.set_error_mode()
        self._qsettings = QSettings("SpineProject", "Spine Toolbox", self)
        self._update_qsettings()
        locale.setlocale(locale.LC_NUMERIC, 'C')
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)  # Set up gui widgets from Qt Designer files
        self.label_item_name = QLabel()
        self._button_item_dir = QToolButton()
        self._properties_title = QWidget()
        self._setup_properties_title()
        self.takeCentralWidget().deleteLater()
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        set_taskbar_icon()  # in helpers.py
        self.ui.graphicsView.set_ui(self)
        self.key_press_filter = ChildCyclingKeyPressFilter(self)
        self.ui.tabWidget_item_properties.installEventFilter(self.key_press_filter)
        self._share_item_edit_actions()
        self.ui.listView_console_executions.setModel(FilterExecutionModel(self))
        # Set style sheets
        self.setStyleSheet(MAINWINDOW_SS)
        # Class variables
        self.undo_stack = QUndoStack(self)
        self._item_categories = dict()
        self._item_properties_uis = dict()
        self.item_factories = dict()  # maps item types to `ProjectItemFactory` objects
        self._item_specification_factories = dict()  # maps item types to `ProjectItemSpecificationFactory` objects
        self._project = None
        self.project_item_model = None
        self.specification_model = None
        self.filtered_spec_factory_models = {}
        self.show_datetime = self.update_datetime()
        self.active_project_item = None
        self.active_link_item = None
        self._selected_item_names = set()
        self.execution_in_progress = False
        self.sync_item_selection_with_scene = True
        self._anchor_callbacks = {}
        self.ui.textBrowser_eventlog.set_toolbox(self)
        # DB manager
        self.db_mngr = SpineDBManager(self._qsettings, self)
        # Widget and form references
        self.settings_form = None
        self.add_project_item_form = None
        self.recent_projects_menu = RecentProjectsPopupMenu(self)
        self.kernels_menu = KernelsPopupMenu(self)
        # Make and initialize toolbars
        self.main_toolbar = toolbars.MainToolBar(
            self.ui.actionExecute_project, self.ui.actionExecute_selection, self.ui.actionStop_execution, self
        )
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        self._original_execute_project_action_tooltip = self.ui.actionExecute_project.toolTip()
        self.setStatusBar(None)
        # Additional consoles for item execution
        self._item_consoles = {}  # Mapping of ProjectItem to console
        self._filter_item_consoles = {}  # (ProjectItem, {f_id_0: console_0, f_id_1:console_1, ... , f_id_n:console_n})
        self._persistent_consoles = {}  # Mapping of key to PersistentConsoleWidget
        self._jupyter_consoles = {}  # Mapping of connection file to JupyterConsoleWidget
        self._current_execution_keys = {}
        # Setup main window menu
        self.add_zoom_action()
        self.add_menu_actions()
        self.ui.menuFile.setToolTipsVisible(True)
        self.ui.menuEdit.setToolTipsVisible(True)
        self.ui.menuConsoles.setToolTipsVisible(True)
        self._add_execute_actions()
        self.kernel_fetcher = None
        # Hidden QActions for debugging or testing
        self.show_properties_tabbar = QAction(self)
        self.show_supported_img_formats = QAction(self)
        self.set_debug_qactions()
        # Finalize init
        self.ui.tabWidget_item_properties.tabBar().hide()  # Hide tab bar in properties dock widget
        self.restore_dock_widgets()
        self.restore_ui()
        self.ui.listView_console_executions.hide()
        self.ui.listView_console_executions.installEventFilter(self)
        self.parse_project_item_modules()
        self.init_project_item_model()
        self.init_specification_model()
        self.make_item_properties_uis()
        self.main_toolbar.setup()
        self.link_properties_widgets = {
            LoggingConnection: LinkPropertiesWidget(self, base_color=LINK_COLOR),
            LoggingJump: JumpPropertiesWidget(self, base_color=JUMP_COLOR),
        }
        link_tab = self._make_properties_tab(self.link_properties_widgets[LoggingConnection])
        jump_tab = self._make_properties_tab(self.link_properties_widgets[LoggingJump])
        self.ui.tabWidget_item_properties.addTab(link_tab, "Link properties")
        self.ui.tabWidget_item_properties.addTab(jump_tab, "Loop properties")
        self._plugin_manager = PluginManager(self)
        self._plugin_manager.load_installed_plugins()
        self.set_work_directory()
        self._disable_project_actions()
        self.connect_signals()

    def eventFilter(self, obj, ev):
        # Save/restore splitter states when hiding/showing execution lists
        if obj == self.ui.listView_console_executions:
            if ev.type() == QEvent.Hide:
                self._qsettings.setValue("mainWindow/consoleSplitterPosition", self.ui.splitter_console.saveState())
            elif ev.type() == QEvent.Show:
                splitter_state = self._qsettings.value("mainWindow/consoleSplitterPosition", defaultValue="false")
                if splitter_state != "false":
                    self.ui.splitter_console.restoreState(splitter_state)
        return super().eventFilter(obj, ev)

    def _setup_properties_title(self):
        self.label_item_name.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.label_item_name.setMinimumHeight(28)
        self._button_item_dir.setIcon(QIcon(":icons/folder-open-regular.svg"))
        layout = QHBoxLayout(self._properties_title)
        layout.addWidget(self.label_item_name)
        layout.addWidget(self._button_item_dir)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

    def connect_signals(self):
        """Connect signals."""
        # Event and process log signals
        self.msg.connect(self.add_message)
        self.msg_success.connect(self.add_success_message)
        self.msg_error.connect(self.add_error_message)
        self.msg_warning.connect(self.add_warning_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_proc_error.connect(self.add_process_error_message)
        self.ui.textBrowser_eventlog.anchorClicked.connect(self.open_anchor)
        # Message box signals
        self.information_box.connect(self._show_message_box)
        self.error_box.connect(self._show_error_box)
        # Menu commands
        self.ui.actionNew.triggered.connect(self.new_project)
        self.ui.actionOpen.triggered.connect(self.open_project)
        self.ui.actionOpen_recent.setMenu(self.recent_projects_menu)
        self.ui.actionOpen_recent.hovered.connect(self.show_recent_projects_menu)
        self.ui.actionStart_jupyter_console.setMenu(self.kernels_menu)
        self.kernels_menu.aboutToShow.connect(self.fetch_kernels)
        self.kernels_menu.aboutToHide.connect(self.stop_fetching_kernels)
        self.ui.actionSave.triggered.connect(self.save_project)
        self.ui.actionSave_As.triggered.connect(self.save_project_as)
        self.ui.actionClose.triggered.connect(lambda _checked=False: self.close_project())
        self.ui.actionSet_description.triggered.connect(self.set_project_description)
        self.ui.actionNew_DB_editor.triggered.connect(self.new_db_editor)
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionRemove_all.triggered.connect(self.remove_all_items)
        self.ui.actionInstall_plugin.triggered.connect(self._plugin_manager.show_install_plugin_dialog)
        self.ui.actionManage_plugins.triggered.connect(self._plugin_manager.show_manage_plugins_dialog)
        self.ui.actionUser_Guide.triggered.connect(self.show_user_guide)
        self.ui.actionGetting_started.triggered.connect(self.show_getting_started_guide)
        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionRetrieve_project.triggered.connect(self.retrieve_project)
        self.ui.menuEdit.aboutToShow.connect(self.refresh_edit_action_states)
        self.ui.menuEdit.aboutToHide.connect(self.enable_edit_actions)
        # noinspection PyArgumentList
        self.ui.actionAbout_Qt.triggered.connect(lambda: QApplication.aboutQt())  # pylint: disable=unnecessary-lambda
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        self.ui.actionCopy.triggered.connect(self.project_item_to_clipboard)
        self.ui.actionPaste.triggered.connect(lambda: self.project_item_from_clipboard(duplicate_files=False))
        self.ui.actionDuplicate.triggered.connect(lambda: self.duplicate_project_item(duplicate_files=False))
        self.ui.actionPasteAndDuplicateFiles.triggered.connect(
            lambda: self.project_item_from_clipboard(duplicate_files=True)
        )
        self.ui.actionDuplicateAndDuplicateFiles.triggered.connect(
            lambda: self.duplicate_project_item(duplicate_files=True)
        )
        self.ui.actionOpen_project_directory.triggered.connect(self._open_project_directory)
        self.ui.actionOpen_item_directory.triggered.connect(self._open_project_item_directory)
        self.ui.actionRename_item.triggered.connect(self._rename_project_item)
        self.ui.actionRemove.triggered.connect(self._remove_selected_items)
        # Debug actions
        self.show_properties_tabbar.triggered.connect(self.toggle_properties_tabbar_visibility)
        self.show_supported_img_formats.triggered.connect(supported_img_formats)  # in helpers.py
        # Context-menus
        self.ui.treeView_project.customContextMenuRequested.connect(self.show_item_context_menu)
        # Undo stack
        self.undo_stack.cleanChanged.connect(self.update_window_modified)
        # Views
        self.ui.listView_console_executions.selectionModel().currentChanged.connect(self._select_console_execution)
        self.ui.listView_console_executions.model().layoutChanged.connect(self._refresh_console_execution_list)
        self.ui.treeView_project.selectionModel().selectionChanged.connect(self.item_selection_changed)
        # Models
        self.project_item_model.rowsInserted.connect(self._update_execute_enabled)
        self.project_item_model.rowsRemoved.connect(self._update_execute_enabled)
        # Execution
        self.ui.actionExecute_project.triggered.connect(self._execute_project)
        self.ui.actionExecute_selection.triggered.connect(self._execute_selection)
        self.ui.actionStop_execution.triggered.connect(self._stop_execution)
        # Open dir
        self._button_item_dir.clicked.connect(self._open_active_item_dir)
        # Consoles
        self.jupyter_console_requested.connect(self._setup_jupyter_console)
        self.kernel_shutdown.connect(self._handle_kernel_shutdown)
        self.persistent_console_requested.connect(self._setup_persistent_console, Qt.BlockingQueuedConnection)

    @Slot(bool)
    def _open_active_item_dir(self, _checked=False):
        self.active_project_item.open_directory()

    @staticmethod
    def set_error_mode():
        """Sets Windows error mode to show all error dialog boxes from subprocesses.

        See https://docs.microsoft.com/en-us/windows/win32/api/errhandlingapi/nf-errhandlingapi-seterrormode
        for documentation.
        """
        if sys.platform == "win32":
            import ctypes  # pylint: disable=import-outside-toplevel

            ctypes.windll.kernel32.SetErrorMode(0)

    def _update_qsettings(self):
        """Updates obsolete settings."""
        old_new = {
            "appSettings/useEmbeddedJulia": "appSettings/useJuliaKernel",
            "appSettings/useEmbeddedPython": "appSettings/usePythonKernel",
        }
        for old, new in old_new.items():
            if not self._qsettings.contains(new) and self._qsettings.contains(old):
                self._qsettings.setValue(new, self._qsettings.value(old))
                self._qsettings.remove(old)
        if self._qsettings.contains("appSettings/saveAtExit"):
            try:
                old_value = int(self._qsettings.value("appSettings/saveAtExit"))
            except ValueError:
                # Old value is already of correct form.
                pass
            else:
                new_value = {0: "prompt", 1: "prompt", 2: "automatic"}[old_value]
                self._qsettings.setValue("appSettings/saveAtExit", new_value)

    def _update_execute_enabled(self):
        first_index = next(self.project_item_model.leaf_indexes(), None)
        enabled_by_project = self._project.settings.enable_execute_all if self._project is not None else False
        self.ui.actionExecute_project.setEnabled(
            enabled_by_project and first_index is not None and not self.execution_in_progress
        )
        if not enabled_by_project:
            self.ui.actionExecute_project.setToolTip("Executing entire project disabled by project settings.")
        else:
            self.ui.actionExecute_project.setToolTip(self._original_execute_project_action_tooltip)

    def _update_execute_selected_enabled(self):
        has_selection = bool(self._selected_item_names)
        self.ui.actionExecute_selection.setEnabled(has_selection and not self.execution_in_progress)

    @Slot(bool)
    def update_window_modified(self, clean):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        self.setWindowModified(not clean)
        self.ui.actionSave.setDisabled(clean)

    def parse_project_item_modules(self):
        """Collects data from project item factories."""
        self._item_categories, self.item_factories = load_project_items("spine_items")
        self._item_specification_factories = load_item_specification_factories("spine_items")

    def set_work_directory(self, new_work_dir=None):
        """Creates a work directory if it does not exist or changes the current work directory to given.

        Args:
            new_work_dir (str, optional): If given, changes the work directory to given
                and creates the directory if it does not exist.
        """
        verbose = new_work_dir is not None
        if not new_work_dir:
            new_work_dir = self._qsettings.value("appSettings/workDir", defaultValue=DEFAULT_WORK_DIR)
            if not new_work_dir:
                # It is possible "appSettings/workDir" is an empty string???
                new_work_dir = DEFAULT_WORK_DIR
        try:
            create_dir(new_work_dir)
            self._qsettings.setValue("appSettings/workDir", new_work_dir)
            if verbose:
                self.msg.emit(f"Work directory is now <b>{new_work_dir}</b>")
        except OSError:
            self.msg_error.emit(f"[OSError] Creating work directory {new_work_dir} failed. Check permissions.")

    def project(self):
        """Returns current project or None if no project open.

        Returns:
            SpineToolboxProject: current project or None
        """
        return self._project

    def qsettings(self):
        """Returns application preferences object."""
        return self._qsettings

    def item_specification_factories(self):
        """Returns project item specification factories.

        Returns:
            list of ProjectItemSpecificationFactory: specification factories
        """
        return self._item_specification_factories

    def update_window_title(self):
        """Updates main window title."""
        if not self._project:
            self.setWindowTitle("Spine Toolbox")
            return
        self.setWindowTitle("{0} [{1}][*] - Spine Toolbox".format(self._project.name, self._project.project_dir))

    @Slot()
    def init_project(self, project_dir):
        """Initializes project at application start-up.

        Opens the last project that was open when app was closed
        (if enabled in Settings) or starts the app without a project.

        Args:
            project_dir (str): project directory
        """
        p = os.path.join(f"{ONLINE_DOCUMENTATION_URL}", "getting_started.html")
        getting_started_anchor = (
            "<a style='color:#99CCFF;' title='"
            + p
            + f"' href='{ONLINE_DOCUMENTATION_URL}/getting_started.html'>Getting Started</a>"
        )
        welcome_msg = "Welcome to Spine Toolbox! If you need help, please read the {0} guide.".format(
            getting_started_anchor
        )
        if not project_dir:
            open_previous_project = int(self._qsettings.value("appSettings/openPreviousProject", defaultValue="0"))
            if (
                open_previous_project != Qt.CheckState.Checked.value
            ):  # 2: Qt.CheckState.Checked, ie. open_previous_project==True
                self.msg.emit(welcome_msg)
                return
            # Get previous project (directory)
            project_dir = self._qsettings.value("appSettings/previousProject", defaultValue="")
            if not project_dir:
                return
        if os.path.isfile(project_dir) and project_dir.endswith(".proj"):
            # Previous project was a .proj file -> Show welcome message instead
            self.msg.emit(welcome_msg)
            return
        if not os.path.isdir(project_dir):
            self.msg_error.emit(
                "Cannot open previous project. Directory <b>{0}</b> may have been moved.".format(project_dir)
            )
            self.remove_path_from_recent_projects(project_dir)
            return
        self.open_project(project_dir)

    @Slot()
    def new_project(self):
        """Opens a file dialog where user can select a directory where a project is created.
        Pops up a question box if selected directory is not empty or if it already contains
        a Spine Toolbox project. Initial project name is the directory name.
        """
        recents = self.qsettings().value("appSettings/recentProjectStorages", defaultValue=None)
        home_dir = os.path.abspath(os.path.join(str(pathlib.Path.home())))
        if not recents:
            initial_path = home_dir
        else:
            recents_lst = str(recents).split("\n")
            if not os.path.isdir(recents_lst[0]):
                # Remove obsolete entry from recentProjectStorages
                OpenProjectDialog.remove_directory_from_recents(recents_lst[0], self.qsettings())
                initial_path = home_dir
            else:
                initial_path = recents_lst[0]
        # noinspection PyCallByClass
        project_dir = QFileDialog.getExistingDirectory(self, "Select project directory (New project...)", initial_path)
        if not project_dir:
            return
        if not os.path.isdir(project_dir):  # Just to be sure, probably not needed
            self.msg_error.emit("Selection is not a directory, please try again")
            return
        # Check if directory is empty and/or a project directory
        if not self.overwrite_check(project_dir):
            return
        self.create_project(project_dir)

    def create_project(self, proj_dir):
        """Creates new project and sets it active.

        Args:
            proj_dir (str): Path to project directory
        """
        if self._project is not None:
            if not self.close_project():
                return
        self.undo_stack.clear()
        self._project = SpineToolboxProject(
            self,
            proj_dir,
            self._plugin_manager.plugin_specs,
            app_settings=self._qsettings,
            settings=ProjectSettings(),
            logger=self,
        )
        self.project_item_model.connect_to_project(self._project)
        self.specification_model.connect_to_project(self._project)
        self._enable_project_actions()
        self.ui.actionSave.setDisabled(True)  # Disable in a clean project
        self._connect_project_signals()
        self.update_window_title()
        self.ui.graphicsView.reset_zoom()
        # Update recentProjects
        self.update_recent_projects()
        # Update recentProjectStorages
        OpenProjectDialog.update_recents(os.path.abspath(os.path.join(proj_dir, os.path.pardir)), self.qsettings())
        self.save_project()
        self._plugin_manager.reload_plugins_with_local_data()
        self.msg.emit(f"New project <b>{self._project.name}</b> is now open")

    @Slot()
    def open_project(self, load_dir=None):
        """Opens project from a selected or given directory.

        Args:
            load_dir (str, optional): Path to project base directory. If default value is used,
                a file explorer dialog is opened where the user can select the
                project to open.

        Returns:
            bool: True when opening the project succeeded, False otherwise
        """
        if not load_dir:
            custom_open_dialog = self.qsettings().value("appSettings/customOpenProjectDialog", defaultValue="true")
            if custom_open_dialog == "true":
                dialog = OpenProjectDialog(self)
                if not dialog.exec():
                    return False
                load_dir = dialog.selection()
            else:
                recents = self.qsettings().value("appSettings/recentProjectStorages", defaultValue=None)
                if not recents:
                    start_dir = os.path.abspath(os.path.join(str(pathlib.Path.home())))
                else:
                    start_dir = str(recents).split("\n")[0]
                load_dir = QFileDialog.getExistingDirectory(self, caption="Open Spine Toolbox Project", dir=start_dir)
                if not load_dir:
                    return False  # Cancelled
        return self.restore_project(load_dir)

    def restore_project(self, project_dir, ask_confirmation=True):
        """Initializes UI, Creates project, models, connections, etc., when opening a project.

        Args:
            project_dir (str): Project directory
            ask_confirmation (bool): True closes the previous project with a confirmation box if user has enabled this

        Returns:
            bool: True when restoring project succeeded, False otherwise
        """
        if not self.close_project(ask_confirmation):
            return False
        # Create project
        self.undo_stack.clear()
        self._project = SpineToolboxProject(
            self,
            project_dir,
            self._plugin_manager.plugin_specs,
            app_settings=self._qsettings,
            settings=ProjectSettings(),
            logger=self,
        )
        self.project_item_model.connect_to_project(self._project)
        self.specification_model.connect_to_project(self._project)
        self._enable_project_actions()
        self.ui.actionSave.setDisabled(True)  # Save is disabled in a clean project
        self._connect_project_signals()
        self.update_window_title()
        # Populate project model with project items
        success = self._project.load(self._item_specification_factories, self.item_factories)
        if not success:
            self.remove_path_from_recent_projects(self._project.project_dir)
            return False
        self._plugin_manager.reload_plugins_with_local_data()
        self.ui.treeView_project.expandAll()
        # Reset zoom on Design View
        self.ui.graphicsView.reset_zoom()
        self.update_recent_projects()
        self.msg.emit(f"Project <b>{self._project.name}</b> is now open")
        return True

    def _toolbars(self):
        """Yields all toolbars in the window."""
        yield self.main_toolbar
        yield from self._plugin_manager.plugin_toolbars.values()

    def _disable_project_actions(self):
        """Disables all project-related actions, except
        New project, Open project and Open recent. Called
        in the constructor and when closing a project."""
        for toolbar in self._toolbars():
            toolbar.set_project_actions_enabled(False)
        self.ui.actionOpen_project_directory.setDisabled(True)
        self.ui.actionSave.setDisabled(True)
        self.ui.actionSave_As.setDisabled(True)
        self.ui.actionClose.setDisabled(True)
        self.ui.actionSet_description.setDisabled(True)
        self.ui.actionExecute_project.setDisabled(True)
        self.ui.actionExecute_selection.setDisabled(True)
        self.ui.actionStop_execution.setDisabled(True)

    def _enable_project_actions(self):
        """Enables all project-related actions. Called when a
        new project is created and when a project is opened."""
        for toolbar in self._toolbars():
            toolbar.set_project_actions_enabled(True)
        self.ui.actionOpen_project_directory.setEnabled(True)
        self.ui.actionSave.setEnabled(True)
        self.ui.actionSave_As.setEnabled(True)
        self.ui.actionClose.setEnabled(True)
        self.ui.actionSet_description.setEnabled(True)
        self._unset_execution_in_progress()

    def refresh_toolbars(self):
        """Set toolbars' color using highest possible contrast."""
        all_toolbars = list(self._toolbars())
        for k, toolbar in enumerate(all_toolbars):
            color = color_from_index(k, len(all_toolbars), base_hue=217.0, saturation=0.6)
            toolbar.set_color(color)

    @Slot()
    def show_recent_projects_menu(self):
        """Updates and sets up the recent projects menu to File-Open recent menu item."""
        if not self.recent_projects_menu.isVisible():
            self.recent_projects_menu = RecentProjectsPopupMenu(self)
            self.ui.actionOpen_recent.setMenu(self.recent_projects_menu)

    @Slot()
    def fetch_kernels(self):
        """Starts a thread for fetching local kernels."""
        if self.kernel_fetcher is not None and self.kernel_fetcher.isRunning():
            return
        QApplication.setOverrideCursor(Qt.CursorShape.BusyCursor)
        self.kernels_menu.clear()
        conda_path = self.qsettings().value("appSettings/condaPath", defaultValue="")
        self.kernel_fetcher = KernelFetcher(conda_path)
        self.kernel_fetcher.kernel_found.connect(self.kernels_menu.add_kernel)
        self.kernel_fetcher.finished.connect(self.restore_override_cursor)
        self.ui.actionStart_jupyter_console.setMenu(self.kernels_menu)
        self.kernel_fetcher.start()

    @Slot()
    def stop_fetching_kernels(self):
        """Terminates kernel fetcher thread."""
        if self.kernel_fetcher is not None:
            self.kernel_fetcher.stop_fetcher.emit()

    @Slot()
    def restore_override_cursor(self):
        """Restores default mouse cursor."""
        QApplication.restoreOverrideCursor()

    @Slot()
    def save_project(self):
        """Saves project."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self._project.save()
        self.msg.emit(f"Project <b>{self._project.name}</b> saved")
        self.undo_stack.setClean()

    @Slot()
    def save_project_as(self):
        """Asks user for a new project directory and duplicates the current project there.
        The name of the duplicated project will be the new directory name. The duplicated
        project is activated."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        # Ask for a new directory
        # noinspection PyCallByClass, PyArgumentList
        answer = QFileDialog.getExistingDirectory(
            self,
            "Select new project directory (Save as...)",
            os.path.abspath(os.path.join(self._project.project_dir, os.path.pardir)),
        )
        if not answer:  # Canceled
            return
        # Just do regular save if selected directory is the same as the current project directory
        if pathlib.Path(answer) == pathlib.Path(self._project.project_dir):
            self.msg_warning.emit("Project directory unchanged")
            self.save_project()
            return
        if not self.overwrite_check(answer):
            return
        if not self.undo_stack.isClean():
            self.save_project()  # Save before copying the project, so the changes are not discarded
        self.msg.emit(f"Saving project to directory {answer}")
        recursive_overwrite(self, self._project.project_dir, answer, silent=False)
        if not self.restore_project(answer, ask_confirmation=False):
            return
        self.save_project()  # Save to update project name in project.json, must be done after restore_project()
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.information(self, f"Project {self._project.name} saved", f"Project directory is now\n\n{answer}")

    def close_project(self, ask_confirmation=True):
        """Closes the current project.

        Args:
            ask_confirmation (bool): if False, no confirmation whatsoever is asked from user

        Returns:
            bool: True when no project open or when it's closed successfully, False otherwise.
        """
        if not self._project:
            return True
        if ask_confirmation and not self.undo_stack.isClean():
            save_at_exit = self._qsettings.value("appSettings/saveAtExit", defaultValue="prompt")
            if save_at_exit == "prompt" and not self._confirm_project_close():
                return False
            elif save_at_exit == "automatic" and not self.save_project():
                return False
        if not self.undo_critical_commands():
            return False
        self.clear_ui()
        self._project.tear_down()
        self._project = None
        self._disable_project_actions()
        self.undo_stack.setClean()
        self.update_window_title()
        self.ui.textBrowser_eventlog.clear()
        return True

    @Slot(bool)
    def set_project_description(self, _=False):
        """Opens a dialog where the user can enter a new description for the project."""
        if not self._project:
            return
        dialog = SetDescriptionDialog(self, self._project)
        dialog.show()

    def init_project_item_model(self):
        """Initializes project item model. Create root and category items and add them to the model."""
        root_item = RootProjectTreeItem()
        self.project_item_model = ProjectItemModel(root_item, self)
        for category in CATEGORIES:
            category_item = CategoryProjectTreeItem(str(category), CATEGORY_DESCRIPTIONS[category])
            self.project_item_model.insert_item(category_item)
        self.ui.treeView_project.setModel(self.project_item_model)

    def init_specification_model(self):
        """Initializes specification model."""
        factory_icons = {item_type: QIcon(factory.icon()) for item_type, factory in self.item_factories.items()}
        self.specification_model = ProjectItemSpecificationModel(factory_icons)
        for item_type in self.item_factories:
            model = self.filtered_spec_factory_models[item_type] = FilteredSpecificationModel(item_type)
            model.setSourceModel(self.specification_model)

    def make_item_properties_uis(self):
        for item_type, factory in self.item_factories.items():
            properties_ui = self._item_properties_uis[item_type] = factory.make_properties_widget(self)
            color = factory.icon_color()
            icon = factory.icon()
            properties_ui.set_color_and_icon(color, icon)
            scroll_area = QScrollArea(self)
            scroll_area.setWidget(properties_ui)
            scroll_area.setWidgetResizable(True)
            tab = self._make_properties_tab(scroll_area)
            self.ui.tabWidget_item_properties.addTab(tab, item_type)

    def _make_properties_tab(self, properties_ui):
        tab = QWidget(self)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(properties_ui)
        return tab

    def add_project_items(self, items_dict, silent=False):
        """Pushes an AddProjectItemsCommand to the undo stack.

        Args:
            items_dict (dict): mapping from item name to item dictionary
            silent (bool): if True, suppress log messages
        """
        if self._project is None or not items_dict:
            return
        self.undo_stack.push(AddProjectItemsCommand(self._project, items_dict, self.item_factories, silent))

    def supports_specifications(self, item_type):
        """Returns True if given project item type supports specifications.

        Returns:
            bool: True if item supports specifications, False otherwise
        """
        return item_type in self._item_specification_factories

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self._qsettings.value("mainWindow/windowSize", defaultValue="false")
        window_pos = self._qsettings.value("mainWindow/windowPosition", defaultValue="false")
        window_state = self._qsettings.value("mainWindow/windowState", defaultValue="false")
        window_maximized = self._qsettings.value("mainWindow/windowMaximized", defaultValue="false")  # returns str
        n_screens = self._qsettings.value("mainWindow/n_screens", defaultValue=1)  # number of screens on last exit
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
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions. Expects QByteArray
        if n_screens_now < int(n_screens):
            # There are less screens available now than on previous application startup
            # Move main window to position 0,0 to make sure that it is not lost on another screen that does not exist
            self.move(0, 0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == "true":
            self.setWindowState(Qt.WindowMaximized)

    def clear_ui(self):
        """Clean UI to make room for a new or opened project."""
        self.activate_no_selection_tab()  # Clear properties widget
        self._restore_original_console()
        self.ui.graphicsView.scene().clear_icons_and_links()  # Clear all items from scene
        self._shutdown_engine_kernels()
        self._close_consoles()

    def undo_critical_commands(self):
        """Undoes critical commands in the undo stack.

        Returns:
            Bool: False if any critical commands aren't successfully undone
        """
        if self.undo_stack.isClean():
            return True
        commands = [self.undo_stack.command(ind) for ind in range(self.undo_stack.index())]

        def is_critical(cmd):
            if isinstance(cmd, SpineToolboxCommand):
                return cmd.is_critical
            return any(is_critical(cmd.child(i)) for i in range(cmd.childCount()))

        def successfully_undone(cmd):
            if isinstance(cmd, SpineToolboxCommand):
                return cmd.successfully_undone
            return all(successfully_undone(cmd.child(i)) for i in range(cmd.childCount()))

        critical_commands = [cmd for cmd in commands if is_critical(cmd)]
        if not critical_commands:
            return True
        for cmd in reversed(critical_commands):
            cmd.undo()
            if not successfully_undone(cmd):
                return False
        return True

    def overwrite_check(self, project_dir):
        """Checks if given directory is a project directory and/or empty
        And asks the user what to do in that case.

        Args:
            project_dir (str): Abs. path to a directory

        Returns:
            bool: True if user wants to overwrite an existing project or
            if the directory is not empty and the user wants to make it
            into a Spine Toolbox project directory anyway. False if user
            cancels the action.
        """
        # Check if directory is empty and/or a project directory
        is_project_dir = os.path.isdir(os.path.join(project_dir, ".spinetoolbox"))
        empty = not bool(os.listdir(project_dir))
        if not empty:
            if is_project_dir:
                msg1 = (
                    "Directory <b>{0}</b> already contains a Spine Toolbox project.<br/><br/>"
                    "Would you like to overwrite the existing project?".format(project_dir)
                )
                box1 = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Overwrite?",
                    msg1,
                    buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    parent=self,
                )
                box1.button(QMessageBox.StandardButton.Ok).setText("Overwrite")
                answer1 = box1.exec()
                if answer1 != QMessageBox.StandardButton.Ok:
                    return False
            else:
                msg2 = (
                    "Directory <b>{0}</b> is not empty.<br/><br/>"
                    "Would you like to make this directory into a Spine Toolbox project?".format(project_dir)
                )
                box2 = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Not empty",
                    msg2,
                    buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    parent=self,
                )
                box2.button(QMessageBox.StandardButton.Ok).setText("Go ahead")
                answer2 = box2.exec()
                if answer2 != QMessageBox.StandardButton.Ok:
                    return False
        return True

    @Slot(QItemSelection, QItemSelection)
    def item_selection_changed(self, selected, deselected):
        """Synchronizes selection with scene. The scene handles item/link de/activation."""
        inds = self.ui.treeView_project.selectedIndexes()
        self._selected_item_names = {
            self.project_item_model.item(i).name for i in self.ui.treeView_project.selectedIndexes()
        }
        self._update_execute_selected_enabled()
        if not self.sync_item_selection_with_scene:
            return
        project_items = [self.project_item_model.item(i).project_item for i in inds]
        project_item_names = {i.name for i in project_items}
        scene = self.ui.graphicsView.scene()
        for icon in scene.project_item_icons():
            icon.setSelected(icon.name() in project_item_names)

    def refresh_active_elements(self, active_project_item, active_link_item, selected_item_names):
        self._selected_item_names = selected_item_names
        self._update_execute_selected_enabled()
        self.ui.textBrowser_eventlog.set_item_log_selected(False)
        self._set_active_project_item(active_project_item)
        self._set_active_link_item(active_link_item)
        self._activate_properties_tab()
        self.ui.textBrowser_eventlog.set_item_log_selected(True)

    def _activate_properties_tab(self):
        if self.active_project_item:
            self.activate_item_tab()
            return
        self._restore_original_console()
        if self.active_link_item:
            self.activate_link_tab()
            return
        self.activate_no_selection_tab()

    def _set_active_project_item(self, active_project_item):
        """
        Args:
            active_project_item (ProjectItemBase or NoneType)
        """
        if self.active_project_item == active_project_item:
            return
        if self.active_project_item:
            # Deactivate old active project item
            if not self.active_project_item.deactivate():
                self.msg_error.emit(
                    "Something went wrong in disconnecting {0} signals".format(self.active_project_item.name)
                )
            self._item_properties_uis[self.active_project_item.item_type()].unset_item()
        self.active_project_item = active_project_item
        if self.active_project_item:
            self.active_project_item.activate()
            self._item_properties_uis[self.active_project_item.item_type()].set_item(self.active_project_item)

    def _set_active_link_item(self, active_link_item):
        """
        Sets active link and connects to corresponding properties widget.

        Args:
            active_link_item (LoggingConnection or LoggingJump, optional)
        """
        if self.active_link_item is active_link_item:
            return
        if self.active_link_item:
            self.link_properties_widgets[type(self.active_link_item)].unset_link()
        self.active_link_item = active_link_item
        if self.active_link_item:
            self.link_properties_widgets[type(self.active_link_item)].set_link(self.active_link_item)

    def activate_no_selection_tab(self):
        """Shows 'No Selection' tab."""
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == "No Selection":
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.dockWidget_item.setWindowTitle("Properties")

    def activate_item_tab(self):
        """Shows active project item properties tab according to item type."""
        # Find tab index according to item type
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == self.active_project_item.item_type():
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.tabWidget_item_properties.currentWidget().layout().insertWidget(0, self._properties_title)
        # Set QDockWidget title to selected item's type
        self.ui.dockWidget_item.setWindowTitle(self.active_project_item.item_type() + " Properties")
        color = self._item_properties_uis[self.active_project_item.item_type()].fg_color
        ss = f"QWidget{{background: {color.name()};}}"
        self._properties_title.setStyleSheet(ss)
        self._button_item_dir.show()
        self._button_item_dir.setToolTip(f"<html>Open <b>{self.active_project_item.name}</b> directory.</html>")

    def activate_link_tab(self):
        """Shows link properties tab."""
        tab_text = {LoggingConnection: "Link properties", LoggingJump: "Loop properties"}[type(self.active_link_item)]
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == tab_text:
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.tabWidget_item_properties.currentWidget().layout().insertWidget(0, self._properties_title)
        self.ui.dockWidget_item.setWindowTitle(tab_text)
        color = self.link_properties_widgets[type(self.active_link_item)].fg_color
        ss = f"QWidget{{background: {color.name()};}}"
        self._properties_title.setStyleSheet(ss)
        self._button_item_dir.hide()

    def update_properties_ui(self):
        widget = self._get_active_properties_widget()
        if widget is not None:
            widget.repaint()

    def _get_active_properties_widget(self):
        if self.active_project_item is not None:
            return self._item_properties_uis[self.active_project_item.item_type()]
        if self.active_link_item is not None:
            return self.link_properties_widgets[type(self.active_link_item)]
        return None

    def add_specification(self, specification):
        """Pushes an AddSpecificationCommand to undo stack."""
        self.undo_stack.push(AddSpecificationCommand(self._project, specification, save_to_disk=True))

    @Slot()
    def import_specification(self):
        """Opens a file dialog where the user can select an existing specification
        definition file (.json). If file is valid, pushes AddSpecificationCommand to undo stack.
        """
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(
            self, "Select Specification file", self._project.project_dir, "JSON (*.json)"
        )
        if answer[0] == "":  # Cancel button clicked
            return
        def_file = os.path.abspath(answer[0])
        # Load specification
        local_data = load_specification_local_data(self._project.config_dir)
        specification = load_specification_from_file(
            def_file, local_data, self._item_specification_factories, self._qsettings, self
        )
        if not specification:
            return
        self.undo_stack.push(AddSpecificationCommand(self._project, specification, save_to_disk=False))

    def replace_specification(self, name, specification):
        """Pushes an ReplaceSpecificationCommand to undo stack."""
        if name == specification.name:
            # If the spec name didn't change, we don't need to make a command.
            # This is because the changes don't affect the project.json file.
            self._project.replace_specification(name, specification)
            return
        self.undo_stack.push(ReplaceSpecificationCommand(self._project, name, specification))

    @Slot(str)
    def repair_specification(self, name):
        """Repairs specification if it is broken.

        Args:
            name (str): specification's name
        """
        specification = self._project.get_specification(name)
        item_factory = self.item_factories.get(specification.item_type)
        if item_factory is not None:
            item_factory.repair_specification(self, specification)

    def prompt_save_location(self, title, proposed_path, file_filter):
        """Shows a dialog for the user to select a path to save a file.

        Args:
            title (str): dialog window title
            proposed_path (str): A proposed location.
            file_filter (str): file extension filter

        Returns:
            str: absolute path or None if dialog was cancelled
        """
        answer = QFileDialog.getSaveFileName(self, title, proposed_path, file_filter)
        if not answer[0]:  # Cancel button clicked
            return None
        return os.path.abspath(answer[0])

    @Slot(str, str)
    def _log_specification_saved(self, name, path):
        """Prints a message in the event log, saying that given spec was saved in a certain location,
        together with a clickable link to change the location.

        Args:
            name (str): specification's name
            path (str): specification's file path
        """
        self.msg_success.emit(
            f"Specification <b>{name}</b> successfully saved as "
            f"<a style='color:#99CCFF;' href='file:///{path}'>{path}</a> "
            f"<a style='color:white;' href='change_spec_file.{name}'><b>[change]</b></a>"
        )

    @Slot()
    def remove_all_items(self):
        """Pushes a RemoveAllProjectItemsCommand to the undo stack."""
        if self._project is None or not self._project.has_items():
            self.msg.emit("No project items to remove.")
            return
        delete_data = int(self._qsettings.value("appSettings/deleteData", defaultValue="0")) != 0
        msg = "Remove all items from project? "
        if not delete_data:
            msg += "Item data directory will still be available in the project directory after this operation."
        else:
            msg += "<br><br><b>Warning: Item data will be permanently lost after this operation.</b>"
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Remove All Items",
            msg,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=self,
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText("Remove Items")
        answer = message_box.exec()
        if answer != QMessageBox.StandardButton.Ok:
            return
        self.undo_stack.push(RemoveAllProjectItemsCommand(self._project, self.item_factories, delete_data=delete_data))

    def register_anchor_callback(self, url, callback):
        """Registers a callback for a given anchor in event log, see ``open_anchor()``.
        Used by ``ToolFactory.repair_specification()``.

        Args:
            url (str): The anchor url
            callback (function): A function to call when the anchor is clicked on event log.
        """
        self._anchor_callbacks[url] = callback

    @Slot(QUrl)
    def open_anchor(self, qurl):
        """Open file explorer in the directory given in qurl.

        Args:
            qurl (QUrl): The url to open
        """
        url = qurl.url()
        if url == "#":  # This is a Tip so do not try to open the URL
            return
        if url.startswith("change_spec_file."):
            _, spec_name = url.split(".")
            self._change_specification_file_location(spec_name)
            return
        callback = self._anchor_callbacks.get(url, None)
        if callback is not None:
            callback()
            return
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(qurl)
        if not res:
            self.msg_error.emit(f"Unable to open <b>{url}</b>")

    def _change_specification_file_location(self, name):
        """Prompts user for new location for a project item specification.

        Delegates saving to project if one is open by pushing a command to the undo stack,
        otherwise tries to find the specification from the plugin manager.

        Args:
            name (str): specification's name
        """
        if self._project is not None:
            if not self._project.is_specification_name_reserved(name):
                self.msg_error.emit(f"Unable to find specification '{name}'")
                return
            spec = self._project.get_specification(name)
            path = self.prompt_save_location(
                f"Save {spec.item_type} specification", spec.definition_file_path, "JSON (*.json)"
            )
            if path is None:
                return
            self.undo_stack.push(SaveSpecificationAsCommand(self._project, name, path))
            return
        spec = None
        for plugin_spec in self._plugin_manager.plugin_specs:
            if plugin_spec.name == name:
                spec = plugin_spec
                break
        if spec is None:
            self.msg_error.emit(f"Unable to find specification '{name}'.")
            return
        path = self.prompt_save_location(
            f"Save {spec.item_type} specification", spec.definition_file_path, "JSON (*.json)"
        )
        if path is None:
            return
        spec.definition_file_path = path
        if not spec.save():
            return
        self._log_specification_saved(spec.name, path)

    @Slot(QModelIndex, QPoint)
    def show_specification_context_menu(self, ind, global_pos):
        """Context menu for item specifications.

        Args:
            ind (QModelIndex): In the ProjectItemSpecificationModel
            global_pos (QPoint): Mouse position
        """
        if not self.project():
            return
        spec = self.specification_model.specification(ind.row())
        if not self.supports_specification(spec.item_type):
            return
        item_factory = self.item_factories[spec.item_type]
        menu = item_factory.make_specification_menu(self, ind)
        menu.exec(global_pos)
        menu.deleteLater()
        menu = None

    @Slot(QModelIndex)
    def edit_specification(self, index, item):
        """Opens a specification editor widget.

        Args:
            index (QModelIndex): Index of the item (from double-click or context menu signal)
            item (ProjectItem, optional)
        """
        if not index.isValid() or not item:
            return
        specification = self.specification_model.specification(index.row())
        # Open spec in Tool specification edit widget
        if item.item_type() == "Importer":
            item.edit_specification()
        else:
            self.show_specification_form(specification.item_type, specification, item)

    @Slot(QModelIndex)
    def remove_specification(self, index):
        """Removes specification from project.

        Args:
            index (QModelIndex): Index of the specification item
        """
        if not index.isValid():
            return
        specification = self.specification_model.specification(index.row())
        message = f"Remove Specification <b>{specification.name}</b> from Project?"
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            "Remove Specification",
            message,
            buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
            parent=self,
        )
        message_box.button(QMessageBox.StandardButton.Ok).setText("Remove Specification")
        answer = message_box.exec()
        if answer != QMessageBox.StandardButton.Ok:
            return
        self.undo_stack.push(RemoveSpecificationCommand(self._project, specification.name))

    @busy_effect
    @Slot(QModelIndex)
    def open_specification_file(self, index):
        """Open the specification definition file in the default (.json) text-editor.

        Args:
            index (QModelIndex): Index of the item
        """
        if not index.isValid():
            return
        specification = self.specification_model.specification(index.row())
        file_path = specification.definition_file_path
        # Check if file exists first. openUrl may return True if file doesn't exist
        if not os.path.isfile(file_path):
            logging.error("Failed to open editor for %s", file_path)
            self.msg_error.emit("Specification file <b>{0}</b> not found.".format(file_path))
            return
        tool_specification_url = "file:///" + file_path
        # Open Tool specification file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = open_url(tool_specification_url)
        if not res:
            self.msg_error.emit(
                "Unable to open specification file {0}. Make sure that <b>.json</b> "
                "files are associated with a text editor. For example on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(file_path)
            )

    @Slot(bool)
    def new_db_editor(self):
        editor = MultiSpineDBEditor(self.db_mngr, {})
        editor.show()

    @Slot()
    def _handle_zoom_minus_pressed(self):
        """Slot for handling case when '-' button in menu is pressed."""
        self.ui.graphicsView.zoom_out()

    @Slot()
    def _handle_zoom_plus_pressed(self):
        """Slot for handling case when '+' button in menu is pressed."""
        self.ui.graphicsView.zoom_in()

    @Slot()
    def _handle_zoom_reset_pressed(self):
        """Slot for handling case when 'reset zoom' button in menu is pressed."""
        self.ui.graphicsView.reset_zoom()

    def add_zoom_action(self):
        """Setups zoom widget action in view menu."""
        zoom_action = ToolBarWidgetAction("Zoom", parent=self.ui.menuView, compact=True)
        zoom_action.tool_bar.addAction("-", self._handle_zoom_minus_pressed).setToolTip("Zoom out")
        zoom_action.tool_bar.addAction("Reset", self._handle_zoom_reset_pressed).setToolTip("Reset zoom")
        zoom_action.tool_bar.addAction("+", self._handle_zoom_plus_pressed).setToolTip("Zoom in")
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(zoom_action)

    @Slot()
    def restore_dock_widgets(self):
        """Dock all floating and or hidden QDockWidgets back to the main window."""
        for dock in self.findChildren(QDockWidget):
            dock.setMinimumSize(0, 0)
            dock.setVisible(True)
            dock.setFloating(False)
        self.splitDockWidget(self.ui.dockWidget_project, self.ui.dockWidget_eventlog, Qt.Orientation.Vertical)
        self.splitDockWidget(self.ui.dockWidget_eventlog, self.ui.dockWidget_console, Qt.Orientation.Horizontal)
        self.ui.dockWidget_eventlog.raise_()
        self.splitDockWidget(self.ui.dockWidget_project, self.ui.dockWidget_design_view, Qt.Orientation.Horizontal)
        self.splitDockWidget(self.ui.dockWidget_design_view, self.ui.dockWidget_item, Qt.Orientation.Horizontal)
        docks = (self.ui.dockWidget_project, self.ui.dockWidget_design_view, self.ui.dockWidget_item)
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.2 * width, 0.5 * width, 0.3 * width], Qt.Orientation.Horizontal)
        docks = (self.ui.dockWidget_project, self.ui.dockWidget_eventlog)
        width = sum(d.size().width() for d in docks)
        self.resizeDocks(docks, [0.6 * width, 0.4 * width], Qt.Orientation.Vertical)

    def _add_execute_actions(self):
        """Adds execution handler actions to the main window."""
        self.addAction(self.ui.actionExecute_project)
        self.addAction(self.ui.actionExecute_selection)
        self.addAction(self.ui.actionStop_execution)

    def set_debug_qactions(self):
        """Sets shortcuts for QActions that may be needed in debugging."""
        self.show_properties_tabbar.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_0))
        self.show_supported_img_formats.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_8))
        self.addAction(self.show_properties_tabbar)
        self.addAction(self.show_supported_img_formats)

    def add_menu_actions(self):
        """Adds extra actions to Edit and View menu."""
        self.ui.menuToolbars.addAction(self.main_toolbar.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_design_view.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_project.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_eventlog.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_console.toggleViewAction())
        undo_action = self.undo_stack.createUndoAction(self)
        redo_action = self.undo_stack.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        before = self.ui.menuEdit.actions()[0]
        self.ui.menuEdit.insertAction(before, undo_action)
        self.ui.menuEdit.insertAction(before, redo_action)
        self.ui.menuEdit.insertSeparator(before)

    def toggle_properties_tabbar_visibility(self):
        """Shows or hides the tab bar in properties dock widget. For debugging purposes."""
        if self.ui.tabWidget_item_properties.tabBar().isVisible():
            self.ui.tabWidget_item_properties.tabBar().hide()
        else:
            self.ui.tabWidget_item_properties.tabBar().show()

    def update_datetime(self):
        """Returns a boolean, which determines whether
        date and time is prepended to every Event Log message."""
        d = int(self._qsettings.value("appSettings/dateTime", defaultValue="2"))
        return d != 0

    @Slot(str)
    def add_message(self, msg):
        """Append regular message to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)

    @Slot(str)
    def add_success_message(self, msg):
        """Append message with green text color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg_success", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)

    @Slot(str)
    def add_error_message(self, msg):
        """Append message with red color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg_error", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)

    @Slot(str)
    def add_warning_message(self, msg):
        """Append message with yellow (golden) color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg_warning", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg", msg)
        self.ui.textBrowser_eventlog.append(message)

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_log_message("msg_error", msg)
        self.ui.textBrowser_eventlog.append(message)

    def override_console_and_execution_list(self):
        self._override_console()
        self._override_execution_list()

    def _override_console(self):
        """Sets the jupyter console of the active project item in Jupyter Console and updates title."""
        if self.active_project_item is not None:
            console = self._item_consoles.get(self.active_project_item)
        elif isinstance(self.active_link_item, LoggingJump):
            console = self._item_consoles.get(self.active_link_item)
        else:
            return
        self._do_override_console(console)

    def _do_override_console(self, console):
        if not isinstance(console, (PersistentConsoleWidget, JupyterConsoleWidget)):
            self._restore_original_console()
            return
        self._set_override_console(console)

    def _override_execution_list(self):
        """Displays executions of the active project item in Executions and updates title."""
        if self.active_project_item is None:
            return
        filter_consoles = self._filter_item_consoles.get(self.active_project_item)
        if filter_consoles is None:
            self.ui.listView_console_executions.hide()
            return
        self.ui.listView_console_executions.show()
        self.ui.listView_console_executions.model().reset_model(filter_consoles)
        current_key = self._current_execution_keys.get(self.active_project_item)
        current = self.ui.listView_console_executions.model().find_index(current_key)
        self.ui.listView_console_executions.setCurrentIndex(current)

    def _restore_original_console(self):
        """Sets the Console back to the original."""
        self.ui.listView_console_executions.hide()
        self._set_override_console(self.ui.label_no_console)

    def _set_override_console(self, console):
        splitter = self.ui.splitter_console
        if console == splitter.widget(1):
            return
        splitter.replaceWidget(1, console)
        console.show()
        try:
            new_title = console.name()
        except AttributeError:
            new_title = "Console"
        self.ui.dockWidget_console.setWindowTitle(new_title)

    @Slot()
    def _refresh_console_execution_list(self):
        """Refreshes console executions as the active project item starts new executions."""
        view = self.ui.listView_console_executions
        view.show()
        model = view.model()
        if model.rowCount() == 0:
            view.setCurrentIndex(QModelIndex())
        elif not view.currentIndex().isValid():
            index = view.model().index(0, 0)
            view.setCurrentIndex(index)
        else:
            current = view.currentIndex()
            self._select_console_execution(current, None)

    @Slot(QModelIndex, QModelIndex)
    def _select_console_execution(self, current, _previous):
        """Sets the console of the selected execution in Console."""
        if not current.data():
            return
        self._current_execution_keys[self.active_project_item] = current.data()
        console = current.model().get_console(current.data())
        self._do_override_console(console)

    def show_add_project_item_form(self, item_type, x=0, y=0, spec=""):
        """Show add project item widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        factory = self.item_factories.get(item_type)
        if factory is None:
            self.msg_error.emit(f"{item_type} not found in factories")
            return
        self.add_project_item_form = factory.make_add_item_widget(self, x, y, spec)
        self.add_project_item_form.show()

    def supports_specification(self, item_type):
        """
        Returns True if given item type supports specifications.

        Args:
            item_type (str): item's type

        Returns:
            bool: True if item supports specifications, False otherwise
        """
        return item_type in self._item_specification_factories

    @Slot()
    def show_specification_form(self, item_type, specification=None, item=None, **kwargs):
        """
        Shows specification widget.

        Args:
            item_type (str): item's type
            specification (ProjectItemSpecification, optional): specification
            item (ProjectItem, optional): project item
            **kwargs: parameters passed to the specification widget
        """
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        if not self.supports_specification(item_type):
            return
        msg = f"Opening {item_type} specification editor"
        if specification:
            msg += f" for {specification.name}"
        self.msg.emit(msg)
        multi_tab_editor = next(self.get_all_multi_tab_spec_editors(item_type), None)
        if multi_tab_editor is None:
            multi_tab_editor = MultiTabSpecEditor(self, item_type)
            multi_tab_editor.add_new_tab(specification, item, **kwargs)
            multi_tab_editor.show()
            return
        existing = self._get_existing_spec_editor(item_type, specification, item)
        if existing is None:
            multi_tab_editor.add_new_tab(specification, item, **kwargs)
        else:
            multi_tab_editor, editor = existing
            multi_tab_editor.set_current_tab(editor)
        if multi_tab_editor.isMinimized():
            multi_tab_editor.showNormal()
        multi_tab_editor.activateWindow()

    @staticmethod
    def get_all_multi_tab_spec_editors(item_type):
        for window in qApp.topLevelWindows():  # pylint: disable=undefined-variable
            if isinstance(window, QWindow):
                widget = QWidget.find(window.winId())
                if isinstance(widget, MultiTabSpecEditor) and widget.item_type == item_type:
                    yield widget

    def _get_existing_spec_editor(self, item_type, specification, item):
        for multi_tab_editor in self.get_all_multi_tab_spec_editors(item_type):
            for k in range(multi_tab_editor.tab_widget.count()):
                editor = multi_tab_editor.tab_widget.widget(k)
                if editor.specification is not None and editor.specification == specification and editor.item == item:
                    return multi_tab_editor, editor
        return None

    @Slot()
    def show_settings(self):
        """Show Settings widget."""
        self.settings_form = SettingsWidget(self)
        self.settings_form.show()

    @Slot()
    def show_about(self):
        """Show About Spine Toolbox form."""
        form = AboutWidget(self)
        form.show()

    # pylint: disable=no-self-use
    @Slot()
    def show_user_guide(self):
        """Open Spine Toolbox documentation index page in browser."""
        index_url = f"{ONLINE_DOCUMENTATION_URL}/index.html"
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        open_url(index_url)

    # pylint: disable=no-self-use
    @Slot()
    def show_getting_started_guide(self):
        """Open Spine Toolbox Getting Started HTML page in browser."""
        index_url = f"{ONLINE_DOCUMENTATION_URL}/getting_started.html"
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        open_url(index_url)

    @Slot()
    def retrieve_project(self):
        """Retrieves project from server."""
        msg = "Retrieve project by Job Id"
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QInputDialog.getText(self, msg, "Job Id?:", flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        job_id = answer[0]
        if not job_id:  # Cancel button clicked
            return
        initial_path = os.path.abspath(os.path.join(str(pathlib.Path.home())))  # Home dir
        project_dir = QFileDialog.getExistingDirectory(self, "Select new project directory...)", initial_path)
        if not project_dir:
            return
        self.msg.emit(f"Retrieving project {job_id} from server and extracting to: {project_dir}")
        host, port, sec_model, sec_folder = self.engine_server_settings()
        if not host:
            self.msg_error.emit(
                "Spine Engine Server <b>host address</b> missing. "
                "Please enter host in <b>File->Settings->Engine</b>."
            )
            return
        elif not port:
            self.msg_error.emit(
                "Spine Engine Server <b>port</b> missing. " "Please select port in <b>File->Settings->Engine</b>."
            )
            return
        self.msg.emit(f"Connecting to Spine Engine Server at <b>{host}:{port}</b>")
        try:
            engine_client = EngineClient(host, port, sec_model, sec_folder)
        except RemoteEngineInitFailed as e:
            self.msg_error.emit(f"Server is not responding. {e}. Check settings in <b>File->Settings->Engine</b>.")
            return
        project_file = engine_client.retrieve_project(job_id)
        # Save the received zip file
        zip_path = os.path.join(project_dir, "project_package.zip")
        try:
            with open(zip_path, "wb") as f:
                f.write(project_file)
        except Exception as e:
            self.msg_error.emit(f"Saving the downloaded file to '{zip_path}' failed. [{type(e).__name__}: {e}")
            engine_client.close()
            return
        # Extract the saved file
        self.msg.emit(f"Extracting project file project_package.zip to: {project_dir}")
        with ZipFile(zip_path, "r") as zip_obj:
            try:
                first_bad_file = zip_obj.testzip()  # debugging
                if not first_bad_file:
                    zip_obj.extractall(project_dir)
                else:
                    self.msg_error.emit(f"Zip-file {zip_path} test failed. First bad file: {first_bad_file}")
            except Exception as e:
                self.msg_error.emit(f"Problem in extracting downloaded project: {e}")
                engine_client.close()
                return
        engine_client.close()
        try:
            os.remove(zip_path)  # Remove downloaded project_package.zip
        except OSError:
            self.msg_error.emit(f"Removing file {zip_path} failed")

    def engine_server_settings(self):
        """Returns the user given Spine Engine Server settings in a tuple."""
        host = self._qsettings.value("engineSettings/remoteHost", defaultValue="")  # Host name
        port = self._qsettings.value("engineSettings/remotePort", defaultValue="49152")  # Host port
        sec_model = self._qsettings.value("engineSettings/remoteSecurityModel", defaultValue="")  # ZQM security model
        security = ClientSecurityModel.NONE if not sec_model else ClientSecurityModel.STONEHOUSE
        sec_folder = (
            ""
            if security == ClientSecurityModel.NONE
            else self._qsettings.value("engineSettings/remoteSecurityFolder", defaultValue="")
        )
        return host, port, sec_model, sec_folder

    @Slot(QPoint)
    def show_item_context_menu(self, pos):
        """Context menu for project items listed in the project QTreeView.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_project.indexAt(pos)
        global_pos = self.ui.treeView_project.viewport().mapToGlobal(pos)
        self.show_project_or_item_context_menu(global_pos, ind)

    def show_project_or_item_context_menu(self, pos, index):
        """Creates and shows the project item context menu.

        Args:
            pos (QPoint): Mouse position
            index (QModelIndex, optional): Index of concerned item or None
        """
        if not index:  # Clicked on a blank area in Design view
            menu = QMenu(self)
            menu.addAction(self.ui.actionPaste)
            menu.addAction(self.ui.actionPasteAndDuplicateFiles)
            menu.addSeparator()
            menu.addAction(self.ui.actionOpen_project_directory)
        elif not index.isValid():  # Clicked on a blank area in Project tree view
            menu = QMenu(self)
            menu.addAction(self.ui.actionOpen_project_directory)
        else:  # Clicked on an item, show the custom context menu for that item
            item = self.project_item_model.item(index)
            menu = item.custom_context_menu(self)
        menu.setToolTipsVisible(True)
        menu.aboutToShow.connect(self.refresh_edit_action_states)
        menu.aboutToHide.connect(self.enable_edit_actions)
        menu.exec(pos)
        menu.deleteLater()

    def show_link_context_menu(self, pos, link):
        """Context menu for connection links.

        Args:
            pos (QPoint): Mouse position
            link (Link(QGraphicsPathItem)): The concerned link
        """
        menu = QMenu(self)
        menu.addAction(self.ui.actionRemove)
        self.ui.actionRemove.setEnabled(True)
        menu.addAction(self.ui.actionTake_link)
        action = menu.exec(pos)
        if action is self.ui.actionTake_link:
            self.ui.graphicsView.take_link(link)
        self.refresh_edit_action_states()
        menu.deleteLater()

    @Slot()
    def refresh_edit_action_states(self):
        """Sets the enabled/disabled state for copy, paste, duplicate,
        and remove actions in File-Edit menu, project tree view
        context menu, and in Design View context menus just before the
        menus are shown to user."""
        clipboard = QApplication.clipboard()
        byte_data = clipboard.mimeData().data("application/vnd.spinetoolbox.ProjectItem")
        can_paste = not byte_data.isNull()
        selected_items = self.ui.graphicsView.scene().selectedItems()
        has_selection = bool(selected_items)
        can_copy = any(isinstance(x, ProjectItemIcon) for x in selected_items)
        has_items = self.project_item_model.n_items() > 0
        selected_project_items = [x for x in selected_items if isinstance(x, ProjectItemIcon)]
        _methods = [
            getattr(self.project_item_model.get_item(x.name()).project_item, "copy_local_data")
            for x in selected_project_items
        ]
        can_duplicate_files = any(m.__qualname__.partition(".")[0] != "ProjectItem" for m in _methods)
        self.ui.actionCopy.setEnabled(can_copy)
        self.ui.actionPaste.setEnabled(can_paste)
        self.ui.actionPasteAndDuplicateFiles.setEnabled(can_paste)
        self.ui.actionDuplicate.setEnabled(can_copy)
        self.ui.actionDuplicateAndDuplicateFiles.setEnabled(can_duplicate_files)
        self.ui.actionRemove.setEnabled(has_selection)
        self.ui.actionRemove_all.setEnabled(has_items)

    @Slot()
    def enable_edit_actions(self):
        """Enables project item edit actions after a QMenu has been shown.
        This is needed to enable keyboard shortcuts (e.g. Ctrl-C & del)
        again."""
        self.ui.actionCopy.setEnabled(True)
        self.ui.actionPaste.setEnabled(True)
        self.ui.actionPasteAndDuplicateFiles.setEnabled(True)
        self.ui.actionDuplicate.setEnabled(True)
        self.ui.actionDuplicateAndDuplicateFiles.setEnabled(True)

    def _tasks_before_exit(self):
        """
        Returns a list of tasks to perform before exiting the application.

        Possible tasks are:

        - `"prompt exit"`: prompt user if quitting is really desired
        - `"prompt save"`: prompt user if project should be saved before quitting
        - `"save"`: save project before quitting

        Returns:
            a list containing zero or more tasks
        """
        save_at_exit = (
            self._qsettings.value("appSettings/saveAtExit", defaultValue="prompt")
            if self._project is not None and not self.undo_stack.isClean()
            else None
        )
        if save_at_exit == "prompt":
            return ["prompt save"]
        show_confirm_exit = int(self._qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        tasks = []
        if show_confirm_exit == 2:
            tasks.append("prompt exit")
        if save_at_exit == "automatic":
            tasks.append("save")
        return tasks

    def _perform_pre_exit_tasks(self):
        """
        Prompts user to confirm quitting and saves the project if necessary.

        Returns:
            True if exit should proceed, False if the process was cancelled
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
                self.save_project()
        return True

    def _confirm_exit(self):
        """
        Confirms exiting from user.

        Returns:
            True if exit should proceed, False if user cancelled
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
            self._qsettings.setValue("appSettings/showExitPrompt", show_prompt)
            return True
        return False

    def _confirm_project_close(self):
        """
        Confirms exit from user and saves the project if requested.

        Returns:
            True if exiting should proceed, False if user cancelled
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
            self.save_project()
        return True

    def remove_path_from_recent_projects(self, p):
        """Removes entry that contains given path from the recent project files list in QSettings.

        Args:
            p (str): Full path to a project directory
        """
        recents = self._qsettings.value("appSettings/recentProjects", defaultValue=None)
        if not recents:
            return
        recents = str(recents)
        recents_list = recents.split("\n")
        for entry in recents_list:
            _, path = entry.split("<>")
            if same_path(path, p):
                recents_list.pop(recents_list.index(entry))
                break
        updated_recents = "\n".join(recents_list)
        # Save updated recent paths
        self._qsettings.setValue("appSettings/recentProjects", updated_recents)
        self._qsettings.sync()  # Commit change immediately

    def clear_recent_projects(self):
        """Clears recent projects list in File->Open recent menu."""
        msg = "Are you sure?"
        title = "Clear recent projects?"
        message_box = QMessageBox(
            QMessageBox.Icon.Question,
            title,
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            parent=self,
        )
        answer = message_box.exec()
        if answer == QMessageBox.StandardButton.No:
            return
        self._qsettings.remove("appSettings/recentProjects")
        self._qsettings.remove("appSettings/recentProjectStorages")
        self._qsettings.sync()

    def update_recent_projects(self):
        """Adds a new entry to QSettings variable that remembers twenty most recent project paths."""
        recents = self._qsettings.value("appSettings/recentProjects", defaultValue=None)
        entry = self.project().name + "<>" + self.project().project_dir
        if not recents:
            updated_recents = entry
        else:
            recents = str(recents)
            recents_list = recents.split("\n")
            normalized_recents = list(map(os.path.normcase, recents_list))
            try:
                index = normalized_recents.index(os.path.normcase(entry))
            except ValueError:
                # Add path only if it's not in the list already
                recents_list.insert(0, entry)
                if len(recents_list) > 20:
                    recents_list.pop()
            else:
                # If entry was on the list, move it as the first item
                recents_list.insert(0, recents_list.pop(index))
            updated_recents = "\n".join(recents_list)
        # Save updated recent paths
        self._qsettings.setValue("appSettings/recentProjects", updated_recents)
        self._qsettings.sync()  # Commit change immediately

    def closeEvent(self, event):
        """Method for handling application exit.

        Args:
             event (QCloseEvent): PySide6 event
        """
        # Show confirm exit message box
        exit_confirmed = self._perform_pre_exit_tasks()
        if not exit_confirmed:
            event.ignore()
            return
        if not self.undo_critical_commands():
            event.ignore()
            return
        # Save settings
        if self._project is None:
            self._qsettings.setValue("appSettings/previousProject", "")
        else:
            self._qsettings.setValue("appSettings/previousProject", self._project.project_dir)
            self.update_recent_projects()
        self._qsettings.setValue("appSettings/toolbarIconOrdering", self.main_toolbar.icon_ordering())
        self._qsettings.setValue("mainWindow/windowSize", self.size())
        self._qsettings.setValue("mainWindow/windowPosition", self.pos())
        self._qsettings.setValue("mainWindow/windowState", self.saveState(version=1))
        self._qsettings.setValue("mainWindow/windowMaximized", self.windowState() == Qt.WindowMaximized)
        # Save number of screens
        # noinspection PyArgumentList
        self._qsettings.setValue("mainWindow/n_screens", len(QGuiApplication.screens()))
        self._shutdown_engine_kernels()
        self._close_consoles()
        if self._project is not None:
            self._project.tear_down()
        for item_type in self.item_factories:
            for editor in self.get_all_multi_tab_spec_editors(item_type):
                editor.close()
        event.accept()

    def _serialize_selected_items(self):
        """
        Serializes selected project items into a dictionary.

        The serialization protocol tries to imitate the format in which projects are saved.

        Returns:
             dict: a dict containing serialized version of selected project items
        """
        selected_project_items = self.ui.graphicsView.scene().selectedItems()
        items_dict = dict()
        for item_icon in selected_project_items:
            if not isinstance(item_icon, ProjectItemIcon):
                continue
            name = item_icon.name()
            index = self.project_item_model.find_item(name)
            project_item = self.project_item_model.item(index).project_item
            item_dict = dict(project_item.item_dict())
            item_dict["original_data_dir"] = project_item.data_dir
            item_dict["original_db_url"] = item_dict.get("url")
            items_dict[name] = item_dict
        return items_dict

    def _deserialized_item_position_shifts(self, item_dicts):
        """
        Calculates horizontal and vertical shifts for project items being deserialized.

        If the mouse cursor is on the Design view we try to place the items unders the cursor.
        Otherwise the items will get a small shift so they don't overlap a possible item below.
        In case the items don't fit the scene rect we clamp their coordinates within it.

        Args:
            item_dicts (dict): a dictionary of serialized items being deserialized
        Returns:
            tuple: a tuple of (horizontal shift, vertical shift) in scene's coordinates
        """
        mouse_position = self.ui.graphicsView.mapFromGlobal(QCursor.pos())
        if self.ui.graphicsView.rect().contains(mouse_position):
            mouse_over_design_view = self.ui.graphicsView.mapToScene(mouse_position)
        else:
            mouse_over_design_view = None
        if mouse_over_design_view is not None:
            first_item = next(iter(item_dicts.values()))
            x = first_item["x"]
            y = first_item["y"]
            shift_x = x - mouse_over_design_view.x()
            shift_y = y - mouse_over_design_view.y()
        else:
            shift_x = -15.0
            shift_y = -15.0
        return shift_x, shift_y

    @staticmethod
    def _set_deserialized_item_position(item_dict, shift_x, shift_y, scene_rect):
        """Moves item's position by shift_x and shift_y while keeping it within the limits of scene_rect."""
        new_x = np.clip(item_dict["x"] - shift_x, scene_rect.left(), scene_rect.right())
        new_y = np.clip(item_dict["y"] - shift_y, scene_rect.top(), scene_rect.bottom())
        item_dict["x"] = new_x
        item_dict["y"] = new_y

    def _deserialize_items(self, items_dict, duplicate_files=False):
        """
        Deserializes project items from a dictionary and adds them to the current project.

        Args:
            items_dict (dict): serialized project items
        """
        if self._project is None:
            return
        scene = self.ui.graphicsView.scene()
        scene.clearSelection()
        shift_x, shift_y = self._deserialized_item_position_shifts(items_dict)
        scene_rect = scene.sceneRect()
        final_items_dict = dict()
        for name, item_dict in items_dict.items():
            item_dict["duplicate_files"] = duplicate_files
            if self.project_item_model.find_item(name) is not None:
                new_name = unique_name(name, self.project().all_item_names)
                final_items_dict[new_name] = item_dict
            else:
                final_items_dict[name] = item_dict
            self._set_deserialized_item_position(item_dict, shift_x, shift_y, scene_rect)
        self.add_project_items(final_items_dict, silent=True)

    @Slot()
    def project_item_to_clipboard(self):
        """Copies the selected project items to system's clipboard."""
        serialized_items = self._serialize_selected_items()
        if not serialized_items:
            return
        item_dump = json.dumps(serialized_items)
        clipboard = QApplication.clipboard()
        data = QMimeData()
        data.setData("application/vnd.spinetoolbox.ProjectItem", QByteArray(item_dump.encode("utf-8")))
        clipboard.setMimeData(data)

    @Slot()
    def project_item_from_clipboard(self, duplicate_files=False):
        """Adds project items in system's clipboard to the current project.

        Args:
            duplicate_files (bool): Duplicate files boolean
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        byte_data = mime_data.data("application/vnd.spinetoolbox.ProjectItem")
        if byte_data.isNull():
            return
        item_dump = str(byte_data.data(), "utf-8")
        item_dicts = json.loads(item_dump)
        self._deserialize_items(item_dicts, duplicate_files)

    @Slot()
    def duplicate_project_item(self, duplicate_files=False):
        """Duplicates the selected project items."""
        item_dicts = self._serialize_selected_items()
        if not item_dicts:
            return
        self._deserialize_items(item_dicts, duplicate_files)

    def _share_item_edit_actions(self):
        """Adds generic actions to project tree view and Design View."""
        actions = [
            self.ui.actionCopy,
            self.ui.actionPaste,
            self.ui.actionPasteAndDuplicateFiles,
            self.ui.actionDuplicate,
            self.ui.actionDuplicateAndDuplicateFiles,
            self.ui.actionRemove,
        ]
        for action in actions:
            action.setShortcutContext(Qt.WidgetShortcut)
            self.ui.treeView_project.addAction(action)
            self.ui.graphicsView.addAction(action)

    @Slot(str, str)
    def _show_message_box(self, title, message):
        """Shows an information message box."""
        QMessageBox.information(self, title, message)

    @Slot(str, str)
    def _show_error_box(self, title, message):
        box = QErrorMessage(self)
        box.setWindowTitle(title)
        box.setWindowModality(Qt.ApplicationModal)
        box.showMessage(message)

    def _connect_project_signals(self):
        """Connects signals emitted by project."""
        self._project.project_execution_about_to_start.connect(self._set_execution_in_progress)
        self._project.project_execution_finished.connect(self._unset_execution_in_progress)
        self._project.item_added.connect(self.set_icon_and_properties_ui)
        self._project.item_added.connect(self.ui.graphicsView.add_icon)
        self._project.item_about_to_be_removed.connect(self.ui.graphicsView.remove_icon)
        self._project.connection_established.connect(self.ui.graphicsView.do_add_link)
        self._project.connection_updated.connect(self.ui.graphicsView.do_update_link)
        self._project.connection_about_to_be_removed.connect(self.ui.graphicsView.do_remove_link)
        self._project.jump_added.connect(self.ui.graphicsView.do_add_jump)
        self._project.jump_about_to_be_removed.connect(self.ui.graphicsView.do_remove_jump)
        self._project.jump_updated.connect(self.ui.graphicsView.do_update_jump)
        self._project.specification_added.connect(self.repair_specification)
        self._project.specification_saved.connect(self._log_specification_saved)

    @Slot(bool)
    def _execute_project(self, _=False):
        """Executes all DAGs in project."""
        if self._project is None:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        self._project.execute_project()

    @Slot(bool)
    def _execute_selection(self, _=False):
        """Executes selected items."""
        if self._project is None:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        self._project.execute_selected(self._selected_item_names)

    @Slot(bool)
    def _stop_execution(self, _=False):
        """Stops execution in progress."""
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        self._project.stop()

    @Slot()
    def _set_execution_in_progress(self):
        self.execution_in_progress = True
        self.ui.actionExecute_project.setEnabled(False)
        self.ui.actionExecute_selection.setEnabled(False)
        self.ui.actionStop_execution.setEnabled(True)
        self.ui.textBrowser_eventlog.verticalScrollBar().setValue(
            self.ui.textBrowser_eventlog.verticalScrollBar().maximum()
        )

    @Slot()
    def _unset_execution_in_progress(self):
        self.execution_in_progress = False
        self._update_execute_enabled()
        self._update_execute_selected_enabled()
        self.ui.actionStop_execution.setEnabled(False)

    @Slot(str)
    def set_icon_and_properties_ui(self, item_name):
        """Adds properties UI to given project item.

        Args:
            item_name (str): item's name
        """
        project_item = self._project.get_item(item_name)
        icon = self.project_item_icon(project_item.item_type())
        project_item.set_icon(icon)
        properties_ui = self.project_item_properties_ui(project_item.item_type())
        project_item.set_properties_ui(properties_ui)

    def project_item_properties_ui(self, item_type):
        """Returns the properties tab widget's ui.

        Args:
            item_type (str): project item's type

        Returns:
            QWidget: item's properties tab widget
        """
        return self._item_properties_uis[item_type].ui

    def project_item_icon(self, item_type):
        return self.item_factories[item_type].make_icon(self)

    @Slot(bool)
    def _open_project_directory(self, _):
        """Opens project's root directory in system's file browser."""
        if self._project is None:
            self.msg.emit("Please open or create a project first")
            return
        open_url("file:///" + self._project.project_dir)

    @Slot(bool)
    def _open_project_item_directory(self, _):
        """Opens project item's directory in system's file browser."""
        selection_model = self.ui.treeView_project.selectionModel()
        current = selection_model.currentIndex()
        if not current.isValid():
            return
        item = self.project_item_model.item(current)
        item.project_item.open_directory()

    @Slot(bool)
    def _remove_selected_items(self, _):
        """Pushes commands to remove selected project items and links from project."""
        selected_items = self.ui.graphicsView.scene().selectedItems()
        if not selected_items:
            return
        project_item_names = set()
        has_connections = False
        for item in selected_items:
            if isinstance(item, ProjectItemIcon):
                project_item_names.add(item.name())
            elif isinstance(item, (JumpLink, Link)):
                has_connections = True
        if not project_item_names and not has_connections:
            return
        delete_data = int(self._qsettings.value("appSettings/deleteData", defaultValue="0")) != 0
        if project_item_names:
            msg = f"Remove item(s) <b>{', '.join(project_item_names)}</b> from project? "
            if not delete_data:
                msg += "Item data directory will still be available in the project directory after this operation."
            else:
                msg += "<br><br><b>Warning: Item data will be permanently lost after this operation.</b>"
            # noinspection PyCallByClass, PyTypeChecker
            message_box = QMessageBox(
                QMessageBox.Icon.Question,
                "Remove Item",
                msg,
                buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.StandardButton.Ok).setText("Remove Item")
            answer = message_box.exec()
            if answer != QMessageBox.StandardButton.Ok:
                return
        self.undo_stack.beginMacro("remove items and links")
        if project_item_names:
            self.undo_stack.push(
                RemoveProjectItemsCommand(self._project, self.item_factories, list(project_item_names), delete_data)
            )
        self.ui.graphicsView.remove_selected_links()
        self.undo_stack.endMacro()

    @Slot(bool)
    def _rename_project_item(self, _):
        """Renames current project item."""
        selection_model = self.ui.treeView_project.selectionModel()
        current = selection_model.currentIndex()
        if not current.isValid():
            return
        item = self.project_item_model.item(current)
        answer = QInputDialog.getText(
            self, "Rename Item", "New name:", text=item.name, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        if not answer[1]:
            return
        new_name = answer[0]
        self.undo_stack.push(RenameProjectItemCommand(self._project, item.name, new_name))

    def item_category_context_menu(self):
        """Creates a context menu for category items.

        Returns:
            QMenu: category context menu
        """
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        menu.addAction(self.ui.actionOpen_project_directory)
        return menu

    def project_item_context_menu(self, additional_actions):
        """Creates a context menu for project items.

        Args:
            additional_actions (list of QAction): actions to be prepended to the menu

        Returns:
            QMenu: project item context menu
        """
        menu = QMenu(self)
        menu.setToolTipsVisible(True)
        if additional_actions:
            for action in additional_actions:
                menu.addAction(action)
            menu.addSeparator()
        menu.addAction(self.ui.actionCopy)
        menu.addAction(self.ui.actionPaste)
        menu.addAction(self.ui.actionPasteAndDuplicateFiles)
        menu.addAction(self.ui.actionDuplicate)
        menu.addAction(self.ui.actionDuplicateAndDuplicateFiles)
        menu.addAction(self.ui.actionOpen_item_directory)
        menu.addSeparator()
        menu.addAction(self.ui.actionRemove)
        menu.addSeparator()
        menu.addAction(self.ui.actionRename_item)
        menu.aboutToShow.connect(self.refresh_edit_action_states)
        menu.aboutToHide.connect(self.enable_edit_actions)
        return menu

    @Slot(str, QIcon, bool)
    def start_detached_jupyter_console(self, kernel_name, icon, conda):
        """Launches a new detached Console with the given kernel
        name or activates an existing Console if the kernel is
        already running.

        Args:
            kernel_name (str): Requested kernel name
            icon (QIcon): Icon representing the kernel language
            conda (bool): Is this a Conda kernel?
        """
        for cw in self._jupyter_consoles.values():
            if cw.kernel_name == kernel_name and None in cw.owners:
                # Console running the requested kernel already exists, show and activate it
                if cw.isMinimized():
                    cw.showNormal()
                cw.activateWindow()
                return
        self.msg.emit(f"Starting kernel {kernel_name} in a detached Jupyter Console")
        c = JupyterConsoleWidget(self, kernel_name, owner=None)
        connection_file = c.request_start_kernel(conda)
        if not connection_file:
            return
        c.set_connection_file(connection_file)
        c.setWindowIcon(icon)
        c.setWindowTitle(f"{kernel_name} on Jupyter Console [Detached]")
        c.connect_to_kernel()
        self._jupyter_consoles[connection_file] = c
        c.console_closed.connect(self._cleanup_jupyter_console)
        c.show()

    @Slot(object, str, str, str, dict)
    def _setup_jupyter_console(self, item, filter_id, kernel_name, connection_file, connection_file_dict):
        """Sets up jupyter console, eventually for a filter execution.

        Args:
            item (ProjectItem): Item
            filter_id (str): Filter identifier
            kernel_name (str): Jupyter kernel name
            connection_file (str): Path to connection file
            connection_file_dict (dict): Contents of connection file when kernel manager runs on Spine Engine Server
        """
        connection_file = solve_connection_file(connection_file, connection_file_dict)
        if not filter_id:
            self._item_consoles[item] = self._make_jupyter_console(item, kernel_name, connection_file)
        else:
            d = self._filter_item_consoles.setdefault(item, dict())
            d[filter_id] = self._make_jupyter_console(item, kernel_name, connection_file)
        self.override_console_and_execution_list()

    @Slot(object, str)
    def _handle_kernel_shutdown(self, item, filter_id):
        """Closes the kernel client when kernel manager has been shutdown due to an
        enabled 'Kill consoles at the end of execution' option.

        Args:
            item (ProjectItem): Item
            filter_id (str): Filter identifier
        """
        console = self._get_console(item, filter_id)
        console.insert_text_to_console(
            "\n\nConsole killed (can be restarted from the right-click menu or by executing the item again)"
        )
        console.shutdown_kernel_client()

    @Slot(object, str, tuple, str)
    def _setup_persistent_console(self, item, filter_id, key, language):
        """Sets up persistent console, eventually for a filter execution.

        Args:
            item (ProjectItem): Item
            filter_id (str): Filter identifier
            key (tuple): Key
            language (str): Language (e.g. 'python' or 'julia')
        """
        if not filter_id:
            self._item_consoles[item] = self._make_persistent_console(item, key, language)
        else:
            d = self._filter_item_consoles.setdefault(item, dict())
            d[filter_id] = self._make_persistent_console(item, key, language)
        self.override_console_and_execution_list()

    def persistent_killed(self, item, filter_id):
        self._get_console(item, filter_id).set_killed(True)

    def add_persistent_stdin(self, item, filter_id, data):
        self._get_console(item, filter_id).add_stdin(data)

    def add_persistent_stdout(self, item, filter_id, data):
        self._get_console(item, filter_id).add_stdout(data)

    def add_persistent_stderr(self, item, filter_id, data):
        self._get_console(item, filter_id).add_stderr(data)

    def _get_console(self, item, filter_id):
        if not filter_id:
            return self._item_consoles[item]
        return self._filter_item_consoles[item][filter_id]

    def _make_jupyter_console(self, item, kernel_name, connection_file):
        """Creates a new JupyterConsoleWidget for given connection file if none exists yet, and returns it.

        Args:
            item (ProjectItem): Item that owns the console
            kernel_name (str): Name of the kernel
            connection_file (str): Path of kernel connection file

        Returns:
            JupyterConsoleWidget
        """
        console = self._jupyter_consoles.get(connection_file)
        if console is not None:
            console.owners.add(item)
            return console
        console = self._jupyter_consoles[connection_file] = JupyterConsoleWidget(self, kernel_name, owner=item)
        console.set_connection_file(connection_file)
        console.connect_to_kernel()
        return console

    def _make_persistent_console(self, item, key, language):
        """Creates a new PersistentConsoleWidget for given process key.

        Args:
            item (ProjectItem): Item that owns the console
            key (tuple): persistent process key in spine engine
            language (str): for syntax highlighting and prompting, etc.

        Returns:
            PersistentConsoleWidget
        """
        console = self._persistent_consoles.get(key)
        if console is not None:
            console.owners.add(item)
            return console
        console = self._persistent_consoles[key] = PersistentConsoleWidget(self, key, language, owner=item)
        return console

    @Slot(str)
    def _cleanup_jupyter_console(self, conn_file):
        """Removes reference to a Jupyter Console and closes the kernel manager on Engine."""
        c = self._jupyter_consoles.pop(conn_file, None)
        if not c:
            return
        exec_remotely = self.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        engine_mngr = make_engine_manager(exec_remotely)
        engine_mngr.shutdown_kernel(conn_file)

    def _shutdown_engine_kernels(self):
        """Shuts down all persistent and Jupyter kernels managed by Spine Engine."""
        exec_remotely = self.qsettings().value("engineSettings/remoteExecutionEnabled", "false") == "true"
        engine_mngr = make_engine_manager(exec_remotely)
        for key in self._persistent_consoles.keys():
            engine_mngr.kill_persistent(key)
        for connection_file in self._jupyter_consoles:
            engine_mngr.shutdown_kernel(connection_file)

    def _close_consoles(self):
        """Closes all Persistent and Jupyter Console widgets."""
        while self._persistent_consoles:
            self._persistent_consoles.popitem()[1].close()
        while self._jupyter_consoles:
            self._jupyter_consoles.popitem()[1].close()
        while self._item_consoles:
            self._item_consoles.popitem()[1].close()
        while self._filter_item_consoles:
            fic = self._filter_item_consoles.popitem()
            # fic is a tuple (ProjectItem, {f_id_0: console_0, f_id_1:console_1, ... , f_id_n:console_n})
            for console in fic[1].values():
                console.close()

    def restore_and_activate(self):
        """Brings the app main window into focus."""
        if self.isMinimized():
            self.showNormal()
        self.activateWindow()

    @staticmethod
    def _make_log_entry_title(title):
        return f'<b>{title}</b>'

    def start_execution(self, timestamp):
        """Starts execution.

        Args:
            timestamp (str): time stamp
        """
        self.ui.textBrowser_eventlog.start_execution(timestamp)

    def add_log_message(self, item_name, filter_id, message):
        """Adds a message to an item's execution log.

        Args:
            item_name (str): item name
            filter_id (str): filter identifier
            message (str): formatted message
        """
        self.ui.textBrowser_eventlog.add_log_message(item_name, filter_id, message)
