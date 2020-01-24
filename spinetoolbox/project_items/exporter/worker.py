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
A worker based machinery to construct the settings data structures needed for gdx export outside the UI loop.

:author: A. Soininen (VTT)
:date:   19.12.2019
"""

from PySide2.QtCore import QThread, Signal
from spinedb_api import DatabaseMapping
from spinetoolbox.spine_io.exporters import gdx


class Worker(QThread):
    """A worker thread to construct export settings for a database."""

    errored = Signal(str, "QVariant")
    """Emitted when an error occurs."""
    finished = Signal(str)
    """Emitted when the worker has finished."""
    indexing_settings_read = Signal(str, "QVariant")
    """Sends the indexing settings away."""
    settings_read = Signal(str, "QVariant")
    """Sends the settings away."""

    def __init__(self, database_url):
        """
        Args:
            database_url (str): database's URL
        """
        super().__init__()
        self._database_url = str(database_url)

    def run(self):
        """Constructs settings and parameter index settings and sends them away using signals."""
        database_map = DatabaseMapping(self._database_url)
        try:
            if not self.isInterruptionRequested():
                settings = gdx.make_settings(database_map)
            if not self.isInterruptionRequested():
                indexing_settings = gdx.make_indexing_settings(database_map)
        except gdx.GdxExportException as error:
            self.errored.emit(self._database_url, error)
            return
        finally:
            database_map.connection.close()
        if not self.isInterruptionRequested():
            self.settings_read.emit(self._database_url, settings)
            self.indexing_settings_read.emit(self._database_url, indexing_settings)
        self.finished.emit(self._database_url)
