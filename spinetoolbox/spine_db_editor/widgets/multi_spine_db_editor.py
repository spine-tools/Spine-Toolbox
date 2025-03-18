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

"""Contains the MultiSpineDBEditor class."""
import os
from PySide6.QtCore import QPoint, Slot
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QMenu, QStatusBar, QToolButton
from ...config import MAINWINDOW_SS, ONLINE_DOCUMENTATION_URL
from ...font import TOOLBOX_FONT
from ...helpers import CharIconEngine, open_url
from ...widgets.multi_tab_window import MultiTabWindow
from ...widgets.settings_widget import SpineDBEditorSettingsWidget
from ..editors import db_editor_registry
from .custom_qwidgets import OpenFileButton, OpenSQLiteFileButton, ShootingLabel
from .spine_db_editor import SpineDBEditor


class MultiSpineDBEditor(MultiTabWindow):
    """Database editor's tabbed main window."""

    def __init__(self, db_mngr, db_urls=None):
        """
        Args:
            db_mngr (SpineDBManager): database manager
            db_urls (Iterable of str, optional): URLs of database to load
        """
        super().__init__(db_mngr.qsettings, "spineDBEditor")
        self.db_mngr = db_mngr
        self._waiting_box = None
        self.settings_form = SpineDBEditorSettingsWidget(self)
        self.setStyleSheet(MAINWINDOW_SS)
        self.setWindowTitle("Spine DB Editor")
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self.setStatusBar(_CustomStatusBar(self))
        self.statusBar().hide()
        self.tab_load_success = True
        if db_urls is not None:
            if not self.add_new_tab(db_urls):
                self.tab_load_success = False
        db_editor_registry.register_window(self)

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
        tab.file_exported.connect(self.insert_open_file_button)
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
        tab.file_exported.disconnect(self.insert_open_file_button)
        tab.ui.actionUser_guide.triggered.disconnect(self.show_user_guide)
        tab.ui.actionSettings.triggered.disconnect(self.settings_form.show)
        tab.ui.actionClose.triggered.disconnect(self.handle_close_request_from_tab)
        return True

    def _make_new_tab(self, db_urls=None):  # pylint: disable=arguments-differ
        """Makes a new tab, if successful return the tab, returns None otherwise"""
        tab = SpineDBEditor(self.db_mngr)
        if not tab.load_db_urls(db_urls if db_urls is not None else [], create=True):
            return
        return tab

    def show_plus_button_context_menu(self, global_pos):
        toolbox = self.db_mngr.parent()
        if toolbox is None:
            return
        data_stores = toolbox.project().get_items_by_type("Data Store")
        ds_urls = {ds.name: ds.sql_alchemy_url() for ds in data_stores}
        is_url_validated = {ds.name: ds.is_url_validated() for ds in data_stores}
        if not ds_urls:
            return
        menu = QMenu(self)
        for name, url in ds_urls.items():
            action = menu.addAction(name, lambda url=url: open_db_editor([url], self.db_mngr, True))
            action.setEnabled(url is not None and is_url_validated[name])
        menu.popup(global_pos)
        menu.aboutToHide.connect(menu.deleteLater)

    def make_context_menu(self, index):
        menu = super().make_context_menu(index)
        if menu is None:
            return None
        tab = self.tab_widget.widget(index)
        menu.addSeparator()
        menu.addAction(tab.toolbar.reload_action)
        db_urls = tab.db_urls
        menu.addAction(
            QIcon(CharIconEngine("\uf24d")),
            "Duplicate",
            lambda _=False, index=index + 1, db_urls=db_urls: self.insert_new_tab(index, db_urls),
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

    @Slot(str, float, bool)
    def insert_open_file_button(self, file_path, progress, is_sqlite):
        button = next(
            (
                x
                for x in self.statusBar().findChildren(OpenFileButton)
                if os.path.samefile(x.file_path, file_path) and x.progress != 1.0
            ),
            None,
        )
        if button is not None:
            button.set_progress(progress)
            return
        button = (OpenSQLiteFileButton if is_sqlite else OpenFileButton)(file_path, progress, self)
        self._insert_statusbar_button(button)

    @Slot(bool)
    def show_user_guide(self, checked=False):
        """Opens Spine db editor documentation page in browser."""
        doc_url = f"{ONLINE_DOCUMENTATION_URL}/spine_db_editor/index.html"
        if not open_url(doc_url):
            self.msg_error.emit(f"Unable to open url <b>{doc_url}</b>")

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            db_editor_registry.unregister_window(self)


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
        self._hide_button.setFont(QFont(TOOLBOX_FONT.family))
        self._hide_button.setFixedSize(24, 24)
        self.insertPermanentWidget(0, self._hide_button)
        self.setSizeGripEnabled(False)
        self._hide_button.clicked.connect(self.hide)


def _get_existing_spine_db_editor(db_urls):
    """Returns existing editor window and tab or None for given database URLs.

    Args:
        db_urls (Sequence of str): database URLs

    Returns:
        tuple: editor window and tab or None if not found
    """
    for multi_db_editor in db_editor_registry.windows():
        for k in range(multi_db_editor.tab_widget.count()):
            db_editor = multi_db_editor.tab_widget.widget(k)
            if db_editor.db_urls and all(url in db_urls for url in db_editor.db_urls):
                return multi_db_editor, db_editor
    return None


def open_db_editor(db_urls, db_mngr, reuse_existing_editor):
    """Opens a SpineDBEditor with given urls.

    Optionally uses an existing MultiSpineDBEditor if any.
    Also, if the same urls are open in an existing SpineDBEditor, just raises that one
    instead of creating another.

    Args:
        db_urls (Iterable of str): URLs of databases to open
        db_mngr (SpineDBManager): database manager
        reuse_existing_editor (bool): if True and the same URL is already open, just raise the existing window
    """
    multi_db_editor = db_editor_registry.get_some_window() if reuse_existing_editor else None
    if multi_db_editor is None:
        multi_db_editor = MultiSpineDBEditor(db_mngr, db_urls)
        if multi_db_editor.tab_load_success:
            multi_db_editor.show()
        return
    existing = _get_existing_spine_db_editor(list(map(str, db_urls)))
    if existing is None:
        multi_db_editor.add_new_tab(db_urls)
    else:
        multi_db_editor, db_editor = existing
        multi_db_editor.set_current_tab(db_editor)
    if multi_db_editor.isMinimized():
        multi_db_editor.showNormal()
    multi_db_editor.activateWindow()
