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
Contains PropertiesWidgetBase.

:author: M. Marin (ER)
:date: 20.01.2022
"""

from PySide2.QtWidgets import QWidget, QAbstractItemView, QLineEdit
from PySide2.QtCore import Qt, QRect, QPoint, QEvent
from PySide2.QtGui import QPainter, QPixmap
from ..helpers import fix_lightness_color


class PropertiesWidgetBase(QWidget):
    """Properties widget base class."""

    def __init__(self, toolbox, base_color=None):
        super().__init__()
        self._toolbox = toolbox
        self._pixmap = None
        self._bg_color = None
        self._fg_color = None
        self._transparent_class_fns = {
            QAbstractItemView: lambda x: x.viewport(),
            QLineEdit: lambda x: x,
        }
        self._transparent_widgets = set()
        if base_color is not None:
            self.set_color_and_icon(base_color)

    @property
    def fg_color(self):
        return self._fg_color

    def set_color_and_icon(self, base_color, icon=None):
        self._bg_color = fix_lightness_color(base_color, 248)
        self._fg_color = fix_lightness_color(base_color, 240)
        if icon is None:
            return
        bnw_pixmap = QPixmap(icon)
        self._pixmap = QPixmap(bnw_pixmap.size())
        self._pixmap.fill(self._fg_color)
        self._pixmap.setMask(bnw_pixmap.createMaskFromColor(Qt.transparent))

    def event(self, ev):
        if ev.type() is QEvent.ChildAdded:
            new_transparent_widgets = {
                widget
                for klass, fn in self._transparent_class_fns.items()
                for widget in {fn(x) for x in self.findChildren(klass)}
            }
            new_transparent_widgets -= self._transparent_widgets
            self._transparent_widgets |= new_transparent_widgets
            for widget in new_transparent_widgets:
                widget.setStyleSheet("background-color: rgba(255,255,255,180);")
        return super().event(ev)

    def paintEvent(self, ev):
        """Paints background"""
        settings = self._toolbox.qsettings()
        if settings.value("appSettings/colorPropertiesWidgets", defaultValue="false") == "false":
            super().paintEvent(ev)
            return
        self.paint_bg(ev.rect())

    def paint_bg(self, rect=None):
        if rect is None:
            rect = self.rect()
        painter = QPainter(self)
        painter.fillRect(rect, self._bg_color)
        if self._pixmap is not None:
            margin = 20
            offset = QPoint(margin, margin)
            painter.drawPixmap(QRect(rect.topLeft() + offset, rect.bottomRight() - offset), self._pixmap)
