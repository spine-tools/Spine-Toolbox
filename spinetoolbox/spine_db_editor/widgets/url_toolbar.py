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
Contains the UrlToolBar class and helpers.

:author: M. Marin (KTH)
:date:   13.5.2020
"""
from PySide2.QtWidgets import QToolBar, QLineEdit, QMenu, QAction
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtCore import QSize, Qt, Slot
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
        self.reload_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_R))
        self._go_back_action.setEnabled(False)
        self._go_forward_action.setEnabled(False)
        self.reload_action.setEnabled(False)
        self._open_project_url_menu = self._add_open_project_url_menu()
        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText("Type the URL of a Spine DB")
        self._line_edit.returnPressed.connect(self._handle_line_edit_return_pressed)
        self.addWidget(self._line_edit)
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
        menu_button.setPopupMode(menu_button.InstantPopup)
        menu_button.setToolTip("<p>Open URL from project</p>")
        menu.aboutToShow.connect(self._update_open_project_url_menu)
        menu.triggered.connect(self._open_ds_url)
        slot = lambda *args: self._update_ds_url_menu_enabled()
        self._connect_project_item_model_signals(slot)
        self.destroyed.connect(lambda obj=None, slot=slot: self._disconnect_project_item_model_signals(slot))
        return menu

    def _update_ds_url_menu_enabled(self):
        ds_items = self._db_editor.toolbox.project_item_model.items("Data Stores")
        self._open_project_url_menu.setEnabled(bool(ds_items))

    def _connect_project_item_model_signals(self, slot):
        project_item_model = self._db_editor.toolbox.project_item_model
        project_item_model.modelReset.connect(slot)
        project_item_model.rowsRemoved.connect(slot)
        project_item_model.rowsInserted.connect(slot)

    def _disconnect_project_item_model_signals(self, slot):
        project_item_model = self._db_editor.toolbox.project_item_model
        project_item_model.modelReset.disconnect(slot)
        project_item_model.rowsRemoved.disconnect(slot)
        project_item_model.rowsInserted.disconnect(slot)

    @Slot()
    def _update_open_project_url_menu(self):
        toolbox = self._db_editor.toolbox
        self._open_project_url_menu.clear()
        ds_items = toolbox.project_item_model.items("Data Stores")
        self._project_urls = {ds.name: ds.project_item.sql_alchemy_url() for ds in ds_items}
        for name, url in self._project_urls.items():
            action = self._open_project_url_menu.addAction(name)
            action.setEnabled(bool(url))

    @Slot("QAction")
    def _open_ds_url(self, action):
        url = self._project_urls[action.text()]
        self._db_editor.load_db_urls({url: action.text()})

    def add_main_menu(self, menu):
        menu_action = self.addAction(QIcon(CharIconEngine("\uf0c9")), "")
        menu_action.setMenu(menu)
        menu_button = self.widgetForAction(menu_action)
        menu_button.setPopupMode(menu_button.InstantPopup)
        action = QAction(self)
        action.triggered.connect(menu_button.showMenu)
        keys = [QKeySequence(Qt.ALT + Qt.Key_F), QKeySequence(Qt.ALT + Qt.Key_E)]
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
        self._line_edit.setText("; ".join(urls))
