"""
Classes for handling link widgets in mdiArea


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
from PySide2.QtWidgets import QWidget, QSizePolicy
from PySide2.QtCore import Qt, QPoint, QSize, Signal, Slot, QRect, QFile, QIODevice
from PySide2.QtGui import QPainter, QColor, QPen, QPixmap, QRegion

class LinkWidget(QWidget):
    """A widget that represents a connection in mdiArea"""

    def __init__(self, parent, from_widget, to_widget):
        """Initializes widget.

        Args:
            parent (ToolboxUI): QMainWindow instance
            from_slot (QToolButton): the button where this link origins from
            to_slot (QToolButton): the destination button
        """
        super().__init__(parent.ui.mdiArea)
        self._from_slot = from_widget
        self._to_slot = to_widget
        self.fr = QPoint(0,0)   #TODO: check if this is needed
        self.to = QPoint(0,0)   #TODO: check if this is needed
        # set pen (TODO: maybe get pen as argument instead?)
        pen_color = QColor(0,255,0,160)
        self.base_width = 5
        self._pen = QPen(pen_color, self.base_width)
        self.resize(self.parent().size())
        self.update_mask()
        self.show()
        # make it transparent for now
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    @Slot(name="custom_repaint")
    def custom_repaint(self):
        self.resize(self.parent().size())
        self.update()

    @Slot(name="custom_show")
    def custom_show(self):
        self.update()

    @Slot(name="custom_hide")
    def custom_hide(self):
        self.update()

    @Slot(name="update_mask")
    def update_mask(self):
        # create mask for mouse events
        self.update_extreme_points()
        pixmap = QPixmap(self.size())
        painter = QPainter(pixmap)
        painter.setPen(QPen(Qt.white, self.base_width))
        painter.drawLine(self.fr, self.to)
        bitmap = pixmap.createMaskFromColor(Qt.white, Qt.MaskOutColor)
        self.setMask(bitmap)
        painter.end()

    @Slot(name="clear_mask")
    def clear_mask(self):
        self.clearMask()

    def paintEvent(self, event):
        """Draw link between slot buttons.

        Args:
            e (QPaintEvent): Paint event
        """
        # Only paint if two subwindows are visible
        visible = self._from_slot.parent().parent().isVisible()
        visible &= self._to_slot.parent().parent().isVisible()

        if visible:
            self.update_extreme_points()
            painter = QPainter(self)
            painter.setPen(self._pen)
            painter.drawEllipse(self.fr, self.base_width, self.base_width)
            painter.drawEllipse(self.to, self.base_width, self.base_width)
            painter.drawLine(self.fr, self.to)

    def mousePressEvent(self, e):
        """.

        Args:
            e (QMouseEvent): Mouse event
        """
        logging.debug("click")

    def update_extreme_points(self):
        """update from and to slot current positions"""
        self.fr = self._from_slot.geometry().center()
        form_offset = self._from_slot.parent().frameGeometry().topLeft()
        subwindow_offset = self._from_slot.parent().parent().pos()
        self.fr += form_offset + subwindow_offset

        self.to = self._to_slot.geometry().center()
        form_offset = self._to_slot.parent().frameGeometry().topLeft()
        subwindow_offset = self._to_slot.parent().parent().pos()
        self.to += form_offset + subwindow_offset


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
        super().__init__(parent.ui.mdiArea)
        self._parent = parent
        self.setMouseTracking(True)
        self._initialPos = None
        self.drawing = False
        self.resize(0,0)
        # set pen
        pen_color = QColor(255,0,255)
        self.base_width = 5
        self._pen = QPen(pen_color, self.base_width)
        # Ensure this window gets garbage-collected when closed
        self.setAttribute(Qt.WA_DeleteOnClose)

    def set_initial_position(self, button):
        # set initial position
        self.resize(self.parent().size())
        self.show()
        button_pos = button.geometry().center() # Within the item form
        form_offset = button.parent().frameGeometry().topLeft() # from subwindow
        subwindow_offset = button.parent().parent().pos()   # from mdiArea
        self._initialPos = button_pos + form_offset + subwindow_offset
        self._mouseMovePos = self._initialPos


    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        if event:
            event.accept()

    def mousePressEvent(self, e):
        """If link lands on slot button, trigger click

        Args:
            e (QMouseEvent): Mouse event
        """
        self.hide()
        if e.button() != Qt.LeftButton:
            self.drawing = False
        else:
            candidate_button = self.parent().childAt(e.pos())
            if hasattr(candidate_button, 'is_inputslot'):
                candidate_button.animateClick()
            else:
                self._parent.msg_error.emit("Unable to make connection."
                                            " Try landing the connection onto a slot button.")
                self.drawing = False

    def mouseMoveEvent(self, e):
        """Save current mouse position.

        Args:
            e (QMouseEvent): Mouse event
        """
        self._mouseMovePos = e.pos()
        self.update()

    def paintEvent(self, e):
        """Draw arrow from origin slot button to mouse position.

        Args:
            e (QPaintEvent): Paint event
        """
        if self._initialPos is not None:
            fr = self._initialPos
            painter = QPainter(self)
            #painter.fillRect(self.contentsRect(), QColor(255, 128, 128, 32))
            painter.setPen(self._pen)
            painter.drawEllipse(fr, self.base_width, self.base_width)
            moved = self._mouseMovePos - self._initialPos
            if moved.manhattanLength() > 3:
                to = self._mouseMovePos
                painter.drawLine(fr, to)
                painter.drawEllipse(to, self.base_width, self.base_width)
