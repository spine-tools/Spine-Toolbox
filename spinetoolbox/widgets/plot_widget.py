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


class PlotWidget(QWidget):
    """Plotting widget, w/ a webview canvas, and a webchannel.

    Attributes:
        canvas (QWebEngineView): webview plotting canvas

        html_path (NamedTemporaryFile): managed temporary HTML file rendered by the canvas.

        channel (WebChannel): webchannel for communication from javascript

    """

    def __init__(self, parent=None):
        """
        Args:
            parent (QWidget, optional): parent widget
        """
        super().__init__(parent)

        self._layout = QVBoxLayout(self)
        self.canvas = QWebEngineView()
        self.html_path = tempfile.NamedTemporaryFile(suffix=".html")
        self.canvas.setUrl(QUrl.fromLocalFile(self.html_path.name))
        self._layout.addWidget(self.canvas)
        self.resize(QSize(900, 600))

        # save plot as image
        self.canvas.page().profile().downloadRequested.connect(self.save_as_prompt)

        # Set up QWebChannel so JavaScript can call back into Python
        self._bridge = DownloadBridge(self)
        self._channel = WebChannel("plot_widget", self._bridge)
        self._channel.setup_js_api(self.canvas)

        QMetaObject.connectSlotsByName(self)

    @property
    def dataframe(self) -> pd.DataFrame:
        """Underlying dataframe for the plot, only used for export."""
        if self._df is None:
            raise RuntimeError("underlying dataframe not set, cannot export data")
        return self._df

    @dataframe.setter
    def dataframe(self, df: pd.DataFrame):
        self._df = df

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
            filter="Images (*.svg *.png *.jpg)",
        )
        if path:
            download.setDownloadFileName(path)
            download.accept()


class DownloadBridge(QObject):
    """QWebChannel bridge exposed via JavaScript for CSV download."""

    def __init__(self, plot_widget):
        super().__init__()
        self._plot = plot_widget

    @Slot(str)
    def downloadFilteredCsv(self, visible_keys_json: str):
        """Called from JavaScript with the list of currently visible legend labels.

        Filters the stored DataFrame to include only the data series that are
        visible in the plot (i.e. not toggled off via the legend), then prompts
        the user to save as CSV.
        """
        match json.loads(visible_keys_json):
            case ([] | ["ALL"]) as visible_keys:
                # - all legend items are hidden, export all w/ warning (FIXME)
                # - first value is "ALL" when no legend is present, e.g. bar charts
                filtered = self._plot.dataframe
            case [str(), *_] as visible_keys:
                filtered = self._plot.dataframe.query("|".join(visible_keys))
                if filtered.empty:
                    # FIXME: warn user
                    filtered = self._plot.dataframe
            case keys:
                raise RuntimeError(f"webchannel returned {keys}, something went terribly wrong!")

        download_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation))
        path, _ = QFileDialog.getSaveFileName(
            self._plot, caption="Save Data as CSV", dir=str(download_dir / "plot_data.csv"), filter="CSV Files (*.csv)"
        )
        if path:
            filtered.to_csv(path, index=False, sep=",", header=True)


class WebChannel(QWebChannel):
    def __init__(self, name: str, obj: QObject, parent: QObject | None = None):
        super().__init__(parent)
        self._name = name
        self.registerObject(name, obj)

    def setup_js_api(self, webview: QWebEngineView):
        # Inject qwebchannel.js (shipped with Qt) so the page can use QWebChannel
        qwebchannel_script = QWebEngineScript()
        qwebchannel_script.setName("qwebchannel")
        qwebchannel_script.setSourceUrl(QUrl("qrc:///qtwebchannel/qwebchannel.js"))
        qwebchannel_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentCreation)
        qwebchannel_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        webview.page().scripts().insert(qwebchannel_script)

        # Inject a small init script that establishes the bridge on window.bridge
        init_script = QWebEngineScript()
        init_script.setName("bridge_init")
        init_script.setSourceCode(
            "new QWebChannel(qt.webChannelTransport, function(channel) {"
            f"    window.bridge = channel.objects.{self._name};"
            "});"
        )
        init_script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        init_script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        webview.page().scripts().insert(init_script)
        webview.page().setWebChannel(self)
