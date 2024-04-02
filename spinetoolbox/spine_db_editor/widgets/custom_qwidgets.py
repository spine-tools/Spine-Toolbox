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

"""Custom QWidgets."""
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
    QFormLayout,
    QSizePolicy,
    QDialog,
    QDateTimeEdit,
    QSpinBox,
)
from PySide6.QtGui import QPainter, QColor, QIcon, QBrush, QPainterPath, QPalette
from PySide6.QtCore import (
    Signal,
    Slot,
    QVariantAnimation,
    QPointF,
    Qt,
    QTimeLine,
    QRectF,
    QTimer,
    QEasingCurve,
    QDateTime,
)
from sqlalchemy.engine.url import URL
import numpy as np
from ...helpers import open_url, CharIconEngine, color_from_index


class OpenFileButton(QWidget):
    """A button to open files or show them in the folder."""

    def __init__(self, file_path, progress, db_editor):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.file_path = file_path
        self.progress = None
        self.db_editor = db_editor
        self.dir_name, self.file_name = os.path.split(file_path)
        self._progress_bar = QProgressBar()
        self._button = QToolButton()
        layout.addWidget(self._progress_bar)
        layout.addStretch()
        layout.addWidget(self._button)
        padding = 4 * " "
        menu_button_size = self.fontMetrics().horizontalAdvance(padding)
        self._progress_bar.setFormat(self.file_name + padding)
        self._progress_bar.setRange(1, 10)
        self._progress_bar.setValue(1)
        self._button.hide()
        self._button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self._button.setText(self.file_name)
        self._button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        menu = QMenu(db_editor)
        self._button.setMenu(menu)
        open_file_action = menu.addAction("Open")
        open_containing_folder_action = menu.addAction("Open containing folder")
        open_file_action.triggered.connect(self.open_file)
        open_containing_folder_action.triggered.connect(self.open_containing_folder)
        self._button.clicked.connect(open_file_action.triggered)
        self.setStyleSheet(
            f"""
            QToolButton {{
                padding-left: 16px; padding-right: {16 + menu_button_size}px; padding-top: 6px; padding-bottom: 6px;
                background-color: #fff;
                border: 1px solid #ccc;
                border-style: outset;
            }}
            QToolButton:hover {{
                background-color: #eee;
            }}
            QToolButton:pressed {{
                background-color: #ddd;
                border-style: inset;
            }}
            QToolButton::menu-button {{
                border: 1px solid #ccc;
                border-style: outset;
                width: {menu_button_size}px;
            }}
            QToolButton::menu-button:pressed {{
                border-style: inset;
            }}
            QProgressBar {{
                text-align: center;
                background-color: #fff;
                border: 1px solid #ccc;
                border-style: inset;
            }}
            """
        )
        self._button.adjustSize()
        size = self._button.size()
        self.setFixedSize(size)
        self._progress_bar.setFixedSize(size)
        self.set_progress(progress)

    def set_progress(self, progress):
        self.progress = progress
        progress_bar_value = self._progress_bar.minimum() + self.progress * (
            self._progress_bar.maximum() - self._progress_bar.minimum()
        )
        self._progress_bar.setValue(progress_bar_value)
        if progress_bar_value == self._progress_bar.maximum():

            def _show_button():
                self._progress_bar.hide()
                self._button.show()

            QTimer.singleShot(100, _show_button)

    @Slot(bool)
    def open_file(self, checked=False):
        open_url("file:///" + os.path.join(self.dir_name, self.file_path))

    @Slot(bool)
    def open_containing_folder(self, checked=False):
        open_url("file:///" + self.dir_name)


class OpenSQLiteFileButton(OpenFileButton):
    """A button to open sqlite files, show them in the folder, or add them to the project."""

    def __init__(self, file_path, progress, db_editor):
        super().__init__(file_path, progress, db_editor)
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
        self._step_len_spin_box = QSpinBox()
        self._step_len_spin_box.setRange(1, 16777215)
        self._step_len_spin_box.setValue(1)
        controls = QWidget()
        ctrls_layout = QHBoxLayout(controls)
        ctrls_layout.setContentsMargins(2, 2, 2, 2)
        ctrls_layout.setSpacing(2)
        ctrls_layout.addWidget(self._play_pause_button)
        ctrls_layout.addStretch()
        ctrls_layout.addWidget(QLabel("Step (hours): "))
        ctrls_layout.addWidget(self._step_len_spin_box)
        ctrls_layout.addSpacing(6)
        ctrls_layout.addWidget(self._label)
        layout.addWidget(self._slider)
        layout.addWidget(controls)
        self._min_index = None
        self._max_index = None
        self._index = None
        self._step_len = np.timedelta64(1, "h")
        self._ms_per_step = None
        self._playback_tl = QTimeLine()
        self._playback_tl.setEasingCurve(QEasingCurve(QEasingCurve.Linear))
        self._slider.valueChanged.connect(self._handle_value_changed)
        self._slider.sliderMoved.connect(self._playback_tl.stop)
        self._playback_tl.frameChanged.connect(self._slider.setValue)
        self._playback_tl.stateChanged.connect(self._refresh_button_icon)
        self.index_changed.connect(lambda index: self._label.setText(str(index) + "/" + str(self._max_index)))
        self._play_pause_button.clicked.connect(self._play_pause)
        self._step_len_spin_box.valueChanged.connect(self._update_step_len)

    @Slot(int)
    def _update_step_len(self, value):
        self._step_len = np.timedelta64(value, "h")
        self._update_playback()

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
        self._update_playback()
        self._playback_tl.start()

    def _update_playback(self):
        current_value = self._slider.value()
        # Rewind if needed
        if current_value >= self._slider.maximum():
            self._slider.setValue(self._slider.minimum())
            current_value = self._slider.value()
        step_count = (self._max_index - self._min_index) // self._step_len
        self._playback_tl.setDuration(step_count * 1000 / 6)  # 6 steps per second

    @Slot(int)
    def _handle_value_changed(self, value):
        self._index = self._min_index + value * np.timedelta64(1, "h")
        self.index_changed.emit(self._index)

    def set_index_range(self, min_index, max_index):
        self._min_index = min_index
        self._max_index = max_index
        self._index = self._min_index
        self.index_changed.emit(self._index)
        self.show()
        step_count = (self._max_index - self._min_index) // np.timedelta64(1, "h")
        self._playback_tl.setFrameRange(0, step_count - 1)
        self._slider.setRange(0, step_count - 1)

    def get_index_range(self):
        return (self._min_index, self._max_index)


class LegendWidget(QWidget):
    _BASE_HEIGHT = 30
    _SPACING = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        self._legend = []
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

    def row_count(self):
        return len(self._legend)

    def set_legend(self, legend):
        self._legend.clear()
        for legend_type, pname, val_range in legend:
            if not val_range:
                continue
            min_val, max_val = val_range
            if min_val == max_val:
                continue
            paint_bar = {"color": self._paint_color_bar, "width": self._paint_volume_bar}.get(legend_type)
            if paint_bar is None:
                continue
            self._legend.append((pname + ": ", str(round(min_val, 2)), paint_bar, str(round(max_val, 2))))
        self.setMaximumHeight(len(self._legend) * self._BASE_HEIGHT)
        self.adjustSize()

    @staticmethod
    def _paint_color_bar(painter, cell):
        steps = 360
        slice_ = QRectF(cell)
        width = cell.width()
        left = cell.left()
        slice_.setWidth(width / steps)
        for k in range(steps):
            slice_.moveLeft(left + (k / steps) * width)
            color = color_from_index(k, steps)
            painter.fillRect(slice_, QBrush(color))

    @staticmethod
    def _paint_volume_bar(painter, cell):
        path = QPainterPath()
        path.moveTo(cell.bottomLeft())
        path.lineTo(cell.topRight())
        path.lineTo(cell.bottomRight())
        painter.fillPath(path, qApp.palette().color(QPalette.Normal, QPalette.WindowText))

    def paintEvent(self, ev):
        if not self._legend:
            return
        painter = QPainter(self)
        rect = self.rect()
        self.paint(painter, rect)

    def paint(self, painter, rect):
        painter.save()
        row_h = rect.height() / self.row_count()
        font = painter.font()
        font.setPointSizeF(0.375 * row_h)
        painter.setFont(font)
        text_flags = Qt.AlignBottom
        # Get column widths
        pname_cws, min_val_cws, max_val_cws = [], [], []
        for pname, min_val, _paint_legend, max_val in self._legend:
            for cws, text in zip((pname_cws, min_val_cws, max_val_cws), (pname, min_val, max_val)):
                cws.append(painter.boundingRect(rect, text_flags, text).width())
        pname_cw = max(pname_cws)
        min_val_cw = max(min_val_cws)
        max_val_cw = max(max_val_cws)
        bar_cw = rect.width() - (pname_cw + min_val_cw + max_val_cw) - 5 * self._SPACING
        # Paint
        for i, (pname, min_val, paint_bar, max_val) in enumerate(self._legend):
            cell = QRectF(0, rect.y() + self._SPACING + i * row_h, 0, row_h - 2 * self._SPACING)
            left = rect.x() + self._SPACING
            cell.setLeft(left)
            cell.setWidth(pname_cw)
            painter.drawText(cell, text_flags, pname)
            left += pname_cw + self._SPACING
            cell.setLeft(left)
            cell.setWidth(min_val_cw)
            painter.drawText(cell, text_flags | Qt.AlignRight, min_val)
            left += min_val_cw + self._SPACING
            cell.setLeft(left)
            cell.setWidth(bar_cw)
            paint_bar(painter, cell)
            left += bar_cw + self._SPACING
            cell.setLeft(left)
            cell.setWidth(max_val_cw)
            painter.drawText(cell, text_flags, max_val)
        painter.restore()


class ExportAsVideoDialog(QDialog):
    def __init__(self, start, stop, parent=None):
        super().__init__(parent=parent)
        start, stop = (QDateTime.fromString(dt, Qt.ISODate) for dt in (start, stop))
        self.setWindowTitle("Export as video")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self._start_edit = QDateTimeEdit()
        self._stop_edit = QDateTimeEdit()
        for dt_edit in (self._start_edit, self._stop_edit):
            dt_edit.setMinimumDateTime(start)
            dt_edit.setMaximumDateTime(stop)
            dt_edit.setCalendarPopup(True)
        self._start_edit.setDateTime(start)
        self._stop_edit.setDateTime(stop)
        self._start_edit.dateTimeChanged.connect(self._handle_start_dt_changed)
        self._stop_edit.dateTimeChanged.connect(self._handle_stop_dt_changed)
        self._step_len_spin_box = QSpinBox()
        self._step_len_spin_box.setRange(1, 16777215)
        self._fps_spin_box = QSpinBox()
        self._fps_spin_box.setRange(1, 20)
        self._fps_spin_box.setValue(6)
        form.addRow("Start:", self._start_edit)
        form.addRow("Stop:", self._stop_edit)
        form.addRow("Step (hours):", self._step_len_spin_box)
        form.addRow("Frames per second:", self._fps_spin_box)
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._button_box.accepted.connect(self.accept)
        self._button_box.rejected.connect(self.reject)
        layout.addLayout(form)
        layout.addWidget(self._button_box)

    @Slot(QDateTime)
    def _handle_start_dt_changed(self, start_dt):
        if start_dt > self._stop_edit.dateTime():
            self._stop_edit.setDateTime(start_dt)

    @Slot(QDateTime)
    def _handle_stop_dt_changed(self, stop_dt):
        if stop_dt < self._start_edit.dateTime():
            self._start_edit.setDateTime(stop_dt)

    def selections(self):
        return (
            self._start_edit.dateTime().toString(Qt.ISODate),
            self._stop_edit.dateTime().toString(Qt.ISODate),
            self._step_len_spin_box.value(),
            self._fps_spin_box.value(),
        )
