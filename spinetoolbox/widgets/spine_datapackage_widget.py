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
Widget shown to user when opening a 'datapackage.json' file
in Data Connection item.

:author: M. Marin (KTH)
:date:   7.7.2018
"""

from collections import Counter
import logging
import os
from PySide2.QtWidgets import QMainWindow, QMessageBox, QErrorMessage, QAction, QToolButton, QFileDialog, QProgressBar
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QItemSelectionModel, QModelIndex, QSize, QThreadPool
from PySide2.QtGui import QGuiApplication, QFontMetrics, QFont, QIcon
from datapackage import Package
from datapackage.exceptions import DataPackageException
from ..datapackage_import_export import DatapackageToSpineConverter
from .custom_delegates import ForeignKeysDelegate, LineEditDelegate, CheckBoxDelegate
from ..mvcmodels.minimal_table_model import MinimalTableModel
from ..mvcmodels.data_package_models import (
    DatapackageResourcesModel,
    DatapackageFieldsModel,
    DatapackageForeignKeysModel,
)
from ..helpers import busy_effect
from ..config import STATUSBAR_SS


class SpineDatapackageWidget(QMainWindow):
    """A widget to allow user to edit a datapackage and convert it
    to a Spine database in SQLite.

    Attributes:
        data_connection (DataConnection): Data Connection associated to this widget
    """

    msg = Signal(str, name="msg")
    msg_proc = Signal(str, name="msg_proc")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, data_connection):
        """Initialize class."""
        from ..ui.spine_datapackage_form import Ui_MainWindow

        super().__init__(flags=Qt.Window)  # TODO: Set parent as toolbox here if it makes sense
        # TODO: Maybe set the parent as ToolboxUI so that its stylesheet is inherited. This may need
        # TODO: reimplementing the window minimizing and maximizing actions as well as setting the window modality
        self._data_connection = data_connection
        self.datapackage = None
        self.descriptor_tree_context_menu = None
        self.selected_resource_name = None
        self.resource_data = dict()
        self.resources_model = DatapackageResourcesModel(self)
        self.fields_model = DatapackageFieldsModel(self)
        self.foreign_keys_model = DatapackageForeignKeysModel(self)
        self.resource_data_model = MinimalTableModel(self)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.err_msg = QErrorMessage(self)
        self.remove_row_icon = QIcon(":/icons/minus.png")
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.focus_widget = None  # Last widget which had focus before showing a menu from the menubar
        #  Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.restore_ui()
        self.add_toggle_view_actions()
        # Add status bar to form
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.ui.statusbar.addPermanentWidget(self.progress_bar)
        self.ui.tableView_resources.setModel(self.resources_model)
        self.ui.tableView_fields.setModel(self.fields_model)
        self.ui.tableView_foreign_keys.setModel(self.foreign_keys_model)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resources.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_fields.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_fields.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_foreign_keys.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_foreign_keys.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.connect_signals()
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_foreign_keys.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_fields.toggleViewAction())

    def show(self):
        """Called when the form shows. Init datapackage
        (either from existing datapackage.json or by inferring a new one from sources)
        and update ui."""
        super().show()
        if not self.load_datapackage():
            return
        self.update_ui()

    @Slot(bool, name="infer_datapackage")
    def infer_datapackage(self, checked=False):
        """Called when the user triggers the infer action.
        Infer datapackage from sources and update ui."""
        if not self.infer_datapackage_():
            return
        self.update_ui()

    def load_datapackage(self):
        """Load datapackage from 'datapackage.json' file in data directory,
        or infer one from CSV files in that directory."""
        file_path = os.path.join(self._data_connection.data_dir, "datapackage.json")
        if os.path.exists(file_path):
            self.datapackage = CustomPackage(file_path)
            msg = "Datapackage successfully loaded from {}".format(file_path)
            self.msg.emit(msg)
            return True
        return self.infer_datapackage()

    def infer_datapackage_(self):
        """Infer datapackage from CSV files in data directory."""
        data_files = self._data_connection.data_files()
        if ".csv" in [os.path.splitext(f)[1] for f in data_files]:
            self.datapackage = CustomPackage(base_path=self._data_connection.data_dir)
            self.datapackage.infer(os.path.join(self._data_connection.data_dir, '*.csv'))
            msg = "Datapackage successfully inferred from {}".format(self._data_connection.data_dir)
            self.msg.emit(msg)
            return True
        self.msg_error.emit(
            "Unable to infer a datapackage from <b>{0}</b>. "
            "Please add some CSV files to that folder,  "
            "and then select the <b>Infer datapackage</b> option "
            "from the <b>File</b> menu.".format(self._data_connection.data_dir)
        )
        return False

    def update_ui(self):
        """Update ui from datapackage attribute."""
        if not self.datapackage:
            return
        self.load_resource_data()
        self.resources_model.reset_model(self.datapackage.resources)
        first_index = self.resources_model.index(0, 0)
        if not first_index.isValid():
            return
        self.ui.tableView_resources.selectionModel().select(first_index, QItemSelectionModel.Select)
        self.reset_resource_models(first_index, QModelIndex())

    def connect_signals(self):
        """Connect signals to slots."""
        # Message actions
        self.msg.connect(self.add_message)
        self.msg_proc.connect(self.add_process_message)
        self.msg_error.connect(self.add_error_message)
        # DC destroyed
        self._data_connection.destroyed.connect(self.close)
        # Copy and paste
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        # Delegates
        # Resource name
        line_edit_delegate = LineEditDelegate(self)
        line_edit_delegate.data_committed.connect(self._handle_resource_name_data_committed)
        self.ui.tableView_resources.setItemDelegateForColumn(0, line_edit_delegate)
        # Field name
        line_edit_delegate = LineEditDelegate(self)
        line_edit_delegate.data_committed.connect(self._handle_field_name_data_committed)
        self.ui.tableView_fields.setItemDelegateForColumn(0, line_edit_delegate)
        # Primary key
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.data_committed.connect(self._handle_primary_key_data_committed)
        self.ui.tableView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        self.ui.tableView_resource_data.setItemDelegate(line_edit_delegate)
        # Foreign keys
        foreign_keys_delegate = ForeignKeysDelegate(self)
        foreign_keys_delegate.data_committed.connect(self._handle_foreign_keys_data_committed)
        self.ui.tableView_foreign_keys.setItemDelegate(foreign_keys_delegate)
        self.foreign_keys_model.rowsInserted.connect(self._handle_foreign_keys_model_rows_inserted)
        # Selected resource changed
        self.ui.tableView_resources.selectionModel().currentChanged.connect(self.reset_resource_models)
        # Foreign keys data changed
        self.foreign_keys_model.dataChanged.connect(self._handle_foreign_keys_data_changed)
        # Actions
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.actionInfer_datapackage.triggered.connect(self.infer_datapackage)
        self.ui.actionExport_to_spine.triggered.connect(self.show_export_to_spine_dialog)
        # Menu about to show
        self.ui.menuFile.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuEdit.aboutToShow.connect(self._handle_menu_about_to_show)
        self.ui.menuView.aboutToShow.connect(self._handle_menu_about_to_show)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("dataPackageWidget/windowSize")
        window_pos = self.qsettings.value("dataPackageWidget/windowPosition")
        splitter_state = self.qsettings.value("dataPackageWidget/splitterState")
        window_maximized = self.qsettings.value("dataPackageWidget/windowMaximized", defaultValue='false')
        window_state = self.qsettings.value("dataPackageWidget/windowState")
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if splitter_state:
            self.ui.splitter.restoreState(splitter_state)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    @Slot(name="_handle_menu_about_to_show")
    def _handle_menu_about_to_show(self):
        """Called when a menu from the menubar is about to show.
        Adjust infer action depending on whether or not we have a datapackage.
        Adjust copy paste actions depending on which widget has the focus.
        TODO Enable/disable action to save datapackage depending on status.
        """
        if self.datapackage:
            self.ui.actionInfer_datapackage.setText("Re-infer datapackage")
        else:
            self.ui.actionInfer_datapackage.setText("Infer datapackage")
        self.ui.actionCopy.setText("Copy")
        self.ui.actionPaste.setText("Paste")
        self.ui.actionCopy.setEnabled(False)
        self.ui.actionPaste.setEnabled(False)
        if self.focusWidget() != self.ui.menubar:
            self.focus_widget = self.focusWidget()
        if self.focus_widget == self.ui.tableView_resources:
            focus_widget_name = "resources"
        elif self.focus_widget == self.ui.tableView_resource_data:
            focus_widget_name = "data"
        elif self.focus_widget == self.ui.tableView_fields:
            focus_widget_name = "fields"
        elif self.focus_widget == self.ui.tableView_foreign_keys:
            focus_widget_name = "foreign keys"
        else:
            return
        if not self.focus_widget.selectionModel().selection().isEmpty():
            self.ui.actionCopy.setText("Copy from {}".format(focus_widget_name))
            self.ui.actionCopy.setEnabled(True)
        if self.focus_widget.canPaste():
            self.ui.actionPaste.setText("Paste to {}".format(focus_widget_name))
            self.ui.actionPaste.setEnabled(True)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Prepend regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        msg += "\t" + self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(msg, 5000)

    @Slot(str, name="add_process_message")
    def add_process_message(self, msg):
        """Show process message in status bar. This messages stays until replaced.

        Args:
            msg (str): String to show in QStatusBar
        """
        self.ui.statusbar.showMessage(msg, 0)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show
        """
        self.err_msg.showMessage(msg)

    @Slot(bool, name="save_datapackage")
    def save_datapackage(self, checked=False):
        """Write datapackage to file 'datapackage.json' in data directory."""
        if os.path.isfile(os.path.join(self._data_connection.data_dir, "datapackage.json")):
            msg = ('<b>Replacing file "datapackage.json" in "{}"</b>. ' 'Are you sure?').format(
                os.path.basename(self._data_connection.data_dir)
            )
            message_box = QMessageBox(
                QMessageBox.Question, "Replace 'datapackage.json", msg, QMessageBox.Ok | QMessageBox.Cancel, parent=self
            )
            message_box.button(QMessageBox.Ok).setText("Replace File")
            answer = message_box.exec_()
            if answer == QMessageBox.Cancel:
                return False
        if self.datapackage.save(os.path.join(self._data_connection.data_dir, 'datapackage.json')):
            msg = '"datapackage.json" saved in {}'.format(self._data_connection.data_dir)
            self.msg.emit(msg)
            return True
        msg = 'Failed to save "datapackage.json" in {}'.format(self._data_connection.data_dir)
        self.msg_error.emit(msg)
        return False

    @Slot(bool, name="show_export_to_spine_dialog")
    def show_export_to_spine_dialog(self, checked=False):
        """Show dialog to allow user to select a file to export."""
        # noinspection PyCallByClass, PyTypeChecker, PyArgumentList
        answer = QFileDialog.getSaveFileName(
            self, "Export to file", self._data_connection._project.project_dir, "SQlite database (*.sqlite *.db)"
        )
        file_path = answer[0]
        if not file_path:  # Cancel button clicked
            return
        self.export_to_spine(file_path)

    @busy_effect
    def export_to_spine(self, file_path):
        """Export datapackage into Spine SQlite file."""
        # Remove file if exists (at this point, the user has confirmed that overwritting is ok)
        try:
            os.remove(file_path)
        except OSError:
            pass
        db_url = 'sqlite:///{0}'.format(file_path)
        # datapackage_path = os.path.join(self.datapackage.base_path, "datapackage.json")
        self.progress_bar.show()
        # converter = DatapackageToSpineConverter(db_url, datapackage_path)
        converter = DatapackageToSpineConverter(db_url, self.datapackage.descriptor, self.datapackage.base_path)
        converter.signaler.finished.connect(self._handle_converter_finished)
        converter.signaler.failed.connect(self._handle_converter_failed)
        converter.signaler.progressed.connect(self._handle_converter_progressed)
        self.msg_proc.emit("Estimating work load...")
        self.progress_bar.setRange(0, converter.number_of_steps())
        self.progress_bar.reset()
        QThreadPool.globalInstance().start(converter)

    @Slot("int", "QString", name="_handle_converter_progressed")
    def _handle_converter_progressed(self, step, msg):
        self.progress_bar.setValue(step)
        if msg:
            self.msg_proc.emit(msg)

    @Slot("QString", name="_handle_converter_failed")
    def _handle_converter_failed(self, msg):
        self.progress_bar.hide()
        self.msg_error.emit("Unable to export datapackage: {}.".format(msg))

    @Slot(name="_handle_converter_finished")
    def _handle_converter_finished(self):
        self.progress_bar.hide()
        self.msg_proc.emit("Datapackage successfully exported.")

    @Slot("bool", name="copy")
    def copy(self, checked=False):
        """Copy data to clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.copy()
        except AttributeError:
            pass

    @Slot("bool", name="paste")
    def paste(self, checked=False):
        """Paste data from clipboard."""
        focus_widget = self.focusWidget()
        try:
            focus_widget.paste()
        except AttributeError:
            pass

    def load_resource_data(self):
        """Load resource data into a local list of tables."""
        for resource in self.datapackage.resources:
            self.resource_data[resource.name] = resource.read(cast=False)

    @Slot("QModelIndex", "QModelIndex", name="reset_resource_models")
    def reset_resource_models(self, current, previous):
        """Reset resource data and schema models whenever a new resource is selected."""
        if current.column() != 0:
            return
        new_selected_resource_name = current.data(Qt.DisplayRole)
        self.selected_resource_name = new_selected_resource_name
        self.reset_resource_data_model()
        schema = self.datapackage.get_resource(self.selected_resource_name).schema
        self.fields_model.reset_model(schema)
        self.foreign_keys_model.reset_model(schema.foreign_keys)
        self.ui.tableView_fields.resizeColumnsToContents()
        self.ui.tableView_foreign_keys.resizeColumnsToContents()
        # Add buttons
        self._handle_foreign_keys_model_rows_inserted(QModelIndex(), 0, self.foreign_keys_model.rowCount() - 1)
        # Resize last section that has the button to remove row
        self.ui.tableView_foreign_keys.horizontalHeader().resizeSection(
            self.foreign_keys_model.columnCount() - 1, self.default_row_height
        )

    def reset_resource_data_model(self):
        """Reset resource data model with data from newly selected resource."""
        data = self.resource_data[self.selected_resource_name]
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.resource_data_model.set_horizontal_header_labels(field_names)
        self.resource_data_model.reset_model(data)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        # Replace delegate
        line_edit_delegate = LineEditDelegate(self)
        self.ui.tableView_resource_data.setItemDelegate(line_edit_delegate)
        line_edit_delegate.data_committed.connect(self.update_resource_data)

    @Slot("QModelIndex", "QVariant", name="update_resource_data")
    def update_resource_data(self, index, new_value):
        """Update resource data with newly edited data."""
        if not self.resource_data_model.setData(index, new_value, Qt.EditRole):
            return
        self.ui.tableView_resource_data.resizeColumnsToContents()

    @Slot("QModelIndex", "QVariant", name="_handle_resource_name_data_committed")
    def _handle_resource_name_data_committed(self, index, new_name):
        """Called when line edit delegate wants to edit resource name data.
        Update resources model and descriptor with new resource name."""
        if not new_name:
            return
        old_name = index.data(Qt.DisplayRole)
        if not self.resources_model.setData(index, new_name, Qt.EditRole):
            return
        resource_data = self.resource_data.pop(self.selected_resource_name)
        if resource_data is None:
            msg = "Couldn't find key in resource data dict. Something is wrong."
            logging.debug(msg)
            return
        self.resource_data[new_name] = resource_data
        self.selected_resource_name = new_name
        self.datapackage.rename_resource(old_name, new_name)

    @Slot("QModelIndex", "QVariant", name="_handle_field_name_data_committed")
    def _handle_field_name_data_committed(self, index, new_name):
        """Called when line edit delegate wants to edit field name data.
        Update name in fields_model, resource_data_model's header and datapackage descriptor.
        """
        if not new_name:
            return
        old_name = index.data(Qt.DisplayRole)
        if not self.fields_model.setData(index, new_name, Qt.EditRole):
            return
        self.datapackage.rename_field(self.selected_resource_name, old_name, new_name)
        field_names = self.datapackage.get_resource(self.selected_resource_name).schema.field_names
        self.resource_data_model.set_horizontal_header_labels(field_names)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        schema = self.datapackage.get_resource(self.selected_resource_name).schema
        self.foreign_keys_model.reset_model(schema.foreign_keys)

    @Slot("QModelIndex", name="_handle_primary_key_data_committed")
    def _handle_primary_key_data_committed(self, index):
        """Called when checkbox delegate wants to edit primary key data.
        Add or remove primary key field accordingly.
        """
        status = index.data(Qt.EditRole)
        field_name = index.sibling(index.row(), 0).data(Qt.DisplayRole)
        if status is False:  # Add to primary key
            self.fields_model.setData(index, True, Qt.EditRole)
            self.datapackage.append_to_primary_key(self.selected_resource_name, field_name)
        else:  # Remove from primary key
            self.fields_model.setData(index, False, Qt.EditRole)
            self.datapackage.remove_from_primary_key(self.selected_resource_name, field_name)

    @Slot("QModelIndex", "QVariant", name="_handle_foreign_keys_data_committed")
    def _handle_foreign_keys_data_committed(self, index, value):
        self.foreign_keys_model.setData(index, value, Qt.EditRole)

    @Slot("QModelIndex", "QModelIndex", "QVector<int>", name="_handle_foreign_keys_data_changed")
    def _handle_foreign_keys_data_changed(self, top_left, bottom_right, roles=None):
        """Called when foreign keys data is updated in model.
        Update descriptor accordingly."""
        if roles is None:
            roles = list()
        if roles and Qt.EditRole not in roles:
            return
        resource = self.selected_resource_name
        anything_updated = False
        rows = range(top_left.row(), bottom_right.row() + 1)
        error_log = ""
        for row in rows:
            # Remove previous foreign key
            self.datapackage.remove_foreign_keys_row(row, resource)
            # Add new foreign key if possible
            row_data = self.foreign_keys_model._main_data[row][0:3]
            if all(row_data):
                fields_str, reference_resource, reference_fields_str = row_data
                fields = fields_str.split(",")
                reference_fields = reference_fields_str.split(",")
                try:
                    self.datapackage.insert_foreign_key(row, resource, fields, reference_resource, reference_fields)
                    anything_updated = True
                except DataPackageException as e:
                    v_section = self.foreign_keys_model.headerData(row, Qt.Vertical)
                    error_log += "<p>Unable to add foreign key at row {0}: '{1}'</p>".format(v_section, e)
        if anything_updated:
            self.msg.emit("Successfully updated foreign keys.")
        if error_log:
            self.msg_error.emit(error_log)

    @Slot("QModelIndex", "int", "int", name="_handle_foreign_keys_model_rows_inserted")
    def _handle_foreign_keys_model_rows_inserted(self, parent, first, last):
        column = self.foreign_keys_model.columnCount() - 1
        for row in range(first, last + 1):
            index = self.foreign_keys_model.index(row, column, parent)
            self.create_remove_foreign_keys_row_button(index)

    def create_remove_foreign_keys_row_button(self, index):
        """Create button to remove foreign keys row."""
        action = QAction()
        action.setIcon(self.remove_row_icon)
        button = QToolButton()
        button.setDefaultAction(action)
        button.setIconSize(QSize(20, 20))
        self.ui.tableView_foreign_keys.setIndexWidget(index, button)
        action.triggered.connect(lambda: self.remove_foreign_key_row(button))

    def remove_foreign_key_row(self, button):
        column = self.foreign_keys_model.columnCount() - 1
        for row in range(self.foreign_keys_model.rowCount()):
            index = self.foreign_keys_model.index(row, column)
            if button != self.ui.tableView_foreign_keys.indexWidget(index):
                continue
            # Remove fk from datapackage descriptor
            self.foreign_keys_model.removeRows(row, 1)
            resource = self.selected_resource_name
            self.datapackage.remove_foreign_keys_row(row, resource)
            self.msg.emit("Successfully removed foreign key.")
            break

    def closeEvent(self, event=None):
        """Handle close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("dataPackageWidget/splitterState", self.ui.splitter.saveState())
        self.qsettings.setValue("dataPackageWidget/windowSize", self.size())
        self.qsettings.setValue("dataPackageWidget/windowPosition", self.pos())
        self.qsettings.setValue("dataPackageWidget/windowState", self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("dataPackageWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("dataPackageWidget/windowMaximized", False)
        if event:
            event.accept()


class CustomPackage(Package):
    """Custom datapackage class."""

    def __init__(self, descriptor=None, base_path=None, strict=False, storage=None):
        super().__init__(descriptor, base_path, strict, storage)

    def rename_resource(self, old, new):
        resource_index = self.resource_names.index(old)
        self.descriptor['resources'][resource_index]['name'] = new
        self.commit()

    def rename_field(self, resource, old, new):
        """Rename a field.
        """
        resource_index = self.resource_names.index(resource)
        resource_dict = self.descriptor['resources'][resource_index]
        resource_schema = self.get_resource(resource).schema
        field_index = resource_schema.field_names.index(old)
        resource_dict['schema']['fields'][field_index]['name'] = new
        primary_key = resource_schema.primary_key
        foreign_keys = resource_schema.foreign_keys
        for i, field in enumerate(primary_key):
            if field == old:
                resource_dict['schema']['primaryKey'][i] = new
        for i, foreign_key in enumerate(foreign_keys):
            for j, field in enumerate(foreign_key["fields"]):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['fields'][j] = new
            for j, field in enumerate(foreign_key['reference']['fields']):
                if field == old:
                    resource_dict['schema']['foreignKeys'][i]['reference']['fields'][j] = new
        self.commit()

    def set_primary_key(self, resource, *primary_key):
        """Set primary key for a given resource in the package"""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        self.descriptor['resources'][i]['schema']['primaryKey'] = primary_key
        self.commit()

    def append_to_primary_key(self, resource, field):
        """Append field to resources's primary key."""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        primary_key = self.descriptor['resources'][i]['schema'].setdefault('primaryKey', [])
        if field not in primary_key:
            primary_key.append(field)
        self.commit()

    def remove_from_primary_key(self, resource, field):
        """Remove field from resources's primary key."""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        primary_key = self.descriptor['resources'][i]['schema'].get('primaryKey')
        if not primary_key:
            return
        if field in primary_key:
            primary_key.remove(field)
        self.commit()

    def insert_foreign_key(self, row, resource_name, field_names, reference_resource_name, reference_field_names):
        """Insert foreign key to a given resource in the package at a given row."""
        if len(field_names) != len(reference_field_names):
            raise DataPackageException("Both 'fields' and 'reference fields' should have the same number of elements.")
        resource = self.get_resource(resource_name)
        if not resource:
            raise DataPackageException("Resource '{}' not in datapackage".format(resource_name))
        for field_name in field_names:
            if field_name not in resource.schema.field_names:
                raise DataPackageException("Field '{}' not in '{}' schema".format(field_name, resource_name))
        reference_resource = self.get_resource(reference_resource_name)
        if not reference_resource:
            raise DataPackageException("Resource '{}' not in datapackage".format(reference_resource_name))
        for reference_field_name in reference_field_names:
            if reference_field_name not in reference_resource.schema.field_names:
                raise DataPackageException(
                    "Field '{}' not in '{}' schema".format(reference_field_name, reference_resource_name)
                )
        foreign_key = {
            "fields": field_names,
            "reference": {"resource": reference_resource_name, "fields": reference_field_names},
        }
        i = self.resource_names.index(resource_name)
        self.descriptor['resources'][i]['schema'].setdefault('foreignKeys', [])
        if foreign_key in self.descriptor['resources'][i]['schema']['foreignKeys']:
            raise DataPackageException("Foreign key already in '{}' schema".format(resource_name))
        self.descriptor['resources'][i]['schema']['foreignKeys'].insert(row, foreign_key)
        self.commit()

    def remove_primary_key(self, resource, *primary_key):
        """Remove the primary key for a given resource in the package"""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        if 'primaryKey' in self.descriptor['resources'][i]['schema']:
            descriptor_primary_key = self.descriptor['resources'][i]['schema']['primaryKey']
            if Counter(descriptor_primary_key) == Counter(primary_key):
                del self.descriptor['resources'][i]['schema']['primaryKey']
                self.commit()

    def remove_foreign_key(self, resource, fields, reference_resource, reference_fields):
        """Remove foreign key from the package"""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        foreign_key = {"fields": fields, "reference": {"resource": reference_resource, "fields": reference_fields}}
        try:
            self.descriptor['resources'][i]['schema']['foreignKeys']
        except KeyError:
            return
        try:
            self.descriptor['resources'][i]['schema']['foreignKeys'].remove(foreign_key)
        except ValueError:
            return
        self.commit()

    def remove_foreign_keys_row(self, row, resource):
        """Remove foreign keys row from the package"""
        try:
            i = self.resource_names.index(resource)
        except ValueError:
            return
        try:
            foreign_keys = self.descriptor['resources'][i]['schema']['foreignKeys']
        except KeyError:
            return
        try:
            foreign_keys.pop(row)
        except IndexError:
            return
        self.commit()
