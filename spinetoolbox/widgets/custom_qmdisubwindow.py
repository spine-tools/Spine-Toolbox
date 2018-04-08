"""
A class so that subwindows on mdiArea can send signals
(these signals are originally intended to be retrieved by LinkWidgets)


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QMdiSubWindow
import logging

class CustomQMdiSubWindow(QMdiSubWindow):
    """Add description here"""

    sw_moved_signal = Signal(name="sw_moved_signal")
    sw_showed_signal = Signal(name="sw_showed_signal")
    sw_hid_signal = Signal(name="sw_hid_signal")
    sw_mouse_pressed_or_released_signal = Signal("bool", name="sw_mouse_pressed_or_released_signal")

    def __init__(self, widget, f=Qt.SubWindow):
        super().__init__(flags=f)
        self.setWidget(widget)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def moveEvent(self, event):
        super().moveEvent(event)
        new_pos = event.pos()
        old_pos = event.oldPos()
        moved = new_pos - old_pos
        if moved.manhattanLength() > 0:
            self.sw_moved_signal.emit()

    def showEvent(self, event):
        super().showEvent(event)
        self.sw_showed_signal.emit()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.sw_hid_signal.emit()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.sw_mouse_pressed_or_released_signal.emit(True)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.sw_mouse_pressed_or_released_signal.emit(False)
