######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains the GraphViewForm class.

:author: M. Marin (KTH)
:date:   26.11.2018
"""

import random
from PySide2.QtCore import Slot, QFinalState, QState, QItemSelectionModel, QAbstractAnimation, QVariantAnimation
from PySide2.QtGui import QCursor
from .state_machine_widget import StateMachineWidget


class GraphViewDemo(StateMachineWidget):
    """A widget that shows a demo for the graph view."""

    def __init__(self, parent):
        """Initializes class.

        Args:
            parent (GraphViewForm)
        """
        super().__init__("Live demo", parent)

    def _make_select_one(self):
        select_one = QState(self.machine)
        begin = QState(select_one)
        simulate = QState(select_one)
        finalize = QFinalState(select_one)
        begin.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        text = """
            <html>
            <p>Selecting items in the object tree automatically triggers
            graph generation.</b><br />
            <p>Press <b>Show</b> to see it in action.</p>
            </html>
        """
        begin.assignProperty(self.label_msg, "text", text)
        begin.assignProperty(self.button_right, "text", "Show")
        begin.assignProperty(self.button_right, "enabled", True)
        simulate.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        simulate.assignProperty(self.button_right, "enabled", False)

        select_one.setInitialState(begin)
        transition = begin.addTransition(self.button_right.clicked, simulate)
        animation = SelectionAnimation(self.parent().ui.treeView_object, command=QItemSelectionModel.ClearAndSelect)
        transition.addAnimation(animation)
        simulate.addTransition(animation.finished, finalize)
        return select_one

    def _make_select_more(self):
        select_more = QState(self.machine)
        begin = QState(select_more)
        simulate = QState(select_more)
        finalize = QFinalState(select_more)
        begin.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        sticky = self.parent().qsettings.value("appSettings/stickySelection", defaultValue="false")
        note = " (by holding down the <b>Ctrl</b> key)" if sticky == "false" else ""
        text = f"""
            <html>
            <p>Selecting multiple items{note} makes things more interesting.</p>
            <p>Press <b>Show</b> to see it in action.</p>
            </html>
        """
        begin.assignProperty(self.label_msg, "text", text)
        begin.assignProperty(self.button_right, "text", "Show")
        begin.assignProperty(self.button_right, "enabled", True)
        simulate.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        simulate.assignProperty(self.button_right, "enabled", False)

        select_more.setInitialState(begin)
        transition = begin.addTransition(self.button_right.clicked, simulate)
        animation = SelectionAnimation(self.parent().ui.treeView_object, command=QItemSelectionModel.Select)
        transition.addAnimation(animation)
        simulate.addTransition(animation.finished, finalize)
        return select_more

    def _make_good_bye(self):
        good_bye = QState(self.machine)
        begin = QState(good_bye)
        finalize = QFinalState(good_bye)
        good_bye.assignProperty(self.label_msg, "text", "<html>That's all for now. Hope you liked it.</html>")
        good_bye.assignProperty(self.button_left, "visible", False)
        good_bye.assignProperty(self.button_right, "enabled", True)
        good_bye.assignProperty(self.button_right, "text", "Close")

        good_bye.setInitialState(begin)
        begin.addTransition(self.button_right.clicked, finalize)
        return good_bye

    def set_up_machine(self):
        super().set_up_machine()
        select_one = self._make_select_one()
        select_more = self._make_select_more()
        good_bye = self._make_good_bye()
        self.welcome.addTransition(self.welcome.finished, select_one)
        select_one.addTransition(select_one.finished, select_more)
        select_more.addTransition(select_more.finished, good_bye)
        good_bye.finished.connect(self.close)


class SelectionAnimation(QVariantAnimation):
    def __init__(self, view, command, duration=2000, max_steps=4):
        """
        Args:
            view (QAbstractItemView)
            command (QItemSelectionModel.SelectionFlags)
            duration (int): milliseconds
            max_steps (int)
        """
        super().__init__(view)
        self.viewport = view.viewport()
        self._command = command
        self._duration = duration
        self._selection_model = view.selectionModel()
        model = view.model()
        root_item = model.root_item
        population_size = root_item.child_count()
        sample_size = min(max_steps, population_size)
        picks = random.sample(range(population_size), k=sample_size)
        self._indexes = [model.index_from_item(root_item.child(k)) for k in picks]
        self._positions = [self._random_point(view.visualRect(ind)) for ind in self._indexes]
        self._lines = None
        self.setStartValue(0.0)
        self.setEndValue(1.0)
        self.setLoopCount(len(self._indexes))
        self.setDuration(self._duration)
        self.currentLoopChanged.connect(self._handle_current_loop_changed)
        self.valueChanged.connect(self._handle_value_changed)
        self.finished.connect(self._handle_finished)

    @staticmethod
    def _random_point(rect):
        return rect.topLeft() + (rect.bottomRight() - rect.topLeft()) / random.triangular(1, 3)

    def updateState(self, new, old):
        if new == QAbstractAnimation.Running and old == QAbstractAnimation.Stopped:
            self._selection_model.clearSelection()
            pos = self.viewport.mapFromGlobal(QCursor.pos())
            self._positions.insert(0, pos)
            self._lines = list(zip(self._positions[:-1], self._positions[1:]))

    @Slot("QVariant")
    def _handle_value_changed(self, value):
        src_pos, dst_pos = self._lines[self.currentLoop()]
        value = max(0.0, min(1.0, 4.0 * (value - 0.5)))
        pos = src_pos + (dst_pos - src_pos) * value
        pos = self.viewport.mapToGlobal(pos)
        QCursor.setPos(pos)

    @Slot(int)
    def _handle_current_loop_changed(self, loop):
        self._selection_model.select(self._indexes[loop - 1], self._command)

    @Slot()
    def _handle_finished(self):
        self._selection_model.select(self._indexes[-1], self._command)
