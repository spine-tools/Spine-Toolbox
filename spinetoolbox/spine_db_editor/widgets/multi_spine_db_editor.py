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
Contains the MultiSpineDBEditor class.

:author: M. Marin (KTH)
:date:   12.12.2020
"""

import os
from PySide2.QtWidgets import QMainWindow, QTabWidget, QToolBar, QWidget, QSizePolicy
from PySide2.QtCore import Qt, Slot, QPoint, QSize
from PySide2.QtGui import QGuiApplication, QIcon, QCursor
from .tab_bar_plus import TabBarPlus
from .spine_db_editor import SpineDBEditor
from .custom_qwidgets import ShootingLabel, OpenFileButton, OpenSQLiteFileButton
from ...helpers import ensure_window_is_on_screen, CharIconEngine, open_url
from ...config import ONLINE_DOCUMENTATION_URL
from ...widgets.settings_widget import SpineDBEditorSettingsWidget


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


class _DBEditorTabWidget(QTabWidget):
    _slots = {}

    def add_connect_tab(self, db_editor, text):
        self.addTab(db_editor, text)
        self.connect_editor_signals(db_editor)

    def insert_connect_tab(self, index, db_editor, text):
        self.insertTab(index, db_editor, text)
        self.connect_editor_signals(db_editor)

    def remove_disconnect_tab(self, index):
        self.disconnect_editor_signals(index)
        self.removeTab(index)

    def connect_tab(self, index):
        db_editor = self.widget(index)
        self.connect_editor_signals(db_editor)

    def connect_editor_signals(self, db_editor):
        if db_editor in self._slots:
            return
        s1 = lambda title, db_editor=db_editor: self._handle_window_title_changed(db_editor, title)
        s2 = lambda dirty, db_editor=db_editor: self._handle_dirty_changed(db_editor, dirty)
        db_editor.windowTitleChanged.connect(s1)
        db_editor.dirty_changed.connect(s2)
        db_editor.file_exported.connect(self.parent().insert_file_open_button)
        db_editor.sqlite_file_exported.connect(self.parent().insert_sqlite_file_open_button)
        db_editor.ui.actionUser_guide.triggered.connect(self.parent().show_user_guide)
        db_editor.ui.actionSettings.triggered.connect(self.parent().settings_form.show)
        self._slots[db_editor] = (s1, s2)

    def disconnect_editor_signals(self, index):
        db_editor = self.widget(index)
        slots = self._slots.pop(db_editor, None)
        if slots is None:
            return
        s1, s2 = slots
        db_editor.windowTitleChanged.disconnect(s1)
        db_editor.dirty_changed.disconnect(s2)
        db_editor.file_exported.disconnect(self.parent().insert_file_open_button)
        db_editor.sqlite_file_exported.disconnect(self.parent().insert_sqlite_file_open_button)
        db_editor.ui.actionUser_guide.triggered.disconnect(self.parent().show_user_guide)
        db_editor.ui.actionSettings.triggered.disconnect(self.parent().settings_form.show)

    def _handle_window_title_changed(self, db_editor, title):
        for k in range(self.count()):
            if self.widget(k) == db_editor:
                self.setTabText(k, title)
                break

    def _handle_dirty_changed(self, db_editor, dirty):
        for k in range(self.count()):
            if self.widget(k) == db_editor:
                mark = "*" if dirty else ""
                self.setTabText(k, db_editor.windowTitle() + mark)
                break


class MultiSpineDBEditor(QMainWindow):
    def __init__(self, db_mngr, db_url_codenames, create=False):
        super().__init__(flags=Qt.Window)
        self.db_mngr = db_mngr
        self.tab_widget = _DBEditorTabWidget()
        self.tab_bar = TabBarPlus(self)
        self.tab_widget.setTabBar(self.tab_bar)
        self.setCentralWidget(self.tab_widget)
        self.qsettings = self.db_mngr.qsettings
        self.settings_form = SpineDBEditorSettingsWidget(self)
        self.settings_group = "spineDBEditor"
        self.setAttribute(Qt.WA_DeleteOnClose)
        if db_url_codenames is not None:
            self.add_new_tab(db_url_codenames)
            if not self.tab_widget.widget(0).db_maps:
                self.close()
        self.setWindowTitle("Spine DB Editor")
        self.setWindowIcon(QIcon(":/symbols/app.ico"))
        self._hot_spot = None
        self._timer_id = None
        self._others = None
        self.restore_ui()
        self._file_open_toolbar = _FileOpenToolBar(self)
        self._file_open_toolbar.hide()
        self.addToolBar(Qt.BottomToolBarArea, self._file_open_toolbar)
        self.connect_signals()

    def connect_signals(self):
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.plus_clicked.connect(self.add_new_tab)

    def name(self):
        name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        other_tab_count = self.tab_widget.count() - 1
        if other_tab_count > 0:
            name += f" and {other_tab_count} other tab"
            if other_tab_count > 1:
                name += "s"
        return name

    def _take_tab(self, index):
        db_editor = self.tab_widget.widget(index)
        text = self.tab_widget.tabText(index)
        self.tab_widget.remove_disconnect_tab(index)
        if not self.tab_widget.count():
            self.close()
        return db_editor, text

    def move_tab(self, index, other=None):
        if other is None:
            other = MultiSpineDBEditor(self.db_mngr, None)
            other.show()
        other.tab_widget.add_connect_tab(*self._take_tab(index))
        other.raise_()
        other.tab_bar.setCurrentIndex(other.tab_bar.count() - 1)

    def detach(self, index, hot_spot, offset=0):
        """Detaches the tab at given index into another MultiSpineDBEditor window and starts dragging it.

        Args:
            index (int)
            hot_spot (QPoint)
            offset (int)
        """
        other = MultiSpineDBEditor(self.db_mngr, None)
        other.tab_widget.addTab(*self._take_tab(index))
        other.show()
        other.start_drag(hot_spot, offset)

    def start_drag(self, hot_spot, offset=0):
        """Starts dragging a detached tab.

        Args:
            hot_spot (QPoint): The anchor point of the drag in widget coordinates.
            offset (int, optional): Horizontal offset of the tab in the bar.
        """
        self.setStyleSheet(f"QTabWidget::tab-bar {{left: {offset}px;}}")
        self._hot_spot = hot_spot
        self.grabMouse()
        self._others = self.others()
        self._timer_id = self.startTimer(1000 / 60)  # 60 fps is supposed to be the maximum the eye can see

    def others(self):
        return [w for w in self.db_mngr.get_all_multi_spine_db_editors() if w is not self]

    def _frame_height(self):
        return self.frameGeometry().height() - self.geometry().height()

    def timerEvent(self, event):
        """Performs the drag, i.e., moves the window with the mouse cursor.
        As soon as the mouse hovers the tab bar of another MultiSpineDBEditor, reattaches it.
        """
        self.move(QCursor.pos() - self._hot_spot - QPoint(0, self._frame_height()))
        for other in self._others:
            index = other.tab_bar.index_under_mouse()
            if index is not None:
                db_editor = self.tab_widget.widget(0)
                text = self.tab_widget.tabText(0)
                self.tab_widget.remove_disconnect_tab(0)
                self.close()
                other.reattach(index, db_editor, text)
                break

    def mouseReleaseEvent(self, event):
        """Stops the drag. This only happens when the detached tab is not reattached to another window."""
        super().mouseReleaseEvent(event)
        if self._hot_spot:
            self.setStyleSheet("")
            self.releaseMouse()
            self.killTimer(self._timer_id)
            self._hot_spot = None
            self.update()
        index = self.tab_bar.tabAt(event.pos())
        if index is not None:
            if index == -1:
                index = self.tab_bar.count() - 1
            self.tab_widget.connect_tab(index)

    def reattach(self, index, db_editor, text):
        """Reattaches a tab that has been dragged over this window's tab bar.

        Args:
            index (int): Index in this widget's tab bar where the detached tab has been dragged.
            db_editor (SpineDBEditor): The widget in the tab being dragged.
            text (str): The title of the tab.
        """
        self.tab_widget.insertTab(index, db_editor, text)
        self.tab_widget.setCurrentIndex(index)
        self.tab_bar.start_dragging(index)

    @Slot()
    def add_new_tab(self, db_url_codenames=()):
        """Creates a new SpineDBEditor with given urls and adds it at the end of the tab bar.

        Args:
            db_url_codenames (dict): Mapping str url to str codename
        """
        db_editor = SpineDBEditor(self.db_mngr)
        self.tab_widget.add_connect_tab(db_editor, "New Tab")
        db_editor.load_db_urls(db_url_codenames, create=True)
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def insert_new_tab(self, index, db_url_codenames):
        """Creates a new SpineDBEditor with given urls and inserts it at the given index.

        Args:
            index (int)
            db_url_codenames (dict): Mapping str url to str codename
        """
        db_editor = SpineDBEditor(self.db_mngr)
        self.tab_widget.insert_connect_tab(index, db_editor, "New Tab")
        db_editor.load_db_urls(db_url_codenames, create=True)
        self.tab_widget.setCurrentIndex(index)

    @Slot(int)
    def _close_tab(self, index):
        """Closes the tab at index.

        Args:
            index (int)
        """
        self.tab_widget.widget(index).close()
        self.tab_widget.removeTab(index)
        if not self.tab_widget.count():
            self.close()

    def restore_ui(self):
        """Restore UI state from previous session."""
        self.qsettings.beginGroup(self.settings_group)
        window_size = self.qsettings.value("windowSize")
        window_pos = self.qsettings.value("windowPosition")
        window_state = self.qsettings.value("windowState")
        window_maximized = self.qsettings.value("windowMaximized", defaultValue='false')
        n_screens = self.qsettings.value("n_screens", defaultValue=1)
        self.qsettings.endGroup()
        original_size = self.size()
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)
        ensure_window_is_on_screen(self, original_size)
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)

    def save_window_state(self):
        """Save window state parameters (size, position, state) via QSettings."""
        self.qsettings.beginGroup(self.settings_group)
        self.qsettings.setValue("windowSize", self.size())
        self.qsettings.setValue("windowPosition", self.pos())
        self.qsettings.setValue("windowState", self.saveState(version=1))
        self.qsettings.setValue("windowMaximized", self.windowState() == Qt.WindowMaximized)
        self.qsettings.setValue("n_screens", len(QGuiApplication.screens()))
        self.qsettings.endGroup()

    def closeEvent(self, event):
        for k in range(self.tab_widget.count()):
            db_editor = self.tab_widget.widget(k)
            if not db_editor.tear_down():
                event.ignore()
                return
        self.save_window_state()
        super().closeEvent(event)

    def _insert_statusbar_button(self, button):
        """Inserts given button to the 'beginning' of the status bar and decorates the thing with a shooting label.

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
