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
Classes for drawing graphics items on graph view's QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:   4.4.2018
"""
from PySide2.QtCore import Qt, Signal, Slot, QLineF, QPointF
from PySide2.QtSvg import QGraphicsSvgItem
from PySide2.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QStyle,
    QApplication,
    QMenu,
)
from PySide2.QtGui import QPen, QBrush, QPainterPath, QPalette, QGuiApplication
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas  # pylint: disable=no-name-in-module
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
        proxy_widget.setAcceptedMouseButtons(Qt.NoButton)
    else:
        proxy_widget = scene.addWidget(canvas, Qt.Window)
    proxy_widget.setZValue(z)
    return proxy_widget, figure


class EntityItem(QGraphicsRectItem):
    """Base class for ObjectItem and RelationshipItem."""

    def __init__(self, spine_db_editor, x, y, extent, db_map_entity_id=None):
        """Initializes item

        Args:
            spine_db_editor (SpineDBEditor): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): Preferred extent
            db_map_entity_id (tuple): db_map, entity id
        """
        super().__init__()
        self._spine_db_editor = spine_db_editor
        self.db_mngr = spine_db_editor.db_mngr
        self.db_map_entity_id = db_map_entity_id
        self.arc_items = list()
        self._extent = extent
        self.setRect(-0.5 * self._extent, -0.5 * self._extent, self._extent, self._extent)
        self.setPen(Qt.NoPen)
        self._svg_item = QGraphicsSvgItem(self)
        self._svg_item.setCacheMode(QGraphicsItem.CacheMode.NoCache)  # Needed for the exported pdf to be vector
        self.refresh_icon()
        self.setPos(x, y)
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
        self.setToolTip(self._make_tool_tip())

    def _make_tool_tip(self):
        raise NotImplementedError()

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
    def db_map(self):
        return self.db_map_entity_id[0]

    @property
    def entity_id(self):
        return self.db_map_entity_id[1]

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
        # NOTE: Needed by EditObjectsDialog and EditRelationshipsDialog
        return self.db_mngr.get_item(self.db_map, self.entity_type, self.entity_id)

    def db_map_id(self, _db_map):
        # NOTE: Needed by EditObjectsDialog and EditRelationshipsDialog
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
        renderer = self.db_mngr.entity_class_renderer(self.db_map, self.entity_class_type, self.entity_class_id)
        self._set_renderer(renderer)

    def _set_renderer(self, renderer):
        self._svg_item.setSharedRenderer(renderer)
        size = renderer.defaultSize()
        scale = self._extent / max(size.width(), size.height())
        self._svg_item.setScale(scale)
        self._svg_item.setPos(self.rect().center() - 0.5 * scale * QPointF(size.width(), size.height()))

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
        """Moves the item and all connected arcs.

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
        return self._spine_db_editor.ui.graphicsView.make_items_menu()

    def contextMenuEvent(self, e):
        """Shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        e.accept()
        if not self.isSelected() and not e.modifiers() & Qt.ControlModifier:
            self.scene().clearSelection()
        self.setSelected(True)
        menu = self._make_menu()
        menu.popup(e.screenPos())


class RelationshipItem(EntityItem):
    """Represents a relationship in the Entity graph."""

    def __init__(self, spine_db_editor, x, y, extent, db_map_entity_id=None):
        """Initializes the item.

        Args:
            spine_db_editor (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            db_map_entity_id (tuple): db_map, relationship id
        """
        super().__init__(spine_db_editor, x, y, extent, db_map_entity_id=db_map_entity_id)

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
            f"""{self.object_name_list.replace(",", self.db_mngr._GROUP_SEP)}<br>"""
            f"""@{self.db_map.codename}</p></html>"""
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

    def __init__(self, spine_db_editor, x, y, extent, db_map_entity_id=None):
        """Initializes the item.

        Args:
            spine_db_editor (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            db_map_entity_id (tuple): db_map, object id
        """
        super().__init__(spine_db_editor, x, y, extent, db_map_entity_id=db_map_entity_id)
        self._relationship_classes = {}
        self.label_item = ObjectLabelItem(self)
        self.setZValue(0.5)
        self.update_name(self.entity_name)

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

    def _make_tool_tip(self):
        return f"<html><p style='text-align:center;'>{self.entity_name}<br>@{self.db_map.codename}</html>"

    def block_move_by(self, dx, dy):
        super().block_move_by(dx, dy)
        rel_items_follow = self._spine_db_editor.qsettings.value(
            "appSettings/relationshipItemsFollow", defaultValue="true"
        )
        if rel_items_follow == "false":
            return
        rel_items = {arc_item.rel_item for arc_item in self.arc_items}
        for rel_item in rel_items:
            rel_item.follow_object_by(dx, dy)

    def mouseDoubleClickEvent(self, e):
        add_relationships_menu = QMenu(self._spine_db_editor)
        title = TitleWidgetAction("Add relationships", self._spine_db_editor)
        add_relationships_menu.addAction(title)
        add_relationships_menu.triggered.connect(self._start_relationship)
        self._refresh_relationship_classes()
        self._populate_add_relationships_menu(add_relationships_menu)
        add_relationships_menu.popup(e.screenPos())

    def _make_menu(self):
        menu = super()._make_menu()
        expand_menu = QMenu("Expand", menu)
        expand_menu.triggered.connect(self._expand)
        collapse_menu = QMenu("Collapse", menu)
        collapse_menu.triggered.connect(self._collapse)
        add_relationships_menu = QMenu("Add relationships", menu)
        add_relationships_menu.triggered.connect(self._start_relationship)
        self._refresh_relationship_classes()
        self._populate_expand_collapse_menu(expand_menu)
        self._populate_expand_collapse_menu(collapse_menu)
        self._populate_add_relationships_menu(add_relationships_menu)
        first = menu.actions()[0]
        first = menu.insertSeparator(first)
        first = menu.insertMenu(first, add_relationships_menu)
        first = menu.insertMenu(first, collapse_menu)
        menu.insertMenu(first, expand_menu)
        return menu

    def _refresh_relationship_classes(self):
        self._relationship_classes.clear()
        db_map_object_ids = {self.db_map: {self.entity_id}}
        relationship_ids_per_class = {}
        for rel in self.db_mngr.find_cascading_relationships(db_map_object_ids).get(self.db_map, []):
            relationship_ids_per_class.setdefault(rel["class_id"], set()).add((self.db_map, rel["id"]))
        db_map_object_class_ids = {self.db_map: {self.entity_class_id}}
        for rel_cls in self.db_mngr.find_cascading_relationship_classes(db_map_object_class_ids).get(self.db_map, []):
            rel_cls = rel_cls.copy()
            rel_cls["object_class_id_list"] = [int(id_) for id_ in rel_cls["object_class_id_list"].split(",")]
            rel_cls["relationship_ids"] = relationship_ids_per_class.get(rel_cls["id"], set())
            self._relationship_classes[rel_cls["name"]] = rel_cls

    def _populate_expand_collapse_menu(self, menu):
        """
        Populates the 'Expand' or 'Collapse' menu.

        Args:
            menu (QMenu)
        """
        if not self._relationship_classes:
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        menu.addAction("All")
        menu.addSeparator()
        for name, rel_cls in self._relationship_classes.items():
            icon = self.db_mngr.entity_class_icon(self.db_map, "relationship_class", rel_cls["id"])
            menu.addAction(icon, name).setEnabled(bool(rel_cls["relationship_ids"]))

    def _populate_add_relationships_menu(self, menu):
        """
        Populates the 'Add relationships' menu.

        Args:
            menu (QMenu)
        """
        object_class_ids_in_graph = {
            x.entity_class_id for x in self._spine_db_editor.ui.graphicsView.entity_items if isinstance(x, ObjectItem)
        }
        for name, rel_cls in self._relationship_classes.items():
            icon = self.db_mngr.entity_class_icon(self.db_map, "relationship_class", rel_cls["id"])
            menu.addAction(icon, name).setEnabled(set(rel_cls["object_class_id_list"]) <= object_class_ids_in_graph)
        menu.setEnabled(bool(self._relationship_classes))

    def _get_relationship_ids_to_expand_or_collapse(self, action):
        rel_cls = self._relationship_classes.get(action.text())
        if rel_cls is not None:
            return rel_cls["relationship_ids"]
        return {id_ for rel_cls in self._relationship_classes.values() for id_ in rel_cls["relationship_ids"]}

    @Slot("QAction")
    def _expand(self, action):
        relationship_ids = self._get_relationship_ids_to_expand_or_collapse(action)
        self._spine_db_editor.added_relationship_ids.update(relationship_ids)
        self._spine_db_editor.build_graph(persistent=True)

    @Slot("QAction")
    def _collapse(self, action):
        relationship_ids = self._get_relationship_ids_to_expand_or_collapse(action)
        self._spine_db_editor.added_relationship_ids.difference_update(relationship_ids)
        self._spine_db_editor.build_graph(persistent=True)

    @Slot("QAction")
    def _start_relationship(self, action):
        self._spine_db_editor.start_relationship(self._relationship_classes[action.text()], self)


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        renderer = self.db_mngr.get_icon_mngr(self.db_map).icon_renderer("\uf05b", 0)
        self._set_renderer(renderer)

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
        renderer = self.db_mngr.get_icon_mngr(self.db_map).icon_renderer(unicode, color)
        self._set_renderer(renderer)
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
        renderer = self.db_mngr.get_icon_mngr(self.db_map).relationship_renderer(object_class_name_list)
        self._set_renderer(renderer)

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
