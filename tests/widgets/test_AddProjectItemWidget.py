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
Unit tests for AddProjectItemWidget.

:author: A. Soininen (VTT)
:date:   17.10.2019
"""

import unittest
from unittest.mock import MagicMock
from PySide2.QtWidgets import QApplication, QWidget
from spinetoolbox.widgets.add_project_item_widget import AddProjectItemWidget


class TestAddProjectItemWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_name_field_initially_selected(self):
        initial_name = "project_item"
        toolbox = QWidget()
        toolbox.project = MagicMock()
        widget = AddProjectItemWidget(toolbox, 0.0, 0.0, initial_name=initial_name)
        self.assertEqual(widget.ui.lineEdit_name.selectedText(), initial_name)


if __name__ == '__main__':
    unittest.main()
