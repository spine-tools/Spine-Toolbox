######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Contains machinery to deal with metadata editor.

:author: A. Soininen (VTT)
:date:   7.2.2022
"""
from PySide2.QtCore import QModelIndex, Qt
from ..mvcmodels.metadata_table_model import MetadataTableModel


class MetadataEditor:
    def __init__(self, metadata_table_view, db_editor, db_mngr):
        """
        Args:
            metadata_table_view (MetadataTableView): editor's view
            db_editor (SpineDBEditor) database editor
            db_mngr (SpineDBManager): database manager
        """
        self._db_editor = db_editor
        self._metadata_table_view = metadata_table_view
        self._metadata_table_model = MetadataTableModel(db_mngr, db_editor.db_maps, self._metadata_table_view)
        self._metadata_table_view.sortByColumn(-1, Qt.AscendingOrder)
        self._metadata_table_view.setModel(self._metadata_table_model)
        self._metadata_table_view.connect_spine_db_editor(db_editor)

    def connect_signals(self, ui):
        self._metadata_table_model.msg_error.connect(self._db_editor.msg_error)

    def init_models(self, db_maps):
        self._metadata_table_model.set_db_maps(db_maps)
        self._metadata_table_model.fetchMore(QModelIndex())

    def add_metadata(self, db_map_data):
        self._metadata_table_model.add_metadata(db_map_data)

    def update_metadata(self, db_map_data):
        self._metadata_table_model.update_metadata(db_map_data)

    def remove_metadata(self, db_map_data):
        self._metadata_table_model.remove_metadata(db_map_data)

    def roll_back(self, db_maps):
        self._metadata_table_model.roll_back(db_maps)
