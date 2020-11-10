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
from PySide2.QtGui import QStandardItemModel
from spinetoolbox.widgets.add_project_item_widget import AddProjectItemWidget


class TestAddProjectItemWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = QWidget()
        self.toolbox.project = lambda: None
        self.toolbox.item_factories = MagicMock()
        self.toolbox.propose_item_name = propose_item_name = MagicMock()
        self.toolbox.filtered_spec_factory_models = filtered_spec_factory_models = MagicMock()
        filtered_spec_factory_models.__getitem__.side_effect = lambda key: QStandardItemModel()
        propose_item_name.side_effect = lambda x: ""
        self.factory = MagicMock()
        self.toolbox.item_factories.__getitem__.side_effect = lambda key: self.factory

    def tearDown(self):
        """Clean up."""
        # clean_up_toolboxui_with_project(self.toolbox)

    def test_name_field_initially_selected(self):
        prefix = "project_item"
        toolbox = QWidget()
        toolbox.project = MagicMock()
        toolbox.filtered_spec_factory_models = MagicMock()
        toolbox.filtered_spec_factory_models.__getitem__.side_effect = lambda x: QStandardItemModel()
        toolbox.propose_item_name = MagicMock()
        toolbox.propose_item_name.side_effect = lambda x: x
        class_ = MagicMock()
        class_.default_name_prefix.return_value = prefix
        widget = AddProjectItemWidget(toolbox, 0.0, 0.0, class_=class_)
        self.assertEqual(widget.ui.lineEdit_name.selectedText(), prefix)


if __name__ == '__main__':
    unittest.main()
