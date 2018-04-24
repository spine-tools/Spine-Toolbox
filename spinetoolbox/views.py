"""
Classes for handling views in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
import inspect
from PySide2.QtCore import Qt, Slot, QRect, QPoint, QPointF, QLineF
from PySide2.QtWidgets import QGraphicsScene, QGraphicsLineItem
from PySide2.QtGui import QColor, QPen, QPolygonF, QBrush
from math import atan2, sin, cos, pi #arrow head
from config import ITEM_TYPE


class Link(QGraphicsLineItem):
    """An item that represents a connection between project items."""

    def __init__(self, parent, from_widget, to_widget):
        """Initializes item."""
        super().__init__()
        self._parent = parent
        self.from_widget = from_widget
        self.to_widget = to_widget
        self.from_connector = self.from_widget.ui.toolButton_connector
        self.to_connector = self.to_widget.ui.toolButton_connector
        self.setZValue(1)   # TODO: is this better than stackBefore?
        self.normal_color = QColor(0, 255, 0, 176)
        self.covered_color = QColor(128, 128, 128, 128)
        self.pen_width = 10
        self.arrow_size = 20
        self.setToolTip("<html><p>Connection from <b>{0}</b>'s output "
                        "to <b>{1}</b>'s input<\html>".format(self.from_widget.owner(), self.to_widget.owner()))
        self.setPen(QPen(self.normal_color, self.pen_width))
        self.from_rect = self.from_connector.geometry()
        self.to_rect = self.to_connector.geometry()
        self.arrow_head = QPolygonF()
        self.update_line()
        self.setData(ITEM_TYPE, "link")
        self.from_center = None
        self.to_center = None
        self.from_topleft = None
        self.to_topleft = None
        self.from_bottomright = None
        self.to_bottomright = None
        self.from_offset = None
        self.to_offset = None


    @Slot(name="update")
    def update(self):
        logging.debug("update link")
        super().update()

    def compute_offsets(self):
        """Compute connector-button offsets within the frame."""
        self.from_offset = self.from_widget.frameGeometry().topLeft()
        self.to_offset = self.to_widget.frameGeometry().topLeft()

    def update_extreme_points(self):  # TODO: look for a better way
        """Update from and to connector current positions."""
        self.compute_offsets()
        self.from_center = self.from_rect.center() + self.from_offset
        self.to_center = self.to_rect.center() + self.to_offset
        self.from_topleft = self.from_rect.topLeft() + self.from_offset
        self.to_topleft = self.to_rect.topLeft() + self.to_offset
        self.from_bottomright = self.from_rect.bottomRight() + self.from_offset
        self.to_bottomright = self.to_rect.bottomRight() + self.to_offset

    def update_line(self):
        """Update extreme points and line accordingly."""
        # logging.debug("update_line")
        self.update_extreme_points()
        self.setLine(self.from_center.x(), self.from_center.y(), self.to_center.x(), self.to_center.y())

    def mousePressEvent(self, e):
        """Trigger slot button if it is underneath."""
        if e.button() != Qt.LeftButton:
            e.ignore()
        else:
            if self.from_connector.underMouse():
                self.from_connector.animateClick()
            elif self.to_connector.underMouse():
                self.to_connector.animateClick()

    def contextMenuEvent(self, e):
        """Show context menu unless mouse is over one of the slot buttons."""
        if self.from_connector.underMouse() or self.to_connector.underMouse():
            e.ignore()
        else:
            self._parent.show_link_context_menu(e.screenPos(), self.from_widget, self.to_widget)

    def paint(self, painter, option, widget):
        """Paint ellipse and arrow at from and to positions, respectively
        Obscure item if connectors overlap any window"""
        # only paint if two items are visible
        if self.from_widget.isVisible() and self.to_widget.isVisible():
            self.update_line()
            from_geom = QRect(self.from_topleft, self.from_bottomright)
            to_geom = QRect(self.to_topleft, self.to_bottomright)
            # check whether the active sw overlaps rects and update color accordingly
            sw = self._parent.ui.graphicsView.activeSubWindow()
            if not sw:
                # super().paint(painter, option, widget)
                # return
                # don't return so ellipse and arrowheads stay when no window is selected
                from_covered = False
                to_covered = False
            else:
                active_item = sw.widget()
                sw_geom = sw.windowFrameGeometry()
                from_covered = active_item != self.from_widget and sw_geom.intersects(from_geom)
                to_covered = active_item != self.to_widget and sw_geom.intersects(to_geom)
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
    """An item that allows one to draw links between slot buttons in QGraphicsView.

    Attributes:
        parent (QGraphicsScene): QGraphicsScene instance
        qmainwindow (ToolboxUI): QMainWindow instance
    """
    def __init__(self, parent, qmainwindow):
        """Initializes instance."""
        super().__init__()
        self._parent = parent  # scene
        self._qmainwindow = qmainwindow
        self.fr = None
        self.to = None
        self.drawing = False
        # set pen
        self.pen_color = QColor(255, 0, 255)
        self.pen_width = 6
        self.arrow_size = 12
        self.arrow_head = QPolygonF()
        self.setPen(QPen(self.pen_color, self.pen_width))
        self.setZValue(2)  # TODO: is this better than stackBefore?
        self.hide()
        self.setData(ITEM_TYPE, "link-drawer")

    def start_drawing_at(self, button):
        """Start drawing."""
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
        """If link lands on slot button, trigger click.

        Args:
            e (QMouseEvent): Mouse event
        """
        self.ungrabMouse()
        self.hide()
        if e.button() != Qt.LeftButton:
            self.drawing = False
        else:
            pos = e.pos().toPoint()
            view_pos = self._qmainwindow.ui.graphicsView.mapFromScene(pos)
            for item in self._qmainwindow.ui.graphicsView.items(view_pos):
                if item.data(ITEM_TYPE) == "subwindow":
                    widget = item.widget()
                    widget_offset = widget.frameGeometry().topLeft()
                    pos -= widget_offset
                    candidate_button = widget.childAt(pos)
                    if hasattr(candidate_button, 'is_connector'):
                        candidate_button.animateClick()
                        return
            self.drawing = False
            self._qmainwindow.msg_error.emit("Unable to make connection."
                                             " Try landing the connection onto a connector button.")

    def paint(self, painter, option, widget):
        """Draw ellipse at begin position and arrowhead at end position."""
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
