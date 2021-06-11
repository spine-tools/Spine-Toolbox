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
Contains the MultiSpineDBEditor class.

:author: M. Marin (KTH)
:date:   12.12.2020
"""

import os
from PySide2.QtWidgets import QToolBar, QWidget, QSizePolicy, QMenu
from PySide2.QtCore import Qt, Slot, QPoint, QSize
from PySide2.QtGui import QIcon
from .spine_db_editor import SpineDBEditor
from .custom_qwidgets import ShootingLabel, OpenFileButton, OpenSQLiteFileButton
from ...widgets.multi_tab_window import MultiTabWindow
from ...helpers import CharIconEngine, open_url
from ...config import ONLINE_DOCUMENTATION_URL
from ...widgets.settings_widget import SpineDBEditorSettingsWidget


class MultiSpineDBEditor(MultiTabWindow):
    def __init__(self, db_mngr, db_url_codenames=None):
        super().__init__(db_mngr.qsettings, "spineDBEditor")
        self.db_mngr = db_mngr
        self.settings_form = SpineDBEditorSettingsWidget(self)
        self.setWindowTitle("Spine DB Editor")
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self._file_open_toolbar = _FileOpenToolBar(self)
        self._file_open_toolbar.hide()
        self.addToolBar(Qt.BottomToolBarArea, self._file_open_toolbar)
        if db_url_codenames is not None:
            self.add_new_tab(db_url_codenames)

    def _make_other(self):
        return MultiSpineDBEditor(self.db_mngr)

    def others(self):
        return [w for w in self.db_mngr.get_all_multi_spine_db_editors() if w is not self]

    def _connect_tab_signals(self, tab):
        if not super()._connect_tab_signals(tab):
            return False
        tab.file_exported.connect(self.insert_file_open_button)
        tab.sqlite_file_exported.connect(self.insert_sqlite_file_open_button)
        tab.ui.actionUser_guide.triggered.connect(self.show_user_guide)
        tab.ui.actionSettings.triggered.connect(self.settings_form.show)
        return True

    def _disconnect_tab_signals(self, index):
        if not super()._disconnect_tab_signals(index):
            return False
        tab = self.tab_widget.widget(index)
        tab.file_exported.disconnect(self.insert_file_open_button)
        tab.sqlite_file_exported.disconnect(self.insert_sqlite_file_open_button)
        tab.ui.actionUser_guide.triggered.disconnect(self.show_user_guide)
        tab.ui.actionSettings.triggered.disconnect(self.settings_form.show)
        return True

    def _make_new_tab(self, db_url_codenames=None):  # pylint: disable=arguments-differ
        tab = SpineDBEditor(self.db_mngr)
        tab.load_db_urls(db_url_codenames, create=True)
        return tab

    def show_plus_button_context_menu(self, global_pos):
        toolbox = self.db_mngr.parent()
        if toolbox is None:
            return
        ds_urls = {ds.name: ds.project_item.sql_alchemy_url() for ds in toolbox.project_item_model.items("Data Stores")}
        if not ds_urls:
            return
        menu = QMenu(self)
        for name, url in ds_urls.items():
            action = menu.addAction(name, lambda name=name, url=url: self.add_new_tab({url: name}))
            action.setEnabled(bool(url))
        menu.popup(global_pos)
        menu.aboutToHide.connect(menu.deleteLater)

    def make_context_menu(self, index):
        menu = super().make_context_menu(index)
        if menu is None:
            return None
        tab = self.tab_widget.widget(index)
        menu.addSeparator()
        menu.addAction(tab.url_toolbar.reload_action)
        db_url_codenames = tab.db_url_codenames
        menu.addAction(
            QIcon(CharIconEngine("\uf24d")),
            "Duplicate",
            lambda _=False, index=index + 1, db_url_codenames=db_url_codenames: self.insert_new_tab(
                index, db_url_codenames
            ),
        )
        return menu

    def _insert_statusbar_button(self, button):
        """Inserts given button to the 'beginning' of the status bar and decorates it with a shooting label.

        Args:
            button (OpenFileButton)
        """
        duplicates = [
            x
            for x in self._file_open_toolbar.findChildren(OpenFileButton)
            if os.path.samefile(x.file_path, button.file_path)
        ]
        for dup in duplicates:
            self._file_open_toolbar.remove_widget(dup)
        self._file_open_toolbar.preppend_widget(button)
        self._file_open_toolbar.show()
        destination = QPoint(16, 0) + button.mapTo(self, QPoint(0, 0))
        label = ShootingLabel(destination - QPoint(0, 64), destination, self)
        pixmap = QIcon(":/icons/file-download.svg").pixmap(32, 32)
        label.setPixmap(pixmap)
        label.show()

    @Slot(str)
    def insert_sqlite_file_open_button(self, file_path):
        button = OpenSQLiteFileButton(file_path, self)
        self._insert_statusbar_button(button)

    @Slot(str)
    def insert_file_open_button(self, file_path):
        button = OpenFileButton(file_path, self)
        self._insert_statusbar_button(button)

    def _open_sqlite_url(self, url, codename):
        """Opens sqlite url."""
        self.add_new_tab({url: codename})

    @Slot(bool)
    def show_user_guide(self, checked=False):
        """Opens Spine db editor documentation page in browser."""
        doc_url = f"{ONLINE_DOCUMENTATION_URL}/spine_db_editor/index.html"
        if not open_url(doc_url):
            self.msg_error.emit("Unable to open url <b>{0}</b>".format(doc_url))


class _FileOpenToolBar(QToolBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("multi_spine_db_editor_file_open_toolbar")
        empty = QWidget()
        empty.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(empty)
        self.addAction(QIcon(CharIconEngine("\uf00d")), "Close", self.hide)
        self.setMovable(False)
        self.setIconSize(QSize(20, 20))

    def preppend_widget(self, widget):
        first_action = next(iter(self.actions()), None)
        if first_action:
            self.insertWidget(first_action, widget)
        else:
            self.addWidget(widget)

    def remove_widget(self, widget):
        action = next(iter(a for a in self.actions() if self.widgetForAction(a) is widget), None)
        if action:
            self.removeAction(action)
