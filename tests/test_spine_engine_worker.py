######################################################################################################################
# Copyright (C) 2017 - 2020 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for ``spine_engine_worker`` module.

:authors: A. Soininen (VTT)
:date:    3.12.2020
"""
import time
import unittest
from PySide2.QtCore import QObject, Slot
from PySide2.QtWidgets import  QApplication
from spinetoolbox.dag_handler import DirectedGraphHandler
from spinetoolbox.spine_engine_worker import SpineEngineWorker
from .mock_helpers import clean_up_toolboxui_with_project, create_toolboxui_with_project


class TestSpineEngineWorker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        self._toolbox = create_toolboxui_with_project()

    def tearDown(self):
        clean_up_toolboxui_with_project(self._toolbox)

    def test_empty_project_executes(self):
        dag = DirectedGraphHandler()
        worker = SpineEngineWorker(self._toolbox, {}, dag, "test dag", {})
        receiver = _Receiver(worker)
        try:
            worker.start()
            finished = False
            start = time.process_time()
            while not finished:
                QApplication.processEvents()
                if receiver.finished:
                    self.assertEqual(receiver._outcome, "COMPLETED")
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
        self.finished = True
        self._outcome = self._worker.engine_final_state()
        self._worker.clean_up()


if __name__ == '__main__':
    unittest.main()
