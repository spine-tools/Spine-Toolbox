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

"""
Custom QWidgets.
"""

import os
from PySide6.QtWidgets import (
    QWidget,
    QMenu,
    QToolButton,
    QLabel,
    QGraphicsOpacityEffect,
    QProgressBar,
    QDialogButtonBox,
    QSlider,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtGui import QPainter, QColor, QIcon, QBrush, QPainterPath, QPalette
from PySide6.QtCore import Signal, Slot, QVariantAnimation, QPointF, Qt, QTimeLine
from sqlalchemy.engine.url import URL
from ...helpers import open_url, CharIconEngine, color_from_index


class OpenFileButton(QToolButton):
    """A button to open files or show them in the folder."""

    def __init__(self, file_path, db_editor):
        super().__init__()
        self.db_editor = db_editor
        self.file_path = file_path
        self.dir_name, self.file_name = os.path.split(file_path)
        self.setText(self.file_name)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setStyleSheet(
            """
            QToolButton {
                padding-left: 12px; padding-right: 32px; padding-top: 6px; padding-bottom: 6px;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-style: outset;
                border-radius: 6px;
            }
            QToolButton:hover {
                background-color: #dddddd;
            }
            QToolButton:pressed {
                background-color: #bbbbbb;
                border-style: inset;
            }
            QToolButton::menu-button {
                border: 1px solid #cccccc;
                border-style: outset;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                width: 20px;
            }
            QToolButton::menu-button:pressed {
                border-style: inset;
            }
            """
        )
        menu = QMenu(db_editor)
        self.setMenu(menu)
        open_file_action = menu.addAction("Open")
        open_containing_folder_action = menu.addAction("Open containing folder")
        open_file_action.triggered.connect(self.open_file)
        open_containing_folder_action.triggered.connect(self.open_containing_folder)
        self.clicked.connect(open_file_action.triggered)

    @Slot(bool)
    def open_file(self, checked=False):
        open_url("file:///" + os.path.join(self.dir_name, self.file_path))

    @Slot(bool)
    def open_containing_folder(self, checked=False):
        open_url("file:///" + self.dir_name)


class OpenSQLiteFileButton(OpenFileButton):
    """A button to open sqlite files, show them in the folder, or add them to the project."""

    def __init__(self, file_path, db_editor):
        super().__init__(file_path, db_editor)
        self.url = URL("sqlite", database=self.file_path)

    @Slot(bool)
    def open_file(self, checked=False):
        codename = os.path.splitext(self.file_name)[0]
        self.db_editor._open_sqlite_url(self.url, codename)


class ShootingLabel(QLabel):
    def __init__(self, origin, destination, parent=None, duration=1200):
        super().__init__("foo", parent=parent)
        self.origin = QPointF(origin)
        self.direction = QPointF(destination - origin)
        self.effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.effect)
        self.anim = QVariantAnimation()
        self.anim.setDuration(duration)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self._handle_value_changed)
        self.anim.finished.connect(self.close)
        self.move(origin)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def _handle_value_changed(self, value):
        opacity = 1.0 - abs(2 * value - 1.0)
        self.effect.setOpacity(opacity)
        pos = self.origin + value * self.direction
        self.move(pos.toPoint())

    def show(self):
        self.anim.start(QVariantAnimation.DeleteWhenStopped)
        super().show()


class ProgressBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QHBoxLayout(self)
        self._progress_bar = QProgressBar()
        button_box = QDialogButtonBox()
        button_box.setCenterButtons(True)
        self._previews_button = button_box.addButton("Show previews", QDialogButtonBox.ButtonRole.NoRole)
        self._previews_button.setCheckable(True)
        self._previews_button.toggled.connect(
            lambda checked: self._previews_button.setText(f"{'Hide' if checked else 'Show'} previews")
        )
        self.stop_button = button_box.addButton("Stop", QDialogButtonBox.ButtonRole.NoRole)
        layout.addWidget(self._progress_bar)
        layout.addWidget(button_box)
        self._layout_gen = None

    def set_layout_generator(self, layout_generator):
        if self._layout_gen is not None:
            self._layout_gen.finished.disconnect(self.hide)
            self._layout_gen.progressed.disconnect(self._progress_bar.setValue)
            self._previews_button.toggled.disconnect(self._layout_gen.set_show_previews)
            self.stop_button.clicked.disconnect(self._layout_gen.stop)
        self._layout_gen = layout_generator
        self._progress_bar.setFormat(f"Processing {self._layout_gen.vertex_count} elements...")
        self._progress_bar.setRange(0, self._layout_gen.max_iters + 2)
        self._progress_bar.setValue(0)
        self._previews_button.toggled.connect(self._layout_gen.set_show_previews)
        self.stop_button.clicked.connect(self._layout_gen.stop)
        self._layout_gen.finished.connect(self.hide)
        self._layout_gen.progressed.connect(self._progress_bar.setValue)
        self._layout_gen.progressed.connect(self.show)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(event.rect(), QColor(0, 0, 0, 96))
        painter.end()
        super().paintEvent(event)


class TimeLineWidget(QWidget):
    index_changed = Signal(object)
    _STEP_COUNT = 10000
    _TL_DURATION = 10000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        self._slider = QSlider(Qt.Horizontal)
        self._label = QLabel()
        self._play_pause_button = QToolButton()
        self._play_pause_button.setIcon(QIcon(CharIconEngine("\uf04b")))
        controls = QWidget()
        ctrls_layout = QHBoxLayout(controls)
        ctrls_layout.setContentsMargins(2, 2, 2, 2)
        ctrls_layout.setSpacing(2)
        ctrls_layout.addWidget(self._play_pause_button)
        ctrls_layout.addStretch()
        ctrls_layout.addWidget(self._label)
        layout.addWidget(self._slider)
        layout.addWidget(controls)
        self._slider.setRange(0, self._STEP_COUNT - 1)
        self._min_index = None
        self._max_index = None
        self._index_incr = None
        self._index = None
        self._playback_tl = QTimeLine()
        self._slider.valueChanged.connect(self._handle_value_changed)
        self._slider.sliderMoved.connect(self._playback_tl.stop)
        self._playback_tl.frameChanged.connect(self._slider.setValue)
        self._playback_tl.stateChanged.connect(self._refresh_button_icon)
        self.index_changed.connect(lambda index: self._label.setText(str(index) + "/" + str(self._max_index)))
        self._play_pause_button.clicked.connect(self._play_pause)

    def _refresh_button_icon(self):
        icon_code = "\uf04c" if self._playback_tl.state() is QTimeLine.Running else "\uf04b"
        self._play_pause_button.setIcon(QIcon(CharIconEngine(icon_code)))

    def _play_pause(self):
        if self._playback_tl.state() is QTimeLine.Running:
            self._playback_tl.setPaused(True)
            return
        if self._playback_tl.state() is QTimeLine.Paused:
            self._playback_tl.resume()
            return
        current_value = self._slider.value()
        first_frame = current_value if current_value != self._slider.maximum() else self._slider.minimum()
        self._playback_tl.setFrameRange(first_frame, self._STEP_COUNT - 1)
        self._playback_tl.setDuration(((self._STEP_COUNT - first_frame - 1) / self._STEP_COUNT) * self._TL_DURATION)
        self._playback_tl.start()

    @Slot(int)
    def _handle_value_changed(self, value):
        self._index = self._min_index + value * self._index_incr
        self.index_changed.emit(self._index)

    def set_index_range(self, min_index, max_index):
        self._min_index = min_index
        self._max_index = max_index
        self._index_incr = (max_index - min_index) / self._STEP_COUNT
        self._index = self._min_index
        self.index_changed.emit(self._index)
        self.show()


class LegendWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._layout.setSpacing(2)
        self._layout.setColumnStretch(2, 2)

    def set_legend(self, legend):
        while self._layout.count():
            self._layout.takeAt(0).widget().deleteLater()
        for i, (legend_type, pname, val_range) in enumerate(legend):
            if not val_range:
                continue
            min_val, max_val = val_range
            if min_val == max_val:
                continue
            legend_widget_factory = {"color": _ColorWidget, "arc_width": _WidthWidget}.get(legend_type)
            if legend_widget_factory is None:
                continue
            self._layout.addWidget(QLabel(pname + ": "), i, 0)
            self._layout.addWidget(QLabel(str(min_val)), i, 1, Qt.AlignRight)
            self._layout.addWidget(legend_widget_factory(), i, 2)
            self._layout.addWidget(QLabel(str(max_val)), i, 3)


class _ColorWidget(QWidget):
    def paintEvent(self, ev):
        painter = QPainter(self)
        rect = self.rect()
        width = rect.width()
        for k in range(360):
            rect.setLeft((k / 360) * width)
            color = color_from_index(k, 360)
            painter.fillRect(rect, QBrush(color))


class _WidthWidget(QWidget):
    def paintEvent(self, ev):
        painter = QPainter(self)
        rect = self.rect()
        path = QPainterPath()
        path.moveTo(rect.bottomLeft())
        path.lineTo(rect.topRight())
        path.lineTo(rect.bottomRight())
        painter.fillPath(path, self.palette().color(QPalette.Normal, QPalette.WindowText))
