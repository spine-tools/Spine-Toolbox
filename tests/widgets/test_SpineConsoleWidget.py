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
Unit tests for the SpineConsoleWidget.

:authors: P. Savolainen (VTT)
:date:   10.11.2020
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.spine_console_widget import SpineConsoleWidget
from tests.mock_helpers import create_toolboxui


class TestSpineConsoleWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = create_toolboxui()

    def tearDown(self):
        """Clean up."""
        pass

    def test_make_spine_console_widget(self):
        python_console = SpineConsoleWidget(self.toolbox, "Python Console")
        self.assertIsInstance(python_console, SpineConsoleWidget)
