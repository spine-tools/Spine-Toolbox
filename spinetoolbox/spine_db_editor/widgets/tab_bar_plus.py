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
from PySide2.QtWidgets import QTabBar, QToolButton, QStyleOptionTab, QStyle, QStylePainter, QApplication, QWidget
from PySide2.QtCore import Signal, Qt, QEvent, QPoint
from PySide2.QtGui import QIcon, QMouseEvent, QCursor
from spinetoolbox.helpers import CharIconEngine


class TabBarPlus(QTabBar):
    """Tab bar that has a plus button floating to the right of the tabs."""

    plus_clicked = Signal()

    def __init__(self, spine_db_editor):
        super().__init__()
        self._spine_db_editor = spine_db_editor
        self._plus_button = QToolButton(self)
        self._plus_button.setIcon(QIcon(CharIconEngine("\uf067")))
        self._plus_button.clicked.connect(lambda _=False: self.plus_clicked.emit())
        self._move_plus_button()
        self.setShape(QTabBar.RoundedNorth)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.setElideMode(Qt.ElideLeft)
        self._delta = None
        self._pressed_index = None
        self._drag_dist = None
        self._drag_index = None

    def paintEvent(self, event):
        if self._drag_dist is None:
            super().paintEvent(event)
            return
        p = QStylePainter(self)
        tab = QStyleOptionTab()
        self.initStyleOption(tab, 0)
        y = tab.rect.top()
        tab.rect.moveCenter(self._drag_dist)
        tab.rect.moveTop(y)
        tab.rect.moveLeft(max(0, tab.rect.left()))
        tab.rect.moveRight(min(self.width(), tab.rect.right()))
        p.drawControl(QStyle.CE_TabBarTab, tab)
        p.end()

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

    def restart_dragging(self, index):
        # FIXME: make sure we always release the mouse?
        self._drag_index = index
        self.grabMouse()
        press_pos = self.tabRect(index).center()
        press_event = QMouseEvent(QEvent.MouseButtonPress, press_pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, press_event)
        self._delta = QCursor.pos() - self._spine_db_editor.pos()
        self._plus_button.hide()
        if self.count() == 1:
            self._drag_dist = self.mapFromGlobal(QCursor.pos())

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._delta = event.globalPos() - self._spine_db_editor.pos()
        self._pressed_index = self.tabAt(event.pos())

    def mouseMoveEvent(self, event):
        self._plus_button.hide()
        if self.count() == 1:
            self._drag_dist = event.pos()
            if self._delta:
                self._spine_db_editor.raise_()
                self._spine_db_editor.move(event.globalPos() - self._delta)
            target = self._spine_db_editor.find_reattach_target(event.globalPos())
            if target is not None:
                self._send_release_event(event.pos())
                self._spine_db_editor.reattach(*target)
            return
        if self.count() > 1 and not self.geometry().contains(event.pos()):
            self._send_release_event(event.pos())
            hotspot_x = event.pos().x()
            hotspot_y = self.height() / 2
            hotspot = QPoint(hotspot_x, hotspot_y)
            delta = self.mapToGlobal(hotspot) - self._spine_db_editor.pos()
            self._spine_db_editor.detach(self._pressed_index, delta)
            return
        super().mouseMoveEvent(event)

    def _send_release_event(self, pos):
        self._drag_index = None
        release_event = QMouseEvent(QEvent.MouseButtonRelease, pos, Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        QApplication.sendEvent(self, release_event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self._plus_button.show()
        self._drag_dist = None
        self.update()
        if QWidget.mouseGrabber() is self:
            self.releaseMouse()
        if self._drag_index is not None:
            self._spine_db_editor.connect_editor_signals(self._drag_index)
            self._drag_index = None
