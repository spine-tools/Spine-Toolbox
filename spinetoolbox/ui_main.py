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
from PySide2.QtCore import QByteArray, QMimeData, Qt, Signal, Slot, QSettings, QUrl, SIGNAL
from PySide2.QtGui import QDesktopServices, QGuiApplication, QKeySequence, QStandardItemModel, QIcon, QCursor
from PySide2.QtWidgets import (
    QMainWindow,
    QApplication,
    QErrorMessage,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QDockWidget,
    QAction,
    QUndoStack,
)
from .graphics_items import ProjectItemIcon
from .mvcmodels.project_item_model import ProjectItemModel
from .mvcmodels.tool_specification_model import ToolSpecificationModel
from .widgets.about_widget import AboutWidget
from .widgets.custom_menus import (
    ProjectItemModelContextMenu,
    ToolSpecificationContextMenu,
    LinkContextMenu,
    AddToolSpecificationPopupMenu,
    RecentProjectsPopupMenu,
)
from .widgets.settings_widget import SettingsWidget
from .widgets.tool_specification_widget import ToolSpecificationWidget
from .widgets.custom_qwidgets import ZoomWidgetAction
from .widgets.julia_repl_widget import JuliaREPLWidget
from .widgets.python_repl_widget import PythonReplWidget
from .widgets import toolbars
from .widgets.open_project_widget import OpenProjectDialog
from .project import SpineToolboxProject
from .config import (
    STATUSBAR_SS,
    TEXTBROWSER_SS,
    MAINWINDOW_SS,
    DOCUMENTATION_PATH,
    _program_root,
    LATEST_PROJECT_VERSION,
    DEFAULT_WORK_DIR,
)
from .helpers import (
    get_datetime,
    busy_effect,
    set_taskbar_icon,
    supported_img_formats,
    create_dir,
    recursive_overwrite,
    serialize_path,
    deserialize_path,
)
from .project_upgrader import ProjectUpgrader
from .project_tree_item import CategoryProjectTreeItem, LeafProjectTreeItem, RootProjectTreeItem
from .project_items import data_store, data_connection, exporter, tool, view, importer
from .project_commands import (
    AddToolSpecificationCommand,
    RemoveToolSpecificationCommand,
    UpdateToolSpecificationCommand,
)
from .configuration_assistants import spine_model


class ToolboxUI(QMainWindow):
    """Class for application main GUI functions."""

    # Signals to comply with the spinetoolbox.logger_interface.LoggerInteface interface.
    msg = Signal(str)
    msg_success = Signal(str)
    msg_error = Signal(str)
    msg_warning = Signal(str)
    msg_proc = Signal(str)
    information_box = Signal(str, str)
    error_box = Signal(str, str)
    # The rest of the msg_* signals should be moved to LoggerInterface in the long run.
    msg_proc_error = Signal(str)
    tool_specification_model_changed = Signal("QVariant")

    def __init__(self):
        """ Initialize application and main window."""
        from .ui.mainwindow import Ui_MainWindow

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
        self._project_item_actions = list()
        self._item_edit_actions()
        # Set style sheets
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.textBrowser_eventlog.setStyleSheet(TEXTBROWSER_SS)
        self.ui.textBrowser_process_output.setStyleSheet(TEXTBROWSER_SS)
        self.setStyleSheet(MAINWINDOW_SS)
        # Class variables
        self.undo_stack = QUndoStack(self)
        self.categories = dict()  # Holds category data parsed from project item plugins
        self._project = None
        self.project_item_model = None
        self.tool_specification_model = None
        self.show_datetime = self.update_datetime()
        self.active_project_item = None
        self.work_dir = None
        # Widget and form references
        self.settings_form = None
        self.tool_specification_context_menu = None
        self.project_item_context_menu = None
        self.link_context_menu = None
        self.process_output_context_menu = None
        self.add_project_item_form = None
        self.tool_specification_form = None
        self.placing_item = ""
        self.add_tool_specification_popup_menu = None
        self.zoom_widget_action = None
        self.recent_projects_menu = RecentProjectsPopupMenu(self)
        # Make and initialize toolbars
        self.item_toolbar = toolbars.ItemToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.item_toolbar)
        # Make julia REPL
        self.julia_repl = JuliaREPLWidget(self)
        self.ui.dockWidgetContents_julia_repl.layout().addWidget(self.julia_repl)
        # Make Python REPL
        self.python_repl = PythonReplWidget(self)
        self.ui.dockWidgetContents_python_repl.layout().addWidget(self.python_repl)
        # Setup main window menu
        self.setup_zoom_widget_action()
        self.add_menu_actions()
        # Hidden QActions for debugging or testing
        self.show_properties_tabbar = QAction(self)
        self.show_supported_img_formats = QAction(self)
        self.test_variable_push = QAction(self)
        self.set_debug_qactions()
        self.ui.tabWidget_item_properties.tabBar().hide()  # Hide tab bar in properties dock widget
        # Finalize init
        self._proposed_item_name_counts = dict()
        self.ui.actionSave.setDisabled(True)
        self.ui.actionSave_As.setDisabled(True)
        self.connect_signals()
        self.restore_ui()
        self.parse_project_item_modules()
        self.parse_assistant_modules()
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
        self.ui.actionUpgrade_project.triggered.connect(self.upgrade_project)
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
        # Debug actions
        self.show_properties_tabbar.triggered.connect(self.toggle_properties_tabbar_visibility)
        self.show_supported_img_formats.triggered.connect(supported_img_formats)  # in helpers.py
        self.test_variable_push.triggered.connect(self.python_repl.test_push_vars)
        # Tool specifications tab
        self.add_tool_specification_popup_menu = AddToolSpecificationPopupMenu(self)
        self.ui.toolButton_add_tool_specification.setMenu(self.add_tool_specification_popup_menu)
        self.ui.toolButton_remove_tool_specification.clicked.connect(self.remove_selected_tool_specification)
        # Context-menus
        self.ui.treeView_project.customContextMenuRequested.connect(self.show_item_context_menu)
        # Zoom actions
        self.zoom_widget_action.minus_pressed.connect(self._handle_zoom_minus_pressed)
        self.zoom_widget_action.plus_pressed.connect(self._handle_zoom_plus_pressed)
        self.zoom_widget_action.reset_pressed.connect(self._handle_zoom_reset_pressed)
        # Undo stack
        self.undo_stack.cleanChanged.connect(self.update_window_modified)

    @Slot(bool)
    def update_window_modified(self, clean):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        self.setWindowModified(not clean)
        self.ui.actionSave.setDisabled(clean)

    def parse_project_item_modules(self):
        """Collects attributes from project item modules into a dict.
        This dict is then used to perform all project item related tasks.
        """
        self.categories.clear()
        for module in (data_store, data_connection, tool, view, importer, exporter):
            item_rank = module.item_rank
            item_category = module.item_category
            item_type = module.item_type
            item_icon = module.item_icon
            item_maker = module.item_maker
            icon_maker = module.icon_maker
            add_form_maker = module.add_form_maker
            properties_widget = module.properties_widget_maker(self)
            properties_ui = properties_widget.ui
            self.categories[item_category] = dict(
                item_rank=item_rank,
                item_type=item_type,
                item_icon=item_icon,
                item_maker=item_maker,
                icon_maker=icon_maker,
                add_form_maker=add_form_maker,
                properties_ui=properties_ui,
            )
        # Sort categories by rank
        self.categories = dict(sorted(self.categories.items(), key=lambda kv: kv[1]["item_rank"]))
        # Create actions for Edit menu, and draggable widgets to toolbar
        category_icon = list()
        for item_category, item_dict in self.categories.items():
            item_icon = item_dict["item_icon"]
            item_type = item_dict["item_type"]
            category_icon.append((item_type, item_category, item_icon))
        # Add draggable widgets to toolbar
        self.item_toolbar.add_draggable_widgets(category_icon)

    def parse_assistant_modules(self):
        """Makes actions to run assistants from assistant modules.
        """
        menu = self.ui.menuTool_configuration_assistants
        for module in (spine_model,):  # NOTE: add others as needed
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
            new_work_dir (str): If given, changes the work directory to given
            and creates the directory if it does not exist.
        """
        if not new_work_dir:
            work_dir = self._qsettings.value("appSettings/workDir", defaultValue="")
            if work_dir == "":
                self.work_dir = DEFAULT_WORK_DIR
            else:
                self.work_dir = work_dir
        else:
            self.work_dir = new_work_dir
            self.msg.emit("Work directory is now <b>{0}</b>".format(self.work_dir))
        try:
            create_dir(self.work_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating work directory {0} failed. Check permissions.".format(self.work_dir)
            )
            self.work_dir = None

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
            "<a style='color:#99CCFF;' title='" + p + "' href='file:///" + p + "'>Getting Started</a>"
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
            self, name, description, location, self.project_item_model, settings=self._qsettings, logger=self
        )
        self._project.connect_signals()
        self._connect_project_signals()
        self.init_tool_specification_model(list())  # Start project with no tool specifications
        self.update_window_title()
        self.ui.actionSave_As.setEnabled(True)
        self.ui.graphicsView.init_scene(empty=True)
        # Update recentProjects
        self.update_recent_projects()
        # Update recentProjectStorages
        OpenProjectDialog.update_recents(os.path.abspath(os.path.join(location, os.path.pardir)), self.qsettings())
        self.save_project()

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
            dialog = OpenProjectDialog(self)
            if not dialog.exec():
                return False
            load_dir = dialog.selection()
        load_path = os.path.abspath(os.path.join(load_dir, ".spinetoolbox", "project.json"))
        try:
            with open(load_path, "r") as fh:
                try:
                    proj_info = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self.msg_error.emit("Error in project file <b>{0}</b>. Invalid JSON. {0}".format(load_path))
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
        # Check that project info is valid
        if not ProjectUpgrader(self).is_valid(project_info):
            self.msg_error.emit("Opening project in directory {0} failed".format(project_dir))
            return False
        version = project_info["project"]["version"]
        # Upgrade project dictionary if needed
        if version < LATEST_PROJECT_VERSION:
            project_info = ProjectUpgrader(self).upgrade(project_info, project_dir, project_dir)
        self.undo_critical_commands()
        # Make room for a new project
        self.clear_ui()
        # Parse project info
        name = project_info["project"]["name"]  # Project name
        desc = project_info["project"]["description"]  # Project description
        tool_spec_paths = project_info["project"]["tool_specifications"]
        connections = project_info["project"]["connections"]
        project_items = project_info["objects"]
        # Init project item model
        self.init_project_item_model()
        self.ui.treeView_project.selectionModel().selectionChanged.connect(self.item_selection_changed)
        # Create project
        self._project = SpineToolboxProject(
            self, name, desc, project_dir, self.project_item_model, settings=self._qsettings, logger=self
        )
        self._connect_project_signals()
        self.update_window_title()
        self.ui.actionSave.setDisabled(True)
        self.ui.actionSave_As.setEnabled(True)
        # Init tool spec model
        deserialized_paths = [deserialize_path(spec, self._project.project_dir) for spec in tool_spec_paths]
        self.init_tool_specification_model(deserialized_paths)
        # Clear text browsers
        if clear_logs:
            self.ui.textBrowser_eventlog.clear()
            self.ui.textBrowser_process_output.clear()
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
        # Initialize scene on Design View
        self.ui.graphicsView.init_scene()
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
        # Put project's tool specification definition files into a list
        tool_spec_paths = [
            self.tool_specification_model.tool_specification(i).get_def_path()
            for i in range(self.tool_specification_model.rowCount())
        ]
        # Serialize tool spec paths
        serialized_tool_spec_paths = [serialize_path(spec, self._project.project_dir) for spec in tool_spec_paths]
        if not self._project.save(serialized_tool_spec_paths):
            self.msg_error.emit("Project saving failed")
            return
        self.msg.emit("Project <b>{0}</b> saved".format(self._project.name))
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

    @Slot(bool)
    def upgrade_project(self, checked=False):
        """Upgrades an old style project (.proj file) to a new directory based Spine Toolbox project.
        Note that this method can be removed when we no longer want to support upgrading .proj projects.
        Project upgrading should happen later automatically when opening a project.
        """
        msg = (
            "This option upgrades your legacy Spine Toolbox projects from .proj files to "
            "<br/>Spine Toolbox project <b>directories</b>."
            "<br/><br/>Next, you will be presented two file dialogs:"
            "<br/><b>1.</b>From the first dialog, select a project you<br/> want "
            "to upgrade by selecting a <i>.proj</i> <b>file</b>"
            "<br/><b>2.</b>From the second dialog, select a <b>directory</b> "
            "for the upgraded project."
            "<br/><br/>Project item data will be copied to the new project directory."
            "<br/><br/><b>P.S.</b> You only need to do this once per project."
        )
        QMessageBox.information(self, "Project upgrade wizard", msg)
        # noinspection PyCallByClass
        answer = QFileDialog.getOpenFileName(
            self, "Select an old project (.proj file) to upgrade", _program_root, "Project file (*.proj)"
        )
        if not answer[0]:
            return
        fp = answer[0]
        upgrader = ProjectUpgrader(self)
        proj_dir = upgrader.get_project_directory()
        if not proj_dir:
            self.msg.emit("Project upgrade canceled")
            return
        proj_info = upgrader.open_proj_json(fp)
        if not proj_info:
            return
        old_project_dir = os.path.normpath(os.path.join(os.path.dirname(fp), fp[:-5]))
        if not os.path.isdir(old_project_dir):
            self.msg_error.emit("Project upgrade failed")
            self.msg_warning.emit("Project directory <b>{0}</b> does not exist".format(old_project_dir))
            return
        # Upgrade project info dict to latest version
        upgraded_proj_info = upgrader.upgrade(proj_info, old_project_dir, proj_dir)
        # Copy project item data from old project to new project directory
        if not upgrader.copy_data(fp, proj_dir):
            self.msg_warning.emit(
                "Copying data to project <b>{0}</b> failed. "
                "Please copy project item directories to directory <b>{1}</b> manually.".format(
                    proj_dir, os.path.join(proj_dir, ".spinetoolbox", "items")
                )
            )
        # Open the upgraded project
        if not self.restore_project(upgraded_proj_info, proj_dir, clear_logs=False):
            return
        # Save project to finish the upgrade process
        self.save_project()

    def init_project_item_model(self):
        """Initializes project item model. Create root and category items and
        add them to the model."""
        root_item = RootProjectTreeItem()
        self.project_item_model = ProjectItemModel(self, root=root_item)
        for category, category_dict in self.categories.items():
            item_maker = category_dict["item_maker"]
            icon_maker = category_dict["icon_maker"]
            add_form_maker = category_dict["add_form_maker"]
            properties_ui = category_dict["properties_ui"]
            category_item = CategoryProjectTreeItem(category, "", item_maker, icon_maker, add_form_maker, properties_ui)
            self.project_item_model.insert_item(category_item)
        self.ui.treeView_project.setModel(self.project_item_model)
        self.ui.treeView_project.header().hide()
        self.ui.graphicsView.set_project_item_model(self.project_item_model)

    def init_tool_specification_model(self, tool_specification_paths):
        """Initializes Tool specification model.

        Args:
            tool_specification_paths (list): List of tool definition file paths used in this project
        """
        self.tool_specification_model_changed.emit(QStandardItemModel())
        self.tool_specification_model = ToolSpecificationModel()
        n_tools = 0
        self.msg.emit("Loading Tool specifications...")
        for path in tool_specification_paths:
            if not path:
                continue
            # Add tool specification into project
            tool_cand = self._project.load_tool_specification_from_file(path)
            n_tools += 1
            if not tool_cand:
                continue
            # Add tool definition file path to tool instance variable
            tool_cand.set_def_path(path)
            # Insert tool into model
            self.tool_specification_model.insertRow(tool_cand)
            # self.msg.emit("Tool specification <b>{0}</b> ready".format(tool_cand.name))
        # Set model to the tool specification list view
        self.ui.listView_tool_specifications.setModel(self.tool_specification_model)
        # Set model to Tool project item combo box
        self.tool_specification_model_changed.emit(self.tool_specification_model)
        # Note: If ToolSpecificationModel signals are in use, they should be reconnected here.
        # Reconnect ToolSpecificationModel and QListView signals. Make sure that signals are connected only once.
        n_recv_sig1 = self.ui.listView_tool_specifications.receivers(
            SIGNAL("doubleClicked(QModelIndex)")
        )  # nr of receivers
        if n_recv_sig1 == 0:
            # logging.debug("Connecting doubleClicked signal for QListView")
            self.ui.listView_tool_specifications.doubleClicked.connect(self.edit_tool_specification)
        elif n_recv_sig1 > 1:  # Check that this never gets over 1
            logging.error("Number of receivers for QListView doubleClicked signal is now: %d", n_recv_sig1)
        else:
            pass  # signal already connected
        n_recv_sig2 = self.ui.listView_tool_specifications.receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        if n_recv_sig2 == 0:
            # logging.debug("Connecting customContextMenuRequested signal for QListView")
            self.ui.listView_tool_specifications.customContextMenuRequested.connect(
                self.show_tool_specification_context_menu
            )
        elif n_recv_sig2 > 1:  # Check that this never gets over 1
            logging.error("Number of receivers for QListView customContextMenuRequested signal is now: %d", n_recv_sig2)
        else:
            pass  # signal already connected
        if n_tools == 0:
            self.msg_warning.emit("Project has no Tool specifications")

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self._qsettings.value("mainWindow/windowSize", defaultValue="false")
        window_pos = self._qsettings.value("mainWindow/windowPosition", defaultValue="false")
        window_state = self._qsettings.value("mainWindow/windowState", defaultValue="false")
        splitter_state = self._qsettings.value("mainWindow/projectDockWidgetSplitterState", defaultValue="false")
        window_maximized = self._qsettings.value("mainWindow/windowMaximized", defaultValue="false")  # returns str
        n_screens = self._qsettings.value("mainWindow/n_screens", defaultValue=1)  # number of screens on last exit
        # noinspection PyArgumentList
        n_screens_now = len(QGuiApplication.screens())  # Number of screens now
        # Note: cannot use booleans since Windows saves them as strings to registry
        if not window_size == "false":
            self.resize(window_size)  # Expects QSize
        if not window_pos == "false":
            self.move(window_pos)  # Expects QPoint
        if not window_state == "false":
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions. Expects QByteArray
        if not splitter_state == "false":
            self.ui.splitter.restoreState(splitter_state)  # Project Dock Widget splitter position. Expects QByteArray
        if window_maximized == "true":
            self.setWindowState(Qt.WindowMaximized)
        if n_screens_now < int(n_screens):
            # There are less screens available now than on previous application startup
            # Move main window to position 0,0 to make sure that it is not lost on another screen that does not exist
            self.move(0, 0)

    def clear_ui(self):
        """Clean UI to make room for a new or opened project."""
        if not self.project():
            return
        item_names = self.project_item_model.item_names()
        for name in item_names:
            self.project().do_remove_item(name)
        self.activate_no_selection_tab()  # Clear properties widget
        if self._project:
            self._project.deleteLater()
        self._project = None
        self.tool_specification_model = None
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

    @Slot("QItemSelection", "QItemSelection")
    def item_selection_changed(self, selected, deselected):
        """Synchronize selection with scene. Check if only one item is selected and make it the
        active item: disconnect signals of previous active item, connect signals of current active item
        and show correct properties tab for the latter.
        """
        inds = self.ui.treeView_project.selectedIndexes()
        proj_items = [self.project_item_model.item(i).project_item for i in inds]
        # NOTE: Category items are not selectable anymore
        # Sync selection with the scene
        if proj_items:
            scene = self.ui.graphicsView.scene()
            scene.sync_selection = False  # This tells the scene not to sync back
            scene.clearSelection()
            for item in proj_items:
                item.get_icon().setSelected(True)
            scene.sync_selection = True
        # Refresh active item if needed
        if len(proj_items) == 1:
            new_active_project_item = proj_items[0]
        else:
            new_active_project_item = None
        if self.active_project_item and self.active_project_item != new_active_project_item:
            # Deactivate old active project item
            ret = self.active_project_item.deactivate()
            if not ret:
                self.msg_error.emit(
                    "Something went wrong in disconnecting {0} signals".format(self.active_project_item.name)
                )
        self.active_project_item = new_active_project_item
        if self.active_project_item:
            # Activate new active project item
            self.active_project_item.activate()
            self.activate_item_tab(self.active_project_item)
        else:
            self.activate_no_selection_tab()

    def activate_no_selection_tab(self):
        """Shows 'No Selection' tab."""
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == "No Selection":
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        self.ui.dockWidget_item.setWindowTitle("Properties")

    def activate_item_tab(self, item):
        """Shows project item properties tab according to item type.
        Note: Does not work if a category item is given as argument.

        Args:
            item (ProjectItem): Instance of a project item
        """
        # Find tab index according to item type
        for i in range(self.ui.tabWidget_item_properties.count()):
            if self.ui.tabWidget_item_properties.tabText(i) == item.item_type():
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        # Set QDockWidget title to selected item's type
        self.ui.dockWidget_item.setWindowTitle(item.item_type() + " Properties")

    @Slot()
    def open_tool_specification(self):
        """Opens a file dialog where the user can select an existing tool specification
        definition file (.json). If file is valid, calls add_tool_specification().
        """
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(self, "Select Tool specification file", _program_root, "JSON (*.json)")
        if answer[0] == "":  # Cancel button clicked
            return
        def_file = os.path.abspath(answer[0])
        # Load tool definition
        tool_specification = self._project.load_tool_specification_from_file(def_file)
        if not tool_specification:
            return
        if self.tool_specification_model.find_tool_specification(tool_specification.name):
            # Tool specification already added to project
            self.msg_warning.emit("Tool specification <b>{0}</b> already in project".format(tool_specification.name))
            return
        # Add definition file path into tool specification
        tool_specification.set_def_path(def_file)
        self.add_tool_specification(tool_specification)

    def add_tool_specification(self, tool_specification):
        """Pushes a new AddToolSpecificationCommand to the undo stack."""
        self.undo_stack.push(AddToolSpecificationCommand(self, tool_specification))

    def do_add_tool_specification(self, tool_specification, row=None):
        """Adds a ToolSpecification instance to project, which then can be added to a Tool item.
        Adds the tool specification file path into project file (project.json)

        Args:
            tool_specification (ToolSpecification): Tool specification that is added to project
        """
        self.tool_specification_model.insertRow(tool_specification, row)
        self.msg_success.emit("Tool specification <b>{0}</b> added to project".format(tool_specification.name))

    def update_tool_specification(self, row, tool_specification):
        """Pushes a new UpdateToolSpecificationCommand to the undo stack."""
        self.undo_stack.push(UpdateToolSpecificationCommand(self, row, tool_specification))

    def do_update_tool_specification(self, row, tool_specification):
        """Updates a Tool specification and refreshes all Tools that use it.

        Args:
            row (int): Row of tool specification in ToolSpecificationModel
            tool_specification (ToolSpecification): An updated Tool specification
        """
        if not self.tool_specification_model.update_tool_specification(row, tool_specification):
            self.msg_error.emit("Unable to update Tool specification <b>{0}</b>".format(tool_specification.name))
            return False
        self.msg_success.emit("Tool specification <b>{0}</b> successfully updated".format(tool_specification.name))
        return True

    def update_tool_settings(self, tool_settings):
        """Updates tool specification and execution mode for a bunch of tool items.
        Called just after successfully updating a Tool Specification.

        Args:
            tool_settings (dict): mapping Tool items to a tuple of (ToolSpecification instance, bool execution mode)
        """
        for tool_item, (tool_specification, execute_in_work) in tool_settings.items():
            tool_item.do_update_execution_mode(execute_in_work)
            tool_item.do_set_tool_specification(tool_specification)
            self.msg.emit(
                "Tool specification <b>{0}</b> successfully updated in Tool <b>{1}</b>".format(
                    tool_specification.name, tool_item.name
                )
            )

    @Slot(bool)
    def remove_selected_tool_specification(self, checked=False):
        """Removes tool specification selected in QListView."""
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        selected = self.ui.listView_tool_specifications.selectedIndexes()
        if not selected:
            self.msg.emit("Select a Tool specification to remove")
            return
        index = selected[0]
        if not index.isValid():
            return
        self.remove_tool_specification(index.row())

    def remove_tool_specification(self, row, ask_verification=True):
        self.undo_stack.push(RemoveToolSpecificationCommand(self, row, ask_verification=ask_verification))

    def do_remove_tool_specification(self, row, ask_verification=True):
        """Removes tool specification from ToolSpecificationModel.
        Removes also Tool specifications from all Tool items
        that use this specification.

        Args:
            row (int): Row in ToolSpecificationModel
            ask_verification (bool): If True, displays a dialog box asking user to verify the removal
        """
        tool_spec = self.tool_specification_model.tool_specification(row)
        if ask_verification:
            message = "Remove Tool Specification <b>{0}</b> from Project?".format(tool_spec.name)
            message_box = QMessageBox(
                QMessageBox.Question,
                "Remove Tool Specification",
                message,
                buttons=QMessageBox.Ok | QMessageBox.Cancel,
                parent=self,
            )
            message_box.button(QMessageBox.Ok).setText("Remove Specification")
            answer = message_box.exec_()
            if answer != QMessageBox.Ok:
                return
        if not self.tool_specification_model.removeRow(row):
            self.msg_error.emit("Error in removing Tool specification <b>{0}</b>".format(tool_spec.name))
            return
        self.msg_success.emit("Tool specification removed")

    @Slot()
    def remove_all_items(self):
        """Removes all items from project. Slot for Remove All button."""
        if not self._project:
            self.msg.emit("No project items to remove")
            return
        self._project.remove_all_items()

    @Slot("QUrl")
    def open_anchor(self, qurl):
        """Open file explorer in the directory given in qurl.

        Args:
            qurl (QUrl): Directory path or a file to open
        """
        if qurl.url() == "#":  # This is a Tip so do not try to open the URL
            return
        path = qurl.toLocalFile()  # Path to result folder
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(qurl)
        if not res:
            self.msg_error.emit("Opening path {} failed".format(path))

    @Slot("QModelIndex")
    def edit_tool_specification(self, index):
        """Open the tool specification widget for editing an existing tool specification.

        Args:
            index (QModelIndex): Index of the item (from double-click or contex menu signal)
        """
        if not index.isValid():
            return
        tool_specification = self.tool_specification_model.tool_specification(index.row())
        # Open spec in Tool specification edit widget
        self.show_tool_specification_form(tool_specification)

    @busy_effect
    @Slot("QModelIndex")
    def open_tool_specification_file(self, index):
        """Open the Tool specification definition file in the default (.json) text-editor.

        Args:
            index (QModelIndex): Index of the item
        """
        if not index.isValid():
            return
        tool_specification = self.tool_specification_model.tool_specification(index.row())
        file_path = tool_specification.get_def_path()
        # Check if file exists first. openUrl may return True if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            logging.error("Failed to open editor for %s", file_path)
            self.msg_error.emit("Tool specification file <b>{0}</b> not found.".format(file_path))
            return
        tool_specification_url = "file:///" + file_path
        # Open Tool specification file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(tool_specification_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", tool_specification_url)
            self.msg_error.emit(
                "Unable to open Tool specification file {0}. Make sure that <b>.json</b> "
                "files are associated with a text editor. For example on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(file_path)
            )
        return

    @busy_effect
    @Slot("QModelIndex")
    def open_tool_main_program_file(self, index):
        """Open the tool specification's main program file in the default editor.

        Args:
            index (QModelIndex): Index of the item
        """
        if not index.isValid():
            return
        tool_item = self.tool_specification_model.tool_specification(index.row())
        file_path = os.path.join(tool_item.path, tool_item.includes[0])
        # Check if file exists first. openUrl may return True even if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            self.msg_error.emit("Tool main program file <b>{0}</b> not found.".format(file_path))
            return
        ext = os.path.splitext(os.path.split(file_path)[1])[1]
        if ext in [".bat", ".exe"]:
            self.msg_warning.emit(
                "Sorry, opening files with extension <b>{0}</b> not supported. "
                "Please open the file manually.".format(ext)
            )
            return
        main_program_url = "file:///" + file_path
        # Open Tool specification main program file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(main_program_url, QUrl.TolerantMode))
        if not res:
            filename, file_extension = os.path.splitext(file_path)
            self.msg_error.emit(
                "Unable to open Tool specification main program file {0}. "
                "Make sure that <b>{1}</b> "
                "files are associated with an editor. E.g. on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(filename, file_extension)
            )
        return

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
        self.test_variable_push.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_7))
        self.addAction(self.show_properties_tabbar)
        self.addAction(self.show_supported_img_formats)
        self.addAction(self.test_variable_push)

    def add_menu_actions(self):
        """Add extra actions to View menu."""
        self.ui.menuToolbars.addAction(self.item_toolbar.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_project.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_eventlog.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_process_output.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_python_repl.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_julia_repl.toggleViewAction())
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
        open_tag = "<span style='color:white;white-space: pre-wrap;'>"
        date_str = get_datetime(show=self.show_datetime)
        message = open_tag + date_str + msg + "</span>"
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_success_message(self, msg):
        """Append message with green text color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:#00ff00;white-space: pre-wrap;'>"
        date_str = get_datetime(show=self.show_datetime)
        message = open_tag + date_str + msg + "</span>"
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_error_message(self, msg):
        """Append message with red color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:#ff3333;white-space: pre-wrap;'>"
        date_str = get_datetime(show=self.show_datetime)
        message = open_tag + date_str + msg + "</span>"
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_warning_message(self, msg):
        """Append message with yellow (golden) color to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:yellow;white-space: pre-wrap;'>"
        date_str = get_datetime(show=self.show_datetime)
        message = open_tag + date_str + msg + "</span>"
        self.ui.textBrowser_eventlog.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_process_message(self, msg):
        """Writes message from stdout to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:white;white-space: pre;'>"
        message = open_tag + msg + "</span>"
        self.ui.textBrowser_process_output.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    @Slot(str)
    def add_process_error_message(self, msg):
        """Writes message from stderr to process output QTextBrowser.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:#ff3333;white-space: pre;'>"
        message = open_tag + msg + "</span>"
        self.ui.textBrowser_process_output.append(message)
        # noinspection PyArgumentList
        QApplication.processEvents()

    def show_add_project_item_form(self, item_category, x=0, y=0):
        """Show add project item widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        category_ind = self.project_item_model.find_category(item_category)
        if not category_ind:
            self.msg_error.emit("Category {0} not found".format(item_category))
            return
        category = self.project_item_model.item(category_ind)
        self.add_project_item_form = category._add_form_maker(self, x, y)
        self.add_project_item_form.show()

    @Slot()
    def show_tool_specification_form(self, tool_specification=None):
        """Show tool specification widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        form = ToolSpecificationWidget(self, tool_specification)
        form.show()

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
        doc_index_path = os.path.join(DOCUMENTATION_PATH, "index.html")
        index_url = "file:///" + doc_index_path
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(index_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", index_url)
            self.msg_error.emit("Unable to open file <b>{0}</b>".format(doc_index_path))

    @Slot()
    def show_getting_started_guide(self):
        """Open Spine Toolbox Getting Started HTML page in browser."""
        getting_started_path = os.path.join(DOCUMENTATION_PATH, "getting_started.html")
        index_url = "file:///" + getting_started_path
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(index_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", index_url)
            self.msg_error.emit("Unable to open file <b>{0}</b>".format(getting_started_path))

    @Slot("QPoint")
    def show_item_context_menu(self, pos):
        """Context menu for project items listed in the project QTreeView.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_project.indexAt(pos)
        global_pos = self.ui.treeView_project.viewport().mapToGlobal(pos)
        self.show_project_item_context_menu(global_pos, ind)

    @Slot("QPoint", str)
    def show_item_image_context_menu(self, pos, name):
        """Context menu for project item images on the QGraphicsView.

        Args:
            pos (QPoint): Mouse position
            name (str): The name of the concerned item
        """
        ind = self.project_item_model.find_item(name)
        self.show_project_item_context_menu(pos, ind)

    def show_project_item_context_menu(self, pos, ind):
        """Create and show project item context menu.

        Args:
            pos (QPoint): Mouse position
            ind (QModelIndex): Index of concerned item
        """
        if not self.project():
            return
        if not ind.isValid():
            # Clicked on a blank area, show the project item model context menu
            self.project_item_context_menu = ProjectItemModelContextMenu(self, pos)
            action = self.project_item_context_menu.get_action()
            if action == "Open project directory...":
                file_url = "file:///" + self._project.project_dir
                self.open_anchor(QUrl(file_url, QUrl.TolerantMode))
            elif action == "Export project to GraphML":
                self.project().export_graphs()
            else:  # No option selected
                pass
        else:
            # Clicked on an item, show the custom context menu for that item
            item = self.project_item_model.item(ind)
            self.project_item_context_menu = item.custom_context_menu(self, pos)
            action = self.project_item_context_menu.get_action()
            item.apply_context_menu_action(self, action)
        self.project_item_context_menu.deleteLater()
        self.project_item_context_menu = None

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

    @Slot("QPoint")
    def show_tool_specification_context_menu(self, pos):
        """Context menu for tool specifications.

        Args:
            pos (QPoint): Mouse position
        """
        if not self.project():
            return
        ind = self.ui.listView_tool_specifications.indexAt(pos)
        global_pos = self.ui.listView_tool_specifications.viewport().mapToGlobal(pos)
        self.tool_specification_context_menu = ToolSpecificationContextMenu(self, global_pos, ind)
        option = self.tool_specification_context_menu.get_action()
        if option == "Edit Tool specification":
            self.edit_tool_specification(ind)
        elif option == "Edit main program file...":
            self.open_tool_main_program_file(ind)
        elif option == "Open main program directory...":
            tool_specification_path = self.tool_specification_model.tool_specification(ind.row()).path
            path_url = "file:///" + tool_specification_path
            self.open_anchor(QUrl(path_url, QUrl.TolerantMode))
        elif option == "Open Tool specification file...":
            self.open_tool_specification_file(ind)
        elif option == "Remove Tool specification":
            self.remove_tool_specification(ind.row())
        else:  # No option selected
            pass
        self.tool_specification_context_menu.deleteLater()
        self.tool_specification_context_menu = None

    def tear_down_items(self):
        """Calls the tear_down method on all project items, so they can clean up their mess if needed."""
        if not self._project:
            return
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
            # Show save project prompt
        self._qsettings.setValue("mainWindow/windowSize", self.size())
        self._qsettings.setValue("mainWindow/windowPosition", self.pos())
        self._qsettings.setValue("mainWindow/windowState", self.saveState(version=1))
        self._qsettings.setValue("mainWindow/projectDockWidgetSplitterState", self.ui.splitter.saveState())
        if self.windowState() == Qt.WindowMaximized:
            self._qsettings.setValue("mainWindow/windowMaximized", True)
        else:
            self._qsettings.setValue("mainWindow/windowMaximized", False)
        # Save number of screens
        # noinspection PyArgumentList
        self._qsettings.setValue("mainWindow/n_screens", len(QGuiApplication.screens()))
        self.julia_repl.shutdown_jupyter_kernel()
        self.python_repl.shutdown_kernel()
        self.tear_down_items()
        event.accept()

    def _serialize_selected_items(self):
        """
        Serializes selected project items into a dictionary.

        The serialization protocol tries to imitate the format in which projects are saved.
        The format of the dictionary is following:
        `{"item_category_1": [{"name": "item_1_name", ...}, ...], ...}`

        Returns:
             a dict containing serialized version of selected project items
        """
        selected_project_items = self.ui.graphicsView.scene().selectedItems()
        serialized_items = dict()
        for item_icon in selected_project_items:
            if not isinstance(item_icon, ProjectItemIcon):
                continue
            name = item_icon.name()
            index = self.project_item_model.find_item(name)
            item = self.project_item_model.item(index)
            category = self.project_item_model.category_of_item(item.name)
            category_items = serialized_items.setdefault(category.name, list())
            item_dict = item.project_item.item_dict()
            item_dict["name"] = item.name
            category_items.append(item_dict)
        return serialized_items

    def _deserialized_item_position_shifts(self, serialized_items):
        """
        Calculates horizontal and vertical shifts for project items being deserialized.

        If the mouse cursor is on the Design view we try to place the items unders the cursor.
        Otherwise the items will get a small shift so they don't overlap a possible item below.
        In case the items don't fit the scene rect we clamp their coordinates within it.

        Args:
            serialized_items (dict): a dictionary of serialized items being deserialized
        Returns:
            a tuple of (horizontal shift, vertical shift) in scene's coordinates
        """
        mouse_position = self.ui.graphicsView.mapFromGlobal(QCursor.pos())
        if self.ui.graphicsView.rect().contains(mouse_position):
            mouse_over_design_view = self.ui.graphicsView.mapToScene(mouse_position)
        else:
            mouse_over_design_view = None
        if mouse_over_design_view is not None:
            first_item = next(iter(serialized_items.values()))[0]
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

    def _deserialize_items(self, serialized_items):
        """
        Deserializes project items from a dictionary and adds them to the current project.

        Args:
            serialized_items (dict): serialized project items
        """
        if self._project is None:
            return
        scene = self.ui.graphicsView.scene()
        scene.clearSelection()
        shift_x, shift_y = self._deserialized_item_position_shifts(serialized_items)
        scene_rect = scene.sceneRect()
        for category_name, item_dicts in serialized_items.items():
            for item in item_dicts:
                name = item["name"]
                if self.project_item_model.find_item(name) is not None:
                    new_name = self.propose_item_name(name)
                    item["name"] = new_name
                self._set_deserialized_item_position(item, shift_x, shift_y, scene_rect)
                item.pop("short name")
            self._project.add_project_items(category_name, *item_dicts, set_selected=True, verbosity=False)

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
        serialized_items = json.loads(item_dump)
        self._deserialize_items(serialized_items)

    @Slot()
    def duplicate_project_item(self):
        """Duplicates the selected project items."""
        serialized_items = self._serialize_selected_items()
        self._deserialize_items(serialized_items)

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

    def _item_edit_actions(self):
        """Creates project item edit actions (copy, paste, duplicate) and adds them to proper places."""

        def prepend_to_edit_menu(text, shortcut, slot):
            action = QAction(text, self.ui.graphicsView)
            action.setShortcuts(shortcut)
            action.setShortcutContext(Qt.WidgetShortcut)
            action.triggered.connect(slot)
            self._project_item_actions.append(action)
            self.ui.graphicsView.addAction(action)
            self.ui.menuEdit.insertAction(self.ui.menuEdit.actions()[0], action)
            return action

        self.ui.menuEdit.insertSeparator(self.ui.menuEdit.actions()[0])
        duplicate_action = prepend_to_edit_menu(
            "Duplicate", [QKeySequence(Qt.CTRL + Qt.Key_D)], lambda checked: self.duplicate_project_item()
        )
        paste_action = prepend_to_edit_menu(
            "Paste", QKeySequence.Paste, lambda checked: self.project_item_from_clipboard()
        )
        copy_action = prepend_to_edit_menu("Copy", QKeySequence.Copy, lambda checked: self.project_item_to_clipboard())

        def mirror_action_to_project_tree_view(action_to_duplicate):
            action = QAction(action_to_duplicate.text(), self.ui.treeView_project)
            action.setShortcuts([action_to_duplicate.shortcut()])
            action.setShortcutContext(Qt.WidgetShortcut)
            action.triggered.connect(action_to_duplicate.trigger)
            self._project_item_actions.append(action)
            self.ui.treeView_project.addAction(action)

        mirror_action_to_project_tree_view(copy_action)
        mirror_action_to_project_tree_view(paste_action)
        mirror_action_to_project_tree_view(duplicate_action)

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
        box.deleteLater()

    def _connect_project_signals(self):
        """Connects signals emitted by project."""
        self._project.dag_execution_about_to_start.connect(self.ui.graphicsView.connect_engine_signals)
        self._project.project_execution_about_to_start.connect(self._scroll_event_log_to_end)
