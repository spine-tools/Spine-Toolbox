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

"""Class for drawing an item group on QGraphicsScene."""
from PySide6.QtCore import Qt, QMarginsF, QRectF
from PySide6.QtGui import QBrush, QPen, QAction, QPainterPath, QTransform
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsRectItem,
    QGraphicsTextItem,
    QGraphicsDropShadowEffect,
    QStyle
)
from .project_item_icon import ProjectItemIcon


class Group(QGraphicsRectItem):

    FONT_SIZE_PIXELS = 12  # pixel size to prevent font scaling by system

    def __init__(self, toolbox, name, item_names):
        super().__init__()
        print(f"toolbox:{toolbox}")
        self._toolbox = toolbox
        self._name = name
        self._item_names = item_names  # strings
        self._items = dict()  # QGraphicsItems
        conns = self._toolbox.project.connections + self._toolbox.project.jumps
        for name in item_names:
            try:
                icon = self._toolbox.project.get_item(name).get_icon()
                self._items[name] = icon
            except KeyError:  # name refers to a link or to a jump
                link_icons = [link.graphics_item for link in conns if link.name == name]
                self._items[name] = link_icons[0]
        for item_icon in self._items.values():
            item_icon.my_groups.add(self)
        self._n_items = len(self._items)
        disband_action = QAction("Ungroup items")
        disband_action.triggered.connect(lambda checked=False, group_name=self.name: self._toolbox.ui.graphicsView.push_disband_group_command(checked, group_name))
        rename_group_action = QAction("Rename group...")
        rename_group_action.triggered.connect(lambda checked=False, group_name=self.name: self._toolbox.rename_group(checked, group_name))
        self._actions = [disband_action, rename_group_action]
        self.margins = QMarginsF(0, 0, 0, 10.0)  # left, top, right, bottom
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setZValue(-10)
        self.name_item = QGraphicsTextItem(self._name, parent=self)
        self.set_name_attributes()
        self.setRect(self.rect())
        self._reposition_name_item()
        self.setBrush(self._toolbox.ui.graphicsView.scene().bg_color.lighter(107))
        self.normal_pen = QPen(QBrush("gray"), 1, Qt.PenStyle.SolidLine)
        self.selected_pen_for_ui_lite = QPen(QBrush("gray"), 5, Qt.PenStyle.DashLine)
        self.selected_pen = QPen(QBrush("black"), 1, Qt.PenStyle.DashLine)
        self.setPen(self.normal_pen)
        self.set_graphics_effects()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name
        self.name_item.setPlainText(new_name)

    @property
    def items(self):
        return self._items.values()

    @property
    def item_names(self):
        return list(self._items.keys())

    @property
    def project_items(self):
        return [item for item in self.items if isinstance(item, ProjectItemIcon)]

    @property
    def n_items(self):
        return len(self._items)

    def actions(self):
        return self._actions

    def set_name_attributes(self):
        """Sets name item attributes (font, size, style, alignment)."""
        self.name_item.setZValue(100)
        font = self.name_item.font()
        font.setPixelSize(self.FONT_SIZE_PIXELS)
        font.setBold(True)
        self.name_item.setFont(font)
        option = self.name_item.document().defaultTextOption()
        option.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_item.document().setDefaultTextOption(option)

    def _reposition_name_item(self):
        """Sets name item position (left side on top of the group icon)."""
        main_rect = self.boundingRect()
        name_rect = self.name_item.sceneBoundingRect()
        self.name_item.setPos(main_rect.left(), main_rect.y() - name_rect.height() - 4)

    def add_item(self, name):
        """Adds item to this Group.

        Args:
            name (str): Project item or Link name
        """
        try:
            icon = self._toolbox.project.get_item(name).get_icon()
        except KeyError:  # name refers to a link or to a jump
            conns = self._toolbox.project.connections + self._toolbox.project.jumps
            link_icons = [link.graphics_item for link in conns if link.name == name]
            icon = link_icons[0]
        icon.my_groups.add(self)
        self._items[name] = icon
        self.update_group_rect()

    def remove_item(self, name):
        """Removes item from this Group.

        Args:
            name (str): Project item name
        """
        item = self._items.pop(name)
        for conn in item.connectors.values():
            for link in conn.outgoing_links():
                if link.name in self._items.keys():
                    self._items.pop(link.name)
                    link.my_groups.remove(self)
            for link in conn.incoming_links():
                if link.name in self._items.keys():
                    self._items.pop(link.name)
                    link.my_groups.remove(self)
        item.my_groups.remove(self)
        self.update_group_rect()

    def remove_all_items(self):
        """Removes all items (ProjectItemIcons) from this group."""
        for item in self.project_items:
            self.remove_item(item.name)

    def update_group_rect(self):
        """Updates group rectangle and it's attributes when group member(s) is/are moved."""
        self.setRect(self.rect())
        self._reposition_name_item()

    def rect(self):
        """Calculates the size of the rectangle for this group."""
        united_rect = QRectF()
        for item in self.items:
            if isinstance(item, ProjectItemIcon):
                united_rect = united_rect.united(item.name_item.sceneBoundingRect().united(item.sceneBoundingRect()))
            else:
                united_rect = united_rect.united(item.sceneBoundingRect())
        rect_with_margins = united_rect.marginsAdded(self.margins)
        return rect_with_margins

    def set_graphics_effects(self):
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1)
        shadow_effect.setEnabled(False)
        self.setGraphicsEffect(shadow_effect)

    def mousePressEvent(self, event):
        """Sets all items belonging to this group selected.

        Args:
            event (QMousePressEvent): Event
        """
        event.accept()
        path = QPainterPath()
        path.addRect(self.rect())
        self._toolbox.toolboxuibase.active_ui_window.ui.graphicsView.scene().setSelectionArea(path, QTransform())

    def mouseReleaseEvent(self, event):
        """Accepts the event to prevent graphics view's mouseReleaseEvent from clearing the selections."""
        event.accept()

    def contextMenuEvent(self, event):
        """Opens context-menu in design mode."""
        if self._toolbox.active_ui_mode == "toolboxuilite":
            event.ignore()  # Send context-menu request to graphics view
            return
        event.accept()
        self.scene().clearSelection()
        self.setSelected(True)
        self._toolbox.show_project_or_item_context_menu(event.screenPos(), self)

    def hoverEnterEvent(self, event):
        """Sets a drop shadow effect to icon when mouse enters group boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(True)
        event.accept()

    def hoverLeaveEvent(self, event):
        """Disables the drop shadow when mouse leaves group boundaries.

        Args:
            event (QGraphicsSceneMouseEvent): Event
        """
        self.prepareGeometryChange()
        self.graphicsEffect().setEnabled(False)
        event.accept()

    def to_dict(self):
        """Returns a dictionary mapping group name to item names."""
        return {self.name: self.item_names}

    def paint(self, painter, option, widget=None):
        """Sets a dashline pen when selected."""
        if option.state & QStyle.StateFlag.State_Selected:
            option.state &= ~QStyle.StateFlag.State_Selected
            if self._toolbox.active_ui_mode == "toolboxui":
                self.setPen(self.selected_pen)
            elif self._toolbox.active_ui_mode == "toolboxuilite":
                self.setPen(self.selected_pen_for_ui_lite)
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)
