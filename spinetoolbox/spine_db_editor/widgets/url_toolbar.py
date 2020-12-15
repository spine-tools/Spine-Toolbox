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
Classes for custom context menus and pop-up menus.

:author: M. Marin (KTH)
:date:   13.5.2020
"""
from PySide2.QtWidgets import QToolBar, QLineEdit, QMenu
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtCore import QSize, Qt
from spinetoolbox.helpers import CharIconEngine


class UrlToolBar(QToolBar):
    def __init__(self, db_editor):
        super().__init__(db_editor)
        self.setObjectName("spine_db_editor_url_toolbar")
        self._db_editor = db_editor
        self._history = []
        self._history_index = -1
        self._go_back_action = self.addAction(QIcon(CharIconEngine("\uf060")), "Go back", db_editor.load_previous_urls)
        self._go_forward_action = self.addAction(
            QIcon(CharIconEngine("\uf061")), "Go forward", db_editor.load_next_urls
        )
        self.reload_action = self.addAction(QIcon(CharIconEngine("\uf021")), "Reload", db_editor.refresh_session)
        self.reload_action.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_R))
        self._go_back_action.setEnabled(False)
        self._go_forward_action.setEnabled(False)
        self._line_edit = QLineEdit(self)
        self._line_edit.returnPressed.connect(self._handle_line_edit_return_pressed)
        self.addWidget(self._line_edit)
        self.addAction(QIcon(CharIconEngine("\uf15b")), "New database file...", db_editor.create_db_file)
        self.addAction(QIcon(CharIconEngine("\uf07c")), "Open database file...", db_editor.open_db_file)
        self.addSeparator()
        self._add_menu()
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

    def _add_menu(self):
        menu = QMenu(self)
        menu.addMenu(self._db_editor.ui.menuSession)
        menu.addMenu(self._db_editor.ui.menuFile)
        menu.addMenu(self._db_editor.ui.menuEdit)
        menu.addMenu(self._db_editor.ui.menuView)
        menu.addMenu(self._db_editor.ui.menuPivot_table)
        menu.addMenu(self._db_editor.ui.menuGraph)
        menu.addSeparator()
        menu.addAction(self._db_editor.ui.actionUser_guide)
        menu.addAction(self._db_editor.ui.actionSettings)
        menu_action = self.addAction(QIcon(CharIconEngine("\uf0c9")), "menu")
        menu_action.setMenu(menu)
        menu_button = self.widgetForAction(menu_action)
        menu_button.setPopupMode(menu_button.InstantPopup)
        menu_button.setToolTip("<p>Customize and control Spine DB Editor</p>")

    def _update_history_actions_availability(self):
        self._go_back_action.setEnabled(self._history_index > 0)
        self._go_forward_action.setEnabled(self._history_index < len(self._history) - 1)

    def add_urls_to_history(self, db_urls):
        self._history_index += 1
        self._update_history_actions_availability()
        self._history[self._history_index :] = [db_urls]

    def get_previous_urls(self):
        self._history_index -= 1
        self._update_history_actions_availability()
        return self._history[self._history_index]

    def get_next_urls(self):
        self._history_index += 1
        self._update_history_actions_availability()
        return self._history[self._history_index]

    def _handle_line_edit_return_pressed(self):
        urls = [url.strip() for url in self._line_edit.text().split(";")]
        self._db_editor.load_db_urls({url: None for url in urls}, create=True)

    def set_current_urls(self, urls):
        self._line_edit.setText("; ".join(urls))
