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

"""Unit tests for the AboutWidget class."""
import unittest
from PySide6.QtWidgets import QApplication, QWidget
from spinetoolbox.widgets.about_widget import AboutWidget


class TestAboutWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._original_clip = QApplication.clipboard().text()

    def tearDown(self):
        QApplication.clipboard().setText(self._original_clip)

    def test_constructor(self):
        w = AboutWidget(QWidget())
        self.assertIsInstance(w, AboutWidget)
        w.close()

    def test_copy_to_clipboard(self):
        w = AboutWidget(QWidget())
        w.copy_to_clipboard(True)
        cb_contents = QApplication.clipboard().text()
        # Note: clipboard tests may break if other apps (eg. VMs in Virtual Box) reserve the system clipboard
        self.assertTrue("Python" in cb_contents)
        w.close()


if __name__ == "__main__":
    unittest.main()
