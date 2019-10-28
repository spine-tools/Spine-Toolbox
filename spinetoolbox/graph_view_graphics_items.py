######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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
from PySide2.QtCore import Qt, Signal, Slot, QRectF, QPointF
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
    QGraphicsSimpleTextItem,
    QGraphicsRectItem,
    QGraphicsPixmapItem,
    QGraphicsLineItem,
    QStyle,
    QApplication,
)
from PySide2.QtGui import QColor, QPen, QBrush, QPainterPath, QFont, QTextCursor, QTransform


class ObjectItem(QGraphicsPixmapItem):
    def __init__(
        self,
        graph_view_form,
        x,
        y,
        extent,
        object_id=None,
        object_class_id=None,
        template_id=None,
        label_color=Qt.transparent,
    ):
        """Initializes the item.

        Args:
            graph_view_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            object_id (int, optional): object id, if not given the item becomes a template
            object_class_id (int, optional): object class id, for template items
            template_id (int, optional): the relationship template id, in case this item is part of one
            label_color (QColor): label bg color

        Raises:
            ValueError: in case object_id and object_class_id are both not provided
        """
        super().__init__()
        if not object_id and not object_class_id:
            raise ValueError("Can't create an ObjectItem without object id nor object class id.")
        self._graph_view_form = graph_view_form
        self.db_mngr = graph_view_form.db_mngr
        self.db_map = graph_view_form.db_map
        self.object_id = object_id
        self._object_class_id = object_class_id
        self._object_name = f"<unnamed {self.object_class_name}>"
        self._extent = extent
        self._label_color = label_color
        self.is_template = None
        self.template_id = template_id  # id of relationship templates
        self.label_item = ObjectLabelItem(self, label_color)
        self.label_item.object_name_changed.connect(self.finish_name_editing)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.question_item = None  # In case this becomes a template
        self._press_pos = None
        self._merge_target = None
        self._moved_on_scene = False
        self._views_cursor = {}
        self.refresh_icon()
        self.refresh_name()
        self.setPos(x, y)
        self.setOffset(-0.5 * extent, -0.5 * extent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self._selection_halo = QGraphicsRectItem(super().boundingRect(), self)
        self._selection_halo.setBrush(graph_view_form.palette().highlight())
        self._selection_halo.setPen(Qt.NoPen)
        self._selection_halo.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
        self._selection_halo.hide()
        self.setZValue(0)
        self.label_item.setZValue(1)
        self._view_transform = QTransform()
        if not self.object_id:
            self.become_template()

    @property
    def object_name(self):
        return self.db_mngr.get_item(self.db_map, "object", self.object_id).get("name", self._object_name)

    @property
    def object_class_id(self):
        return self.db_mngr.get_item(self.db_map, "object", self.object_id).get("class_id", self._object_class_id)

    @property
    def object_class_name(self):
        return self.db_mngr.get_item(self.db_map, "object class", self.object_class_id).get("name")

    def refresh_icon(self):
        """Refreshes the icon."""
        pixmap = self.db_mngr.entity_class_icon(self.db_map, "object class", self.object_class_id).pixmap(self._extent)
        self.setPixmap(pixmap)

    def refresh_name(self):
        """Refreshes the name."""
        self.label_item.setPlainText(self.object_name)

    def shape(self):
        """Returns a shape containing the entire bounding rect, to work better with icon transparency."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget=None):
        """Shows or hides the selection halo."""
        if option.state & (QStyle.State_Selected):
            self._selection_halo.setVisible(not self.label_item.hasFocus())
            option.state &= ~QStyle.State_Selected
        else:
            self._selection_halo.hide()
        super().paint(painter, option, widget)

    def become_template(self):
        """Turns this item into a template."""
        self.is_template = True
        font = QFont("", 0.75 * self._extent)
        self.question_item = OutlinedTextItem("?", font)
        self.question_item.setParentItem(self)
        rect = self.boundingRect()
        question_rect = self.question_item.boundingRect()
        x = rect.center().x() - question_rect.width() / 2
        y = rect.center().y() - question_rect.height() / 2
        self.question_item.setPos(x, y)
        if self.template_id:
            self.setToolTip(
                """
                <html>
                Template for a <b>{0}</b>, also part of a relationship.
                Please give it a name or merge it into an existing <b>{0}</b> entity.
                </html>""".format(
                    self.object_class_name
                )
            )
        else:
            self.setToolTip(
                """
                <html>
                Template for a <b>{0}</b>.
                Please give it a name.
                </html>""".format(
                    self.object_class_name
                )
            )

    def become_whole(self):
        """Removes the template status from this item."""
        self.is_template = False
        self.scene().removeItem(self.question_item)
        self.setToolTip("")

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
        self._object_name = text
        if self.is_template:
            # Add
            object_id = self._graph_view_form.add_object(self._object_class_id, self._object_name)
            if not object_id:
                return
            self.object_id = object_id
            self.refresh_name()  # Is this doing something?
            self.become_whole()
            if not self.template_id:
                return
            self._graph_view_form.add_relationship(self.template_id)
        else:
            # Update
            self._graph_view_form.update_object(self.object_id, self._object_name)

    def add_incoming_arc_item(self, arc_item):
        """Adds an item to the list of incoming arcs.

        Args:
            arc_item (ArcItem)
        """
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Adds an item to the list of outgoing arcs.

        Args:
            arc_item (ArcItem)
        """
        self.outgoing_arc_items.append(arc_item)

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

    def mousePressEvent(self, event):
        """Saves original position for bouncing purposes.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        super().mousePressEvent(event)
        self._press_pos = self.pos()
        self._merge_target = None

    def adjust_to_zoom(self, transform):
        """Saves the view's transform to determine collisions.

        Args:
            transform (QTransform): The view's transformation matrix after the zoom.
        """
        self._view_transform = transform

    def device_rect(self):
        """Returns the item's rect in devices's coordinates."""
        return self.deviceTransform(self._view_transform).mapRect(self.boundingRect())

    def _find_merge_target(self):
        """Returns a suitable merge target if any.

        Returns:
            ObjectItem, NoneType
        """
        scene = self.scene()
        if not scene:
            return None
        colliding = [
            x
            for x in scene.items()
            if isinstance(x, ObjectItem) and x is not self and x.device_rect().intersects(self.device_rect())
        ]
        return next(iter(colliding), None)

    def _is_target_valid(self):
        """Whether or not the registered merge target is valid.

        Returns:
            bool
        """
        return (
            self._merge_target
            and self._merge_target.is_template != self.is_template
            and (self.template_id is not None or self._merge_target.template_id is not None)
            and self._merge_target.object_class_id == self.object_class_id
        )

    def mouseMoveEvent(self, event):
        """Moves the item and all connected arcs. Also checks for a merge target
        and sets an appropriate mouse cursor.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        if event.buttons() & Qt.LeftButton == 0:
            super().mouseMoveEvent(event)
            return
        # We need to manually move ObjectItems because the ItemIgnoresTransformations flag
        # prevents the default movement working properly when the scene rect changes
        # during the movement.
        move_by = event.scenePos() - event.lastScenePos()
        # Move selected items together
        for item in self.scene().selectedItems():
            if isinstance(item, ObjectItem):
                item.moveBy(move_by.x(), move_by.y())
                item.move_related_items(move_by)
        self._merge_target = self._find_merge_target()
        for view in self.scene().views():
            self._views_cursor.setdefault(view, view.viewport().cursor())
            if not self._merge_target:
                try:
                    view.viewport().setCursor(self._views_cursor[view])
                except KeyError:
                    pass
                continue
            elif self._is_target_valid():
                view.viewport().setCursor(Qt.DragCopyCursor)
            else:
                view.viewport().setCursor(Qt.ForbiddenCursor)

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
            self.scene().shrink_if_needed()

    def _bounce_back(self, current_pos):
        """Bounces the item back from given position to its original position.

        Args:
            current_pos (QPoint)
        """
        if self._press_pos is None:
            return
        self.move_related_items(self._press_pos - current_pos)
        self.setPos(self._press_pos)

    def merge_into_target(self):
        """Merges this item into the registered target if valid.

        Returns:
            bool: True if merged, False if not.
        """
        if not self._is_target_valid():
            return False
        if not self.is_template:
            # Merge the other into this, so we always merge template into whole
            other = self._merge_target
            other._merge_target = self
            return other.merge_into_target()
        try:
            relationship_template = self._graph_view_form.relationship_templates[self.template_id]
        except IndexError:
            return False
        object_items = relationship_template["object_items"]
        if [x for x in object_items if x.is_template] == [self]:
            # It's time to try and add the relationship
            self.object_id = self._merge_target.object_id
            relationship_id = self._graph_view_form.add_relationship(self.template_id)
            if not relationship_id:
                return False
        else:
            object_items[object_items.index(self)] = self._merge_target
            self._merge_target.template_id = self.template_id
        self.do_merge_into_target()
        return True

    def do_merge_into_target(self):
        """Merges this item into the registered target without any verification."""
        self.move_related_items(self._merge_target.pos() - self.pos())
        for arc_item in self.outgoing_arc_items:
            arc_item.src_item = self._merge_target
        for arc_item in self.incoming_arc_items:
            arc_item.dst_item = self._merge_target
        self._merge_target.incoming_arc_items.extend(self.incoming_arc_items)
        self._merge_target.outgoing_arc_items.extend(self.outgoing_arc_items)
        self.scene().removeItem(self)

    def move_related_items(self, pos_diff):
        """Moves related items.

        Args:
            pos_diff (QPoint)
        """
        for item in self.outgoing_arc_items:
            item.move_src_by(pos_diff)
        for item in self.incoming_arc_items:
            item.move_dst_by(pos_diff)

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        e.accept()
        if not self.isSelected() and not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        self._graph_view_form.show_object_item_context_menu(e.screenPos(), self)

    def set_all_visible(self, on):
        """Sets visibility status for this item and all related items.

        Args:
            on (bool)
        """
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            item.setVisible(on)
        self.setVisible(on)

    def wipe_out(self):
        """Removes this item and all related items from the scene."""
        scene = self.scene()
        for item in self.incoming_arc_items + self.outgoing_arc_items:
            if not item.scene():
                # Already removed
                continue
            scene.removeItem(item)
        scene.removeItem(self)


class ObjectLabelItem(QGraphicsTextItem):
    """Object label item to use with GraphViewForm."""

    object_name_changed = Signal(str, name="object_name_changed")

    def __init__(self, object_item, bg_color):
        """Initializes item.

        Args:
            object_item (ObjectItem): The parent item.
            bg_color (QColor): Color for the label.
        """
        super().__init__(object_item)
        self.object_item = object_item
        self._font = QApplication.font()
        self._font.setPointSize(11)
        self.setFont(self._font)
        self.bg = QGraphicsRectItem(self)
        self.set_bg_color(bg_color)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setAcceptHoverEvents(False)
        self._cursor = self.textCursor()

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

    def keyPressEvent(self, event):
        """Keeps text centered as the user types.
        Gives up focus when the user presses Enter or Return.

        Args:
            event (QKeyEvent)
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
        else:
            super().keyPressEvent(event)
        self.reset_position()

    def focusOutEvent(self, event):
        """Ends editing and sends object_name_changed signal."""
        super().focusOutEvent(event)
        self.setTextInteractionFlags(Qt.NoTextInteraction)
        self.object_name_changed.emit(self.toPlainText())
        self.setTextCursor(self._cursor)

    def mouseDoubleClickEvent(self, event):
        """Starts editing the name.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        self.start_editing()


class ArcItem(QGraphicsLineItem):
    """Arc item to use with GraphViewForm."""

    def __init__(
        self,
        graph_view_form,
        src_item,
        dst_item,
        width,
        arc_color,
        dimensions,
        relationship_id=None,
        relationship_class_id=None,
        template_id=None,
        token_color=QColor(),
        token_object_extent=0,
        token_object_label_color=QColor(),
    ):
        """Initializes item

        Args:
            graph_view_form (GraphViewForm): 'owner'
            src_item (ObjectItem): source item
            dst_item (ObjectItem): destination item
            width (float): Preferred line width
            arc_color (QColor): arc color
            dimensions (tuple): the two dimensions in the relationship this arc represents
            relationship_id (int, optional): relationship id, if not given the item becomes a template
            relationship_class_id (int, optional): relationship class id, for template items
            template_id (int, optional): the relationship template id, in case this item is part of one
            token_color (QColor): token bg color
            token_object_extent (int): token preferred extent
            token_object_label_color (QColor): token object label color
        """
        super().__init__()
        self._graph_view_form = graph_view_form
        self.db_mngr = graph_view_form.db_mngr
        self.db_map = graph_view_form.db_map
        self.dimensions = dimensions
        self.relationship_id = relationship_id
        self._relationship_class_id = relationship_class_id
        self.src_item = src_item
        self.dst_item = dst_item
        self._width = float(width)
        self.is_template = None
        self.template_id = template_id
        src_x = src_item.x()
        src_y = src_item.y()
        dst_x = dst_item.x()
        dst_y = dst_item.y()
        self.setLine(src_x, src_y, dst_x, dst_y)
        self.token_item = ArcTokenItem(self, token_color, token_object_extent, token_object_label_color)
        self.normal_pen = QPen()
        self.normal_pen.setWidth(self._width)
        self.normal_pen.setColor(arc_color)
        self.normal_pen.setStyle(Qt.SolidLine)
        self.normal_pen.setCapStyle(Qt.RoundCap)
        self.selected_pen = QPen(self.normal_pen)
        self.selected_pen.setColor(graph_view_form.palette().highlight().color())
        self.setPen(self.normal_pen)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setZValue(-2)
        src_item.add_outgoing_arc_item(self)
        dst_item.add_incoming_arc_item(self)
        self.setAcceptHoverEvents(True)
        viewport = self._graph_view_form.ui.graphicsView.viewport()
        self.viewport_cursor = viewport.cursor()
        if self.template_id:
            self.become_template()

    @property
    def relationship_class_id(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.relationship_id).get(
            "class_id", self._relationship_class_id
        )

    @property
    def object_class_id_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship class", self.relationship_class_id)[
            "object_class_id_list"
        ]

    @property
    def object_name_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.relationship_id).get(
            "object_name_list", ",".join(["<unnamed>" for _ in range(len(self.object_class_id_list))])
        )

    def paint(self, painter, option, widget=None):
        """Highlights the item when it's selected."""
        if option.state & (QStyle.State_Selected):
            self.setPen(self.selected_pen)
            option.state &= ~QStyle.State_Selected
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def become_template(self):
        """Turns this item into a template."""
        self.is_template = True
        self.normal_pen.setStyle(Qt.DotLine)
        self.selected_pen.setStyle(Qt.DotLine)

    def become_whole(self):
        """Removes the template status from this item."""
        self.is_template = False
        self.normal_pen.setStyle(Qt.SolidLine)
        self.selected_pen.setStyle(Qt.SolidLine)

    def move_src_by(self, pos_diff):
        """Moves source point.

        Args:
            pos_diff (QPoint)
        """
        line = self.line()
        line.setP1(line.p1() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def move_dst_by(self, pos_diff):
        """Moves destination point.

        Args:
            pos_diff (QPoint)
        """
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def adjust_to_zoom(self, transform):
        """Adjusts the item's geometry so it stays the same size after performing a zoom.

        Args:
            transform (QTransform): The view's transformation matrix after the zoom.
        """
        factor = transform.m11()
        scaled_width = self._width / factor
        self.normal_pen.setWidthF(scaled_width)
        self.selected_pen.setWidthF(scaled_width)


class ArcTokenItem(QGraphicsEllipseItem):
    """Arc token item to use with GraphViewForm."""

    def __init__(self, arc_item, color, object_extent, object_label_color):
        """Initializes item

        Args:
            arc_item (ArcItem): The parent item.
            color (QColor): Color for the background.
            object_extent (int): Preferred extent of object items in the token.
            object_label_color (QColor): Color for the object label.
        """
        super().__init__(arc_item)
        self._zoomed_position_offset = QPointF(0.0, 0.0)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)
        self.arc_item = arc_item
        # Get object class ids and corresponding names from the parent item
        object_class_id_list = [int(id_) for id_ in arc_item.object_class_id_list.split(",")]
        object_name_list = arc_item.object_name_list.split(",")
        object_class_id_name_list = list(zip(object_class_id_list, object_name_list))
        # Remove the dimensions covered by the endpoint
        for dim in sorted(arc_item.dimensions, reverse=True):
            object_class_id_name_list.pop(dim)
        if not object_class_id_name_list:
            # Set a minimum rect so scene shrinking works (See #452)
            self.setRect(QRectF(0, 0, 1, 1))
            return
        x = 0.0
        for j, (object_class_id, object_name) in enumerate(object_class_id_name_list):
            object_item = SimpleObjectItem(
                self, 0.875 * object_extent, object_label_color, object_class_id, object_name
            )
            if j % 2 == 0:
                y = 0.0
            else:
                y = -0.875 * 0.75 * object_item.boundingRect().height()
            object_item.setPos(x, y)
            x += 0.875 * 0.5 * object_item.boundingRect().width()
        rectf = self._direct_children_bounding_rect()
        offset = -rectf.topLeft()
        for item in self.childItems():
            item.setOffset(offset)
        rectf = self._direct_children_bounding_rect()
        width = rectf.width()
        height = rectf.height()
        if width > height:
            delta = width - height
            rectf.adjust(0, -delta / 2, 0, delta / 2)
        else:
            delta = height - width
            rectf.adjust(-delta / 2, 0, delta / 2, 0)
        self.setRect(rectf)
        self.setPen(Qt.NoPen)
        self.setBrush(color)

    def boundingRect(self):
        """Returns a rect that includes the children so they are correctly painted."""
        return self.childrenBoundingRect() | super().boundingRect()

    def _direct_children_bounding_rect(self):
        """Returns a rect that includes the direct children but none beyond
        (i.e., excludes the ObjectItemLabel of children ObjectItem's.)"""
        rectf = QRectF()
        for item in self.childItems():
            rectf |= item.sceneBoundingRect()
        return rectf

    def update_pos(self):
        """Puts the token at the center point of the arc."""
        center = self.arc_item.line().center()
        self.setPos(center - self._zoomed_position_offset)

    def adjust_to_zoom(self, transform):
        """Adjusts the item's geometry so it stays the same size after performing a zoom.

        Args:
            transform (QTransform): The view's transformation matrix after the zoom.
        """
        factor = transform.m11()
        rect = self.rect()
        rect.setWidth(rect.width() / factor)
        rect.setHeight(rect.height() / factor)
        self._zoomed_position_offset = rect.center()
        self.update_pos()


class SimpleObjectItem(QGraphicsPixmapItem):
    """Simple object item to use in ArcTokenItem."""

    def __init__(self, parent, extent, label_color, object_class_id, object_name):
        """Initializes item.

        Args:
            parent (ArcTokenItem): parent item
            extent (int): preferred extent
            label_color (QColor): label bg color
            object_class_id (int): object class id
            object_name (str): object name
        """
        super().__init__(parent)
        arc_item = parent.arc_item
        pixmap = arc_item.db_mngr.entity_class_icon(arc_item.db_map, "object class", object_class_id).pixmap(extent)
        self.setPixmap(pixmap)
        self.text_item = QGraphicsTextItem(object_name, self)
        font = QApplication.font()
        font.setPointSize(9)
        self.text_item.setFont(font)
        x = (self.boundingRect().width() - self.text_item.boundingRect().width()) / 2
        y = (self.boundingRect().height() - self.text_item.boundingRect().height()) / 2
        self.text_item.setPos(x, y)
        self.bg = QGraphicsRectItem(self.text_item.boundingRect(), self.text_item)
        self.bg.setFlag(QGraphicsItem.ItemStacksBehindParent)
        self.bg.setBrush(QBrush(label_color))
        self.setZValue(-1)

    def setOffset(self, offset):
        """Sets the offset for the item and its text item.

        Args:
            offset (QPoint)
        """
        super().setOffset(offset)
        self.text_item.moveBy(offset.x(), offset.y())


class OutlinedTextItem(QGraphicsSimpleTextItem):
    """Outlined text item to use with GraphViewForm."""

    def __init__(self, text="", font=QFont(), brush=QBrush(Qt.white), outline_pen=QPen(Qt.black, 3, Qt.SolidLine)):
        """Initializes item.

        Args:
            text (str): text to show
            font (QFont, optional): font to display the text
            brush (QBrush, optional)
            outline_pen (QPen, optional)
        """
        super().__init__()
        self.setText(text)
        font.setWeight(QFont.Black)
        self.setFont(font)
        self.setBrush(brush)
        self.setPen(outline_pen)


class CustomTextItem(QGraphicsTextItem):
    """Custom text item to use with GraphViewForm."""

    def __init__(self, html, font):
        """Initializes item.

        Args:
            html (str): text to show
            font (QFont): font to display the text
        """
        super().__init__()
        self.setHtml(html)
        self.setFont(font)
        self.adjustSize()
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
