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

"""Contains the UrlToolBar class and helpers."""
from PySide6.QtWidgets import (
    QToolBar,
    QLineEdit,
    QMenu,
    QWidget,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QDialogButtonBox,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QToolButton,
)
from PySide6.QtGui import QIcon, QKeySequence, QAction
from PySide6.QtCore import QSize, Qt, Signal, Slot
from spinedb_api.filters.tools import (
    SCENARIO_FILTER_TYPE,
    filter_config,
    append_filter_config,
    filter_configs,
    name_from_dict,
    clear_filter_configs,
)
from spinetoolbox.helpers import CharIconEngine


class UrlToolBar(QToolBar):
    def __init__(self, db_editor):
        super().__init__(db_editor)
        self.setObjectName("spine_db_editor_url_toolbar")
        self._db_editor = db_editor
        self._history = []
        self._history_index = -1
        self._project_urls = {}
        self._go_back_action = self.addAction(QIcon(CharIconEngine("\uf060")), "Go back", db_editor.load_previous_urls)
        self._go_forward_action = self.addAction(
            QIcon(CharIconEngine("\uf061")), "Go forward", db_editor.load_next_urls
        )
        self.reload_action = self.addAction(QIcon(CharIconEngine("\uf021")), "Reload", db_editor.refresh_session)
        self.reload_action.setShortcut(QKeySequence(Qt.Modifier.CTRL.value | Qt.Key.Key_R.value))
        self._go_back_action.setEnabled(False)
        self._go_forward_action.setEnabled(False)
        self.reload_action.setEnabled(False)
        self._open_project_url_menu = self._add_open_project_url_menu()
        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText("Type the URL of a Spine DB")
        self._line_edit.returnPressed.connect(self._handle_line_edit_return_pressed)
        self._filter_action = self._line_edit.addAction(QIcon(CharIconEngine("\uf0b0")), QLineEdit.TrailingPosition)
        self._filter_action.triggered.connect(self._show_filter_menu)
        self.addWidget(self._line_edit)
        toolbox_icon = QIcon(":/symbols/Spine_symbol.png")
        self.show_toolbox_action = self.addAction(toolbox_icon, "Show Spine Toolbox (Ctrl+ESC)")
        self.show_toolbox_action.setShortcut(QKeySequence(Qt.Modifier.CTRL.value | Qt.Key.Key_Escape.value))
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

    @property
    def line_edit(self):
        return self._line_edit

    def _add_open_project_url_menu(self):
        toolbox = self._db_editor.toolbox
        if toolbox is None:
            return None
        menu = QMenu(self)
        menu_action = self.addAction(QIcon(CharIconEngine("\uf1c0")), "")
        menu_action.setMenu(menu)
        menu_button = self.widgetForAction(menu_action)
        menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu_button.setToolTip("<p>Open URL from project</p>")
        menu.aboutToShow.connect(self._update_open_project_url_menu)
        menu.triggered.connect(self._open_ds_url)
        return menu

    @Slot()
    def _update_open_project_url_menu(self):
        self._open_project_url_menu.clear()
        ds_items = self._db_editor.toolbox.project().get_items_by_type("Data Store")
        self._project_urls = {ds.name: ds.sql_alchemy_url() for ds in ds_items}
        is_url_validated = {ds.name: ds.is_url_validated() for ds in ds_items}
        for name, url in self._project_urls.items():
            action = self._open_project_url_menu.addAction(name)
            action.setEnabled(url is not None and is_url_validated[name])

    @Slot(QAction)
    def _open_ds_url(self, action):
        url = self._project_urls[action.text()]
        self._db_editor.db_mngr.open_db_editor({url: action.text()}, True)

    def add_main_menu(self, menu):
        menu_action = self.addAction(QIcon(CharIconEngine("\uf0c9")), "")
        menu_action.setMenu(menu)
        menu_button = self.widgetForAction(menu_action)
        menu_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        action = QAction(self)
        action.triggered.connect(menu_button.showMenu)
        keys = [
            QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_F.value),
            QKeySequence(Qt.Modifier.ALT.value | Qt.Key.Key_E.value),
        ]
        action.setShortcuts(keys)
        keys_str = ", ".join([key.toString() for key in keys])
        menu_button.setToolTip(f"<p>Customize and control Spine DB Editor ({keys_str})</p>")
        return action

    def _update_history_actions_availability(self):
        self._go_back_action.setEnabled(self._history_index > 0)
        self._go_forward_action.setEnabled(self._history_index < len(self._history) - 1)

    def add_urls_to_history(self, db_urls):
        """Adds url to history.

        Args:
            db_urls (list of str)
        """
        self._history_index += 1
        self._update_history_actions_availability()
        self._history[self._history_index :] = [db_urls]

    def get_previous_urls(self):
        """Returns previous urls in history.

        Returns:
            list of str
        """
        self._history_index -= 1
        self._update_history_actions_availability()
        return self._history[self._history_index]

    def get_next_urls(self):
        """Returns next urls in history.

        Returns:
            list of str
        """
        self._history_index += 1
        self._update_history_actions_availability()
        return self._history[self._history_index]

    def _handle_line_edit_return_pressed(self):
        urls = [url.strip() for url in self._line_edit.text().split(";")]
        self._db_editor.load_db_urls({url: None for url in urls}, create=True)

    def set_current_urls(self, urls):
        filtered = any(filter_configs(url) for url in urls)
        color = Qt.magenta if filtered else None
        self._filter_action.setIcon(QIcon(CharIconEngine("\uf0b0", color=color)))
        self._line_edit.setText("; ".join(urls))

    @Slot(bool)
    def _show_filter_menu(self, _checked=False):
        global_pos = self.mapToGlobal(self.pos())
        dialog = _UrlFilterDialog(self._db_editor.db_mngr, self._db_editor.db_maps, parent=self)
        dialog.show()
        p = global_pos + self._line_edit.frameGeometry().bottomRight()
        dialog.move(p.x() - dialog.width(), p.y())
        dialog.filter_accepted.connect(self._db_editor.load_db_urls)


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
