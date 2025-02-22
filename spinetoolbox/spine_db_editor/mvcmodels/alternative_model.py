######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# Copyright Spine Toolbox contributors
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""Contains alternative tree model."""
from collections import defaultdict
import pickle
from PySide6.QtCore import QByteArray, QMimeData
from . import mime_types
from .alternative_item import DBItem
from .tree_model_base import TreeModelBase
from .utils import two_column_as_csv


class AlternativeModel(TreeModelBase):
    """A model to display alternatives in a tree view."""

    def _make_db_item(self, db_map):
        return DBItem(self, db_map, self.db_mngr.name_registry)

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
        d = defaultdict(list)
        # We have two columns and consequently usually twice the same item per row.
        # Make items unique without losing order using a dictionary trick.
        items = list(dict.fromkeys(self.item_from_index(ind) for ind in indexes))
        for item in items:
            db_item = item.parent_item
            db_key = self.db_mngr.db_map_key(db_item.db_map)
            d[db_key].append(item.name)
        mime = QMimeData()
        mime.setText(two_column_as_csv(indexes))
        mime.setData(mime_types.ALTERNATIVE_DATA, QByteArray(pickle.dumps(d)))
        return mime

    def paste_alternative_mime_data(self, mime_data, database_item):
        """Pastes alternatives from mime data into model.

        Args:
            mime_data (QMimeData): mime data
            database_item (alternative_item.DBItem): target database item
        """
        alternative_data = pickle.loads(mime_data.data(mime_types.ALTERNATIVE_DATA).data())
        names_to_descriptions = {}
        for db_key in alternative_data:
            db_map = self.db_mngr.db_map_from_key(db_key)
            items = self.db_mngr.get_items(db_map, "alternative")
            names_to_descriptions.update({i["name"]: i["description"] for i in items})
        existing_names = {item["name"] for item in self.db_mngr.get_items(database_item.db_map, "alternative")}
        alternative_db_items = []
        for name, description in names_to_descriptions.items():
            if name in existing_names:
                continue
            alternative_db_items.append({"name": name, "description": description})
        if alternative_db_items:
            self.db_mngr.add_alternatives({database_item.db_map: alternative_db_items})
