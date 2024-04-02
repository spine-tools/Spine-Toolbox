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

"""Unit tests for ``custom_delegates`` module."""
import unittest
from unittest import mock
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QApplication
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.widgets.custom_delegates import BooleanValueDelegate


class TestBooleanValueDelegate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._model = QStandardItemModel()
        row = [QStandardItem()]
        self._model.appendRow(row)
        self._delegate = BooleanValueDelegate(None, None)

    def tearDown(self):
        self._model.deleteLater()
        self._delegate.deleteLater()

    def test_set_model_data_emits_when_true_is_selected(self):
        editor = mock.MagicMock()
        index = self._model.index(0, 0)
        for value in (True, False):
            with self.subTest(value=value):
                editor.data.return_value = value
                with signal_waiter(self._delegate.data_committed, timeout=1.0) as waiter:
                    self._delegate.setModelData(editor, self._model, index)
                    waiter.wait()
                    self.assertEqual(len(waiter.args), 2)
                    self.assertEqual(waiter.args[0], index)
                    if value:
                        self.assertTrue(waiter.args[1])
                    else:
                        self.assertFalse(waiter.args[1])

    def test_set_model_data_does_not_emit_when_editor_value_is_unrecognized(self):
        editor = mock.MagicMock()
        index = self._model.index(0, 0)
        editor.data.return_value = None
        with mock.patch.object(self._delegate, "data_committed") as data_committed_signal:
            self._delegate.setModelData(editor, self._model, index)
            data_committed_signal.emit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
