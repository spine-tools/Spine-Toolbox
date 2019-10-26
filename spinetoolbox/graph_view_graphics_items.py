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
Classes for drawing graphics items on graph view/s QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""
from PySide2.QtCore import Qt, QRectF, QPointF
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
from PySide2.QtGui import QColor, QPen, QBrush, QPainterPath, QFont, QTextCursor


class ObjectItem(QGraphicsPixmapItem):
    def __init__(self, graph_view_form, x, y, extent, object_id=None, object_class_id=None, label_color=Qt.transparent):
        """Object item to use with GraphViewForm.

        Args:
            graph_view_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            object_id (int): object id
            object_class_id (int): object class id
            label_color (QColor): label bg color
        """
        super().__init__()
        self._graph_view_form = graph_view_form
        self.db_mngr = graph_view_form.db_mngr
        self.db_map = graph_view_form.db_map
        self.object_id = object_id
        self._object_class_id = object_class_id
        self._extent = extent
        self._label_color = label_color
        self._object_name = f"<unnamed {self.object_class_name}>"
        self.label_item = ObjectLabelItem(self, label_color)
        self.incoming_arc_items = list()
        self.outgoing_arc_items = list()
        self.is_template = False
        self.template_id = None  # id of relationship templates
        self.question_item = None  # In case this becomes a template
        self._press_pos = None
        self._merge_target = None
        self._moved_on_scene = False
        self._views_cursor = {}
        self._selected_color = graph_view_form.palette().highlight()
        pixmap = self.db_mngr.entity_class_icon(self.db_map, "object class", self.object_class_id).pixmap(extent)
        self.setPixmap(pixmap.scaled(extent, extent))
        self.setPos(x, y)
        self.setOffset(-0.5 * extent, -0.5 * extent)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.shade = QGraphicsRectItem(super().boundingRect(), self)
        self.shade.setBrush(self._selected_color)
        self.shade.setPen(Qt.NoPen)
        self.shade.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
        self.shade.hide()
        self.setZValue(0)
        self.label_item.setZValue(1)

    @property
    def object_name(self):
        return self.db_mngr.get_item(self.db_map, "object", self.object_id).get("name", self._object_name)

    @property
    def object_class_id(self):
        return self.db_mngr.get_item(self.db_map, "object", self.object_id).get("class_id", self._object_class_id)

    @property
    def object_class_name(self):
        return self.db_mngr.get_item(self.db_map, "object class", self.object_class_id).get("name")

    def shape(self):
        """Make the entire bounding rect to be the shape."""
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def boundingRect(self):
        """Include children's bounding rect so they are correctly painted."""
        return super().boundingRect() | self.childrenBoundingRect()

    def paint(self, painter, option, widget=None):
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            if self.label_item.hasFocus():
                self.shade.hide()
            else:
                self.shade.show()
            option.state &= ~QStyle.State_Selected
        else:
            self.shade.hide()
        super().paint(painter, option, widget)

    def become_template(self):
        """Become a template."""
        self.is_template = True
        font = QFont("", 0.75 * self._extent)
        brush = QBrush(Qt.white)
        outline_pen = QPen(Qt.black, 8, Qt.SolidLine)
        self.question_item = OutlinedTextItem("?", font, brush=brush, outline_pen=outline_pen)
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
                This item is part of a <i>template</i> for a relationship
                and needs to be associated with an object.
                Please do one of the following:
                <ul>
                <li>Give this item a name to create a new <b>{0}</b> object (select it and press F2).</li>
                <li>Drag-and-drop this item onto an existing <b>{0}</b> object (or viceversa)</li>
                </ul>
                </html>""".format(
                    self.object_class_name
                )
            )
        else:
            self.setToolTip(
                """
                <html>
                This item is a <i>template</i> for a <b>{0}</b>.
                Please give it a name to create a new <b>{0}</b> object (select it and press F2).
                </html>""".format(
                    self.object_class_name
                )
            )

    def become_whole(self):
        """Make this arc no longer a template."""
        self.is_template = False
        self.scene().removeItem(self.question_item)
        self.setToolTip("")

    def edit_name(self):
        """Start editing object name."""
        self.setSelected(True)
        self.label_item.setTextInteractionFlags(Qt.TextEditorInteraction)
        self.label_item.setFocus()
        cursor = QTextCursor(self.label_item._cursor)
        cursor.select(QTextCursor.Document)
        self.label_item.setTextCursor(cursor)

    def finish_name_editing(self):
        """Called by the label item when editing finishes."""
        self.label_item.setTextInteractionFlags(Qt.NoTextInteraction)
        self._object_name = self.label_item.toPlainText()
        if self.is_template:
            # Add
            object_id = self._graph_view_form.add_object(self, self._object_name)
            if not object_id:
                return
            self.object_id = object_id
            self.label_item.refresh_name()  # For 'fun', mostly
            self.become_whole()
            if not self.template_id:
                return
            self._graph_view_form.add_relationship(self.template_id)
        else:
            # Update
            self._graph_view_form.update_object(self, self._object_name)

    def add_incoming_arc_item(self, arc_item):
        """Add an ArcItem to the list of incoming arcs."""
        self.incoming_arc_items.append(arc_item)

    def add_outgoing_arc_item(self, arc_item):
        """Add an ArcItem to the list of outgoing arcs."""
        self.outgoing_arc_items.append(arc_item)

    def itemChange(self, change, value):
        """
        Keeps track on item's movements on the scene.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
             Whatever super() does with the value parameter
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
        return value

    def keyPressEvent(self, event):
        """Triggers name editing."""
        if event.key() == Qt.Key_F2:
            self.edit_name()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Triggers name editing."""
        self.edit_name()
        event.accept()

    def mousePressEvent(self, event):
        """Saves original position."""
        super().mousePressEvent(event)
        self._press_pos = self.pos()
        self._merge_target = None

    def _find_merge_target(self, scene_pos):
        """Returns a suitable merge target.
        Used for building a relationship."""
        candidates = [x for x in self.scene().items(scene_pos) if isinstance(x, ObjectItem) and x != self]
        return next(iter(candidates), None)

    def _is_target_valid(self):
        return (
            self._merge_target
            and self._merge_target.is_template != self.is_template
            and (self.template_id or self._merge_target.template_id)
            and self._merge_target.object_class_id == self.object_class_id
        )

    def mouseMoveEvent(self, event):
        """Calls move related items and checks for a merge target."""
        if event.buttons() & Qt.LeftButton == 0:
            super().mouseMoveEvent(event)
            return
        # We need to manually move ObjectItems because the ItemIgnoresTransformations flag
        # prevents the default movement working properly when the scene rect changes
        # during the movement.
        move_by = event.scenePos() - event.lastScenePos()
        # Move selected items together
        selected_items = [x for x in self.scene().selectedItems() if isinstance(x, ObjectItem)]
        for item in selected_items:
            item.moveBy(move_by.x(), move_by.y())
            item.move_related_items_by(move_by)
        self._merge_target = self._find_merge_target(event.scenePos())
        # Depending on the value of merge target and bounce, set drop indicator cursor
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
        """Merge, bounce, notify scene or just do nothing."""
        super().mouseReleaseEvent(event)
        if self._merge_target:
            if self.merge_into_target():
                return
            self._bounce_back(self.pos())
        if self._moved_on_scene:
            self._moved_on_scene = False
            self.scene().shrink_if_needed()

    def _bounce_back(self, current_pos):
        """Bounce item back from given position to press position."""
        if self._press_pos is None:
            return
        self.move_related_items_by(self._press_pos - current_pos)
        self.setPos(self._press_pos)

    def merge_into_target(self):
        """Merges this item into the target."""
        if not self._is_target_valid():
            return False
        if not self.is_template:
            # Merge the template into the whole, by convention
            template = self._merge_target
            template._merge_target = self
            return template.merge_into_target()
        relationship_template = self._graph_view_form.relationship_templates.get(self.template_id)
        if not relationship_template:
            return False
        object_items = relationship_template["object_items"]
        if [x for x in object_items if x.is_template] == [self]:
            # It's time to try and add the relationship
            self.object_id = self._merge_target.object_id
            relationship_id = self._graph_view_form.add_relationship(self.template_id)
            if not relationship_id:
                return False
            self._graph_view_form.remove_relationship_template(self.template_id, relationship_id)
        else:
            object_items[object_items.index(self)] = self._merge_target
        self.do_merge_into_target()
        return True

    def do_merge_into_target(self):
        self.move_related_items_by(self._merge_target.pos() - self.pos())
        for arc_item in self.outgoing_arc_items:
            arc_item.src_item = self._merge_target
        for arc_item in self.incoming_arc_items:
            arc_item.dst_item = self._merge_target
        self._merge_target.incoming_arc_items.extend(self.incoming_arc_items)
        self._merge_target.outgoing_arc_items.extend(self.outgoing_arc_items)
        self.scene().removeItem(self)

    def move_related_items_by(self, pos_diff):
        """Moves related items."""
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
        self._graph_view_form.show_object_item_context_menu(e, self)

    def set_all_visible(self, on):
        """Sets visibility status for this item and all related items."""
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
    def __init__(self, object_item, bg_color):
        """Object label item to use with GraphViewForm.

        Args:
            object_item (ObjectItem): the ObjectItem instance
            bg_color (QColor): color to paint the label
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
        self.refresh_name()

    def refresh_name(self):
        self.setPlainText(self.object_item.object_name)
        self.reset_position()

    def reset_position(self):
        """Centers this item."""
        rectf = self.boundingRect()
        x = -rectf.width() / 2
        y = -rectf.height() / 2
        self.setPos(x, y)
        self.bg.setRect(self.boundingRect())

    def set_bg_color(self, bg_color):
        """Set background color."""
        self.bg.setBrush(QBrush(bg_color))

    def keyPressEvent(self, event):
        """Give up focus when the user presses Enter or Return.
        In the meantime, adapt item geometry so text is always centered.
        """
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.clearFocus()
        else:
            super().keyPressEvent(event)
        self.reset_position()

    def focusOutEvent(self, event):
        """Call method to finish name editing in object item."""
        super().focusOutEvent(event)
        self.object_item.finish_name_editing()
        self.setTextCursor(self._cursor)


class ArcItem(QGraphicsLineItem):
    def __init__(
        self,
        graph_view_form,
        src_item,
        dst_item,
        width,
        arc_color,
        relationship_id=None,
        relationship_class_id=None,
        token_color=QColor(),
        token_object_extent=0,
        token_object_label_color=QColor(),
    ):
        """Arc item to use with GraphViewForm.

        Args:
            graph_view_form (GraphViewForm): 'owner'
            src_item (ObjectItem): source item
            dst_item (ObjectItem): destination item
            width (float): Preferred line width
            arc_color (QColor): arc color
            relationship_id (int): relationship id
            token_object_extent (int): token preferred extent
            token_color (QColor): token bg color
        """
        super().__init__()
        self._graph_view_form = graph_view_form
        self.db_mngr = graph_view_form.db_mngr
        self.db_map = graph_view_form.db_map
        self.relationship_id = relationship_id
        self._relationship_class_id = relationship_class_id
        self.src_item = src_item
        self.dst_item = dst_item
        self._width = float(width)
        self.is_template = False
        self.template_id = None
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
        """Try and make it more clear when an item is selected."""
        if option.state & (QStyle.State_Selected):
            self.setPen(self.selected_pen)
            option.state &= ~QStyle.State_Selected
        else:
            self.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def become_template(self):
        """Make this arc part of a template for a relationship."""
        self.is_template = True
        self.normal_pen.setStyle(Qt.DotLine)
        self.selected_pen.setStyle(Qt.DotLine)

    def become_whole(self):
        """Make this arc no longer part of a template for a relationship."""
        self.is_template = False
        self.normal_pen.setStyle(Qt.SolidLine)
        self.selected_pen.setStyle(Qt.SolidLine)

    def move_src_by(self, pos_diff):
        """Move source point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP1(line.p1() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def move_dst_by(self, pos_diff):
        """Move destination point by pos_diff. Used when moving ObjectItems around."""
        line = self.line()
        line.setP2(line.p2() + pos_diff)
        self.setLine(line)
        self.token_item.update_pos()

    def adjust_to_zoom(self, factor):
        """Update item geometry after performing a zoom.
        This is so items stay the same size (that is, the zoom controls the *spread*)."""
        scaled_width = self._width / factor
        self.normal_pen.setWidthF(scaled_width)
        self.selected_pen.setWidthF(scaled_width)


class ArcTokenItem(QGraphicsEllipseItem):
    def __init__(self, arc_item, color, object_extent, object_label_color):
        """Arc token item to use with GraphViewForm.

        Args:
            arc_item (ArcItem): the ArcItem instance
            color (QColor): color to paint the token
            object_extent (int): Preferred extent
            object_label_color (QColor): Preferred extent
            object_name_tuples (Iterable): one or more (object class name, object name) tuples
        """
        super().__init__(arc_item)
        self.arc_item = arc_item
        x = 0.0
        object_class_id_list = [int(id_) for id_ in arc_item.object_class_id_list.split(",")]
        object_name_list = arc_item.object_name_list.split(",")
        for j, args in enumerate(zip(object_class_id_list, object_name_list)):
            if not args:
                continue
            object_item = SimpleObjectItem(self, 0.875 * object_extent, object_label_color, *args)
            if j % 2 == 0:
                y = 0.0
            else:
                y = -0.875 * 0.75 * object_item.boundingRect().height()
                object_item.setZValue(-1)
            object_item.setPos(x, y)
            x += 0.875 * 0.5 * object_item.boundingRect().width()
        rectf = self.direct_children_bounding_rect()
        offset = -rectf.topLeft()
        for item in self.childItems():
            item.setOffset(offset)
        rectf = self.direct_children_bounding_rect()
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
        self._zoomed_position_offset = QPointF(0.0, 0.0)
        self.setTransformOriginPoint(self.boundingRect().center())
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)

    def boundingRect(self):
        """Include children's bounding rect so they are correctly painted."""
        return self.childrenBoundingRect() | super().boundingRect()

    def direct_children_bounding_rect(self):
        """Alternative to childrenBoundingRect that only goes one generation forward."""
        rectf = QRectF()
        for item in self.childItems():
            rectf |= item.sceneBoundingRect()
        return rectf

    def update_pos(self):
        """Put token item in position."""
        center = self.arc_item.line().center()
        self.setPos(center - self._zoomed_position_offset)

    def adjust_to_zoom(self, factor):
        """Update item geometry after performing a zoom.
        This is so items stay the same size (that is, the zoom controls the *spread*)."""
        rect = self.rect()
        rect.setWidth(rect.width() / factor)
        rect.setHeight(rect.height() / factor)
        self._zoomed_position_offset = rect.center()
        self.update_pos()


class SimpleObjectItem(QGraphicsPixmapItem):
    def __init__(self, parent, extent, label_color, object_class_id, object_name):
        """Object item to use with GraphViewForm.

        Args:
            parent (ArcTokenItem): arc token item
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

    def setOffset(self, offset):
        super().setOffset(offset)
        self.text_item.moveBy(offset.x(), offset.y())


class OutlinedTextItem(QGraphicsSimpleTextItem):
    def __init__(self, text="", font=QFont(), brush=QBrush(Qt.black), outline_pen=QPen(Qt.white, 3, Qt.SolidLine)):
        """Outlined text item to use with GraphViewForm.

        Args:
            text (str): text to show
            font (QFont): font to display the text
            brush (QBrus)
            outline_pen (QPen)
        """
        super().__init__()
        self.setText(text)
        font.setWeight(QFont.Black)
        self.setFont(font)
        self.setBrush(brush)
        self.setPen(outline_pen)


class CustomTextItem(QGraphicsTextItem):
    def __init__(self, html, font):
        """Custom text item to use with GraphViewForm.

        Args:
            html (str): text to show
            font (QFont): font to display the text
        """
        super().__init__()
        self.setHtml(html)
        # font.setWeight(QFont.Black)
        self.setFont(font)
        self.adjustSize()
        self.setTextInteractionFlags(Qt.TextBrowserInteraction)
        # self.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
