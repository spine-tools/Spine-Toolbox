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
Unit tests for ``custom_editors`` module.
"""

import unittest

from PySide6.QtWidgets import QApplication

from spinetoolbox.widgets.custom_editors import SearchBarEditor


class TestSearchBarEditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._editor = SearchBarEditor(None)

    def tearDown(self):
        self._editor.deleteLater()

    def test_set_data_sorts_items_case_insensitively(self):
        self._editor.set_data("a", ["d", "b", "a", "C"])
        rows = [self._editor.proxy_model.index(row, 0).data() for row in range(self._editor.proxy_model.rowCount())]
        self.assertEqual(rows, ["a", "a", "b", "C", "d"])


if __name__ == '__main__':
    unittest.main()
