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

"""Contains unit tests for the ``notification`` module."""
import unittest
from unittest.mock import MagicMock, patch
from PySide6.QtCore import QAbstractAnimation
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QUndoCommand, QUndoStack
from spinetoolbox.widgets.notification import Notification, ChangeNotifier


@unittest.skip("Test hangs on Windows when running all tests.")
class TestChangeNotifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._parent = QWidget()
        self._undo_stack = QUndoStack(self._parent)

    def tearDown(self):
        self._parent.deleteLater()

    @patch.object(Notification, "_FADE_IN_OUT_DURATION", new=1)
    @patch.object(ChangeNotifier, "_ANIMATION_LIFE_SPAN", new=1)
    def test_tear_down_disconnects_signals(self):
        app_settings = MagicMock()
        app_settings.value.return_value = "2"
        notifier = ChangeNotifier(self._parent, self._undo_stack, app_settings, "settings key")
        with patch.object(Notification, "show") as show_method:
            self._undo_stack.push(QUndoCommand("something"))
            while notifier._notification.fade_in_anim.state() != QAbstractAnimation.Stopped:
                QApplication.processEvents()
            notifier._notification.start_self_destruction()
            try:
                while notifier._notification.fade_out_anim.state() != QAbstractAnimation.Stopped:
                    QApplication.processEvents()
            except RuntimeError:
                pass
            show_method.assert_called_once()
        notifier.tear_down()
        with patch.object(Notification, "show") as show_method:
            self._undo_stack.push(QUndoCommand("something else"))
            show_method.assert_not_called()


if __name__ == "__main__":
    unittest.main()
