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
Unit tests for AddToolWidget.

:author: A. Soininen (VTT)
:date:   17.10.2019
"""

import unittest
from unittest.mock import MagicMock
from PySide2.QtGui import QStandardItemModel
from PySide2.QtWidgets import QApplication, QWidget
from spinetoolbox.project_items.tool.widgets.add_tool_widget import AddToolWidget


class TestAddToolWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_name_field_initially_selected(self):
        toolbox = QWidget()
        toolbox.project = MagicMock()
        toolbox.tool_specification_model = QStandardItemModel()
        toolbox.propose_item_name = MagicMock(return_value="Tool 1")
        widget = AddToolWidget(toolbox, 0.0, 0.0)
        self.assertEqual(widget.ui.lineEdit_name.selectedText(), "Tool 1")


if __name__ == '__main__':
    unittest.main()
