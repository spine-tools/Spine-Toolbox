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
Classes for drawing graphics items on QGraphicsScene.

:authors: M. Marin (KTH), P. Savolainen (VTT)
:date:    4.4.2018
"""

from math import atan2, sin, cos, pi
from itertools import product, chain
from PySide2.QtCore import Qt, Slot, QPointF, QLineF, QRectF, QVariantAnimation, QEventLoop
from PySide2.QtWidgets import QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, QGraphicsEllipseItem, QStyle
from PySide2.QtGui import QColor, QPen, QBrush, QPainterPath, QLinearGradient, QFont
from spinedb_api.filters.tools import filter_config
from spinedb_api.filters.scenario_filter import SCENARIO_FILTER_TYPE
from spinedb_api.filters.tool_filter import TOOL_FILTER_TYPE
from spinetoolbox.project_commands import ToggleFilterIdsCommand
from spinetoolbox.mvcmodels.resource_filter_model import ResourceFilterModel
from .project_item_icon import ConnectorButton


class LinkBase(QGraphicsPathItem):
    """Base class for Link and LinkDrawer.

    Mainly provides the ``update_geometry`` method for 'drawing' the link on the scene.
    """

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__()
        self._toolbox = toolbox
        self.arrow_angle = pi / 4
        self.setCursor(Qt.PointingHandCursor)

    @property
    def magic_number(self):
        return 0.625 * self.src_rect.width()

    @property
    def src_rect(self):
        """Returns the scene rectangle of the source connector."""
        return self.src_connector.sceneBoundingRect()

    @property
    def src_center(self):
        """Returns the center point of the source rectangle."""
        return self.src_rect.center()

    @property
    def dst_rect(self):
        """Returns the scene rectangle of the destination connector."""
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        """Returns the center point of the destination rectangle."""
        return self.dst_rect.center()

    def moveBy(self, _dx, _dy):
        """Does nothing. This item is not moved the regular way, but follows the ConnectorButtons it connects."""

    def update_geometry(self, curved_links=None):
        """Updates geometry."""
        self.prepareGeometryChange()
        if curved_links is None:
            qsettings = self._toolbox.qsettings()
            curved_links = qsettings.value("appSettings/curvedLinks", defaultValue="false") == "true"
        guide_path = self._make_guide_path(curved_links)
        self.do_update_geometry(guide_path)

    def do_update_geometry(self, guide_path):
        """Sets the path for this item.

        Args:
            guide_path (QPainterPath)
        """
        ellipse_path = self._make_ellipse_path()
        connecting_path = self._make_connecting_path(guide_path)
        arrow_path = self._make_arrow_path(guide_path)
        path = ellipse_path + connecting_path + arrow_path
        self.setPath(path.simplified())

    def _make_ellipse_path(self):
        """Returns an ellipse path for the link's base.

        Returns:
            QPainterPath
        """
        ellipse_path = QPainterPath()
        rect = QRectF(0, 0, 1.6 * self.magic_number, 1.6 * self.magic_number)
        rect.moveCenter(self.src_center)
        ellipse_path.addEllipse(rect)
        return ellipse_path

    def _get_src_offset(self):
        if self.src_connector == self.dst_connector:
            return {"left": QPointF(0, 1), "bottom": QPointF(1, 0), "right": QPointF(0, -1)}[
                self.src_connector.position
            ]
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.src_connector.position]

    def _get_dst_offset(self, c1):
        if not self.dst_connector:
            guide_path = QPainterPath(self.src_center)
            guide_path.quadTo(c1, self.dst_center)
            line = self._get_joint_line(guide_path).unitVector()
            return QPointF(-line.dx(), -line.dy())
        return {"left": QPointF(-1, 0), "bottom": QPointF(0, 1), "right": QPointF(1, 0)}[self.dst_connector.position]

    def _make_guide_path(self, curved_links):
        """Returns a 'narrow' path connecting this item's source and destination.

        Args:
            curved_links (bool): Whether the path should follow a curved line or just a straight line

        Returns:
            QPainterPath
        """
        path = QPainterPath(self.src_center)
        if not curved_links:
            path.lineTo(self.dst_center)
            return path
        c_min = 2 * self.magic_number
        c_max = 8 * self.magic_number
        c_factor = QLineF(self.src_center, self.dst_center).length() / 2
        c_factor = min(c_factor, c_max)
        c_factor = max(c_factor, c_min)
        c1 = self.src_center + c_factor * self._get_src_offset()
        c2 = self.dst_center + c_factor * self._get_dst_offset(c1)
        path.cubicTo(c1, c2, self.dst_center)
        return path

    def _points_and_angles_from_path(self, path):
        """Returns a list of representative points and angles from given path.

        Args:
            path (QPainterPath)

        Returns:
            list(QPointF): points
            list(float): angles
        """
        max_incr = 0.05
        min_incr = 0.01
        max_angle_change = 0.001
        percents = list()
        angles = list()
        t = path.percentAtLength(self.src_rect.width() / 2)
        a = path.angleAtPercent(t)
        while t < 0.5:
            percents.append(t)
            angles.append(a)
            t_ref = t
            a_ref = a
            incr = max_incr
            while incr > min_incr:
                t = t_ref + incr
                a = path.angleAtPercent(t)
                try:
                    angle_change = abs((a - a_ref) / (a_ref + a) / 2)
                except ZeroDivisionError:
                    incr = min_incr
                    break
                if angle_change < max_angle_change:
                    break
                incr /= 2
            t += incr
        t = 0.5
        a = path.angleAtPercent(t)
        percents.append(t)
        angles.append(a)
        points = list(map(path.pointAtPercent, percents))
        for t in reversed(percents):
            p = path.pointAtPercent(1.0 - t)
            a = path.angleAtPercent(1.0 - t)
            points.append(p)
            angles.append(a)
        return points, angles

    def _make_connecting_path(self, guide_path):
        """Returns a 'thick' path connecting source and destination, by following the given 'guide' path.

        Args:
            guide_path (QPainterPath)

        Returns:
            QPainterPath
        """
        points, angles = self._points_and_angles_from_path(guide_path)
        outgoing_points = []
        incoming_points = []
        for point, angle in zip(points, angles):
            off = self._radius_from_point_and_angle(point, angle)
            outgoing_points.append(point + off)
            incoming_points.insert(0, point - off)
        p0 = guide_path.pointAtPercent(0)
        a0 = guide_path.angleAtPercent(0)
        off0 = self._radius_from_point_and_angle(p0, a0)
        curve_path = QPainterPath(p0 + off0)
        self._follow_points(curve_path, outgoing_points)
        curve_path.lineTo(incoming_points[0])
        self._follow_points(curve_path, incoming_points)
        curve_path.lineTo(p0 - off0)
        curve_path.closeSubpath()
        curve_path.setFillRule(Qt.WindingFill)
        return curve_path.simplified()

    @staticmethod
    def _follow_points(curve_path, points):
        points = iter(points)
        for p0 in points:
            p1 = next(points)
            curve_path.quadTo(p0, p1)

    def _radius_from_point_and_angle(self, point, angle):
        line = QLineF()
        line.setP1(point)
        line.setAngle(angle)
        normal = line.normalVector()
        normal.setLength(self.magic_number / 2)
        return QPointF(normal.dx(), normal.dy())

    def _make_arrow_path(self, guide_path):
        """Returns an arrow path for the link's tip.

        Args:
            guide_path (QPainterPath): A narrow path connecting source and destination,
                used to determine the arrow orientation.

        Returns:
            QPainterPath
        """
        angle = self._get_joint_angle(guide_path)
        arrow_p0 = self.dst_center
        d1 = QPointF(sin(angle + self.arrow_angle), cos(angle + self.arrow_angle))
        d2 = QPointF(sin(angle + (pi - self.arrow_angle)), cos(angle + (pi - self.arrow_angle)))
        arrow_diag = self.magic_number / sin(self.arrow_angle)
        arrow_p1 = arrow_p0 - d1 * arrow_diag
        arrow_p2 = arrow_p0 - d2 * arrow_diag
        arrow_path = QPainterPath(arrow_p1)
        arrow_path.lineTo(arrow_p0)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        return arrow_path

    def _get_joint_line(self, guide_path):
        t = 1.0 - guide_path.percentAtLength(self.src_rect.width() / 2)
        t = max(t, 0.01)
        src = guide_path.pointAtPercent(t - 0.01)
        dst = guide_path.pointAtPercent(t)
        return QLineF(src, dst)

    def _get_joint_angle(self, guide_path):
        line = self._get_joint_line(guide_path)
        return atan2(-line.dy(), line.dx())


class FilterIcon(QGraphicsEllipseItem):
    """An icon to show that a Link has filters."""

    def __init__(self, x, y, w, h, parent):
        super().__init__(x, y, w, h, parent)
        self._parent = parent
        color = QColor("slateblue")
        self.setBrush(qApp.palette().window())  # pylint: disable=undefined-variable
        self._text_item = QGraphicsTextItem(self)
        font = QFont('Font Awesome 5 Free Solid')
        self._text_item.setFont(font)
        self._text_item.setPos(0, 0)
        self._text_item.setPlainText("\uf0b0")
        self._text_item.setDefaultTextColor(color)
        self._text_item.setPos(self.sceneBoundingRect().center() - self._text_item.sceneBoundingRect().center())
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=False)


class Link(LinkBase):
    """A graphics item to represent the connection between two project items."""

    def __init__(self, toolbox, src_connector, dst_connector, resource_filters=None):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            resource_filters (dict, optional): Mapping resource labels to filter types to list of values
        """
        super().__init__(toolbox)
        if resource_filters is None:
            resource_filters = {}
        self.src_connector = src_connector  # QGraphicsRectItem
        self.dst_connector = dst_connector
        self.src_icon = src_connector.parent
        self.dst_icon = dst_connector.parent
        self.selected_pen = QPen(Qt.black, 1, Qt.DashLine)
        self.normal_pen = QPen(Qt.black, 0.5)
        self._filter_icon_extent = 4 * self.magic_number
        self._filter_icon = FilterIcon(0, 0, self._filter_icon_extent, self._filter_icon_extent, self)
        self._filter_icon.setPen(self.normal_pen)
        self.setToolTip(
            "<html><p>Connection from <b>{0}</b>'s output "
            "to <b>{1}</b>'s input</html>".format(self.src_icon.name(), self.dst_icon.name())
        )
        self.setBrush(QBrush(QColor(255, 255, 0, 204)))
        self.parallel_link = None
        self.setFlag(QGraphicsItem.ItemIsSelectable, enabled=True)
        self.setFlag(QGraphicsItem.ItemIsFocusable, enabled=True)
        self.setZValue(0.5)  # This makes links appear on top of items because item zValue == 0.0
        self.update_geometry()
        self._color = QColor(255, 255, 0, 204)
        self._exec_color = None
        self.resource_filters = resource_filters
        self.resource_filter_model = ResourceFilterModel(self)
        self.db_mngr = toolbox.db_mngr
        self._fetched_db_resources = set()
        self._unfetched_db_resources = set()
        self._obsolete_db_resources = set()

    def handle_dag_changed(self, upstream_resources):
        """Handles changes in dag.

        Args:
            upstream_resources (list(ProjectItemResource)): Resources advertised by predecessor.
        """
        db_resources = {r for r in upstream_resources if r.type_ == "database"}
        self._unfetched_db_resources = db_resources - self._fetched_db_resources
        self._obsolete_db_resources = self._fetched_db_resources - db_resources

    def refresh_resource_filter_model(self):
        """Refreshes the resource filter model. Called when the Link becomes active."""
        self._fetch_unfetched()
        self._remove_obsolete()

    def _fetch_unfetched(self):
        """Fetches db maps corresponding to unfetched incoming db resources."""
        unfetched_db_maps = set()
        unfetchable_resources = set()
        for resource in self._unfetched_db_resources:
            db_map = self.db_mngr.get_db_map(resource.url, self._toolbox)
            if db_map is None:
                unfetchable_resources.add(resource)
                continue
            unfetched_db_maps.add(db_map)
        self._unfetched_db_resources -= unfetchable_resources
        self.resource_filter_model.init_resources(self._unfetched_db_resources)
        self.db_mngr.register_listener(self, *unfetched_db_maps)
        self._synch_fetch_db_maps(unfetched_db_maps)
        self._fetched_db_resources |= self._unfetched_db_resources
        self._unfetched_db_resources.clear()

    def _remove_obsolete(self):
        """Removes obsolete resources."""
        self.resource_filter_model.remove_resources({r.url for r in self._obsolete_db_resources})
        obsolete_db_maps = {self.db_mngr.get_db_map(r.url, self._toolbox) for r in self._obsolete_db_resources}
        obsolete_db_maps.discard(None)
        self.db_mngr.unregister_listener(self, *obsolete_db_maps)
        self._fetched_db_resources -= self._obsolete_db_resources
        self._obsolete_db_resources.clear()

    def _synch_fetch_db_maps(self, db_maps):
        """Fetches given db_maps synchronously. Called by ``refresh_resource_filter_model()`` and ``filter_stacks``.

        Args:
            db_maps (Sequence): DatabaseMapping instances
        """
        if not db_maps:
            return
        fetcher = self.db_mngr.get_fetcher(self)
        loop = QEventLoop()
        fetcher.finished.connect(loop.quit)
        fetcher.fetch(db_maps, tablenames=["scenario", "tool"])
        if not fetcher.is_finished:
            loop.exec_()
        self._update_filters(db_maps)

    def _update_filters(self, db_maps):
        """Updates filters for given resource after possible changes in the underlying db.
        Called by ``_synch_fetch_db_maps()``.

        Args:
            db_maps (Sequence): DatabaseMapping instances
        """
        resource_labels = {r.url: r.label for r in chain(self._fetched_db_resources, self._unfetched_db_resources)}
        for db_map in db_maps:
            resource_label = resource_labels.get(db_map.db_url)
            if not resource_label:
                continue
            valid_scenario_ids = {x["id"] for x in self.db_mngr.get_items(db_map, "scenario")}
            valid_tool_ids = {x["id"] for x in self.db_mngr.get_items(db_map, "tool")}
            filters = self.resource_filters.get(resource_label, {})
            filter_scen_ids = filters.get(SCENARIO_FILTER_TYPE, [])
            filter_tool_ids = filters.get(TOOL_FILTER_TYPE, [])
            invalid_scen_ids = set(filter_scen_ids) - valid_scenario_ids
            invalid_tool_ids = set(filter_tool_ids) - valid_tool_ids
            for id_ in invalid_scen_ids:
                filter_scen_ids.remove(id_)
            for id_ in invalid_tool_ids:
                filter_tool_ids.remove(id_)

    def filter_stacks(self):
        """Returns a dictionary mapping tuples (resource label, destination item name) to a list of filter stacks.
        A filter stack is simply a tuple where each element is a filter configuration dictionary.
        Stacks are computed as the cross-product of all individual filters defined for a resource.

        Returns:
            dict((str,str),list(tuple(dict)))
        """
        # Fetches resources that have filters defined, so we can call ``self.db_mngr.get_item()``
        # to compute the filter stacks
        resources_to_fetch = (
            resource_label
            for resource_label, filters in self.resource_filters.items()
            for filter_type, ids in filters.items()
            if ids
        )
        urls = {r.label: r.url for r in chain(self._fetched_db_resources, self._unfetched_db_resources)}
        db_maps = {}
        for resource_label in resources_to_fetch:
            url = urls.get(resource_label)
            if url is None:
                continue
            db_map = self.db_mngr.get_db_map(url, self._toolbox)
            if db_map is None:
                continue
            db_maps[resource_label] = db_map
        self._synch_fetch_db_maps(db_maps.values())
        # Now compute the filter stacks
        filter_stacks = {}
        for resource_label, filters in self.resource_filters.items():
            filter_configs_list = []
            for filter_type, ids in filters.items():
                db_map = db_maps.get(resource_label)
                if db_map is None:
                    filter_configs_list.append([])
                    continue
                item_type = {SCENARIO_FILTER_TYPE: "scenario", TOOL_FILTER_TYPE: "tool"}[filter_type]
                names = {self.db_mngr.get_item(db_map, item_type, id_).get("name") for id_ in ids}
                names.discard(None)
                filter_configs = [filter_config(filter_type, name) for name in names]
                filter_configs_list.append(filter_configs)
            filter_stacks[resource_label, self.dst_icon.name()] = list(product(*filter_configs_list))
        return filter_stacks

    def receive_scenarios_added(self, db_map_data):
        self.resource_filter_model.receive_scenarios_added(db_map_data)

    def receive_tools_added(self, db_map_data):
        self.resource_filter_model.receive_tools_added(db_map_data)

    def receive_scenarios_updated(self, _db_map_data):
        self.resource_filter_model.refresh_model()

    def receive_tools_updated(self, _db_map_data):
        self.resource_filter_model.refresh_model()

    def receive_scenarios_removed(self, db_map_data):
        self.resource_filter_model.receive_scenarios_removed(db_map_data)

    def receive_tools_removed(self, db_map_data):
        self.resource_filter_model.receive_tools_removed(db_map_data)

    def receive_session_rolled_back(self, db_maps):
        self._force_refetch(db_maps)

    def receive_session_refreshed(self, db_maps):
        self._force_refetch(db_maps)

    def _force_refetch(self, db_maps):
        """Forces refetching given db_maps in next activation, after they've been refreshed or rolled back.

        Args:
            db_maps (Sequence(DatabaseMapping))
        """
        for db_map in db_maps:
            url = db_map.db_url
            resource = next((r for r in self._fetched_db_resources if r.url == url), None)
            if resource is not None:
                self._fetched_db_resources.remove(resource)
                self._unfetched_db_resources.add(resource)
        if self == self._toolbox.active_link:
            self.refresh_resource_filter_model()

    @property
    def name(self):
        return f"from {self.src_icon.name()} to {self.dst_icon.name()}"

    def to_dict(self):
        """Returns a dictionary representation of this Link.

        Returns:
            dict
        """
        src_connector = self.src_connector
        src_anchor = src_connector.position
        src_name = src_connector.parent_name()
        dst_connector = self.dst_connector
        dst_anchor = dst_connector.position
        dst_name = dst_connector.parent_name()
        d = {"from": [src_name, src_anchor], "to": [dst_name, dst_anchor]}
        resource_filters = self._compile_resource_filters()
        if resource_filters:
            d["resource_filters"] = resource_filters
        return d

    def _compile_resource_filters(self):
        """Returns a dictionary mapping resource labels to another dictionary mapping filter type to filtered ids.
        Called by ``to_dict``.

        Returns:
            dict(str,dict(str,list))
        """
        resource_filters = {}
        for resource, filters in self.resource_filters.items():
            for filter_type, values in filters.items():
                if not values:
                    continue
                resource_filters.setdefault(resource, {})[filter_type] = values
        return resource_filters

    def toggle_filter_ids(self, resource, filter_type, *ids):
        """Pushes a ``ToggleFilterIdsCommand`` to the toolbox undo stack.

        Args:
            resource (str): Resource label
            filter_type (str): Either SCENARIO_FILTER_TYPE or TOOL_FILTER_TYPE, for now.
            ids (Iterable(int))
        """
        cmd = ToggleFilterIdsCommand(self, resource, filter_type, ids)
        self._toolbox.undo_stack.push(cmd)

    def _do_toggle_filter_ids(self, resource, filter_type, ids):
        """Toggles the given ids in the resource filters.

        Args:
            resource (str): Resource label
            filter_type (str): Either SCENARIO_FILTER_TYPE or TOOL_FILTER_TYPE, for now.
            ids (Iterable(int))
        """
        current = self.resource_filters.setdefault(resource, {}).setdefault(filter_type, [])
        for id_ in ids:
            if id_ in current:
                current.remove(id_)
            else:
                current.append(id_)
        if self == self._toolbox.active_link:
            self.resource_filter_model.refresh_model()
        self.update()

    def do_update_geometry(self, guide_path):
        """See base class."""
        super().do_update_geometry(guide_path)
        center = guide_path.pointAtPercent(0.5)
        self._filter_icon.setPos(center - 0.5 * QPointF(self._filter_icon_extent, self._filter_icon_extent))

    def make_execution_animation(self, skipped):
        """Returns an animation to play when execution 'passes' through this link.

        Returns:
            QVariantAnimation
        """
        colorname = "lightGray" if skipped else "red"
        self._exec_color = QColor(colorname)
        qsettings = self._toolbox.qsettings()
        duration = int(qsettings.value("appSettings/dataFlowAnimationDuration", defaultValue="100"))
        animation = QVariantAnimation()
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setDuration(duration)
        animation.valueChanged.connect(self._handle_execution_animation_value_changed)
        animation.finished.connect(lambda: self.setBrush(self._color))
        animation.finished.connect(animation.deleteLater)
        return animation

    @Slot(object)
    def _handle_execution_animation_value_changed(self, step):
        gradient = QLinearGradient(self.src_center, self.dst_center)
        delta = 8 * self.magic_number / QLineF(self.src_center, self.dst_center).length()
        gradient.setColorAt(0, self._color)
        gradient.setColorAt(max(0.0, step - delta), self._color)
        gradient.setColorAt(step, self._exec_color)
        gradient.setColorAt(min(1.0, step + delta), self._color)
        gradient.setColorAt(1.0, self._color)
        self.setBrush(gradient)

    def has_parallel_link(self):
        """Returns whether or not this link entirely overlaps another."""
        self.parallel_link = next(
            iter(l for l in self.dst_connector.outgoing_links() if l.dst_connector == self.src_connector), None
        )
        return self.parallel_link is not None

    def send_to_bottom(self):
        """Stacks this link before the parallel one if any."""
        if self.parallel_link:
            self.stackBefore(self.parallel_link)

    def mousePressEvent(self, e):
        """Ignores event if there's a connector button underneath,
        to allow creation of new links.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if any(isinstance(x, ConnectorButton) for x in self.scene().items(e.scenePos())):
            e.ignore()

    def contextMenuEvent(self, e):
        """Selects the link and shows context menu.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        self.setSelected(True)
        self._toolbox.show_link_context_menu(e.screenPos(), self)

    def paint(self, painter, option, widget=None):
        """Sets a dashed pen if selected."""
        self._filter_icon.setVisible(bool(self._compile_resource_filters()))
        if option.state & QStyle.State_Selected:
            option.state &= ~QStyle.State_Selected
            self.setPen(self.selected_pen)
            self._filter_icon.setPen(self.selected_pen)
        else:
            self.setPen(self.normal_pen)
            self._filter_icon.setPen(self.normal_pen)
        super().paint(painter, option, widget)

    def shape(self):
        shape = super().shape()
        if self._filter_icon.isVisible():
            shape.addEllipse(self._filter_icon.sceneBoundingRect())
        return shape

    def itemChange(self, change, value):
        """Brings selected link to top."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange and value == 1:
            for item in self.collidingItems():  # TODO: try using scene().collidingItems() which is ordered
                if not isinstance(item, Link):
                    continue
                item.stackBefore(self)
            return value
        return super().itemChange(change, value)

    def wipe_out(self):
        """Removes any trace of this item from the system."""
        self.src_connector.links.remove(self)
        self.dst_connector.links.remove(self)
        scene = self.scene()
        if scene:
            scene.removeItem(self)


class LinkDrawer(LinkBase):
    """An item for drawing links between project items."""

    def __init__(self, toolbox):
        """
        Args:
            toolbox (ToolboxUI): main UI class instance
        """
        super().__init__(toolbox)
        self.src_connector = None
        self.dst_connector = None
        self.tip = None
        self.setBrush(QBrush(QColor(255, 0, 255, 204)))
        self.setPen(QPen(Qt.black, 0.5))
        self.setZValue(1)  # LinkDrawer should be on top of every other item

    @property
    def src_rect(self):
        if not self.src_connector:
            return QRectF()
        return self.src_connector.sceneBoundingRect()

    @property
    def dst_rect(self):
        if not self.dst_connector:
            return QRectF()
        return self.dst_connector.sceneBoundingRect()

    @property
    def dst_center(self):
        if not self.dst_connector:
            return self.tip
        # If link drawer tip is on a connector button, this makes
        # the tip 'snap' to the center of the connector button
        return self.dst_rect.center()

    def add_link(self):
        """Makes link between source and destination connectors."""
        self._toolbox.ui.graphicsView.add_link(self.src_connector, self.dst_connector)
        self.sleep()

    def wake_up(self, src_connector):
        """Sets the source connector, shows this item and adds it to the scene.
        After calling this, the scene is in link drawing mode.

        Args:
            src_connector (ConnectorButton)
        """
        src_connector.scene().addItem(self)
        self.src_connector = src_connector
        self.src_connector.set_friend_connectors_enabled(False)
        self.tip = src_connector.sceneBoundingRect().center()
        self.update_geometry()
        self.show()

    def sleep(self):
        """Removes this drawer from the scene, clears its source and destination connectors, and hides it.
        After calling this, the scene is no longer in link drawing mode.
        """
        self.scene().removeItem(self)
        self.src_connector.set_friend_connectors_enabled(True)
        self.src_connector = self.dst_connector = self.tip = None
        self.hide()
