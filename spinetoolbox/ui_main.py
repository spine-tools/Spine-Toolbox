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
from PySide2.QtCore import Qt, Slot, QSize
from PySide2.QtWidgets import QMainWindow, QApplication, QMdiSubWindow
from ui.mainwindow import Ui_MainWindow
from widgets.data_store_widget import DataStoreWidget
from widgets.about_widget import AboutWidget
from widgets.subwindow_widget import SubWindowWidget
from data_store import DataStore
from data_connection import DataConnection
from tool import Tool
from view import View


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
        self.data_store_list = list()  # References to data stores. TODO: Remove reference if data store is deleted
        self.data_connection_list = list()
        self.tool_list = list()
        self.view_list = list()
        self.connect_signals()

    def connect_signals(self):
        """Connect signals."""
        self.ui.actionData_Collection_View.triggered.connect(self.open_data_store_view)
        self.ui.pushButton_add_data_store.clicked.connect(self.add_data_store)
        self.ui.pushButton_add_data_connection.clicked.connect(self.add_data_connection)
        self.ui.pushButton_add_tool.clicked.connect(self.add_tool)
        self.ui.pushButton_add_view.clicked.connect(self.add_view)
        self.ui.pushButton_test1.clicked.connect(self.test1)
        self.ui.pushButton_test2.clicked.connect(self.test2)
        self.ui.actionAbout.triggered.connect(self.show_about)

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
        # logging.debug(current_sub_window.windowTitle())
        widget_name = current_sub_window.widget().name_label_txt()
        par = current_sub_window.widget().parent()
        logging.debug("Parent of {0}:{1}".format(widget_name, par))

    @Slot(name="add_data_store")
    def add_data_store(self):
        """Make a QMdiSubwindow, add data store widget to it, and add subwindow to QMdiArea."""
        sw = QMdiSubWindow()
        data_store = DataStore(sw, "Data Store", "Data Store description")
        # Set data store widget as QMdiSubWindow's internal widget
        sw.setWidget(data_store.widget())
        sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.ui.mdiArea.addSubWindow(sw, Qt.SubWindow)  # Add subwindow into QMdiArea
        self.data_store_list.append(data_store)  # Save reference or signals don't stick
        sw.show()

    @Slot(name="add_data_connection")
    def add_data_connection(self):
        """Add Data Connection as a QMdiSubwindow to QMdiArea."""
        sw = QMdiSubWindow()
        data_connection = DataConnection(sw, "Data Connection", "Data Connection description")
        # Set data connection widget as QMdiSubWindow's internal widget
        sw.setWidget(data_connection.widget())
        sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.ui.mdiArea.addSubWindow(sw, Qt.SubWindow)  # Add subwindow into QMdiArea
        self.data_connection_list.append(data_connection)  # Save reference or signals don't stick
        sw.show()

    @Slot(name="add_tool")
    def add_tool(self):
        """Add Tool as a QMdiSubwindow to QMdiArea."""
        sw = QMdiSubWindow()
        tool = Tool(sw, "Tool", "Tool description")
        # Set tool widget as QMdiSubWindow's internal widget
        sw.setWidget(tool.widget())
        sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.ui.mdiArea.addSubWindow(sw, Qt.SubWindow)  # Add subwindow into QMdiArea
        self.tool_list.append(tool)  # Save reference or signals don't stick
        sw.show()

    @Slot(name="add_view")
    def add_view(self):
        """Add View as a QMdiSubwindow to QMdiArea."""
        sw = QMdiSubWindow()
        view = View(sw, "View", "View description")
        # Set view widget as QMdiSubWindow's internal widget
        sw.setWidget(view.widget())
        sw.setAttribute(Qt.WA_DeleteOnClose)  # Closing deletes the subwindow
        self.ui.mdiArea.addSubWindow(sw, Qt.SubWindow)  # Add subwindow into QMdiArea
        self.view_list.append(view)  # Save reference or signals don't stick
        sw.show()

    @Slot(name="show_about")
    def show_about(self):
        """Show About Spine Toolbox form."""
        self.about_form = AboutWidget(self, "0.0.1")
        self.about_form.show()

    def closeEvent(self, event):
        """Method for handling application exit.

        Args:
             event (QEvent): PySide2 event
        """
        logging.debug("Bye bye")
        # noinspection PyArgumentList
        QApplication.quit()
