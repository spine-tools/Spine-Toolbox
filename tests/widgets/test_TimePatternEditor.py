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
Unit tests for the TimePatternEditor widget.

:authors: A. Soininen (VTT)
:date:   3.7.2019
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinedb_api import TimePattern
from spinetoolbox.widgets.time_pattern_editor import TimePatternEditor


class TestTimePatternEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_initial_value(self):
        editor = TimePatternEditor()
        value = editor.value()
        self.assertEqual(value, TimePattern(["1-7d"], [0.0]))

    def test_value_access(self):
        editor = TimePatternEditor()
        editor.set_value(TimePattern(["1,5d", "2-4,6,7d"], [2.2, 2.1]))
        self.assertEqual(editor.value(), TimePattern(["1,5d", "2-4,6,7d"], [2.2, 2.1]))


if __name__ == '__main__':
    unittest.main()
