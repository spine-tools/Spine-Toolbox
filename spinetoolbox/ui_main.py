#############################################################################
# Copyright (C) 2016 - 2017 VTT Technical Research Centre of Finland
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
Module for main application GUI functions.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   14.12.2017
"""

import locale
import logging
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QMainWindow, QApplication
from PySide2.QtGui import QStandardItemModel, QStandardItem
from ui.mainwindow import Ui_MainWindow
from widgets.data_store_widget import DataStoreWidget
from widgets.about_widget import AboutWidget
from data_store import DataStore
from data_connection import DataConnection
from tool import Tool
from view import View
from config import SPINE_TOOLBOX_VERSION


class ToolboxUI(QMainWindow):
    """Class for application main GUI functions."""
    def __init__(self):
        """ Initialize application and main window."""
        super().__init__(flags=Qt.Window)
        # Set number formatting to use user's default settings
        locale.setlocale(locale.LC_NUMERIC, '')
        # Setup the user interface from Qt Designer files
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.about_form = None
        self.data_store_form = None
        self.project_item_model = self.init_models()
        self.data_store_list = list()  # TODO: Find out why these are needed in addition with project_item_model refs.
        self.data_connection_list = list()
        self.tool_list = list()
        self.view_list = list()
        self.ui.treeView_project.setModel(self.project_item_model)
        self.ds_n = 0
        self.dc_n = 0
        self.tool_n = 0
        self.view_n = 0
        self.connect_signals()

    def connect_signals(self):
        """Connect signals."""
        # Menu commands
        self.ui.actionQuit.triggered.connect(self.closeEvent)
        self.ui.actionData_Store.triggered.connect(self.open_data_store_view)
        self.ui.actionAdd_Data_Store.triggered.connect(self.add_data_store)
        self.ui.actionAdd_Data_Connection.triggered.connect(self.add_data_connection)
        self.ui.actionAdd_Tool.triggered.connect(self.add_tool)
        self.ui.actionAdd_View.triggered.connect(self.add_view)
        self.ui.actionAbout.triggered.connect(self.show_about)
        # Buttons
        self.ui.pushButton_add_data_store.clicked.connect(self.add_data_store)
        self.ui.pushButton_add_data_connection.clicked.connect(self.add_data_connection)
        self.ui.pushButton_add_tool.clicked.connect(self.add_tool)
        self.ui.pushButton_add_view.clicked.connect(self.add_view)
        self.ui.pushButton_test1.clicked.connect(self.test1)
        self.ui.pushButton_test2.clicked.connect(self.test2)
        # QMdiArea
        self.ui.mdiArea.subWindowActivated.connect(self.update_details_frame)
        # Project TreeView
        self.ui.treeView_project.clicked.connect(self.activate_subwindow)
        self.ui.treeView_project.doubleClicked.connect(self.show_subwindow)

    @Slot("QModelIndex", name="activate_subwindow")
    def activate_subwindow(self, index):
        """Set focus on selected subwindow.

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
                item_data = item.data(Qt.UserRole)  # This is e.g. DataStore object
                item_widget = item_data.get_widget()
                item_subwindow = item_widget.parent()  # QMdiSubWindow that has item_widget as its internal widget
                self.ui.mdiArea.setActiveSubWindow(item_subwindow)
            return

    @Slot("QModelIndex", name="show_subwindow")
    def show_subwindow(self, index):
        """Show double-clicked item subwindow if it was hidden.
        Sets both QMdiSubWindow and its internal widget visible.

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
                item_data = self.project_item_model.itemFromIndex(index).data(Qt.UserRole)  # e.g. DataStore object
                internal_widget = item_data.get_widget()  # QWidget of e.g. DataStore object
                subwindow = internal_widget.parent()  # QMdiSubWindow that has internal_widget as its widget
                subwindow.show()
                internal_widget.show()
            return

    def init_models(self):
        """Initialize Qt data model for project contents."""
        m = QStandardItemModel()
        m.setHorizontalHeaderItem(0, QStandardItem("Contents"))
        m.appendRow(QStandardItem("Data Stores"))
        m.appendRow(QStandardItem("Data Connections"))
        m.appendRow(QStandardItem("Tools"))
        m.appendRow(QStandardItem("Views"))
        return m

    @Slot(name="open_data_store_view")
    def open_data_store_view(self):
        self.data_store_form = DataStoreWidget(self)
        self.data_store_form.show()

    @Slot(name="test1")
    def test1(self):
        sub_windows = self.ui.mdiArea.subWindowList()
        logging.debug("Number of subwindows:{0}".format(len(sub_windows)))

    @Slot(name="test2")
    def test2(self):
        current_sub_window = self.ui.mdiArea.currentSubWindow()
        if not current_sub_window:
            return
        widget_name = current_sub_window.widget().name_label_txt()
        par = current_sub_window.widget().parent()
        logging.debug("Parent of {0}:{1}".format(widget_name, par))

    @Slot("QMdiSubWindow", name="update_details_frame")
    def update_details_frame(self, window):
        if window is not None:
            w = window.widget()
            obj_type = w.objectName()
            name = w.name_label_txt()
            self.ui.lineEdit_type.setText(obj_type)
            self.ui.lineEdit_name.setText(name)
            # Find object data from model. Note: Finds child items only if Qt.MatchRecursive is set.
            found_items = self.project_item_model.findItems(name, Qt.MatchExactly | Qt.MatchRecursive, column=0)
            if len(found_items) == 0:
                logging.error("Item '{0}' not found in project model".format(name))
                return
            if len(found_items) > 1:
                logging.error("More than one item with name '{0}' found".format(name))
                return
            object = found_items[0].data(Qt.UserRole)
            self.ui.lineEdit_data.setText(str(object.get_data()))
            # self.match_selected_item_to_widget(w, w.name_label_txt())
        else:
            self.ui.lineEdit_type.setText("")
            self.ui.lineEdit_name.setText("")
            self.ui.lineEdit_data.setText("")
            self.ui.lineEdit_test.setText("")

    def match_selected_item_to_widget(self, window, name):
        """[OBSOLETE] Return the object (Data Store, Data Connection, etc.) that has window as its widget."""
        obj_type = window.objectName()
        if obj_type == "Data Store":
            for item in self.data_store_list:
                if item.name == name:
                    logging.debug("Found item: {0}".format(name))
                    self.ui.lineEdit_data.setText(str(item.get_data()))
        elif obj_type == "Data Connection":
            for item in self.data_connection_list:
                if item.name == name:
                    logging.debug("Found item: {0}".format(name))
                    self.ui.lineEdit_data.setText(str(item.get_data()))
        elif obj_type == "Tool":
            for item in self.tool_list:
                if item.name == name:
                    logging.debug("Found item: {0}".format(name))
                    self.ui.lineEdit_data.setText(str(item.get_data()))
        elif obj_type == "View":
            for item in self.view_list:
                if item.name == name:
                    logging.debug("Found item: {0}".format(name))
                    self.ui.lineEdit_data.setText(str(item.get_data()))
        else:
            logging.debug("Unknown object type: {0}".format(obj_type))

    @Slot(name="add_data_store")
    def add_data_store(self):
        """Make a QMdiSubwindow, add data store widget to it, and add subwindow to QMdiArea."""
        self.ds_n += 1
        name = "Data Store " + str(self.ds_n)
        data_store = DataStore(name, "Data Store description")
        # Add QWidget -> QMdiSubWindow -> QMdiArea. Returns the added QMdiSubWindow
        sw = self.ui.mdiArea.addSubWindow(data_store.get_widget(), Qt.SubWindow)
        # sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.data_store_list.append(data_store)  # Save reference or signals don't stick
        self.add_item_to_model("Data Stores", name, data_store)
        sw.show()

    @Slot(name="add_data_connection")
    def add_data_connection(self):
        """Add Data Connection as a QMdiSubwindow to QMdiArea."""
        self.dc_n += 1
        name = "Data Connection " + str(self.dc_n)
        data_connection = DataConnection(name, "Data Connection description")
        # Add QWidget -> QMdiSubWindow -> QMdiArea. Returns the added QMdiSubWindow
        sw = self.ui.mdiArea.addSubWindow(data_connection.get_widget(), Qt.SubWindow)
        # sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.data_connection_list.append(data_connection)  # Save reference or signals don't stick
        self.add_item_to_model("Data Connections", name, data_connection)
        sw.show()

    @Slot(name="add_tool")
    def add_tool(self):
        """Add Tool as a QMdiSubwindow to QMdiArea."""
        self.tool_n += 1
        name = "Tool " + str(self.tool_n)
        tool = Tool(name, "Tool description")
        # Add QWidget -> QMdiSubWindow -> QMdiArea. Returns the added QMdiSubWindow
        sw = self.ui.mdiArea.addSubWindow(tool.get_widget(), Qt.SubWindow)
        # sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.tool_list.append(tool)  # Save reference or signals don't stick
        self.add_item_to_model("Tools", name, tool)
        sw.show()

    @Slot(name="add_view")
    def add_view(self):
        """Add View as a QMdiSubwindow to QMdiArea."""
        self.view_n += 1
        name = "View " + str(self.view_n)
        view = View("View " + str(self.view_n), "View description")
        # Add QWidget -> QMdiSubWindow -> QMdiArea. Returns the added QMdiSubWindow
        sw = self.ui.mdiArea.addSubWindow(view.get_widget(), Qt.SubWindow)
        # sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.view_list.append(view)  # Save reference or signals don't stick
        self.add_item_to_model("Views", name, view)
        sw.show()

    def add_item_to_model(self, category, text, data):
        """Add item to project model.

        Args:
            category (str): Project category (e.g. Data Stores)
            text (str): Display role for the new item
            data (QObject): Object that is added to model (e.g. DataStore())
        """
        # First, find QStandardItem where new child item is added
        found_items = self.project_item_model.findItems(category, Qt.MatchExactly, column=0)
        if not found_items:
            logging.error("'{0}' item not found in project item model".format(category))
            return False
        if len(found_items) > 1:
            logging.error("More than one '{0}' item found in project item model".format(category))
            return False
        item_index = found_items[0].index()
        parent_index = item_index.parent()
        if not parent_index.isValid():
            # Parent index is not valid if item has no parent
            new_item = QStandardItem(text)
            new_item.setData(data, role=Qt.UserRole)
            self.project_item_model.itemFromIndex(item_index).appendRow(new_item)
        return True

    @Slot(name="show_about")
    def show_about(self):
        """Show About Spine Toolbox form."""
        self.about_form = AboutWidget(self, SPINE_TOOLBOX_VERSION)
        self.about_form.show()

    def closeEvent(self, event=None):
        """Method for handling application exit.

        Args:
             event (QEvent): PySide2 event
        """
        if event:
            event.accept()
        logging.debug("Bye bye")
        # noinspection PyArgumentList
        QApplication.quit()
