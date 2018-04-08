"""
Classes for handling views in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
from PySide2.QtCore import Qt, Signal, Slot, QModelIndex, QPoint
from PySide2.QtWidgets import QAbstractItemView
from widgets.link_widget import LinkWidget

class LinkView(QAbstractItemView):
    """View for showing connections as links.

    Attributes:
        parent(ToolboxUI): Parent of this view
    """

    customContextMenuRequested = Signal("QPoint", "QModelIndex", name="customContextMenuRequested")

    def __init__(self, parent, layout):
        super().__init__()
        self._parent = parent
        self.layout = layout

    def find_link_widget(self, index):
        """Find link widget in layout, by model index"""
        for i in range(self.layout.count()):
            link = self.layout.itemAt(i).widget()
            if not link.is_link:
                continue
            if link.model_index == index:
                return i
        return None

    @Slot(QModelIndex, QModelIndex, name='dataChanged') #TODO: check this
    def dataChanged(self, top_left, bottom_right, roles=None):
        """update view when model changes"""
        #logging.debug("data changed")
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom+1):
            for column in range(left, right+1):
                index = self.model().index(row, column)
                data = self.model().data(index, Qt.DisplayRole)
                if data:    #connection made, add link widget
                    input_item = self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
                    output_item = self.model().headerData(row, Qt.Vertical, Qt.DisplayRole)
                    sub_windows = self._parent.ui.mdiArea.subWindowList()
                    sw_owners = list(sw.widget().owner() for sw in sub_windows)
                    o = sw_owners.index(output_item)
                    i = sw_owners.index(input_item)
                    from_slot = sub_windows[o].widget().ui.toolButton_outputslot
                    to_slot = sub_windows[i].widget().ui.toolButton_inputslot
                    link = LinkWidget(self._parent, from_slot, to_slot, index)
                    #connect signals
                    sub_windows[i].sw_moved_signal.connect(link.update)
                    sub_windows[o].sw_moved_signal.connect(link.update)
                    sub_windows[i].sw_showed_signal.connect(link.update)
                    sub_windows[o].sw_showed_signal.connect(link.update)
                    sub_windows[i].sw_hid_signal.connect(link.update)
                    sub_windows[o].sw_hid_signal.connect(link.update)
                    #sub_windows[i].sw_mouse_pressed_or_released_signal.connect(link.set_update_mask_on_move)
                    #sub_windows[o].sw_mouse_pressed_or_released_signal.connect(link.set_update_mask_on_move)
                    link.customContextMenuRequested.connect(self.request_context_menu)
                    self.layout.addWidget(link)
                else:   #connection destroyed, remove link widget
                    i = self.find_link_widget(index)
                    if i is not None:
                        self.layout.takeAt(i).widget().deleteLater()

    @Slot("QPoint", "QModelIndex", name="request_context_menu")
    def request_context_menu(self, pos, index):
        self.customContextMenuRequested.emit(pos, index)
