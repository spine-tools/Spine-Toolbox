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
Contains the MultiTabWindow and TabBarPlus classes.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QTabBar, QToolButton, QApplication, QMenu
from PySide6.QtCore import Qt, Slot, QPoint, Signal, QEvent
from PySide6.QtGui import QGuiApplication, QCursor, QIcon, QMouseEvent
from ..helpers import ensure_window_is_on_screen, CharIconEngine


class MultiTabWindow(QMainWindow):
    """A main window that has a tab widget as its central widget."""

    _tab_slots = {}
    _other_editor_windows = {}

    def __init__(self, qsettings, settings_group):
        """
        Args:
            qsettings (QSettings): Toolbox settings
            settings_group (str): this window's settings group in ``qsettings``
        """
        super().__init__()
        self._other_editor_windows.setdefault(type(self).__name__, []).append(self)
        self.qsettings = qsettings
        self.settings_group = settings_group
        self.tab_widget = QTabWidget(self)
        self.tab_bar = TabBarPlus(self)
        self.tab_widget.setTabBar(self.tab_bar)
        self.setCentralWidget(self.tab_widget)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._hot_spot = None
        self._timer_id = None
        self._accepting_new_tabs = True
        self.restore_ui()
        self.connect_signals()
        for w in self.findChildren(QWidget):
            w.setFocusPolicy(Qt.ClickFocus)

    @property
    def accepting_new_tabs(self):
        return self._accepting_new_tabs

    def _make_other(self):
        """Creates a new MultiTabWindow of this type.

        Returns:
            MultiTabWindow: new MultiTabWindow
        """
        raise NotImplementedError()

    def others(self):
        """List of other MultiTabWindows of the same type.

        Returns:
            list of MultiTabWindow: other MutliTabWindows windows
        """
        return [w for w in self._other_editor_windows[type(self).__name__] if w is not self]

    def _make_new_tab(self, *args, **kwargs):
        """Creates a new tab.

        Args:
            *args: positional arguments neede to make a new tab
            **kwargs: keyword arguments needed to make a new tab
        """
        raise NotImplementedError()

    def show_plus_button_context_menu(self, global_pos):
        """Opens a context menu for the tool bar.

        Args:
            global_pos (QPoint): menu position on screen
        """
        raise NotImplementedError()

    @property
    def new_tab_title(self):
        """Title for new tabs."""
        return "New tab"

    def connect_signals(self):
        """Connects window's signals."""
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_bar.plus_clicked.connect(self.add_new_tab)

    def name(self):
        """Generates name based on the current tab and total tab count.

        Returns:
            str: a name
        """
        name = self.tab_widget.tabText(self.tab_widget.currentIndex())
        other_tab_count = self.tab_widget.count() - 1
        if other_tab_count > 0:
            name += f" and {other_tab_count} other tab"
            if other_tab_count > 1:
                name += "s"
        return name

    def all_tabs(self):
        """Iterates over tab contents widgets.

        Yields:
            QWidget: tab contents widget
        """
        for k in range(self.tab_widget.count()):
            yield self.tab_widget.widget(k)

    @Slot()
    def add_new_tab(self, *args, **kwargs):
        """Creates a new tab and adds it at the end of the tab bar.

        Args:
            *args: parameters forwarded to :func:`MutliTabWindow._make_new_tab`
            **kwargs: parameters forwarded to :func:`MultiTabwindow._make_new_tab`
        """
        if not self._accepting_new_tabs:
            return
        tab = self._make_new_tab(*args, **kwargs)
        self._add_connect_tab(tab, self.new_tab_title)

    def insert_new_tab(self, index, *args, **kwargs):
        """Creates a new tab and inserts it at the given index.

        Args:
            index (int): insertion point index
            *args: parameters forwarded to :func:`MutliTabWindow._make_new_tab`
            **kwargs: parameters forwarded to :func:`MultiTabwindow._make_new_tab`
        """
        if not self._accepting_new_tabs:
            return
        tab = self._make_new_tab(*args, **kwargs)
        self._insert_connect_tab(index, tab, self.new_tab_title)

    def _add_connect_tab(self, tab, text):
        """Appends a new tab and connects signals.

        Args:
            tab (QWidget): tab contents widget
            text (str): appended tab title
        """
        self.tab_widget.addTab(tab, text)
        self._connect_tab_signals(tab)
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)

    def _insert_connect_tab(self, index, tab, text):
        """Inserts a new tab and connects signals.

        Args:
            index (int): insertion point index
            tab (QWidget): tab contents widget
            text (str): inserted tab title
        """
        self.tab_widget.insertTab(index, tab, text)
        if not tab.windowTitle():
            tab.setWindowTitle(text)
        self._connect_tab_signals(tab)
        self.tab_widget.setCurrentIndex(index)

    def _remove_disconnect_tab(self, index):
        """Disconnects and removes a tab.

        Args:
            index (int): tab index
        """
        self._disconnect_tab_signals(index)
        self.tab_widget.removeTab(index)

    def _connect_tab(self, index):
        """Connects signals from a tab contents widget.

        Args:
            index (int): tab index
        """
        tab = self.tab_widget.widget(index)
        self._connect_tab_signals(tab)

    def _connect_tab_signals(self, tab):
        """Connects signals from a tab contents widget.

        Args:
            tab (QWidget): tab contents widget

        Returns:
            bool: True if signals were connected successfully, False otherwise
        """
        if tab in self._tab_slots:
            return False
        slot = lambda title, tab=tab: self._handle_tab_window_title_changed(tab, title)
        self._tab_slots[tab] = slot
        tab.windowTitleChanged.connect(slot)
        self._handle_tab_window_title_changed(tab, tab.windowTitle())
        return True

    def _disconnect_tab_signals(self, index):
        """Disconnects signals from given tab.

        Args:
            index (int): tab index

        Returns:
            bool: True if signals were disconnected successfully, False otherwise
        """
        tab = self.tab_widget.widget(index)
        slot = self._tab_slots.pop(tab, None)
        if slot is None:
            return False
        tab.windowTitleChanged.disconnect(slot)
        return True

    def _handle_tab_window_title_changed(self, tab, title):
        """Updates tab's title.

        Args:
            tab (QWidget): tab's content widget
            title (str): new tab title; if emtpy, one will be generated
        """
        dirty = tab.isWindowModified()
        for k in range(self.tab_widget.count()):
            if not title:
                title = self.new_tab_title
            if self.tab_widget.widget(k) == tab:
                mark = "*" if dirty else ""
                self.tab_widget.setTabText(k, title + mark)
                break

    def _take_tab(self, index):
        """Removes a tab and returns its contents.

        Args:
            index (int): tab index

        Returns:
            tuple: widget the tab was holding and tab's title
        """
        tab = self.tab_widget.widget(index)
        text = self.tab_widget.tabText(index)
        self._remove_disconnect_tab(index)
        if not self.tab_widget.count():
            self.close()
        return tab, text

    def move_tab(self, index, other=None):
        """Moves a tab to another MultiTabWindow.

        Args:
            index (int): tab index
            other (MultiTabWindow, optional): target window; if None, creates a new window
        """
        if other is None:
            other = self._make_other()
            other.show()
        other._add_connect_tab(*self._take_tab(index))
        other.raise_()

    def detach(self, index, hot_spot, offset=0):
        """Detaches the tab at given index into another MultiTabWindow window and starts dragging it.

        Args:
            index (int)
            hot_spot (QPoint)
            offset (int)
        """
        other = self._make_other()
        other.tab_widget.addTab(*self._take_tab(index))
        other.show()
        other.start_drag(hot_spot, offset)

    def start_drag(self, hot_spot, offset=0):
        """Starts dragging a detached tab.

        Args:
            hot_spot (QPoint): The anchor point of the drag in widget coordinates.
            offset (int): Horizontal offset of the tab in the bar.
        """
        self.setStyleSheet(f"QTabWidget::tab-bar {{left: {offset}px;}}")
        self._hot_spot = hot_spot
        self.grabMouse()
        self._timer_id = self.startTimer(1000 // 60)  # 60 fps is supposed to be the maximum the eye can see

    def _frame_height(self):
        """Calculates the total 'thickness' of window frame in vertical direction.

        Returns:
            int: frame height
        """
        return self.frameGeometry().height() - self.geometry().height()

    def timerEvent(self, event):
        """Performs the drag, i.e., moves the window with the mouse cursor.
        As soon as the mouse hovers the tab bar of another MultiTabWindow, reattaches it.
        """
        if self._hot_spot is not None:
            self.move(QCursor.pos() - self._hot_spot - QPoint(0, self._frame_height()))
        for other in self.others():
            index = other.tab_bar.index_under_mouse()
            if index is not None:
                db_editor = self.tab_widget.widget(0)
                text = self.tab_widget.tabText(0)
                self._remove_disconnect_tab(0)
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
        if self.tab_bar.count() == 0:
            return
        index = self.tab_bar.tabAt(event.position().toPoint())
        if index is not None:
            if index == -1:
                index = self.tab_bar.count() - 1
            self._connect_tab(index)

    def reattach(self, index, tab, text):
        """Reattaches a tab that has been dragged over this window's tab bar.

        Args:
            index (int): Index in this widget's tab bar where the detached tab has been dragged.
            tab (QWidget): The widget in the tab being dragged.
            text (str): The title of the tab.
        """
        self.tab_widget.insertTab(index, tab, text)
        self.tab_widget.setCurrentIndex(index)
        self.tab_bar.start_dragging(index)

    @Slot()
    def handle_close_request_from_tab(self):
        """Catches close event triggered by a QAction in tab's QToolBar. Calls
        QTabWidgets close tabs method to ensure that the last closed tab closes
        the editor window."""
        self._close_tab(self.tab_widget.currentIndex())

    @Slot(int)
    def _close_tab(self, index):
        """Closes the tab at index.

        Args:
            index (int): tab index
        """
        if not self.tab_widget.widget(index).close():
            return
        self.tab_widget.removeTab(index)
        if not self.tab_widget.count():
            self.close()

    def set_current_tab(self, tab):
        """Sets the tab that is shown on the window.

        Args:
            tab (QWidget): tab's contents widget
        """
        index = self.tab_widget.indexOf(tab)
        if index is None:
            return
        self.tab_widget.setCurrentIndex(index)

    def make_context_menu(self, index):
        """Creates a context menu for given tab.

        Args:
            index (int): tab index

        Returns:
            QMenu: context menu or None if tab was not found
        """
        tab = self.tab_widget.widget(index)
        if tab is None:
            return None
        menu = QMenu(self)
        others = self.others()
        if others:
            move_tab_menu = menu.addMenu("Move tab to another window")
            move_tab_to_new_window = move_tab_menu.addAction(
                "New window", lambda _=False, index=index: self.move_tab(index, None)
            )
            for other in others:
                move_tab_menu.addAction(
                    other.name(), lambda _=False, index=index, other=other: self.move_tab(index, other)
                )
        else:
            move_tab_to_new_window = menu.addAction(
                "Move tab to new window", lambda _=False, index=index: self.move_tab(index, None)
            )
        move_tab_to_new_window.setEnabled(self.tab_widget.count() > 1)
        return menu

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
        self._accepting_new_tabs = False
        for k in range(self.tab_widget.count()):
            editor = self.tab_widget.widget(k)
            if not editor.close():
                event.ignore()
                self._accepting_new_tabs = True
                return
        self.save_window_state()
        super().closeEvent(event)
        if event.isAccepted():
            other_windows = self._other_editor_windows[type(self).__name__]
            try:
                window_index = other_windows.index(self)
            except ValueError:
                # It's possible that closeEvent() is called again after we've already popped
                # this window from _other_editor_windows.
                return
            other_windows.pop(window_index)


class TabBarPlus(QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plus_clicked = Signal()

    def __init__(self, parent):
        """
        Args:
            parent (MultiSpineDBEditor)
        """
        super().__init__(parent)
        self._parent = parent
        self._plus_button = QToolButton(self)
        self._plus_button.setIcon(QIcon(CharIconEngine("\uf067")))
        self._plus_button.clicked.connect(lambda _=False: self.plus_clicked.emit())
        self._move_plus_button()
        self.setShape(QTabBar.Shape.RoundedNorth)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setElideMode(Qt.ElideLeft)
        self.drag_index = None
        self._tab_hot_spot_x = None
        self._hot_spot_y = None

    def resizeEvent(self, event):
        """Sets the dimension of the plus button. Also, makes the tab bar as wide as the parent."""
        super().resizeEvent(event)
        self.setFixedWidth(self.parent().width())
        self.setMinimumHeight(self.height())
        self._move_plus_button()
        extent = max(0, self.height() - 2)
        self._plus_button.setFixedSize(extent, extent)
        self.setExpanding(False)

    def tabLayoutChange(self):
        super().tabLayoutChange()
        self._move_plus_button()

    def _move_plus_button(self):
        """Places the plus button at the right of the last tab."""
        left = sum([self.tabRect(i).width() for i in range(self.count())])
        top = self.geometry().top() + 1
        self._plus_button.move(left, top)

    def mousePressEvent(self, event):
        """Registers the position of the press, in case we need to detach the tab."""
        super().mousePressEvent(event)
        event_pos = event.position().toPoint()
        tab_rect = self.tabRect(self.tabAt(event_pos))
        self._tab_hot_spot_x = event_pos.x() - tab_rect.x()
        self._hot_spot_y = event_pos.y() - tab_rect.y()

    def mouseMoveEvent(self, event):
        """Detaches a tab either if the user moves beyond the limits of the tab bar, or if it's the only one."""
        if self.count() > 0:
            self._plus_button.hide()
        if self.count() == 1:
            self._send_release_event(event.position().toPoint())
            hot_spot = QPoint(event.position().toPoint().x(), self._hot_spot_y)
            self._parent.start_drag(hot_spot)
            return
        if self.count() > 1 and not self.geometry().contains(event.position().toPoint()):
            self._send_release_event(event.position().toPoint())
            hot_spot_x = event.position().toPoint().x()
            hot_spot = QPoint(hot_spot_x, self._hot_spot_y)
            index = self.tabAt(hot_spot)
            if index == -1:
                index = self.count() - 1
            self._parent.detach(index, hot_spot, hot_spot_x - self._tab_hot_spot_x)
            return
        super().mouseMoveEvent(event)

    def _send_release_event(self, pos):
        """Sends a mouse release event at given position in local coordinates. Called just before detaching a tab.

        Args:
            pos (QPoint)
        """
        self.drag_index = None
        release_event = QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, release_event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._plus_button.show()
        self.update()
        self.releaseMouse()
        if self.drag_index is not None:
            # Pass it to parent
            event.ignore()

    def start_dragging(self, index):
        """Stars dragging the given index. This happens when a detached tab is reattached to this bar.

        Args:
            index (int)
        """
        self.drag_index = index
        press_pos = self.tabRect(self.drag_index).center()
        press_event = QMouseEvent(QEvent.MouseButtonPress, press_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, press_event)
        QApplication.processEvents()
        move_pos = self.mapFromGlobal(QCursor.pos())
        if self.geometry().contains(move_pos):
            move_event = QMouseEvent(QEvent.MouseMove, move_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
            QApplication.sendEvent(self, move_event)
        self.grabMouse()

    def index_under_mouse(self):
        """Returns the index under the mouse cursor, or None if the cursor isn't over the tab bar.
        Used to check for drop targets.

        Returns:
            int or NoneType
        """
        pos = self.mapFromGlobal(QCursor.pos())
        if not self.geometry().contains(pos):
            return None
        index = self.tabAt(pos)
        if index == -1:
            index = self.count()
        return index

    def contextMenuEvent(self, event):
        index = self.tabAt(event.pos())
        if self._plus_button.underMouse():
            self._parent.show_plus_button_context_menu(event.globalPos())
            return
        tab_button = self.tabButton(index, QTabBar.RightSide)
        if tab_button is None or tab_button.underMouse():
            return
        menu = self._parent.make_context_menu(index)
        if menu is None:
            return
        menu.popup(event.globalPos())
        menu.aboutToHide.connect(menu.deleteLater)
        event.accept()
