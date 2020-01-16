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
Unit tests for the DuratonEditor widget.

:authors: A. Soininen (VTT)
:date:   3.7.2019
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinedb_api import Duration
from spinetoolbox.widgets.duration_editor import DurationEditor


class TestDurationEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_initial_value(self):
        editor = DurationEditor()
        value = editor.value()
        self.assertEqual(value, Duration("1h"))

    def test_value_access_single_duration(self):
        editor = DurationEditor()
        editor.set_value(Duration("3 months"))
        self.assertEqual(editor.value(), Duration("3M"))

    def test_value_access_variable_duration(self):
        editor = DurationEditor()
        editor.set_value(Duration(["3 months", "6 months"]))
        self.assertEqual(editor.value(), Duration(["3M", "6M"]))


if __name__ == '__main__':
    unittest.main()
