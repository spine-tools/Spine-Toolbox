######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
"""

import os
from PySide6.QtWidgets import QMessageBox, QMenu, QStatusBar, QToolButton
from PySide6.QtCore import Slot, QPoint
from PySide6.QtGui import QIcon, QFont
from .spine_db_editor import SpineDBEditor
from .custom_qwidgets import ShootingLabel, OpenFileButton, OpenSQLiteFileButton
from ...widgets.multi_tab_window import MultiTabWindow
from ...helpers import CharIconEngine, open_url
from ...config import ONLINE_DOCUMENTATION_URL
from ...widgets.settings_widget import SpineDBEditorSettingsWidget
from ...config import MAINWINDOW_SS


class MultiSpineDBEditor(MultiTabWindow):
    """Database editor's tabbed main window."""

    def __init__(self, db_mngr, db_url_codenames=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_url_codenames (dict, optional): mapping from database URL to its codename
        """
        super().__init__(db_mngr.qsettings, "spineDBEditor")
        self.db_mngr = db_mngr
        self.db_mngr.waiting_for_fetcher.connect(self._show_waiting_for_fetcher)
        self.db_mngr.fetcher_waiting_over.connect(self._close_waiting_for_fetcher)
        self._waiting_box = None
        self.settings_form = SpineDBEditorSettingsWidget(self)
        self.setStyleSheet(MAINWINDOW_SS)
        self.setWindowTitle("Spine DB Editor")
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStatusBar(_CustomStatusBar(self))
        self.statusBar().hide()
        if db_url_codenames is not None:
            self.add_new_tab(db_url_codenames)

    def _make_other(self):
        return MultiSpineDBEditor(self.db_mngr)

    def _connect_tab_signals(self, tab):
        """Connects Spine Db editor window (tab) signals.

        Args:
            tab (SpineDBEditor): Spine Db editor window

        Returns:
            bool: True if ok, False otherwise
        """
        if not super()._connect_tab_signals(tab):
            return False
        tab.file_exported.connect(self.insert_file_open_button)
        tab.sqlite_file_exported.connect(self.insert_sqlite_file_open_button)
        tab.ui.actionUser_guide.triggered.connect(self.show_user_guide)
        tab.ui.actionSettings.triggered.connect(self.settings_form.show)
        tab.ui.actionClose.triggered.connect(self.handle_close_request_from_tab)
        return True

    def _disconnect_tab_signals(self, index):
        """Disconnects signals of Spine Db editor window (tab) in given index.

        Args:
            index (int): Tab index

        Returns:
            bool: True if ok, False otherwise
        """
        if not super()._disconnect_tab_signals(index):
            return False
        tab = self.tab_widget.widget(index)
        tab.file_exported.disconnect(self.insert_file_open_button)
        tab.sqlite_file_exported.disconnect(self.insert_sqlite_file_open_button)
        tab.ui.actionUser_guide.triggered.disconnect(self.show_user_guide)
        tab.ui.actionSettings.triggered.disconnect(self.settings_form.show)
        tab.ui.actionClose.triggered.disconnect(self.handle_close_request_from_tab)
        return True

    def _make_new_tab(self, db_url_codenames=None):  # pylint: disable=arguments-differ
        tab = SpineDBEditor(self.db_mngr)
        tab.load_db_urls(db_url_codenames, create=True)
        return tab

    def show_plus_button_context_menu(self, global_pos):
        toolbox = self.db_mngr.parent()
        if toolbox is None:
            return
        data_stores = tuple(ds_item.project_item for ds_item in toolbox.project_item_model.items("Data Stores"))
        ds_urls = {ds.name: ds.sql_alchemy_url() for ds in data_stores}
        is_url_validated = {ds.name: ds.is_url_validated() for ds in data_stores}
        if not ds_urls:
            return
        menu = QMenu(self)
        for name, url in ds_urls.items():
            action = menu.addAction(name, lambda name=name, url=url: self.add_new_tab({url: name}))
            action.setEnabled(url is not None and is_url_validated[name])
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
            x for x in self.statusBar().findChildren(OpenFileButton) if os.path.samefile(x.file_path, button.file_path)
        ]
        for dup in duplicates:
            self.statusBar().removeWidget(dup)
            dup.deleteLater()
        self.statusBar().insertWidget(0, button)
        self.statusBar().show()
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

    @Slot()
    def _show_waiting_for_fetcher(self):
        """Shows a message box to user informing that a tab is waiting for fetcher to finish working."""
        if self._waiting_box is not None:
            return
        self._waiting_box = QMessageBox(
            QMessageBox.Information,
            "Closing database",
            "Waiting for database to close...",
            QMessageBox.StandardButton.Ok,
            parent=self,
        )
        self._waiting_box.button(QMessageBox.StandardButton.Ok).setText("I wait patiently")
        self._waiting_box.open()

    @Slot()
    def _close_waiting_for_fetcher(self):
        if self._waiting_box is None:
            return
        self._waiting_box.close()
        self._waiting_box.deleteLater()
        self._waiting_box = None


class _CustomStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContentsMargins(0, 0, 4, 0)
        self._hide_button = QToolButton()
        self._hide_button.setStyleSheet(
            """
            QToolButton {
                background-color: transparent;
                border: 0px;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #dddddd;
            }
            QToolButton:pressed {
                background-color: #bbbbbb;
            }
            """
        )
        self._hide_button.setText("\uf00d")
        self._hide_button.setFont(QFont('Font Awesome 5 Free Solid'))
        self._hide_button.setFixedSize(24, 24)
        self.insertPermanentWidget(0, self._hide_button)
        self.setSizeGripEnabled(False)
        self._hide_button.clicked.connect(self.hide)
