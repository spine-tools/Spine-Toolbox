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
from PySide2.QtWidgets import QTabBar, QToolButton, QApplication, QWidget
from PySide2.QtCore import Signal, Qt, QEvent, QPoint
from PySide2.QtGui import QIcon, QMouseEvent
from spinetoolbox.helpers import CharIconEngine


class TabBarPlus(QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plus_clicked = Signal()

    def __init__(self, multi_db_editor):
        super().__init__()
        self._multi_db_editor = multi_db_editor
        self._plus_button = QToolButton(self)
        self._plus_button.setIcon(QIcon(CharIconEngine("\uf067")))
        self._plus_button.clicked.connect(lambda _=False: self.plus_clicked.emit())
        self._move_plus_button()
        self.setShape(QTabBar.RoundedNorth)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setElideMode(Qt.ElideLeft)
        self.drag_index = None
        self.setAcceptDrops(True)
        self.setStyleSheet("QTabBar::tab:disabled { width: 0; height: 0; margin: 0; padding: 0; border: none; }")

    @property
    def multi_db_editor(self):
        return self._multi_db_editor

    def dragEnterEvent(self, event):
        super().dragEnterEvent(event)
        if isinstance(event.source(), type(self._multi_db_editor)):
            self.drag_index = self.tabAt(event.pos())
            if self.drag_index == -1:
                self.drag_index = self.count()
            event.accept()

    def restart_dragging(self):
        press_pos = self.tabRect(self.drag_index).center()
        press_event = QMouseEvent(QEvent.MouseButtonPress, press_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, press_event)
        self._plus_button.hide()
        qApp.installEventFilter(self)

    def resizeEvent(self, event):
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
        """Moves the plus button to the correct location."""
        left = sum([self.tabRect(i).width() for i in range(self.count())])
        top = self.geometry().top() + 1
        self._plus_button.move(left, top)

    def _show_only_index(self, index):
        self._plus_button.hide()
        for k in range(self.count()):
            self.setTabEnabled(k, k == index)
            self.tabButton(k, QTabBar.RightSide).setVisible(k == index)

    def _show_all(self):
        self._plus_button.show()
        for k in range(self.count()):
            self.setTabEnabled(k, True)
            self.tabButton(k, QTabBar.RightSide).setVisible(True)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonRelease:
            self.mouseReleaseEvent(event)
        elif event.type() == QEvent.MouseMove:
            self.mouseMoveEvent(event)
        return False

    def mouseMoveEvent(self, event):
        self._plus_button.hide()
        if self.count() == 1 or self.count() > 1 and not self.geometry().contains(event.pos()):
            self._send_release_event(event.pos())
            hotspot_x = event.pos().x()
            hotspot_y = self.height() / 2
            hotspot = QPoint(hotspot_x, hotspot_y)
            index = self.tabAt(hotspot)
            if index == -1:
                index = self.count() - 1
            self._multi_db_editor.detach(index, hotspot)
            return
        super().mouseMoveEvent(event)

    def _send_release_event(self, pos):
        self.drag_index = None
        release_event = QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, release_event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._plus_button.show()
        self.update()
        qApp.removeEventFilter(self)
        if self.drag_index is not None:
            self._multi_db_editor.connect_editor_signals(self.drag_index)
            self.drag_index = None
