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

"""Contains the DBEditorToolBar class and helpers."""
from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtGui import QAction, QIcon, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTextEdit,
    QToolBar,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)
from spinedb_api.filters.tools import (
    SCENARIO_FILTER_TYPE,
    append_filter_config,
    clear_filter_configs,
    filter_config,
    filter_configs,
    name_from_dict,
)
from spinetoolbox.helpers import CharIconEngine, add_keyboard_shortcut_to_tool_tip, plain_to_tool_tip


class DBEditorToolBar(QToolBar):
    def __init__(self, db_editor):
        super().__init__(db_editor)
        self.setObjectName("spine_db_editor_toolbar")
        self._db_editor = db_editor
        self.reload_action = QAction(QIcon(CharIconEngine("\uf021")), "Reload")
        self.reload_action.setToolTip("Reload data from database keeping changes")
        self.reload_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_R))
        add_keyboard_shortcut_to_tool_tip(self.reload_action)
        self.reload_action.setEnabled(False)
        self.reset_docks_action = QAction(QIcon(CharIconEngine("\uf2d2")), "Reset docks")
        self.reset_docks_action.setToolTip(plain_to_tool_tip("Reset window back to default configuration<"))
        self.show_toolbox_action = QAction(QIcon(":/symbols/Spine_symbol.png"), "Show Toolbox")
        self.show_toolbox_action.setShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Escape))
        self.show_toolbox_action.setToolTip("Show Spine Toolbox window")
        add_keyboard_shortcut_to_tool_tip(self.show_toolbox_action)
        self._filter_action = QAction(QIcon(CharIconEngine("\uf0b0")), "Filter")
        self._filter_action.setToolTip(plain_to_tool_tip("Set DB API level scenario filters<"))
        self.show_url_action = QAction(QIcon(CharIconEngine("\uf550")), "Show URLs")
        self.show_url_action.setToolTip(plain_to_tool_tip("Show URLs of currently databases in the session"))
        self._add_actions()
        self._connect_signals()
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

    def _add_actions(self):
        """Creates buttons for the actions and adds them to the toolbar"""
        self.create_button_for_action(self._db_editor.ui.actionNew_db_file)
        self.create_button_for_action(self._db_editor.ui.actionAdd_db_file)
        self.create_button_for_action(self._db_editor.ui.actionOpen_db_file)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionUndo)
        self.create_button_for_action(self._db_editor.ui.actionRedo)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionCommit)
        self.create_button_for_action(self._db_editor.ui.actionMass_remove_items)
        self.create_button_for_action(self.reload_action)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionStacked_style)
        self.create_button_for_action(self._db_editor.ui.actionGraph_style)
        self.addSeparator()
        self.create_button_for_action(self._db_editor.ui.actionValue)
        self.create_button_for_action(self._db_editor.ui.actionIndex)
        self.create_button_for_action(self._db_editor.ui.actionElement)
        self.create_button_for_action(self._db_editor.ui.actionScenario)
        self.addSeparator()
        self.create_button_for_action(self.reset_docks_action)
        self.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(spacer)
        self.addSeparator()
        self.create_button_for_action(self.show_url_action)
        self.create_button_for_action(self._filter_action)
        self.addSeparator()
        self.create_button_for_action(self.show_toolbox_action)

    def _connect_signals(self):
        """Connects signals"""
        self.reload_action.triggered.connect(self._db_editor.refresh_session)
        self.reset_docks_action.triggered.connect(self._db_editor.reset_docks)
        self.show_url_action.triggered.connect(self._show_url_codename_widget)
        self._filter_action.triggered.connect(self._show_filter_menu)

    def create_button_for_action(self, action):
        """Creates a button for the given action and adds it to the widget"""
        tool_button = QToolButton()
        tool_button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        tool_button.setPopupMode(QToolButton.InstantPopup)
        tool_button.setDefaultAction(action)
        self.addWidget(tool_button)

    def _show_url_codename_widget(self):
        """Shows the url codename widget"""
        dialog = _URLDialog(self._db_editor.db_url_codenames, parent=self)
        dialog.show()

    @Slot(bool)
    def _show_filter_menu(self, _checked=False):
        """Shows the filter menu"""
        dialog = _UrlFilterDialog(self._db_editor.db_mngr, self._db_editor.db_maps, parent=self)
        dialog.show()
        dialog.filter_accepted.connect(self._db_editor.load_db_urls)
        dialog.filter_accepted.connect(self.set_filter_action_icon_color)

    def set_filter_action_icon_color(self, codenames):
        filtered = any(filter_configs(url) for url in codenames.keys())
        color = Qt.magenta if filtered else None
        self._filter_action.setIcon(QIcon(CharIconEngine("\uf0b0", color=color)))


class _FilterWidget(QTreeWidget):
    def __init__(self, db_mngr, db_map, item_type, filter_type, active_item, parent=None):
        super().__init__(parent=parent)
        self._filter_type = filter_type
        self.setIndentation(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHeaderLabel(filter_type)
        items = db_mngr.get_items(db_map, item_type)
        top_level_items = [QTreeWidgetItem([x["name"]]) for x in items]
        self.addTopLevelItems(top_level_items)
        self.resizeColumnToContents(0)
        current = next(iter(item for item in top_level_items if item.text(0) == active_item), None)
        if current is not None:
            self.setCurrentItem(current)

    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(self.header().sectionSize(0) + self.frameWidth() * 2 + 2)
        return size

    def filter_config(self):
        selected = self.selectedItems()
        if not selected:
            return {}
        return filter_config(self._filter_type, selected[0].text(0))


class _FilterArrayWidget(QWidget):
    filter_selection_changed = Signal()

    def __init__(self, db_mngr, db_map, parent=None):
        super().__init__(parent=parent)
        layout = QHBoxLayout(self)
        self._offset = 0
        self._db_map = db_map
        self._filter_widgets = []
        active_filter_configs = {cfg["type"]: cfg for cfg in filter_configs(db_map.db_url)}
        for item_type, filter_type in (("scenario", SCENARIO_FILTER_TYPE),):
            active_cfg = active_filter_configs.get(filter_type, {})
            active_item = name_from_dict(active_cfg) if active_cfg else None
            filter_widget = _FilterWidget(db_mngr, db_map, item_type, filter_type, active_item, parent=self)
            layout.addWidget(filter_widget)
            self._filter_widgets.append(filter_widget)
            filter_widget.itemSelectionChanged.connect(self.filter_selection_changed)

    def filtered_url_codename(self):
        url = clear_filter_configs(self._db_map.db_url)
        for filter_widget in self._filter_widgets:
            filter_config_ = filter_widget.filter_config()
            if not filter_config_:
                continue
            url = append_filter_config(url, filter_config_)
        return url, self._db_map.codename

    def sizeHint(self):
        size = super().sizeHint()
        size.setWidth(size.width() - self._offset)
        return size

    def moveEvent(self, ev):
        if ev.pos().x() > 0:
            margin = 2
            self._offset = ev.pos().x() - margin
            self.move(margin, ev.pos().y())
            self.adjustSize()
            return
        super().moveEvent(ev)


class _DBListWidget(QTreeWidget):
    db_filter_selection_changed = Signal()

    def __init__(self, db_mngr, db_maps, parent=None):
        super().__init__(parent=parent)
        self.header().hide()
        self._filter_arrays = []
        for db_map in db_maps:
            top_level_item = QTreeWidgetItem([db_map.codename])
            self.addTopLevelItem(top_level_item)
            child = QTreeWidgetItem()
            top_level_item.addChild(child)
            filter_array = _FilterArrayWidget(db_mngr, db_map, parent=self)
            self.setItemWidget(child, 0, filter_array)
            self._filter_arrays.append(filter_array)
            top_level_item.setExpanded(True)
            filter_array.filter_selection_changed.connect(self.db_filter_selection_changed)
        self.resizeColumnToContents(0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def sizeHint(self):
        size = super().sizeHint()
        last = self.topLevelItem(self.topLevelItemCount() - 1)
        last_child = self.itemBelow(last)
        rect = self.visualItemRect(last_child)
        size.setWidth(rect.right() + 2 * self.frameWidth() + 2)
        size.setHeight(rect.bottom() + 2 * self.frameWidth() + 2)
        return size

    def filtered_url_codenames(self):
        return dict(filter_array.filtered_url_codename() for filter_array in self._filter_arrays)


class _UrlFilterDialog(QDialog):
    filter_accepted = Signal(dict)

    def __init__(self, db_mngr, db_maps, parent=None):
        super().__init__(parent=parent, f=Qt.Popup)
        outer_layout = QVBoxLayout(self)
        button_box = QDialogButtonBox(self)
        self._filter_button = button_box.addButton("Update filters", QDialogButtonBox.ButtonRole.AcceptRole)
        self._db_list = _DBListWidget(db_mngr, db_maps, parent=self)
        self._orig_filtered_url_codenames = self._db_list.filtered_url_codenames()
        self._update_filter_enabled()
        outer_layout.addWidget(QLabel("Select URL filters"))
        outer_layout.addWidget(self._db_list)
        outer_layout.addWidget(button_box)
        button_box.accepted.connect(self.accept)
        self._db_list.db_filter_selection_changed.connect(self._update_filter_enabled)
        self.adjustSize()

    def sizeHint(self):
        size = super().sizeHint()
        return size

    def _update_filter_enabled(self):
        self._filter_button.setEnabled(self._orig_filtered_url_codenames != self._db_list.filtered_url_codenames())

    def accept(self):
        super().accept()
        self.filter_accepted.emit(self._db_list.filtered_url_codenames())


class _URLDialog(QDialog):
    """Class for showing URLs and codenames in the database"""

    def __init__(self, url_codenames, parent=None):
        super().__init__(parent=parent, f=Qt.Popup)
        self.textEdit = QTextEdit(self)
        self.textEdit.setObjectName("textEdit")
        text = "<br>".join([f"<b>{codename}</b>: {url}" for url, codename in url_codenames.items()])
        self.textEdit.setHtml(text)
        self.textEdit.setReadOnly(True)
        self.textEdit.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.textEdit.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.textEdit.setLineWrapMode(QTextEdit.NoWrap)
        layout = QVBoxLayout(self)
        layout.addWidget(self.textEdit)
        self.setLayout(layout)
        self.resize(500, 200)

    def showEvent(self, event):
        super().showEvent(event)
        self.textEdit.moveCursor(QTextCursor.Start)
        self.textEdit.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key_Return,
            Qt.Key_Escape,
            Qt.Key_Enter,
        ):
            self.close()
