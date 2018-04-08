"""
Classes for handling link widgets in mdiArea


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
import inspect
from PySide2.QtWidgets import QWidget, QSizePolicy, QWidgetItem, QLayout
from PySide2.QtCore import Qt, QPoint, QSize, Signal, Slot, QRect, QEvent
from PySide2.QtGui import QPainter, QColor, QPen, QRegion, QBitmap

class LinkWidget(QWidget):
    """A widget that represents a connection in mdiArea"""

    customContextMenuRequested = Signal("QPoint", "QModelIndex", name="customContextMenuRequested")

    def __init__(self, parent, from_widget, to_widget, index):
        """Initializes widget.

        Args:
            parent (ToolboxUI): QMainWindow instance
            from_slot (QToolButton): the button where this link origins from
            to_slot (QToolButton): the destination button
        """
        super().__init__()
        self._parent = parent
        self._from_slot = from_widget
        self._to_slot = to_widget
        self.is_link = True
        self.model_index = index
        self.pen_color = QColor(0,255,0,160)
        self.pen_width = 10
        self.update_mask_on_move = True
        self.from_item = self._from_slot.parent()
        self.from_subwindow = self.from_item.parent()
        self.to_item = self._to_slot.parent()
        self.to_subwindow = self.to_item.parent()
        self.setToolTip("<html><p>Connection link from {}'s ouput to {}'s input<\html>"\
            .format(self.from_item.owner(), self.to_item.owner()))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_DeleteOnClose)

    #TODO: this below was intended to improve performance, however it bugs
    #when the mouse is released while the subwindow is not visible
    #(since the subwindow does not send the signal to restore mask)
    #May be improved by catching hide event on the subwindow (or st)
    #and stop blocking mask updates at that point
    #@Slot("bool", "set_update_mask")
    #def set_update_mask_on_move(self, value):
    #    self.update_mask_on_move = value
    #    if not value:
    #        self.clear_mask()

    def compute_offsets(self):
        self.from_offset = self.from_item.frameGeometry().topLeft()
        self.from_offset += self.from_subwindow.pos()
        self.to_offset = self.to_item.frameGeometry().topLeft()
        self.to_offset += self.to_subwindow.pos()

    def update_extreme_points(self):    #TODO: look for a better way
        """update from and to slot current positions"""
        self.compute_offsets()
        self.from_center = self.from_rect.center() + self.from_offset
        self.to_center = self.to_rect.center() + self.to_offset
        self.from_topleft = self.from_rect.topLeft() + self.from_offset
        self.to_topleft = self.to_rect.topLeft() + self.to_offset
        self.from_bottomright = self.from_rect.bottomRight() + self.from_offset
        self.to_bottomright = self.to_rect.bottomRight() + self.to_offset

    def update_mask(self):
        """mask everything but the link"""
        #logging.debug("update mask")
        bitmap = QBitmap(self.size())
        bitmap.clear()
        painter = QPainter(bitmap)
        painter.setPen(QPen(Qt.color1, self.pen_width))
        painter.drawLine(self.from_center, self.to_center)
        painter.drawRect(QRect(self.from_topleft, self.from_bottomright))
        painter.drawRect(QRect(self.to_topleft, self.to_bottomright))
        painter.end()
        self.setMask(bitmap)

    def mask_fully(self):
        """fully mask the widget"""
        #logging.debug("mask all")
        region = QRegion(0,0,1,1)   #won't work with empty region...
        self.setMask(region)

    def clear_mask(self):
        if not self.mask().isEmpty():
            #logging.debug("clear mask")
            self.clearMask()
        return

    def paintEvent(self, event):
        """Draw link between slot buttons.

        Args:
            e (QPaintEvent): Paint event
        """
        # Only paint if two subwindows are visible
        if self.from_subwindow.isVisible() and self.to_subwindow.isVisible():
            self.from_rect = self._from_slot.geometry()
            self.to_rect = self._to_slot.geometry()
            self.update_extreme_points()
            if self.update_mask_on_move:
                self.update_mask()
            painter = QPainter(self)
            painter.setPen(QPen(self.pen_color, self.pen_width))
            painter.drawLine(self.from_center, self.to_center)
            painter.setPen(QPen(self.pen_color, .5*self.pen_width))
            painter.fillRect(QRect(self.from_topleft, self.from_bottomright), self.pen_color)
            painter.fillRect(QRect(self.to_topleft, self.to_bottomright), self.pen_color)
        else:
            self.mask_fully()

    def contextMenuEvent(self, e):
        self.customContextMenuRequested.emit(e.globalPos(), self.model_index)


class DrawLinkWidget(QWidget):
    """A widget to draw links between slot buttons in mdiArea
    Attributes:
        parent (ToolboxUI): QMainWindow instance
    """

    def __init__(self, parent):
        """Initializes widget.

        Params:
            parent (ToolboxUI): QMainWindow instance
        """
        super().__init__()
        self._parent = parent
        self.setMouseTracking(True)
        self._initialPos = None
        self.drawing = False
        #don't catch the mouse until one slot button is clicked
        self.hide()
        # set pen
        self.pen_color = QColor(255,0,255)
        self.pen_width = 6
        self.is_link = False #pass on this widget when looking for links
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def start_drawing_at(self, button):
        """start drawing"""
        self.show()
        self.raise_()
        button_pos = button.geometry().center() # Within the item form
        form_offset = button.parent().frameGeometry().topLeft() # from subwindow
        subwindow_offset = button.parent().parent().pos()   # from mdiArea
        self._initialPos = button_pos + form_offset + subwindow_offset
        self._mouseMovePos = self._initialPos

    def mousePressEvent(self, e):
        """If link lands on slot button, trigger click

        Args:
            e (QMouseEvent): Mouse event
        """
        self.hide()
        if e.button() != Qt.LeftButton:
            self.drawing = False
        else:
            candidate_button = self._parent.ui.mdiArea.childAt(e.pos())
            if hasattr(candidate_button, 'is_inputslot'):
                candidate_button.animateClick()
            else:
                self.drawing = False
                self._parent.msg_error.emit("Unable to make connection."
                                            " Try landing the connection onto a slot button.")


    def mouseMoveEvent(self, e):
        """Save current mouse position.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mouseMovePos = e.pos()
        self.update()

    def paintEvent(self, e):
        """Draw link from origin slot button to mouse position.

        Args:
            e (QPaintEvent): Paint event
        """
        if self._initialPos is not None:
            fr = self._initialPos
            painter = QPainter(self)
            painter.setPen(QPen(self.pen_color, self.pen_width))
            p = QPoint(self.pen_width, self.pen_width)
            painter.fillRect(QRect(fr-p, fr+p), self.pen_color)
            moved = self._mouseMovePos - self._initialPos
            if moved.manhattanLength() > 3:
                to = self._mouseMovePos
                painter.drawLine(fr, to)
                painter.fillRect(QRect(to-p, to+p), self.pen_color)


class LinkLayout(QLayout):
    """A layout for arranging LinkWidgets in a LinkView

    Attributes:
        parent(QMdiArea): Parent of this layout, where it applies on
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.items = list()

    def count(self):
        return len(self.items)

    def itemAt(self, ind):  #TODO: handle index out of range error
        logging.debug("Item at called by {}, index {}".format(inspect.stack()[1][3], ind))
        if 0 <= ind < self.count():
            return self.items[ind]
        else:
            logging.debug("Item at: Got index {}, len {}".format(ind, self.count()))
            return 0

    def takeAt(self, ind):
        logging.debug("take at index {}, current len {}".format(ind, self.count()))
        if 0 <= ind < self.count():
            item = self.items.pop(ind)
            self.removeItem(item)
            return item
        else:
            return 0

    def addItem(self, item):
        logging.debug("add item {}".format(item))
        self.items.append(item)

    def addWidget(self, widget):
        logging.debug("add widget {}".format(widget))
        self.addChildWidget(widget)
        self.addItem(QWidgetItem(widget))

    def setGeometry(self, rect):
        logging.debug("setting geom {}".format(rect))
        super().setGeometry(rect)
        if len(self.items) == 0:
            return
        for ind in range(self.count()):
            item = self.itemAt(ind)
            if item != 0:
                item.setGeometry(rect)

    def sizeHint(self):
        return self.parent().sizeHint()

    def minimumSize(self):
        return self.parent().minimumSize()
