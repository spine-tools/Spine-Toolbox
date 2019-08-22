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
Classes for custom QGraphicsViews for the Design and Graph views.

:authors: P. Savolainen (VTT), M. Marin (KTH)
:date:   6.2.2018
"""

import logging
from PySide2.QtWidgets import QGraphicsView
from PySide2.QtGui import QCursor
from PySide2.QtCore import Signal, Slot, Qt, QRectF, QTimeLine, QMarginsF
from graphics_items import LinkDrawer, Link
from widgets.custom_qlistview import DragListView
from widgets.custom_qgraphicsscene import CustomQGraphicsScene


class CustomQGraphicsView(QGraphicsView):
    """Super class for Design and Graph QGraphicsViews.

    Attributes:
        parent (QWidget): Parent widget
    """

    def __init__(self, parent):
        """Init CustomQGraphicsView."""
        super().__init__(parent=parent)  # Pass parent to QGraphicsView constructor
        self._zoom_factor_base = 1.0015
        self._angle = 120
        self._num_scheduled_scalings = 0
        self.anim = None
        self.default_zoom_factor = 1
        self.max_rel_zoom_factor = 10.0
        self.min_rel_zoom_factor = 0.1

    def keyPressEvent(self, event):
        """Overridden method. Enable zooming with plus and minus keys (comma resets zoom).
        Send event downstream to QGraphicsItems if pressed key is not handled here.

        Args:
            event (QKeyEvent): Pressed key
        """
        if event.key() == Qt.Key_Plus:
            self.zoom_in()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key_Comma:
            self.reset_zoom()
        else:
            super().keyPressEvent(event)

    def enterEvent(self, event):
        """Overridden method. Do not show the stupid open hand mouse cursor.

        Args:
            event (QEvent): event
        """
        super().enterEvent(event)
        self.viewport().setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Set rubber band selection mode if Control pressed.
        Enable resetting the zoom factor from the middle mouse button.
        """
        if event.modifiers() & Qt.ControlModifier:
            self.setDragMode(QGraphicsView.RubberBandDrag)
            self.viewport().setCursor(Qt.CrossCursor)
        if event.button() == Qt.MidButton:
            self.reset_zoom()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.viewport().setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        """Zoom in/out.

        Args:
            event (QWheelEvent): Mouse wheel event
        """
        if event.orientation() != Qt.Vertical:
            event.ignore()
            return
        event.accept()
        ui = self.parent().parent()
        qsettings = ui.qsettings()
        smooth_zoom = qsettings.value("appSettings/smoothZoom", defaultValue="false")
        if smooth_zoom == "true":
            num_degrees = event.delta() / 8
            num_steps = num_degrees / 15
            self._num_scheduled_scalings += num_steps
            if self._num_scheduled_scalings * num_steps < 0:
                self._num_scheduled_scalings = num_steps
            if self.anim:
                self.anim.deleteLater()
            self.anim = QTimeLine(200, self)
            self.anim.setUpdateInterval(20)
            self.anim.valueChanged.connect(lambda x, pos=event.pos(): self.scaling_time(pos))
            self.anim.finished.connect(self.anim_finished)
            self.anim.start()
        else:
            angle = event.angleDelta().y()
            factor = self._zoom_factor_base ** angle
            self.gentle_zoom(factor, event.pos())

    def scaling_time(self, pos):
        """Called when animation value for smooth zoom changes. Perform zoom."""
        factor = 1.0 + self._num_scheduled_scalings / 100.0
        self.gentle_zoom(factor, pos)

    def anim_finished(self):
        """Called when animation for smooth zoom finishes. Clean up."""
        if self._num_scheduled_scalings > 0:
            self._num_scheduled_scalings -= 1
        else:
            self._num_scheduled_scalings += 1
        self.sender().deleteLater()
        self.anim = None

    def zoom_in(self):
        """Perform a zoom in with a fixed scaling."""
        self.gentle_zoom(self._zoom_factor_base ** self._angle, self.viewport().rect().center())

    def zoom_out(self):
        """Perform a zoom out with a fixed scaling."""
        self.gentle_zoom(self._zoom_factor_base ** -self._angle, self.viewport().rect().center())

    def reset_zoom(self):
        """Reset zoom to the default factor."""
        self.resetTransform()
        self.scale(self.default_zoom_factor, self.default_zoom_factor)

    def gentle_zoom(self, factor, center):
        """Perform a zoom by a given factor."""
        transform = self.transform()
        current_scaling_factor = transform.m11()  # The [1, 1] element contains the x scaling factor
        proposed_scaling_factor = current_scaling_factor * factor
        if proposed_scaling_factor > self.max_rel_zoom_factor or proposed_scaling_factor < self.min_rel_zoom_factor:
            return
        self.scale(factor, factor)
        scene_center = self.mapToScene(center)
        self.centerOn(scene_center)

    def scale_to_fit_scene(self):
        """Scale view so the scene fits best in it."""
        if not self.isVisible():
            return
        scene_rect = self.scene().sceneRect()
        scene_extent = max(scene_rect.width(), scene_rect.height())
        if not scene_extent:
            return
        size = self.size()
        extent = min(size.height(), size.width())
        self.default_zoom_factor = extent / scene_extent
        self.reset_zoom()


class DesignQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Design View.

    Attributes:
        parent (QWidget): Graph View Form's (QMainWindow) central widget (self.centralwidget)
    """

    def __init__(self, parent):
        """Initialize DesignQGraphicsView."""
        super().__init__(parent=parent)  # Parent is passed to QWidget's constructor
        self._scene = None
        self._toolbox = None
        self._connection_model = None
        self._project_item_model = None
        self.link_drawer = None
        self.src_connector = None  # Source connector of a link drawing operation
        self.dst_connector = None  # Destination connector of a link drawing operation
        self.src_item_name = None  # Name of source project item when drawing links
        self.dst_item_name = None  # Name of destination project item when drawing links
        self.show()

    def mousePressEvent(self, event):
        """Manage drawing of links. Handle the case where a link is being
        drawn and the user doesn't hit a connector button.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        was_drawing = self.link_drawer.drawing if self.link_drawer else None
        # This below will trigger connector button if any
        super().mousePressEvent(event)
        if was_drawing:
            self.link_drawer.hide()
            # If `drawing` is still `True` here, it means we didn't hit a connector
            if self.link_drawer.drawing:
                self.link_drawer.drawing = False
                if event.button() != Qt.LeftButton:
                    return
                self._toolbox.msg_warning.emit(
                    "Unable to make connection. Try landing " "the connection onto a connector button."
                )

    def mouseMoveEvent(self, event):
        """Update line end position.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.drawing:
            self.link_drawer.dst = self.mapToScene(event.pos())
            self.link_drawer.update_geometry()
        super().mouseMoveEvent(event)

    def set_ui(self, toolbox):
        """Set a new scene into the Design View when app is started."""
        self._toolbox = toolbox
        self.setScene(CustomQGraphicsScene(self, toolbox))

    def init_scene(self, empty=False):
        """Resize scene and add a link drawer on scene.
        The scene must be cleared before calling this.

        Args:
            empty (boolean): True when creating a new project
        """
        self.link_drawer = LinkDrawer()
        self.scene().addItem(self.link_drawer)
        if len(self.scene().items()) == 1:
            # Loaded project has no project items
            empty = True
        if not empty:
            # Reset scene rectangle to be as big as the items bounding rectangle
            items_rect = self.scene().itemsBoundingRect()
            margin_rect = items_rect.marginsAdded(QMarginsF(20, 20, 20, 20))  # Add margins
            self.scene().setSceneRect(margin_rect)
            self.centerOn(margin_rect.center())
        else:
            rect = QRectF(0, 0, 401, 301)
            self.scene().setSceneRect(rect)
            self.centerOn(rect.center())
        self.reset_zoom()  # Reset zoom

    def set_project_item_model(self, model):
        """Set project item model."""
        self._project_item_model = model

    def set_connection_model(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        self._connection_model.rowsAboutToBeRemoved.connect(self.connection_rows_removed)
        self._connection_model.columnsAboutToBeRemoved.connect(self.connection_columns_removed)

    def add_link(self, src_connector, dst_connector, index):
        """Draws link between source and sink items on scene and
        appends connection model. Refreshes View references if needed.

        Args:
            src_connector (ConnectorButton): Source connector button
            dst_connector (ConnectorButton): Destination connector button
            index (QModelIndex): Index in connection model
        """
        link = Link(self._toolbox, src_connector, dst_connector)
        self.scene().addItem(link)
        self._connection_model.setData(index, link)
        # Refresh View references
        src_name = src_connector.parent_name()  # Project item name
        dst_name = dst_connector.parent_name()  # Project item name
        dst_item_index = self._project_item_model.find_item(dst_name)
        dst_item = self._project_item_model.project_item(dst_item_index)
        # TODO: Add refresh signal and method to all project items, so that we don't need check what item is the dst
        # Refresh View and Data Interface items
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()
        elif dst_item.item_type == "Data Interface":
            dst_item.data_interface_refresh_signal.emit()
        # Add edge (connection link) to a dag as well
        self._toolbox.project().dag_handler.add_graph_edge(src_name, dst_name)

    def remove_link(self, index):
        """Removes link between source and sink items on scene and
        updates connection model. Refreshes View references if needed."""
        link = self._connection_model.data(index, Qt.UserRole)
        if not link:
            logging.error("Link not found. This should not happen.")
            return False
        # Source item name
        src_name = link.src_icon.name()
        # Find destination item and refresh it is a View
        dst_name = link.dst_icon.name()
        dst_item = self._project_item_model.project_item(self._project_item_model.find_item(dst_name))
        self.scene().removeItem(link)
        self._connection_model.setData(index, None)
        # TODO: Add refresh signal and method to all project items, so that we don't need check what item is the dst
        # Refresh View and Data Interface items
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()
        elif dst_item.item_type == "Data Interface":
            dst_item.data_interface_refresh_signal.emit()
        # Remove edge (connection link) from dag
        self._toolbox.project().dag_handler.remove_graph_edge(src_name, dst_name)

    def take_link(self, index):
        """Remove link, then start drawing another one from the same source connector."""
        link = self._connection_model.data(index, Qt.UserRole)
        self.remove_link(index)
        self.draw_links(link.src_connector)
        # noinspection PyArgumentList
        self.link_drawer.dst = self.mapToScene(self.mapFromGlobal(QCursor.pos()))
        self.link_drawer.update_geometry()

    def restore_links(self):
        """Iterates connection model and draws links for each valid entry.
        Should be called only when a project is loaded from a save file."""
        rows = self._connection_model.rowCount()
        columns = self._connection_model.columnCount()
        for row in range(rows):
            for column in range(columns):
                index = self._connection_model.index(row, column)
                data = self._connection_model.data(index, Qt.UserRole)
                # NOTE: data UserRole returns a list with source and destination positions
                if data:
                    try:
                        src_pos, dst_pos = data
                    except TypeError:
                        # Happens when first loading a project that wasn't saved with the current version
                        src_pos = dst_pos = "bottom"
                    src_name = self._connection_model.headerData(row, Qt.Vertical, Qt.DisplayRole)
                    dst_name = self._connection_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
                    src = self._project_item_model.find_item(src_name)
                    src_item = self._project_item_model.project_item(src)
                    dst = self._project_item_model.find_item(dst_name)
                    dst_item = self._project_item_model.project_item(dst)
                    # logging.debug("Cell ({0},{1}):{2} -> Adding link".format(row, column, data))
                    src_icon = src_item.get_icon()
                    dst_icon = dst_item.get_icon()
                    link = Link(self._toolbox, src_icon.conn_button(src_pos), dst_icon.conn_button(dst_pos))
                    self.scene().addItem(link)
                    self._connection_model.setData(index, link)
                    # Add edge (connection link) to dag handler as well
                    self._toolbox.project().dag_handler.add_graph_edge(src_name, dst_name)
                else:
                    # logging.debug("Cell ({0},{1}):{2} -> No link".format(row, column, data))
                    self._connection_model.setData(index, None)

    @Slot("QModelIndex", "int", "int", name='connection_rows_removed')
    def connection_rows_removed(self, index, first, last):
        """Update view when connection model changes."""
        for i in range(first, last + 1):
            for j in range(self._connection_model.columnCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connection_columns_removed')
    def connection_columns_removed(self, index, first, last):
        """Update view when connection model changes."""
        for j in range(first, last + 1):
            for i in range(self._connection_model.rowCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    def draw_links(self, connector):
        """Draw links when slot button is clicked.

        Args:
            connector (ConnectorButton): Connector button that triggered the drawing
        """
        if not self.link_drawer.drawing:
            # start drawing and remember source connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(connector.sceneBoundingRect())
            self.src_connector = connector
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.dst_connector = connector
            self.src_item_name = self.src_connector.parent_name()
            self.dst_item_name = self.dst_connector.parent_name()
            # create connection
            row = self._connection_model.header.index(self.src_item_name)
            column = self._connection_model.header.index(self.dst_item_name)
            index = self._connection_model.createIndex(row, column)
            if self._connection_model.data(index, Qt.DisplayRole) == "True":
                # Remove current link, so it gets updated
                self.remove_link(index)
            self.add_link(self.src_connector, self.dst_connector, index)
            self.emit_connection_information_message()

    def emit_connection_information_message(self):
        """Inform user about what connections are implemented and how they work."""
        if self.src_item_name == self.dst_item_name:
            self._toolbox.msg_warning.emit("Link established. Feedback link functionality not implemented.")
        else:
            src_index = self._project_item_model.find_item(self.src_item_name)
            if not src_index:
                logging.error("Item %s not found", self.src_item_name)
                return
            dst_index = self._project_item_model.find_item(self.dst_item_name)
            if not dst_index:
                logging.error("Item %s not found", self.dst_item_name)
                return
            src_item_type = self._project_item_model.project_item(src_index).item_type
            dst_item_type = self._project_item_model.project_item(dst_index).item_type
            if src_item_type == "Data Connection" and dst_item_type == "Tool":
                self._toolbox.msg.emit(
                    "Link established. Tool <b>{0}</b> will look for input "
                    "files from <b>{1}</b>'s references and data directory.".format(
                        self.dst_item_name, self.src_item_name
                    )
                )
            elif src_item_type == "Data Store" and dst_item_type == "Tool":
                self._toolbox.msg.emit(
                    "Link established. Data Store <b>{0}</b> reference will "
                    "be passed to Tool <b>{1}</b> when executing.".format(self.src_item_name, self.dst_item_name)
                )
            elif src_item_type == "Tool" and dst_item_type in ["Data Connection", "Data Store"]:
                self._toolbox.msg.emit(
                    "Link established. Tool <b>{0}</b> output files will be "
                    "passed to item <b>{1}</b> after execution.".format(self.src_item_name, self.dst_item_name)
                )
            elif src_item_type in ["Data Connection", "Data Store", "Data Interface"] and dst_item_type in [
                "Data Connection",
                "Data Store",
                "Data Interface",
            ]:
                self._toolbox.msg.emit("Link established")
            elif src_item_type == "Tool" and dst_item_type == "View":
                self._toolbox.msg_warning.emit(
                    "Link established. You can visualize the ouput from Tool "
                    "<b>{0}</b> in View <b>{1}</b>.".format(self.src_item_name, self.dst_item_name)
                )
            elif src_item_type == "Data Store" and dst_item_type == "View":
                self._toolbox.msg_warning.emit(
                    "Link established. You can visualize Data Store "
                    "<b>{0}</b> in View <b>{1}</b>.".format(self.src_item_name, self.dst_item_name)
                )
            elif src_item_type == "Tool" and dst_item_type == "Tool":
                self._toolbox.msg_warning.emit("Link established.")
            else:
                self._toolbox.msg_warning.emit(
                    "Link established. Interaction between a "
                    "<b>{0}</b> and a <b>{1}</b> has not been "
                    "implemented yet.".format(src_item_type, dst_item_type)
                )


class GraphQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Graph View."""

    item_dropped = Signal("QPoint", "QString", name="item_dropped")

    def __init__(self, parent):
        """Init GraphQGraphicsView."""
        super().__init__(parent=parent)
        self._graph_view_form = None

    def dragLeaveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not DragListView."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not DragListView."""
        event.accept()
        source = event.source()
        if not isinstance(source, DragListView):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not DragListView."""
        event.accept()
        source = event.source()
        if not isinstance(source, DragListView):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of DragListView.
        Capture text from event's mimedata and emit signal.
        """
        source = event.source()
        if not isinstance(source, DragListView):
            super().dropEvent(event)
            return
        event.acceptProposedAction()
        text = event.mimeData().text()
        pos = event.pos()
        self.item_dropped.emit(pos, text)

    def contextMenuEvent(self, e):
        """Show context menu.

        Args:
            e (QContextMenuEvent): Context menu event
        """
        super().contextMenuEvent(e)
        if e.isAccepted():
            return
        if not self._graph_view_form:
            e.ignore()
            return
        e.accept()
        self._graph_view_form.show_graph_view_context_menu(e.globalPos())
