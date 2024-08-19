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
from unittest import mock
from PySide6.QtWidgets import QWidget
from spinetoolbox.widgets.about_widget import AboutWidget
from tests.mock_helpers import TestCaseWithQApplication


class TestAboutWidget(TestCaseWithQApplication):
    def setUp(self):
        self._parent_widget = QWidget()

    def tearDown(self):
        self._parent_widget.deleteLater()

    def test_constructor(self):
        w = AboutWidget(self._parent_widget)
        self.assertIsInstance(w, AboutWidget)
        w.close()

    def test_copy_to_clipboard(self):
        w = AboutWidget(self._parent_widget)
        with mock.patch("spinetoolbox.widgets.about_widget.QApplication.clipboard") as clipboard_getter:
            mock_clipboard = mock.MagicMock()
            clipboard_getter.return_value = mock_clipboard
            w.copy_to_clipboard(True)
            clipboard_getter.assert_called_once_with()
            mock_clipboard.setText.assert_called_once()
        w.close()


if __name__ == "__main__":
    unittest.main()
