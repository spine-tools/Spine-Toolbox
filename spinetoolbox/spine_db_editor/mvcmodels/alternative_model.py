######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################
"""Contains alternative tree model."""
import csv
import pickle
from io import StringIO

from PySide6.QtCore import QMimeData
from .tree_model_base import TreeModelBase
from .alternative_item import DBItem
from .utils import two_column_as_csv
from . import mime_types


class AlternativeModel(TreeModelBase):
    """A model to display alternatives in a tree view."""

    @staticmethod
    def _make_db_item(db_map):
        return DBItem(db_map)

    @staticmethod
    def _top_children():
        return []

    def mimeData(self, indexes):
        """Stores selected indexes into MIME data.

        The MIME data structure contains two distinct data:

        - Text representation of the selection
        - A pickled dict mapping db identifier to list of alternative ids

        Args:
            indexes (Sequence of QModelIndex): selected indexes

        Returns:
            QMimeData: MIME data
        """
        d = {}
        # We have two columns and consequently usually twice the same item per row.
        # Make items unique without losing order using a dictionary trick.
        items = list(dict.fromkeys(self.item_from_index(ind) for ind in indexes))
        for item in items:
            db_item = item.parent_item
            db_key = self.db_mngr.db_map_key(db_item.db_map)
            d.setdefault(db_key, []).append(item.id)
        mime = QMimeData()
        mime.setText(two_column_as_csv(indexes))
        mime.setData(mime_types.ALTERNATIVE_DATA, pickle.dumps(d))
        return mime
