#############################################################################
# Copyright (C) 2017 - 2018 VTT Technical Research Centre of Finland
#
# This file is part of Spine Toolbox.
#
# Spine Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#############################################################################

"""
Class for main application GUI functions.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   14.12.2017
"""

import os
import locale
import logging
import json
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QUrl, QModelIndex, SIGNAL
from PySide2.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QCheckBox, QAction
from PySide2.QtGui import QStandardItemModel, QStandardItem, QDesktopServices
from ui.mainwindow import Ui_MainWindow
from widgets.data_store_widget import DataStoreForm
from widgets.about_widget import AboutWidget
from widgets.custom_menus import ProjectItemContextMenu, ToolTemplateContextMenu, LinkContextMenu, \
    addToolTemplatePopupMenu
from widgets.project_form_widget import NewProjectForm
from widgets.settings_widget import SettingsWidget
from widgets.add_data_store_widget import AddDataStoreWidget
from widgets.add_data_connection_widget import AddDataConnectionWidget
from widgets.add_tool_widget import AddToolWidget
from widgets.add_view_widget import AddViewWidget
from widgets.tool_template_widget import ToolTemplateWidget
import widgets.toolbars
from project import SpineToolboxProject
from configuration import ConfigurationParser
from config import SPINE_TOOLBOX_VERSION, CONFIGURATION_FILE, SETTINGS, STATUSBAR_SS, TEXTBROWSER_SS, \
    SPLITTER_SS, SEPARATOR_SS
from helpers import project_dir, get_datetime, erase_dir, blocking_updates
from models import ToolTemplateModel, ConnectionModel


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
        # Set number formatting to use user's default settings
        locale.setlocale(locale.LC_NUMERIC, '')
        # Setup the user interface from Qt Designer files
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Class variables
        self._config = None
        self._project = None
        self.project_item_model = None
        self.tool_template_model = None
        self.connection_model = None
        # Widget and form references
        self.settings_form = None
        self.about_form = None
        self.data_store_form = None
        self.tool_template_context_menu = None
        self.project_item_context_menu = None
        self.link_context_menu = None
        self.add_tool_template_popup_menu = None
        self.project_form = None
        self.add_data_store_form = None
        self.add_data_connection_form = None
        self.add_tool_form = None
        self.add_view_form = None
        self.tool_template_form = None
        self.project_refs = list()  # TODO: Find out why these are needed in addition with project_item_model
        # self.scene_bg = SceneBackground(self)
        # Initialize application
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)  # Initialize QStatusBar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.textBrowser_eventlog.setStyleSheet(TEXTBROWSER_SS)
        self.ui.textBrowser_process_output.setStyleSheet(TEXTBROWSER_SS)
        self.ui.splitter.setStyleSheet(SPLITTER_SS)
        self.setStyleSheet(SEPARATOR_SS)
        # Make and initialize toolbars
        self.item_toolbar = widgets.toolbars.make_item_toolbar(self)
        self.addToolBar(Qt.TopToolBarArea, self.item_toolbar)
        # Make keyboard shortcuts
        self.test1_action = QAction(self)
        self.test1_action.setShortcut("F5")
        self.addAction(self.test1_action)
        self.test2_action = QAction(self)
        self.test2_action.setShortcut("F6")
        self.addAction(self.test2_action)
        self.init_conf()  # Load settings to memory
        self.set_debug_level(level=self._config.get("settings", "logging_level"))
        self.connect_signals()
        self.init_project()
        self.restore_ui()

    def init_conf(self):
        """Load settings from configuration file."""
        self._config = ConfigurationParser(CONFIGURATION_FILE, defaults=SETTINGS)
        self._config.load()

    # noinspection PyMethodMayBeStatic
    def set_debug_level(self, level):
        """Control application debug message verbosity.

        Args:
            level (str): '0': Error messages only, '2': All messages
        """
        if level == '2':
            logging.getLogger().setLevel(level=logging.DEBUG)
            logging.debug("Logging level: All messages")
        else:
            logging.debug("Logging level: Error messages only")
            logging.getLogger().setLevel(level=logging.ERROR)

    def connect_signals(self):
        """Connect signals."""
        # Event log signals
        self.msg.connect(self.add_message)
        self.msg_success.connect(self.add_success_message)
        self.msg_error.connect(self.add_error_message)
        self.msg_warning.connect(self.add_warning_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_proc_error.connect(self.add_process_error_message)
        # Menu commands
        self.ui.actionNew.triggered.connect(self.new_project)
        self.ui.actionOpen.triggered.connect(self.open_project)
        self.ui.actionSave.triggered.connect(self.save_project)
        self.ui.actionSave_As.triggered.connect(self.save_project_as)
        self.ui.actionSettings.triggered.connect(self.show_settings)
        self.ui.actionQuit.triggered.connect(self.closeEvent)
        self.ui.actionData_Store.triggered.connect(self.open_data_store_view)
        self.ui.actionAdd_Data_Store.triggered.connect(self.show_add_data_store_form)
        self.ui.actionAdd_Data_Connection.triggered.connect(self.show_add_data_connection_form)
        self.ui.actionAdd_Tool.triggered.connect(self.show_add_tool_form)
        self.ui.actionAdd_View.triggered.connect(self.show_add_view_form)
        self.ui.actionAdd_Item_Toolbar.triggered.connect(lambda: self.item_toolbar.show())
        self.ui.actionEvent_Log.triggered.connect(lambda: self.ui.dockWidget_eventlog.show())
        self.ui.actionSubprocess_Output.triggered.connect(lambda: self.ui.dockWidget_process_output.show())
        self.ui.actionSelected_Item.triggered.connect(lambda: self.ui.dockWidget_item.show())
        self.ui.actionAbout.triggered.connect(self.show_about)
        # Keyboard shortcut actions
        # noinspection PyUnresolvedReferences
        self.test1_action.triggered.connect(self.test1)
        # noinspection PyUnresolvedReferences
        self.test2_action.triggered.connect(self.test2)
        # QGraphicsView and QGraphicsScene
        # self.ui.graphicsView.scene().sceneRectChanged.connect(self.scene_bg.update_scene_bg)
        # self.ui.graphicsView.subWindowActivated.connect(self.update_details_frame)
        # Project TreeView
        self.ui.treeView_project.clicked.connect(self.select_item_and_show_info)
        # self.ui.treeView_project.doubleClicked.connect(self.show_subwindow)
        self.ui.treeView_project.customContextMenuRequested.connect(self.show_item_context_menu)
        # Tools ListView
        self.add_tool_template_popup_menu = addToolTemplatePopupMenu(self)
        self.ui.pushButton_add_tool_template.setMenu(self.add_tool_template_popup_menu)
        self.ui.pushButton_refresh_tool_templates.clicked.connect(self.refresh_tool_templates)
        self.ui.pushButton_remove_tool_template.clicked.connect(self.remove_selected_tool_template)
        self.ui.listView_tool_templates.setContextMenuPolicy(Qt.CustomContextMenu)
        # Event Log & Process output
        self.ui.textBrowser_eventlog.anchorClicked.connect(self.open_anchor)

    @Slot(name="init_project")
    def init_project(self):
        """Initializes project at application start-up. Loads the last project that was open
        when app was closed or starts without a project if app is started for the first time.
        """
        if not self._config.getboolean("settings", "open_previous_project"):
            return
        # Get path to previous project file from configuration file
        project_file_path = self._config.get("settings", "previous_project")
        if not project_file_path:
            return
        if not os.path.isfile(project_file_path):
            msg = "Could not load previous project. File '{0}' not found.".format(project_file_path)
            self.ui.statusbar.showMessage(msg, 10000)
            return
        self.msg.emit("Loading project from previous session")
        if not self.open_project(project_file_path):
            self.msg_error.emit("Loading project file <b>{0}</b> failed".format(project_file_path))
            logging.error("Loading project file '{0}' failed".format(project_file_path))
        return

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("mainWindow/windowSize")
        window_pos = self.qsettings.value("mainWindow/windowPosition")
        window_state = self.qsettings.value("mainWindow/windowState")
        window_maximized = self.qsettings.value("mainWindow/windowMaximized", defaultValue='false')  # returns string
        splitter_state = self.qsettings.value("mainWindow/splitterState")
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)

    # noinspection PyMethodMayBeStatic
    def init_models(self, tool_template_paths):
        """Initialize application internal data models.

        Args:
            tool_template_paths (list): List of tool definition file paths used in this project
        """
        self.project_item_model = QStandardItemModel()
        self.project_item_model.setHorizontalHeaderItem(0, QStandardItem("Contents"))
        self.project_item_model.appendRow(QStandardItem("Data Stores"))
        self.project_item_model.appendRow(QStandardItem("Data Connections"))
        self.project_item_model.appendRow(QStandardItem("Tools"))
        self.project_item_model.appendRow(QStandardItem("Views"))
        self.ui.treeView_project.setModel(self.project_item_model)
        self.ui.graphicsView.setProjectItemModel(self.project_item_model)
        self.init_tool_template_model(tool_template_paths)
        self.init_connection_model()

    def init_tool_template_model(self, tool_template_paths):
        """Initializes Tool template model.

        Args:
            tool_template_paths (list): List of tool definition file paths used in this project
        """
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
            self.msg.emit("Tool template <b>{0}</b> ready".format(tool_cand.name))
        # Set ToolTemplateModel to available Tools view
        self.ui.listView_tool_templates.setModel(self.tool_template_model)
        # Note: If ToolTemplateModel signals are in use, they should be reconnected here.
        # Reconnect ToolTemplateModel and QListView signals. Make sure that signals are connected only once.
        # doubleClicked signal
        n_recv = self.ui.listView_tool_templates.receivers(SIGNAL("doubleClicked(QModelIndex)"))  # nr of receivers
        if n_recv == 0:
            # logging.debug("Connecting doubleClicked signal for QListView")
            self.ui.listView_tool_templates.doubleClicked.connect(self.edit_tool_template)
        elif n_recv > 1:
            # Check that this never gets over 1
            logging.error("Number of receivers for QListView doubleClicked signal is now:{0}".format(n_recv))
        else:
            pass  # signal already connected
        # customContextMenuRequested signal. Get n of receivers for this signal
        n_recv = self.ui.listView_tool_templates.receivers(SIGNAL("customContextMenuRequested(QPoint)"))
        if n_recv == 0:
            # slogging.debug("Connecting customContextMenuRequested signal for QListView")
            self.ui.listView_tool_templates.customContextMenuRequested.connect(self.show_tool_template_context_menu)
        elif n_recv > 1:
            # Check that this never gets over 1
            logging.error("Number of receivers for QListView customContextMenuRequested signal is now:{0}"
                          .format(n_recv))
        else:
            pass  # signal already connected
        if n_tools == 0:
            self.msg_warning.emit("Project has no tool templates")

    def init_connection_model(self):
        """Initializes a model representing connections between project items."""
        self.connection_model = ConnectionModel(self)
        self.ui.tableView_connections.setModel(self.connection_model)
        self.ui.graphicsView.setConnectionModel(self.connection_model)
        # Reconnect ConnectionModel and QTableView. Make sure that signals are connected only once.
        n_connected = self.ui.tableView_connections.receivers(SIGNAL("clicked(QModelIndex)"))  # nr of receivers
        if n_connected == 0:
            # logging.debug("Connecting clicked signal for QTableView")
            self.ui.tableView_connections.clicked.connect(self.connection_clicked)
        elif n_connected > 1:
            # Check that this never gets over 1
            logging.error("Number of receivers for tableView_connections clicked signal is now:{0}".format(n_connected))
        else:
            pass  # signal already connected

    @Slot("QModelIndex", name="connection_clicked")
    def connection_clicked(self, index):
        """Toggle boolean value in the connection model.

        Args:
            index (QModelIndex): Clicked index
        """
        if not index.isValid():
            return
        # logging.debug("index {0}:{1} clicked".format(index.row(), index.column()))
        self.connection_model.setData(index, "value", Qt.EditRole)  # value not used

    def clear_ui(self):
        """Clean UI to make room for a new or opened project."""
        item_names = self.return_item_names()
        n = len(item_names)
        if n == 0:
            return
        # Clear widget info from QDockWidget
        self.clear_info_area()
        for name in item_names:
            ind = self.find_item(name, Qt.MatchExactly | Qt.MatchRecursive).index()
            self.remove_item(ind)
        self._project = None
        self.tool_template_model = None
        self.msg.emit("All {0} items removed from project".format(n))

    @Slot(name="new_project")
    def new_project(self):
        """Create new project and activate it."""
        self.project_form = NewProjectForm(self, self._config)
        self.project_form.show()

    def create_project(self, name, description):
        """Create new project and set it active.

        Args:
            name (str): Project name
            description (str): Project description
        """
        self.clear_ui()
        self._project = None
        self._project = SpineToolboxProject(self, name, description, self._config, ext='.proj')
        self.init_models(tool_template_paths=list())  # Start project with no tool templates
        self.setWindowTitle("Spine Toolbox    -- {} --".format(self._project.name))
        self.ui.textBrowser_eventlog.clear()
        self.msg.emit("New project created")
        self.save_project()

    @Slot(name="open_project")
    def open_project(self, load_path=None):
        """Load project from a save file (.proj) file.

        Args:
            load_path (str): If not None, this method is used to load the
            previously opened project at start-up
        """
        tool_template_paths = list()
        connections = list()
        if not load_path:
            # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
            func = blocking_updates(self.ui.graphicsView, QFileDialog.getOpenFileName)
            answer = func(self, 'Open project', project_dir(self._config), 'Projects (*.proj)')
            load_path = answer[0]
            if load_path == '':  # Cancel button clicked
                return False
        if not os.path.isfile(load_path):
            self.msg_error.emit("File <b>{0}</b> not found".format(load_path))
            logging.debug("File not found: {0}".format(load_path))
            return False
        if not load_path.lower().endswith('.proj'):
            logging.debug("File name has unsupported extension. Only .proj files supported")
            return False
        # Load project from JSON file
        try:
            with open(load_path, 'r') as fh:
                try:
                    dicts = json.load(fh)
                except json.decoder.JSONDecodeError:
                    logging.exception("Failed to load file:{0}".format(load_path))
                    return False
        except OSError:
            logging.exception("Could not load project from file {0}".format(load_path))
            return False
        # Initialize UI
        self.clear_ui()
        # Parse project info
        project_dict = dicts['project']
        proj_name = project_dict['name']
        proj_desc = project_dict['description']
        try:
            tool_template_paths = project_dict['tool_templates']
        except KeyError:
            self.msg_warning.emit("Tool templates not found in project file")
        try:
            connections = project_dict['connections']
        except KeyError:
            self.msg_warning.emit("No connections found in project file")
        try:
            x = project_dict['scene_x']
            y = project_dict['scene_y']
            w = project_dict['scene_w']
            h = project_dict['scene_h']
        except KeyError:
            pass
        # self.ui.graphicsView.reset_scene()
        # self.ui.graphicsView.setSceneRect(QRectF())  # TODO: This should setSceneRect to 0 but does nothing
        # Create project
        self._project = SpineToolboxProject(self, proj_name, proj_desc, self._config)
        # Init models and views
        self.setWindowTitle("Spine Toolbox    -- {} --".format(self._project.name))
        # Populate project model with items read from JSON file
        self.init_models(tool_template_paths)
        if not self._project.load(dicts['objects']):
            self.msg_error.emit("Loading project items failed")
            return False
        self.ui.treeView_project.expandAll()
        # Restore connections
        self.msg.emit("Restoring connections...")
        self.connection_model.reset_model(connections)
        self.msg.emit("Project <b>{0}</b> is now open".format(self._project.name))
        return True

    @Slot(name="save_project")
    def save_project(self):
        """Save project."""
        if not self._project:
            self.msg.emit("No project open")
            return
        # Put project's tool template definition files into a list
        tool_templates = list()
        for i in range(self.tool_template_model.rowCount()):
            if i > 0:
                tool_templates.append(self.tool_template_model.tool_template(i).get_def_path())
        self._project.save(tool_templates)
        self.msg.emit("Project saved to <b>{0}</b>".format(self._project.path))

    @Slot(name="save_project_as")
    def save_project_as(self):
        """Save current project on a new name and activate it."""
        # noinspection PyCallByClass
        func = blocking_updates(self.ui.graphicsView, QFileDialog.getSaveFileName)
        dir_path = func(self, 'Save project', project_dir(self._config), 'Project (*.proj)')
        file_path = dir_path[0]
        if file_path == '':  # Cancel button clicked
            return
        file_name = os.path.split(file_path)[-1]
        if not file_name.lower().endswith('.proj'):
            self.msg_warning.emit("Only *.proj files supported")
            logging.debug("Only *.proj files supported")
            return
        if not self._project:
            self.new_project()
        else:
            # Update project file name
            self._project.change_filename(file_name)
            # TODO: Make a new project with the given name and switch references of all items for the new project.
            # Save open project into new file
            self.save_project()
        return

    @Slot("QModelIndex", name="select_item_and_show_info")
    def select_item_and_show_info(self, index):
        """Set item selected in scene and show item info in QDockWidget.

        Args:
            index (QModelIndex): Index of clicked item, if available
        """
        if not index:
            return
        if not index.isValid():
            logging.error("Index not valid")
            return
        else:
            if index.parent().isValid():
                item = self.project_item_model.itemFromIndex(index)
                if not item:
                    logging.error("Item not found")
                    return
                item_data = item.data(Qt.UserRole)  # This is e.g. DataStore object
                # Clear previous selection
                self.ui.graphicsView.scene().clearSelection()
                # Set item icon on scene selected.
                icon = item_data.get_icon()
                # Select master icon and all of its children are selected as well
                icon.master().setSelected(True)
                self.show_info(item_data.name)
            return

    # @Slot("QModelIndex", name="show_subwindow")
    # def show_subwindow(self, index):
    #     """Show double-clicked item subwindow if it was hidden.
    #     Sets both QMdiSubWindow and its internal widget visible.
    #
    #     Args:
    #         index (QModelIndex): Index of clicked item, if available
    #     """
    #     if not index:
    #         return
    #     if not index.isValid():
    #         logging.error("Index not valid")
    #         return
    #     else:
    #         if index.parent().isValid():
    #             item_data = self.project_item_model.itemFromIndex(index).data(Qt.UserRole)  # e.g. DataStore object
    #             internal_widget = item_data.get_widget()  # QWidget of e.g. DataStore object
    #             internal_widget.show()
    #         return

    @Slot(name="test1")
    def test1(self):
        sub_windows = self.ui.graphicsView.subWindowList()
        self.msg.emit("Number of subwindows: {0}".format(len(sub_windows)))
        logging.debug("Total number of items: {0}".format(self.n_items("all")))
        logging.debug("Number of Data Stores: {0}".format(self.n_items("Data Stores")))
        logging.debug("Number of Data Connections: {0}".format(self.n_items("Data Connections")))
        logging.debug("Number of Tools: {0}".format(self.n_items("Tools")))
        logging.debug("Number of Views: {0}".format(self.n_items("Views")))
        top_level_items = self.project_item_model.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            # logging.debug("Children of {0}".format(top_level_item.data(Qt.DisplayRole)))
            if top_level_item.hasChildren():
                n_children = top_level_item.rowCount()
                for i in range(n_children):
                    child = top_level_item.child(i, 0)
                    self.msg.emit("{0}".format(child.data(Qt.DisplayRole)))

    @Slot(name="test2")
    def test2(self):
        logging.debug("Items on scene:{0}".format(len(self.ui.graphicsView.scene().items())))
        # for item in self.ui.graphicsView.scene().items():
        #     logging.debug(item)
        scene_size = self.ui.graphicsView.scene().sceneRect()
        logging.debug("sceneRect:{0}".format(scene_size))
        mouse_item = self.ui.graphicsView.scene().mouseGrabberItem()
        # logging.debug("mouse grabber item:{0}".format(mouse_item))
        # self.ui.graphicsView.scene().addItem(self.dc)
        return
        # for subwindow in self.ui.graphicsView.subWindowList():
        #     w = subwindow.widget()  # SubWindowWidget
        #     w_type = w.objectName()  # Tool, Data Store, Data Connection, or View
        #     # w_parent = w.parent()  # QMdiSubWindow == subwindow
        #     # w_owner = w.owner()  # item name
        #     if w_type == "Tool":
        #         self.msg.emit("Found Tool {0}".format(w.owner()))
        #         # Find item in project model
        #         size_hint = subwindow.sizeHint()
        #         min_size = subwindow.minimumSize()
        #         min_size_hint = subwindow.minimumSizeHint()
        #         size_policy = subwindow.sizePolicy()
        #         logging.debug("sizeHint:{0} minSize:{1} minSizeHint:{2} sizePolicy:{3}"
        #                       .format(size_hint, min_size, min_size_hint, size_policy))
        #         item = self.find_item(w.owner(), Qt.MatchExactly | Qt.MatchRecursive)  # QStandardItem
        #         tool = item.data(Qt.UserRole)  # Tool instance that is saved into QStandardItem data
        #         if tool.tool_template() is not None:
        #             self.msg.emit("Tool template of this Tool:{0}".format(tool.tool_template().name))

    def show_info(self, name):
        """Show information of selected item. Embed old item widgets into QDockWidget."""
        item = self.find_item(name, Qt.MatchExactly | Qt.MatchRecursive)  # Find item from project model
        if not item:
            logging.error("Item {0} not found".format(name))
            return
        item_data = item.data(Qt.UserRole)
        # Clear QGroupBox layout
        self.clear_info_area()
        # Add new item into layout
        self.ui.groupBox_subwindow.layout().addWidget(item_data.get_widget())
        # If Data Connection, refresh data files
        if item_data.item_type == "Data Connection" or item_data.item_type == "Data Store":
            item_data.refresh()

    def clear_info_area(self):
        """Clear SubWindowArea QDockWidget."""
        layout = self.ui.groupBox_subwindow.layout()
        for i in reversed(range(layout.count())):
            widget_to_remove = layout.itemAt(i).widget()
            # Remove it from the layout list
            layout.removeWidget(widget_to_remove)
            # Remove it from the gui
            widget_to_remove.setParent(None)

    # @Slot("QMdiSubWindow", name="update_details_frame")
    # def update_details_frame(self, window):
    #     """OBSOLETE: Update labels on main window according to the currently selected QMdiSubWindow.
    #
    #     Args:
    #         window (QMdiSubWindow): Active sub-window
    #     """
    #     if window is not None:
    #         w = window.widget()  # SubWindowWidget
    #         obj_type = w.objectName()
    #         name = w.owner()
    #         # self.ui.lineEdit_type.setText(obj_type)
    #         # self.ui.lineEdit_name.setText(name)
    #         # Find object data from model. Note: Finds child items only if Qt.MatchRecursive is set.
    #         selected_item = self.find_item(name, Qt.MatchExactly | Qt.MatchRecursive)
    #         if not selected_item:
    #             logging.error("Item {0} not found".format(name))
    #             return
    #         item_data = selected_item.data(Qt.UserRole)
    #         if item_data.item_type == "Data Connection":
    #             # logging.debug("DC selected")
    #             item_data.refresh()
    #         # matching_item_data = selected_item.data(Qt.UserRole)
    #     else:
    #         pass
    #         # self.ui.lineEdit_type.setText("")
    #         # self.ui.lineEdit_name.setText("")

    @Slot(name="open_tool_template")
    def open_tool_template(self):
        """Open a file dialog so that the user can select an existant tool template .json file.
        Continue loading the tool template into the Project if succesfull.
        """
        if not self._project:
            self.msg.emit("No project open")
            return
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        func = blocking_updates(self.ui.graphicsView, QFileDialog.getOpenFileName)
        answer = func(self, 'Select tool template file',
                      os.path.join(project_dir(self._config), os.path.pardir),
                      'JSON (*.json)')
        if answer[0] == '':  # Cancel button clicked
            return
        def_file = os.path.abspath(answer[0])
        # Load tool definition
        tool = self._project.load_tool_template_from_file(def_file)
        if not tool:
            self.msg_error.emit("Adding Tool template failed".format(def_file))
            return
        if self.tool_template_model.find_tool_template(tool.name):
            # Tool template already added to project
            self.msg_warning.emit("Tool template <b>{0}</b> already in project".format(tool.name))
            return
        # Add definition file path into tool
        tool.set_def_path(def_file)
        self.add_tool_template(tool)

    def add_tool_template(self, tool):
        """Add a ToolTemplate instance to project, which then can be added to a Tool item."""
        # Get definition file path
        def_file = tool.get_def_path()
        # Insert tool into model
        self.tool_template_model.insertRow(tool)
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
                logging.debug("Adding tool_templates keyword to project file")
                project_dict['tool_templates'] = [def_file]
            # Save dictionaries back to project save file
            dicts['project'] = project_dict
            dicts['objects'] = objects_dict
            with open(project_file, 'w') as fp:
                json.dump(dicts, fp, indent=4)
            self.msg_success.emit("Tool template <b>{0}</b> added to project".format(tool.name))
        else:
            self.msg_error.emit("Unsupported project filename {0}. Extension should be .proj.".format(project_file))
            return

    def update_tool_template(self, row, tool):
        """Update a ToolTemplate instance in the project.
        """
        # Insert tool into model
        index = self.tool_template_model.createIndex(row, 0)
        self.tool_template_model.removeRow(row)
        self.tool_template_model.insertRow(tool, row)
        self.msg_success.emit("Tool template <b>{0}</b> updated".format(tool.name))
        # Reattach Tool template to any Tools that use it
        logging.debug("Reattaching tool template {}".format(tool.name))
        self.reattach_tool_templates(tool.name)

    @Slot(name="refresh_tool_templates")
    def refresh_tool_templates(self):
        """If user has changed a Tool template while the application is running,
        this method refreshes all Tools that use this template to reflect the changes."""
        if not self._project:
            self.msg.emit("No project open")
            return
        self.msg.emit("Refreshing Tool templates")
        # Re-open project
        project_file = self._project.path  # Path to project file
        if project_file.lower().endswith(".proj"):
            try:
                with open(project_file, 'r') as fh:
                    dicts = json.load(fh)
            except OSError:
                self.msg_error.emit("OSError: Could not load file <b>{0}</b>".format(project_file))
                return
            # Get project settings
            project_dict = dicts['project']
            try:
                tool_template_paths = project_dict['tool_templates']
            except KeyError:
                logging.debug("tool_templates keyword not found in project file")
                self.msg_warning.emit("No Tool templates in project")
                return
            self.init_tool_template_model(tool_template_paths)
            # Reattach all Tool templates because ToolTemplateModel may have changed
            self.reattach_tool_templates()
        else:
            self.msg_error.emit("Unsupported project filename {0}. Extension should be .proj.".format(project_file))
            return

    def reattach_tool_templates(self, tool_template_name=None):
        """Reattach tool templates that may have changed.

        Args:
        tool_template_name (str): if None, reattach all tool templates in project.
            If a name is given, only reattach that one
        """
        for subwindow in self.ui.graphicsView.subWindowList():
            w = subwindow.widget()  # SubWindowWidget
            w_type = w.objectName()  # Tool, Data Store, Data Connection, or View
            if w_type == "Tool":
                # Find item in project model
                item = self.find_item(w.owner(), Qt.MatchExactly | Qt.MatchRecursive)  # QStandardItem
                tool = item.data(Qt.UserRole)  # Tool that is saved into QStandardItem data
                if tool.tool_template() is not None:
                    # Get old tool template name
                    old_t_name = tool.tool_template().name
                    if not tool_template_name or old_t_name == tool_template_name:
                        # Find the same tool template from ToolTemplateModel
                        new_template = self.tool_template_model.find_tool_template(old_t_name)
                        if not new_template:
                            self.msg_error.emit("Could not find Tool template <b>{0}</b>".format(old_t_name))
                            tool.set_tool_template(None)
                            continue
                        tool.set_tool_template(new_template)
                        self.msg.emit("Template <b>{0}</b> reattached to Tool <b>{1}</b>"
                                      .format(new_template.name, tool.name))

    @Slot(name="remove_selected_tool_template")
    def remove_selected_tool_template(self):
        """Prepare to remove tool template selected in QListView."""
        if not self._project:
            self.msg.emit("No project open")
            return
        try:
            index = self.ui.listView_tool_templates.selectedIndexes()[0]
        except IndexError:
            # Nothing selected
            self.msg.emit("Select a Tool template to remove")
            return
        if not index.isValid():
            return
        if index.row() == 0:
            # Do not remove No Tool option
            self.msg.emit("<b>No Tool</b> cannot be removed")
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
        msg = "Removing Tool template <b>{0}</b>. Are you sure?".format(sel_tool.name)
        # noinspection PyCallByClass, PyTypeChecker
        answer = QMessageBox.question(self, 'Remove Tool template', msg, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            return
        self.msg.emit("Removing Tool template <b>{0}</b> -> <b>{1}</b>".format(sel_tool.name, tool_def_path))
        # Remove tool def file path from the project file (only JSON supported)
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
            self.msg_error.emit("Error in removing Tool <b>{0}</b>".format(sel_tool.name))
            return
        try:
            tools = project_dict['tool_templates']
            tools.remove(tool_def_path)
            # logging.debug("tools list after removal:{}".format(tools))
            project_dict['tool_templates'] = tools
        except KeyError:
            self.msg_error.emit("This is odd. tool_templates list not found in project file <b>{0}</b>"
                                .format(project_file))
            return
        except ValueError:
            self.msg_error.emit("This is odd. Tool definition file path <b>{0}</b> not found "
                                "in project file <b>{1}</b>".format(tool_def_path, project_file))
            return
        # Save dictionaries back to JSON file
        dicts['project'] = project_dict
        dicts['objects'] = object_dict
        with open(project_file, 'w') as fp:
            json.dump(dicts, fp, indent=4)
        # Remove tool template also from Tools that use it
        for subwindow in self.ui.graphicsView.subWindowList():
            w = subwindow.widget()  # SubWindowWidget
            w_type = w.objectName()  # Tool, Data Store, Data Connection, or View
            if w_type == "Tool":
                # Find item in project model
                item = self.find_item(w.owner(), Qt.MatchExactly | Qt.MatchRecursive)  # QStandardItem
                tool = item.data(Qt.UserRole)  # Tool instance that is saved into QStandardItem data
                if tool.tool_template() is not None:
                    if tool.tool_template().name == sel_tool.name:
                        tool.set_tool_template(None)
                        self.msg.emit("Removed {0} from Tool <b>{1}</b>".format(sel_tool.name, tool.name))
        self.msg_success.emit("Tool template removed successfully")

    def add_item_to_model(self, category, text, data):
        """Add item to project model.

        Args:
            category (str): Project category (e.g. Data Stores)
            text (str): Display role for the new item
            data (QObject): Object that is added to model (e.g. DataStore())
        """
        # First, find QStandardItem category item where new child item is added
        found_items = self.project_item_model.findItems(category, Qt.MatchExactly, column=0)
        if not found_items:
            logging.error("'{0}' item not found in project item model".format(category))
            return False
        if len(found_items) > 1:
            logging.error("More than one '{0}' items found in project item model".format(category))
            return False
        item_index = found_items[0].index()
        parent_index = item_index.parent()
        if not parent_index.isValid():
            # Parent index is not valid if item has no parent
            new_item = QStandardItem(text)
            new_item.setData(data, role=Qt.UserRole)
            self.project_item_model.itemFromIndex(item_index).appendRow(new_item)
            # Get row and column number (i.e. index) for the connection model. This is to
            # keep the project item model and connection model synchronized.
            index = self.new_item_index(data.item_category)  # Get index according to item category
            self.connection_model.append_item(new_item, index)
            self.ui.treeView_project.expand(item_index)
        return True

    @Slot(name="remove_all_items")
    def remove_all_items(self):
        """Slot for Remove All button."""
        if not self._project:
            self.msg.emit("No items to remove")
            return
        msg = "Remove all items from project?"
        # noinspection PyCallByClass, PyTypeChecker
        answer = QMessageBox.question(self, 'Removing all items', msg, QMessageBox.Yes, QMessageBox.No)
        if not answer == QMessageBox.Yes:
            return
        item_names = self.return_item_names()
        n = len(item_names)
        if n == 0:
            return
        for name in item_names:
            ind = self.find_item(name, Qt.MatchExactly | Qt.MatchRecursive).index()
            self.remove_item(ind, delete_item=True)
        self.msg.emit("All {0} items removed from project".format(n))

    def remove_item(self, ind, delete_item=False):
        """Remove subwindow from project when it's index in the project model is known.
        To remove all items in project, loop all indices through this method.
        This method is used in both opening and creating a new project as
        well as when item(s) are deleted from project.
        Use delete_item=False when closing the project or creating a new one.
        Setting delete_item=True deletes the item irrevocably. This means that
        data directories will be deleted from the hard drive.

        Args:
            ind (QModelIndex): Index of removed item in project model
            delete_item: If set to True, deletes the directories and data associated with the item
        """
        name = ind.data(Qt.UserRole).get_widget().owner()
        item = self.find_item(name, Qt.MatchExactly | Qt.MatchRecursive)  # QStandardItem
        item_data = item.data(Qt.UserRole)  # Object that is contained in the QStandardItem (e.g. DataStore)
        data_dir = None
        if item_data.item_type == "Data Connection":
            data_dir = item_data.data_dir
        # Remove item icon (QGraphicsItems) from scene
        self.ui.graphicsView.scene().removeItem(item_data.get_icon().master())
        item_data.set_icon(None)
        # Remove item from connection model. This also removes Link QGraphicsItems associated to this item
        if not self.connection_model.remove_item(item):
            self.msg_error.emit("Removing item {0} from connection model failed".format(item_data.name))
        # Remove item from project model
        if not self.project_item_model.removeRow(ind.row(), ind.parent()):
            self.msg_error.emit("Removing item <b>{0}</b> from project failed".format(item_data.name))
        # Remove item data from reference list
        try:
            self.project_refs.remove(item_data)  # Note: remove() removes only the first occurrence in the list
        except ValueError:
            self.msg_error.emit("Item '{0}' not found in reference list".format(item_data))
            return
        if delete_item:
            if data_dir:
                # Remove data directory and all its contents
                self.msg.emit("Removing directory <b>{0}</b>".format(data_dir))
                try:
                    if not erase_dir(data_dir):
                        self.msg_error.emit("Directory does not exist")
                        return
                except OSError:
                    self.msg_error.emit("[OSError] Removing directory failed. Check directory permissions.")
                    return
        self.msg.emit("Item <b>{0}</b> removed from project".format(name))
        return

    def find_item(self, name, match_flags=Qt.MatchExactly):
        """Find item by name in project model (column 0)

        Args:
            name (str): Item name to find
            match_flags (QFlags): Or combination of Qt.MatchFlag types

        Returns:
            Matching QStandardItem or None if item not found or more than one item with the same name found.
        """
        found_items = self.project_item_model.findItems(name, match_flags, column=0)
        if len(found_items) == 0:
            # logging.debug("Item '{0}' not found in project model".format(name))
            return None
        if len(found_items) > 1:
            logging.error("More than one item with name '{0}' found".format(name))
            return None
        return found_items[0]

    def n_items(self, typ):
        """Returns the number of items in the project according to type.

        Args:
            typ (str): Type of item to count. "all" returns the number of items in project.
        """
        n = 0
        if not self.project_item_model:
            return n
        top_level_items = self.project_item_model.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            if typ == "all":
                if top_level_item.hasChildren():
                    n = n + top_level_item.rowCount()
            elif typ == "Data Stores":
                if top_level_item.data(Qt.DisplayRole) == "Data Stores":
                    n = top_level_item.rowCount()
            elif typ == "Data Connections":
                if top_level_item.data(Qt.DisplayRole) == "Data Connections":
                    n = top_level_item.rowCount()
            elif typ == "Tools":
                if top_level_item.data(Qt.DisplayRole) == "Tools":
                    n = top_level_item.rowCount()
            elif typ == "Views":
                if top_level_item.data(Qt.DisplayRole) == "Views":
                    n = top_level_item.rowCount()
            else:
                logging.error("Unknown type: {0}".format(typ))
        return n

    def new_item_index(self, category):
        """Get index where a new item is appended according to category."""
        if category == "Data Stores":
            # Return number of data stores
            return self.n_items("Data Stores") - 1
        elif category == "Data Connections":
            # Return number of data stores + data connections - 1
            return self.n_items("Data Stores") + self.n_items("Data Connections") - 1
        elif category == "Tools":
            # Return number of data stores + data connections + tools - 1
            return self.n_items("Data Stores") + self.n_items("Data Connections") + self.n_items("Tools") - 1
        elif category == "Views":
            # Return total number of items - 1
            return self.n_items("all") - 1
        else:
            logging.error("Unknown category:{0}".format(category))
            return 0

    def return_item_names(self):
        """Returns the names of all items in a list."""
        item_names = list()
        if not self.project_item_model:
            return item_names
        top_level_items = self.project_item_model.findItems('*', Qt.MatchWildcard, column=0)
        for top_level_item in top_level_items:
            if top_level_item.hasChildren():
                n_children = top_level_item.rowCount()
                for i in range(n_children):
                    child = top_level_item.child(i, 0)
                    item_names.append(child.data(Qt.DisplayRole))
        return item_names

    @Slot("QUrl", name="open_anchor")
    def open_anchor(self, qurl):
        """Open file explorer in the directory given in qurl.

        Args:
            qurl (QUrl): Directory path or a file to open
        """
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
        if index.row() == 0:
            return  # Don't do anything if No Tool option is double-clicked
        tool_template = self.tool_template_model.tool_template(index.row())

        # Show the template in the Tool Template Form
        self.show_tool_template_form(tool_template)

    @Slot("QModelIndex", name='open_tool_template_file')
    def open_tool_template_file(self, index):
        """Open the Tool template definition file in the default (.json) text-editor.

        Args:
            index (QModelIndex): Index of the item
        """
        tool_template = self.tool_template_model.tool_template(index.row())
        file_path = tool_template.def_file_path
        # Check if file exists first. openUrl may return True if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            logging.error("Failed to open editor for {0}".format(file_path))
            self.msg_error.emit("Tool definition file <b>{0}</b> not found."
                                .format(file_path))
            return
        tool_template_url = "file:///" + file_path
        # Open Tool template definition file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(tool_template_url, QUrl.TolerantMode))
        logging.debug(res)
        if not res:
            logging.error("Failed to open editor for {0}".format(tool_template_url))
            self.msg_error.emit("Unable to open Tool template file {0}. Make sure that <b>.json</b> "
                                "files are associated with a text editor. For example on Windows "
                                "10, go to Control Panel -> Default Programs to do this."
                                .format(file_path))
        return

    @Slot("QModelIndex", name='open_tool_main_program_file')
    def open_tool_main_program_file(self, index):
        """Open the tool template's main program file in the default editor.

        Args:
            index (QModelIndex): Index of the item
        """
        tool = self.tool_template_model.tool_template(index.row())
        file_path = os.path.join(tool.path, tool.includes[0])
        # Check if file exists first. openUrl may return True if file doesn't exist
        # TODO: this could still fail if the file is deleted or renamed right after the check
        if not os.path.isfile(file_path):
            logging.error("Failed to open editor for {0}".format(file_path))
            self.msg_error.emit("Tool main program file <b>{0}</b> not found."
                                .format(file_path))
            return
        main_program_url = "file:///" + file_path
        # Open Tool template main program file in editor
        # noinspection PyTypeChecker, PyCallByClass, PyArgumentList
        res = QDesktopServices.openUrl(QUrl(main_program_url, QUrl.TolerantMode))
        if not res:
            logging.error("Failed to open editor for {0}".format(main_program_url))
            filename, file_extension = os.path.splitext(file_path)
            self.msg_error.emit("Unable to open Tool template main program file {0}. "
                                "Make sure that <b>{1}</b> "
                                "files are associated with an editor. For example on Windows "
                                "10, go to Control Panel -> Default Programs to do this."
                                .format(filename, file_extension))
        return

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to Event Log.

        Args:
            msg (str): String written to QTextBrowser
        """
        open_tag = "<span style='color:white;white-space: pre-wrap;'>"
        date_str = get_datetime(self._config)
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
        date_str = get_datetime(self._config)
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
        date_str = get_datetime(self._config)
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
        date_str = get_datetime(self._config)
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

    @Slot(name="show_add_data_store_form")
    def show_add_data_store_form(self):
        """Show add data store widget."""
        if not self._project:
            self.msg.emit("Create or open a project first")
            return
        self.add_data_store_form = AddDataStoreWidget(self, self._project)
        self.add_data_store_form.show()

    @Slot(name="show_add_data_connection_form")
    def show_add_data_connection_form(self):
        """Show add data connection widget."""
        if not self._project:
            self.msg.emit("Create or open a project first")
            return
        self.add_data_connection_form = AddDataConnectionWidget(self, self._project)
        self.add_data_connection_form.show()

    @Slot(name="show_add_tool_form")
    def show_add_tool_form(self):
        """Show add tool widget."""
        if not self._project:
            self.msg.emit("Create or open a project first")
            return
        self.add_tool_form = AddToolWidget(self, self._project)
        self.add_tool_form.show()

    @Slot(name="show_add_view_form")
    def show_add_view_form(self):
        """Show add view widget."""
        if not self._project:
            self.msg.emit("Create or open a project first")
            return
        self.add_view_form = AddViewWidget(self, self._project)
        self.add_view_form.show()

    @Slot(name="show_tool_template_form")
    def show_tool_template_form(self, tool_template=None):
        """Show create tool template widget."""
        if not self._project:
            self.msg.emit("Create or open a project first")
            return
        self.tool_template_form = ToolTemplateWidget(self, self._project, tool_template)
        self.tool_template_form.show()

    @Slot(name="show_settings")
    def show_settings(self):
        """Show Settings widget."""
        self.settings_form = SettingsWidget(self, self._config, self._project)
        self.settings_form.show()

    @Slot(name="show_about")
    def show_about(self):
        """Show About Spine Toolbox form."""
        self.about_form = AboutWidget(self, SPINE_TOOLBOX_VERSION)
        self.about_form.show()

    @Slot(name="open_data_store_view")
    def open_data_store_view(self):
        self.data_store_form = DataStoreWidget(self)
        self.data_store_form.show()

    @Slot("QPoint", name="show_item_context_menu")
    def show_item_context_menu(self, pos):
        """Context menu for project items.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.treeView_project.indexAt(pos)
        global_pos = self.ui.treeView_project.viewport().mapToGlobal(pos)
        self.project_item_context_menu = ProjectItemContextMenu(self, global_pos, ind)
        option = self.project_item_context_menu.get_action()
        if option == "Remove Item":
            self.remove_item(ind, delete_item=True)
            return
        else:  # No option selected
            pass
        self.project_item_context_menu.deleteLater()
        self.project_item_context_menu = None

    @Slot("QPoint", name="show_tool_template_context_menu")
    def show_tool_template_context_menu(self, pos):
        """Context menu for tool templates.

        Args:
            pos (QPoint): Mouse position
        """
        ind = self.ui.listView_tool_templates.indexAt(pos)
        global_pos = self.ui.listView_tool_templates.viewport().mapToGlobal(pos)
        self.tool_template_context_menu = ToolTemplateContextMenu(self, global_pos, ind)
        option = self.tool_template_context_menu.get_action()
        if option == "Open":
            self.edit_tool_template(ind)
        elif option == "Open in external editor":
            self.open_tool_template_file(ind)
        elif option == "Open main program":
            self.open_tool_main_program_file(ind)
        elif option == "Remove":
            self.remove_tool_template(ind)
        else:  # No option selected
            pass
        self.tool_template_context_menu.deleteLater()
        self.tool_template_context_menu = None

    def show_item_image_context_menu(self, pos, item_name):
        """Context menu for item images.

        Args:
            pos (QPoint): Mouse position
            item_name (QGraphicsItem): The name of the concerned item
        """
        logging.debug(item_name)

    def show_link_context_menu(self, pos, src_item_name, dst_item_name):
        """Context menu for connection links.

        Args:
            pos (QPoint): Mouse position
            src_item_name (QGraphicsItem): The item this link originates from
            dst_item_name (QGraphicsItem): The item this link lands on
        """
        row = self.connection_model.header.index(src_item_name)
        column = self.connection_model.header.index(dst_item_name)
        ind = self.connection_model.index(row, column)
        self.link_context_menu = LinkContextMenu(self, pos, ind)
        option = self.link_context_menu.get_action()
        if option == "Remove":
            self.connection_clicked(ind)
            return
        else:  # No option selected
            pass
        self.link_context_menu.deleteLater()
        self.link_context_menu = None

    def show_confirm_exit(self):
        """Shows confirm exit message box.

        Returns:
            True if user clicks Yes or False if exit is cancelled
        """
        ex = self._config.getboolean("settings", "show_exit_prompt")
        if ex:
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
                    show_prompt = True
                else:
                    show_prompt = False
                self._config.setboolean("settings", "show_exit_prompt", show_prompt)
                return True
            else:
                return False
        return True

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
        logging.debug("Bye bye")
        # Save current project (if enabled in settings)
        if not self._project:
            self._config.set("settings", "previous_project", "")
        else:
            self._config.set("settings", "previous_project", self._project.path)
        self._config.save()
        self.qsettings.setValue("mainWindow/splitterState", self.ui.splitter.saveState())
        self.qsettings.setValue("mainWindow/windowSize", self.size())
        self.qsettings.setValue("mainWindow/windowPosition", self.pos())
        self.qsettings.setValue("mainWindow/windowState", self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("mainWindow/windowMaximized", True)
        else:
            self.qsettings.setValue("mainWindow/windowMaximized", False)
        if event:
            event.accept()
        # noinspection PyArgumentList
        QApplication.quit()
