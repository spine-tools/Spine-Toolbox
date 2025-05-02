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

"""Unit tests for the DuratonEditor widget."""
import unittest
from PySide6.QtWidgets import QWidget
from spinedb_api import Duration
from spinetoolbox.widgets.duration_editor import DurationEditor
from tests.mock_helpers import TestCaseWithQApplication, q_object


class TestDurationEditor(TestCaseWithQApplication):
    def test_initial_value(self):
        with q_object(QWidget()) as parent:
            editor = DurationEditor(parent)
            value = editor.value()
            self.assertEqual(value, Duration("1h"))

    def test_value_access_single_duration(self):
        with q_object(QWidget()) as parent:
            editor = DurationEditor(parent)
            editor.set_value(Duration("3 months"))
            self.assertEqual(editor.value(), Duration("3M"))


if __name__ == "__main__":
    unittest.main()
