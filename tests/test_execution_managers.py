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

"""Unit tests for ``execution_managers`` module."""
import sys
import unittest
from unittest.mock import MagicMock
from spinetoolbox.execution_managers import QProcessExecutionManager


class TestQProcessExecutionManager(unittest.TestCase):
    def test_execute_nothing(self):
        logger = MagicMock()
        manager = QProcessExecutionManager(logger)
        manager.start_execution()
        self.assertFalse(manager.wait_for_process_finished())
        self.assertTrue(manager.process_failed_to_start)

    def test_execute_python_interpreter(self):
        program = sys.executable
        logger = MagicMock()
        manager = QProcessExecutionManager(logger, program, args=["--version"])
        manager.start_execution()
        self.assertTrue(manager.wait_for_process_finished())
        self.assertFalse(manager.process_failed_to_start)
        self.assertFalse(manager.process_failed)


if __name__ == "__main__":
    unittest.main()
