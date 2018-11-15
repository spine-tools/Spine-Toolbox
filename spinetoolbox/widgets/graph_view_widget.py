######################################################################################################################
# Copyright (C) 2017 - 2018 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Widget to show graph view form.

:author: M. Marin (KTH), J. Olauson (KTH)
:date:   5.11.2018
"""

import logging
from ui.graph_view_form import Ui_MainWindow
from PySide2.QtWidgets import QMainWindow, QGraphicsScene, QDialog, QErrorMessage, QToolButton, QAction
from PySide2.QtGui import QFont, QFontMetrics, QColor, QGuiApplication, QIcon
from PySide2.QtCore import Qt, Signal, Slot, QSettings, QRectF, QItemSelection, QItemSelectionModel, QSize
import numpy as np
from numpy import atleast_1d as arr
from scipy.sparse.csgraph import dijkstra
from widgets.custom_qdialog import AddObjectClassesDialog, AddObjectsDialog, \
    AddRelationshipClassesDialog, AddRelationshipsDialog, \
    EditObjectClassesDialog, EditObjectsDialog, \
    EditRelationshipClassesDialog, EditRelationshipsDialog, \
    CommitDialog
from models import ObjectTreeModel, ObjectClassListModel
from graphics_items import ObjectItem, ArcItem, ObjectLabelItem, ArcLabelItem, CustomTextItem
from helpers import busy_effect
from config import STATUSBAR_SS


class GraphViewForm(QMainWindow):
    """A widget to show the graph view.

    Attributes:
        view (View): View instance that owns this form
        db_map (DiffDatabaseMapping): The object relational database mapping
        database (str): The database name
    """
    msg = Signal(str, name="msg")
    msg_error = Signal(str, name="msg_error")

    def __init__(self, view, db_map, database):
        """Initialize class."""
        super().__init__(flags=Qt.Window)  # Setting the parent inherits the stylesheet
        self._view = view
        self.db_map = db_map
        self._spacing_factor = 1.0
        self._has_graph = False
        self.database = database
        self.temp_object_item = None
        self.err_msg = QErrorMessage(self)
        # Setup UI from Qt Designer file
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.qsettings = QSettings("SpineProject", "Spine Toolbox")
        # Set up status bar
        self.ui.statusbar.setFixedHeight(20)
        self.ui.statusbar.setSizeGripEnabled(False)
        self.ui.statusbar.setStyleSheet(STATUSBAR_SS)
        self.setWindowTitle("Data store graph view    -- {} --".format(database))
        self.font = QFont("", 64)
        self.font_metric = QFontMetrics(self.font)
        self.object_name_list = list()
        self.object_class_name_list = list()
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        self.object_tree_model = ObjectTreeModel(self)
        self.object_class_list_model = ObjectClassListModel(self)
        self.init_models()
        self.connect_signals()
        self.restore_ui()
        self.add_toggle_view_actions()
        self.set_commit_rollback_actions_enabled(False)
        self.build_graph()

    def init_models(self):
        """Initialize models and their respective views."""
        self.object_tree_model.build_flat_tree(self.database)
        self.object_class_list_model.populate_list()
        self.ui.treeView.setModel(self.object_tree_model)
        self.ui.treeView.resizeColumnToContents(0)
        self.ui.treeView.expand(self.object_tree_model.root_item.index())
        self.ui.listView_object_class.setModel(self.object_class_list_model)
        # Setup a button for 'New object class' item)
        index = self.object_class_list_model.add_more_index
        action = QAction()
        icon = QIcon(":/icons/plus_object_icon.png")
        action.setIcon(icon)
        action.setText(index.data(Qt.DisplayRole))
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setDefaultAction(action)
        button.setIconSize(self.ui.listView_object_class.iconSize())
        height = self.ui.listView_object_class.iconSize().height()
        height += QFontMetrics(self.ui.listView_object_class.font()).lineSpacing()
        height += 4  # Some extra room
        button.setMinimumHeight(height)
        self.ui.listView_object_class.setIndexWidget(index, button)
        action.triggered.connect(self.show_add_object_classes_form)

    def show(self):
        """Make sure object tree is somewhat visible."""
        super().show()
        length = self.ui.treeView.header().length()
        return
        # FIXME
        sizes = self.ui.splitter_tree_graph.sizes()
        if sizes[0] < length:
            self.ui.splitter_tree_graph.setSizes([length, sizes[1] - (length - sizes[0])])

    def connect_signals(self):
        """Connect signals."""
        self.msg.connect(self.add_message)
        self.msg_error.connect(self.add_error_message)
        self.ui.treeView.selectionModel().selectionChanged.connect(self.receive_item_tree_selection_changed)
        self.ui.actionBuild.triggered.connect(self.build_graph)
        self.ui.graphicsView.object_dropped.connect(self.show_add_object_form)
        self.ui.actionCommit.triggered.connect(self.show_commit_session_dialog)
        self.ui.actionRollback.triggered.connect(self.rollback_session)
        self.ui.actionRefresh.triggered.connect(self.refresh_session)

    @Slot(str, name="add_message")
    def add_message(self, msg):
        """Append regular message to status bar.

        Args:
            msg (str): String to show in QStatusBar
        """
        current_msg = self.ui.statusbar.currentMessage()
        self.ui.statusbar.showMessage(" ".join([current_msg, msg]), 5000)

    @Slot(str, name="add_error_message")
    def add_error_message(self, msg):
        """Show error message.

        Args:
            msg (str): String to show in QErrorMessage
        """
        self.err_msg.showMessage(msg)

    def add_toggle_view_actions(self):
        """Add toggle view actions to View menu."""
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_tree.toggleViewAction())
        self.ui.menuDock_Widgets.addAction(self.ui.dockWidget_item_list.toggleViewAction())

    def set_commit_rollback_actions_enabled(self, on):
        self.ui.actionCommit.setEnabled(on)
        self.ui.actionRollback.setEnabled(on)

    @Slot(name="show_commit_session_dialog")
    def show_commit_session_dialog(self):
        """Query user for a commit message and commit changes to source database."""
        if not self.db_map.has_pending_changes():
            self.msg.emit("Nothing to commit yet.")
            return
        dialog = CommitDialog(self, self.database)
        answer = dialog.exec_()
        if answer != QDialog.Accepted:
            return
        self.commit_session(dialog.commit_msg)

    @busy_effect
    def commit_session(self, commit_msg):
        try:
            self.db_map.commit_session(commit_msg)
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes committed successfully."
        self.msg.emit(msg)

    @Slot(name="rollback_session")
    def rollback_session(self):
        try:
            self.db_map.rollback_session()
            self.set_commit_rollback_actions_enabled(False)
        except SpineDBAPIError as e:
            self.msg_error.emit(e.msg)
            return
        msg = "All changes since last commit rolled back successfully."
        self.msg.emit(msg)
        self.init_models()

    @Slot(name="refresh_session")
    def refresh_session(self):
        msg = "Session refreshed."
        self.msg.emit(msg)
        self.init_models()

    @busy_effect
    @Slot("bool", name="build_graph")
    def build_graph(self, checked=True):
        self.init_graph_data()
        self.make_graph()
        self.ui.graphicsView.scale_to_fit_scene()

    @Slot("QItemSelection", "QItemSelection", name="receive_item_tree_selection_changed")
    def receive_item_tree_selection_changed(self, selected, deselected):
        """Select or deselect all children when selecting or deselecting the parent."""
        current = self.sender().currentIndex()
        if self.sender().isSelected(current):
            selected.select(self.sender().currentIndex(), self.sender().currentIndex())
        else:
            deselected.select(self.sender().currentIndex(), self.sender().currentIndex())
        new_selection = QItemSelection()
        for index in deselected.indexes():
            if not self.object_tree_model.hasChildren(index):
                continue
            row_count = self.object_tree_model.rowCount(index)
            top = self.object_tree_model.index(0, 0, index)
            bottom = self.object_tree_model.index(row_count - 1, 0, index)
            new_selection.merge(QItemSelection(top, bottom), QItemSelectionModel.Select)
        self.sender().select(new_selection, QItemSelectionModel.Deselect)
        new_selection = QItemSelection()
        for index in selected.indexes():
            if not self.object_tree_model.hasChildren(index):
                continue
            row_count = self.object_tree_model.rowCount(index)
            top = self.object_tree_model.index(0, 0, index)
            bottom = self.object_tree_model.index(row_count - 1, 0, index)
            new_selection.merge(QItemSelection(top, bottom), QItemSelectionModel.Select)
        self.sender().select(new_selection, QItemSelectionModel.Select)
        self.build_graph()

    def init_graph_data(self):
        """Initialize graph data by querying db_map."""
        self.object_name_list = list()
        self.object_class_name_list = list()
        selection_model = self.ui.treeView.selectionModel()
        root_item = self.object_tree_model.root_item
        for i in range(root_item.rowCount()):
            object_class_name_item = root_item.child(i, 0)
            object_class_name = object_class_name_item.data(Qt.EditRole)
            for j in range(object_class_name_item.rowCount()):
                object_name_item = object_class_name_item.child(j, 0)
                object_name = object_name_item.data(Qt.EditRole)
                index = self.object_tree_model.indexFromItem(object_name_item)
                if selection_model.isSelected(index):
                    self.object_name_list.append(object_name)
                    self.object_class_name_list.append(object_class_name)
        self.arc_relationship_class_name_list = list()
        self.arc_object_names_list = list()
        self.arc_object_class_names_list = list()
        self.src_ind_list = list()
        self.dst_ind_list = list()
        relationship_class_dict = {
            x.id: {
                "name": x.name,
                "object_class_name_list": x.object_class_name_list.split(",")
            } for x in self.db_map.wide_relationship_class_list()
        }
        for relationship in self.db_map.wide_relationship_list():
            relationship_class_name = relationship_class_dict[relationship.class_id]["name"]
            object_class_name_list = relationship_class_dict[relationship.class_id]["object_class_name_list"]
            object_name_list = relationship.object_name_list.split(",")
            for i in range(len(object_name_list)):
                src_object_name = object_name_list[i]
                try:
                    dst_object_name = object_name_list[i + 1]
                except IndexError:
                    dst_object_name = object_name_list[0]
                try:
                    src_ind = self.object_name_list.index(src_object_name)
                    dst_ind = self.object_name_list.index(dst_object_name)
                except ValueError:
                    continue
                self.src_ind_list.append(src_ind)
                self.dst_ind_list.append(dst_ind)
                self.arc_relationship_class_name_list.append(relationship_class_name)
                arc_object_names = list()
                arc_object_class_names = list()
                for x, y in zip(object_name_list, object_class_name_list):
                    if x in (src_object_name, dst_object_name):
                        continue
                    arc_object_names.append(x)
                    arc_object_class_names.append(y)
                self.arc_object_names_list.append(arc_object_names)
                self.arc_object_class_names_list.append(arc_object_class_names)

    def shortest_path_matrix(self):
        """Return the shortest-path matrix."""
        N = len(self.object_name_list)
        if not N:
            return None
        dist = np.zeros((N, N))
        src_ind = arr(self.src_ind_list)
        dst_ind = arr(self.dst_ind_list)
        max_sep = max([self.font_metric.width(x) for x in self.object_name_list], default=0)
        try:
            dist[src_ind, dst_ind] = dist[dst_ind, src_ind] = self._spacing_factor * max_sep
        except IndexError:
            pass
        d = dijkstra(dist, directed=False)
        # Remove infinites and zeros
        # d[d == np.inf] = np.max(d[d != np.inf])
        d[d == np.inf] = self._spacing_factor * max_sep * 3
        d[d == 0] = self._spacing_factor * max_sep * 1e-6
        return d

    def sets(self, N):
        """Return sets of vertex pairs indices."""
        sets = []
        for n in range(1, N):
            pairs = np.zeros((N - n, 2), int)  # pairs on diagonal n
            pairs[:, 0] = np.arange(N - n)
            pairs[:, 1] = pairs[:, 0] + n
            mask = np.mod(range(N - n), 2 * n) < n
            s1 = pairs[mask]
            s2 = pairs[~mask]
            if len(s1) > 0:
                sets.append(s1)
            if len(s2) > 0:
                sets.append(s2)
        return sets

    def vertex_coordinates(self, matrix, iterations=10, weight_exp=-2, initial_diameter=100):
        """Return x and y coordinates for each vertex in the graph, computed using VSGD-MS."""
        N = len(matrix)
        if N == 1:
            return [0], [0]
        mask = np.ones((N, N)) == 1 - np.tril(np.ones((N, N)))  # Upper triangular except diagonal
        layout = np.random.rand(N, 2) * initial_diameter - initial_diameter / 2  # Random layout with diameter 100
        weights = matrix ** weight_exp  # bus-pair weights (lower for distant buses)
        maxstep = 1 / np.min(weights[mask])
        minstep = 1 / np.max(weights[mask])
        lambda_ = np.log(minstep / maxstep) / (iterations - 1)  # exponential decay of allowed adjustment
        sets = self.sets(N)  # construct sets of bus pairs
        for iteration in range(iterations):
            step = maxstep * np.exp(lambda_ * iteration)  # how big adjustments are allowed?
            rand_order = np.random.permutation(N)  # we don't want to use the same pair order each iteration
            for p in sets:
                v1, v2 = rand_order[p[:, 0]], rand_order[p[:, 1]]  # arrays of vertex1 and vertex2
                # current distance (possibly accounting for rescaling of system)
                dist = ((layout[v1, 0] - layout[v2, 0]) ** 2 + (layout[v1, 1] - layout[v2, 1]) ** 2) ** 0.5
                r = (matrix[v1, v2] - dist)[:, None] / 2 * (layout[v1] - layout[v2]) / dist[:, None]  # desired change
                dx1 = r * np.minimum(1, weights[v1, v2] * step)[:, None]
                dx2 = -dx1
                layout[v1, :] += dx1  # update position
                layout[v2, :] += dx2
        return layout[:, 0], layout[:, 1]

    def make_graph(self):
        """Make graph."""
        scene = QGraphicsScene()
        self.ui.graphicsView.setScene(scene)
        d = self.shortest_path_matrix()
        if d is None:
            msg = """
                <p>Select items in the <b>Item tree</b> to show them here.</p>
                <p>You can select multiple items by holding the 'Ctrl' key.</p>
                <br>
                <p>Drag items from the <b>Item list</b> and drop them here to create new ones.</p>
            """
            msg_item = CustomTextItem(msg, self.font)
            scene.addItem(msg_item)
            self._has_graph = False
            return
        x, y = self.vertex_coordinates(d)
        object_items = list()
        for i in range(len(self.object_name_list)):
            object_name = self.object_name_list[i]
            object_class_name = self.object_class_name_list[i]
            icon = self.object_tree_model.icon_dict[object_class_name]
            extent = 2 * self.font.pointSize()
            object_item = ObjectItem(icon.pixamp(extent, extent), x[i], y[i])
            label_item = ObjectLabelItem(object_name, self.font, QColor(224, 224, 224, 128))
            object_item.set_label_item(label_item)
            scene.addItem(object_item)
            scene.addItem(label_item)
            object_items.append(object_item)
        for k in range(len(self.src_ind_list)):
            i = self.src_ind_list[k]
            j = self.dst_ind_list[k]
            relationship_class_name = self.arc_relationship_class_name_list[k]
            object_names = self.arc_object_names_list[k]
            object_class_names = self.arc_object_class_names_list[k]
            arc_item = ArcItem(x[i], y[i], x[j], y[j], .5 * self.font.pointSize())
            icons = [self.object_tree_model.icon_dict[x] for x in object_class_names]
            arc_label_item = ArcLabelItem(
                relationship_class_name, icons, object_names,
                2 * self.font.pointSize(), self.font, QColor(224, 224, 224, 224))
            arc_item.set_label_item(arc_label_item)
            scene.addItem(arc_item)
            scene.addItem(arc_label_item)
            object_items[i].add_outgoing_arc_item(arc_item)
            object_items[j].add_incoming_arc_item(arc_item)
        self._has_graph = True

    @Slot(name="show_add_object_classes_form")
    def show_add_object_classes_form(self):
        """Show dialog to let user select preferences for new object classes."""
        dialog = AddObjectClassesDialog(self)
        dialog.show()

    def add_object_classes(self, object_classes):
        """Insert new object classes."""
        for object_class in object_classes:
            self.object_tree_model.add_object_class(object_class)
            self.object_class_list_model.add_object_class(object_class)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new object classes '{}'.".format("', '".join([x.name for x in object_classes]))
        self.msg.emit(msg)

    @Slot("QPoint", "int", "QPixmap", name="show_add_object_form")
    def show_add_object_form(self, pos, class_id, pixmap):
        if self._has_graph:
            scene = self.ui.graphicsView.scene()
        else:
            scene = QGraphicsScene()
            self.ui.graphicsView.setScene(scene)
        # Add transparent rect item the size of the scene
        view_rect = self.ui.graphicsView.viewport().rect()
        top_left = self.ui.graphicsView.mapToScene(view_rect.topLeft())
        bottom_right = self.ui.graphicsView.mapToScene(view_rect.bottomRight())
        scene_rect = QRectF(top_left, bottom_right)
        rect_item = scene.addRect(scene_rect, Qt.NoPen)
        rect_item.setZValue(-100)
        # Add temp object item as a marker
        scene_pos = self.ui.graphicsView.mapToScene(pos)
        extent = 2 * self.font.pointSize()
        self.temp_object_item = ObjectItem(pixmap.scaled(extent, extent), scene_pos.x(), scene_pos.y())
        scene.addItem(self.temp_object_item)
        self._has_graph = True
        dialog = AddObjectsDialog(self, class_id=class_id, force_default=True)
        dialog.rejected.connect(lambda: scene.removeItem(self.temp_object_item))
        dialog.show()

    def add_objects(self, objects):
        """Insert new objects."""
        scene = self.ui.graphicsView.scene()
        pixmap = self.temp_object_item.pixmap()
        x = self.temp_object_item.x()
        y = self.temp_object_item.y()
        width = self.temp_object_item.pixmap().width()
        height = self.temp_object_item.pixmap().height()
        scene.removeItem(self.temp_object_item)
        for k, object_ in enumerate(objects):
            self.object_tree_model.add_object(object_, flat=True)
            object_item = ObjectItem(pixmap, x + .5 * width, y + (k + .5) * height)
            label_item = ObjectLabelItem(object_.name, self.font, QColor(224, 224, 224, 128))
            object_item.set_label_item(label_item)
            scene.addItem(object_item)
            scene.addItem(label_item)
        self.set_commit_rollback_actions_enabled(True)
        msg = "Successfully added new objects '{}'.".format("', '".join([x.name for x in objects]))
        self.msg.emit(msg)

    def restore_ui(self):
        """Restore UI state from previous session."""
        window_size = self.qsettings.value("graphViewWidget/windowSize")
        window_state = self.qsettings.value("graphViewWidget/windowState")
        window_pos = self.qsettings.value("graphViewWidget/windowPosition")
        window_maximized = self.qsettings.value("graphViewWidget/windowMaximized", defaultValue='false')  # returns str
        n_screens = self.qsettings.value("graphViewWidget/n_screens", defaultValue=1)
        if window_size:
            self.resize(window_size)
        if window_pos:
            self.move(window_pos)
        if window_state:
            self.restoreState(window_state, version=1)  # Toolbar and dockWidget positions
        if window_maximized == 'true':
            self.setWindowState(Qt.WindowMaximized)
        # noinspection PyArgumentList
        if len(QGuiApplication.screens()) < int(n_screens):
            # There are less screens available now than on previous application startup
            self.move(0, 0)  # Move this widget to primary screen position (0,0)

    def closeEvent(self, event=None):
        """Handle close window.

        Args:
            event (QEvent): Closing event if 'X' is clicked.
        """
        # save qsettings
        self.qsettings.setValue("graphViewWidget/windowSize", self.size())
        self.qsettings.setValue("graphViewWidget/windowPosition", self.pos())
        self.qsettings.setValue("graphViewWidget/windowState", self.saveState(version=1))
        if self.windowState() == Qt.WindowMaximized:
            self.qsettings.setValue("graphViewWidget/windowMaximized", True)
        else:
            self.qsettings.setValue("graphViewWidget/windowMaximized", False)
        self.db_map.close()
        if event:
            event.accept()
