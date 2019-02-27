######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
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
from PySide2.QtCore import Signal, Slot, Qt, QRectF, QPointF, QTimeLine, QMarginsF
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
        self.target_viewport_pos = None
        self.target_scene_pos = QPointF(0, 0)
        self._num_scheduled_scalings = 0
        self.anim = None
        self.rel_zoom_factor = 1.0
        self.default_zoom_factor = 1
        self.max_rel_zoom_factor = 10.0
        self.min_rel_zoom_factor = 0.1

    # def keyPressEvent(self, evnt):
    # TODO: Check that this does not conflict with other key presses (Delete in particular)
    #     pass

    def mousePressEvent(self, event):
        """Set rubber band selection mode if Control pressed.
        Enable resetting the zoom factor from the middle mouse button.
        """
        if event.modifiers() & Qt.ControlModifier:
            self.setDragMode(QGraphicsView.RubberBandDrag)
        if event.button() == Qt.MidButton:
            self.reset_zoom()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        super().mouseReleaseEvent(event)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mouseMoveEvent(self, event):
        """Register mouse position to recenter the scene after zoom."""
        super().mouseMoveEvent(event)
        if self.target_viewport_pos is not None:
            delta = self.target_viewport_pos - event.pos()
            if delta.manhattanLength() <= 3:
                return
        self.target_viewport_pos = event.pos()
        self.target_scene_pos = self.mapToScene(self.target_viewport_pos)

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
        smooth_zoom_str = qsettings.value("appSettings/smoothZoom", defaultValue="false")
        smooth_zoom = True if smooth_zoom_str == "true" else False
        if smooth_zoom:
            num_degrees = event.delta() / 8
            num_steps = num_degrees / 15
            self._num_scheduled_scalings += num_steps
            if self._num_scheduled_scalings * num_steps < 0:
                self._num_scheduled_scalings = num_steps
            if self.anim:
                self.anim.deleteLater()
            self.anim = QTimeLine(200, self)
            self.anim.setUpdateInterval(20)
            self.anim.valueChanged.connect(self.scaling_time)
            self.anim.finished.connect(self.anim_finished)
            self.anim.start()
        else:
            angle = event.angleDelta().y()
            factor = self._zoom_factor_base ** angle
            self.gentle_zoom(factor)

    def scaling_time(self, x):
        """Called when animation value for smooth zoom changes. Perform zoom."""
        factor = 1.0 + self._num_scheduled_scalings / 100.0
        self.gentle_zoom(factor)

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
        self.target_viewport_pos = self.viewport().rect().center()
        self.target_scene_pos = self.mapToScene(self.target_viewport_pos)
        self.gentle_zoom(self._zoom_factor_base ** self._angle)

    def zoom_out(self):
        """Perform a zoom out with a fixed scaling."""
        self.gentle_zoom(self._zoom_factor_base ** -self._angle)

    def reset_zoom(self):
        """Reset zoom to the default factor."""
        self.resetTransform()
        self.scale(self.default_zoom_factor, self.default_zoom_factor)
        self.rel_zoom_factor = 1.0

    def gentle_zoom(self, factor):
        """Perform a zoom by a given factor."""
        new_rel_zoom_factor = self.rel_zoom_factor * factor
        if new_rel_zoom_factor > self.max_rel_zoom_factor or new_rel_zoom_factor < self.min_rel_zoom_factor:
            return
        self.rel_zoom_factor = new_rel_zoom_factor
        self.scale(factor, factor)
        self.centerOn(self.target_scene_pos)
        delta_viewport_pos = self.target_viewport_pos - self.viewport().geometry().center()
        viewport_center = self.mapFromScene(self.target_scene_pos) - delta_viewport_pos
        self.centerOn(self.mapToScene(viewport_center))

    def scale_to_fit_scene(self):
        """Scale view so the scene fits best in it."""
        if not self.isVisible():
            return
        scene_rect = self.sceneRect()
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
        self.src_item_name = None  # Name of source project item when drawing links
        self.dst_item_name = None  # Name of destination project item when drawing links
        self.show()

    def mousePressEvent(self, e):
        """Manage drawing of links. Handle the case where a link is being
        drawn and the user doesn't hit a connector button.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        was_drawing = self.link_drawer.drawing if self.link_drawer else None
        # This below will trigger connector button if any
        super().mousePressEvent(e)
        if was_drawing:
            self.link_drawer.hide()
            # If `drawing` is still `True` here, it means we didn't hit a connector
            if self.link_drawer.drawing:
                self.link_drawer.drawing = False
                if e.button() != Qt.LeftButton:
                    return
                self._toolbox.msg_warning.emit("Unable to make connection. Try landing "
                                               "the connection onto a connector button.")

    def mouseReleaseEvent(self, event):
        """Mouse release event.

        Args:
            event (QGraphicsSceneMouseEvent): Mouse event
        """
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.drawing:
            self.link_drawer.dst = self.mapToScene(e.pos())
            self.link_drawer.update_geometry()
        super().mouseMoveEvent(e)

    def wheelEvent(self, event):
        """Zoom in/out."""
        super().wheelEvent(event)

    def showEvent(self, event):
        """Calls super method. Not in use."""
        super().showEvent(event)

    def resizeEvent(self, event):
        """Calls super method. Not in use."""
        super().resizeEvent(event)

    def set_ui(self, toolbox):
        """Set a new scene into the Design View when app is started."""
        self._toolbox = toolbox
        self.setScene(CustomQGraphicsScene(self, toolbox))
        self.scene().changed.connect(self.scene_changed)

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

    def resize_scene(self):
        """Resize scene to be at least the size of items bounding rectangle.
        Does not let the scene shrink."""
        scene_rect = self.scene().sceneRect()
        items_rect = self.scene().itemsBoundingRect()
        union_rect = scene_rect | items_rect
        self.scene().setSceneRect(union_rect)

    @Slot("QList<QRectF>", name="scene_changed")
    def scene_changed(self, rects):
        """Resize scene as it changes."""
        rect = self.scene().sceneRect()
        # logging.debug("scene_changed pos:({0:.1f}, {1:.1f}) size:({2:.1f}, {3:.1f})"
        #               .format(rect.x(), rect.y(), rect.width(), rect.height()))
        self.resize_scene()

    def set_project_item_model(self, model):
        """Set project item model."""
        self._project_item_model = model

    def set_connection_model(self, model):
        """Set connection model and connect signals."""
        self._connection_model = model
        self._connection_model.rowsAboutToBeRemoved.connect(self.connection_rows_removed)
        self._connection_model.columnsAboutToBeRemoved.connect(self.connection_columns_removed)

    def add_link(self, src_name, dst_name, index):
        """Draws link between source and sink items on scene and
        appends connection model. Refreshes View references if needed."""
        src_item_index = self._project_item_model.find_item(src_name)
        dst_item_index = self._project_item_model.find_item(dst_name)
        src_item = self._project_item_model.project_item(src_item_index)
        dst_item = self._project_item_model.project_item(dst_item_index)
        # logging.debug("Adding link {0} -> {1}".format(src_name, dst_name))
        link = Link(self._toolbox, src_item.get_icon(), dst_item.get_icon())
        self.scene().addItem(link)
        self._connection_model.setData(index, link)
        # Refresh View references
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()

    def remove_link(self, index):
        """Removes link between source and sink items on scene and
        updates connection model. Refreshes View references if needed."""
        link = self._connection_model.data(index, Qt.UserRole)
        if not link:
            logging.error("Link not found. This should not happen.")
            return False
        # Find destination item
        dst_name = link.dst_icon.name()
        dst_item = self._project_item_model.project_item(self._project_item_model.find_item(dst_name))
        self.scene().removeItem(link)
        self._connection_model.setData(index, None)
        # Refresh View references
        if dst_item.item_type == "View":
            dst_item.view_refresh_signal.emit()

    def restore_links(self):
        """Iterate connection model and draw links to all that are 'True'
        Should be called only when a project is loaded from a save file."""
        rows = self._connection_model.rowCount()
        columns = self._connection_model.columnCount()
        for row in range(rows):
            for column in range(columns):
                index = self._connection_model.index(row, column)
                data = self._connection_model.data(index, Qt.DisplayRole)  # NOTE: data DisplayRole returns a string
                src_name = self._connection_model.headerData(row, Qt.Vertical, Qt.DisplayRole)
                dst_name = self._connection_model.headerData(column, Qt.Horizontal, Qt.DisplayRole)
                src = self._project_item_model.find_item(src_name)
                src_item = self._project_item_model.project_item(src)
                dst = self._project_item_model.find_item(dst_name)
                dst_item = self._project_item_model.project_item(dst)
                if data == "True":
                    # logging.debug("Cell ({0},{1}):{2} -> Adding link".format(row, column, data))
                    link = Link(self._toolbox, src_item.get_icon(), dst_item.get_icon())
                    self.scene().addItem(link)
                    self._connection_model.setData(index, link)
                else:
                    # logging.debug("Cell ({0},{1}):{2} -> No link".format(row, column, data))
                    self._connection_model.setData(index, None)

    @Slot("QModelIndex", "int", "int", name='connection_rows_removed')
    def connection_rows_removed(self, index, first, last):
        """Update view when connection model changes."""
        for i in range(first, last+1):
            for j in range(self._connection_model.columnCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connection_columns_removed')
    def connection_columns_removed(self, index, first, last):
        """Update view when connection model changes."""
        for j in range(first, last+1):
            for i in range(self._connection_model.rowCount()):
                link = self._connection_model.link(i, j)
                if link:
                    self.scene().removeItem(link)

    def draw_links(self, src_rect, name):
        """Draw links when slot button is clicked.

        Args:
            src_rect (QRectF): Position on scene where to start drawing. Rect of connector button.
            name (str): Name of item where to start drawing
        """
        if not self.link_drawer.drawing:
            # start drawing and remember connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(src_rect)
            self.src_item_name = name
        else:
            # stop drawing and make connection
            self.link_drawer.drawing = False
            self.dst_item_name = name
            # create connection
            row = self._connection_model.header.index(self.src_item_name)
            column = self._connection_model.header.index(self.dst_item_name)
            index = self._connection_model.createIndex(row, column)
            if self._connection_model.data(index, Qt.DisplayRole) == "False":
                self.add_link(self.src_item_name, self.dst_item_name, index)
                self._toolbox.msg.emit("<b>{}</b>'s output is now connected to <b>{}</b>'s input."
                                       .format(self.src_item_name, self.dst_item_name))
            elif self._connection_model.data(index, Qt.DisplayRole) == "True":
                self._toolbox.msg.emit("<b>{}</b>'s output is already connected to <b>{}</b>'s input."
                                       .format(self.src_item_name, self.dst_item_name))
            self.emit_connection_information_message()

    def emit_connection_information_message(self):
        """Inform user about what connections are implemented and how they work."""
        if self.src_item_name == self.dst_item_name:
            self._toolbox.msg_warning.emit("<b>Not implemented</b>. The functionality for feedback links "
                                           "is not implemented yet.")
        else:
            src_index = self._project_item_model.find_item(self.src_item_name)
            if not src_index:
                logging.error("Item {0} not found".format(self.src_item_name))
                return
            dst_index = self._project_item_model.find_item(self.dst_item_name)
            if not dst_index:
                logging.error("Item {0} not found".format(self.dst_item_name))
                return
            src_item_type = self._project_item_model.project_item(src_index).item_type
            dst_item_type = self._project_item_model.project_item(dst_index).item_type
            if src_item_type == "Data Connection" and dst_item_type == "Tool":
                self._toolbox.msg.emit("-> Input files for <b>{0}</b>'s execution "
                                       "will be looked up in <b>{1}</b>'s references and data directory."
                                       .format(self.dst_item_name, self.src_item_name))
            elif src_item_type == "Data Store" and dst_item_type == "Tool":
                self._toolbox.msg.emit("-> Input files for <b>{0}</b>'s execution "
                                       "will be looked up in <b>{1}</b>'s data directory."
                                       .format(self.dst_item_name, self.src_item_name))
            elif src_item_type == "Tool" and dst_item_type in ["Data Connection", "Data Store"]:
                self._toolbox.msg.emit("-> Output files from <b>{0}</b>'s execution "
                                       "will be passed as reference to <b>{1}</b>'s data directory."
                                       .format(self.src_item_name, self.dst_item_name))
            elif src_item_type in ["Data Connection", "Data Store"] \
                    and dst_item_type in ["Data Connection", "Data Store"]:
                self._toolbox.msg.emit("-> Input files for a tool's execution "
                                       "will be looked up in <b>{0}</b> if not found in <b>{1}</b>."
                                       .format(self.src_item_name, self.dst_item_name))
            elif src_item_type == "Data Store" and dst_item_type == "View":
                self._toolbox.msg_warning.emit("-> Database references in <b>{0}</b> will be viewed by <b>{1}</b>."
                                               .format(self.src_item_name, self.dst_item_name))
            elif src_item_type == "Tool" and dst_item_type == "Tool":
                self._toolbox.msg_warning.emit("<b>Not implemented</b>. Interaction between two "
                                               "Tool items is not implemented yet.")
            else:
                self._toolbox.msg_warning.emit("<b>Not implemented</b>. Whatever you are trying to do "
                                               "is not implemented yet :)")


class GraphQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Graph View."""

    item_dropped = Signal("QPoint", "QString", name="item_dropped")

    def __init__(self, parent):
        """Init GraphQGraphicsView."""
        super().__init__(parent=parent)
        self._graph_view_form = None

    def mousePressEvent(self, event):
        """Call superclass method."""
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Register mouse position to recenter the scene after zoom."""
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        """Zoom in/out."""
        super().wheelEvent(event)

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
