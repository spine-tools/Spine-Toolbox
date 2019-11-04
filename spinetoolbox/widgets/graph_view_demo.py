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
    QFinalState,
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

    drag_entered = Signal()

    def __init__(self, parent):
        """Initializes class.

        Args:
            parent (GraphViewForm)
        """
        super().__init__(parent)
        self.graphics_overlay = OverlayWidget(parent.ui.graphicsView, Qt.white)
        self.object_tree_overlay = OverlayWidget(parent.ui.dockWidget_object_tree, QColor(0, 255, 255, 32))
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
        button_layout.addStretch()
        button_layout.addWidget(self.button_abort)
        button_layout.addWidget(self.button_back)
        button_layout.addWidget(self.button_next)
        button_layout.addStretch()
        layout = QVBoxLayout(self.graphics_overlay)
        layout.addStretch()
        layout.addWidget(self.label)
        layout.addWidget(button_container)
        layout.addStretch()
        self.machine = QStateMachine(self)

    def eventFilter(self, obj, event):
        if obj == self.graphics_overlay and event.type() == QEvent.DragEnter:
            self.drag_entered.emit()
        return False

    def is_running(self):
        return self.machine.isRunning()

    def init_demo(self):
        if self.is_running():
            return
        self.parent().ui.treeView_object.selectionModel().clearSelection()
        # States
        dead = QFinalState(self.machine)
        dying = QState(self.machine)
        running = QState(self.machine)
        teasing = QState(running)
        before_selecting_one = QState(running)
        selecting_one = QState(running)
        before_selecting_more = QState(running)
        selecting_more = QState(running)
        ending = QState(running)
        self.machine.setInitialState(running)
        running.setInitialState(teasing)
        # State properties
        dying.assignProperty(self.graphics_overlay, "visible", False)
        dying.assignProperty(self.object_tree_overlay, "visible", False)
        dying.entered.connect(lambda: self.graphics_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True))
        running.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        running.assignProperty(self.graphics_overlay, "visible", True)
        running.entered.connect(lambda: self.graphics_overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False))
        teasing.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        teasing.assignProperty(self.label, "text", "<html>First time? Try the live demo!</html>")
        teasing.assignProperty(self.button_abort, "visible", False)
        teasing.assignProperty(self.button_next, "text", "Start demo")
        teasing.assignProperty(self.button_back, "visible", False)
        teasing.assignProperty(self.object_tree_overlay, "visible", False)
        text = """
            <html>
            <p>Selecting items in the object tree automatically triggers
            graph generation.</b>
            <p>Press <b>Show</b> to see it in action.</p>
            </html>
        """
        before_selecting_one.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        before_selecting_one.assignProperty(self.label, "text", text)
        before_selecting_one.assignProperty(self.button_abort, "visible", True)
        before_selecting_one.assignProperty(self.button_next, "text", "Show")
        before_selecting_one.assignProperty(self.button_back, "visible", False)
        before_selecting_one.assignProperty(self.object_tree_overlay, "visible", True)
        selecting_one.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        selecting_one.assignProperty(self.graphics_overlay, "visible", False)
        selecting_one.assignProperty(self.object_tree_overlay, "visible", False)
        before_selecting_more.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        before_selecting_more.assignProperty(self.graphics_overlay, "visible", True)
        sticky = self.parent().qsettings().value("appSettings/stickySelection", defaultValue="false")
        note = " (by holding down the <b>Ctrl</b> key)" if sticky == "false" else ""
        text = f"""
            <html>
            <p>Selecting multiple items{note} makes things more interesting.</p>
            <p>Press <b>Show</b> to see it in action.</p>
            </html>
        """
        before_selecting_more.assignProperty(self.label, "text", text)
        before_selecting_more.assignProperty(self.button_back, "visible", True)
        before_selecting_more.assignProperty(self.object_tree_overlay, "visible", True)
        selecting_more.assignProperty(self.parent().ui.dockWidget_object_tree, "visible", True)
        selecting_more.assignProperty(self.graphics_overlay, "visible", False)
        selecting_more.assignProperty(self.object_tree_overlay, "visible", False)
        ending.assignProperty(self.graphics_overlay, "visible", True)
        ending.assignProperty(self.label, "text", "<html>That's all for now. Thanks for watching.</html>")
        ending.assignProperty(self.button_abort, "visible", False)
        ending.assignProperty(self.button_next, "text", "Close")
        ending.assignProperty(self.button_back, "visible", False)
        ending.assignProperty(self.object_tree_overlay, "visible", False)
        # Transitions
        dying.addTransition(dead)
        running.addTransition(self.button_abort.clicked, dying)
        teasing.addTransition(self.parent().graph_created, dying)
        teasing.addTransition(self.drag_entered, dying)
        teasing.addTransition(self.button_next.clicked, before_selecting_one)
        transition = before_selecting_one.addTransition(self.button_next.clicked, selecting_one)
        animation = SelectionAnimation(self.parent(), command=QItemSelectionModel.ClearAndSelect)
        transition.addAnimation(animation)
        selecting_one.addTransition(animation.finished, before_selecting_more)
        before_selecting_more.addTransition(self.button_back.clicked, before_selecting_one)
        transition = before_selecting_more.addTransition(self.button_next.clicked, selecting_more)
        animation = SelectionAnimation(self.parent(), command=QItemSelectionModel.Select)
        transition.addAnimation(animation)
        selecting_more.addTransition(animation.finished, ending)
        ending.addTransition(self.button_next.clicked, dying)
        # Run
        self.machine.start()


class SelectionAnimation(QVariantAnimation):
    def __init__(self, parent, command, duration=1000, max_steps=4):
        """
        Args:
            parent (GraphViewForm)
            command (QItemSelectionModel.SelectionFlags)
            duration (int): milliseconds
            max_steps (int)
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
            self.setDuration(self._duration)
            self._selection_model.clearSelection()
            self._selection_model.select(self._indexes[0], self._command)

    @Slot(int)
    def _handle_current_loop_changed(self, loop):
        self._selection_model.select(self._indexes[loop], self._command)
