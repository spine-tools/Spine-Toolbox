"""
Classes for handling views in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
import inspect
from PySide2.QtCore import Qt, QRect, QPoint
from PySide2.QtWidgets import QGraphicsScene, QGraphicsLineItem
from PySide2.QtGui import QColor, QPen
from config import ITEM_TYPE, MODEL_INDEX


class Link(QGraphicsLineItem):
    """An item that represents a connection between project items."""

    def __init__(self, parent, from_widget, to_widget, index):
        """Initializes item."""
        super().__init__()
        self._parent = parent
        self._from_slot = from_widget
        self._to_slot = to_widget
        self.setZValue(1)   # TODO: is this better than stackBefore?
        self.setData(MODEL_INDEX, index)
        # self.model_index = index
        self.pen_color = QColor(0, 255, 0, 176)
        self.pen_width = 10
        self.from_item = self._from_slot.parent()
        self.to_item = self._to_slot.parent()
        self.setToolTip("<html><p>Connection from <b>{0}</b>'s output "
                        "to <b>{1}</b>'s input<\html>".format(self.from_item.owner(), self.to_item.owner()))
        self.setPen(QPen(self.pen_color, self.pen_width))
        self.update_line()
        self.setData(ITEM_TYPE, "link")
        self.from_rect = None
        self.to_rect = None
        self.from_center = None
        self.to_center = None
        self.from_topleft = None
        self.to_topleft = None
        self.from_bottomright = None
        self.to_bottomright = None
        self.from_offset = None
        self.to_offset = None

    def compute_offsets(self):
        """Compute slot-button offsets within the frame."""
        self.from_offset = self.from_item.frameGeometry().topLeft()
        self.to_offset = self.to_item.frameGeometry().topLeft()

    def update_extreme_points(self):  # TODO: look for a better way
        """Update from and to slot current positions."""
        self.compute_offsets()
        self.from_rect = self._from_slot.geometry()
        self.to_rect = self._to_slot.geometry()
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
            if self._from_slot.underMouse():
                self._from_slot.animateClick()
            elif self._to_slot.underMouse():
                self._to_slot.animateClick()

    def contextMenuEvent(self, e):
        """Show context menu unless mouse is over one of the slot buttons."""
        if self._from_slot.underMouse() or self._to_slot.underMouse():
            e.ignore()
        else:
            self._parent.show_link_context_menu(e.screenPos(), self.data(MODEL_INDEX))

    def paint(self, painter, option, widget):
        """Paint rectangles over the slot-buttons simulating connection anchors."""
        # only paint if two items are visible
        if self.from_item.isVisible() and self.to_item.isVisible():
            self.update_line()
            from_geom = QRect(self.from_topleft, self.from_bottomright)
            to_geom = QRect(self.to_topleft, self.to_bottomright)
            # check whether the active sw overlaps rects and update color accordingly
            sw = self._parent.ui.graphicsView.activeSubWindow()
            if not sw:
                super().paint(painter, option, widget)
                return
            else:
                active_item = sw.widget()
                sw_geom = sw.windowFrameGeometry()
                from_covered = active_item != self.from_item and sw_geom.intersects(from_geom)
                to_covered = active_item != self.to_item and sw_geom.intersects(to_geom)
            if from_covered:
                from_rect_color = QColor(128, 128, 128, 128)
            else:
                from_rect_color = self.pen_color
            if to_covered:
                to_rect_color = QColor(128, 128, 128, 64)
            else:
                to_rect_color = self.pen_color
            painter.fillRect(from_geom, from_rect_color)
            painter.fillRect(to_geom, to_rect_color)
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
            moved = self.fr - self.to
            if moved.manhattanLength() > 3:
                self.setLine(self.fr.x(), self.fr.y(), self.to.x(), self.to.y())

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
                    sw = item.widget()
                    sw_offset = sw.frameGeometry().topLeft()
                    pos -= sw_offset
                    candidate_button = sw.childAt(pos)
                    if hasattr(candidate_button, 'is_inputslot'):
                        candidate_button.animateClick()
                        return
            self.drawing = False
            self._qmainwindow.msg_error.emit("Unable to make connection."
                                             " Try landing the connection onto a slot button.")

    def paint(self, painter, option, widget):
        """Draw small rectangles on begin and end positions."""
        p = QPoint(self.pen_width, self.pen_width)
        painter.fillRect(QRect(self.fr-p, self.fr+p), self.pen_color)
        painter.fillRect(QRect(self.to-p, self.to+p), self.pen_color)
        super().paint(painter, option, widget)
