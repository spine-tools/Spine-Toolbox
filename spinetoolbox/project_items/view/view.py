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
Module for view class.

:authors: P. Savolainen (VTT), M. Marin (KHT), J. Olauson (KTH)
:date:   14.07.2018
"""

import os
import logging
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon, QPixmap
from sqlalchemy.engine.url import URL, make_url
from spinedb_api import SpineDBAPIError
from spinetoolbox.project_item import ProjectItem
from spinetoolbox.widgets.graph_view_widget import GraphViewForm
from spinetoolbox.widgets.tabular_view_widget import TabularViewForm
from spinetoolbox.widgets.tree_view_widget import TreeViewForm
from spinetoolbox.executioner import ExecutionState


class View(ProjectItem):
    def __init__(self, toolbox, name, description, x, y):
        """
        View class.

        Args:
            toolbox (ToolboxUI): QMainWindow instance
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
        """
        super().__init__(toolbox, name, description, x, y)
        self._graph_views = {}
        self._tabular_views = {}
        self._tree_views = {}
        self._references = list()
        self.reference_model = QStandardItemModel()  # References to databases
        self._spine_ref_icon = QIcon(QPixmap(":/icons/Spine_db_ref_icon.png"))

    @staticmethod
    def item_type():
        """See base class."""
        return "View"

    @staticmethod
    def category():
        """See base class."""
        return "Views"

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers.
        This is to enable simpler connecting and disconnecting."""
        s = super().make_signal_handler_dict()
        s[self._properties_ui.toolButton_view_open_dir.clicked] = lambda checked=False: self.open_directory()
        s[self._properties_ui.pushButton_view_open_graph_view.clicked] = self.open_graph_view_btn_clicked
        s[self._properties_ui.pushButton_view_open_tabular_view.clicked] = self.open_tabular_view_btn_clicked
        s[self._properties_ui.pushButton_view_open_tree_view.clicked] = self.open_tree_view_btn_clicked
        return s

    def activate(self):
        """Restore selections and connect signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Save selections and disconnect signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed", self.name)
            return False
        return True

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._properties_ui.label_view_name.setText(self.name)
        self._properties_ui.treeView_view.setModel(self.reference_model)

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        self._properties_ui.treeView_view.setModel(None)

    def references(self):
        """Returns a list of url strings that are in this item as references."""
        return self._references

    @Slot(bool)
    def open_graph_view_btn_clicked(self, checked=False):
        """Slot for handling the signal emitted by clicking on 'Graph view' button."""
        self._open_view("graph", supports_multiple_databases=False)

    @Slot(bool)
    def open_tabular_view_btn_clicked(self, checked=False):
        """Slot for handling the signal emitted by clicking on 'Tabular view' button."""
        self._open_view("tabular", supports_multiple_databases=False)

    @Slot(bool)
    def open_tree_view_btn_clicked(self, checked=False):
        """Slot for handling the signal emitted by clicking on 'Tree view' button."""
        self._open_view("tree", supports_multiple_databases=True)

    def _open_view(self, view, supports_multiple_databases):
        """Opens references in a view window.

        Args:
            view (str): either "tree", "graph", or "tabular"
            supports_multiple_databases (bool): True if the view supports more than one database
        """
        view_store = {"graph": self._graph_views, "tabular": self._tabular_views, "tree": self._tree_views}[view]
        indexes = self._selected_indexes()
        database_urls = self._database_urls(indexes)
        if not database_urls:
            return
        db_urls = [str(x[0]) for x in database_urls]
        # Mangle database paths to get a hashable string identifying the view window.
        view_id = ";".join(sorted(db_urls))
        if not supports_multiple_databases and len(database_urls) > 1:
            # Currently, Graph and Tabular views do not support multiple databases.
            # This if clause can be removed once that support has been implemented.
            self._toolbox.msg_error.emit("Selected view does not support multiple databases.")
            return
        if self._restore_existing_view_window(view_id, view_store):
            return
        view_window = self._make_view_window(view, database_urls)
        if not view_window:
            return
        view_window.show()
        view_window.destroyed.connect(lambda: view_store.pop(view_id))
        view_store[view_id] = view_window

    def populate_reference_list(self, items):
        """Add given list of items to the reference model. If None or
        an empty list given, the model is cleared."""
        self.reference_model.clear()
        self.reference_model.setHorizontalHeaderItem(0, QStandardItem("References"))  # Add header
        sorted_dbs = sorted([item.database for item in items], reverse=True)
        for db in sorted_dbs:
            qitem = QStandardItem(db)
            qitem.setFlags(~Qt.ItemIsEditable)
            qitem.setData(self._spine_ref_icon, Qt.DecorationRole)
            self.reference_model.appendRow(qitem)

    def update_name_label(self):
        """Update View tab name label. Used only when renaming project items."""
        self._properties_ui.label_view_name.setText(self.name)

    def stop_execution(self):
        """Stops executing this View."""
        self._toolbox.msg.emit("Stopping {0}".format(self.name))

    def _do_execute(self, resources_upstream, resources_downstream):
        """Executes this item."""
        self._update_references_list(resources_upstream)
        return ExecutionState.CONTINUE

    def _do_handle_dag_changed(self, resources_upstream):
        """Update the list of references that this item is viewing."""
        self._update_references_list(resources_upstream)

    def _update_references_list(self, resources_upstream):
        """Updates the references list with resources upstream.

        Args:
            resources_upstream (list): ProjectItemResource instances
        """
        self._references.clear()
        for resource in resources_upstream:
            if resource.type_ == "database" and resource.scheme == "sqlite":
                self._references.append((make_url(resource.url), resource.provider.name))
            elif resource.type_ == "file" and resource.metadata.get("is_output"):
                filepath = resource.path
                if os.path.splitext(filepath)[1] == '.sqlite':
                    url = URL("sqlite", database=filepath)
                    self._references.append((url, resource.provider.name))
        self.populate_reference_list([url for url, _ in self._references])

    def _selected_indexes(self):
        """Returns selected indexes."""
        selection_model = self._properties_ui.treeView_view.selectionModel()
        if not selection_model.hasSelection():
            self._properties_ui.treeView_view.selectAll()
        return self._properties_ui.treeView_view.selectionModel().selectedRows()

    def _database_urls(self, indexes):
        """Returns list of tuples (url, provider) for given indexes."""
        return [self._references[index.row()] for index in indexes]

    @staticmethod
    def _restore_existing_view_window(view_id, view_store):
        """Restores an existing view window and returns True if the operation was successful."""
        if view_id not in view_store:
            return False
        view_window = view_store[view_id]
        if view_window.windowState() & Qt.WindowMinimized:
            view_window.setWindowState(view_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        view_window.activateWindow()
        return True

    def _make_view_window(self, view, db_maps):
        make_view = {"graph": GraphViewForm, "tabular": TabularViewForm, "tree": TreeViewForm}.get(view)
        if not make_view:
            raise RuntimeError("view must be 'tree', 'graph', or 'tabular'")
        kwargs = {"graph": {"read_only": True}}.get(view, {})
        try:
            return make_view(self._project, *db_maps, **kwargs)
        except SpineDBAPIError as e:
            self._toolbox.msg_error.emit(e.msg)

    def tear_down(self):
        """Tears down this item. Called by toolbox just before closing. Closes all view windows."""
        for view in self._graph_views.values():
            view.close()
        for view in self._tabular_views.values():
            view.close()
        for view in self._tree_views.values():
            view.close()

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Tool":
            self._toolbox.msg.emit(
                "Link established. You can visualize the ouput from Tool "
                "<b>{0}</b> in View <b>{1}</b>.".format(source_item.name, self.name)
            )
        elif source_item.item_type() == "Data Store":
            self._toolbox.msg.emit(
                "Link established. You can visualize Data Store "
                "<b>{0}</b> in View <b>{1}</b>.".format(source_item.name, self.name)
            )
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "View"
