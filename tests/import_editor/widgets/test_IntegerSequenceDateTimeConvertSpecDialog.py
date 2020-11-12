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
Contains unit tests for :class:`IntegerSequenceDateTimeConvertSpecDialog`.

:author: A. Soininen (VTT)
:date:   12.11.2020
"""
import unittest
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QApplication
from spinedb_api import DateTime, Duration
from spine_engine.spine_io.type_conversion import IntegerSequenceDateTimeConvertSpec
from spinetoolbox.import_editor.widgets.table_view_with_button_header import IntegerSequenceDateTimeConvertSpecDialog


class TestIntegerSequenceDateTimeConvertSpecDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_restore_previous_spec(self):
        spec = IntegerSequenceDateTimeConvertSpec(DateTime("2020-11-12T15:45"), 23, Duration("5h"))
        widget = IntegerSequenceDateTimeConvertSpecDialog(spec, None)
        self.assertEqual(widget.datetime.dateTime().toString(Qt.ISODate), "2020-11-12T15:45:00")
        self.assertEqual(widget.start_integer.value(), 23)
        self.assertEqual(widget.duration.text(), "5h")


if __name__ == '__main__':
    unittest.main()
