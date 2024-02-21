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

"""Classes for drawing graphics items on graph view's QGraphicsScene."""
from enum import Enum, auto
from PySide6.QtCore import Qt, Signal, Slot, QLineF, QRectF, QPointF, QObject, QByteArray
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
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPen, QBrush, QPainterPath, QPalette, QGuiApplication, QAction, QColor
from spinetoolbox.helpers import DB_ITEM_SEPARATOR, color_from_index
from spinetoolbox.widgets.custom_qwidgets import TitleWidgetAction


class EntityItem(QGraphicsRectItem):
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
        self._circle_item = QGraphicsEllipseItem(self)
        self._circle_item.setPen(Qt.NoPen)
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
        self._db_map_entity_class_lists = {}
        self.label_item = EntityLabelItem(self)
        self.label_item.setVisible(not self.has_dimensions)
        self.setZValue(0.5 if not self.has_dimensions else 0.25)
        self._extent = None
        self.set_up()

    def clone(self):
        return type(self)(
            self._spine_db_editor,
            self.pos().x(),
            self.pos().y(),
            self._given_extent,
            self._db_map_ids,
            offset=self._offset,
        )

    @property
    def has_dimensions(self):
        return bool(self.element_id_list(self.first_db_map))

    @property
    def db_map_ids(self):
        return tuple(x for x in self._db_map_ids if x not in self._removed_db_map_ids)

    @property
    def original_db_map_ids(self):
        return self._db_map_ids

    @property
    def name(self):
        return self.db_mngr.get_item(self.first_db_map, "entity", self.first_id).get("name", "")

    @property
    def first_entity_class_id(self):
        return self.db_mngr.get_item(self.first_db_map, "entity", self.first_id).get("class_id")

    @property
    def entity_class_name(self):
        return self.db_mngr.get_item(self.first_db_map, "entity_class", self.first_entity_class_id).get("name", "")

    @property
    def dimension_id_list(self):
        # FIXME: is this used?
        return self.db_mngr.get_item(self.first_db_map, "entity_class", self.first_entity_class_id).get(
            "dimension_id_list", ()
        )

    @property
    def dimension_name_list(self):
        return self.db_mngr.get_item(self.first_db_map, "entity_class", self.first_entity_class_id).get(
            "dimension_name_list", ()
        )

    @property
    def byname(self):
        return self.db_mngr.get_item(self.first_db_map, "entity", self.first_id).get("entity_byname", ())

    @property
    def element_name_list(self):
        return self.db_mngr.get_item(self.first_db_map, "entity", self.first_id).get("element_name_list", ())

    def element_id_list(self, db_map):
        return self.db_mngr.get_item(db_map, "entity", self.entity_id(db_map)).get("element_id_list", ())

    @property
    def element_byname_list(self):
        # NOTE: Needed by EditEntitiesDialog
        return self.db_mngr.get_item(self.first_db_map, "entity", self.first_id).get("element_byname_list", ())

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
        return self.name

    @property
    def display_database(self):
        return ",".join([db_map.codename for db_map in self.db_maps])

    @property
    def db_maps(self):
        return list(db_map for db_map, _id in self.db_map_ids)

    def entity_class_id(self, db_map):
        return self.db_mngr.get_item(db_map, "entity", self.entity_id(db_map)).get("class_id")

    def entity_class_ids(self, db_map):
        return {self.entity_class_id(db_map)} | {
            x["superclass_id"]
            for x in db_map.get_items("superclass_subclass", subclass_id=self.entity_class_id(db_map))
        }

    def entity_id(self, db_map):
        return dict(self.db_map_ids).get(db_map)

    def db_map_data(self, db_map):
        # NOTE: Needed by EditEntitiesDialog
        return self.db_mngr.get_item(db_map, "entity", self.entity_id(db_map))

    def db_map_id(self, db_map):
        # NOTE: Needed by EditEntitiesDialog
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
        ent_items = {arc_item.ent_item for arc_item in self.arc_items}
        for ent_item in ent_items:
            ent_item.update_entity_pos()

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
            name = self._spine_db_editor.get_item_name(db_map, id_)
            if isinstance(name, str):
                return name

    def _get_prop(self, getter, index):
        values = {getter(db_map, id_, index) for db_map, id_ in self.db_map_ids}
        values.discard(None)
        if not values:
            return None
        values.discard(self._spine_db_editor.NOT_SPECIFIED)
        if not values:
            return self._spine_db_editor.NOT_SPECIFIED
        return next(iter(values))

    def _get_color(self, index=None):
        color = self._get_prop(self._spine_db_editor.get_item_color, index)
        if color in (None, self._spine_db_editor.NOT_SPECIFIED):
            return color
        min_val, val, max_val = color
        count = max(1, max_val - min_val)
        k = val - min_val
        return color_from_index(k, count)

    def _get_arc_width(self, index=None):
        arc_width = self._get_prop(self._spine_db_editor.get_arc_width, index)
        if arc_width in (None, self._spine_db_editor.NOT_SPECIFIED):
            return arc_width
        min_val, val, max_val = arc_width
        range_ = max_val - min_val
        if range_ == 0:
            return None
        if val > 0:
            return val / max_val, 1
        return val / min_val, -1

    def _get_vertex_radius(self, index=None):
        vertex_radius = self._get_prop(self._spine_db_editor.get_vertex_radius, index)
        if vertex_radius in (None, self._spine_db_editor.NOT_SPECIFIED):
            return None
        min_val, val, max_val = vertex_radius
        range_ = max_val - min_val
        if range_ == 0:
            return 0
        return (val - min_val) / range_

    def _has_name(self):
        return True

    def set_up(self):
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
        self._update_bg()
        self.refresh_icon()
        self.update_entity_pos()

    def update_props(self, index):
        color = self._get_color(index)
        arc_width = self._get_arc_width(index)
        vertex_radius = self._get_vertex_radius(index)
        self._update_renderer(color, resize=True)
        self._update_arcs(color, arc_width)
        self._update_circle(color, vertex_radius)

    def _update_bg(self):
        bg_rect = QRectF(-0.5 * self._extent, -0.5 * self._extent, self._extent, self._extent)
        if self._bg is not None:
            self._bg.setRect(bg_rect)
            self._bg.prepareGeometryChange()
            self._bg.update()
            return
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
        color = self._get_color()
        self._update_renderer(color)

    def _update_renderer(self, color, resize=True):
        if color is self._spine_db_editor.NOT_SPECIFIED:
            color = color_from_index(0, 1, value=0)
        self._renderer = self.db_mngr.entity_class_renderer(self.first_db_map, self.first_entity_class_id, color=color)
        self._install_renderer()

    def _install_renderer(self, resize=True):
        self._svg_item.setSharedRenderer(self._renderer)
        if not resize:
            return
        size = self._renderer.defaultSize()
        scale = self._extent / max(size.width(), size.height())
        self._svg_item.setScale(scale)
        rect = self._svg_item.boundingRect()
        self._svg_item.setTransformOriginPoint(rect.center())
        self._svg_item.setPos(-rect.center())

    def _make_tool_tip(self):
        if not self.first_id:
            return None
        return (
            f"""<html><p style="text-align:center;">{self.entity_class_name}<br>"""
            f"""{DB_ITEM_SEPARATOR.join(self.byname)}<br>"""
            f"""@{self.display_database}</p></html>"""
        )

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        if not self.db_map_ids:
            return {}
        return dict(
            entity_class_name=self.entity_class_name,
            entity_byname=DB_ITEM_SEPARATOR.join(self.byname),
            database=self.first_db_map.codename,
        )

    def shape(self):
        """Returns a shape containing the entire bounding rect, to work better with icon transparency."""
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRect(self._bg.boundingRect())
        path.addPolygon(self.label_item.mapToItem(self, self.label_item.boundingRect()))
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

    def update_entity_pos(self):
        for arc_item in self.arc_items:
            arc_item.ent_item.do_update_entity_pos()
        self.do_update_entity_pos()

    def do_update_entity_pos(self):
        el_items = sorted(
            (arc_item.el_item for arc_item in self.arc_items if arc_item.el_item is not self),
            key=lambda x: x.entity_id(x.first_db_map) or 0,
        )
        dim_count = len(el_items)
        if not dim_count:
            return
        new_pos_x = sum(el_item.pos().x() for el_item in el_items) / dim_count
        new_pos_y = sum(el_item.pos().y() for el_item in el_items) / dim_count
        offset = self._offset.value() if self._offset is not None else None
        if offset:
            el_item = el_items[0]
            line = QLineF(QPointF(new_pos_x, new_pos_y), el_item.pos()).normalVector()
            if offset < 0:
                line.setAngle(line.angle() + 180)
            line.setLength(3 * abs(offset) * self._extent)
            new_pos_x, new_pos_y = line.x2(), line.y2()
        self.setPos(new_pos_x, new_pos_y)
        self.update_arcs_line()

    def apply_zoom(self, factor):
        """Applies zoom.

        Args:
            factor (float): The zoom factor.
        """
        factor = min(factor, 1)
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
        color = self._get_color()
        arc_width = self._get_arc_width()
        self._update_arcs(color, arc_width)

    def _update_arcs(self, color, arc_width):
        if color not in (None, self._spine_db_editor.NOT_SPECIFIED):
            for item in self.arc_items:
                item.update_color(color)
        if arc_width not in (None, self._spine_db_editor.NOT_SPECIFIED):
            width, sign = arc_width
            factor = 0.75 * (0.5 + 0.5 * width) * self._extent
            switched = False
            for item in self.arc_items:
                item.apply_value(factor, sign)
                if not switched:
                    switched = True
                    sign = -sign

    def _update_circle(self, color, vertex_radius):
        if color is self._spine_db_editor.NOT_SPECIFIED:
            color = color_from_index(0, 1, value=0)
        else:
            color = QColor(color)
        circle_extent = 2 * (0.5 + 0.5 * vertex_radius) * self._extent if vertex_radius is not None else 0
        self._circle_item.setRect(-circle_extent / 2, -circle_extent / 2, circle_extent, circle_extent)
        color.setAlphaF(0.5)
        self._circle_item.setBrush(color)

    def itemChange(self, change, value):
        """
        Keeps track of item's movements on the scene. Rotates svg item if the relationship is 2D.
        This makes it possible to define e.g. an arow icon for relationships that express direction.

        Args:
            change (GraphicsItemChange): a flag signalling the type of the change
            value: a value related to the change

        Returns:
            the same value given as input
        """
        if change == QGraphicsItem.ItemScenePositionHasChanged:
            self._moved_on_scene = True
            self._rotate_svg_item()
        return super().itemChange(change, value)

    def setVisible(self, on):
        """Sets visibility status for this item and all arc items.

        Args:
            on (bool)
        """
        super().setVisible(on)
        for arc_item in self.arc_items:
            arc_item.setVisible(arc_item.el_item.isVisible() and arc_item.ent_item.isVisible())

    def _make_menu(self):
        menu = self._spine_db_editor.ui.graphicsView.make_items_menu()
        expand_menu = QMenu("Expand", menu)
        expand_menu.triggered.connect(self._expand)
        collapse_menu = QMenu("Collapse", menu)
        collapse_menu.triggered.connect(self._collapse)
        connect_entities_menu = QMenu("Connect entities", menu)
        connect_entities_menu.triggered.connect(self._start_connecting_entities)
        self._refresh_db_map_entity_class_lists()
        self._populate_expand_collapse_menu(expand_menu)
        self._populate_expand_collapse_menu(collapse_menu)
        self._populate_connect_entities_menu(connect_entities_menu)
        first = menu.actions()[0]
        first = menu.insertSeparator(first)
        first = menu.insertMenu(first, connect_entities_menu)
        first = menu.insertMenu(first, collapse_menu)
        menu.insertMenu(first, expand_menu)
        menu.addAction("Duplicate", self._duplicate)
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

    def _rotate_svg_item(self):
        arc_items_as_ent = [x for x in self.arc_items if x.ent_item is self]
        if len(arc_items_as_ent) != 2 or self.first_id is None:
            self._svg_item.setRotation(0)
            return
        first_dimension = self.dimension_name_list[0]
        element1 = arc_items_as_ent[0].el_item
        element2 = arc_items_as_ent[1].el_item
        if element1.entity_class_name == first_dimension:
            start = element1.pos()
            end = element2.pos()
        else:
            start = element2.pos()
            end = element1.pos()
        line = QLineF(start, end)
        self._svg_item.setRotation(-line.angle())

    def mouseDoubleClickEvent(self, e):
        connect_entities_menu = QMenu(self._spine_db_editor)
        title = TitleWidgetAction("Connect entities", self._spine_db_editor)
        connect_entities_menu.addAction(title)
        connect_entities_menu.triggered.connect(self._start_connecting_entities)
        self._refresh_db_map_entity_class_lists()
        self._populate_connect_entities_menu(connect_entities_menu)
        connect_entities_menu.popup(e.screenPos())

    def _duplicate(self):
        self._spine_db_editor.duplicate_entity(self)

    def _refresh_db_map_entity_class_lists(self):
        self._db_map_entity_class_lists.clear()
        db_map_entity_ids = {db_map: {id_} for db_map, id_ in self.db_map_ids}
        entity_ids_per_class = {}
        for db_map, ents in self.db_mngr.find_cascading_entities(db_map_entity_ids).items():
            for ent in ents:
                entity_ids_per_class.setdefault((db_map, ent["class_id"]), set()).add(ent["id"])
        db_map_entity_class_ids = {db_map: self.entity_class_ids(db_map) for db_map in self.db_maps}
        for db_map, ent_clss in self.db_mngr.find_cascading_entity_classes(db_map_entity_class_ids).items():
            for ent_cls in ent_clss:
                ent_cls = ent_cls._extended()
                ent_cls["dimension_id_list"] = list(ent_cls["dimension_id_list"])
                ent_cls["entity_ids"] = entity_ids_per_class.get((db_map, ent_cls["id"]), set())
                self._db_map_entity_class_lists.setdefault(ent_cls["name"], []).append((db_map, ent_cls))

    def _populate_expand_collapse_menu(self, menu):
        """
        Populates the 'Expand' or 'Collapse' menu.

        Args:
            menu (QMenu)
        """
        if not self._db_map_entity_class_lists:
            menu.setEnabled(False)
            return
        menu.setEnabled(True)
        menu.addAction("All")
        menu.addSeparator()
        for name, db_map_ent_clss in sorted(self._db_map_entity_class_lists.items()):
            db_map, ent_cls = next(iter(db_map_ent_clss))
            icon = self.db_mngr.entity_class_icon(db_map, ent_cls["id"])
            menu.addAction(icon, name).setEnabled(any(rel_cls["entity_ids"] for (db_map, rel_cls) in db_map_ent_clss))

    def _populate_connect_entities_menu(self, menu):
        """
        Populates the 'Add relationships' menu.

        Args:
            menu (QMenu)
        """
        entity_class_ids_in_graph = {}
        for item in self._spine_db_editor.ui.graphicsView.entity_items:
            if not isinstance(item, EntityItem):
                continue
            for db_map in item.db_maps:
                entity_class_ids_in_graph.setdefault(db_map, set()).update(item.entity_class_ids(db_map))
        action_name_icon_enabled = []
        for name, db_map_ent_clss in self._db_map_entity_class_lists.items():
            for db_map, ent_cls in db_map_ent_clss:
                icon = self.db_mngr.entity_class_icon(db_map, ent_cls["id"])
                action_name = name + "@" + db_map.codename
                enabled = set(ent_cls["dimension_id_list"]) <= entity_class_ids_in_graph.get(db_map, set())
                action_name_icon_enabled.append((action_name, icon, enabled))
        for action_name, icon, enabled in sorted(action_name_icon_enabled):
            menu.addAction(icon, action_name).setEnabled(enabled)
        menu.setEnabled(bool(self._db_map_entity_class_lists))

    def _get_db_map_entity_ids_to_expand_or_collapse(self, action):
        if action.text() == "All":
            return {
                (db_map, id_)
                for db_map_ent_clss in self._db_map_entity_class_lists.values()
                for db_map, ent_cls in db_map_ent_clss
                for id_ in ent_cls["entity_ids"]
            }
        db_map_ent_clss = self._db_map_entity_class_lists.get(action.text())
        if db_map_ent_clss is not None:
            return {(db_map, id_) for db_map, ent_cls in db_map_ent_clss for id_ in ent_cls["entity_ids"]}
        return ()

    @Slot(QAction)
    def _expand(self, action):
        db_map_entity_ids = self._get_db_map_entity_ids_to_expand_or_collapse(action)
        self._spine_db_editor.expand_graph(db_map_entity_ids)

    @Slot(QAction)
    def _collapse(self, action):
        db_map_entity_ids = self._get_db_map_entity_ids_to_expand_or_collapse(action)
        self._spine_db_editor.collapse_graph(db_map_entity_ids)

    @Slot(QAction)
    def _start_connecting_entities(self, action):
        class_name, db_name = action.text().split("@")
        db_map_ent_cls_lst = self._db_map_entity_class_lists[class_name]
        db_map, ent_cls = next(
            iter((db_map, ent_cls) for db_map, ent_cls in db_map_ent_cls_lst if db_map.codename == db_name)
        )
        self._spine_db_editor.start_connecting_entities(db_map, ent_cls, self)


class ArcItem(QGraphicsPathItem):
    """Connects two EntityItems."""

    def __init__(self, ent_item, el_item, width):
        """
        Args:
            ent_item (spinetoolbox.widgets.graph_view_graphics_items.EntityItem): entity item
            el_item (spinetoolbox.widgets.graph_view_graphics_items.EntityItem): element item
            width (float): Preferred line width
        """
        super().__init__()
        self.ent_item = ent_item
        self.el_item = el_item
        self._original_width = float(width)
        self._pen = self._make_pen()
        self.setPen(self._pen)
        self.setZValue(-2)
        self._scaling_factor = 1
        self._gradient = QGraphicsPathItem(self)
        self._gradient.setPen(Qt.NoPen)
        self._gradient_position = 0.5
        self._gradient_width = 1
        self._gradient_sign = 1
        ent_item.add_arc_item(self)
        el_item.add_arc_item(self)
        self.setCursor(Qt.ArrowCursor)
        self.update_line()

    def clone(self, entity_items):
        ent_item = entity_items[self.ent_item.db_map_ids]
        el_item = entity_items[self.el_item.db_map_ids]
        return type(self)(ent_item, el_item, self._original_width)

    def _make_pen(self):
        pen = QPen()
        pen.setWidthF(self._original_width)
        color = QGuiApplication.palette().color(QPalette.Normal, QPalette.WindowText)
        color.setAlphaF(0.8)
        pen.setColor(color)
        pen.setStyle(Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap)
        return pen

    def moveBy(self, dx, dy):
        """Does nothing. This item is not moved the regular way, but follows the EntityItems it connects."""

    def update_line(self):
        path = QPainterPath(self.ent_item.pos())
        path.lineTo(self.el_item.pos())
        self.setPath(path)
        self._do_move_gradient()

    def update_color(self, color):
        self._pen.setColor(color)
        self.setPen(self._pen)
        color = QColor(color)
        color.setAlphaF(0.5)
        self._gradient.setBrush(color)

    def apply_value(self, factor, sign):
        self._update_width()
        self._move_gradient(factor, sign)

    def mousePressEvent(self, event):
        """Accepts the event so it's not propagated."""
        event.accept()

    def other_item(self, item):
        return {self.ent_item: self.el_item, self.el_item: self.ent_item}.get(item)

    def apply_zoom(self, factor):
        """Applies zoom.

        Args:
            factor (float): The zoom factor.
        """
        self._scaling_factor = max(factor, 1)
        self._update_width()

    def _update_width(self):
        width = self._original_width / self._scaling_factor
        self._pen.setWidthF(width)
        self.setPen(self._pen)

    def _move_gradient(self, factor, sign):
        self._gradient_sign = sign
        self._gradient_width = max(1, factor)
        self._gradient_position += 0.1 * self._gradient_sign / self._scaling_factor
        if self._gradient_position > 1:
            self._gradient_position -= 1
        elif self._gradient_position < 0:
            self._gradient_position += 1
        self._do_move_gradient()

    def _do_move_gradient(self):
        width = self._original_width * self._gradient_width / self._scaling_factor
        init_pos, final_pos = self.ent_item.pos(), self.el_item.pos()
        line = QLineF(init_pos, final_pos)
        line.translate(self._gradient_position * line.dx(), self._gradient_position * line.dy())
        line.setLength(width)
        line.translate(-line.dx() / 2, -line.dy() / 2)
        if self._gradient_sign < 0:
            line.setPoints(line.p2(), line.p1())
        normal = line.normalVector()
        normal.translate(-normal.dx() / 2, -normal.dy() / 2)
        path = QPainterPath(line.p2())
        path.lineTo(normal.p1())
        path.lineTo(normal.p2())
        self._gradient.setPath(path)


class CrossHairsItem(EntityItem):
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
    def name(self):
        return None

    @property
    def has_dimensions(self):
        return False

    def _make_tool_tip(self):
        return "<p>Click on an object to add it to the relationship.</p>"

    def _has_name(self):
        return False

    def refresh_icon(self):
        self._renderer = self.db_mngr.get_icon_mngr(self.first_db_map).icon_renderer("\uf05b", 0)
        self._install_renderer()

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
        self._renderer = self.db_mngr.get_icon_mngr(self.first_db_map).icon_renderer(unicode, color)
        self._install_renderer()
        self._current_icon = (unicode, color)

    def _snap(self, x, y):
        return (x, y)

    def mouseMoveEvent(self, event):
        delta = event.scenePos() - self.scenePos()
        self.move_by(delta.x(), delta.y())

    def contextMenuEvent(self, e):
        e.accept()


class CrossHairsEntityItem(EntityItem):
    """Represents the relationship that's being created using the CrossHairsItem."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)

    @property
    def has_dimensions(self):
        return True

    def _make_tool_tip(self):
        return None

    def _has_name(self):
        return False

    def refresh_icon(self):
        """Refreshes the icon."""
        el_items = [arc_item.el_item for arc_item in self.arc_items]
        dimension_name_list = tuple(
            el_item.entity_class_name for el_item in el_items if not isinstance(el_item, CrossHairsItem)
        )
        self._renderer = self.db_mngr.get_icon_mngr(self.first_db_map).multi_class_renderer(dimension_name_list)
        self._install_renderer()

    def contextMenuEvent(self, e):
        e.accept()


class CrossHairsArcItem(ArcItem):
    """Connects a CrossHairsEntityItem with the CrossHairsItem,
    and with all the EntityItem's in the relationship so far.
    """

    def _make_pen(self):
        pen = super()._make_pen()
        pen.setStyle(Qt.DotLine)
        color = pen.color()
        color.setAlphaF(0.5)
        pen.setColor(color)
        return pen


class EntityLabelItem(QGraphicsTextItem):
    """Provides a label for EntityItem."""

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

    def boundingRect(self):
        if not self.isVisible():
            return QRectF()
        return super().boundingRect()

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


class BgItem(QGraphicsRectItem):
    class Anchor(Enum):
        TL = auto()
        TR = auto()
        BL = auto()
        BR = auto()

    _getter_setter = {
        Anchor.TL: ("topLeft", "setTopLeft"),
        Anchor.TR: ("topRight", "setTopRight"),
        Anchor.BL: ("bottomLeft", "setBottomLeft"),
        Anchor.BR: ("bottomRight", "setBottomRight"),
    }

    _cursors = {
        Anchor.TL: Qt.SizeFDiagCursor,
        Anchor.TR: Qt.SizeBDiagCursor,
        Anchor.BL: Qt.SizeBDiagCursor,
        Anchor.BR: Qt.SizeFDiagCursor,
    }

    def __init__(self, svg, parent=None):
        super().__init__(parent)
        self._renderer = QSvgRenderer()
        self._svg_item = _ResizableQGraphicsSvgItem(self)
        self.svg = svg
        _loading_ok = self._renderer.load(QByteArray(self.svg))
        self._svg_item.setCacheMode(QGraphicsItem.CacheMode.NoCache)  # Needed for the exported pdf to be vector
        self._svg_item.setSharedRenderer(self._renderer)
        self._scaling_factor = 1
        size = self._renderer.defaultSize()
        self.setRect(0, 0, size.width(), size.height())
        self.setZValue(-1000)
        self.setPen(Qt.NoPen)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self._resizers = {anchor: _Resizer(parent=self) for anchor in self.Anchor}
        for anchor, resizer in self._resizers.items():
            resizer.resized.connect(lambda delta, strong, anchor=anchor: self._resize(anchor, delta, strong))
            resizer.setCursor(self._cursors[anchor])
            resizer.hide()

    def clone(self):
        other = type(self)(self.svg)
        other.fit_rect(self.scene_rect())
        return other

    def hoverEnterEvent(self, ev):
        super().hoverEnterEvent(ev)
        for resizer in self._resizers.values():
            resizer.show()

    def hoverLeaveEvent(self, ev):
        super().hoverLeaveEvent(ev)
        for resizer in self._resizers.values():
            resizer.hide()

    def apply_zoom(self, factor):
        self._scaling_factor = factor
        self._place_resizers()

    def _place_resizers(self):
        for anchor, resizer in self._resizers.items():
            getter, _ = self._getter_setter[anchor]
            resizer.setPos(
                getattr(self.rect(), getter)() - getattr(resizer.rect(), getter)() / self.scale() / self._scaling_factor
            )

    def _resize(self, anchor, delta, strong):
        delta /= self.scale() * self._scaling_factor
        rect = self.rect()
        getter, setter = self._getter_setter[anchor]
        get_point = getattr(rect, getter)
        set_point = getattr(rect, setter)
        set_point(get_point() + delta)
        self._do_resize(rect, strong)

    def _do_resize(self, rect, strong):
        if strong:
            self._svg_item.resize(rect.width(), rect.height())
            self._svg_item.setPos(rect.topLeft())
            self.setPen(Qt.NoPen)
        else:
            self.setPen(QPen(Qt.DashLine))
        self.setRect(rect)
        self.prepareGeometryChange()
        self.update()
        self._place_resizers()

    def fit_rect(self, rect):
        if not isinstance(rect, QRectF):
            rect = QRectF(*rect)
        self._do_resize(rect, True)

    def scene_rect(self):
        return self.mapToScene(self.rect()).boundingRect()


class _ResizableQGraphicsSvgItem(QGraphicsSvgItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._width = 0
        self._height = 0
        self.setFlag(QGraphicsItem.ItemStacksBehindParent, True)

    def resize(self, width, height):
        self._width = width
        self._height = height
        self.prepareGeometryChange()
        self.update()

    def setSharedRenderer(self, renderer):
        super().setSharedRenderer(renderer)
        self._width = renderer.defaultSize().width()
        self._height = renderer.defaultSize().height()

    def boundingRect(self):
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter, options, widget):
        self.renderer().render(painter, self.boundingRect())


class _Resizer(QGraphicsRectItem):
    class SignalsProvider(QObject):
        resized = Signal(QPointF, bool)

    def __init__(self, rect=QRectF(0, 0, 20, 20), parent=None):
        super().__init__(rect, parent)
        self._original_rect = self.rect()
        self._press_pos = None
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations, True)
        self._signal_provider = self.SignalsProvider()
        self.resized = self._signal_provider.resized

    def mousePressEvent(self, ev):
        super().mousePressEvent(ev)
        self._press_pos = ev.pos()

    def mouseMoveEvent(self, ev):
        super().mouseMoveEvent(ev)
        delta = ev.pos() - self._press_pos
        self._signal_provider.resized.emit(delta, False)

    def mouseReleaseEvent(self, ev):
        super().mouseReleaseEvent(ev)
        delta = ev.pos() - self._press_pos
        self._signal_provider.resized.emit(delta, True)
