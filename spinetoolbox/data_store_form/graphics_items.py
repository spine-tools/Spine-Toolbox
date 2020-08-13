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
from PySide2.QtCore import Qt, Signal, Slot, QLineF, QSize
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPixmapItem,
    QGraphicsPathItem,
    QStyle,
    QApplication,
    QMenu,
)
from PySide2.QtGui import QPen, QBrush, QPainterPath, QPalette, QGuiApplication
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas  # pylint: disable=no-name-in-module
from spinetoolbox.helpers import CharIconEngine
from spinetoolbox.widgets.custom_qwidgets import TitleWidgetAction


def make_figure_graphics_item(scene, z=0, static=True):
    """Creates a FigureCanvas and adds it to the given scene.
    Used for creating heatmaps and associated colorbars.

    Args:
        scene (QGraphicsScene)
        z (int, optional): z value. Defaults to 0.
        static (bool, optional): if True (the default) the figure canvas is not movable

    Returns:
        QGraphicsProxyWidget: the graphics item that represents the canvas
        Figure: the figure in the canvas
    """
    figure = Figure(tight_layout={"pad": 0})
    axes = figure.gca(xmargin=0, ymargin=0, frame_on=None)
    axes.get_xaxis().set_visible(False)
    axes.get_yaxis().set_visible(False)
    canvas = FigureCanvas(figure)
    if static:
        proxy_widget = scene.addWidget(canvas)
        proxy_widget.setAcceptedMouseButtons(0)
    else:
        proxy_widget = scene.addWidget(canvas, Qt.Window)
    proxy_widget.setZValue(z)
    return proxy_widget, figure


class EntityItem(QGraphicsPixmapItem):
    """Base class for ObjectItem and RelationshipItem."""

    def __init__(self, data_store_form, x, y, extent, entity_id=None):
        """Initializes item

        Args:
            data_store_form (DataStoreForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): Preferred extent
            entity_id (int): The entity id
        """
        super().__init__()
        self._data_store_form = data_store_form
        self.db_mngr = data_store_form.db_mngr
        self.db_map = data_store_form.graph_db_map
        self.entity_id = entity_id
        self.arc_items = list()
        self._extent = extent
        self.refresh_icon()
        self.setPos(x, y)
        rect = self.boundingRect()
        self.setOffset(-rect.width() / 2, -rect.height() / 2)
        self._moved_on_scene = False
        self._bg = None
        self._bg_brush = Qt.NoBrush
        self._init_bg()
        self._bg.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)
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
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id)["name"]

    @property
    def entity_class_type(self):
        return {"relationship": "relationship_class", "object": "object_class"}[self.entity_type]

    @property
    def entity_class_id(self):
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id)["class_id"]

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, self.entity_class_type, self.entity_class_id)["name"]

    @property
    def first_db_map(self):
        return self.db_map

    @property
    def display_data(self):
        return self.entity_name

    @property
    def display_database(self):
        return self.db_map.codename

    @property
    def db_maps(self):
        return (self.db_map,)

    def db_map_data(self, _db_map):
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id)

    def db_map_id(self, _db_map):
        return self.entity_id

    def boundingRect(self):
        return super().boundingRect() | self.childrenBoundingRect()

    def moveBy(self, dx, dy):
        super().moveBy(dx, dy)
        self.update_arcs_line()

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
        path.setFillRule(Qt.WindingFill)
        path.addRect(self._bg.boundingRect())
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
        arc_item.update_line()

    def apply_zoom(self, factor):
        """Applies zoom.

        Args:
            factor (float): The zoom factor.
        """
        if factor > 1:
            factor = 1
        self.setScale(factor)

    def apply_rotation(self, angle, center):
        """Applies rotation.

        Args:
            angle (float): The angle in degrees.
            center (QPoint): Rotates around this point.
        """
        line = QLineF(center, self.pos())
        line.setAngle(line.angle() + angle)
        self.setPos(line.p2())
        self.update_arcs_line()

    def block_move_by(self, dx, dy):
        self.moveBy(dx, dy)

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
                item.block_move_by(move_by.x(), move_by.y())

    def update_arcs_line(self):
        """Moves arc items."""
        for item in self.arc_items:
            item.update_line()

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

    def _make_menu(self):
        menu = QMenu(self._data_store_form)
        menu.addAction(self._data_store_form.ui.actionSave_positions)
        menu.addAction(self._data_store_form.ui.actionClear_positions)
        menu.addSeparator()
        menu.addAction(self._data_store_form.ui.actionHide_selected)
        menu.addAction(self._data_store_form.ui.actionPrune_selected_entities)
        menu.addAction(self._data_store_form.ui.actionPrune_selected_classes)
        menu.addSeparator()
        menu.addAction(self._data_store_form.ui.actionEdit_selected)
        menu.addAction(self._data_store_form.ui.actionRemove_selected)
        return menu

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        e.accept()
        if not self.isSelected() and not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        self._data_store_form._handle_menu_graph_about_to_show()
        self._menu.popup(e.screenPos())


class RelationshipItem(EntityItem):
    """Represents a relationship in the Entity graph."""

    def __init__(self, data_store_form, x, y, extent, entity_id=None):
        """Initializes the item.

        Args:
            data_store_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            entity_id (int): object id
        """
        super().__init__(data_store_form, x, y, extent, entity_id=entity_id)
        self._menu = self._make_menu()
        self.setToolTip(self._make_tool_tip())

    @property
    def entity_type(self):
        return "relationship"

    @property
    def object_class_id_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship_class", self.entity_class_id)["object_class_id_list"]

    @property
    def object_name_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.entity_id)["object_name_list"]

    @property
    def object_id_list(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.entity_id)["object_id_list"]

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.db_map, "relationship", self.entity_id)["class_name"]

    @property
    def db_representation(self):
        return dict(
            class_id=self.entity_class_id,
            id=self.entity_id,
            object_id_list=self.object_id_list,
            object_name_list=self.object_name_list,
        )

    def _make_tool_tip(self):
        return (
            f"""<html><p style="text-align:center;">{self.entity_class_name}<br>"""
            f"""{self.object_name_list.replace(",", self.db_mngr._GROUP_SEP)}</p></html>"""
        )

    def _init_bg(self):
        extent = self._extent
        self._bg = QGraphicsEllipseItem(-0.5 * extent, -0.5 * extent, extent, extent, self)
        self._bg.setPen(Qt.NoPen)
        bg_color = QGuiApplication.palette().color(QPalette.Normal, QPalette.Window)
        bg_color.setAlphaF(0.8)
        self._bg_brush = QBrush(bg_color)

    def follow_object_by(self, dx, dy):
        factor = 1.0 / len(set(arc.obj_item for arc in self.arc_items))
        self.moveBy(factor * dx, factor * dy)


class ObjectItem(EntityItem):
    """Represents an object in the Entity graph."""

    def __init__(self, data_store_form, x, y, extent, entity_id=None):
        """Initializes the item.

        Args:
            data_store_form (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            entity_id (int): object id
        """
        super().__init__(data_store_form, x, y, extent, entity_id=entity_id)
        self._add_relationships_menu = None
        self._relationship_class_per_action = {}
        self.label_item = ObjectLabelItem(self)
        self.setZValue(0.5)
        self.update_name(self.entity_name)
        description = self.db_mngr.get_item(self.db_map, "object", self.entity_id).get("description")
        self.update_description(description)
        self._menu = self._make_menu()

    @property
    def entity_type(self):
        return "object"

    @property
    def db_representation(self):
        return dict(class_id=self.entity_class_id, id=self.entity_id, name=self.entity_name)

    def shape(self):
        path = super().shape()
        path.addPolygon(self.label_item.mapToItem(self, self.label_item.boundingRect()))
        return path

    def update_name(self, name):
        """Refreshes the name."""
        self.label_item.setPlainText(name)

    def update_description(self, description):
        if not description:
            description = "No description"
        self.setToolTip(f"<html>{description}</html>")

    def block_move_by(self, dx, dy):
        super().block_move_by(dx, dy)
        rel_items_follow = self._data_store_form.qsettings.value(
            "appSettings/relationshipItemsFollow", defaultValue="true"
        )
        if rel_items_follow == "false":
            return
        rel_items = {arc_item.rel_item for arc_item in self.arc_items}
        for rel_item in rel_items:
            rel_item.follow_object_by(dx, dy)

    def _make_menu(self):
        menu = super()._make_menu()
        menu.addSeparator()
        self._add_relationships_menu = menu.addMenu("Add relationships...")
        self._add_relationships_menu.triggered.connect(self._start_relationship)
        return menu

    def _populate_add_relationships_menu(self, add_title=False):
        """
        Populates the 'Add relationships' menu.
        """
        self._add_relationships_menu.clear()
        if add_title:
            title = TitleWidgetAction("Add relationships", self._data_store_form)
            self._add_relationships_menu.addAction(title)
        self._relationship_class_per_action.clear()
        object_class_ids_in_graph = {x.entity_class_id for x in self.scene().items() if isinstance(x, ObjectItem)}
        db_map_object_class_ids = {self.db_map: {self.entity_class_id}}
        for rel_cls in self.db_mngr.find_cascading_relationship_classes(db_map_object_class_ids).get(self.db_map, []):
            object_class_id_list = [int(id_) for id_ in rel_cls["object_class_id_list"].split(",")]
            if not set(object_class_id_list) <= object_class_ids_in_graph:
                continue
            icon = self.db_mngr.entity_class_icon(self.db_map, "relationship_class", rel_cls["id"])
            action = self._add_relationships_menu.addAction(icon, rel_cls["name"])
            rel_cls = rel_cls.copy()
            rel_cls["object_class_id_list"] = object_class_id_list
            self._relationship_class_per_action[action] = rel_cls
        self._add_relationships_menu.setEnabled(bool(self._relationship_class_per_action))

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self._populate_add_relationships_menu()
        super().contextMenuEvent(e)

    def mouseDoubleClickEvent(self, e):
        self._populate_add_relationships_menu(add_title=True)
        self._add_relationships_menu.popup(e.screenPos())

    @Slot("QAction")
    def _start_relationship(self, action):
        self._data_store_form.start_relationship(self._relationship_class_per_action[action], self)


class ArcItem(QGraphicsPathItem):
    """Connects a RelationshipItem to an ObjectItem."""

    def __init__(self, rel_item, obj_item, width):
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
        self._pen = self._make_pen()
        self.setPen(self._pen)
        self.setZValue(-2)
        rel_item.add_arc_item(self)
        obj_item.add_arc_item(self)
        self.setCursor(Qt.ArrowCursor)
        self.update_line()

    def _make_pen(self):
        pen = QPen()
        pen.setWidth(self._width)
        color = QGuiApplication.palette().color(QPalette.Normal, QPalette.WindowText)
        color.setAlphaF(0.8)
        pen.setColor(color)
        pen.setStyle(Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        return pen

    def moveBy(self, dx, dy):
        """Does nothing. This item is not moved the regular way, but follows the EntityItems it connects."""

    def update_line(self):
        overlapping_arcs = [arc for arc in self.rel_item.arc_items if arc.obj_item == self.obj_item]
        count = len(overlapping_arcs)
        path = QPainterPath(self.rel_item.pos())
        if count == 1:
            path.lineTo(self.obj_item.pos())
        else:
            rank = overlapping_arcs.index(self)
            line = QLineF(self.rel_item.pos(), self.obj_item.pos())
            line.setP1(line.center())
            line = line.normalVector()
            line.setLength(self._width * count)
            line.setP1(2 * line.p1() - line.p2())
            t = rank / (count - 1)
            ctrl_point = line.pointAt(t)
            path.quadTo(ctrl_point, self.obj_item.pos())
        self.setPath(path)

    def mousePressEvent(self, event):
        """Accepts the event so it's not propagated."""
        event.accept()

    def other_item(self, item):
        return {self.rel_item: self.obj_item, self.obj_item: self.rel_item}.get(item)

    def apply_zoom(self, factor):
        """Applies zoom.

        Args:
            factor (float): The zoom factor.
        """
        if factor < 1:
            factor = 1
        scaled_width = self._width / factor
        self._pen.setWidthF(scaled_width)
        self.setPen(self._pen)


class CrossHairsItem(RelationshipItem):
    """Creates new relationships directly in the graph."""

    def __init__(self, data_store_form, x, y, extent):
        super().__init__(data_store_form, x, y, 0.8 * extent)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)
        self.setZValue(2)
        self._current_icon = None

    @property
    def entity_class_name(self):
        return None

    @property
    def entity_name(self):
        return None

    def _make_tool_tip(self):
        return "<p>Click on an object to add it to the relationship.</p>"

    def refresh_icon(self):
        pixmap = CharIconEngine("\uf05b", 0).pixmap(QSize(self._extent, self._extent))
        self.setPixmap(pixmap)

    def set_plus_icon(self):
        self.set_icon("\uf067", Qt.blue)

    def set_check_icon(self):
        self.set_icon("\uf00c", Qt.green)

    def set_normal_icon(self):
        self.set_icon("\uf05b")

    def set_ban_icon(self):
        self.set_icon("\uf05e", Qt.red)

    def set_icon(self, unicode, color=0):
        """Refreshes the icon."""
        if (unicode, color) == self._current_icon:
            return
        pixmap = CharIconEngine(unicode, color).pixmap(QSize(self._extent, self._extent))
        self.setPixmap(pixmap)
        self._current_icon = (unicode, color)

    def mouseMoveEvent(self, event):
        move_by = event.scenePos() - self.scenePos()
        self.block_move_by(move_by.x(), move_by.y())

    def block_move_by(self, dx, dy):
        self.moveBy(dx, dy)
        rel_items = {arc_item.rel_item for arc_item in self.arc_items}
        for rel_item in rel_items:
            rel_item.follow_object_by(dx, dy)

    def contextMenuEvent(self, e):
        e.accept()


class CrossHairsRelationshipItem(RelationshipItem):
    """Represents the relationship that's being created using the CrossHairsItem."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)

    def _make_tool_tip(self):
        return None

    def refresh_icon(self):
        """Refreshes the icon."""
        obj_items = [arc_item.obj_item for arc_item in self.arc_items]
        object_class_name_list = [
            obj_item.entity_class_name for obj_item in obj_items if not isinstance(obj_item, CrossHairsItem)
        ]
        object_class_name_list = ",".join(object_class_name_list)
        pixmap = (
            self.db_mngr.icon_mngr[self.db_map]
            .relationship_pixmap(object_class_name_list)
            .scaled(self._extent, self._extent)
        )
        self.setPixmap(pixmap)

    def contextMenuEvent(self, e):
        e.accept()


class CrossHairsArcItem(ArcItem):
    """Connects a CrossHairsRelationshipItem with the CrossHairsItem,
    and with all the ObjectItem's in the relationship so far.
    """

    def _make_pen(self):
        pen = super()._make_pen()
        pen.setStyle(Qt.DotLine)
        color = pen.color()
        color.setAlphaF(0.5)
        pen.setColor(color)
        return pen


class ObjectLabelItem(QGraphicsTextItem):
    """Provides a label for ObjectItem's."""

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
        self.bg_color = QGuiApplication.palette().color(QPalette.Normal, QPalette.ToolTipBase)
        self.bg_color.setAlphaF(0.8)
        self.bg.setBrush(QBrush(self.bg_color))
        self.bg.setPen(Qt.NoPen)
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
