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

"""Unit tests for the classes in ``custom_combobox`` module.
OpenProjectDialogComboBox is tested in test_open_project_dialog module."""
import unittest
from PySide6.QtGui import QPaintEvent
from PySide6.QtWidgets import QWidget
from spinetoolbox.widgets.custom_combobox import CustomQComboBox, ElidedCombobox
from tests.mock_helpers import TestCaseWithQApplication


class TestCustomComboBoxes(TestCaseWithQApplication):
    def test_custom_combobox(self):
        parent = QWidget()
        cb = CustomQComboBox(parent)
        cb.addItems(["a", "b", "c"])
        self.assertEqual("a", cb.itemText(0))
        parent.deleteLater()

    def test_elided_combobox(self):
        parent = QWidget()
        cb = ElidedCombobox(parent)
        cb.paintEvent(QPaintEvent(cb.rect()))
        parent.deleteLater()
