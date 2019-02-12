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
Class for a custom QGraphicsView for visualizing project items and connections.

:author: P. Savolainen (VTT)
:date:   6.2.2018
"""

import logging
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene
from PySide2.QtCore import Signal, Slot, Qt, QRectF, QPointF, QTimeLine
from PySide2.QtGui import QColor, QPen, QBrush
from graphics_items import LinkDrawer, Link, ItemImage
from widgets.toolbars import DraggableWidget
from widgets.custom_qlistview import DragListView


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
        self.default_zoom_factor = None
        self.max_rel_zoom_factor = 10.0
        self.min_rel_zoom_factor = 0.1

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
        """Zoom in/out."""
        if event.orientation() != Qt.Vertical:
            event.ignore()
            return
        event.accept()
        try:
            # TODO: This only work with DesignQGraphicsView
            config = self._graph_view_form._data_store._toolbox._config
            use_smooth_zoom = config.getboolean("settings", "use_smooth_zoom")
        except AttributeError:
            use_smooth_zoom = False
        if use_smooth_zoom:
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
        if not self.default_zoom_factor:
            return
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

    def set_ui(self, toolbox):
        """Set the main ToolboxUI instance."""
        self._toolbox = toolbox
        self._scene = CustomQGraphicsScene(self, toolbox)
        self.setScene(self._scene)
        self.make_link_drawer()
        self.init_scene()

    @Slot("QList<QRectF>", name='scene_changed')
    def scene_changed(self, changed_qrects):
        """Resize scene as it changes."""
        self.resize_scene()

    def make_new_scene(self):
        """Make a new, clean scene. Needed when clearing the UI for a new project
        so that new items are correctly placed."""
        try:
            self._scene.changed.disconnect(self.scene_changed)
        except RuntimeError:
            logging.error("RuntimeError in disconnecting changed signal")
        self._scene = CustomQGraphicsScene(self, self._toolbox)
        self.setScene(self._scene)
        self._scene.addItem(self.link_drawer)

    def init_scene(self):
        """Resize the scene and connect its `changed` signal. Needed after
        loading a new project.
        """
        self._scene.changed.connect(self.scene_changed)
        self.resize_scene(recenter=True)

    def resize_scene(self, recenter=False):
        """Make the scene at least as big as the viewport."""
        view_rect = self.mapToScene(self.rect()).boundingRect()
        items_rect = self._scene.itemsBoundingRect()
        if recenter:
            view_rect.moveCenter(items_rect.center())
            self.centerOn(items_rect.center())
        self._scene.setSceneRect(view_rect | items_rect)

    def make_link_drawer(self):
        """Make new LinkDrawer and add it scene. Needed when opening a new project."""
        self.link_drawer = LinkDrawer(self._toolbox)
        self.scene().addItem(self.link_drawer)

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

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QGraphicsSceneMouseEvent): Mouse event
        """
        if self.link_drawer and self.link_drawer.drawing:
            self.link_drawer.dst = self.mapToScene(e.pos())
            self.link_drawer.update_geometry()
        super().mouseMoveEvent(e)

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

    def wheelEvent(self, event):
        """Zoom in/out."""
        super().wheelEvent(event)

    def showEvent(self, event):
        """Make the scene at least as big as the viewport."""
        super().showEvent(event)
        self.resize_scene(recenter=True)

    def resizeEvent(self, event):
        """Make the scene at least as big as the viewport."""
        super().resizeEvent(event)
        self.resize_scene(recenter=True)


class GraphQGraphicsView(CustomQGraphicsView):
    """QGraphicsView for the Graph View."""

    item_dropped = Signal("QPoint", "QString", name="item_dropped")

    def __init__(self, parent):
        """Init GraphQGraphicsView."""
        super().__init__(parent=parent)
        self._graph_view_form = None

    def mouseMoveEvent(self, event):
        """Register mouse position to recenter the scene after zoom."""
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        """Zoom in/out."""
        super().wheelEvent(event)

    def mousePressEvent(self, event):
        """Call superclass method."""
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Reestablish scroll hand drag mode."""
        super().mouseReleaseEvent(event)

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


class CustomQGraphicsScene(QGraphicsScene):
    """A scene that handles drag and drop events of DraggableWidget sources."""

    files_dropped_on_dc = Signal("QGraphicsItem", "QVariant", name="files_dropped_on_dc")

    def __init__(self, parent, toolbox):
        """Initialize class."""
        super().__init__(parent)
        self._toolbox = toolbox
        self.item_shadow = None

    def dragLeaveEvent(self, event):
        """Accept event."""
        event.accept()

    def dragEnterEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a DraggableWidget (from Add Item toolbar)."""
        event.accept()
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        """Accept event. Then call the super class method
        only if drag source is not a DraggableWidget (from Add Item toolbar)."""
        event.accept()
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        """Only accept drops when the source is an instance of
        DraggableWidget (from Add Item toolbar).
        Capture text from event's mimedata and show the appropriate 'Add Item form.'
        """
        source = event.source()
        if not isinstance(source, DraggableWidget):
            super().dropEvent(event)
            return
        if not self._toolbox.project():
            self._toolbox.msg.emit("Create or open a project first")
            event.ignore()
            return
        event.acceptProposedAction()
        text = event.mimeData().text()
        pos = event.scenePos()
        pen = QPen(QColor('white'))
        x = pos.x() - 35
        y = pos.y() - 35
        w = 70
        h = 70
        if text == "Data Store":
            brush = QBrush(QColor(0, 255, 255, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._toolbox.show_add_data_store_form(pos.x(), pos.y())
        elif text == "Data Connection":
            brush = QBrush(QColor(0, 0, 255, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_data_master(pen, brush)
            self._toolbox.show_add_data_connection_form(pos.x(), pos.y())
        elif text == "Tool":
            brush = QBrush(QColor(255, 0, 0, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._toolbox.show_add_tool_form(pos.x(), pos.y())
        elif text == "View":
            brush = QBrush(QColor(0, 255, 0, 160))
            self.item_shadow = ItemImage(None, x, y, w, h, '').make_master(pen, brush)
            self._toolbox.show_add_view_form(pos.x(), pos.y())
        self.addItem(self.item_shadow)
