######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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

:author: P. Savolainen (VTT)
:date:   14.12.2017
"""

import os
import locale
import logging
import json
import pathlib
import numpy as np
from PySide2.QtCore import QByteArray, QItemSelection, QMimeData, QModelIndex, QPoint, Qt, Signal, Slot, QSettings, QUrl
from PySide2.QtGui import QDesktopServices, QGuiApplication, QKeySequence, QIcon, QCursor
from PySide2.QtWidgets import (
    QMainWindow,
    QApplication,
    QErrorMessage,
    QFileDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
    QCheckBox,
    QDockWidget,
    QAction,
    QUndoStack,
)
from spine_engine.utils.serialization import serialize_path, deserialize_path
from spine_engine.utils.helpers import shorten
from .spine_db_editor.widgets.spine_db_editor import SpineDBEditor
from .graphics_items import ProjectItemIcon
from .category import CATEGORIES, CATEGORY_DESCRIPTIONS
from .load_project_items import load_item_specification_factories, load_project_items
from .mvcmodels.project_item_model import ProjectItemModel
from .mvcmodels.project_item_factory_models import ProjectItemSpecFactoryModel, FilteredSpecFactoryModel
from .mvcmodels.filter_execution_model import FilterExecutionModel
from .widgets.about_widget import AboutWidget
from .widgets.custom_menus import LinkContextMenu, RecentProjectsPopupMenu
from .widgets.settings_widget import SettingsWidget
from .widgets.custom_qwidgets import ZoomWidgetAction
from .widgets.spine_console_widget import SpineConsoleWidget
from .widgets import toolbars
from .widgets.open_project_widget import OpenProjectDialog
from .widgets.link_properties_widget import LinkPropertiesWidget
from .project import SpineToolboxProject
from .config import (
    STATUSBAR_SS,
    TEXTBROWSER_SS,
    MAINWINDOW_SS,
    DOCUMENTATION_PATH,
    _program_root,
    LATEST_PROJECT_VERSION,
    DEFAULT_WORK_DIR,
    PROJECT_FILENAME,
)
from .helpers import (
    create_dir,
    ensure_window_is_on_screen,
    set_taskbar_icon,
    supported_img_formats,
    recursive_overwrite,
    ChildCyclingKeyPressFilter,
    open_url,
    busy_effect,
    format_event_message,
    format_process_message,
)
from .project_upgrader import ProjectUpgrader
from .project_tree_item import LeafProjectTreeItem, CategoryProjectTreeItem, RootProjectTreeItem
from .project_commands import (
    AddSpecificationCommand,
    RemoveSpecificationCommand,
    RenameProjectItemCommand,
    UpdateSpecificationCommand,
)
from .configuration_assistants import spine_opt


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
    specification_model_changed = Signal()

    def __init__(self):
        """Initializes application and main window."""
        from .ui.mainwindow import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(flags=Qt.Window)
        self._qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set number formatting to use user's default settings
        locale.setlocale(locale.LC_NUMERIC, 'C')
        # Setup the user interface from Qt Designer files
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        set_taskbar_icon()  # in helpers.py
        self.ui.graphicsView.set_ui(self)
        self.key_press_filter = ChildCyclingKeyPressFilter()
        self.ui.tabWidget_item_properties.installEventFilter(self.key_press_filter)
        self._create_item_edit_actions()
        self.ui.listView_executions.setModel(FilterExecutionModel(self))
        # Set style sheets
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.textBrowser_eventlog.setStyleSheet(TEXTBROWSER_SS)
        self.ui.textBrowser_processlog.setStyleSheet(TEXTBROWSER_SS)
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
        self.active_link = None
        self.sync_item_selection_with_scene = True
        self.link_properties_widget = LinkPropertiesWidget(self)
        self._saved_specification = None
        # Widget and form references
        self.settings_form = None
        self.specification_context_menu = None
        self.link_context_menu = None
        self.process_output_context_menu = None
        self.add_project_item_form = None
        self.specification_form = None
        self.zoom_widget_action = None
        self.recent_projects_menu = RecentProjectsPopupMenu(self)
        # Make and initialize toolbars
        self.main_toolbar = toolbars.MainToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        # Make julia REPL
        self.julia_console = SpineConsoleWidget(self, "Julia Console")
        self.ui.dockWidgetContents_julia_console.layout().addWidget(self.julia_console)
        # Make Python REPL
        self.python_console = SpineConsoleWidget(self, "Python Console")
        self.ui.dockWidgetContents_python_console.layout().addWidget(self.python_console)
        # Setup main window menu
        self.setup_zoom_widget_action()
        self.add_menu_actions()
        # Hidden QActions for debugging or testing
        self.show_properties_tabbar = QAction(self)
        self.show_supported_img_formats = QAction(self)
        self.set_debug_qactions()
        self.ui.tabWidget_item_properties.tabBar().hide()  # Hide tab bar in properties dock widget
        # Finalize init
        self._proposed_item_name_counts = dict()
        self.ui.actionSave.setDisabled(True)
        self.ui.actionSave_As.setDisabled(True)
        self.connect_signals()
        self.restore_ui()
        self.ui.dockWidget_executions.hide()
        self.parse_project_item_modules()
        self.parse_assistant_modules()
        self.main_toolbar.setup()
        self.set_work_directory()

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
        self.ui.actionSave.triggered.connect(self.save_project)
        self.ui.actionSave_As.triggered.connect(self.save_project_as)
        self.ui.actionExport_project_to_GraphML.triggered.connect(self.export_as_graphml)
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionRemove_all.triggered.connect(self.remove_all_items)
        self.ui.actionUser_Guide.triggered.connect(self.show_user_guide)
        self.ui.actionGetting_started.triggered.connect(self.show_getting_started_guide)
        self.ui.actionAbout.triggered.connect(self.show_about)
        # noinspection PyArgumentList
        self.ui.actionAbout_Qt.triggered.connect(lambda: QApplication.aboutQt())  # pylint: disable=unnecessary-lambda
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        self.ui.actionCopy.triggered.connect(self.project_item_to_clipboard)
        self.ui.actionPaste.triggered.connect(self.project_item_from_clipboard)
        self.ui.actionDuplicate.triggered.connect(self.duplicate_project_item)
        self.ui.actionOpen_project_directory.triggered.connect(self._open_project_directory)
        self.ui.actionOpen_item_directory.triggered.connect(self._open_project_item_directory)
        self.ui.actionRename_item.triggered.connect(self._rename_project_item)
        self.ui.actionRemove.triggered.connect(self._remove_item)
        # Debug actions
        self.show_properties_tabbar.triggered.connect(self.toggle_properties_tabbar_visibility)
        self.show_supported_img_formats.triggered.connect(supported_img_formats)  # in helpers.py
        # Context-menus
        self.ui.treeView_project.customContextMenuRequested.connect(self.show_item_context_menu)
        # Zoom actions
        self.zoom_widget_action.minus_pressed.connect(self._handle_zoom_minus_pressed)
        self.zoom_widget_action.plus_pressed.connect(self._handle_zoom_plus_pressed)
        self.zoom_widget_action.reset_pressed.connect(self._handle_zoom_reset_pressed)
        # Undo stack
        self.undo_stack.cleanChanged.connect(self.update_window_modified)
        # Log views
        self.ui.listView_executions.selectionModel().currentChanged.connect(self._select_execution)
        self.ui.listView_executions.model().layoutChanged.connect(self._refresh_execution_list)

    @Slot(bool)
    def update_window_modified(self, clean):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        try:
            self.setWindowModified(not clean)
        except RuntimeError as e:
            raise e
        self.ui.actionSave.setDisabled(clean)

    def parse_project_item_modules(self):
        """Collects data from project item factories."""
        self._item_categories, self.item_factories = load_project_items(self)
        self._item_specification_factories = load_item_specification_factories()
        for item_type, factory in self.item_factories.items():
            self._item_properties_uis[item_type] = factory.make_properties_widget(self)

    def parse_assistant_modules(self):
        """Makes actions to run assistants from assistant modules."""
        menu = self.ui.menuTool_configuration_assistants
        for module in (spine_opt,):  # NOTE: add others as needed
            action = menu.addAction(module.assistant_name)
            action.triggered.connect(
                lambda checked=False, module=module, action=action: self.show_assistant(module, action)
            )

    def show_assistant(self, module, action):
        """Creates and shows the assistant for the given module.
        Disables the given action while the assistant is shown,
        enables the action back when the assistant is destroyed.
        This is to make sure we don't open the same assistant twice.
        """
        assistant = module.make_assistant(self)
        action.setEnabled(False)
        assistant.destroyed.connect(lambda obj=None: action.setEnabled(True))
        assistant.show()

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
        """Returns current project or None if no project open."""
        return self._project

    def qsettings(self):
        """Returns application preferences object."""
        return self._qsettings

    def update_window_title(self):
        self.setWindowTitle("{0} [{1}][*] - Spine Toolbox".format(self._project.name, self._project.project_dir))

    @Slot()
    def init_project(self, project_dir):
        """Initializes project at application start-up. Opens the last project that was open
        when app was closed (if enabled in Settings) or starts the app without a project.
        """
        p = os.path.join(DOCUMENTATION_PATH, "getting_started.html")
        getting_started_anchor = (
            "<a style='color:#99CCFF;' title='"
            + p
            + "' href='https://spine-toolbox.readthedocs.io/en/latest/getting_started.html'>Getting Started</a>"
        )
        welcome_msg = "Welcome to Spine Toolbox! If you need help, please read the {0} guide.".format(
            getting_started_anchor
        )
        if not project_dir:
            open_previous_project = int(self._qsettings.value("appSettings/openPreviousProject", defaultValue="0"))
            if open_previous_project != Qt.Checked:  # 2: Qt.Checked, ie. open_previous_project==True
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
            self.ui.statusbar.showMessage("Opening previous project failed", 10000)
            self.msg_error.emit(
                "Cannot open previous project. Directory <b>{0}</b> may have been moved.".format(project_dir)
            )
            return
        self.open_project(project_dir, clear_logs=False)

    @Slot()
    def new_project(self):
        """Opens a file dialog where user can select a directory where a project is created.
        Pops up a question box if selected directory is not empty or if it already contains
        a Spine Toolbox project. Initial project name is the directory name.
        """
        recents = self.qsettings().value("appSettings/recentProjectStorages", defaultValue=None)
        if not recents:
            initial_path = _program_root
        else:
            recents_lst = str(recents).split("\n")
            if not os.path.isdir(recents_lst[0]):
                # Remove obsolete entry from recentProjectStorages
                OpenProjectDialog.remove_directory_from_recents(recents_lst[0], self.qsettings())
                initial_path = _program_root
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
        _, project_name = os.path.split(project_dir)
        self.create_project(project_name, "", project_dir)

    def create_project(self, name, description, location):
        """Creates new project and sets it active.

        Args:
            name (str): Project name
            description (str): Project description
            location (str): Path to project directory
        """
        self.undo_critical_commands()
        self.clear_ui()
        self.init_project_item_model()
        self.ui.treeView_project.selectionModel().selectionChanged.connect(self.item_selection_changed)
        self._project = SpineToolboxProject(
            self,
            name,
            description,
            location,
            self.project_item_model,
            settings=self._qsettings,
            embedded_julia_console=self.julia_console,
            embedded_python_console=self.python_console,
            logger=self,
        )
        self._project.connect_signals()
        self._connect_project_signals()
        self.init_specification_model(list())  # Start project with no specifications
        self.update_window_title()
        self.ui.actionSave_As.setEnabled(True)
        self.ui.graphicsView.reset_zoom()
        # Update recentProjects
        self.update_recent_projects()
        # Update recentProjectStorages
        OpenProjectDialog.update_recents(os.path.abspath(os.path.join(location, os.path.pardir)), self.qsettings())
        self.save_project()
        # Clear text browsers
        self.ui.textBrowser_eventlog.clear()
        self.ui.textBrowser_processlog.clear()
        self.msg.emit("New project <b>{0}</b> is now open".format(self._project.name))

    @Slot()
    def open_project(self, load_dir=None, clear_logs=True):
        """Opens project from a selected or given directory.

        Args:
            load_dir (str): Path to project base directory. If default value is used,
            a file explorer dialog is opened where the user can select the
            project to open.
            clear_logs (bool): True clears Event and Process Log, False does not

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
                    start_dir = ""
                else:
                    start_dir = str(recents).split("\n")[0]
                load_dir = QFileDialog.getExistingDirectory(self, caption="Open Spine Toolbox Project", dir = start_dir)
                if not load_dir:
                    return False  # Cancelled
                if not os.path.isfile(os.path.join(load_dir, ".spinetoolbox", PROJECT_FILENAME)):
                    self.msg_warning.emit(f"Opening project failed. <b>{load_dir}</b> is not a Spine Toolbox project.")
                    return False
                # TODO: Save load_dir parent directory to "appSettings/recentProjectStorages"
        load_path = os.path.abspath(os.path.join(load_dir, ".spinetoolbox", PROJECT_FILENAME))
        try:
            with open(load_path, "r") as fh:
                try:
                    proj_info = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self.msg_error.emit("Error in project file <b>{0}</b>. Invalid JSON.".format(load_path))
                    return False
        except OSError:
            # Remove path from recent projects
            self.remove_path_from_recent_projects(load_dir)
            self.msg_error.emit("Project file <b>{0}</b> missing".format(load_path))
            return False
        return self.restore_project(proj_info, load_dir, clear_logs)

    def restore_project(self, project_info, project_dir, clear_logs):
        """Initializes UI, Creates project, models, connections, etc., when opening a project.

        Args:
            project_info (dict): Project information dictionary
            project_dir (str): Project directory
            clear_logs (bool): True clears Event and Process Log, False does not

        Returns:
            bool: True when restoring project succeeded, False otherwise
        """
        self.undo_critical_commands()
        # Make room for a new project
        self.clear_ui()
        # Clear text browsers
        if clear_logs:
            self.ui.textBrowser_eventlog.clear()
            self.ui.textBrowser_processlog.clear()
        # Check if project dictionary needs to be upgraded
        project_info = ProjectUpgrader(self).upgrade(project_info, project_dir)
        if not project_info:
            return False
        if not ProjectUpgrader(self).is_valid(LATEST_PROJECT_VERSION, project_info):  # Check project info validity
            self.msg_error.emit(f"Opening project in directory {project_dir} failed")
            return False
        # Parse project info
        name = project_info["project"]["name"]  # Project name
        desc = project_info["project"]["description"]  # Project description
        spec_paths_per_type = project_info["project"]["specifications"]
        connections = project_info["project"]["connections"]
        project_items = project_info["items"]
        # Init project item model
        self.init_project_item_model()
        self.ui.treeView_project.selectionModel().selectionChanged.connect(self.item_selection_changed)
        # Create project
        self._project = SpineToolboxProject(
            self,
            name,
            desc,
            project_dir,
            self.project_item_model,
            settings=self._qsettings,
            embedded_julia_console=self.julia_console,
            embedded_python_console=self.python_console,
            logger=self,
        )
        self._connect_project_signals()
        self.update_window_title()
        self.ui.actionSave.setDisabled(True)
        self.ui.actionSave_As.setEnabled(True)
        # Init tool spec model. We don't use the information on the item type in spec_paths_per_type, but we could...
        deserialized_paths = [
            deserialize_path(path, self._project.project_dir)
            for paths in spec_paths_per_type.values()
            for path in paths
        ]
        self.init_specification_model(deserialized_paths)
        # Populate project model with project items
        if not self._project.load(project_items):
            self.msg_error.emit("Loading project items failed")
            return False
        self.ui.treeView_project.expandAll()
        # Restore connections
        self.msg.emit("Restoring connections...")
        self.ui.graphicsView.restore_links(connections)
        # Simulate project execution after restoring links
        self._project.notify_changes_in_all_dags()
        self._project.connect_signals()
        # Reset zoom on Design View
        self.ui.graphicsView.reset_zoom()
        self.update_recent_projects()
        self.msg.emit("Project <b>{0}</b> is now open".format(self._project.name))
        return True

    @Slot()
    def show_recent_projects_menu(self):
        """Updates and sets up the recent projects menu to File-Open recent menu item."""
        if not self.recent_projects_menu.isVisible():
            self.recent_projects_menu = RecentProjectsPopupMenu(self)
            self.ui.actionOpen_recent.setMenu(self.recent_projects_menu)

    @Slot()
    def save_project(self):
        """Save project."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        # Save specs
        for spec in self.specification_model.specifications():
            if not spec.save():
                self.msg_error.emit("Project saving failed")
                return
        # Put project's specification definition files into a dict by item type
        serialized_tool_spec_paths = dict()
        for spec in self.specification_model.specifications():
            serialized_path = serialize_path(spec.definition_file_path, self._project.project_dir)
            serialized_tool_spec_paths.setdefault(spec.item_type, []).append(serialized_path)
        if not self._project.save(serialized_tool_spec_paths):
            self.msg_error.emit("Project saving failed")
            return
        self.msg.emit(f"Project <b>{self._project.name}</b> saved")
        self.undo_stack.setClean()

    @Slot()
    def save_project_as(self):
        """Ask user for a new project name and save. Creates a duplicate of the open project."""
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
        # Check and ask what to do if selected directory is not empty
        if not self.overwrite_check(answer):
            return
        self.msg.emit("Saving project to directory {0}".format(answer))
        recursive_overwrite(self, self._project.project_dir, answer, silent=False)
        # Get the project info from the new directory and restore project
        config_file_path = os.path.join(answer, ".spinetoolbox", "project.json")
        try:
            with open(config_file_path, "r") as fh:
                try:
                    proj_info = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self.msg_error.emit("Error in project file <b>{0}</b>. Invalid JSON. {0}".format(config_file_path))
                    return
        except OSError:
            self.msg_error.emit("[OSError] Opening project file <b>{0}</b> failed".format(config_file_path))
            return
        if not self.restore_project(proj_info, answer, clear_logs=False):
            return
        # noinspection PyCallByClass, PyArgumentList
        QMessageBox.information(self, f"Project {self._project.name} saved", f"Project directory is now\n\n{answer}")
        self.undo_stack.setClean()

    def init_project_item_model(self):
        """Initializes project item model. Create root and category items and
        add them to the model."""
        root_item = RootProjectTreeItem()
        self.project_item_model = ProjectItemModel(self, root=root_item)
        for category in CATEGORIES:
            category_item = CategoryProjectTreeItem(str(category), CATEGORY_DESCRIPTIONS[category])
            self.project_item_model.insert_item(category_item)
        self.ui.treeView_project.setModel(self.project_item_model)
        self.ui.treeView_project.header().hide()
        self.ui.graphicsView.set_project_item_model(self.project_item_model)

    def init_specification_model(self, specification_paths):
        """Initializes Tool specification model.

        Args:
            specification_paths (list): List of tool definition file paths used in this project
        """
        factory_icons = {name: QIcon(factory.icon()) for name, factory in self.item_factories.items()}
        self.specification_model = ProjectItemSpecFactoryModel(factory_icons)
        self.filtered_spec_factory_models = {name: FilteredSpecFactoryModel(name) for name in self.item_factories}
        for model in self.filtered_spec_factory_models.values():
            model.setSourceModel(self.specification_model)
        n_specs = 0
        self.msg.emit("Loading specifications...")
        for path in specification_paths:
            if not path:
                continue
            # Add tool specification into project
            spec = self.load_specification_from_file(path)
            if not spec:
                continue
            n_specs += 1
            # Add tool definition file path to tool instance variable
            spec.definition_file_path = path
            # Insert tool into model
            self.specification_model.insertRow(spec)
        # Set model to Tool project item combo box
        self.specification_model_changed.emit()
        if n_specs == 0:
            self.msg_warning.emit("Project has no specifications")

    def load_specification_from_file(self, def_path):
        """Returns an Item specification from a definition file.

        Args:
            def_path (str): Path of the specification definition file

        Returns:
            ProjectItemSpecification: item specification or None if reading the file failed
        """
        try:
            with open(def_path, "r") as fp:
                try:
                    definition = json.load(fp)
                except ValueError:
                    self.msg_error.emit("Item specification file not valid")
                    logging.exception("Loading JSON data failed")
                    return None
        except FileNotFoundError:
            self.msg_error.emit("Specification file <b>{0}</b> does not exist".format(def_path))
            return None
        item_type = definition.get("item_type", "Tool")
        if item_type == "Tool":
            includes_main_path = definition.get("includes_main_path", ".")
            if not os.path.isabs(includes_main_path):
                definition["includes_main_path"] = os.path.normpath(
                    os.path.join(os.path.dirname(def_path), includes_main_path)
                )
        spec = self.load_specification(definition)
        if spec is not None:
            spec.definition_file_path = def_path
        return spec

    def load_specification(self, definition):
        """Returns Item specification from a definition dictionary.

        Args:
            definition (dict): Dictionary with the definition

        Returns:
            ProjectItemSpecification or NoneType: specification or None if specification factory was not found
        """
        # NOTE: Default to Tools so tool-specs work out of the box
        item_type = definition.get("item_type", "Tool")
        factory = self._item_specification_factories.get(item_type)
        if factory is None:
            return None
        return factory.make_specification(definition, self._qsettings, self, self.julia_console, self.python_console)

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
        if not self.project():
            return
        self.activate_no_selection_tab()  # Clear properties widget
        self._project.deleteLater()
        self._project = None
        self.ui.graphicsView.scene().clear()  # Clear all items from scene

    def undo_critical_commands(self):
        """Undoes critical commands in the undo stack.
        """
        if self.undo_stack.isClean():
            return
        for ind in reversed(range(self.undo_stack.index())):
            cmd = self.undo_stack.command(ind)
            if cmd.is_critical():
                cmd.undo()

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
                    QMessageBox.Question, "Overwrite?", msg1, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self
                )
                box1.button(QMessageBox.Ok).setText("Overwrite")
                answer1 = box1.exec_()
                if answer1 != QMessageBox.Ok:
                    return False
            else:
                msg2 = (
                    "Directory <b>{0}</b> is not empty.<br/><br/>"
                    "Would you like to make this directory into a Spine Toolbox project?".format(project_dir)
                )
                box2 = QMessageBox(
                    QMessageBox.Question, "Not empty", msg2, buttons=QMessageBox.Ok | QMessageBox.Cancel, parent=self
                )
                box2.button(QMessageBox.Ok).setText("Go ahead")
                answer2 = box2.exec_()
                if answer2 != QMessageBox.Ok:
                    return False
        return True

    @Slot(QItemSelection, QItemSelection)
    def item_selection_changed(self, selected, deselected):
        """Synchronizes selection with scene. The scene handles item/link de/activation.
        """
        if not self.sync_item_selection_with_scene:
            return
        inds = self.ui.treeView_project.selectedIndexes()
        proj_items = [self.project_item_model.item(i).project_item for i in inds]
        proj_item_names = {i.name for i in proj_items}
        scene = self.ui.graphicsView.scene()
        for icon in scene.project_item_icons():
            icon.setSelected(icon.name() in proj_item_names)

    def refresh_active_elements(self, new_active_project_item, new_active_link):
        self._set_active_project_item(new_active_project_item)
        self._set_active_link(new_active_link)
        if self.active_project_item:
            self.activate_item_tab()
        elif self.active_link:
            self.activate_link_tab()
        else:
            self.activate_no_selection_tab()

    def _set_active_project_item(self, new_active_project_item):
        """
        Args:
            new_active_project_item (ProjectItemBase or NoneType)
        """
        if self.active_project_item == new_active_project_item:
            return
        if self.active_project_item:
            # Deactivate old active project item
            if not self.active_project_item.deactivate():
                self.msg_error.emit(
                    "Something went wrong in disconnecting {0} signals".format(self.active_project_item.name)
                )
        self.active_project_item = new_active_project_item
        if self.active_project_item:
            self.active_project_item.activate()

    def _set_active_link(self, new_active_link):
        """
        Args:
            new_active_link (Link or NoneType)
        """
        if self.active_link == new_active_link:
            return
        if self.active_link:
            self.link_properties_widget.unset_link()
        self.active_link = new_active_link
        if self.active_link:
            self.link_properties_widget.set_link(self.active_link)

    def activate_no_selection_tab(self):
        """Shows 'No Selection' tab."""
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == "No Selection":
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.dockWidget_item.setWindowTitle("Properties")
        self.restore_original_event_log_document()
        self.restore_original_process_log_document()
        self.restore_original_python_console()
        self.restore_original_julia_console()
        self.ui.dockWidget_executions.hide()

    def activate_item_tab(self):
        """Shows active project item properties tab according to item type."""
        # Find tab index according to item type
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == self.active_project_item.item_type():
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        # Set QDockWidget title to selected item's type
        self.ui.dockWidget_item.setWindowTitle(self.active_project_item.item_type() + " Properties")
        self.override_event_log()
        self.override_process_log()
        self.override_python_console()
        self.override_julia_console()
        self.override_execution_list()

    def activate_link_tab(self):
        """Shows link properties tab."""
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == "Link properties":
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.dockWidget_item.setWindowTitle("Link properties")

    @Slot()
    def import_specification(self):
        """Opens a file dialog where the user can select an existing specification
        definition file (.json). If file is valid, calls add_specification().
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
        specification = self.load_specification_from_file(def_file)
        if not specification:
            return
        self.add_specification(specification)

    def _save_specificiation_file(self, specification):
        if specification.definition_file_path:
            return specification.save()
        specs_dir = self.project().specs_dir
        specs_type_dir = os.path.join(specs_dir, specification.item_type)
        try:
            create_dir(specs_type_dir)
        except OSError:
            self._logger.msg_error.emit("Creating directory {0} failed".format(specs_type_dir))
            specs_type_dir = specs_dir
        candidate_def_file_path = os.path.join(specs_type_dir, shorten(specification.name) + ".json")
        if not os.path.exists(candidate_def_file_path):
            specification.definition_file_path = candidate_def_file_path
            return specification.save()
        return self._prompt_to_save_specification_file(specification, candidate_def_file_path)

    def _prompt_to_save_specification_file(self, specification, candidate_def_file_path):
        answer = QFileDialog.getSaveFileName(
            self, f"Save {specification.item_type} specification", candidate_def_file_path, "JSON (*.json)"
        )
        if not answer[0]:  # Cancel button clicked
            return False
        specification.definition_file_path = os.path.abspath(answer[0])
        return specification.save()

    def _emit_specification_saved(self, specification):
        path = specification.definition_file_path
        self._saved_specification = specification
        self.msg_success.emit(
            f"Specification <b>{specification.name}</b> successfully saved as "
            f"<a style='color:#99CCFF;' href='file:///{path}'>{path}</a> "
            f"<a style='color:white;' href='change_spec_file'><b>[change]</b></a>"
        )

    def add_specification(self, specification):
        """Pushes a new AddSpecificationCommand to the undo stack."""
        if not self._save_specificiation_file(specification):
            return
        self._emit_specification_saved(specification)
        row = self.specification_model.specification_row(specification.name)
        if row >= 0:
            if self.specification_model.specification(row) != specification:
                button = QMessageBox.question(
                    self,
                    "Duplicate specification name",
                    f"There's already a specification called <b>{specification.name}</b> in the current project.<br>"
                    "Do you want to replace it?",
                )
                if button != QMessageBox.Yes:
                    return
            self.undo_stack.push(UpdateSpecificationCommand(self, row, specification))
        else:
            self.undo_stack.push(AddSpecificationCommand(self, specification))

    def update_specification(self, specification):
        if not self._save_specificiation_file(specification):
            return
        self._emit_specification_saved(specification)
        row = self.specification_model.specification_row(specification.name)
        if row >= 0:
            self.undo_stack.push(UpdateSpecificationCommand(self, row, specification))

    def do_add_specification(self, specification, row=None):
        """Adds a ProjectItemSpecification instance to project.

        Args:
            specification (ProjectItemSpecification): specification that is added to project
        """
        self.specification_model.insertRow(specification, row)
        self.msg_success.emit("Specification <b>{0}</b> added to project".format(specification.name))

    def do_update_specification(self, row, specification):
        """Updates a specification and refreshes all items that use it.

        Args:
            row (int): Row of tool specification in ProjectItemSpecFactoryModel
            specification (ProjectItemSpecification): An updated specification
        """
        if not self.specification_model.update_specification(row, specification):
            self.msg_error.emit(f"Unable to update specification <b>{specification.name}</b>")
            return
        self.msg_success.emit(f"Specification <b>{specification.name}</b> successfully updated")
        for item in self.project_item_model.items():
            project_item = item.project_item
            project_item_spec = project_item.specification()
            if project_item_spec is None or project_item_spec.name != specification.name:
                continue
            if project_item.do_set_specification(specification):
                self.msg_success.emit(
                    f"Specification <b>{specification.name}</b> successfully updated "
                    f"in Item <b>{project_item.name}</b>"
                )
            else:
                self.msg_warning.emit(
                    f"Specification <b>{specification.name}</b> "
                    f"of type <b>{specification.item_type}</b> "
                    f"is no longer valid for Item <b>{project_item.name}</b> "
                    f"of type <b>{project_item.item_type()}</b>"
                )
                project_item.do_set_specification(None)

    def undo_update_specification(self, row):
        """Reverts a specification update and refreshes all items that use it.

        Args:
            row (int): Row of item specification in ProjectItemSpecFactoryModel
        """
        if not self.specification_model.undo_update_specification(row):
            self.msg_error.emit(f"Unable to update specification at row <b>{row}</b>")
            return
        specification = self.specification_model.specification(row)
        self.msg_success.emit(f"Specification <b>{specification.name}</b> successfully updated")
        for item in self.project_item_model.items():
            project_item = item.project_item
            if project_item.undo_specification == specification:
                project_item.undo_set_specification()
                self.msg_success.emit(
                    f"Specification <b>{specification.name}</b> successfully updated "
                    f"in Item <b>{project_item.name}</b>"
                )

    def _get_specific_items(self, specification):
        """Yields project items with given specification.

        Args:
            specification (ProjectItemSpecification)
        """
        for item in self.project_item_model.items(specification.item_category):
            project_item = item.project_item
            if project_item.specification() == specification:
                yield project_item

    @Slot(bool)
    def remove_selected_specification(self, checked=False):
        """Removes specification selected in QListView."""
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        selected = self.main_toolbar.project_item_spec_list_view.selectedIndexes()
        if not selected:
            self.msg.emit("Select a specification to remove")
            return
        index = selected[0]
        if not index.isValid():
            return
        self.remove_specification(index.row())

    def remove_specification(self, row, ask_verification=True):
        self.undo_stack.push(RemoveSpecificationCommand(self, row, ask_verification=ask_verification))

    def do_remove_specification(self, row, ask_verification=True):
        """Removes specification from ProjectItemSpecFactoryModel.
        Removes also specifications from all items that use this specification.

        Args:
            row (int): Row in ProjectItemSpecFactoryModel
            ask_verification (bool): If True, displays a dialog box asking user to verify the removal
        """
        specification = self.specification_model.specification(row)
        if ask_verification:
            message = "Remove Specification <b>{0}</b> from Project?".format(specification.name)
            message_box = QMessageBox(
                QMessageBox.Question,
                "Remove Specification",
                message,
                buttons=QMessageBox.Ok | QMessageBox.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.Ok).setText("Remove Specification")
            answer = message_box.exec_()
            if answer != QMessageBox.Ok:
                return
        items_with_removed_spec = list(self._get_specific_items(specification))
        if not self.specification_model.removeRow(row):
            self.msg_error.emit("Error in removing specification <b>{0}</b>".format(specification.name))
            return
        self.msg_success.emit("Specification removed")
        for project_item in items_with_removed_spec:
            project_item.do_set_specification(None)
            self.msg.emit(
                "Specification <b>{0}</b> successfully removed from Item <b>{1}</b>".format(
                    specification.name, project_item.name
                )
            )

    @Slot()
    def remove_all_items(self):
        """Removes all items from project. Slot for Remove All button."""
        if not self._project:
            self.msg.emit("No project items to remove")
            return
        self._project.remove_all_items()

    @Slot(QUrl)
    def open_anchor(self, qurl):
        """Open file explorer in the directory given in qurl.

        Args:
            qurl (QUrl): The url to open
        """
        url = qurl.url()
        if url == "#":  # This is a Tip so do not try to open the URL
            return
        if url == "change_spec_file":
            if self._prompt_to_save_specification_file(
                self._saved_specification, self._saved_specification.definition_file_path
            ):
                self._emit_specification_saved(self._saved_specification)
            return
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(qurl)
        if not res:
            self.msg_error.emit(f"Unable to open <b>{url}</b>")

    @Slot(QModelIndex, QPoint)
    def show_specification_context_menu(self, ind, global_pos):
        """Context menu for item specifications.

        Args:
            ind (QModelIndex): In the ProjectItemSpecFactoryModel
            pos (QPoint): Mouse position
        """
        if not self.project():
            return
        spec = self.specification_model.specification(ind.row())
        factory = self.item_factories[spec.item_type]
        if not factory.supports_specifications():
            return
        self.specification_context_menu = factory.make_specification_menu(self, ind)
        self.specification_context_menu.exec_(global_pos)
        self.specification_context_menu.deleteLater()
        self.specification_context_menu = None

    @Slot(QModelIndex)
    def edit_specification(self, index):
        """Open the tool specification widget for editing an existing tool specification.

        Args:
            index (QModelIndex): Index of the item (from double-click or contex menu signal)
        """
        if not index.isValid():
            return
        specification = self.specification_model.specification(index.row())
        # Open spec in Tool specification edit widget
        self.show_specification_form(specification.item_type, specification)

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
        # TODO: this could still fail if the file is deleted or renamed right after the check
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

    @Slot()
    def export_as_graphml(self):
        """Exports all DAGs in project to separate GraphML files."""
        if not self.project():
            self.msg.emit("Please open or create a project first")
            return
        self.project().export_graphs()

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

    def setup_zoom_widget_action(self):
        """Setups zoom widget action in view menu."""
        self.zoom_widget_action = ZoomWidgetAction(self.ui.menuView)
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.zoom_widget_action)

    @Slot()
    def restore_dock_widgets(self):
        """Dock all floating and or hidden QDockWidgets back to the main window."""
        for dock in self.findChildren(QDockWidget):
            if not dock.isVisible():
                dock.setVisible(True)
            if dock.isFloating():
                dock.setFloating(False)

    def set_debug_qactions(self):
        """Set shortcuts for QActions that may be needed in debugging."""
        self.show_properties_tabbar.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_0))
        self.show_supported_img_formats.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_8))
        self.addAction(self.show_properties_tabbar)
        self.addAction(self.show_supported_img_formats)

    def add_menu_actions(self):
        """Add extra actions to View menu."""
        self.ui.menuToolbars.addAction(self.main_toolbar.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_project.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_eventlog.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_process_output.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_python_console.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_julia_console.toggleViewAction())
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
        message = format_event_message("msg", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_success_message(self, msg):
        """Append message with green text color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_success", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_error_message(self, msg):
        """Append message with red color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_error", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_warning_message(self, msg):
        """Append message with yellow (golden) color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_event_message("msg_warning", msg, self.show_datetime)
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg", msg)
        self.ui.textBrowser_processlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        message = format_process_message("msg_error", msg)
        self.ui.textBrowser_processlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    def override_event_log(self):
        """Sets the log document of the active project item in Event Log and updates title."""
        document = self.active_project_item.event_document
        self.ui.textBrowser_eventlog.set_override_document(document)
        self._update_event_log_title()

    def override_process_log(self):
        """Sets the log document of the active project item in Process Log and updates title."""
        document = self.active_project_item.process_document
        self.ui.textBrowser_processlog.set_override_document(document)
        self._update_process_log_title()

    def override_python_console(self):
        """Sets the python console of the active project item in Python Console and updates title."""
        console = self.active_project_item.python_console
        dockwidget = self.ui.dockWidgetContents_python_console
        self._set_override_console(dockwidget, console)

    def override_julia_console(self):
        """Sets the julia console of the active project item in Julia Console and updates title."""
        console = self.active_project_item.julia_console
        widget = self.ui.dockWidgetContents_julia_console
        self._set_override_console(widget, console)

    def restore_original_event_log_document(self):
        """Sets the Event Log document back to the original."""
        self.ui.textBrowser_eventlog.restore_original_document()
        self._update_event_log_title()

    def restore_original_process_log_document(self):
        """Sets the Process Log document back to the original."""
        self.ui.textBrowser_processlog.restore_original_document()
        self._update_process_log_title()

    def restore_original_python_console(self):
        """Sets the Python Console back to the original."""
        console = self.python_console
        widget = self.ui.dockWidgetContents_python_console
        self._set_override_console(widget, console)

    def restore_original_julia_console(self):
        """Sets the Julia Console back to the original."""
        console = self.julia_console
        widget = self.ui.dockWidgetContents_julia_console
        self._set_override_console(widget, console)

    def _update_event_log_title(self):
        """Updates Event Log title."""
        new_title = "Event Log"
        owner = self.ui.textBrowser_eventlog.document().owner
        if owner:
            new_title = f"{new_title} --{owner}"
        self.ui.dockWidget_eventlog.setWindowTitle(new_title)

    def _update_process_log_title(self):
        """Updates Event Log title."""
        new_title = "Process Log"
        owner = self.ui.textBrowser_processlog.document().owner
        if owner:
            new_title = f"{new_title} --{owner}"
        self.ui.dockWidget_process_output.setWindowTitle(new_title)

    @staticmethod
    def _set_override_console(widget, console):
        if console is None:
            return
        layout = widget.layout()
        for i in range(layout.count()):
            layout.itemAt(i).widget().hide()
        layout.addWidget(console)
        console.show()
        new_title = console.name()
        if console.owner:
            new_title = f"{new_title} --{console.owner}"
        widget.parent().setWindowTitle(new_title)

    def override_execution_list(self):
        """Displays executions of the active project item in Executions and updates title."""
        self.ui.listView_executions.model().reset_model(self.active_project_item)
        self.ui.dockWidget_executions.setVisible(
            bool(self.active_project_item.filter_execution_documents or self.active_project_item.filter_consoles)
        )
        self.ui.dockWidget_executions.setWindowTitle(f"Executions --{self.active_project_item.name}")
        current = self.ui.listView_executions.currentIndex()
        self._select_execution(current, None)

    @Slot()
    def _refresh_execution_list(self):
        """Refreshes Executions as the active project item starts new executions."""
        self.ui.dockWidget_executions.show()
        if not self.ui.listView_executions.currentIndex().isValid():
            index = self.ui.listView_executions.model().index(0, 0)
            self.ui.listView_executions.setCurrentIndex(index)
        else:
            current = self.ui.listView_executions.currentIndex()
            self._select_execution(current, None)

    @Slot(QModelIndex, QModelIndex)
    def _select_execution(self, current, _previous):
        """Sets the log documents of the selected execution in Event and Process Log,
        and any consoles in Python and Julia Console."""
        if not current.data():
            return
        event_log_doc, process_log_doc = current.model().get_documents(current.data())
        python_console, julia_console = current.model().get_consoles(current.data())
        self.ui.textBrowser_eventlog.set_override_document(event_log_doc)
        self.ui.textBrowser_processlog.set_override_document(process_log_doc)
        self._set_override_console(self.ui.dockWidgetContents_python_console, python_console)
        self._set_override_console(self.ui.dockWidgetContents_julia_console, julia_console)

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

    @Slot()
    def show_specification_form(self, item_type, specification=None, **kwargs):
        """
        Show specification widget.

        Args:
            item_type (str): item's type
            specification (ProjectItemSpecification, optional): item's specification
        """
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        factory = self.item_factories[item_type]
        if not factory.supports_specifications():
            return
        factory.show_specification_widget(self, specification, **kwargs)

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

    @Slot()
    def show_user_guide(self):
        """Open Spine Toolbox documentation index page in browser."""
        # doc_index_path = os.path.join(DOCUMENTATION_PATH, "index.html")
        # index_url = "file:///" + doc_index_path
        index_url = "https://spine-toolbox.readthedocs.io/en/latest/"
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        open_url(index_url, self)

    @Slot()
    def show_getting_started_guide(self):
        """Open Spine Toolbox Getting Started HTML page in browser."""
        index_url = "https://spine-toolbox.readthedocs.io/en/latest/getting_started.html"
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        open_url(index_url, self)

    @Slot(QPoint)
    def show_item_context_menu(self, pos):
        """Context menu for project items listed in the project QTreeView.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_project.indexAt(pos)
        global_pos = self.ui.treeView_project.viewport().mapToGlobal(pos)
        self.show_project_item_context_menu(global_pos, ind)

    def show_project_item_context_menu(self, pos, index_or_name):
        """Create and show project item context menu.

        Args:
            pos (QPoint): Mouse position
            index_or_name (QModelIndex or str): Index or name of concerned item
        """
        index = self.project_item_model.find_item(index_or_name) if isinstance(index_or_name, str) else index_or_name
        if not index.isValid():
            # Clicked on a blank area, show the project item model context menu
            menu = QMenu(self)
            menu.addAction(self.ui.actionOpen_project_directory)
            menu.addSeparator()
            menu.addAction(self.ui.actionExport_project_to_GraphML)
        else:
            # Clicked on an item, show the custom context menu for that item
            item = self.project_item_model.item(index)
            menu = item.custom_context_menu(self)
        menu.exec_(pos)
        menu.deleteLater()

    def show_link_context_menu(self, pos, link):
        """Context menu for connection links.

        Args:
            pos (QPoint): Mouse position
            link (Link(QGraphicsPathItem)): The concerned link
        """
        self.link_context_menu = LinkContextMenu(self, pos, link)
        option = self.link_context_menu.get_action()
        if option == "Remove connection":
            self.ui.graphicsView.remove_link(link)
            return
        if option == "Take connection":
            self.ui.graphicsView.take_link(link)
            return
        if option == "Send to bottom":
            link.send_to_bottom()
        self.link_context_menu.deleteLater()
        self.link_context_menu = None

    def tear_down_items_and_factories(self):
        """Calls the tear_down method on all project items, so they can clean up their mess if needed."""
        if not self._project:
            return
        for factory in self.item_factories.values():
            factory.tear_down()
        for item in self.project_item_model.items():
            if isinstance(item, LeafProjectTreeItem):
                item.project_item.tear_down()

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
        show_confirm_exit = int(self._qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        save_at_exit = (
            int(self._qsettings.value("appSettings/saveAtExit", defaultValue="1")) if self._project is not None else 0
        )
        if show_confirm_exit != 2:
            # Don't prompt for exit
            if save_at_exit == 0:
                return []
            if save_at_exit == 1:
                # We still need to prompt for saving
                return ["prompt save"]
            return ["save"]
        if save_at_exit == 0:
            return ["prompt exit"]
        if save_at_exit == 1:
            return ["prompt save"]
        return ["prompt exit", "save"]

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
                if not self._confirm_save_and_exit():
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
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Confirm exit")
        msg.setText("Are you sure you want to exit Spine Toolbox?")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.button(QMessageBox.Ok).setText("Exit")
        chkbox = QCheckBox()
        chkbox.setText("Do not ask me again")
        msg.setCheckBox(chkbox)
        answer = msg.exec_()  # Show message box
        if answer == QMessageBox.Ok:
            # Update conf file according to checkbox status
            if not chkbox.checkState():
                show_prompt = "2"  # 2 as in True
            else:
                show_prompt = "0"  # 0 as in False
            self._qsettings.setValue("appSettings/showExitPrompt", show_prompt)
            return True
        return False

    def _confirm_save_and_exit(self):
        """
        Confirms exit from user and saves the project if requested.

        Returns:
            True if exiting should proceed, False if user cancelled
        """
        msg = QMessageBox(parent=self)
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Save project before exiting")
        msg.setText("Exiting Spine Toolbox. Save changes to project?")
        msg.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg.button(QMessageBox.Save).setText("Save And Exit")
        msg.button(QMessageBox.Discard).setText("Exit without Saving")
        chkbox = QCheckBox()
        chkbox.setText("Do not ask me again")
        msg.setCheckBox(chkbox)
        answer = msg.exec_()
        if answer == QMessageBox.Cancel:
            return False
        if answer == QMessageBox.Save:
            self.save_project()
        chk = chkbox.checkState()
        if chk == 2:
            if answer == QMessageBox.Save:
                self._qsettings.setValue("appSettings/saveAtExit", "2")
            elif answer == QMessageBox.Discard:
                self._qsettings.setValue("appSettings/saveAtExit", "0")
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
            if os.path.normcase(path) == os.path.normcase(p):
                recents_list.pop(recents_list.index(entry))
                break
        updated_recents = "\n".join(recents_list)
        # Save updated recent paths
        self._qsettings.setValue("appSettings/recentProjects", updated_recents)
        self._qsettings.sync()  # Commit change immediately

    def update_recent_projects(self):
        """Adds a new entry to QSettings variable that remembers the five most recent project paths."""
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
                if len(recents_list) > 5:
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
             event (QCloseEvent): PySide2 event
        """
        # Show confirm exit message box
        exit_confirmed = self._perform_pre_exit_tasks()
        if not exit_confirmed:
            event.ignore()
            return
        # Save settings
        if self._project is None:
            self._qsettings.setValue("appSettings/previousProject", "")
        else:
            self._qsettings.setValue("appSettings/previousProject", self._project.project_dir)
            self.update_recent_projects()
        self._qsettings.setValue("mainWindow/windowSize", self.size())
        self._qsettings.setValue("mainWindow/windowPosition", self.pos())
        self._qsettings.setValue("mainWindow/windowState", self.saveState(version=1))
        self._qsettings.setValue("mainWindow/windowMaximized", self.windowState() == Qt.WindowMaximized)
        # Save number of screens
        # noinspection PyArgumentList
        self._qsettings.setValue("mainWindow/n_screens", len(QGuiApplication.screens()))
        self.julia_console.shutdown_kernel()
        self.python_console.shutdown_kernel()
        self.tear_down_items_and_factories()
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
            items_dict[name] = project_item.item_dict()
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

    def _deserialize_items(self, items_dict):
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
            if self.project_item_model.find_item(name) is not None:
                new_name = self.propose_item_name(name)
                final_items_dict[new_name] = item_dict
            else:
                final_items_dict[name] = item_dict
            self._set_deserialized_item_position(item_dict, shift_x, shift_y, scene_rect)
        self._project.add_project_items(final_items_dict, set_selected=True, verbosity=False)

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
    def project_item_from_clipboard(self):
        """Adds project items in system's clipboard to the current project."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        byte_data = mime_data.data("application/vnd.spinetoolbox.ProjectItem")
        if byte_data.isNull():
            return
        item_dump = str(byte_data.data(), "utf-8")
        item_dicts = json.loads(item_dump)
        self._deserialize_items(item_dicts)

    @Slot()
    def duplicate_project_item(self):
        """Duplicates the selected project items."""
        item_dicts = self._serialize_selected_items()
        if not item_dicts:
            return
        self._deserialize_items(item_dicts)

    def propose_item_name(self, prefix):
        """
        Proposes a name for a project item.

        The format is `prefix_xx` where `xx` is a counter value [01..99].

        Args:
            prefix (str): a prefix for the name

        Returns:
            a name string
        """
        name_count = self._proposed_item_name_counts.setdefault(prefix, 0)
        name = prefix + " {}".format(name_count + 1)
        if self.project_item_model.find_item(name) is not None:
            if name_count == 98:
                # Avoiding too deep recursions.
                raise RuntimeError("Ran out of numbers: cannot find suitable name for project item.")
            # Increment index recursively if name is already in project.
            self._proposed_item_name_counts[prefix] += 1
            name = self.propose_item_name(prefix)
        return name

    def _create_item_edit_actions(self):
        """Creates project item edit actions (copy, paste, duplicate) and adds them to proper places."""
        actions = [self.ui.actionCopy, self.ui.actionPaste, self.ui.actionPaste, self.ui.actionRemove]
        for action in actions:
            action.setShortcutContext(Qt.WidgetShortcut)
            self.ui.treeView_project.addAction(action)
            self.ui.graphicsView.addAction(action)

    @Slot()
    def _scroll_event_log_to_end(self):
        self.ui.textBrowser_eventlog.verticalScrollBar().setValue(
            self.ui.textBrowser_eventlog.verticalScrollBar().maximum()
        )

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
        self._project.project_execution_about_to_start.connect(self._scroll_event_log_to_end)

    def project_item_properties_ui(self, item_type):
        """
        Returns the properties tab widget's ui.

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
            return
        open_url("file:///" + self._project.project_dir, self)

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
    def _remove_item(self, _):
        """Removes selected project items and links."""
        self.ui.graphicsView.remove_selected_links()
        selection_model = self.ui.treeView_project.selectionModel()
        for index in selection_model.selection().indexes():
            item = self.project_item_model.item(index)
            self._project.remove_item(item.project_item.name)

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
        self.undo_stack.push(RenameProjectItemCommand(self.project_item_model, item, new_name))

    def item_category_context_menu(self):
        """
        Creates a context menu for project item categories.

        Returns:
            QMenu: category context menu
        """
        menu = QMenu(self)
        menu.addAction(self.ui.actionOpen_project_directory)
        return menu

    def project_item_context_menu(self, additional_actions):
        """
        Creates a context menu for project items.

        Args:
            additional_actions (list of QAction): actions to be prepended to the menu

        Returns:
            QMenu: project item context menu
        """
        menu = QMenu(self)
        if additional_actions:
            for action in additional_actions:
                menu.addAction(action)
            menu.addSeparator()
        menu.addAction(self.ui.actionCopy)
        menu.addAction(self.ui.actionPaste)
        menu.addAction(self.ui.actionDuplicate)
        menu.addAction(self.ui.actionOpen_item_directory)
        menu.addSeparator()
        menu.addAction(self.ui.actionRemove)
        menu.addSeparator()
        menu.addAction(self.ui.actionRename_item)
        return menu
