######################################################################################################################
# Copyright (C) 2017-2021 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for SpineOptConfigurationAssistant class.

:author: M. Marin (KTH)
:date:   3.9.2019
"""

from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch, Mock
import logging
import sys
from PySide2.QtWidgets import QApplication
from spinetoolbox.configuration_assistants.spine_opt.configuration_assistant import SpineOptConfigurationAssistant
from spinetoolbox.execution_managers import QProcessExecutionManager
from tests.mock_helpers import create_toolboxui_with_project, clean_up_toolbox


class TestSpineOptConfigurationAssistant(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )

    def setUp(self):
        """Overridden method. Runs before each test."""
        self._temp_dir = TemporaryDirectory()
        self._toolbox = create_toolboxui_with_project(self._temp_dir.name)
        self.widget = SpineOptConfigurationAssistant(self._toolbox)

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.widget.deleteLater()
        self.widget = None
        clean_up_toolbox(self._toolbox)
        self._temp_dir.cleanup()

    def goto_welcome(self):
        self.widget.set_up_machine()
        self.widget.machine.start()
        QApplication.processEvents()

    def goto_checking_spine_opt_version(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_opt.configuration_assistant.QProcessExecutionManager"
        ) as mock_QProcessExecutionManager:
            exec_mngr = Mock()
            mock_QProcessExecutionManager.side_effect = lambda *args, **kwargs: exec_mngr
            exec_mngr.process_output = self.widget._required_julia_version
            self.goto_welcome()
        with patch.object(QProcessExecutionManager, "start_execution"):
            self.widget.button_right.click()

    def goto_prompt_to_install_spine_opt(self):
        self.goto_checking_spine_opt_version()
        self.widget.spine_opt_version = None
        self.widget.exec_mngr.execution_finished.emit(0)

    def goto_prompt_to_update_spine_opt(self):
        self.goto_checking_spine_opt_version()
        self.widget.exec_mngr.process_output = "0.1.0"
        self.widget.exec_mngr.execution_finished.emit(0)

    def goto_installing_spine_opt(self):
        self.goto_prompt_to_install_spine_opt()
        with patch.object(QProcessExecutionManager, "start_execution"):
            self.widget.button_right.click()

    def goto_updating_spine_opt(self):
        self.goto_prompt_to_update_spine_opt()
        with patch.object(QProcessExecutionManager, "start_execution"):
            self.widget.button_right.click()

    def goto_report_failure_checking(self):
        self.goto_checking_spine_opt_version()
        self.widget.exec_mngr.execution_finished.emit(-1)

    def goto_report_failure_installing(self):
        self.goto_installing_spine_opt()
        self.widget.exec_mngr.execution_finished.emit(-1)

    def goto_report_failure_updating(self):
        self.goto_updating_spine_opt()
        self.widget.exec_mngr.execution_finished.emit(-1)

    def goto_report_ready_by_checking(self):
        self.goto_checking_spine_opt_version()
        self.widget.exec_mngr.process_output = self.widget._preferred_spine_opt_version
        self.widget.exec_mngr.execution_finished.emit(0)

    def goto_report_ready_by_installing(self):
        self.goto_installing_spine_opt()
        self.widget.exec_mngr.execution_finished.emit(0)

    def goto_report_ready_by_updating(self):
        self.goto_updating_spine_opt()
        self.widget.exec_mngr.execution_finished.emit(0)

    def test_report_bad_julia_version(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_opt.configuration_assistant.subprocess"
        ) as mock_subprocess:
            p = Mock()
            mock_subprocess.run.side_effect = lambda *args, **kwargs: p
            p.stdout = b"1.0.0"
            self.goto_welcome()
        self.assertEqual(self.widget.current_state, "report_bad_julia_version")

    def test_report_julia_not_found(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_opt.configuration_assistant.get_julia_command"
        ) as mock_get_julia_command:
            mock_get_julia_command.return_value = None
            self.goto_welcome()
        self.assertEqual(self.widget.current_state, "report_julia_not_found")

    def test_checking_spine_opt_version(self):
        self.goto_checking_spine_opt_version()
        self.assertEqual(self.widget.current_state, "checking_spine_opt_version")

    def test_prompt_to_install_spine_opt(self):
        self.goto_prompt_to_install_spine_opt()
        self.assertEqual(self.widget.current_state, "prompt_to_install_spine_opt")

    def test_prompt_to_update_spine_opt(self):
        self.goto_prompt_to_update_spine_opt()
        self.assertEqual(self.widget.current_state, "prompt_to_update_spine_opt")

    def test_installing_spine_opt(self):
        self.goto_installing_spine_opt()
        self.assertEqual(self.widget.current_state, "installing_spine_opt")

    def test_updating_spine_opt(self):
        self.goto_updating_spine_opt()
        self.assertEqual(self.widget.current_state, "updating_spine_opt")

    def test_report_failure_checking(self):
        self.goto_report_failure_checking()
        self.assertEqual(self.widget.current_state, "report_failure")

    def test_report_failure_installing(self):
        self.goto_report_failure_installing()
        self.assertEqual(self.widget.current_state, "report_failure")

    def test_report_failure_updating(self):
        self.goto_report_failure_updating()
        self.assertEqual(self.widget.current_state, "report_failure")

    def test_report_ready_by_checking(self):
        self.goto_report_ready_by_checking()
        self.assertEqual(self.widget.current_state, "report_spine_opt_ready")

    def test_report_ready_by_installing(self):
        self.goto_report_ready_by_installing()
        self.assertEqual(self.widget.current_state, "report_spine_opt_ready")

    def test_report_ready_by_updating(self):
        self.goto_report_ready_by_updating()
        self.assertEqual(self.widget.current_state, "report_spine_opt_ready")


if __name__ == '__main__':
    unittest.main()
