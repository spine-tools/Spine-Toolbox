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

"""Unit tests for ``spine_engine_worker`` module."""
import time
import unittest
from unittest.mock import MagicMock
from PySide6.QtCore import QObject, Slot
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_engine_worker import SpineEngineWorker


class TestSpineEngineWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def test_empty_project_executes(self):
        logger = MagicMock()
        worker = SpineEngineWorker(
            {"execution_permits": {}, "connections": [], "items_module_name": "spine_items", "settings": {}},
            MagicMock(),
            "test dag",
            {},
            {},
            logger,
            "123",
        )
        receiver = _Receiver(worker)
        try:
            worker.start()
            finished = False
            start = time.process_time()
            while not finished:
                QApplication.processEvents()
                if receiver.finished:
                    self.assertEqual(receiver.outcome, "COMPLETED")
                    finished = True
                elif time.process_time() - start > 10.0:
                    self.fail("Engine is taking too long to run.")
        finally:
            receiver.deleteLater()


class _Receiver(QObject):
    def __init__(self, worker):
        super().__init__()
        self._worker = worker
        self._worker.finished.connect(self._mark_worker_finished)
        self.finished = False
        self.outcome = None

    @Slot()
    def _mark_worker_finished(self):
        self.outcome = self._worker.engine_final_state()
        self._worker.clean_up()
        QApplication.processEvents()
        self.finished = True


if __name__ == "__main__":
    unittest.main()
