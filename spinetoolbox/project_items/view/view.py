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
Module for view class.

:authors: P. Savolainen (VTT), M. Marin (KHT), J. Olauson (KTH)
:date:   14.07.2018
"""

import os
from PySide2.QtCore import Qt, Slot
from PySide2.QtGui import QStandardItem, QStandardItemModel, QIcon, QPixmap
from sqlalchemy.engine.url import URL, make_url
from spinedb_api import SpineDBAPIError
from spinetoolbox.project_item import ProjectItem
from spinetoolbox.widgets.data_store_widget import DataStoreForm


class View(ProjectItem):
    def __init__(self, name, description, x, y, toolbox, project, logger):
        """
        View class.

        Args:
            name (str): Object name
            description (str): Object description
            x (float): Initial X coordinate of item icon
            y (float): Initial Y coordinate of item icon
            toolbox (ToolboxUI): a toolbox instance
            project (SpineToolboxProject): the project this item belongs to
            logger (LoggerInterface): a logger instance
        """
        super().__init__(name, description, x, y, project, logger)
        self._ds_views = {}
        self._references = dict()
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
        s[self._properties_ui.pushButton_view_open_ds_view.clicked] = self.open_view
        return s

    def restore_selections(self):
        """Restore selections into shared widgets when this project item is selected."""
        self._properties_ui.label_view_name.setText(self.name)
        self._properties_ui.treeView_view.setModel(self.reference_model)

    def save_selections(self):
        """Save selections in shared widgets for this project item into instance variables."""
        self._properties_ui.treeView_view.setModel(None)

    @Slot(bool)
    def open_view(self, checked=False):
        """Opens references in a view window.
        """
        indexes = self._selected_indexes()
        database_urls = self._database_urls(indexes)
        if not database_urls:
            return
        db_urls = [str(x[0]) for x in database_urls]
        # Mangle database paths to get a hashable string identifying the view window.
        view_id = ";".join(sorted(db_urls))
        if self._restore_existing_view_window(view_id):
            return
        view_window = self._make_view_window(database_urls)
        if not view_window:
            return
        view_window.show()
        view_window.destroyed.connect(lambda: self._ds_views.pop(view_id))
        self._ds_views[view_id] = view_window

    def populate_reference_list(self):
        """Populates reference list."""
        self.reference_model.clear()
        self.reference_model.setHorizontalHeaderItem(0, QStandardItem("References"))  # Add header
        for db in sorted(self._references, reverse=True):
            qitem = QStandardItem(db)
            qitem.setFlags(~Qt.ItemIsEditable)
            qitem.setData(self._spine_ref_icon, Qt.DecorationRole)
            self.reference_model.appendRow(qitem)

    def update_name_label(self):
        """Update View tab name label. Used only when renaming project items."""
        self._properties_ui.label_view_name.setText(self.name)

    def execute_forward(self, resources):
        """see base class"""
        self._update_references_list(resources)
        return True

    def _do_handle_dag_changed(self, resources):
        """Update the list of references that this item is viewing."""
        self._update_references_list(resources)

    def _update_references_list(self, resources_upstream):
        """Updates the references list with resources upstream.

        Args:
            resources_upstream (list): ProjectItemResource instances
        """
        self._references.clear()
        for resource in resources_upstream:
            if resource.type_ == "database" and resource.scheme == "sqlite":
                url = make_url(resource.url)
                self._references[url.database] = (url, resource.provider.name)
            elif resource.type_ == "file":
                filepath = resource.path
                if os.path.splitext(filepath)[1] == '.sqlite':
                    url = URL("sqlite", database=filepath)
                    self._references[url.database] = (url, resource.provider.name)
        self.populate_reference_list()

    def _selected_indexes(self):
        """Returns selected indexes."""
        selection_model = self._properties_ui.treeView_view.selectionModel()
        if not selection_model.hasSelection():
            self._properties_ui.treeView_view.selectAll()
        return self._properties_ui.treeView_view.selectionModel().selectedRows()

    def _database_urls(self, indexes):
        """Returns list of tuples (url, provider) for given indexes."""
        return [self._references[index.data(Qt.DisplayRole)] for index in indexes]

    def _restore_existing_view_window(self, view_id):
        """Restores an existing view window and returns True if the operation was successful."""
        if view_id not in self._ds_views:
            return False
        view_window = self._ds_views[view_id]
        if view_window.windowState() & Qt.WindowMinimized:
            view_window.setWindowState(view_window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        view_window.activateWindow()
        return True

    def _make_view_window(self, db_maps):
        try:
            return DataStoreForm(self._project.db_mngr, *db_maps)
        except SpineDBAPIError as e:
            self._logger.msg_error.emit(e.msg)

    def tear_down(self):
        """Tears down this item. Called by toolbox just before closing. Closes all view windows."""
        for view in self._ds_views.values():
            view.close()

    def notify_destination(self, source_item):
        """See base class."""
        if source_item.item_type() == "Tool":
            self._logger.msg.emit(
                "Link established. You can visualize the ouput from Tool "
                f"<b>{source_item.name}</b> in View <b>{self.name}</b>."
            )
        elif source_item.item_type() == "Data Store":
            self._logger.msg.emit(
                "Link established. You can visualize Data Store "
                f"<b>{source_item.name}</b> in View <b>{self.name}</b>."
            )
        else:
            super().notify_destination(source_item)

    @staticmethod
    def default_name_prefix():
        """see base class"""
        return "View"
