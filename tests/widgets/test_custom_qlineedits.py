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

"""Unit tests for the classes in ``custom_qlineedits`` module."""
from PySide6.QtWidgets import QWidget
from spinetoolbox.widgets.custom_qlineedits import PropertyQLineEdit
from tests.mock_helpers import TestCaseWithQApplication


class TestPropertyQLineEdit(TestCaseWithQApplication):
    def test_property_qlineedit(self):
        parent = QWidget()
        le = PropertyQLineEdit(parent)
        le.setText("abc")
        self.assertEqual("abc", le.text())
        parent.deleteLater()
