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
Unit tests for the PlainParameterValueEditor widget.

:authors: A. Soininen (VTT)
:date:   3.7.2019
"""

import unittest
from PySide2.QtWidgets import QApplication
from spinetoolbox.widgets.plain_parameter_value_editor import PlainParameterValueEditor


class TestPlainParameterValueEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_initial_value(self):
        editor = PlainParameterValueEditor()
        value = editor.value()
        self.assertEqual(value, 0.0)

    def test_value_access(self):
        editor = PlainParameterValueEditor()
        editor.set_value(True)
        self.assertEqual(editor.value(), True)


if __name__ == '__main__':
    unittest.main()
