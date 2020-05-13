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
Custom QWidgets.

:author: M. Marin (KTH)
:date:   13.5.2018
"""

import os
from PySide2.QtWidgets import QWidget, QMenu, QToolButton, QStatusBar, QLabel, QGraphicsOpacityEffect
from PySide2.QtCore import Slot, QVariantAnimation, QPointF
from PySide2.QtGui import QIcon
from sqlalchemy.engine.url import URL
from ...helpers import open_url
from ...mvcmodels.filter_checkbox_list_model import LazyFilterCheckboxListModel, DataToValueFilterCheckboxListModel
from ...widgets.custom_qwidgets import FilterWidgetBase


class DataToValueFilterWidget(FilterWidgetBase):
    def __init__(self, parent, data_to_value, show_empty=True):
        """Init class.

        Args:
            parent (QWidget)
            data_to_value (method): a method to translate item data to a value for display role
        """
        super().__init__(parent)
        self._filter_model = DataToValueFilterCheckboxListModel(self, data_to_value, show_empty=show_empty)
        self._filter_model.set_list(self._filter_state)
        self._ui_list.setModel(self._filter_model)
        self.connect_signals()


class LazyFilterWidget(FilterWidgetBase):
    def __init__(self, parent, source_model, show_empty=True):
        """Init class.

        Args:
            parent (DataStoreForm)
            source_model (CompoundParameterModel, optional): a model to lazily get data from
        """
        super().__init__(parent)
        self._filter_model = LazyFilterCheckboxListModel(self, source_model, show_empty=show_empty)
        self._filter_model.set_list(self._filter_state)
        self.connect_signals()

    def set_model(self):
        self._ui_list.setModel(self._filter_model)


class OpenFileButton(QToolButton):
    """A button to open files or show them in the folder."""

    def __init__(self, file_path, ds_form):
        super().__init__()
        self.ds_form = ds_form
        self.file_path = file_path
        self.dir_name, self.file_name = os.path.split(file_path)
        self.setText(self.file_name)
        self.setPopupMode(QToolButton.MenuButtonPopup)
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
                background-color: #eeeeee;
            }
            QToolButton:pressed {
                background-color: #dddddd;
            }
            QToolButton::menu-button {
                border: 1px solid #cccccc;
                border-style: outset;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                width: 20px;
            }
            """
        )
        menu = QMenu(ds_form)
        self.setMenu(menu)
        open_file_action = menu.addAction("Open")
        show_in_folder_action = menu.addAction("Show in folder")
        open_file_action.triggered.connect(self.open_file)
        show_in_folder_action.triggered.connect(self.show_in_folder)
        self.clicked.connect(open_file_action.triggered)

    @Slot(bool)
    def open_file(self, checked=False):
        open_url(self.file_path)

    @Slot(bool)
    def show_in_folder(self, checked=False):
        open_url(self.dir_name)


class OpenSQLiteFileButton(OpenFileButton):
    """A button to open sqlite files, show them in the folder, or add them to the project."""

    def __init__(self, file_path, ds_form):
        super().__init__(file_path, ds_form)
        self.url = URL("sqlite", database=self.file_path)
        self.menu().addSeparator()
        add_to_project_action = self.menu().addAction("Add to project")
        add_to_project_action.triggered.connect(self.add_to_project)

    @Slot(bool)
    def open_file(self, checked=False):
        codename = os.path.splitext(self.file_name)[0]
        self.ds_form._open_sqlite_url(self.url, codename)

    @Slot(bool)
    def add_to_project(self, checked=False):
        self.ds_form._add_sqlite_url_to_project(self.url)


class ClearableStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hide()
        self._widgets = list()
        self.clear_button = QToolButton()
        self.clear_button.setIcon(QIcon(":/icons/menu_icons/window-close.svg"))
        self.addPermanentWidget(self.clear_button)
        self.clear_button.clicked.connect(self.clear)

    def clear(self):
        widgets = [wg for wg in self.findChildren(QWidget) if wg is not self.clear_button]
        for wg in widgets:
            self.removeWidget(wg)
        self.hide()


class ShootingLabel(QLabel):
    def __init__(self, origin, destination, parent=None, duration=1200):
        super().__init__("FIXME", parent=parent)
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

    def _handle_value_changed(self, value):
        opacity = 1.0 - abs(2 * value - 1.0)
        self.effect.setOpacity(opacity)
        pos = self.origin + value * self.direction
        self.move(pos.toPoint())

    def show(self):
        self.anim.start(QVariantAnimation.DeleteWhenStopped)
        super().show()
