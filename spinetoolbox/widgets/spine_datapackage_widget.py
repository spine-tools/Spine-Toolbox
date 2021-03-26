######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
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

import glob
import os
import csv
from PySide2.QtWidgets import QMainWindow, QMessageBox, QErrorMessage, QAction, QUndoStack, QUndoGroup, QMenu
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QItemSelectionModel, QFileSystemWatcher
from PySide2.QtGui import QGuiApplication, QFontMetrics, QFont, QIcon, QKeySequence
from datapackage import Package
from .custom_delegates import ForeignKeysDelegate, CheckBoxDelegate
from .notification import NotificationStack
from ..mvcmodels.data_package_models import (
    DatapackageResourcesModel,
    DatapackageFieldsModel,
    DatapackageForeignKeysModel,
    DatapackageResourceDataModel,
)
from ..helpers import ensure_window_is_on_screen, focused_widget_has_callable, call_on_focused_widget
from ..config import MAINWINDOW_SS


class SpineDatapackageWidget(QMainWindow):
    """A widget to edit CSV files in a Data Connection and create a tabular datapackage.
    """

    msg = Signal(str)
    msg_error = Signal(str)

    def __init__(self, datapackage):
        """Initialize class.

        Args:
            datapackage (CustomPackage): Data package associated to this widget
        """
        from ..ui.spine_datapackage_form import Ui_MainWindow  # pylint: disable=import-outside-toplevel

        super().__init__(flags=Qt.Window)
        self.datapackage = datapackage
        self.selected_resource_index = None
        self.resources_model = DatapackageResourcesModel(self, self.datapackage)
        self.fields_model = DatapackageFieldsModel(self, self.datapackage)
        self.foreign_keys_model = DatapackageForeignKeysModel(self, self.datapackage)
        self.resource_data_model = DatapackageResourceDataModel(self, self.datapackage)
        self.default_row_height = QFontMetrics(QFont("", 0)).lineSpacing()
        max_screen_height = max([s.availableSize().height() for s in QGuiApplication.screens()])
        self.visible_rows = int(max_screen_height / self.default_row_height)
        self.err_msg = QErrorMessage(self)
        self.notification_stack = NotificationStack(self)
        self._foreign_keys_context_menu = QMenu(self)
        self._file_watcher = QFileSystemWatcher(self)
        self._file_watcher.addPath(self.datapackage.base_path)
        self._changed_source_indexes = set()
        self.undo_group = QUndoGroup(self)
        self.undo_stacks = {}
        self._save_resource_actions = []
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.takeCentralWidget()
        self._before_save_all = self.ui.menuFile.insertSeparator(self.ui.actionSave_All)
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        self.restore_ui()
        self.add_menu_actions()
        self.setStyleSheet(MAINWINDOW_SS)
        self.ui.tableView_resources.setModel(self.resources_model)
        self.ui.tableView_resources.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.setModel(self.resource_data_model)
        self.ui.tableView_resource_data.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_resource_data.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_fields.setModel(self.fields_model)
        self.ui.tableView_fields.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_fields.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.ui.tableView_foreign_keys.setModel(self.foreign_keys_model)
        self.ui.tableView_foreign_keys.verticalHeader().setDefaultSectionSize(self.default_row_height)
        self.ui.tableView_foreign_keys.horizontalHeader().setResizeContentsPrecision(self.visible_rows)
        self.connect_signals()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle("{0}[*] - Spine datapackage manager".format(self.datapackage.base_path))
        self.load_datapackage()

    @property
    def undo_stack(self):
        return self.undo_group.activeStack()

    @property
    def datapackage_path(self):
        return os.path.join(self.datapackage.base_path, "datapackage.json")

    def load_datapackage(self):
        if self.datapackage.sources:
            self._file_watcher.addPaths(self.datapackage.sources)
        self.append_save_resource_actions()
        self.resources_model.refresh_model()
        first_index = self.resources_model.index(0, 0)
        if not first_index.isValid():
            return
        self.ui.tableView_resources.selectionModel().setCurrentIndex(first_index, QItemSelectionModel.Select)

    def add_menu_actions(self):
        """Add extra menu actions."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_resources.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_data.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_fields.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_foreign_keys.toggleViewAction())
        undo_action = self.undo_group.createUndoAction(self)
        redo_action = self.undo_group.createRedoAction(self)
        undo_action.setShortcuts(QKeySequence.Undo)
        redo_action.setShortcuts(QKeySequence.Redo)
        undo_action.setIcon(QIcon(":/icons/menu_icons/undo.svg"))
        redo_action.setIcon(QIcon(":/icons/menu_icons/redo.svg"))
        before = self.ui.menuEdit.actions()[0]
        self.ui.menuEdit.insertAction(before, undo_action)
        self.ui.menuEdit.insertAction(before, redo_action)
        self.ui.menuEdit.insertSeparator(before)

    def connect_signals(self):
        """Connect signals to slots."""
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self._file_watcher.directoryChanged.connect(self._handle_source_dir_changed)
        self._file_watcher.fileChanged.connect(self._handle_source_file_changed)
        self.ui.actionCopy.triggered.connect(self.copy)
        self.ui.actionPaste.triggered.connect(self.paste)
        self.ui.actionClose.triggered.connect(self.close)
        self.ui.actionSave_All.triggered.connect(self.save_all)
        self.ui.actionSave_datapackage.triggered.connect(self.save_datapackage)
        self.ui.menuEdit.aboutToShow.connect(self.refresh_copy_paste_actions)
        self.fields_model.dataChanged.connect(self._handle_fields_data_changed)
        self.undo_group.cleanChanged.connect(self.update_window_modified)
        checkbox_delegate = CheckBoxDelegate(self)
        checkbox_delegate.data_committed.connect(self.fields_model.setData)
        self.ui.tableView_fields.setItemDelegateForColumn(2, checkbox_delegate)
        foreign_keys_delegate = ForeignKeysDelegate(self)
        foreign_keys_delegate.data_committed.connect(self.foreign_keys_model.setData)
        self.ui.tableView_foreign_keys.setItemDelegate(foreign_keys_delegate)
        self.ui.tableView_resources.selectionModel().currentChanged.connect(self._handle_current_resource_changed)
        self.ui.tableView_foreign_keys.customContextMenuRequested.connect(self.show_foreign_keys_context_menu)
        self._foreign_keys_context_menu.addAction("Remove foreign key", self._remove_foreign_key)

    @Slot(bool)
    def update_window_modified(self, _clean=None):
        """Updates window modified status and save actions depending on the state of the undo stack."""
        try:
            dirty_resource_indexes = {
                idx for idx in range(len(self.datapackage.resources)) if self.is_resource_dirty(idx)
            }
            dirty = bool(dirty_resource_indexes)
            self.setWindowModified(dirty)
        except RuntimeError:
            return
        self.ui.actionSave_datapackage.setEnabled(dirty)
        self.ui.actionSave_All.setEnabled(dirty)
        for idx, action in enumerate(self._save_resource_actions):
            dirty = idx in dirty_resource_indexes
            action.setEnabled(dirty)
            self.resources_model.update_resource_dirty(idx, dirty)

    def is_resource_dirty(self, resource_index):
        if resource_index in self._changed_source_indexes:
            return True
        try:
            return not self.undo_stacks[resource_index].isClean()
        except KeyError:
            return False

    def get_undo_stack(self, resource_index):
        if resource_index not in self.undo_stacks:
            self.undo_stacks[resource_index] = stack = QUndoStack(self.undo_group)
            stack.cleanChanged.connect(self.update_window_modified)
        return self.undo_stacks[resource_index]

    @Slot(str)
    def _handle_source_dir_changed(self, _path):
        if not self.datapackage.resources:
            self.load_datapackage()
            return
        self.datapackage.difference_infer(os.path.join(self.datapackage.base_path, '*.csv'))
        if self.datapackage.sources:
            self._file_watcher.addPaths(self.datapackage.sources)
        self.append_save_resource_actions()
        self.resources_model.refresh_model()
        self.refresh_models()

    @Slot(str)
    def _handle_source_file_changed(self, path):
        for idx, source in enumerate(self.datapackage.sources):
            if os.path.normpath(source) == os.path.normpath(path):
                self._changed_source_indexes.add(idx)
                self.update_window_modified()
                break

    def append_save_resource_actions(self):
        new_actions = []
        for resource_index in range(len(self._save_resource_actions), len(self.datapackage.resources)):
            resource = self.datapackage.resources[resource_index]
            action = QAction(f"Save '{os.path.basename(resource.source)}'")
            action.setEnabled(False)
            action.triggered.connect(
                lambda checked=False, resource_index=resource_index: self.save_resource(resource_index)
            )
            new_actions.append(action)
        self.ui.menuFile.insertActions(self._before_save_all, new_actions)
        self._save_resource_actions += new_actions

    @Slot()
    def refresh_copy_paste_actions(self):
        """Adjusts copy and paste actions depending on which widget has the focus.
        """
        self.ui.actionCopy.setEnabled(focused_widget_has_callable(self, "copy"))
        self.ui.actionPaste.setEnabled(focused_widget_has_callable(self, "paste"))

    @Slot(str)
    def add_message(self, msg):
        """Prepend regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        self.notification_stack.push(msg)

    @Slot(str)
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show
        """
        self.err_msg.showMessage(msg)

    @Slot(bool)
    def save_all(self, _=False):
        resource_paths = {k: r.source for k, r in enumerate(self.datapackage.resources) if self.is_resource_dirty(k)}
        all_paths = list(resource_paths.values()) + [self.datapackage_path]
        if not self.get_permission(*all_paths):
            return
        for k, path in resource_paths.items():
            self._save_resource(k, path)
        self.save_datapackage()

    @Slot(bool)
    def save_datapackage(self, _=False):
        if self.datapackage.save(self.datapackage_path):
            self.msg.emit("'datapackage.json' succesfully saved")
            return
        self.msg_error.emit("Failed to save 'datapackage.json'")

    def save_resource(self, resource_index):
        resource = self.datapackage.resources[resource_index]
        filepath = resource.source
        if not self.get_permission(filepath, self.datapackage_path):
            return
        self._save_resource(resource_index, filepath)
        self.save_datapackage()

    def _save_resource(self, resource_index, filepath):
        headers = self.datapackage.resources[resource_index].schema.field_names
        self._file_watcher.removePath(filepath)
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for row in self.datapackage.resource_data(resource_index):
                writer.writerow(row)
        self.msg.emit(f"'{os.path.basename(filepath)}' successfully saved")
        self._file_watcher.addPath(filepath)
        self._changed_source_indexes.discard(resource_index)
        stack = self.undo_stacks.get(resource_index)
        if not stack or stack.isClean():
            self.update_window_modified()
        elif stack:
            stack.setClean()

    def get_permission(self, *filepaths):
        start_dir = self.datapackage.base_path
        filepaths = [os.path.relpath(path, start_dir) for path in filepaths if os.path.isfile(path)]
        if not filepaths:
            return True
        pathlist = "".join([f"<li>{path}</li>" for path in filepaths])
        msg = f"The following file(s) in <b>{os.path.basename(start_dir)}</b> will be replaced: <ul>{pathlist}</ul>. Are you sure?"
        message_box = QMessageBox(
            QMessageBox.Question, "Replacing file(s)", msg, QMessageBox.Ok | QMessageBox.Cancel, parent=self
        )
        message_box.button(QMessageBox.Ok).setText("Replace")
        return message_box.exec_() != QMessageBox.Cancel

    @Slot(bool)
    def copy(self, checked=False):
        """Copies data to clipboard."""
        call_on_focused_widget(self, "copy")

    @Slot(bool)
    def paste(self, checked=False):
        """Pastes data from clipboard."""
        call_on_focused_widget(self, "paste")

    @Slot("QModelIndex", "QModelIndex")
    def _handle_current_resource_changed(self, current, _previous):
        """Resets resource data and schema models whenever a new resource is selected."""
        self.refresh_models(current)

    def refresh_models(self, current=None):
        if current is None:
            current = self.ui.tableView_resources.selectionModel().currentIndex()
        if current.column() != 0 or current.row() == self.selected_resource_index:
            return
        self.selected_resource_index = current.row()
        self.get_undo_stack(self.selected_resource_index).setActive()
        self.resource_data_model.refresh_model(self.selected_resource_index)
        self.fields_model.refresh_model(self.selected_resource_index)
        self.foreign_keys_model.refresh_model(self.selected_resource_index)
        self.ui.tableView_resource_data.resizeColumnsToContents()
        self.ui.tableView_fields.resizeColumnsToContents()
        self.ui.tableView_foreign_keys.resizeColumnsToContents()

    @Slot("QModelIndex", "QModelIndex", "QVector<int>")
    def _handle_fields_data_changed(self, top_left, bottom_right, roles):
        top, left = top_left.row(), top_left.column()
        bottom, right = bottom_right.row(), bottom_right.column()
        if left <= 0 <= right and Qt.DisplayRole in roles:
            # Fields name changed
            self.resource_data_model.headerDataChanged.emit(Qt.Horizontal, top, bottom)
            self.ui.tableView_resource_data.resizeColumnsToContents()
            self.foreign_keys_model.emit_data_changed()

    @Slot("QPoint")
    def show_foreign_keys_context_menu(self, pos):
        index = self.ui.tableView_foreign_keys.indexAt(pos)
        if not index.isValid() or index.row() == index.model().rowCount() - 1:
            return
        global_pos = self.ui.tableView_foreign_keys.viewport().mapToGlobal(pos)
        self._foreign_keys_context_menu.popup(global_pos)

    @Slot(bool)
    def _remove_foreign_key(self, checked=False):
        index = self.ui.tableView_foreign_keys.currentIndex()
        if not index.isValid():
            return
        index.model().call_remove_foreign_key(index.row())

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("dataPackageWidget/windowSize")
        window_pos = self.qsettings.value("dataPackageWidget/windowPosition")
        window_maximized = self.qsettings.value("dataPackageWidget/windowMaximized", defaultValue='false')
        window_state = self.qsettings.value("dataPackageWidget/windowState")
        n_screens = self.qsettings.value("mainWindow/n_screens", defaultValue=1)
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions

    def closeEvent(self, event=None):
        """Handle close event.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("dataPackageWidget/windowSize", self.size())
        self.qsettings.setValue("dataPackageWidget/windowPosition", self.pos())
        self.qsettings.setValue("dataPackageWidget/windowState", self.saveState(version=1))
        self.qsettings.setValue("dataPackageWidget/windowMaximized", self.windowState() == Qt.WindowMaximized)
        self.qsettings.setValue("dataPackageWidget/n_screens", len(QGuiApplication.screens()))
        if event:
            event.accept()


class CustomPackage(Package):
    """Custom datapackage class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._resource_data = [resource.read(cast=False) for resource in self.resources]

    @property
    def sources(self):
        return [r.source for r in self.resources]

    def set_resource_data(self, resource_index, row, column, value):
        self._resource_data[resource_index][row][column] = value

    def resource_data(self, resource_index):
        return self._resource_data[resource_index]

    def add_resource(self, descriptor):
        resource = super().add_resource(descriptor)
        self._resource_data.append(resource.read(cast=False))
        return resource

    def difference_infer(self, path):
        """Infers only what's *new* in the given path.

        Args:
            path (str)
        """
        current_resources = {r.source: r.name for r in self.resources}
        current_csv_files = set(glob.glob(path))
        old_resource_count = len(self.resources)
        new_resources = [
            self.add_resource({"path": csv_file}) for csv_file in current_csv_files - current_resources.keys()
        ]
        if not new_resources:
            return
        for k, resource in enumerate(new_resources):
            self.descriptor['resources'][old_resource_count + k] = resource.infer()
        self.commit()

    def check_resource_name(self, new_name):
        if not new_name:
            return "Resource name can't be empty."
        if new_name in self.resource_names:
            return f"A resource named {new_name} already exists."

    def rename_resource(self, index, new):
        self.descriptor['resources'][index]['name'] = new
        self.commit()

    def valid_field_names(self, resource_index, new_names):
        current_names = self.resources[resource_index].schema.field_names
        return [name for name in set(new_names).difference(current_names) if name]

    def rename_fields(self, resource_index, field_indexes, old_names, new_names):
        """Renames fields."""
        schema = self.descriptor['resources'][resource_index]['schema']
        for field_index, old, new in zip(field_indexes, old_names, new_names):
            schema['fields'][field_index]['name'] = new
            for i, field in enumerate(schema["primaryKey"]):
                if field == old:
                    schema['primaryKey'][i] = new
            for i, foreign_key in enumerate(schema["foreignKeys"]):
                for j, field in enumerate(foreign_key["fields"]):
                    if field == old:
                        schema['foreignKeys'][i]['fields'][j] = new
                for j, field in enumerate(foreign_key['reference']['fields']):
                    if field == old:
                        schema['foreignKeys'][i]['reference']['fields'][j] = new
        self.commit()

    def append_to_primary_key(self, resource_index, field_index):
        """Append field to resources's primary key."""
        schema = self.descriptor['resources'][resource_index]['schema']
        primary_key = schema.setdefault('primaryKey', [])
        field_name = schema["fields"][field_index]["name"]
        if field_name not in primary_key:
            primary_key.append(field_name)
        self.commit()

    def remove_from_primary_key(self, resource_index, field_index):
        """Remove field from resources's primary key."""
        schema = self.descriptor['resources'][resource_index]['schema']
        primary_key = schema.get('primaryKey')
        if not primary_key:
            return
        field_name = schema["fields"][field_index]["name"]
        if field_name in primary_key:
            primary_key.remove(field_name)
        self.commit()

    def check_foreign_key(self, resource_index, foreign_key):
        """Check foreign key."""
        resource = self.resources[resource_index]
        try:
            fields = foreign_key["fields"]
            reference = foreign_key["reference"]
        except KeyError as e:
            return f"{e} missing."
        try:
            reference_resource = reference["resource"]
            reference_fields = reference["fields"]
        except KeyError as e:
            return f"Reference {e} missing."
        if len(fields) != len(reference_fields):
            return "Both 'fields' and 'reference_fields' must have the same length."
        missing_fields = [fn for fn in fields if fn not in resource.schema.field_names]
        if missing_fields:
            return f"Fields {missing_fields} not in {resource.name}'s schema."
        reference_resource_obj = self.get_resource(reference_resource)
        if not reference_resource_obj:
            return f"Resource {reference_resource} not in datapackage"
        missing_ref_fields = [fn for fn in reference_fields if fn not in reference_resource_obj.schema.field_names]
        if missing_ref_fields:
            return f"Fields {missing_ref_fields} not in {reference_resource}'s schema."
        fks = self.descriptor['resources'][resource_index]['schema'].get('foreignKeys', [])
        if foreign_key in fks:
            return f"Foreign key already in {resource.name}'s schema."
        return None

    def append_foreign_key(self, resource_index, foreign_key):
        fks = self.descriptor['resources'][resource_index]['schema'].setdefault('foreignKeys', [])
        fks.append(foreign_key)
        self.commit()

    def insert_foreign_key(self, resource_index, fk_index, foreign_key):
        fks = self.descriptor['resources'][resource_index]['schema'].setdefault('foreignKeys', [])
        fks.insert(fk_index, foreign_key)
        self.commit()

    def update_foreign_key(self, resource_index, fk_index, foreign_key):
        fks = self.descriptor['resources'][resource_index]['schema'].get('foreignKeys', [])
        fks[fk_index] = foreign_key
        self.commit()

    def remove_foreign_key(self, resource_index, fk_index):
        self.descriptor['resources'][resource_index]['schema']['foreignKeys'].pop(fk_index)
        self.commit()

    def update_descriptor(self, descriptor_filepath):
        """Updates this package's schema from other package's."""
        if not os.path.isfile(descriptor_filepath):
            return
        other_datapackage = Package(descriptor_filepath, unsafe=True)
        for resource in self.descriptor["resources"]:
            other_resource = other_datapackage.get_resource(resource["name"])
            if other_resource is None:
                continue
            other_schema = other_resource.schema
            resource["schema"]["primaryKey"] = other_schema.primary_key
            resource["schema"]["foreignKeys"] = other_schema.foreign_keys
        self.commit()
