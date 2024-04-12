######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains PluginManager dialogs and widgets."""
from PySide6.QtCore import Qt, Slot, Signal, QSortFilterProxyModel, QTimer, QSize
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QListView, QDialogButtonBox
from PySide6.QtGui import QStandardItemModel, QStandardItem
from .custom_qwidgets import ToolBarWidget


class _InstallPluginModel(QStandardItemModel):
    def data(self, index, role=None):
        if role == Qt.SizeHintRole:
            return QSize(0, 40)
        return super().data(index, role)


class _ManagePluginsModel(_InstallPluginModel):
    def flags(self, index):
        return super().flags(index) & ~Qt.ItemIsSelectable


class InstallPluginDialog(QDialog):
    item_selected = Signal(str)

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowTitle("Install plugin")
        QVBoxLayout(self)
        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText("Search registry...")
        self._list_view = QListView(self)
        self._model = QSortFilterProxyModel(self)
        self._source_model = _InstallPluginModel(self)
        self._model.setSourceModel(self._source_model)
        self._model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._list_view.setModel(self._model)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        self.layout().addWidget(self._line_edit)
        self.layout().addWidget(self._list_view)
        self.layout().addWidget(self._button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(400)
        self._button_box.button(QDialogButtonBox.StandardButton.Cancel).clicked.connect(self.close)
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).clicked.connect(self._handle_ok_clicked)
        self._list_view.doubleClicked.connect(self._emit_item_selected)
        self._list_view.selectionModel().selectionChanged.connect(self._update_ok_button_enabled)
        self._line_edit.textEdited.connect(self._handle_search_text_changed)
        self._timer.timeout.connect(self._filter_model)

    def populate_list(self, names):
        for name in names:
            self._source_model.appendRow(QStandardItem(name))

    @Slot(str)
    def _handle_search_text_changed(self, _text):
        self._timer.start()

    def _filter_model(self):
        self._model.setFilterRegularExpression(self._line_edit.text())

    @Slot(bool)
    def _handle_ok_clicked(self, _=False):
        index = self._list_view.currentIndex()
        self._emit_item_selected(index)

    @Slot("QModelIndex")
    def _emit_item_selected(self, index):
        if not index.isValid():
            return
        self.item_selected.emit(index.data(Qt.ItemDataRole.DisplayRole))
        self.close()

    @Slot("QItemSelection", "QItemSelection")
    def _update_ok_button_enabled(self, _selected, _deselected):
        on = self._list_view.selectionModel().hasSelection()
        self._button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(on)


class ManagePluginsDialog(QDialog):
    item_removed = Signal(str)
    item_updated = Signal(str)

    def __init__(self, parent):
        """Initialize class"""
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowTitle("Manage plugins")
        QVBoxLayout(self)
        self._list_view = QListView(self)
        self._model = _ManagePluginsModel(self)
        self._list_view.setModel(self._model)
        self._button_box = QDialogButtonBox(self)
        self._button_box.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        self.layout().addWidget(self._list_view)
        self.layout().addWidget(self._button_box)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(400)
        self._button_box.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.close)

    def populate_list(self, names):
        for name, can_update in names:
            item = QStandardItem(name)
            self._model.appendRow(item)
            widget = self._create_plugin_widget(name, can_update)
            index = self._model.indexFromItem(item)
            self._list_view.setIndexWidget(index, widget)

    def _create_plugin_widget(self, plugin_name, can_update):
        widget = ToolBarWidget(plugin_name, self)
        widget.tool_bar.addAction("Remove", lambda _=False, n=plugin_name: self._emit_item_removed(n))
        update = widget.tool_bar.addAction("Update", lambda _=False, n=plugin_name: self._emit_item_updated(n))
        update.setEnabled(can_update)
        update.triggered.connect(lambda _=False: update.setEnabled(False))
        return widget

    def _emit_item_removed(self, plugin_name):
        for row in range(self._model.rowCount()):
            if self._model.index(row, 0).data(Qt.ItemDataRole.DisplayRole) == plugin_name:
                self._model.removeRow(row)
                break
        self.item_removed.emit(plugin_name)

    def _emit_item_updated(self, plugin_name):
        self.item_updated.emit(plugin_name)
