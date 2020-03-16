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
ImportDialog class.

:author: P. Vennström (VTT)
:date:   1.6.2019
"""

from PySide2.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QDialogButtonBox,
    QPushButton,
    QLabel,
    QSplitter,
    QStyle,
)
from PySide2.QtCore import QSize, Qt, Slot
from PySide2.QtGui import QGuiApplication
import spinedb_api
from ..helpers import busy_effect
from ..spine_io.connection_manager import ConnectionManager
from ..spine_io.importers.csv_reader import CSVConnector
from ..spine_io.importers.excel_reader import ExcelConnector
from ..spine_io.importers.sqlalchemy_connector import SqlAlchemyConnector
from ..spine_io.importers.gdx_connector import GdxConnector
from ..spine_io.importers.json_reader import JSONConnector
from .import_preview_widget import ImportPreviewWidget
from .import_errors_widget import ImportErrorWidget


class ImportDialog(QDialog):
    """
    A widget for importing data into a Spine db. Currently used by DataStoreForm.
    It embeds three widgets that alternate depending on user's actions:
    - `select_widget` is a `QWidget` for selecting the source data type (CSV, Excel, etc.)
    - `_import_preview` is an `ImportPreviewWidget` for defining Mappings to associate with the source data
    - `_error_widget` is an `ImportErrorWidget` to show errors from import operations
    """

    _SETTINGS_GROUP_NAME = "importDialog"

    def __init__(self, settings, parent):
        """
        Args:
            settings (QSettings): settings for storing/restoring window state
            parent (QWidget): parent widget
        """
        from ..ui.import_source_selector import Ui_ImportSourceSelector

        super().__init__(parent)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)
        self.setWindowTitle("Import data")
        # DB mapping
        if parent is not None:
            self._db_map = parent.db_maps[0]

        # state
        self._mapped_data = None
        self._mapping_errors = []
        self.connector_list = [CSVConnector, ExcelConnector, SqlAlchemyConnector, GdxConnector, JSONConnector]
        self.connector_list = {c.DISPLAY_NAME: c for c in self.connector_list}
        self._selected_connector = None
        self.active_connector = None
        self._current_view = "connector"
        self._settings = settings
        self._preview_window_state = {}

        # create widgets
        self._import_preview = None
        self._error_widget = ImportErrorWidget()
        self._error_widget.hide()
        self._dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Abort | QDialogButtonBox.Cancel)
        self._dialog_buttons.button(QDialogButtonBox.Abort).setText("Back")

        self._layout = QVBoxLayout()

        # layout
        self.select_widget = QWidget(self)
        self._select_widget_ui = Ui_ImportSourceSelector()
        self._select_widget_ui.setupUi(self.select_widget)

        self.setLayout(QVBoxLayout())
        self.layout().addLayout(self._layout)
        self.layout().addWidget(self._dialog_buttons)
        self._layout.addWidget(self._error_widget)
        self._layout.addWidget(self.select_widget)

        # set list items
        self._select_widget_ui.source_list.blockSignals(True)
        self._select_widget_ui.source_list.addItems(list(self.connector_list.keys()))
        self._select_widget_ui.source_list.clearSelection()
        self._select_widget_ui.source_list.blockSignals(False)

        # connect signals
        self._select_widget_ui.source_list.currentItemChanged.connect(self.connector_selected)
        self._select_widget_ui.source_list.activated.connect(self.launch_import_preview)
        self._dialog_buttons.button(QDialogButtonBox.Ok).clicked.connect(self.ok_clicked)
        self._dialog_buttons.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel_clicked)
        self._dialog_buttons.button(QDialogButtonBox.Abort).clicked.connect(self.back_clicked)

        # init ok button
        self.set_ok_button_availability()

        self._dialog_buttons.button(QDialogButtonBox.Abort).hide()

    @property
    def mapped_data(self):
        return self._mapped_data

    @property
    def mapping_errors(self):
        return self._mapping_errors

    @Slot()
    def connector_selected(self, selection):
        connector = None
        if selection:
            connector = self.connector_list.get(selection.text(), None)
        self._selected_connector = connector
        self.set_ok_button_availability()

    def set_ok_button_availability(self):
        if self._current_view == "connector":
            if self._selected_connector:
                self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        elif self._current_view == "preview":
            if self._import_preview.checked_tables:
                self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)
            else:
                self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(False)
        else:
            self._dialog_buttons.button(QDialogButtonBox.Ok).setEnabled(True)

    @busy_effect
    def import_data(self, data, errors):
        errors = [f"{table_name}: {error_message}" for table_name, error_message in errors]
        try:
            import_num, import_errors = spinedb_api.import_data(self._db_map, **data)
            import_errors = [f"{e.db_type}: {e.msg}" for e in import_errors]
            errors.extend(import_errors)
        except spinedb_api.SpineIntegrityError as err:
            self._db_map.rollback_session()
            self._error_widget.set_import_state(0, [err.msg])
            self.set_error_widget_as_main_widget()
        except spinedb_api.SpineDBAPIError as err:
            self._db_map.rollback_session()
            self._error_widget.set_import_state(0, ["Unable to import Data: %s", err.msg])
            self.set_error_widget_as_main_widget()
        if errors:
            self._error_widget.set_import_state(import_num, errors)
            self.set_error_widget_as_main_widget()
            return False
        return True

    @Slot()
    def data_ready(self, data, errors):
        if self.import_data(data, errors):
            self.accept()

    @Slot()
    def ok_clicked(self):
        if self._current_view == "connector":
            self.launch_import_preview()
        elif self._current_view == "preview":
            self._import_preview.request_mapped_data()
        elif self._current_view == "error":
            self.accept()

    @Slot()
    def cancel_clicked(self):
        if self._db_map.has_pending_changes():
            self._db_map.rollback_session()
        self.reject()

    @Slot()
    def back_clicked(self):
        if self._db_map.has_pending_changes():
            self._db_map.rollback_session()
        self.set_preview_as_main_widget()

    @Slot()
    def launch_import_preview(self):
        if self._selected_connector:
            # create instance of connector
            self.active_connector = ConnectionManager(self._selected_connector)
            valid_source = self.active_connector.connection_ui()
            if valid_source:
                # Create instance of ImportPreviewWidget and configure
                self._import_preview = ImportPreviewWidget(self.active_connector, self)
                self._import_preview.set_loading_status(True)
                self._import_preview.tableChecked.connect(self.set_ok_button_availability)
                # Connect data_ready method to the widget
                self._import_preview.mappedDataReady.connect(self.data_ready)
                self._layout.addWidget(self._import_preview)
                self.active_connector.connectionFailed.connect(self._handle_failed_connection)
                self.active_connector.init_connection()
                # show preview widget
                self.set_preview_as_main_widget()
            else:
                # remove connector object.
                self.active_connector.deleteLater()
                self.active_connector = None

    @Slot(str)
    def _handle_failed_connection(self, msg):
        """Handle failed connection, show error message and select widget

        Arguments:
            msg {str} -- str with message of reason for failed connection.
        """
        self.select_widget.hide()
        self._error_widget.hide()
        self._import_preview.hide()

        if self.active_connector:
            self.active_connector.close_connection()
            self.active_connector.deleteLater()
            self.active_connector = None
        if self._import_preview:
            self._import_preview.deleteLater()
            self._import_preview = None

        ok_button = QPushButton()
        ok_button.setText("Ok")

        temp_widget = QWidget()
        temp_widget.setLayout(QVBoxLayout())
        temp_widget.layout().addWidget(QLabel(msg))
        temp_widget.layout().addWidget(ok_button)

        ok_button.clicked.connect(self.select_widget.show)
        ok_button.clicked.connect(temp_widget.deleteLater)
        self.layout().addWidget(temp_widget)

    def set_preview_as_main_widget(self):
        self._current_view = "preview"
        self.select_widget.hide()
        self._error_widget.hide()
        self._import_preview.show()
        self._restore_preview_ui()
        self._dialog_buttons.button(QDialogButtonBox.Abort).hide()
        self.set_ok_button_availability()

    def set_error_widget_as_main_widget(self):
        self._current_view = "error"
        if self._import_preview is not None and not self._import_preview.isHidden():
            self._preview_window_state["maximized"] = self.windowState() == Qt.WindowMaximized
            self._preview_window_state["size"] = self.size()
            self._preview_window_state["position"] = self.pos()
            splitters = dict()
            self._preview_window_state["splitters"] = splitters
            for splitter in self._import_preview.findChildren(QSplitter):
                splitters[splitter.objectName()] = splitter.saveState()
        self.select_widget.hide()
        self._error_widget.show()
        self._import_preview.hide()
        self._dialog_buttons.button(QDialogButtonBox.Abort).show()
        self.set_ok_button_availability()

    def _restore_preview_ui(self):
        """Restore UI state from previous session."""
        if not self._preview_window_state:
            self._settings.beginGroup(self._SETTINGS_GROUP_NAME)
            window_size = self._settings.value("windowSize")
            window_pos = self._settings.value("windowPosition")
            n_screens = self._settings.value("n_screens", defaultValue=1)
            window_maximized = self._settings.value("windowMaximized", defaultValue='false')
            splitter_state = {}
            for splitter in self._import_preview.findChildren(QSplitter):
                splitter_state[splitter] = self._settings.value(splitter.objectName() + "_splitterState")
            self._settings.endGroup()
            if window_size:
                self.resize(window_size)
            else:
                self.setGeometry(
                    QStyle.alignedRect(
                        Qt.LeftToRight, Qt.AlignCenter, QSize(1000, 700), QApplication.desktop().availableGeometry(self)
                    )
                )
            if window_pos:
                self.move(window_pos)
            if window_maximized == 'true':
                self.setWindowState(Qt.WindowMaximized)
            for splitter, state in splitter_state.items():
                if state:
                    splitter.restoreState(state)
            if len(QGuiApplication.screens()) < int(n_screens):
                # There are less screens available now than on previous application startup
                self.move(0, 0)  # Move this widget to primary screen position (0,0)
        else:
            self.resize(self._preview_window_state["size"])
            self.move(self._preview_window_state["position"])
            self.setWindowState(self._preview_window_state["maximized"])
            for splitter in self._import_preview.findChildren(QSplitter):
                name = splitter.objectName()
                splitter.restoreState(self._preview_window_state["splitters"][name])

    def closeEvent(self, event):
        """Stores window's settings and accepts the event."""
        if self._import_preview is not None:
            self._settings.beginGroup(self._SETTINGS_GROUP_NAME)
            self._settings.setValue("n_screens", len(QGuiApplication.screens()))
            if not self._import_preview.isHidden():
                self._settings.setValue("windowSize", self.size())
                self._settings.setValue("windowPosition", self.pos())
                self._settings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
                for splitter in self._import_preview.findChildren(QSplitter):
                    self._settings.setValue(splitter.objectName() + "_splitterState", splitter.saveState())
            elif self._preview_window_state:
                self._settings.setValue("windowSize", self._preview_window_state["size"])
                self._settings.setValue("windowPosition", self._preview_window_state["position"])
                self._settings.setValue("windowMaximized", self._preview_window_state.maximized)
                for name, state in self._preview_window_state["splitters"]:
                    self._settings.setValue(name + "_splitterState", state)
            self._settings.endGroup()
        event.accept()
