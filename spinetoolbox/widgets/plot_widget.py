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

"""A Qt widget showing a toolbar and a matplotlib plotting canvas."""
from pathlib import Path
import tempfile

from PySide6.QtCore import QMetaObject, Qt, QUrl, QSize, Slot
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QVBoxLayout, QWidget


class PlotWidget(QWidget):
    """
    A widget that contains a toolbar and a plotting canvas.

    Attributes:
        canvas (PlotCanvas): the plotting canvas
    """

    plot_windows = {}
    """A global list of plot windows."""

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self.canvas = QWebEngineView()
        self.html_path = tempfile.NamedTemporaryFile(suffix=".html")
        print(self)
        print(self.html_path.name)
        self.canvas.setUrl(QUrl.fromLocalFile(self.html_path.name))
        self._layout.addWidget(self.canvas)
        self.resize(QSize(900, 600))
        self.canvas.page().profile().downloadRequested.connect(self.save_as_prompt)
        QMetaObject.connectSlotsByName(self)

    def write(self, html_content: str):
        Path(self.html_path.name).write_bytes(bytes(html_content, "utf8"))
        self.canvas.reload()

    @Slot(QWebEngineDownloadRequest)
    def save_as_prompt(self, download: QWebEngineDownloadRequest):
        default_dir = download.downloadDirectory()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", default_dir, "Images (*.svg *.png *.jpg)")
        if path:
            download.setDownloadFileName(path)
            download.accept()
