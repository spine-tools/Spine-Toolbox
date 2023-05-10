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

"""Unit tests for the ConsoleWidget class."""

import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot
from spinetoolbox.widgets.console_window import ConsoleWindow
from spinetoolbox.widgets.jupyter_console_widget import JupyterConsoleWidget
from tests.mock_helpers import create_toolboxui, clean_up_toolbox


class TestConsoleWindow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = create_toolboxui()
        self.closed_emitted = False

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self.toolbox)

    def test_make_console_window(self):
        jcw = JupyterConsoleWidget(self.toolbox, kernel_name="testkernel")
        with mock.patch("spinetoolbox.widgets.console_window.ConsoleWindow.show") as mock_show:
            c = ConsoleWindow(self.toolbox, jcw, icon=QIcon())
            c.closed.connect(self.assert_closed_is_emitted)
            mock_show.assert_called_once()
            c.set_window_title("testkernel")
            console_widget = c.console()
            self.assertIsInstance(console_widget, JupyterConsoleWidget)
            c.close()
            self.assertTrue(self.closed_emitted)

    @Slot()
    def assert_closed_is_emitted(self):
        self.closed_emitted = True
