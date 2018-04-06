"""
A class so that subwindows on mdiArea can send signals
(These signals are intended to be retrieved by LinkWidgets)


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QMdiSubWindow
import logging

class CustomQMdiSubWindow(QMdiSubWindow):

    sw_moved_signal = Signal(name="sw_moved_signal")
    sw_showed_signal = Signal(name="sw_showed_signal")
    sw_hid_signal = Signal(name="sw_hid_signal")
    sw_mouse_released_signal = Signal(name="sw_mouse_released_signal")
    sw_mouse_pressed_signal = Signal(name="sw_mouse_pressed_signal")

    def __init__(self, parent, widget):
        super().__init__(parent)
        self.setWidget(widget)
        self.setAttribute(Qt.WA_DeleteOnClose)

    def moveEvent(self, event):
        self.sw_moved_signal.emit()

    def showEvent(self, event):
        self.sw_showed_signal.emit()

    def hideEvent(self, event):
        self.sw_hid_signal.emit()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.sw_mouse_released_signal.emit()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.sw_mouse_pressed_signal.emit()
