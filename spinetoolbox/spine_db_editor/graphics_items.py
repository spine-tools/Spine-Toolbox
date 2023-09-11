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
Classes for drawing graphics items on graph view's QGraphicsScene.
"""
from PySide6.QtCore import Qt, Signal, Slot, QLineF, QRectF, QPointF
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtWidgets import (
    QGraphicsItem,
    QGraphicsTextItem,
    QGraphicsRectItem,
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QStyle,
    QApplication,
    QMenu,
)
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPalette, QGuiApplication, QAction
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas  # pylint: disable=no-name-in-module

from spinetoolbox.helpers import DB_ITEM_SEPARATOR, color_from_index
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

    def __init__(self, spine_db_editor, x, y, extent, db_map_ids, offset=None):
        """
        Args:
            spine_db_editor (SpineDBEditor): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): Preferred extent
            db_map_ids (tuple): tuple of (db_map, id) tuples
        """
        super().__init__()
        self._spine_db_editor = spine_db_editor
        self.db_mngr = spine_db_editor.db_mngr
        self._given_extent = extent
        self._db_map_ids = db_map_ids
        self._offset = offset
        self._dx = self._dy = 0
        self._removed_db_map_ids = ()
        self.arc_items = []
        self.set_pos(x, y)
        self.setPen(Qt.NoPen)
        self._svg_item = QGraphicsSvgItem(self)
        self._svg_item.setZValue(100)
        self._svg_item.setCacheMode(QGraphicsItem.CacheMode.NoCache)  # Needed for the exported pdf to be vector
        self._renderer = None
        self._moved_on_scene = False
        self._bg = None
        self._bg_brush = None
        self.setZValue(0)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, enabled=True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, enabled=True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.ArrowCursor)
        self.setToolTip(self._make_tool_tip())
        self._highlight_color = Qt.transparent
        self._extent = None
        self.label_item = EntityLabelItem(self)

    def _make_tool_tip(self):
        raise NotImplementedError()

    def default_parameter_data(self):
        raise NotImplementedError()

    @property
    def has_dimensions(self):
        raise NotImplementedError()

    @property
    def entity_type(self):
        raise NotImplementedError()

    @property
    def db_map_ids(self):
        return tuple(x for x in self._db_map_ids if x not in self._removed_db_map_ids)

    @property
    def original_db_map_ids(self):
        return self._db_map_ids

    @property
    def entity_class_type(self):
        return {"relationship": "relationship_class", "object": "object_class"}[self.entity_type]

    @property
    def entity_name(self):
        return self.db_mngr.get_item(self.first_db_map, self.entity_type, self.first_id).get("name", "")

    @property
    def first_entity_class_id(self):
        return self.db_mngr.get_item(self.first_db_map, self.entity_type, self.first_id).get("class_id")

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.first_db_map, self.entity_class_type, self.first_entity_class_id).get(
            "name", ""
        )

    @property
    def first_db_map_id(self):
        return next(iter(self.db_map_ids), (None, None))

    @property
    def first_id(self):
        return self.first_db_map_id[1]

    @property
    def first_db_map(self):
        return self.first_db_map_id[0]

    @property
    def display_data(self):
        return self.entity_name

    @property
    def display_database(self):
        return ",".join([db_map.codename for db_map in self.db_maps])

    @property
    def db_maps(self):
        return list(db_map for db_map, _id in self.db_map_ids)

    def entity_class_id(self, db_map):
        return self.db_mngr.get_item(db_map, self.entity_type, self.entity_id(db_map)).get("class_id")

    def entity_id(self, db_map):
        return dict(self.db_map_ids).get(db_map)

    def db_map_data(self, db_map):
        # NOTE: Needed by EditObjectsDialog and EditRelationshipsDialog
        return self.db_mngr.get_item(db_map, self.entity_type, self.entity_id(db_map))

    def db_map_id(self, db_map):
        # NOTE: Needed by EditObjectsDialog and EditRelationshipsDialog
        return self.entity_id(db_map)

    def db_items(self, db_map):
        for db_map_, id_ in self.db_map_ids:
            if db_map_ == db_map:
                yield dict(class_id=self.entity_class_id(db_map), id=id_)

    def boundingRect(self):
        return super().boundingRect() | self.childrenBoundingRect()

    def set_pos(self, x, y):
        x, y = self._snap(x, y)
        self.setPos(x, y)
        self.update_arcs_line()

    def move_by(self, dx, dy):
        self._dx += dx
        self._dy += dy
        dx, dy = self._snap(self._dx, self._dy)
        if dx == dy == 0:
            return
        self.moveBy(dx, dy)
        self._dx -= dx
        self._dy -= dy
        self.update_arcs_line()
        rel_items = {arc_item.rel_item for arc_item in self.arc_items}
        for rel_item in rel_items:
            rel_item.update_entity_pos()

    def _snap(self, x, y):
        if self._spine_db_editor.qsettings.value("appSettings/snapEntities", defaultValue="false") != "true":
            return (x, y)
        grid_size = self._given_extent
        x = round(x / grid_size) * grid_size
        y = round(y / grid_size) * grid_size
        return (x, y)

    def has_unique_key(self):
        """Returns whether or not the item still has a single key in all the databases it represents.

        Returns:
            bool
        """
        db_map_ids_by_key = {}
        for db_map_id in self.db_map_ids:
            key = self._spine_db_editor.get_entity_key(db_map_id)
            db_map_ids_by_key.setdefault(key, []).append(db_map_id)
        if len(db_map_ids_by_key) == 1:
            return True
        first_key = next(iter(db_map_ids_by_key))
        self._db_map_ids = tuple(db_map_ids_by_key[first_key])
        return False

    def _get_name(self):
        for db_map, id_ in self.db_map_ids:
            name = self._spine_db_editor.get_item_name(db_map, self.entity_type, id_)
            if isinstance(name, str):
                return name

    def _get_color(self):
        for db_map, id_ in self.db_map_ids:
            color = self._spine_db_editor.get_item_color(db_map, self.entity_type, id_)
            if color is not None:
                min_val, val, max_val = color
                count = max_val - min_val
                if count == 0:
                    return int(color_from_index(0, 1, value=0).rgba())
                k = val - min_val
                return int(color_from_index(k, count).rgba())

    def _get_arc_width(self):
        for db_map, id_ in self.db_map_ids:
            arc_width = self._spine_db_editor.get_arc_width(db_map, self.entity_type, id_)
            if arc_width is not None:
                min_val, val, max_val = arc_width
                range_ = max_val - min_val
                if range_ == 0:
                    return None
                # val == min_val => result = 1
                # val == max_val => result = 5
                return 1 + 9 * (val - min_val) / range_

    def _set_up(self):
        if self._has_name():
            name = self._get_name()
            if not name:
                self.label_item.hide()
                self._extent = 0.2 * self._given_extent
            else:
                if not self.has_dimensions:
                    self.label_item.show()
                    self.label_item.setPlainText(name)
                    self._extent = self._given_extent
                else:
                    self.label_item.hide()
                    self._extent = 0.5 * self._given_extent
        else:
            self.label_item.hide()
            self._extent = self._given_extent
        self.setRect(-0.5 * self._extent, -0.5 * self._extent, self._extent, self._extent)
        self._init_bg()
        self.refresh_icon()
        self.update_entity_pos()

    def polish(self):
        self._renderer = self.db_mngr.entity_class_renderer(
            self.first_db_map, self.entity_class_type, self.first_entity_class_id, color_code=self._get_color()
        )
        self._svg_item.setSharedRenderer(self._renderer)
        self._update_arcs_width()

    def _init_bg(self):
        bg_rect = QRectF(-0.5 * self._extent, -0.5 * self._extent, self._extent, self._extent)
        if not self.has_dimensions:
            self._bg = QGraphicsRectItem(bg_rect, self)
            self._bg_brush = Qt.NoBrush
        else:
            self._bg = QGraphicsEllipseItem(bg_rect, self)
            self._bg_brush = QGuiApplication.palette().button()
        pen = self._bg.pen()
        pen.setColor(Qt.transparent)
        self._bg.setPen(pen)
        self._bg.setFlag(QGraphicsItem.ItemStacksBehindParent, enabled=True)

    def refresh_icon(self):
        """Refreshes the icon."""
        renderer = self.db_mngr.entity_class_renderer(
            self.first_db_map, self.entity_class_type, self.first_entity_class_id, color_code=self._get_color()
        )
        self._set_renderer(renderer)

    def _set_renderer(self, renderer):
        self._renderer = renderer
        self._svg_item.setSharedRenderer(self._renderer)
        size = self._renderer.defaultSize()
        scale = self._extent / max(size.width(), size.height())
        self._svg_item.setScale(scale)
        rect = self._svg_item.boundingRect()
        self._svg_item.setTransformOriginPoint(rect.center())
        self._svg_item.setPos(-rect.center())

    def shape(self):
        """Returns a shape containing the entire bounding rect, to work better with icon transparency."""
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRect(self._bg.boundingRect())
        return path

    def set_highlight_color(self, color):
        self._highlight_color = color

    def paint(self, painter, option, widget=None):
        """Shows or hides the selection halo."""
        if option.state & (QStyle.StateFlag.State_Selected):
            self._paint_as_selected()
            option.state &= ~QStyle.StateFlag.State_Selected
        else:
            self._paint_as_deselected()
        pen = self._bg.pen()
        pen.setColor(self._highlight_color)
        width = max(1, 10 / self.scale())
        pen.setWidth(width)
        self._bg.setPen(pen)
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
        self._rotate_svg_item()
        self.update_entity_pos()

    def _rotate_svg_item(self):
        if len(self.arc_items) != 2:
            self._svg_item.setRotation(0)
            return
        arc1, arc2 = self.arc_items  # pylint: disable=unbalanced-tuple-unpacking
        obj1, obj2 = arc1.obj_item, arc2.obj_item
        line = QLineF(obj1.pos(), obj2.pos())
        self._svg_item.setRotation(-line.angle())

    def update_entity_pos(self):
        el_items = [arc_item.obj_item for arc_item in self.arc_items]
        dim_count = len(el_items)
        if not dim_count:
            return
        new_pos_x = sum(el_item.pos().x() for el_item in el_items) / dim_count
        new_pos_y = sum(el_item.pos().y() for el_item in el_items) / dim_count
        if self._offset:
            el_item = el_items[0]
            line = QLineF(QPointF(new_pos_x, new_pos_y), el_item.pos()).normalVector()
            if self._offset < 0:
                line.setAngle(line.angle() + 180)
            line.setLength(abs(self._offset) * self._extent)
            new_pos_x, new_pos_y = line.x2(), line.y2()
        self.setPos(new_pos_x, new_pos_y)
        self.update_arcs_line()

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
            center (QPointF): Rotates around this point.
        """
        line = QLineF(center, self.pos())
        line.setAngle(line.angle() + angle)
        pos = line.p2()
        self.set_pos(pos.x(), pos.y())

    def mouseMoveEvent(self, event):
        """Moves the item and all connected arcs.

        Args:
            event (QGraphicsSceneMouseEvent)
        """
        if event.buttons() & Qt.LeftButton == 0:
            super().mouseMoveEvent(event)
            return
        delta = event.scenePos() - event.lastScenePos()
        # Move selected items together
        for item in self.scene().selectedItems():
            if isinstance(item, (EntityItem)):
                item.move_by(delta.x(), delta.y())

    def update_arcs_line(self):
        """Moves arc items."""
        for item in self.arc_items:
            item.update_line()
        self._update_arcs_width()

    def _update_arcs_width(self):
        arc_width = self._get_arc_width()
        if arc_width is not None:
            for item in self.arc_items:
                item.apply_value_factor(arc_width)

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

    def setVisible(self, on):
        """Sets visibility status for this item and all arc items.

        Args:
            on (bool)
        """
        super().setVisible(on)
        for arc_item in self.arc_items:
            arc_item.setVisible(arc_item.obj_item.isVisible() and arc_item.rel_item.isVisible())

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

    def remove_db_map_ids(self, db_map_ids):
        """Removes db_map_ids."""
        self._removed_db_map_ids += tuple(db_map_ids)
        self.setToolTip(self._make_tool_tip())

    def add_db_map_ids(self, db_map_ids):
        for db_map_id in db_map_ids:
            if db_map_id not in self._db_map_ids:
                self._db_map_ids += (db_map_id,)
            else:
                self._removed_db_map_ids = tuple(x for x in self._removed_db_map_ids if x != db_map_id)
        self.setToolTip(self._make_tool_tip())


class RelationshipItem(EntityItem):
    """Represents a relationship in the Entity graph."""

    def __init__(self, spine_db_editor, x, y, extent, db_map_ids):
        """Initializes the item.

        Args:
            spine_db_editor (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            db_map_ids (tuple): tuple of (db_map, id) tuples
        """
        super().__init__(spine_db_editor, x, y, extent, db_map_ids=db_map_ids)
        self._set_up()

    @property
    def has_dimensions(self):
        return True

    def _has_name(self):
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        if not self.db_map_ids:
            return {}
        return dict(
            relationship_class_name=self.entity_class_name,
            object_name_list=DB_ITEM_SEPARATOR.join(self.object_name_list),
            database=self.first_db_map.codename,
        )

    @property
    def entity_type(self):
        return "relationship"

    @property
    def object_class_id_list(self):
        # FIXME: where is this used?
        return self.db_mngr.get_item(self.first_db_map, "relationship_class", self.first_entity_class_id).get(
            "object_class_id_list"
        )

    @property
    def object_name_list(self):
        return self.db_mngr.get_item(self.first_db_map, "relationship", self.first_id).get("object_name_list", "")

    def object_id_list(self, db_map):
        return self.db_mngr.get_item(db_map, "relationship", self.entity_id(db_map)).get("object_id_list")

    def db_representation(self, db_map):
        return dict(
            class_id=self.entity_class_id(db_map),
            id=self.entity_id(db_map),
            object_id_list=self.object_id_list(db_map),
            object_name_list=self.object_name_list,
        )

    def _make_tool_tip(self):
        if not self.first_id:
            return None
        return (
            f"""<html><p style="text-align:center;">{self.entity_class_name}<br>"""
            f"""{DB_ITEM_SEPARATOR.join(self.object_name_list)}<br>"""
            f"""@{self.display_database}</p></html>"""
        )

    def itemChange(self, change, value):
        """Rotates svg item if the relationship is 2D.
        This makes it possible to define e.g. an arow icon for relationships that express direction.
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._rotate_svg_item()
        return super().itemChange(change, value)


class ObjectItem(EntityItem):
    """Represents an object in the Entity graph."""

    def __init__(self, spine_db_editor, x, y, extent, db_map_ids):
        """Initializes the item.

        Args:
            spine_db_editor (GraphViewForm): 'owner'
            x (float): x-coordinate of central point
            y (float): y-coordinate of central point
            extent (int): preferred extent
            db_map_ids (tuple): tuple of (db_map, id) tuples
        """
        super().__init__(spine_db_editor, x, y, extent, db_map_ids=db_map_ids)
        self._db_map_relationship_class_lists = {}
        self.setZValue(0.5)
        self._set_up()

    @property
    def has_dimensions(self):
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        if not self.db_map_ids:
            return {}
        return dict(
            object_class_name=self.entity_class_name, object_name=self.entity_name, database=self.first_db_map.codename
        )

    @property
    def entity_type(self):
        return "object"

    def db_representation(self, db_map):
        return dict(class_id=self.entity_class_id(db_map), id=self.entity_id(db_map), name=self.entity_name)

    def shape(self):
        path = super().shape()
        path.addPolygon(self.label_item.mapToItem(self, self.label_item.boundingRect()))
        return path

    def _has_name(self):
        return True

    def _make_tool_tip(self):
        if not self.first_id:
            return None
        return f"<html><p style='text-align:center;'>{self.entity_name}<br>@{self.display_database}</html>"

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
        menu.addAction("Duplicate", self._duplicate)
        return menu

    def _duplicate(self):
        self._spine_db_editor.duplicate_object(self)

    def _refresh_relationship_classes(self):
        self._db_map_relationship_class_lists.clear()
        db_map_object_ids = {db_map: {id_} for db_map, id_ in self.db_map_ids}
        relationship_ids_per_class = {}
        for db_map, rels in self.db_mngr.find_cascading_relationships(db_map_object_ids).items():
            for rel in rels:
                relationship_ids_per_class.setdefault((db_map, rel["class_id"]), set()).add(rel["id"])
        db_map_object_class_ids = {db_map: {self.entity_class_id(db_map)} for db_map in self.db_maps}
        for db_map, rel_clss in self.db_mngr.find_cascading_relationship_classes(db_map_object_class_ids).items():
            for rel_cls in rel_clss:
                rel_cls = rel_cls.copy()
                rel_cls["object_class_id_list"] = list(rel_cls["object_class_id_list"])
                rel_cls["relationship_ids"] = relationship_ids_per_class.get((db_map, rel_cls["id"]), set())
                self._db_map_relationship_class_lists.setdefault(rel_cls["name"], []).append((db_map, rel_cls))

    def _populate_expand_collapse_menu(self, menu):
        """
        Populates the 'Expand' or 'Collapse' menu.

        Args:
            menu (QMenu)
        """
        if not self._db_map_relationship_class_lists:
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        menu.addAction("All")
        menu.addSeparator()
        for name, db_map_rel_cls_lst in sorted(self._db_map_relationship_class_lists.items()):
            db_map, rel_cls = next(iter(db_map_rel_cls_lst))
            icon = self.db_mngr.entity_class_icon(db_map, "relationship_class", rel_cls["id"])
            menu.addAction(icon, name).setEnabled(
                any(rel_cls["relationship_ids"] for (db_map, rel_cls) in db_map_rel_cls_lst)
            )

    def _populate_add_relationships_menu(self, menu):
        """
        Populates the 'Add relationships' menu.

        Args:
            menu (QMenu)
        """
        object_class_ids_in_graph = {}
        for item in self._spine_db_editor.ui.graphicsView.entity_items:
            if not isinstance(item, ObjectItem):
                continue
            for db_map in item.db_maps:
                object_class_ids_in_graph.setdefault(db_map, set()).add(item.entity_class_id(db_map))
        action_name_icon_enabled = []
        for name, db_map_rel_cls_lst in self._db_map_relationship_class_lists.items():
            for db_map, rel_cls in db_map_rel_cls_lst:
                icon = self.db_mngr.entity_class_icon(db_map, "relationship_class", rel_cls["id"])
                action_name = name + "@" + db_map.codename
                enabled = set(rel_cls["object_class_id_list"]) <= object_class_ids_in_graph.get(db_map, set())
                action_name_icon_enabled.append((action_name, icon, enabled))
        for action_name, icon, enabled in sorted(action_name_icon_enabled):
            menu.addAction(icon, action_name).setEnabled(enabled)
        menu.setEnabled(bool(self._db_map_relationship_class_lists))

    def _get_db_map_relationship_ids_to_expand_or_collapse(self, action):
        db_map_rel_clss = self._db_map_relationship_class_lists.get(action.text())
        if db_map_rel_clss is not None:
            return {(db_map, id_) for db_map, rel_cls in db_map_rel_clss for id_ in rel_cls["relationship_ids"]}
        return {
            (db_map, id_)
            for class_list in self._db_map_relationship_class_lists.values()
            for db_map, rel_cls in class_list
            for id_ in rel_cls["relationship_ids"]
        }

    @Slot(QAction)
    def _expand(self, action):
        db_map_relationship_ids = self._get_db_map_relationship_ids_to_expand_or_collapse(action)
        self._spine_db_editor.added_db_map_relationship_ids.update(db_map_relationship_ids)
        self._spine_db_editor.build_graph(persistent=True)

    @Slot(QAction)
    def _collapse(self, action):
        db_map_relationship_ids = self._get_db_map_relationship_ids_to_expand_or_collapse(action)
        self._spine_db_editor.added_db_map_relationship_ids.difference_update(db_map_relationship_ids)
        self._spine_db_editor.build_graph(persistent=True)

    @Slot(QAction)
    def _start_relationship(self, action):
        class_name, db_name = action.text().split("@")
        db_map_rel_cls_lst = self._db_map_relationship_class_lists[class_name]
        db_map, rel_cls = next(
            iter((db_map, rel_cls) for db_map, rel_cls in db_map_rel_cls_lst if db_map.codename == db_name)
        )
        self._spine_db_editor.start_relationship(db_map, rel_cls, self)


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
        self._original_width = float(width)
        self._scaled_width = self._original_width
        self._pen = self._make_pen()
        self.setPen(self._pen)
        self.setZValue(-2)
        self._scaling_factor = 1
        self._value_factor = 1
        rel_item.add_arc_item(self)
        obj_item.add_arc_item(self)
        self.setCursor(Qt.ArrowCursor)
        self.update_line()

    def _make_pen(self):
        pen = QPen()
        pen.setWidthF(self._scaled_width)
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

    def apply_value_factor(self, factor):
        self._value_factor = max(1, factor)
        self._update_width()

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
        self._scaling_factor = max(factor, 1)
        self._update_width()

    def _update_width(self):
        width = self._original_width * self._value_factor / self._scaling_factor
        self._pen.setWidthF(width)
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

    def _has_name(self):
        return False

    def refresh_icon(self):
        renderer = self.db_mngr.get_icon_mngr(self.first_db_map).icon_renderer("\uf05b", 0)
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
        renderer = self.db_mngr.get_icon_mngr(self.first_db_map).icon_renderer(unicode, color)
        self._set_renderer(renderer)
        self._current_icon = (unicode, color)

    def _snap(self, x, y):
        return (x, y)

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - self.scenePos()
        self.move_by(delta.x(), delta.y())

    def contextMenuEvent(self, e):
        e.accept()


class CrossHairsRelationshipItem(RelationshipItem):
    """Represents the relationship that's being created using the CrossHairsItem."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)

    def _make_tool_tip(self):
        return None

    def _has_name(self):
        return False

    def refresh_icon(self):
        """Refreshes the icon."""
        obj_items = [arc_item.obj_item for arc_item in self.arc_items]
        object_class_name_list = tuple(
            obj_item.entity_class_name for obj_item in obj_items if not isinstance(obj_item, CrossHairsItem)
        )
        renderer = self.db_mngr.get_icon_mngr(self.first_db_map).relationship_class_renderer(
            None, object_class_name_list
        )
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


class EntityLabelItem(QGraphicsTextItem):
    """Provides a label for EntityItem's."""

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
