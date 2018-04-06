"""
Classes for handling views in PySide2's model/view framework.
Note: These are Spine Toolbox internal data models.


:author: Manuel Marin <manuelma@kth.se>
:date:   4.4.2018
"""

import logging
from PySide2.QtCore import Qt, Slot, QModelIndex
from PySide2.QtWidgets import QAbstractItemView
from widgets.link_widget import LinkWidget

class LinkView(QAbstractItemView):
    """View for showing connections as links.

    Attributes:
        parent(ToolboxUI): Parent of this view
    """

    def __init__(self, parent):
        super().__init__()
        self._parent = parent
        self.link_widgets = list()
        self.model_indices = list()

    def append_link_widget(self, link):
        """Add link widget to the view"""
        self.link_widgets.append(link)

    def remove_link_widget(self, pos):
        """Remove link widget from the view"""
        self.link_widgets.pop(pos).deleteLater()
        del self.model_indices[pos]

    @Slot(QModelIndex, QModelIndex, name='dataChanged') #TODO: check this
    def dataChanged(self, top_left, bottom_right, roles=None):
        """update view when model changes"""
        logging.debug("data changed")
        top = top_left.row()
        left = top_left.column()
        bottom = bottom_right.row()
        right = bottom_right.column()
        for row in range(top, bottom+1):
            for column in range(left, right+1):
                idx = self.model().index(row, column)
                data = self.model().data(idx, Qt.DisplayRole)
                if data:    #connection made, add link widget
                    input_item = self.model().headerData(column, Qt.Horizontal, Qt.DisplayRole)
                    output_item = self.model().headerData(row, Qt.Vertical, Qt.DisplayRole)
                    sub_windows = self._parent.ui.mdiArea.subWindowList()
                    sw_owners = list(sw.widget().owner() for sw in sub_windows)
                    o = sw_owners.index(output_item)
                    i = sw_owners.index(input_item)
                    from_slot = sub_windows[o].widget().ui.toolButton_outputslot
                    to_slot = sub_windows[i].widget().ui.toolButton_inputslot
                    link = LinkWidget(self._parent, from_slot, to_slot)
                    #connect signals
                    sub_windows[i].sw_moved_signal.connect(link.custom_repaint)
                    sub_windows[o].sw_moved_signal.connect(link.custom_repaint)
                    sub_windows[i].sw_showed_signal.connect(link.custom_show)
                    sub_windows[o].sw_showed_signal.connect(link.custom_show)
                    sub_windows[i].sw_hid_signal.connect(link.custom_hide)
                    sub_windows[o].sw_hid_signal.connect(link.custom_hide)
                    sub_windows[i].sw_mouse_released_signal.connect(link.update_mask)
                    sub_windows[o].sw_mouse_released_signal.connect(link.update_mask)
                    sub_windows[i].sw_mouse_pressed_signal.connect(link.clear_mask)
                    sub_windows[o].sw_mouse_pressed_signal.connect(link.clear_mask)
                    self.model_indices.append(idx)
                    self.append_link_widget(link)
                else:   #connection destroyed, remove link widget
                    try:
                        l = self.model_indices.index(idx)
                        self.remove_link_widget(l)
                    except ValueError:
                        pass
