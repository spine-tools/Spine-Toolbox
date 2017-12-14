"""
Module for main application GUI functions.

:author: Pekka Savolainen <pekka.t.savolainen@vtt.fi>
:date:   14.12.2017
"""

import locale
import logging
from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import QMainWindow, QApplication
from ui.mainwindow import Ui_MainWindow
from widgets.data_store_widget import DataStoreWidget


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
        self.data_store_form = None
        self.ui.mdiArea.addSubWindow(self.ui.subwindow)
        self.ui.mdiArea.addSubWindow(self.ui.subwindow_2)
        self.ui.mdiArea.addSubWindow(self.ui.subwindow_3)
        sub_windows = self.ui.mdiArea.subWindowList()
        logging.debug("Number of subwindows:{0}".format(len(sub_windows)))
        self.connect_signals()

    def connect_signals(self):
        """Connect signals."""
        self.ui.actionData_Collection_View.triggered.connect(self.open_data_store_view)
        self.ui.pushButton_datastore_edit.pressed.connect(self.open_data_store_view)

    @Slot(name="data_store_view_slot")
    def open_data_store_view(self):
        self.data_store_form = DataStoreWidget(self)
        self.data_store_form.show()

    def closeEvent(self, event):
        """Method for handling application exit.

        Args:
             event (QEvent): PySide2 event
        """
        logging.debug("Bye bye")
        # noinspection PyArgumentList
        QApplication.quit()
