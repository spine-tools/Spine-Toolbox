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
Classes for drawing graphics items on graph view's QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""
from PySide2.QtCore import Qt, Signal, Slot
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsSimpleTextItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsLineItem,
    QStyle,
    QApplication,
)
from PySide2.QtGui import QPen, QBrush, QPainterPath, QFont, QTextCursor, QTransform, QPalette, QGuiApplication


class EntityItem(QGraphicsPixmapItem):
    def __init__(self, graph_view_form, x, y, extent, entity_id=None, entity_class_id=None):
        """Initializes item

        Args:
            graph_view_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): Preferred extent
            entity_id (int, optional): The entity id in case of a non-wip item
            entity_class_id (int, optional): The entity class id in case of a wip item
        """
        if not entity_id and not entity_class_id:
            raise ValueError("Can't create an RelationshipItem without relationship id nor relationship class id.")
        super().__init__()
        self._graph_view_form = graph_view_form
        self.db_mngr = graph_view_form.db_mngr
        self.db_map = graph_view_form.db_map
        self.entity_id = entity_id
        self._entity_class_id = entity_class_id
        self._entity_name = f"<WIP {self.entity_class_name}>"
        self.arc_items = list()
        self._extent = extent
        self.refresh_icon()
        self.setPos(x, y)
        rect = self.boundingRect()
        self.setOffset(-rect.width() / 2, -rect.height() / 2)
        self._press_pos = None
        self._merge_target = None
        self._moved_on_scene = False
        self._view_transform = QTransform()  # To determine collisions in the view
        self._views_cursor = {}
        self._bg = None
        self._bg_brush = Qt.NoBrush
        self._init_bg()
        self._bg.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
        self.is_wip = None
        self._question_item = None  # In case this becomes a template
        if not self.entity_id:
            self.become_wip()
        else:
            self.become_whole()
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.ArrowCursor)

    @property
    def entity_type(self):
        raise NotImplementedError()

    @property
    def entity_name(self):
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id).get("name", self._entity_name)

    @property
    def entity_class_type(self):
        return {"relationship": "relationship class", "object": "object class"}[self.entity_type]

    @property
    def entity_class_id(self):
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id).get(
            "class_id", self._entity_class_id
        )

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, self.entity_class_type, self.entity_class_id)["name"]

    def boundingRect(self):
        return super().boundingRect() | self.childrenBoundingRect()

    def _init_bg(self):
        self._bg = QGraphicsRectItem(self.boundingRect(), self)
        self._bg.setPen(Qt.NoPen)

    def refresh_icon(self):
        """Refreshes the icon."""
        pixmap = self.db_mngr.entity_class_icon(self.db_map, self.entity_class_type, self.entity_class_id).pixmap(
            self._extent
        )
        self.setPixmap(pixmap)

    def shape(self):
        """Returns a shape containing the entire bounding rect, to work better with icon transparency."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Shows or hides the selection halo."""
        if option.state & (QStyle.State_Selected):
            self._paint_as_selected()
            option.state &= ~QStyle.State_Selected
        else:
            self._paint_as_deselected()
        super().paint(painter, option, widget)

    def _paint_as_selected(self):
        self._bg.setBrush(QGuiApplication.palette().highlight())

    def _paint_as_deselected(self):
        self._bg.setBrush(self._bg_brush)

    def add_arc_item(self, arc_item):
        """Adds an item to the list of arcs.

        Args:
            arc_item (ArcItem)
        """
        self.arc_items.append(arc_item)

    def become_wip(self):
        """Turns this item into a work-in-progress."""
        self.is_wip = True
        font = QFont("", 0.6 * self._extent)
        self._question_item = OutlinedTextItem("?", self, font)
        # Position question item
        rect = super().boundingRect()
        question_rect = self._question_item.boundingRect()
        x = rect.center().x() - question_rect.width() / 2
        y = rect.center().y() - question_rect.height() / 2
        self._question_item.setPos(x, y)
        self.setToolTip(self._make_wip_tool_tip())

    def _make_wip_tool_tip(self):
        raise NotImplementedError()

    def become_whole(self):
        """Removes the wip status from this item."""
        self.is_wip = False
        if self._question_item:
            self.scene().removeItem(self._question_item)

    def adjust_to_zoom(self, transform):
        """Saves the view's transform to determine collisions later on.

        Args:
            transform (QTransform): The view's transformation matrix after the zoom.
        """
        self._view_transform = transform
        factor = transform.m11()
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=factor > 1)

    def device_rect(self):
        """Returns the item's rect in devices's coordinates.
        Used to accurately determine collisions.
        """
        return self.deviceTransform(self._view_transform).mapRect(super().boundingRect())

    def _find_merge_target(self):
        """Returns a suitable merge target if any.

        Returns:
            spinetoolbox.widgets.graph_view_graphics_items.EntityItem, NoneType
        """
        scene = self.scene()
        if not scene:
            return None
        colliding = [
            x
            for x in scene.items()
            if x.isVisible()
            and isinstance(x, EntityItem)
            and x is not self
            and x.device_rect().intersects(self.device_rect())
        ]
        return next(iter(colliding), None)

    # pylint: disable=no-self-use
    def _is_target_valid(self):
        """Whether or not the registered merge target is valid.

        Returns:
            bool
        """
        return False

    # pylint: disable=no-self-use
    def merge_into_target(self, force=False):
        """Merges this item into the registered target if valid.

        Returns:
            bool: True if merged, False if not.
        """
        return False

    def mousePressEvent(self, event):
        """Saves original position for bouncing purposes.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        super().mousePressEvent(event)
        self._press_pos = self.pos()
        self._merge_target = None

    def mouseMoveEvent(self, event):
        """Moves the item and all connected arcs. Also checks for a merge target
        and sets an appropriate mouse cursor.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        if event.buttons() & Qt.LeftButton == 0:
            super().mouseMoveEvent(event)
            return
        move_by = event.scenePos() - event.lastScenePos()
        # Move selected items together
        for item in self.scene().selectedItems():
            if isinstance(item, (EntityItem)):
                item.moveBy(move_by.x(), move_by.y())
                item.move_arc_items(move_by)
        self._merge_target = self._find_merge_target()
        for view in self.scene().views():
            self._views_cursor.setdefault(view, view.viewport().cursor())
            if not self._merge_target:
                try:
                    view.viewport().setCursor(self._views_cursor[view])
                except KeyError:
                    pass
                continue
            if self._is_target_valid():
                view.viewport().setCursor(Qt.DragCopyCursor)
            else:
                view.viewport().setCursor(Qt.ForbiddenCursor)

    def move_arc_items(self, pos_diff):
        """Moves arc items.

        Args:
            pos_diff (QPoint)
        """
        raise NotImplementedError()

    def mouseReleaseEvent(self, event):
        """Merges the item into the registered target if any. Bounces it if not possible.
        Shrinks the scene if needed.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        super().mouseReleaseEvent(event)
        if self._merge_target:
            if self.merge_into_target():
                return
            self._bounce_back(self.pos())
        if self._moved_on_scene:
            self._moved_on_scene = False
            scene = self.scene()
            scene.shrink_if_needed()
            scene.item_move_finished.emit(self)

    def _bounce_back(self, current_pos):
        """Bounces the item back from given position to its original position.

        Args:
            current_pos (QPoint)
        """
        if self._press_pos is None:
            return
        self.move_arc_items(self._press_pos - current_pos)
        self.setPos(self._press_pos)

    def itemChange(self, change, value):
        """
        Keeps track of item's movements on the scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
            the same value given as input
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
        return value

    def set_all_visible(self, on):
        """Sets visibility status for this item and all arc items.

        Args:
            on (bool)
        """
        for item in self.arc_items:
            item.setVisible(on)
        self.setVisible(on)

    def wipe_out(self):
        """Removes this item and all its arc items from the scene."""
        self.scene().removeItem(self)
        for arc_item in self.arc_items:
            if arc_item.scene():
                arc_item.scene().removeItem(arc_item)
                other_item = arc_item.other_item(self)
                if other_item.is_wip:
                    other_item.wipe_out()

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        e.accept()
        if not self.isSelected() and not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        self._show_item_context_menu_in_parent(e.screenPos())

    def _show_item_context_menu_in_parent(self, pos):
        raise NotImplementedError()


class RelationshipItem(EntityItem):
    """Relationship item to use with GraphViewForm."""

    @property
    def entity_type(self):
        return "relationship"

    @property
    def object_class_id_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship class", self.entity_class_id)["object_class_id_list"]

    @property
    def object_name_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.entity_id).get(
            "object_name_list", ",".join(["<unnamed>" for _ in range(len(self.object_class_id_list))])
        )

    @property
    def object_id_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.entity_id).get("object_id_list")

    @property
    def db_representation(self):
        return dict(
            class_id=self.entity_class_id,
            id=self.entity_id,
            object_id_list=self.object_id_list,
            object_name_list=self.object_name_list,
        )

    def _init_bg(self):
        extent = self._extent
        self._bg = QGraphicsEllipseItem(-0.5 * extent, -0.5 * extent, extent, extent, self)
        self._bg.setPen(Qt.NoPen)
        bg_color = QGuiApplication.palette().color(QPalette.Normal, QPalette.Window)
        bg_color.setAlphaF(0.8)
        self._bg_brush = QBrush(bg_color)

    def validate_member_objects(self):
        """Goes through connected object items and tries to complete the relationship."""
        if not self.is_wip:
            return True
        object_id_list = [arc_item.obj_item.entity_id for arc_item in self.arc_items]
        if None in object_id_list:
            return True
        object_name_list = [arc_item.obj_item.entity_name for arc_item in self.arc_items]
        entity_id = self._graph_view_form.add_relationship(self._entity_class_id, object_id_list, object_name_list)
        if not entity_id:
            return False
        self.entity_id = entity_id
        self.become_whole()
        return True

    def move_arc_items(self, pos_diff):
        """Moves arc items.

        Args:
            pos_diff (QPoint)
        """
        for item in self.arc_items:
            item.move_rel_item_by(pos_diff)

    def _make_wip_tool_tip(self):
        return """
            <html>This is a work-in-progress <b>{0}</b> relationship.</html>
        """.format(
            self.entity_class_name
        )

    def become_whole(self):
        super().become_whole()
        self.setToolTip(self.object_name_list)
        for item in self.arc_items:
            item.become_whole()

    def _show_item_context_menu_in_parent(self, pos):
        self._graph_view_form.show_relationship_item_context_menu(pos)


class ObjectItem(EntityItem):
    def __init__(self, graph_view_form, x, y, extent, entity_id=None, entity_class_id=None):
        """Initializes the item.

        Args:
            graph_view_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            entity_id (int, optional): object id, if not given the item becomes a template
            entity_class_id (int, optional): object class id, for template items

        Raises:
            ValueError: in case object_id and object_class_id are both not provided
        """
        super().__init__(graph_view_form, x, y, extent, entity_id, entity_class_id)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.label_item = EntityLabelItem(self)
        self.label_item.entity_name_edited.connect(self.finish_name_editing)
        self.setZValue(0.5)
        self.refresh_name()

    @property
    def entity_type(self):
        return "object"

    @property
    def db_representation(self):
        return dict(class_id=self.entity_class_id, id=self.entity_id, name=self.entity_name)

    def refresh_name(self):
        """Refreshes the name."""
        self.label_item.setPlainText(self.entity_name)

    def _paint_as_selected(self):
        if not self.label_item.hasFocus():
            super()._paint_as_selected()
        else:
            self._paint_as_deselected()

    def _make_wip_tool_tip(self):
        return "<html>This is a work-in-progress <b>{0}</b>. Give it a name to finish the job.</html>".format(
            self.entity_class_name
        )

    def become_whole(self):
        super().become_whole()
        self.refresh_description()

    def refresh_description(self):
        description = self.db_mngr.get_item(self.db_map, "object", self.entity_id).get("description")
        self.setToolTip(f"<html>{description}</html>")

    def edit_name(self):
        """Starts editing the object name."""
        self.setSelected(True)
        self.label_item.start_editing()

    @Slot(str)
    def finish_name_editing(self, text):
        """Runs when the user finishes editing the name.
        Adds or updates the object in the database.

        Args:
            text (str): The new name.
        """
        if text == self.entity_name:
            return
        if self.is_wip:
            # Add
            entity_id = self._graph_view_form.add_object(self._entity_class_id, text)
            if not entity_id:
                return
            self.entity_id = entity_id
            for arc_item in self.arc_items:
                arc_item.rel_item.validate_member_objects()
            self.become_whole()
        else:
            # Update
            self._graph_view_form.update_object(self.entity_id, text)
        self.refresh_name()

    def move_arc_items(self, pos_diff):
        """Moves arc items.

        Args:
            pos_diff (QPoint)
        """
        for item in self.arc_items:
            item.move_obj_item_by(pos_diff)

    def keyPressEvent(self, event):
        """Starts editing the name if F2 is pressed.

        Args:
            event (QKeyEvent)
        """
        if event.key() == Qt.Key_F2:
            self.edit_name()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Starts editing the name.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        self.edit_name()
        event.accept()

    def _is_in_wip_relationship(self):
        return any(arc_item.rel_item.is_wip for arc_item in self.arc_items)

    def _is_target_valid(self):
        """Whether or not the registered merge target is valid.

        Returns:
            bool
        """
        return (
            self._merge_target
            and isinstance(self._merge_target, ObjectItem)
            and (self._is_in_wip_relationship() or self._merge_target._is_in_wip_relationship())
            and self._merge_target.entity_class_id == self.entity_class_id
        )

    def merge_into_target(self, force=False):
        """Merges this item into the registered target if valid.

        Args:
            force (bool)

        Returns:
            bool: True if merged, False if not.
        """
        if not self._is_target_valid() and not force:
            return False
        if not self.is_wip and self._merge_target.is_wip:
            # Make sure we don't merge a non-wip into a wip item
            other = self._merge_target
            other._merge_target = self
            return other.merge_into_target(force=force)
        for arc_item in self.arc_items:
            arc_item.obj_item = self._merge_target
        if not all(arc_item.rel_item.validate_member_objects() for arc_item in self.arc_items):
            # Revert
            for arc_item in self.arc_items:
                arc_item.obj_item = self
            return False
        self._merge_target.arc_items.extend(self.arc_items)
        self.move_arc_items(self._merge_target.pos() - self.pos())
        self.scene().removeItem(self)
        return True

    def _show_item_context_menu_in_parent(self, pos):
        self._graph_view_form.show_object_item_context_menu(pos, self)


class EntityLabelItem(QGraphicsTextItem):
    """Label item for items in GraphViewForm."""

    entity_name_edited = Signal(str)

    def __init__(self, entity_item):
        """Initializes item.

        Args:
            entity_item (spinetoolbox.widgets.graph_view_graphics_items.EntityItem): The parent item.
        """
        super().__init__(entity_item)
        self.entity_item = entity_item
        self._font = QApplication.font()
        self._font.setPointSize(11)
        self.setFont(self._font)
        self.bg = QGraphicsRectItem(self)
        color = QGuiApplication.palette().color(QPalette.Normal, QPalette.ToolTipBase)
        color.setAlphaF(0.8)
        self.set_bg_color(color)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setAcceptHoverEvents(False)
        self._cursor = self.textCursor()
        self._text_backup = None

    def setPlainText(self, text):
        """Set texts and resets position.

        Args:
            text (str)
        """
        super().setPlainText(text)
        self.reset_position()

    def reset_position(self):
        """Adapts item geometry so text is always centered."""
        rectf = self.boundingRect()
        x = -rectf.width() / 2
        y = rectf.height() + 4
        self.setPos(x, y)
        self.bg.setRect(self.boundingRect())

    def set_bg_color(self, bg_color):
        """Sets background color.

        Args:
            bg_color (QColor)
        """
        self.bg.setBrush(QBrush(bg_color))

    def start_editing(self):
        """Starts editing."""
        self.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.setFocus()
        cursor = QTextCursor(self._cursor)
        cursor.select(QTextCursor.Document)
        self.setTextCursor(cursor)
        self._text_backup = self.toPlainText()

    def keyPressEvent(self, event):
        """Keeps text centered as the user types.
        Gives up focus when the user presses Enter or Return.

        Args:
            event (QKeyEvent)
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
        elif event.key() == Qt.Key_Escape:
            self.setPlainText(self._text_backup)
            self.clearFocus()
        else:
            super().keyPressEvent(event)
        self.reset_position()

    def focusOutEvent(self, event):
        """Ends editing and sends entity_name_edited signal."""
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.entity_name_edited.emit(self.toPlainText())
        self.setTextCursor(self._cursor)

    def mouseDoubleClickEvent(self, event):
        """Starts editing the name.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        self.start_editing()


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm. Connects a RelationshipItem to an ObjectItem."""

    def __init__(self, rel_item, obj_item, width, is_wip=False):
        """Initializes item.

        Args:
            rel_item (spinetoolbox.widgets.graph_view_graphics_items.RelationshipItem): relationship item
            obj_item (spinetoolbox.widgets.graph_view_graphics_items.ObjectItem): object item
            width (float): Preferred line width
        """
        super().__init__()
        self.rel_item = rel_item
        self.obj_item = obj_item
        self._width = float(width)
        self.is_wip = is_wip
        src_x = rel_item.x()
        src_y = rel_item.y()
        dst_x = obj_item.x()
        dst_y = obj_item.y()
        self.setLine(src_x, src_y, dst_x, dst_y)
        self._pen = QPen()
        self._pen.setWidth(self._width)
        color = QGuiApplication.palette().color(QPalette.Normal, QPalette.WindowText)
        color.setAlphaF(0.8)
        self._pen.setColor(color)
        self._pen.setStyle(Qt.SolidLine)
        self._pen.setCapStyle(Qt.RoundCap)
        self.setPen(self._pen)
        self.setZValue(-2)
        rel_item.add_arc_item(self)
        obj_item.add_arc_item(self)
        if self.is_wip:
            self.become_wip()
        self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Accepts the event so it's not propagated."""
        event.accept()

    def other_item(self, item):
        return {self.rel_item: self.obj_item, self.obj_item: self.rel_item}.get(item)

    def become_wip(self):
        """Turns this arc into a work-in-progress."""
        self.is_wip = True
        self._pen.setStyle(Qt.DotLine)
        self.setPen(self._pen)

    def become_whole(self):
        """Removes the wip status from this arc."""
        self.is_wip = False
        self._pen.setStyle(Qt.SolidLine)
        self.setPen(self._pen)

    def move_rel_item_by(self, pos_diff):
        """Moves source point.

        Args:
            pos_diff (QPoint)
        """
        line = self.line()
        line.setP1(line.p1() + pos_diff)
        self.setLine(line)

    def move_obj_item_by(self, pos_diff):
        """Moves destination point.

        Args:
            pos_diff (QPoint)
        """
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)

    def adjust_to_zoom(self, transform):
        """Adjusts the item's geometry so it stays the same size after performing a zoom.

        Args:
            transform (QTransform): The view's transformation matrix after the zoom.
        """
        factor = transform.m11()
        if factor < 1:
            return
        scaled_width = self._width / factor
        self._pen.setWidthF(scaled_width)
        self.setPen(self._pen)

    def wipe_out(self):
        self.obj_item.arc_items.remove(self)
        self.rel_item.arc_items.remove(self)


class OutlinedTextItem(QGraphicsSimpleTextItem):
    """Outlined text item."""

    def __init__(self, text, parent, font=QFont(), brush=QBrush(Qt.white), outline_pen=QPen(Qt.black, 3, Qt.SolidLine)):
        """Initializes item.

        Args:
            text (str): text to show
            font (QFont, optional): font to display the text
            brush (QBrush, optional)
            outline_pen (QPen, optional)
        """
        super().__init__(text, parent)
        font.setWeight(QFont.Black)
        self.setFont(font)
        self.setBrush(brush)
        self.setPen(outline_pen)
