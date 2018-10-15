"""
Classes for handling views in PySide2's model/view framework.
Note: These are Spine Toolbox internal data views.


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
from PySide2.QtCore import Qt, QObject, Signal, Slot, QModelIndex, QPoint, QRect, QPointF, QLineF
from PySide2.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsItem
from PySide2.QtGui import QColor, QPen, QBrush, QPainter, QTransform, QPolygonF
from math import atan2, sin, cos, pi #arrow head

# QGraphicsItem arbitrary properties
ITEM_TYPE = 0


class LinksView(QGraphicsView):
    """Pseudo-QMdiArea implemented as QGraphicsView.
    It 'views' the project_item_model as well as the connections_model.
    The project_item_model is viewed as pseudo-QMdiAreaSubwindows.
    The connections_model is viewed as objects of class Link (see below)
    drawn between the pseudo-QMdiAreaSubwindows

    Attributes:
        parent(ToolboxUI): Parent of this view
    """
    subWindowActivated = Signal("QGraphicsProxyWidget", name="subWindowActivated")

    def __init__(self, parent):
        """Initialize the view"""
        self._scene = QGraphicsScene()
        super().__init__(self._scene)
        self._parent = parent
        self._connection_model = None
        self._project_item_model = None
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.link_drawer = LinkDrawer(parent)
        self.scene().addItem(self.link_drawer)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.max_sw_width = 0
        self.max_sw_height = 0
        self.scene().changed.connect(self.scene_changed)
        self.active_subwindow = None

    @Slot(name='scene_changed')
    def scene_changed(self):
        """Check if active subwindow has changed and emit signal accordingly"""
        #logging.debug("scene changed")
        current_active_sw = self.scene().activeWindow()
        if current_active_sw and current_active_sw.data(ITEM_TYPE) == "subwindow":
            if current_active_sw != self.active_subwindow:
                self.active_subwindow = current_active_sw
                self.subWindowActivated.emit(self.active_subwindow)

    def setProjectItemModel(self, model):
        """Set project item model and connect signals"""
        self._project_item_model = model
        self._project_item_model.rowsInserted.connect(self.projectRowsInserted)
        self._project_item_model.rowsAboutToBeRemoved.connect(self.projectRowsRemoved)

    def setConnectionModel(self, model):
        """Set connection model and connect signals"""
        self._connection_model = model
        self._connection_model.dataChanged.connect(self.connectionDataChanged)
        self._connection_model.rowsRemoved.connect(self.connectionsRemoved)
        #self._connection_model.columnsRemoved.connect(self.connectionsRemoved)

    def project_item_model(self):
        """return project item model"""
        return self._project_item_model

    def connection_model(self):
        """return connection model"""
        return self._connection_model

    def subWindowList(self):
        """Return list of subwindows (replicate QMdiArea.subWindowList)"""
        return [x for x in self.scene().items() if x.data(ITEM_TYPE) == 'subwindow']

    def setActiveSubWindow(self, item):
        """replicate QMdiArea.setActiveWindow"""
        self.scene().setActiveWindow(item)

    def activeSubWindow(self):
        """replicate QMdiArea.activeSubWindow"""
        return self.scene().activeWindow()

    def removeSubWindow(self, sw): #this method will be obsolete, since it doesn't coordinate with the model
        """remove subwindow and any attached links from the scene"""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if sw.widget() == item.from_widget or sw.widget() == item.to_widget:
                    self.scene().removeItem(item)
        self.scene().removeItem(sw)

    def find_link(self, from_widget, to_widget):
        """Find link in scene, by model index"""
        for item in self.scene().items():
            if item.data(ITEM_TYPE) == "link":
                if item.from_widget == from_widget and item.to_widget == to_widget:
                    return item
        return None

    @Slot("QModelIndex", "int", "int", name='projectRowsInserted')
    def projectRowsInserted(self, item, first, last):
        """update view when model changes"""
        #logging.debug("project rows inserted")
        for ind in range(first, last+1):
            widget = item.child(ind, 0).data(role=Qt.UserRole).get_widget()
            flags = Qt.Window
            proxy = self.scene().addWidget(widget, flags)
            proxy.setData(ITEM_TYPE, "subwindow")
            #figure out the best position on the view
            sw_geom = proxy.windowFrameGeometry()
            self.max_sw_width = max(self.max_sw_width, sw_geom.width())
            self.max_sw_height = max(self.max_sw_height, sw_geom.height())
            position = QPoint(item.row() * self.max_sw_width, ind * self.max_sw_height)
            proxy.setPos(position)
            proxy.widget().activateWindow()

    @Slot("QModelIndex", "int", "int", name='projectRowsRemoved')
    def projectRowsRemoved(self, item, first, last):
        """update view when model changes"""
        #logging.debug("project rows removed")
        for ind in range(first, last+1):
            sw = item.child(ind, 0).data(role=Qt.UserRole).get_widget().parent()
            self.scene().removeItem(sw)

    @Slot("QModelIndex", "QModelIndex", name='connectionDataChanged')
    def connectionDataChanged(self, top_left, bottom_right, roles=None):
        """update view when model changes"""
        logging.debug("conn data changed")
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom+1):
            for column in range(left, right+1):
                index = self.connection_model().index(row, column)
                data = self.connection_model().data(index, Qt.DisplayRole)
                from_name = self.connection_model().headerData(row, Qt.Vertical, Qt.DisplayRole)
                to_name = self.connection_model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
                sub_windows = self.subWindowList()
                sw_owners = list(sw.widget().owner() for sw in sub_windows)
                fr = sw_owners.index(from_name)
                to = sw_owners.index(to_name)
                from_widget = sub_windows[fr].widget()
                to_widget = sub_windows[to].widget()
                if data:    #connection made, add link widget
                    link = Link(self._parent, from_widget, to_widget)
                    self.scene().addItem(link)
                else:   #connection destroyed, remove link widget
                    link = self.find_link(from_widget, to_widget)
                    if link is not None:
                        self.scene().removeItem(link)

    @Slot("QModelIndex", "int", "int", name='connectionsRemoved')
    def connectionsRemoved(self, index, first, last):
        """update view when model changes"""
        logging.debug("conns. removed")
        for i in range(first,last+1):
            removed_name = self.connection_model().headerData(i, orientation=Qt.Horizontal)
            for item in self.scene().items():
                if item.data(ITEM_TYPE) == "link":
                    from_name = item.from_widget.owner()
                    to_name = item.to_widget.owner()
                    if removed_name == from_name or removed_name == to_name:
                        self.scene().removeItem(item)


    def draw_links(self, button):
        """Draw links when connector button is clicked"""
        if not self.link_drawer.drawing:
            #start drawing and remember connector
            self.link_drawer.drawing = True
            self.link_drawer.start_drawing_at(button)
            self.from_widget = button.parent().owner()
        else:
            #stop drawing and make connection
            self.link_drawer.drawing = False
            self.to_widget = button.parent().owner()
            # create connection
            row = self.connection_model().header.index(self.from_widget)
            column = self.connection_model().header.index(self.to_widget)
            index = self.connection_model().createIndex(row, column)
            if not self.connection_model().data(index, Qt.DisplayRole):
                self.connection_model().setData(index, "value", Qt.EditRole)  # value not used
                self._parent.msg.emit("<b>{}</b>'s output is now connected to"\
                              " <b>{}</b>'s input.".format(self.from_widget, self.to_widget))
            else:
                self._parent.msg.emit("<b>{}</b>'s output is already connected to"\
                          " <b>{}</b>'s input.".format(self.from_widget, self.to_widget))

class Link(QGraphicsLineItem):
    """An item that represents a connection in mdiArea"""

    def __init__(self, parent, from_widget, to_widget):
        """Initializes item.

        Args:
            parent (ToolboxUI): QMainWindow instance
            from_button (QToolButton): the button where this link origins from
            to_button (QToolButton): the destination button
            index (QModelIndex): the corresponding index in the model
        """
        super().__init__()
        self._parent = parent
        self.setZValue(1)   #TODO: is this better than stackBefore?
        self.normal_color = QColor(0,255,0,176)
        self.covered_color = QColor(128,128,128,128)
        self.pen_width = 10
        self.arrow_size = 20
        self.arrow_head = QPolygonF()
        self.from_widget = from_widget
        self.to_widget = to_widget
        self.from_connector = self.from_widget.ui.toolButton_connector
        self.to_connector = self.to_widget.ui.toolButton_connector
        self.from_rect = self.from_connector.geometry()
        self.to_rect = self.to_connector.geometry()
        self.setToolTip("<html><p>Connection from <b>{}</b>'s ouput to <b>{}</b>'s input<\html>"\
            .format(self.from_widget.owner(), self.to_widget.owner()))
        self.setPen(QPen(self.normal_color, self.pen_width))
        self.update_line()
        self.setData(ITEM_TYPE, "link")

    def compute_offsets(self):
        """compute connector-button offsets within the frame"""
        self.from_offset = self.from_widget.frameGeometry().topLeft()
        self.to_offset = self.to_widget.frameGeometry().topLeft()

    def update_extreme_points(self):    #TODO: look for a better way
        """update from and to connector current positions"""
        self.compute_offsets()
        self.from_center = self.from_rect.center() + self.from_offset
        self.to_center = self.to_rect.center() + self.to_offset
        self.from_topleft = self.from_rect.topLeft() + self.from_offset
        self.to_topleft = self.to_rect.topLeft() + self.to_offset
        self.from_bottomright = self.from_rect.bottomRight() + self.from_offset
        self.to_bottomright = self.to_rect.bottomRight() + self.to_offset

    def update_line(self):
        """Update extreme points and line accordingly"""
        #logging.debug("update_line")
        self.update_extreme_points()
        self.setLine(self.from_center.x(), self.from_center.y(), self.to_center.x(), self.to_center.y())

    def mousePressEvent(self, e):
        """Trigger connector button if it is underneath"""
        if e.button() != Qt.LeftButton:
            e.ignore()
        else:
            if self.from_connector.underMouse():
                self.from_connector.animateClick()
            elif self.to_connector.underMouse():
                self.to_connector.animateClick()

    def contextMenuEvent(self, e):
        """show contex menu unless mouse is over one of the connector buttons"""
        if self.from_connector.underMouse() or self.to_connector.underMouse():
            e.ignore()
        else:
            self._parent.show_link_context_menu(e.screenPos(), self.from_widget, self.to_widget)

    def paint(self, painter, option, widget):
        """Paint ellipse and arrow at from and to positions, respectively
        Obscure item if connectors overlap any window"""
        #only paint if two items are visible
        if self.from_widget.isVisible() and self.to_widget.isVisible():
            self.update_line()
            from_geom = QRect(self.from_topleft, self.from_bottomright)
            to_geom = QRect(self.to_topleft, self.to_bottomright)
            #check whether the active sw overlaps rects and update color accordingly
            from_covered = False
            to_covered = False
            sw = self._parent.ui.mdiArea.activeSubWindow()
            if sw:
                active_widget = sw.widget()
                sw_geom = sw.windowFrameGeometry()
                from_covered = active_widget != self.from_widget and sw_geom.intersects(from_geom)
                to_covered = active_widget != self.to_widget and sw_geom.intersects(to_geom)
            if from_covered or to_covered:
                color = self.covered_color
            else:
                color = self.normal_color
            #arrow head
            angle = atan2(-self.line().dy(), self.line().dx())
            arrow_p0 = self.line().p2()
            shorter_line = QLineF(self.line())
            shorter_line.setLength(shorter_line.length() - self.arrow_size)
            self.setLine(shorter_line)
            arrow_p1 = arrow_p0 - QPointF(sin(angle + pi / 3) * self.arrow_size,
                                    cos(angle + pi / 3) * self.arrow_size);
            arrow_p2 = arrow_p0 - QPointF(sin(angle + pi - pi / 3) * self.arrow_size,
                                    cos(angle + pi - pi / 3) * self.arrow_size);
            self.arrow_head.clear()
            self.arrow_head.append(arrow_p0)
            self.arrow_head.append(arrow_p1)
            self.arrow_head.append(arrow_p2)
            brush = QBrush(color, Qt.SolidPattern)
            painter.setBrush(brush)
            painter.drawEllipse(self.from_center, self.pen_width, self.pen_width)
            painter.drawPolygon(self.arrow_head)
            self.setPen(QPen(color, self.pen_width))
            super().paint(painter, option, widget)

class LinkDrawer(QGraphicsLineItem):
    """An item that allows one to draw links between connector buttons in mdiArea
    Attributes:
        parent (ToolboxUI): QMainWindow instance
    """

    def __init__(self, parent):
        """Initializes item.

        Params:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__()
        self._parent = parent
        self.fr = None
        self.drawing = False
        # set pen
        self.pen_color = QColor(255,0,255)
        self.pen_width = 6
        self.arrow_size = 12
        self.arrow_head = QPolygonF()
        self.setPen(QPen(self.pen_color, self.pen_width))
        self.setZValue(2)   #TODO: is this better than stackBefore?
        self.hide()
        self.setData(ITEM_TYPE, "link-drawer")

    def start_drawing_at(self, button):
        """start drawing"""
        button_pos = button.geometry().center()
        sw_offset = button.parent().frameGeometry().topLeft()
        self.fr = button_pos + sw_offset
        self.to = self.fr
        self.setLine(self.fr.x(), self.fr.y(), self.fr.x(), self.fr.y())
        self.show()
        self.grabMouse()

    def mouseMoveEvent(self, e):
        """Update line end position.

        Args:
            e (QMouseEvent): Mouse event
        """
        if self.fr is not None:
            self.to = e.pos().toPoint()
            self.update()

    def mousePressEvent(self, e):
        """If link lands on connector button, trigger click

        Args:
            e (QMouseEvent): Mouse event
        """
        self.ungrabMouse()
        self.hide()
        if e.button() != Qt.LeftButton:
            self.drawing = False
        else:
            pos = e.pos().toPoint()
            view_pos = self._parent.ui.mdiArea.mapFromScene(pos)
            for item in self._parent.ui.mdiArea.items(view_pos):
                if item.data(ITEM_TYPE) == "subwindow":
                    widget = item.widget()
                    widget_offset = widget.frameGeometry().topLeft()
                    pos -= widget_offset
                    candidate_button = widget.childAt(pos)
                    if hasattr(candidate_button, 'is_connector'):
                        candidate_button.animateClick()
                        return
            self.drawing = False
            self._parent.msg_error.emit("Unable to make connection."
                                        " Try landing the link onto a connector button.")


    def paint(self, painter, option, widget):
        """Draw small rects on begin and end positions.

        Args:
            e (QPaintEvent): Paint event
        """
        #arrow head
        self.setLine(self.fr.x(), self.fr.y(), self.to.x(), self.to.y())
        angle = atan2(-self.line().dy(), self.line().dx())
        arrow_p0 = self.line().p2()
        shorter_line = QLineF(self.line())
        shorter_line.setLength(shorter_line.length() - self.arrow_size)
        self.setLine(shorter_line)
        arrow_p1 = arrow_p0 - QPointF(sin(angle + pi / 3) * self.arrow_size,
                                cos(angle + pi / 3) * self.arrow_size);
        arrow_p2 = arrow_p0 - QPointF(sin(angle + pi - pi / 3) * self.arrow_size,
                                cos(angle + pi - pi / 3) * self.arrow_size);
        self.arrow_head.clear()
        self.arrow_head.append(arrow_p0)
        self.arrow_head.append(arrow_p1)
        self.arrow_head.append(arrow_p2)
        p = QPoint(self.pen_width, self.pen_width)
        brush = QBrush(self.pen_color, Qt.SolidPattern)
        painter.setBrush(brush)
        painter.drawEllipse(self.fr, self.pen_width, self.pen_width)
        painter.drawPolygon(self.arrow_head)
        super().paint(painter, option, widget)
