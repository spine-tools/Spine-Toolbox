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
Tool class.

:author: A. Soininen (VTT)
:date:   5.9.2019
"""

import logging
import os.path
from PySide2.QtGui import QIcon, QPixmap
from spinedb_api import DatabaseMapping
from data_store import DataStore
from graphics_items import GdxExportIcon
from helpers import create_dir
from project_item import ProjectItem
from spine_io.exporters import gdx
from widgets.gdx_export_settings import GdxExportSettings
from widgets.export_list_item import ExportListItem


class GdxExport(ProjectItem):
    """
    This project item handles all functionality regarding exporting a database to .gdx file.

    Attributes:
        toolbox (ToolboxUI): a ToolboxUI instance
        name (str): item name
        description (str): item description
        database_urls (list): a list of connected database urls
        database_to_file_name_map (dict): mapping from database path (str) to an output file name (str)
        x (int): initial X coordinate of item icon
        y (int): initial Y coordinate of item icon
    """
    def __init__(self, toolbox, name, description, database_urls=None, database_to_file_name_map=None, x=0.0, y=0.0):
        super().__init__(toolbox, name, description)
        self.item_type = "Gdx Export"
        self._settings_window = None
        self._database_urls = database_urls if database_urls is not None else list()
        self._database_to_file_name_map = database_to_file_name_map if database_to_file_name_map is not None else dict()
        self.spine_ref_icon = QIcon(QPixmap(":/icons/Spine_db_ref_icon.png"))
        # Make project directory for this View
        self.data_dir = os.path.join(self._toolbox.project().project_dir, self.short_name)
        try:
            create_dir(self.data_dir)
        except OSError:
            self._toolbox.msg_error.emit(
                "[OSError] Creating directory {0} failed." " Check permissions.".format(self.data_dir)
            )
        self._graphics_item = GdxExportIcon(self._toolbox, x - 35, y - 35, 70, 70, self.name)
        self._sigs = self.make_signal_handler_dict()

    @property
    def database_urls(self):
        return self._database_urls

    @property
    def database_to_file_name_map(self):
        return self._database_to_file_name_map

    def make_signal_handler_dict(self):
        """Returns a dictionary of all shared signals and their handlers."""
        s = {
            self._toolbox.ui.toolButton_gdx_export_open_dir.clicked: lambda checked: self.open_directory(checked)
        }
        return s

    def activate(self):
        """Restores selections and connects signals."""
        self.restore_selections()
        super().connect_signals()

    def deactivate(self):
        """Saves selections and disconnects signals."""
        self.save_selections()
        if not super().disconnect_signals():
            logging.error("Item %s deactivation failed.", self.name)
            return False
        return True

    def save_selections(self):
        """Saves selections in shared widgets for this project item into instance variables."""

    def restore_selections(self):
        """Restores selections into shared widgets when this project item is selected."""
        self._toolbox.ui.label_gdx_export_name.setText(self.name)
        self.link_changed()
        database_list_storage = self._toolbox.ui.gdx_export_databases_list_layout
        while not database_list_storage.isEmpty():
            widget_to_remove = database_list_storage.takeAt(0)
            widget_to_remove.widget().deleteLater()
        for row, url in enumerate(self._database_urls):
            url = url["database"]
            file_name = self._database_to_file_name_map.get(url, '')
            item = ExportListItem(url, file_name)
            database_list_storage.insertWidget(0, item)
            item.settings_button.clicked.connect(lambda checked: self.__show_settings(url))
            item.out_file_name_edit.textChanged.connect(lambda text: self.__update_out_file_name(text, url))

    def link_changed(self):
        """Updates the list of files that this item is exporting."""
        self._database_urls.clear()
        for input_item in self._toolbox.connection_model.input_items(self.name):
            found_index = self._toolbox.project_item_model.find_item(input_item)
            if not found_index:
                self._toolbox.msg_error.emit("Item {0} not found. Something is seriously wrong.".format(input_item))
                continue
            item = self._toolbox.project_item_model.project_item(found_index)
            if not isinstance(item, DataStore):
                continue
            self._database_urls.append(item.url())

    def data_files(self):
        """Returns a list of exported file names."""
        return list()

    def execute(self):
        """Executes this Tool."""
        if not gdx.available():
            self._toolbox.msg_error.emit('No GAMS Python bindings installed. GDX export is disabled.')
            abort = -1
            self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(abort)
            return
        self._toolbox.msg.emit("")
        self._toolbox.msg.emit("Executing Gdx Export <b>{}</b>".format(self.name))
        self._toolbox.msg.emit("***")
        for url in self._database_urls:
            db_map = DatabaseMapping(url["dialect"] + ":///" + url["database"], username=url["username"])
            domains = gdx.object_classes_to_domains(db_map)
            sets = gdx.relationship_classes_to_sets(db_map)
            gams_workspace = gdx.make_gams_workspace()
            gams_database = gdx.make_gams_database(gams_workspace)
            gams_domains = gdx.domains_to_gams(gams_database, domains)
            gdx.sets_to_gams(gams_database, sets, gams_domains)
            out_path = os.path.join(self.data_dir, self._database_to_file_name_map[url["database"]])
            gdx.export_to_gdx(gams_database, out_path)
        success = 0
        self._toolbox.project().execution_instance.project_item_execution_finished_signal.emit(success)

    def stop_execution(self):
        """Stops executing this Tool."""

    def __show_settings(self, database_url):
        """Opens the item's settings window."""
        if self._settings_window is None:
            self._settings_window = GdxExportSettings(self._toolbox)
        self._settings_window.show()

    def __update_out_file_name(self, file_name, url):
        self._database_to_file_name_map[url] = file_name

    def item_dict(self):
        """Returns a dictionary corresponding to this item."""
        d = super().item_dict()
        d["database_urls"] = self._database_urls
        d["database_to_file_name_map"] = self._database_to_file_name_map
        return d
