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

"""
Unit tests for the AboutWidget class.

:authors: P. Savolainen (VTT)
:date:   4.11.2022
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.about_widget import AboutWidget
from tests.mock_helpers import create_toolboxui, clean_up_toolbox


class TestAboutWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self.toolbox = create_toolboxui()
        self._original_clip = QApplication.clipboard().text()

    def tearDown(self):
        clean_up_toolbox(self.toolbox)
        QApplication.clipboard().setText(self._original_clip)

    def test_constructor(self):
        w = AboutWidget(self.toolbox)
        self.assertIsInstance(w, AboutWidget)
        w.close()

    def test_copy_to_clipboard(self):
        w = AboutWidget(self.toolbox)
        w.copy_to_clipboard(True)
        cb_contents = QApplication.clipboard().text()
        self.assertTrue("Python" in cb_contents)
        w.close()


if __name__ == '__main__':
    unittest.main()
