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
Contains ToolboxUI class.

:author: P. Savolainen (VTT)
:date:   14.12.2017
"""

import os
import locale
import logging
import json
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QUrl, SIGNAL, QTimeLine
from PySide2.QtWidgets import (
    QMainWindow,
    QApplication,
    QFileDialog,
    QMessageBox,
    QCheckBox,
    QInputDialog,
    QDockWidget,
    QAction,
    QWidgetAction,
)
from PySide2.QtGui import QDesktopServices, QGuiApplication, QKeySequence, QStandardItemModel, QIcon, QIntValidator
from spinedb_api import SUPPORTED_DIALECTS
from ui.mainwindow import Ui_MainWindow
from widgets.about_widget import AboutWidget
from widgets.custom_menus import (
    ProjectItemContextMenu,
    ToolTemplateContextMenu,
    LinkContextMenu,
    AddToolTemplatePopupMenu,
    DcRefContextMenu,
    DcDataContextMenu,
    ToolPropertiesContextMenu,
    ViewPropertiesContextMenu,
    DiFilesContextMenu,
)
from widgets.project_form_widget import NewProjectForm
from widgets.settings_widget import SettingsWidget
from widgets.tool_configuration_assistant_widget import ToolConfigurationAssistantWidget
from widgets.add_data_store_widget import AddDataStoreWidget
from widgets.add_data_connection_widget import AddDataConnectionWidget
from widgets.add_tool_widget import AddToolWidget
from widgets.add_view_widget import AddViewWidget
from widgets.add_data_interface_widget import AddDataInterfaceWidget
from widgets.tool_template_widget import ToolTemplateWidget
from widgets.custom_delegates import CheckBoxDelegate
from widgets.custom_qwidgets import ZoomWidget
from widgets.julia_repl_widget import JuliaREPLWidget
from widgets.python_repl_widget import PythonReplWidget
import widgets.toolbars
from project import SpineToolboxProject
from config import (
    SPINE_TOOLBOX_VERSION,
    STATUSBAR_SS,
    TEXTBROWSER_SS,
    MAINWINDOW_SS,
    DOCUMENTATION_PATH,
    TREEVIEW_HEADER_SS,
)
from helpers import project_dir, get_datetime, erase_dir, busy_effect, set_taskbar_icon, supported_img_formats
from models import ProjectItemModel, ToolTemplateModel, ConnectionModel
from project_item import BaseProjectItem


class ToolboxUI(QMainWindow):
    """Class for application main GUI functions."""

    # Custom signals
    msg = Signal(str, name="msg")
    msg_success = Signal(str, name="msg_success")
    msg_error = Signal(str, name="msg_error")
    msg_warning = Signal(str, name="msg_warning")
    msg_proc = Signal(str, name="msg_proc")
    msg_proc_error = Signal(str, name="msg_proc_error")

    def __init__(self):
        """ Initialize application and main window."""
        super().__init__(flags=Qt.Window)
        self._qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set number formatting to use user's default settings
        locale.setlocale(locale.LC_NUMERIC, '')
        # Setup the user interface from Qt Designer files
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        set_taskbar_icon()  # in helpers.py
        self.ui.graphicsView.set_ui(self)
        # Set style sheets
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.textBrowser_eventlog.setStyleSheet(TEXTBROWSER_SS)
        self.ui.textBrowser_process_output.setStyleSheet(TEXTBROWSER_SS)
        self.setStyleSheet(MAINWINDOW_SS)
        # Class variables
        self._project = None
        self.project_item_model = None
        self.tool_template_model = None
        self.connection_model = None
        self.show_datetime = self.update_datetime()
        self.active_project_item = None
        # Widget and form references
        self.settings_form = None
        self.tool_config_asst_form = None
        self.about_form = None
        self.tool_template_context_menu = None
        self.project_item_context_menu = None
        self.link_context_menu = None
        self.process_output_context_menu = None
        self.dc_ref_context_menu = None
        self.dc_data_context_menu = None
        self.tool_prop_context_menu = None
        self.view_prop_context_menu = None
        self.di_files_context_menu = None
        self.project_form = None
        self.add_data_store_form = None
        self.add_data_connection_form = None
        self.add_tool_form = None
        self.add_view_form = None
        self.add_data_interface_form = None
        self.tool_template_form = None
        self.placing_item = ""
        self.add_tool_template_popup_menu = None
        self.connections_tab = None
        self.zoom_widget = None
        self.zoom_widget_action = None
        # Make and initialize toolbars
        self.item_toolbar = widgets.toolbars.ItemToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.item_toolbar)
        # Make julia REPL
        self.julia_repl = JuliaREPLWidget(self)
        self.ui.dockWidgetContents_julia_repl.layout().addWidget(self.julia_repl)
        # Make Python REPL
        self.python_repl = PythonReplWidget(self)
        self.ui.dockWidgetContents_python_repl.layout().addWidget(self.python_repl)
        # Setup main window menu
        self.setup_zoom_action()
        self.add_toggle_view_actions()
        # Hidden QActions for debugging or testing
        self.show_connections_tab = QAction(self)  # self is for PySide 5.6
        self.show_item_tabbar = QAction(self)
        self.show_supported_img_formats = QAction(self)
        self.test_variable_push = QAction(self)
        self.set_debug_qactions()
        self.hide_tabs()
        # Finalize init
        self.connect_signals()
        self.init_shared_widgets()  # Shared among multiple project items
        self.restore_ui()
        self.ui.lineEdit_port.setValidator(QIntValidator())

    # noinspection PyArgumentList, PyUnresolvedReferences
    def connect_signals(self):
        """Connect signals."""
        # Event log signals
        self.msg.connect(self.add_message)
        self.msg_success.connect(self.add_success_message)
        self.msg_error.connect(self.add_error_message)
        self.msg_warning.connect(self.add_warning_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_proc_error.connect(self.add_process_error_message)
        # Custom signals
        self.ui.treeView_dc_references.del_key_pressed.connect(self.remove_refs_with_del_key)
        self.ui.treeView_dc_data.del_key_pressed.connect(self.remove_data_with_del_key)
        # Menu commands
        self.ui.actionNew.triggered.connect(self.new_project)
        self.ui.actionOpen.triggered.connect(self.open_project)
        self.ui.actionSave.triggered.connect(self.save_project)
        self.ui.actionSave_As.triggered.connect(self.save_project_as)
        self.ui.actionExport_project_to_GraphML.triggered.connect(self.export_as_graphml)
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionPackages.triggered.connect(self.show_tool_config_asst)
        self.ui.actionQuit.triggered.connect(self.closeEvent)
        self.ui.actionAdd_Data_Store.triggered.connect(self.show_add_data_store_form)
        self.ui.actionAdd_Data_Connection.triggered.connect(self.show_add_data_connection_form)
        self.ui.actionAdd_Tool.triggered.connect(self.show_add_tool_form)
        self.ui.actionAdd_View.triggered.connect(self.show_add_view_form)
        self.ui.actionAdd_Data_Interface.triggered.connect(self.show_add_data_interface_form)
        self.ui.actionRemove_all.triggered.connect(self.remove_all_items)
        self.ui.actionUser_Guide.triggered.connect(self.show_user_guide)
        self.ui.actionGetting_started.triggered.connect(self.show_getting_started_guide)
        self.ui.actionAbout.triggered.connect(self.show_about)
        self.ui.actionAbout_Qt.triggered.connect(lambda: QApplication.aboutQt())  # pylint: disable=unnecessary-lambda
        self.ui.actionRestore_Dock_Widgets.triggered.connect(self.restore_dock_widgets)
        # Debug QActions
        self.show_item_tabbar.triggered.connect(self.toggle_tabbar_visibility)
        self.show_connections_tab.triggered.connect(self.toggle_connections_tab_visibility)
        self.show_supported_img_formats.triggered.connect(supported_img_formats)  # in helpers.py
        self.test_variable_push.triggered.connect(self.python_repl.test_push_vars)
        # Tool templates tab
        self.add_tool_template_popup_menu = AddToolTemplatePopupMenu(self)
        self.ui.toolButton_add_tool_template.setMenu(self.add_tool_template_popup_menu)
        self.ui.toolButton_remove_tool_template.clicked.connect(self.remove_selected_tool_template)
        # Event Log & Process output
        self.ui.textBrowser_eventlog.anchorClicked.connect(self.open_anchor)
        # Context-menus
        self.ui.treeView_project.customContextMenuRequested.connect(self.show_item_context_menu)
        self.ui.treeView_dc_references.customContextMenuRequested.connect(self.show_dc_ref_properties_context_menu)
        self.ui.treeView_dc_data.customContextMenuRequested.connect(self.show_dc_data_properties_context_menu)
        self.ui.treeView_template.customContextMenuRequested.connect(self.show_tool_properties_context_menu)
        self.ui.treeView_view.customContextMenuRequested.connect(self.show_view_properties_context_menu)
        self.ui.treeView_data_interface_files.customContextMenuRequested.connect(
            self.show_di_files_properties_context_menu
        )
        # Main menu
        self.zoom_widget.minus_pressed.connect(self._handle_zoom_widget_minus_pressed)
        self.zoom_widget.plus_pressed.connect(self._handle_zoom_widget_plus_pressed)
        self.zoom_widget.reset_pressed.connect(self._handle_zoom_widget_reset_pressed)

    def project(self):
        """Returns current project or None if no project open."""
        return self._project

    def qsettings(self):
        """Returns application preferences object."""
        return self._qsettings

    @Slot(name="init_project")
    def init_project(self):
        """Initializes project at application start-up. Loads the last project that was open
        when app was closed or starts without a project if app is started for the first time.
        """
        open_previous_project = int(self._qsettings.value("appSettings/openPreviousProject", defaultValue="0"))
        if open_previous_project != 2:  # 2: Qt.Checked, ie. open_previous_project==True
            p = os.path.join(DOCUMENTATION_PATH, "getting_started.html")
            getting_started_anchor = (
                "<a style='color:#99CCFF;' title='" + p + "' href='file:///" + p + "'>Getting Started</a>"
            )
            self.msg.emit(
                "Welcome to Spine Toolbox! If you need help, please read the {0} guide.".format(getting_started_anchor)
            )
            return
        # Get path to previous project file
        project_file_path = self._qsettings.value("appSettings/previousProject", defaultValue="")
        if not project_file_path:
            return
        if not os.path.isfile(project_file_path):
            msg = "Could not load previous project. File '{0}' not found.".format(project_file_path)
            self.ui.statusbar.showMessage(msg, 10000)
            return
        if not self.open_project(project_file_path):
            self.msg_error.emit("Loading project file <b>{0}</b> failed".format(project_file_path))
            logging.error("Loading project file '%s' failed", project_file_path)
        return

    @Slot(name="new_project")
    def new_project(self):
        """Shows new project form."""
        self.project_form = NewProjectForm(self)
        self.project_form.show()

    def create_project(self, name, description):
        """Create new project and set it active.

        Args:
            name (str): Project name
            description (str): Project description
        """
        self.clear_ui()
        self._project = SpineToolboxProject(self, name, description)
        self._project.connect_signals()
        self.init_models(tool_template_paths=list())  # Start project with no tool templates
        self.setWindowTitle("Spine Toolbox    -- {} --".format(self._project.name))
        self.ui.graphicsView.init_scene(empty=True)
        self.msg.emit("New project created")
        self.save_project()

    # noinspection PyUnusedLocal
    @Slot(name="open_project")
    def open_project(self, load_path=None):
        """Load project from a save file (.proj) file.

        Args:
            load_path (str): Path to project save file. If default value is used,
            a file explorer dialog is opened where the user can select the
            project file to load.

        Returns:
            bool: True when opening the project succeeded, False otherwise
        """
        tool_template_paths = list()
        connections = list()
        if not load_path:
            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            answer = QFileDialog.getOpenFileName(
                self, 'Open project', project_dir(self._qsettings), 'Projects (*.proj)'
            )
            load_path = answer[0]
            if load_path == '':  # Cancel button clicked
                return False
        if not os.path.isfile(load_path):
            self.msg_error.emit("File <b>{0}</b> not found".format(load_path))
            return False
        if not load_path.lower().endswith('.proj'):
            self.msg_error.emit("Selected file has unsupported extension. Only .proj files are supported")
            return False
        # Load project from JSON file
        try:
            with open(load_path, 'r') as fh:
                try:
                    dicts = json.load(fh)
                except json.decoder.JSONDecodeError:
                    self.msg_error.emit("Error in file <b>{0}</b>. Not valid JSON. {0}".format(load_path))
                    return False
        except OSError:
            self.msg_error.emit("[OSError] Loading project file <b>{0}</b> failed".format(load_path))
            return False
        # Initialize UI
        self.clear_ui()
        # Parse project info
        project_dict = dicts['project']
        proj_name = project_dict['name']
        proj_desc = project_dict['description']
        try:
            work_dir = project_dict['work_dir']
        except KeyError:
            work_dir = ""
        try:
            tool_template_paths = project_dict['tool_templates']
        except KeyError:
            self.msg_warning.emit("Tool templates not found in project file")
        try:
            connections = project_dict['connections']
        except KeyError:
            self.msg_warning.emit("No connections found in project file")
        # Create project
        self._project = SpineToolboxProject(self, proj_name, proj_desc, work_dir)
        # Init models and views
        self.setWindowTitle("Spine Toolbox    -- {} --".format(self._project.name))
        # Clear QTextBrowsers
        self.ui.textBrowser_eventlog.clear()
        self.ui.textBrowser_process_output.clear()
        # Populate project model with items read from JSON file
        self.init_models(tool_template_paths)
        if not self._project.load(dicts['objects']):
            self.msg_error.emit("Loading project items failed")
            return False
        self.ui.treeView_project.expandAll()
        # Restore connections
        self.msg.emit("Restoring connections...")
        self.connection_model.reset_model(connections)
        self.ui.tableView_connections.resizeColumnsToContents()
        self.ui.graphicsView.restore_links()
        # Simulate project execution after restoring links
        self._project.simulate_project_execution()
        self._project.connect_signals()
        self.ui.tabWidget.setCurrentIndex(0)  # Activate 'Items' tab
        # Initialize Design View scene
        self.ui.graphicsView.init_scene()
        self.msg.emit("Project <b>{0}</b> is now open".format(self._project.name))
        return True

    @Slot(name="save_project")
    def save_project(self):
        """Save project."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        # Put project's tool template definition files into a list
        tool_templates = list()
        for i in range(self.tool_template_model.rowCount()):
            tool_templates.append(self.tool_template_model.tool_template(i).get_def_path())
        self._project.save(tool_templates)
        self.msg.emit("Project saved to <b>{0}</b>".format(self._project.path))

    @Slot(name="save_project_as")
    def save_project_as(self):
        """Ask user for a new project name and save. Creates a duplicate of the open project."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        msg = "This creates a copy of the current project. <br/><br/>New name:"
        # noinspection PyCallByClass
        answer = QInputDialog.getText(
            self, "New project name", msg, text=self._project.name, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )
        if not answer[1]:  # answer[str, bool]
            return
        name = answer[0]
        # Check if name is valid and copy project tree under a new name
        if not self._project.rename_project(name):
            return
        # Save project into new file
        self.save_project()
        # Load project
        self.open_project(self._project.path)
        return

    def init_models(self, tool_template_paths):
        """Initialize application internal data models.

        Args:
            tool_template_paths (list): List of tool definition file paths used in this project
        """
        self.init_project_item_model()
        # self.ui.treeView_project.selectionModel().currentChanged.connect(self.current_item_changed)
        self.ui.treeView_project.selectionModel().selectionChanged.connect(self.item_selection_changed)
        self.init_tool_template_model(tool_template_paths)
        self.init_connection_model()

    def init_project_item_model(self):
        """Initializes project item model. Create root and category items and
        add them to the model."""
        root_item = BaseProjectItem("root", "", is_root=True, is_category=False)
        ds_category = BaseProjectItem("Data Stores", "", is_root=False, is_category=True)
        dc_category = BaseProjectItem("Data Connections", "", is_root=False, is_category=True)
        tool_category = BaseProjectItem("Tools", "", is_root=False, is_category=True)
        view_category = BaseProjectItem("Views", "", is_root=False, is_category=True)
        di_category = BaseProjectItem("Data Interfaces", "", is_root=False, is_category=True)
        self.project_item_model = ProjectItemModel(self, root=root_item)
        self.project_item_model.insert_item(ds_category)
        self.project_item_model.insert_item(dc_category)
        self.project_item_model.insert_item(tool_category)
        self.project_item_model.insert_item(view_category)
        self.project_item_model.insert_item(di_category)
        self.ui.treeView_project.setModel(self.project_item_model)
        self.ui.treeView_project.header().hide()
        self.ui.graphicsView.set_project_item_model(self.project_item_model)

    def init_tool_template_model(self, tool_template_paths):
        """Initializes Tool template model.

        Args:
            tool_template_paths (list): List of tool definition file paths used in this project
        """
        self.ui.comboBox_tool.setModel(QStandardItemModel())  # Reset combo box by setting and empty model to it
        self.tool_template_model = ToolTemplateModel()
        n_tools = 0
        self.msg.emit("Loading Tool templates...")
        for path in tool_template_paths:
            if path == '' or not path:
                continue
            # Add tool template into project
            tool_cand = self._project.load_tool_template_from_file(path)
            n_tools += 1
            if not tool_cand:
                self.msg_error.emit("Failed to load Tool template from <b>{0}</b>".format(path))
                continue
            # Add tool definition file path to tool instance variable
            tool_cand.set_def_path(path)
            # Insert tool into model
            self.tool_template_model.insertRow(tool_cand)
            # self.msg.emit("Tool template <b>{0}</b> ready".format(tool_cand.name))
        # Set model to the tool template list view
        self.ui.listView_tool_templates.setModel(self.tool_template_model)
        # Set model to Tool project item combo box
        self.ui.comboBox_tool.setModel(self.tool_template_model)
        # Note: If ToolTemplateModel signals are in use, they should be reconnected here.
        # Reconnect ToolTemplateModel and QListView signals. Make sure that signals are connected only once.
        n_recv_sig1 = self.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))  # nr of receivers
        if n_recv_sig1 == 0:
            # logging.debug("Connecting doubleClicked signal for QListView")
            self.ui.listView_tool_templates.doubleClicked.connect(self.edit_tool_template)
        elif n_recv_sig1 > 1:  # Check that this never gets over 1
            logging.error("Number of receivers for QListView doubleClicked signal is now: %d", n_recv_sig1)
        else:
            pass  # signal already connected
        n_recv_sig2 = self.ui.listView_tool_templates.receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        if n_recv_sig2 == 0:
            # logging.debug("Connecting customContextMenuRequested signal for QListView")
            self.ui.listView_tool_templates.customContextMenuRequested.connect(self.show_tool_template_context_menu)
        elif n_recv_sig2 > 1:  # Check that this never gets over 1
            logging.error("Number of receivers for QListView customContextMenuRequested signal is now: %d", n_recv_sig2)
        else:
            pass  # signal already connected
        if n_tools == 0:
            self.msg_warning.emit("Project has no tool templates")

    def init_connection_model(self):
        """Initializes a model representing connections between project items."""
        self.connection_model = ConnectionModel(self)
        self.ui.tableView_connections.setModel(self.connection_model)
        self.ui.tableView_connections.setItemDelegate(CheckBoxDelegate(self))
        self.ui.tableView_connections.itemDelegate().data_committed.connect(self.connection_data_changed)
        self.ui.graphicsView.set_connection_model(self.connection_model)

    def init_shared_widgets(self):
        """Initialize widgets that are shared among all ProjectItems of the same type."""
        # Data Stores
        self.ui.comboBox_dialect.addItems(list(SUPPORTED_DIALECTS.keys()))
        self.ui.comboBox_dialect.setCurrentIndex(-1)
        # Data Connections
        self.ui.treeView_dc_references.setStyleSheet(TREEVIEW_HEADER_SS)
        self.ui.treeView_dc_data.setStyleSheet(TREEVIEW_HEADER_SS)
        # Tools (Tool template combobox is initialized in init_tool_template_model)
        self.ui.treeView_template.setStyleSheet(TREEVIEW_HEADER_SS)
        # Views
        self.ui.treeView_view.setStyleSheet(TREEVIEW_HEADER_SS)
        # Data Interfaces
        self.ui.treeView_data_interface_files.setStyleSheet(TREEVIEW_HEADER_SS)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self._qsettings.value("mainWindow/windowSize", defaultValue="false")
        window_pos = self._qsettings.value("mainWindow/windowPosition", defaultValue="false")
        window_state = self._qsettings.value("mainWindow/windowState", defaultValue="false")
        splitter_state = self._qsettings.value("mainWindow/projectDockWidgetSplitterState", defaultValue="false")
        window_maximized = self._qsettings.value("mainWindow/windowMaximized", defaultValue='false')  # returns str
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
        if window_maximized == 'true':
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
            ind = self.project_item_model.find_item(name)
            self.remove_item(ind)
        self.activate_no_selection_tab()  # Clear widget info from QDockWidget
        if self._project:
            self._project.deleteLater()
        self._project = None
        self.tool_template_model = None
        self.ui.textBrowser_eventlog.clear()
        self.ui.textBrowser_process_output.clear()
        self.ui.graphicsView.scene().clear()  # Clear all items from scene

    @Slot("QItemSelection", "QItemSelection", name="item_selection_changed")
    def item_selection_changed(self, selected, deselected):
        """Synchronize selection with scene. Check if only one item is selected and make it the
        active item: disconnect signals of previous active item, connect signals of current active item
        and show correct properties tab for the latter.
        """
        inds = self.ui.treeView_project.selectedIndexes()
        proj_items = [self.project_item_model.project_item(i) for i in inds]
        # NOTE: Category items are not selectable anymore
        # Sync selection with the scene
        if len(proj_items) > 0:
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
            if self.ui.tabWidget_item_properties.tabText(i) == item.item_type:
                self.ui.tabWidget_item_properties.setCurrentIndex(i)
                break
        # Set QDockWidget title to selected item's type
        self.ui.dockWidget_item.setWindowTitle(item.item_type + " Properties")

    @Slot(name="open_tool_template")
    def open_tool_template(self):
        """Open a file dialog so the user can select an existing tool template .json file.
        Continue loading the tool template into the Project if successful.
        """
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getOpenFileName(
            self,
            'Select Tool template file',
            os.path.join(project_dir(self._qsettings), os.path.pardir),
            'JSON (*.json)',
        )
        if answer[0] == '':  # Cancel button clicked
            return
        def_file = os.path.abspath(answer[0])
        # Load tool definition
        tool_template = self._project.load_tool_template_from_file(def_file)
        if not tool_template:
            self.msg_error.emit("Adding Tool template failed")
            return
        if self.tool_template_model.find_tool_template(tool_template.name):
            # Tool template already added to project
            self.msg_warning.emit("Tool template <b>{0}</b> already in project".format(tool_template.name))
            return
        # Add definition file path into tool tool template
        tool_template.set_def_path(def_file)
        self.add_tool_template(tool_template)

    def add_tool_template(self, tool_template):
        """Add a ToolTemplate instance to project, which then can be added to a Tool item.
        Add tool template definition file path into project file (.proj)

        tool_template (ToolTemplate): Tool template that is added to project
        """
        def_file = tool_template.get_def_path()  # Definition file path (.json)
        # Insert tool template into model
        self.tool_template_model.insertRow(tool_template)
        # Save Tool def file path to project file
        project_file = self._project.path  # Path to project file
        if project_file.lower().endswith('.proj'):
            # Manipulate project file contents
            try:
                with open(project_file, 'r') as fh:
                    dicts = json.load(fh)
            except OSError:
                self.msg_error.emit("OSError: Could not load file <b>{0}</b>".format(project_file))
                return
            # Get project settings
            project_dict = dicts['project']
            objects_dict = dicts['objects']
            try:
                tools = project_dict['tool_templates']
                if def_file not in tools:
                    tools.append(def_file)
                project_dict['tool_templates'] = tools
            except KeyError:
                project_dict['tool_templates'] = [def_file]
            # Save dictionaries back to project save file
            dicts['project'] = project_dict
            dicts['objects'] = objects_dict
            with open(project_file, 'w') as fp:
                json.dump(dicts, fp, indent=4)
            self.msg_success.emit("Tool template <b>{0}</b> added to project".format(tool_template.name))
        else:
            self.msg_error.emit("Unsupported project filename {0}. Extension should be .proj.".format(project_file))
            return

    def update_tool_template(self, row, tool_template):
        """Update a Tool template and refresh Tools that use it.

        Args:
            row (int): Row of tool template in ToolTemplateModel
            tool_template (ToolTemplate): An updated Tool template
        """
        if not self.tool_template_model.update_tool_template(tool_template, row):
            self.msg_error.emit("Unable to update Tool template <b>{0}</b>".format(tool_template.name))
            return
        self.msg_success.emit("Tool template <b>{0}</b> successfully updated".format(tool_template.name))
        # Reattach Tool template to any Tools that use it
        # Find the updated tool template from ToolTemplateModel
        template = self.tool_template_model.find_tool_template(tool_template.name)
        if not template:
            self.msg_error.emit("Could not find Tool template <b>{0}</b>".format(tool_template.name))
            return
        # Get all Tool project items
        tools = self.project_item_model.items("Tools")
        for tool in tools:
            if not tool.tool_template():
                continue
            elif tool.tool_template().name == tool_template.name:
                tool.set_tool_template(template)
                tool.execute_in_work = template.execute_in_work
                self.msg.emit("Tool template <b>{0}</b> reattached to Tool <b>{1}</b>".format(template.name, tool.name))
        # Set execution mode radioButton depending on Tool template setting
        if template.execute_in_work:
            self.ui.radioButton_execute_in_work.setChecked(True)
        else:
            self.ui.radioButton_execute_in_source.setChecked(True)

    @Slot(name="remove_selected_tool_template")
    def remove_selected_tool_template(self):
        """Prepare to remove tool template selected in QListView."""
        if not self._project:
            self.msg.emit("Please create a new project or open an existing one first")
            return
        try:
            index = self.ui.listView_tool_templates.selectedIndexes()[0]
        except IndexError:
            # Nothing selected
            self.msg.emit("Select a Tool template to remove")
            return
        if not index.isValid():
            return
        self.remove_tool_template(index)

    @Slot("QModelIndex", name="remove_tool_template")
    def remove_tool_template(self, index):
        """Remove tool template from ToolTemplateModel
        and tool definition file path from project file.
        Removes also Tool templates from all Tool items
        that use this template."""
        sel_tool = self.tool_template_model.tool_template(index.row())
        tool_def_path = sel_tool.def_file_path
        msg = "Removing Tool template <b>{0}</b> from project. Are you sure?".format(sel_tool.name)
        # noinspection PyCallByClass, PyTypeChecker
        answer = QMessageBox.question(self, 'Remove Tool template', msg, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            return
        # Remove tool def file path from the project file
        project_file = self._project.path
        if not project_file.lower().endswith('.proj'):
            self.msg_error.emit("Project file extension not supported. Needs to be .proj.")
            return
        # Read project data from JSON file
        try:
            with open(project_file, 'r') as fh:
                dicts = json.load(fh)
        except OSError:
            self.msg_error.emit("OSError: Could not load file <b>{0}</b>".format(project_file))
            return
        # Get project settings
        project_dict = dicts['project']
        object_dict = dicts['objects']
        if not self.tool_template_model.removeRow(index.row()):
            self.msg_error.emit("Error in removing Tool template <b>{0}</b>".format(sel_tool.name))
            return
        try:
            tools = project_dict['tool_templates']
            tools.remove(tool_def_path)
            # logging.debug("tools list after removal:{}".format(tools))
            project_dict['tool_templates'] = tools
        except KeyError:
            self.msg_error.emit(
                "This is odd. tool_templates list not found in project file <b>{0}</b>".format(project_file)
            )
            return
        except ValueError:
            self.msg_error.emit(
                "This is odd. Tool template definition file path <b>{0}</b> not found "
                "in project file <b>{1}</b>".format(tool_def_path, project_file)
            )
            return
        # Save dictionaries back to JSON file
        dicts['project'] = project_dict
        dicts['objects'] = object_dict
        with open(project_file, 'w') as fp:
            json.dump(dicts, fp, indent=4)
        self.msg_success.emit("Tool template removed")

    def remove_all_items(self):
        """Slot for Remove All button."""
        if not self._project:
            self.msg.emit("No project items to remove")
            return
        msg = "Remove all items from project?"
        # noinspection PyCallByClass, PyTypeChecker
        answer = QMessageBox.question(self, 'Removing all items', msg, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            return
        item_names = self.project_item_model.item_names()
        n = len(item_names)
        if n == 0:
            return
        for name in item_names:
            ind = self.project_item_model.find_item(name)
            delete_int = int(self._qsettings.value("appSettings/deleteData", defaultValue="0"))
            delete_bool = delete_int != 0
            self.remove_item(ind, delete_item=delete_bool)
        self.msg.emit("All {0} items removed from project".format(n))
        self.activate_no_selection_tab()
        self.ui.graphicsView.scene().clear()
        self.ui.graphicsView.init_scene()

    def remove_item(self, ind, delete_item=False, check_dialog=False):
        """Removes item from project when it's index in the project model is known.
        To remove all items in project, loop all indices through this method.
        This method is used in both opening and creating a new project as
        well as when item(s) are deleted from project.
        Use delete_item=False when closing the project or creating a new one.
        Setting delete_item=True deletes the item irrevocably. This means that
        data directories will be deleted from the hard drive. Handles also
        removing the node from the dag graph that contains it.

        Args:
            ind (QModelIndex): Index of removed item in project model
            delete_item (bool): If set to True, deletes the directories and data associated with the item
            check_dialog (bool): If True, shows 'Are you sure?' message box
        """
        project_item = self.project_item_model.project_item(ind)
        name = project_item.name
        if check_dialog:
            if not delete_item:
                msg = (
                    "Are you sure? If Yes, item data directory will still be available in "
                    "the project directory after this operation.\n\n"
                    "Tip: Remove items by pressing 'Delete' key to bypass this dialog."
                )
            else:
                msg = (
                    "Are you sure? If Yes, item data directory will be deleted from your project.\n\n"
                    "Tip: Remove items by pressing 'Delete' key to bypass this dialog."
                )
            # noinspection PyCallByClass, PyTypeChecker
            answer = QMessageBox.question(self, "Remove item {0}?".format(name), msg, QMessageBox.Yes, QMessageBox.No)
            if not answer == QMessageBox.Yes:
                return
        try:
            data_dir = project_item.data_dir
        except AttributeError:
            data_dir = None
        # Remove item from connection model. This also removes Link QGraphicsItems associated to this item
        if not self.connection_model.remove_item(project_item.name):
            self.msg_error.emit("Removing item {0} from connection model failed".format(project_item.name))
        # Remove item from project model
        if not self.project_item_model.remove_item(project_item, parent=ind.parent()):
            self.msg_error.emit("Removing item <b>{0}</b> from project failed".format(name))
        # Remove item icon (QGraphicsItems) from scene
        self.ui.graphicsView.scene().removeItem(project_item.get_icon())
        self._project.dag_handler.remove_node_from_graph(name)
        if delete_item:
            if data_dir:
                # Remove data directory and all its contents
                self.msg.emit("Removing directory <b>{0}</b>".format(data_dir))
                try:
                    if not erase_dir(data_dir):
                        self.msg_error.emit("Directory does not exist")
                except OSError:
                    self.msg_error.emit("[OSError] Removing directory failed. Check directory permissions.")
        self.msg.emit("Item <b>{0}</b> removed from project".format(name))

    @Slot("QUrl", name="open_anchor")
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

    @Slot("QModelIndex", name='edit_tool_template')
    def edit_tool_template(self, index):
        """Open the tool template widget for editing an existing tool template.

        Args:
            index (QModelIndex): Index of the item (from double-click or contex menu signal)
        """
        if not index.isValid():
            return
        tool_template = self.tool_template_model.tool_template(index.row())
        # Show the template in the Tool Template Form
        self.show_tool_template_form(tool_template)

    @busy_effect
    @Slot("QModelIndex", name='open_tool_template_file')
    def open_tool_template_file(self, index):
        """Open the Tool template definition file in the default (.json) text-editor.

        Args:
            index (QModelIndex): Index of the item
        """
        if not index.isValid():
            return
        tool_template = self.tool_template_model.tool_template(index.row())
        file_path = tool_template.get_def_path()
        # Check if file exists first. openUrl may return True if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            logging.error("Failed to open editor for %s", file_path)
            self.msg_error.emit("Tool template definition file <b>{0}</b> not found.".format(file_path))
            return
        tool_template_url = "file:///" + file_path
        # Open Tool template definition file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(tool_template_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", tool_template_url)
            self.msg_error.emit(
                "Unable to open Tool template definition file {0}. Make sure that <b>.json</b> "
                "files are associated with a text editor. For example on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(file_path)
            )
        return

    @busy_effect
    @Slot("QModelIndex", name='open_tool_main_program_file')
    def open_tool_main_program_file(self, index):
        """Open the tool template's main program file in the default editor.

        Args:
            index (QModelIndex): Index of the item
        """
        if not index.isValid():
            return
        tool = self.tool_template_model.tool_template(index.row())
        file_path = os.path.join(tool.path, tool.includes[0])
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
        # Open Tool template main program file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(main_program_url, QUrl.TolerantMode))
        if not res:
            filename, file_extension = os.path.splitext(file_path)
            self.msg_error.emit(
                "Unable to open Tool template main program file {0}. "
                "Make sure that <b>{1}</b> "
                "files are associated with an editor. E.g. on Windows "
                "10, go to Control Panel -> Default Programs to do this.".format(filename, file_extension)
            )
        return

    @Slot(name="export_as_graphml")
    def export_as_graphml(self):
        """Exports all DAGs in project to separate GraphML files."""
        if not self.project():
            self.msg.emit("Please open or create a project first")
            return
        self.project().export_graphs()

    @Slot("QModelIndex", name="connection_data_changed")
    def connection_data_changed(self, index):
        """[OBSOLETE?] Called when checkbox delegate wants to
        edit connection data. Add or remove Link instance accordingly."""
        d = self.connection_model.data(index, Qt.DisplayRole)  # Current status
        if d == "False":  # Add link
            src_name = self.connection_model.headerData(index.row(), Qt.Vertical, Qt.DisplayRole)
            dst_name = self.connection_model.headerData(index.column(), Qt.Horizontal, Qt.DisplayRole)
            self.ui.graphicsView.add_link(src_name, dst_name, index)
        else:  # Remove link
            self.ui.graphicsView.remove_link(index)

    @Slot(name="_handle_zoom_widget_minus_pressed")
    def _handle_zoom_widget_minus_pressed(self):
        """Slot for handling case when '-' button in menu is pressed."""
        self.ui.graphicsView.zoom_out()

    @Slot(name="_handle_zoom_widget_plus_pressed")
    def _handle_zoom_widget_plus_pressed(self):
        """Slot for handling case when '+' button in menu is pressed."""
        self.ui.graphicsView.zoom_in()

    @Slot(name="_handle_zoom_widget_reset_pressed")
    def _handle_zoom_widget_reset_pressed(self):
        """Slot for handling case when 'reset zoom' button in menu is pressed."""
        self.ui.graphicsView.reset_zoom()

    def setup_zoom_action(self):
        """Setup zoom action in view menu."""
        self.zoom_widget = ZoomWidget(self)
        self.zoom_widget_action = QWidgetAction(self)
        self.zoom_widget_action.setDefaultWidget(self.zoom_widget)
        self.ui.menuView.addSeparator()
        self.ui.menuView.addAction(self.zoom_widget_action)

    @Slot(name="restore_dock_widgets")
    def restore_dock_widgets(self):
        """Dock all floating and or hidden QDockWidgets back to the main window."""
        for dock in self.findChildren(QDockWidget):
            if not dock.isVisible():
                dock.setVisible(True)
            if dock.isFloating():
                dock.setFloating(False)

    def set_debug_qactions(self):
        """Set shortcuts for QActions that may be needed in debugging."""
        self.show_item_tabbar.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_0))
        self.show_connections_tab.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_9))
        self.show_supported_img_formats.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_8))
        self.test_variable_push.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_7))
        self.addAction(self.show_item_tabbar)
        self.addAction(self.show_connections_tab)
        self.addAction(self.show_supported_img_formats)
        self.addAction(self.test_variable_push)

    def hide_tabs(self):
        """Hides project item info tab bar and connections tab in project item QTreeView.
        Makes (hidden) actions on how to show them if needed for debugging purposes."""
        self.ui.tabWidget_item_properties.tabBar().hide()  # Hide project item info QTabBar
        self.connections_tab = self.ui.tabWidget.widget(1)
        self.ui.tabWidget.removeTab(1)  # Remove connections tab

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuToolbars.addAction(self.item_toolbar.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_project.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_eventlog.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_process_output.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_python_repl.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_julia_repl.toggleViewAction())

    def toggle_tabbar_visibility(self):
        """Shows or hides the tab bar in project item info tab widget. For debugging purposes."""
        if self.ui.tabWidget_item_properties.tabBar().isVisible():
            self.ui.tabWidget_item_properties.tabBar().hide()
        else:
            self.ui.tabWidget_item_properties.tabBar().show()

    def toggle_connections_tab_visibility(self):
        """Shows or hides connections tab in the project item QTreeView. For debugging purposes."""
        if self.ui.tabWidget.count() == 1:  # Connections tab hidden
            self.ui.tabWidget.insertTab(1, self.connections_tab, "Connections")
        else:
            self.connections_tab = self.ui.tabWidget.widget(1)
            self.ui.tabWidget.removeTab(1)

    def update_datetime(self):
        """Returns a boolean, which determines whether
        date and time is prepended to every Event Log message."""
        d = int(self._qsettings.value("appSettings/dateTime", defaultValue="2"))
        return d != 0

    @Slot(str, name="add_message")
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

    @Slot(str, name="add_success_message")
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

    @Slot(str, name="add_error_message")
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

    @Slot(str, name="add_warning_message")
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

    @Slot(str, name="add_process_message")
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

    @Slot(str, name="add_process_error_message")
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

    @Slot("float", "float", name="show_add_data_store_form")
    def show_add_data_store_form(self, x=0, y=0):
        """Show add data store widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.add_data_store_form = AddDataStoreWidget(self, x, y)
        self.add_data_store_form.show()

    @Slot("float", "float", name="show_add_data_connection_form")
    def show_add_data_connection_form(self, x=0, y=0):
        """Show add data connection widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.add_data_connection_form = AddDataConnectionWidget(self, x, y)
        self.add_data_connection_form.show()

    @Slot("float", "float", name="show_add_data_interface_form")
    def show_add_data_interface_form(self, x=0, y=0):
        """Show add data interface widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.add_data_interface_form = AddDataInterfaceWidget(self, x, y)
        self.add_data_interface_form.show()

    @Slot("float", "float", name="show_add_tool_form")
    def show_add_tool_form(self, x=0, y=0):
        """Show add tool widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.add_tool_form = AddToolWidget(self, x, y)
        self.add_tool_form.show()

    @Slot("float", "float", name="show_add_view_form")
    def show_add_view_form(self, x=0, y=0):
        """Show add view widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.add_view_form = AddViewWidget(self, x, y)
        self.add_view_form.show()

    @Slot(name="show_tool_template_form")
    def show_tool_template_form(self, tool_template=None):
        """Show create tool template widget."""
        if not self._project:
            self.msg.emit("Please open or create a project first")
            return
        self.tool_template_form = ToolTemplateWidget(self, tool_template)
        self.tool_template_form.show()

    @Slot(name="show_settings")
    def show_settings(self):
        """Show Settings widget."""
        self.settings_form = SettingsWidget(self)
        self.settings_form.show()

    @Slot(name="show_tool_config_asst")
    def show_tool_config_asst(self):
        """Show Tool configuration assistant widget."""
        self.tool_config_asst_form = ToolConfigurationAssistantWidget(self)
        self.tool_config_asst_form.show()

    @Slot(name="show_about")
    def show_about(self):
        """Show About Spine Toolbox form."""
        self.about_form = AboutWidget(self, SPINE_TOOLBOX_VERSION)
        self.about_form.show()

    @Slot(name="show_user_guide")
    def show_user_guide(self):
        """Open Spine Toolbox documentation index page in browser."""
        doc_index_path = os.path.join(DOCUMENTATION_PATH, "index.html")
        index_url = "file:///" + doc_index_path
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(index_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", index_url)
            self.msg_error.emit("Unable to open file <b>{0}</b>".format(doc_index_path))

    @Slot(name="show_getting_started_guide")
    def show_getting_started_guide(self):
        """Open Spine Toolbox Getting Started HTML page in browser."""
        getting_started_path = os.path.join(DOCUMENTATION_PATH, "getting_started.html")
        index_url = "file:///" + getting_started_path
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(index_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for %s", index_url)
            self.msg_error.emit("Unable to open file <b>{0}</b>".format(getting_started_path))

    @Slot("QPoint", name="show_item_context_menu")
    def show_item_context_menu(self, pos):
        """Context menu for project items listed in the project QTreeView.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_project.indexAt(pos)
        global_pos = self.ui.treeView_project.viewport().mapToGlobal(pos)
        self.show_project_item_context_menu(global_pos, ind)

    @Slot("QPoint", str, name="show_item_image_context_menu")
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
        self.project_item_context_menu = ProjectItemContextMenu(self, pos, ind)
        option = self.project_item_context_menu.get_action()
        d = self.project_item_model.project_item(ind)
        if option == "Open directory...":
            d.open_directory()  # Open data_dir of Data Connection or Data Store
        elif option == "Open tree view...":
            d.open_tree_view()  # Open tree view of Data Store
        elif option == "Open graph view...":
            d.open_graph_view()  # Open graph view of Data Store
        elif option == "Open tabular view...":
            d.open_tabular_view()  # Open tabular view of Data Store
        elif option == "Results...":
            d.open_results()
        elif option == "Stop":
            # Check that the wheel is still visible, because execution may have stopped before the user clicks Stop
            if d.get_icon().timer.state() != QTimeLine.Running:
                self.msg.emit("Tool <b>{0}</b> is not running".format(d.name))
            else:
                d.stop_process()  # Proceed with stopping
        elif option == "Edit Tool template":
            d.edit_tool_template()
        elif option == "Edit main program file...":
            d.open_tool_main_program_file()
        elif option == "Rename":
            # noinspection PyCallByClass
            answer = QInputDialog.getText(
                self, "Rename Item", "New name:", text=d.name, flags=Qt.WindowTitleHint | Qt.WindowCloseButtonHint
            )
            # answer[str, bool]
            if not answer[1]:
                pass
            else:
                new_name = answer[0]
                self.project_item_model.setData(ind, new_name)
        elif option == "Remove item":
            delete_int = int(self._qsettings.value("appSettings/deleteData", defaultValue="0"))
            delete_bool = delete_int != 0
            self.remove_item(ind, delete_item=delete_bool, check_dialog=True)
        elif option == "Open project directory...":
            file_url = "file:///" + self._project.project_dir
            self.open_anchor(QUrl(file_url, QUrl.TolerantMode))
        elif option == "Export project to GraphML":
            self.project().export_graphs()
        else:  # No option selected
            pass
        self.project_item_context_menu.deleteLater()
        self.project_item_context_menu = None

    def show_link_context_menu(self, pos, link):
        """Context menu for connection links.

        Args:
            pos (QPoint): Mouse position
            link (Link(QGraphicsPathItem)): The concerned link
        """
        self.link_context_menu = LinkContextMenu(self, pos, link.model_index, link.parallel_link)
        option = self.link_context_menu.get_action()
        if option == "Remove connection":
            self.ui.graphicsView.remove_link(link.model_index)
            return
        if option == "Take connection":
            self.ui.graphicsView.take_link(link.model_index)
            return
        if option == "Send to bottom":
            link.send_to_bottom()
        self.link_context_menu.deleteLater()
        self.link_context_menu = None

    @Slot("QPoint", name="show_tool_template_context_menu")
    def show_tool_template_context_menu(self, pos):
        """Context menu for tool templates.

        Args:
            pos (QPoint): Mouse position
        """
        if not self.project():
            return
        ind = self.ui.listView_tool_templates.indexAt(pos)
        global_pos = self.ui.listView_tool_templates.viewport().mapToGlobal(pos)
        self.tool_template_context_menu = ToolTemplateContextMenu(self, global_pos, ind)
        option = self.tool_template_context_menu.get_action()
        if option == "Edit Tool template":
            self.edit_tool_template(ind)
        elif option == "Edit main program file...":
            self.open_tool_main_program_file(ind)
        elif option == "Open main program directory...":
            tool_template_path = self.tool_template_model.tool_template(ind.row()).path
            path_url = "file:///" + tool_template_path
            self.open_anchor(QUrl(path_url, QUrl.TolerantMode))
        elif option == "Open Tool template definition file...":
            self.open_tool_template_file(ind)
        elif option == "Remove Tool template":
            self.remove_tool_template(ind)
        else:  # No option selected
            pass
        self.tool_template_context_menu.deleteLater()
        self.tool_template_context_menu = None

    @Slot("QPoint", name="show_dc_ref_properties_context_menu")
    def show_dc_ref_properties_context_menu(self, pos):
        """Create and show a context-menu in data connection properties
        references view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_dc_references.indexAt(pos)
        global_pos = self.ui.treeView_dc_references.viewport().mapToGlobal(pos)
        self.dc_ref_context_menu = DcRefContextMenu(self, global_pos, ind)
        option = self.dc_ref_context_menu.get_action()
        # Get selected Data Connection from project item model
        cur_index = self.ui.treeView_project.currentIndex()
        dc = self.project_item_model.project_item(cur_index)
        if not dc:
            self.msg_error.emit("FIXME: Data Connection {0} not found in project items".format(cur_index))
            return
        if option == "Open containing directory...":
            ref_path = self.ui.treeView_dc_references.model().itemFromIndex(ind).data(Qt.DisplayRole)
            ref_dir = os.path.split(ref_path)[0]
            file_url = "file:///" + ref_dir
            self.open_anchor(QUrl(file_url, QUrl.TolerantMode))
        elif option == "Edit...":
            dc.open_reference(ind)
        elif option == "Add reference(s)":
            dc.add_references()
        elif option == "Remove reference(s)":
            dc.remove_references()
        elif option == "Copy reference(s) to project":
            dc.copy_to_project()
        return

    @Slot("QPoint", name="show_dc_data_properties_context_menu")
    def show_dc_data_properties_context_menu(self, pos):
        """Create and show a context-menu in data connection properties
        data view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_dc_data.indexAt(pos)
        global_pos = self.ui.treeView_dc_data.viewport().mapToGlobal(pos)
        self.dc_data_context_menu = DcDataContextMenu(self, global_pos, ind)
        option = self.dc_data_context_menu.get_action()
        # Get selected Data Connection from project item model
        cur_index = self.ui.treeView_project.currentIndex()
        dc = self.project_item_model.project_item(cur_index)
        if not dc:
            self.msg_error.emit("FIXME: Data Connection {0} not found in project items".format(cur_index))
            return
        if option == "New file...":
            dc.make_new_file()
        elif option == "Edit...":
            dc.open_data_file(ind)
        elif option == "Remove file(s)":
            dc.remove_files()
        elif option == "Open Spine Datapackage Editor":
            dc.show_spine_datapackage_form()
        elif option == "Open directory...":
            dc.open_directory()
        return

    @Slot("QPoint", name="show_tool_properties_context_menu")
    def show_tool_properties_context_menu(self, pos):
        """Create and show a context-menu in Tool properties
        if selected Tool has a Tool template.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_template.indexAt(pos)  # Index of selected QStandardItem in Tool properties tree view.
        cur_index = self.ui.treeView_project.currentIndex()  # Get selected Tool
        tool = self.project_item_model.project_item(cur_index)
        if not tool.tool_template():
            return
        # Find index of Tool template
        name = tool.tool_template().name
        tool_index = self.tool_template_model.tool_template_index(name)
        global_pos = self.ui.treeView_template.viewport().mapToGlobal(pos)
        self.tool_prop_context_menu = ToolPropertiesContextMenu(self, global_pos, ind)
        option = self.tool_prop_context_menu.get_action()
        if option == "Edit Tool template":
            self.edit_tool_template(tool_index)  # index in tool template model
        elif option == "Edit main program file...":
            self.open_tool_main_program_file(tool_index)  # index in tool template model
        elif option == "Open main program directory...":
            tool.open_tool_main_directory()
        elif option == "Open Tool template definition file...":
            self.open_tool_template_file(tool_index)
        elif option == "Open directory...":
            tool.open_directory()
        return

    @Slot("QPoint", name="show_view_properties_context_menu")
    def show_view_properties_context_menu(self, pos):
        """Create and show a context-menu in View properties.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_view.indexAt(pos)  # Index of selected item in View references tree view.
        cur_index = self.ui.treeView_project.currentIndex()  # Get selected View
        view = self.project_item_model.project_item(cur_index)
        global_pos = self.ui.treeView_view.viewport().mapToGlobal(pos)
        self.view_prop_context_menu = ViewPropertiesContextMenu(self, global_pos, ind)
        option = self.view_prop_context_menu.get_action()
        if option == "Open tree view":
            view.open_tree_view_btn_clicked()
        elif option == "Open graph view":
            view.open_graph_view_btn_clicked()
        elif option == "Open tabular view":
            view.open_tabular_view_btn_clicked()
        return

    @Slot("QPoint", name="show_di_files_properties_context_menu")
    def show_di_files_properties_context_menu(self, pos):
        """Create and show a context-menu in Data Interface properties source files view.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_data_interface_files.indexAt(pos)  # Index of selected item in DI references tree view.
        cur_index = self.ui.treeView_project.currentIndex()  # Get selected DI
        di = self.project_item_model.project_item(cur_index)
        global_pos = self.ui.treeView_data_interface_files.viewport().mapToGlobal(pos)
        self.di_files_context_menu = DiFilesContextMenu(self, global_pos, ind)
        option = self.di_files_context_menu.get_action()
        if option == "Open import editor":
            di.open_import_editor(ind)
        elif option == "Select connector type":
            di.select_connector_type(ind)
        elif option == "Open directory...":
            di.open_directory()
        return

    @Slot(name="remove_refs_with_del_key")
    def remove_refs_with_del_key(self):
        """Slot that removes selected references from the currently selected Data Connection.
        Used when removing DC references by pressing the Delete key on keyboard (Qt.Key_Delete)."""
        cur_index = self.ui.treeView_project.currentIndex()  # Find selected dc index
        if not cur_index.isValid():
            return
        dc = self.project_item_model.project_item(cur_index)
        if not dc:
            return
        dc.remove_references()

    @Slot(name="remove_data_with_del_key")
    def remove_data_with_del_key(self):
        """Slot that removes selected data files from the currently selected Data Connection.
        Used when removing DC data files by pressing the Delete key on keyboard (Qt.Key_Delete)."""
        cur_index = self.ui.treeView_project.currentIndex()  # Find selected dc index
        if not cur_index.isValid():
            return
        dc = self.project_item_model.project_item(cur_index)
        if not dc:
            return
        dc.remove_files()

    def close_view_forms(self):
        """Closes all GraphViewForm, TreeViewForm, and TabularViewForm instances opened in
        Data Stores and Views. Ensures that close() method is called on all corresponding
        DiffDatabaseMapping instances, which cleans up the databases. Also closes all
        SpineDatapackageWidget instances opened in Data Connections.
        """
        if not self._project:
            return
        for data_store in self.project_item_model.items("Data Stores"):
            if data_store.tree_view_form:
                data_store.tree_view_form.close()
            if data_store.tabular_view_form:
                data_store.tabular_view_form.close()
            if data_store.graph_view_form:
                data_store.graph_view_form.close()
        for data_connection in self.project_item_model.items("Data Connections"):
            if data_connection.spine_datapackage_form:
                data_connection.spine_datapackage_form.close()
        for view in self.project_item_model.items("Views"):
            view.close_all_views()

    def show_confirm_exit(self):
        """Shows confirm exit message box.

        Returns:
            True if user clicks Yes or False if exit is cancelled
        """
        ex = int(self._qsettings.value("appSettings/showExitPrompt", defaultValue="2"))
        if ex == 2:  # 2 as in True
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Confirm exit")
            msg.setText("Are you sure you want to exit Spine Toolbox?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()  # Show message box
            if answer == QMessageBox.Yes:
                # Update conf file according to checkbox status
                if not chkbox.checkState():
                    show_prompt = "2"  # 2 as in True
                else:
                    show_prompt = "0"  # 0 as in False
                self._qsettings.setValue("appSettings/showExitPrompt", show_prompt)
                return True
            return False
        return True

    def show_save_project_prompt(self):
        """Shows the save project message box."""
        save_at_exit = int(self._qsettings.value("appSettings/saveAtExit", defaultValue="1"))
        if save_at_exit == 0:
            # Don't save project and don't show message box
            return
        if save_at_exit == 1:  # Default
            # Show message box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Save project")
            msg.setText("Save changes to project?")
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            chkbox = QCheckBox()
            chkbox.setText("Do not ask me again")
            msg.setCheckBox(chkbox)
            answer = msg.exec_()
            chk = chkbox.checkState()
            if answer == QMessageBox.Yes:
                self.save_project()
                if chk == 2:
                    # Save preference
                    self._qsettings.setValue("appSettings/saveAtExit", "2")
            else:
                if chk == 2:
                    # Save preference
                    self._qsettings.setValue("appSettings/saveAtExit", "0")
        elif save_at_exit == 2:
            # Save project and don't show message box
            self.save_project()
        else:
            self._qsettings.setValue("appSettings/saveAtExit", "1")
        return

    def closeEvent(self, event=None):
        """Method for handling application exit.

        Args:
             event (QEvent): PySide2 event
        """
        # Show confirm exit message box
        if not self.show_confirm_exit():
            # Exit cancelled
            if event:
                event.ignore()
            return
        # Save current project (if enabled in settings)
        if not self._project:
            self._qsettings.setValue("appSettings/previousProject", "")
        else:
            self._qsettings.setValue("appSettings/previousProject", self._project.path)
            # Show save project prompt
            self.show_save_project_prompt()
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
        self.close_view_forms()
        if event:
            event.accept()
        # noinspection PyArgumentList
        QApplication.quit()
