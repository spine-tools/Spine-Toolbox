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
Unit tests for the KernelEditor widget.

:authors: P. Savolainen (VTT)
:date:   10.11.2020
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.kernel_editor import KernelEditor
from spinetoolbox.widgets.settings_widget import SettingsWidget
from tests.mock_helpers import create_toolboxui


class TestKernelEditor(unittest.TestCase):
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

    def test_make_kernel_editor(self):
        sw = SettingsWidget(self.toolbox)
        # Make Python Kernel Editor
        ke = KernelEditor(sw, python="", julia="", python_or_julia="python", current_kernel="")
        self.assertIsInstance(ke, KernelEditor)
        self.assertEqual(ke.windowTitle(), "Python Kernel Editor")
        # Make Julia Kernel Editor
        ke = KernelEditor(sw, python="", julia="", python_or_julia="julia", current_kernel="")
        self.assertEqual(ke.windowTitle(), "Julia Kernel Editor")
