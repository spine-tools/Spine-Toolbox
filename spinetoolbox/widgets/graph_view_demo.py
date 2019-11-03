######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
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

from random import sample
from PySide2.QtCore import (
    Qt,
    QObject,
    Signal,
    Slot,
    QEvent,
    QStateMachine,
    QState,
    QItemSelectionModel,
    QAbstractAnimation,
    QVariantAnimation,
)
from PySide2.QtGui import QColor, QFont
from PySide2.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from .custom_qwidgets import OverlayWidget


class GraphViewDemo(QObject):
    """A widget that shows a demo for the graph view."""

    started = Signal()
    stopped = Signal()

    def __init__(self, parent):
        """Initializes class.

        Args:
            parent (GraphViewForm)
        """
        super().__init__(parent)
        self._ignore_stop = False
        self.graphics_overlay = OverlayWidget(parent.ui.graphicsView, QColor(255, 255, 255, 255))
        self.object_tree_overlay = OverlayWidget(parent.ui.treeView_object, QColor(0, 255, 255, 32))
        self.graphics_overlay.setAcceptDrops(True)
        self.graphics_overlay.installEventFilter(self)
        self.label = QLabel(self.graphics_overlay)
        self.label.setFont(QFont("arial,helvetica", 16))
        self.label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.label.setWordWrap(True)
        self.button_abort = QPushButton("Abort", self.graphics_overlay)
        self.button_next = QPushButton(self.graphics_overlay)
        self.button_back = QPushButton("Back", self.graphics_overlay)
        button_container = QWidget(self.graphics_overlay)
        button_layout = QHBoxLayout(button_container)
        button_layout.addWidget(self.button_abort)
        button_layout.addStretch()
        button_layout.addWidget(self.button_back)
        button_layout.addWidget(self.button_next)
        layout = QVBoxLayout(self.graphics_overlay)
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(button_container)
        self.machine = QStateMachine(self)
        self.button_abort.clicked.connect(self.stop)
        parent.graph_created.connect(self._handle_graph_created)

    def eventFilter(self, obj, event):
        if obj == self.graphics_overlay and event.type() == QEvent.DragEnter:
            obj.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        return False

    def init_demo(self):
        # States
        sleeping = QState(self.machine)
        running = QState(self.machine)
        teasing = QState(running)
        before_selecting_one = QState(running)
        selecting_one = QState(running)
        before_selecting_two = QState(running)
        selecting_two = QState(running)
        ending = QState(running)
        running.setInitialState(teasing)
        sleeping.assignProperty(self.graphics_overlay, "visible", False)
        sleeping.assignProperty(self.object_tree_overlay, "visible", False)
        running.assignProperty(self.graphics_overlay, "visible", True)
        teasing.assignProperty(self.label, "text", "First time? Try the live demo!")
        teasing.assignProperty(self.button_abort, "visible", False)
        teasing.assignProperty(self.button_next, "text", "Start demo")
        teasing.assignProperty(self.button_back, "visible", False)
        teasing.assignProperty(self.object_tree_overlay, "visible", False)
        before_selecting_one.assignProperty(self.label, "text", "Select items in the object tree to see them here.")
        before_selecting_one.assignProperty(self.button_abort, "visible", True)
        before_selecting_one.assignProperty(self.button_next, "text", "Show")
        before_selecting_one.assignProperty(self.button_back, "visible", False)
        before_selecting_one.assignProperty(self.object_tree_overlay, "visible", False)
        selecting_one.assignProperty(self.graphics_overlay, "visible", False)
        selecting_one.assignProperty(self.object_tree_overlay, "visible", True)
        before_selecting_two.assignProperty(self.graphics_overlay, "visible", True)
        before_selecting_two.assignProperty(self.label, "text", "Select multiple items to make it more interesting.")
        before_selecting_two.assignProperty(self.button_back, "visible", True)
        before_selecting_two.assignProperty(self.object_tree_overlay, "visible", False)
        selecting_two.assignProperty(self.graphics_overlay, "visible", False)
        selecting_two.assignProperty(self.object_tree_overlay, "visible", True)
        ending.assignProperty(self.graphics_overlay, "visible", True)
        ending.assignProperty(self.label, "text", "That's all for now. Thanks for watching.")
        ending.assignProperty(self.button_abort, "visible", False)
        ending.assignProperty(self.button_next, "text", "Close")
        ending.assignProperty(self.button_back, "visible", False)
        ending.assignProperty(self.object_tree_overlay, "visible", False)
        # Transitions
        running.addTransition(self.stopped, sleeping)
        sleeping.addTransition(self.started, running)
        teasing.addTransition(self.button_next.clicked, before_selecting_one)
        transition = before_selecting_one.addTransition(self.button_next.clicked, selecting_one)
        animation = SelectionAnimation(self.parent(), command=QItemSelectionModel.ClearAndSelect)
        transition.addAnimation(animation)
        animation.started.connect(self.begin_animation)
        animation.finished.connect(self.end_animation)
        selecting_one.addTransition(animation.finished, before_selecting_two)
        before_selecting_two.addTransition(self.button_back.clicked, before_selecting_one)
        transition = before_selecting_two.addTransition(self.button_next.clicked, selecting_two)
        animation = SelectionAnimation(self.parent(), command=QItemSelectionModel.Select)
        animation.started.connect(self.begin_animation)
        animation.finished.connect(self.end_animation)
        transition.addAnimation(animation)
        selecting_two.addTransition(animation.finished, ending)
        ending.addTransition(self.button_next.clicked, sleeping)
        # Run
        self.machine.setInitialState(running)
        self.machine.start()

    @Slot()
    def begin_animation(self):
        self.parent().ui.treeView_object.selectionModel().clearSelection()
        self._ignore_stop = True

    @Slot()
    def end_animation(self):
        self._ignore_stop = False

    @Slot(bool)
    def _handle_graph_created(self, checked=False):
        if not self._ignore_stop:
            self.stop()

    def start(self):
        self.started.emit()
        self.graphics_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def stop(self):
        self.stopped.emit()
        self.graphics_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)


class SelectionAnimation(QVariantAnimation):

    started = Signal()

    def __init__(self, parent, command, duration=1500, max_steps=5):
        """
        Args:
            parent (GraphViewForm)
        """
        super().__init__(parent)
        self._command = command
        self._duration = duration
        self._selection_model = parent.ui.treeView_object.selectionModel()
        model = parent.object_tree_model
        root_item = model.root_item
        population_size = root_item.child_count()
        sample_size = min(max_steps, population_size)
        picks = sample(range(population_size), k=sample_size)
        self._indexes = [model.index_from_item(root_item.child(k)) for k in picks]
        self.setStartValue(0)
        self.setEndValue(0)
        self.setLoopCount(len(self._indexes))
        self.currentLoopChanged.connect(self._handle_current_loop_changed)

    def updateState(self, new, old):
        if new == QAbstractAnimation.Running and old == QAbstractAnimation.Stopped:
            self.started.emit()
            self.setDuration(self._duration)
            self._selection_model.select(self._indexes[0], self._command)

    @Slot(int)
    def _handle_current_loop_changed(self, loop):
        self._selection_model.select(self._indexes[loop], self._command)
