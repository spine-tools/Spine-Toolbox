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
Classes to show db session history

:author: M. Marin (KTH)
:date:   5.2.2020
"""

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QColumnView, QDialog, QVBoxLayout
from PySide2.QtGui import QStandardItemModel, QStandardItem


class DBSessionHistoryModel(QStandardItemModel):
    def __init__(self, parent, db_mngr, *db_maps):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps

    def build(self):
        for db_map in self.db_maps:
            db_map_item = QStandardItem(db_map.codename)
            self.appendRow(db_map_item)
            for cmd in self.db_mngr.undo_stack[db_map].commands():
                cmd_item = QStandardItem(cmd.text())
                db_map_item.appendRow(cmd_item)
                for key, items in cmd.data().items():
                    key_item = QStandardItem(str(key))
                    cmd_item.appendRow(key_item)
                    for item in items:
                        key_item.appendRow(QStandardItem(item))


class DBSessionHistoryView(QColumnView):
    def __init__(self, parent, db_mngr, *db_maps):
        super().__init__(parent)
        self.db_mngr = db_mngr
        self.db_maps = db_maps
        self.model = DBSessionHistoryModel(self, db_mngr, *db_maps)
        self.setModel(self.model)
        self.model.build()
        self.setColumnWidths([150, 250, 200, 250])


class DBSessionHistoryDialog(QDialog):
    def __init__(self, parent, db_mngr, *db_maps):
        """Initialize class"""
        super().__init__(parent)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Session history')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self.history_view = DBSessionHistoryView(self, db_mngr, *db_maps)
        layout.addWidget(self.history_view)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setMinimumWidth(850)
