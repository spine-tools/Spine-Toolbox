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

"""A Qt widget showing a toolbar and a plotting canvas."""
import json
from pathlib import Path
import tempfile

import pandas as pd
from PySide6.QtCore import QMetaObject, QObject, QStandardPaths, Qt, QUrl, QSize, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QVBoxLayout, QWidget


class DownloadBridge(QObject):
    """Bridge object exposed to JavaScript via QWebChannel for on-demand CSV download."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: pd.DataFrame | None = None
        self._parent_widget: QWidget | None = None

    def set_data(self, data: pd.DataFrame):
        """Store the DataFrame to be exported on demand."""
        self._data = data

    def set_parent_widget(self, widget: QWidget):
        """Set the parent widget for file dialogs."""
        self._parent_widget = widget

    @Slot(str)
    def downloadFilteredCsv(self, visible_keys_json: str):
        """Called from JavaScript with the list of currently visible legend labels.

        Filters the stored DataFrame to include only the data series that are
        visible in the plot (i.e. not toggled off via the legend), then prompts
        the user to save as CSV.
        """
        if self._data is None:
            return
        visible_keys = json.loads(visible_keys_json)
        if not visible_keys:
            # All legend items are hidden — nothing to export
            return

        # Legend labels are formatted as "col=value"; strip the prefix to get raw values
        raw_values = [k.split("=", 1)[1] if "=" in k else k for k in visible_keys]

        filter_col = self._data.columns[0]
        filtered = self._data[self._data[filter_col].astype(str).isin(raw_values)]

        if filtered.empty:
            # No match after filtering (e.g. single-series plot with key "value") — export all data
            filtered = self._data

        csv_text = filtered.to_csv(index=False, sep=",", header=True)
        path, _ = QFileDialog.getSaveFileName(
            self._parent_widget,
            caption="Save Data as CSV",
            dir=str(Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)) / "plot_data.csv"),
            filter="CSV Files (*.csv)",
        )
        if path:
            Path(path).write_text(csv_text, encoding="utf-8")


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

        # Set up QWebChannel so JavaScript can call back into Python
        self._bridge = DownloadBridge(self)
        self._bridge.set_parent_widget(self)
        self._channel = QWebChannel(self)
        self._channel.registerObject("bridge", self._bridge)
        self.canvas.page().setWebChannel(self._channel)

        # Inject qwebchannel.js (shipped with Qt) so the page can use QWebChannel
        qwebchannel_script = QWebEngineScript()
        qwebchannel_script.setName("qwebchannel")
        qwebchannel_script.setSourceUrl(QUrl("qrc:///qtwebchannel/qwebchannel.js"))
        qwebchannel_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        qwebchannel_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        self.canvas.page().scripts().insert(qwebchannel_script)

        # Inject a small init script that establishes the bridge on window.bridge
        init_script = QWebEngineScript()
        init_script.setName("bridge_init")
        init_script.setSourceCode(
            "new QWebChannel(qt.webChannelTransport, function(channel) {"
            "    window.bridge = channel.objects.bridge;"
            "});"
        )
        init_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        init_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        self.canvas.page().scripts().insert(init_script)

        self.canvas.setUrl(QUrl.fromLocalFile(self.html_path.name))
        self._layout.addWidget(self.canvas)
        self.resize(QSize(900, 600))
        self.canvas.page().profile().downloadRequested.connect(self.save_as_prompt)
        QMetaObject.connectSlotsByName(self)

    def set_download_data(self, data: pd.DataFrame):
        """Set the DataFrame that will be exported when the user clicks the CSV download button."""
        self._bridge.set_data(data)

    def write(self, html_content: str):
        Path(self.html_path.name).write_bytes(bytes(html_content, "utf8"))
        self.canvas.reload()

    @Slot(QWebEngineDownloadRequest)
    def save_as_prompt(self, download: QWebEngineDownloadRequest):
        download_dir: Path = Path(download.downloadDirectory())
        path, _ = QFileDialog.getSaveFileName(
                self,
                caption="Save File",
                dir=str(download_dir / download.suggestedFileName()),
                filter="Images (*.svg *.png *.jpg)")
        if path:
            download.setDownloadFileName(path)
            download.accept()
