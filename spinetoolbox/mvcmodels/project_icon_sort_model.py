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
Contains a filter proxy model.

:authors: P. Savolainen (VTT)
:date:   28.6.2019
"""

import logging
import os
from PySide2.QtCore import Qt, QSortFilterProxyModel
from PySide2.QtWidgets import QFileIconProvider
from PySide2.QtGui import QIcon


class ProjectDirectoryIconFilterProxyModel(QSortFilterProxyModel):
    """Filter proxy model for switching the directory icon in Open Project..QFileDialog."""

    def __init__(self, parent):
        super().__init__(parent)

    def filterAcceptsRow(self, source_row, source_parent):
        """Overridden method. Returns True if the item in the row indicated by the given source_row and source_parent
        should be included in the model. Otherwise Returns False.

        Args:
            source_row (int): Source row number
            source_parent (QModelIndex): Index of parent

        Returns:
            bool: See title.
        """
        file_model = self.sourceModel()  # QFileSystemModel from QDialog
        index = file_model.index(source_row, 0, source_parent)
        if file_model.isDir(index):
            path = file_model.filePath(index)
            # logging.debug("Processing: {0}".format(path))
            if os.path.isdir(os.path.abspath(os.path.join(path, ".spinetoolbox"))):
                # file_model.setData(index, "Pekka", role=Qt.DisplayRole)
                logging.debug("Found project directory:{0}".format(path))

            return True
        else:
            return False


class ProjectDirectoryIconProvider(QFileIconProvider):

    def __init__(self):
        super().__init__()
        self.spine_icon = QIcon(":/symbols/Spine_symbol.png")

    def icon(self, info):
        """Returns an icon for the file described by info.

        Args:
            info (QFileInfo): File (or directory) info

        Returns:
            QIcon: Icon for a file system resource with the given info
        """
        if info.__class__() == QFileIconProvider.IconType:
            return super().icon(info)  # Because there are two icon() methods
        if not info.isDir():
            return super().icon(info)
        p = info.filePath()
        # logging.debug("In dir:{0}".format(p))
        if os.path.exists(os.path.join(p, ".spinetoolbox")):
            # logging.debug("found project dir:{0}".format(p))
            return self.spine_icon
        else:
            return super().icon(info)
