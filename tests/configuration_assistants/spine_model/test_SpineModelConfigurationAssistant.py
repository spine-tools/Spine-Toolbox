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
Unit tests for SpineModelConfigurationAssistant class.

:author: M. Marin (KTH)
:date:   3.9.2019
"""

import unittest
from unittest.mock import patch, Mock
import logging
import sys
from PySide2.QtWidgets import QApplication
from spinetoolbox.configuration_assistants.spine_model.configuration_assistant import SpineModelConfigurationAssistant
from spinetoolbox.execution_managers import QProcessExecutionManager
from tests.mock_helpers import create_toolboxui_with_project


class TestSpineModelConfigurationAssistant(unittest.TestCase):
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
        toolbox = create_toolboxui_with_project()
        self.widget = SpineModelConfigurationAssistant(toolbox)
        self.widget.setup()

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        self.widget.deleteLater()
        self.widget = None

    def test_report_julia_version_not_found(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_model.configuration_assistant.QProcessExecutionManager"
        ) as mock_QProcessExecutionManager, patch.object(self.widget, "_goto_report_julia_not_found") as mock_method:
            exec_mngr = Mock()
            mock_QProcessExecutionManager.side_effect = lambda *args, **kwargs: exec_mngr
            exec_mngr.process_output = None
            self.widget._handle_welcome_finished()
        mock_method.assert_called_once()

    def test_report_bad_julia_version(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_model.configuration_assistant.QProcessExecutionManager"
        ) as mock_QProcessExecutionManager, patch.object(self.widget, "_goto_report_bad_julia_version") as mock_method:
            exec_mngr = Mock()
            mock_QProcessExecutionManager.side_effect = lambda *args, **kwargs: exec_mngr
            exec_mngr.process_output = "1.0.0"
            self.widget._handle_welcome_finished()
        mock_method.assert_called_once()

    def test_updating_spine_model(self):
        with patch(
            "spinetoolbox.configuration_assistants.spine_model.configuration_assistant.QProcessExecutionManager"
        ) as mock_QProcessExecutionManager, patch.object(self.widget, "_goto_updating_spine_model") as mock_method:
            exec_mngr = Mock()
            mock_QProcessExecutionManager.side_effect = lambda *args, **kwargs: exec_mngr
            exec_mngr.process_output = self.widget._required_julia_version
            self.widget._handle_welcome_finished()
        mock_method.assert_called_once()

    def test_prompt_to_install_spine_model(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_prompt_to_install_latest_spine_model"
        ) as mock_method:
            self.widget._goto_updating_spine_model()
            self.widget.exec_mngr.execution_finished.emit(-1)
        mock_method.assert_called_once()

    def test_checking_py_call_program1(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_checking_py_call_program"
        ) as mock_method:
            self.widget._goto_updating_spine_model()
            self.widget.exec_mngr.execution_finished.emit(0)
        mock_method.assert_called_once()

    def test_checking_py_call_program2(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_checking_py_call_program"
        ) as mock_method:
            self.widget._goto_installing_py_call()
            self.widget.exec_mngr.execution_finished.emit(0)
        mock_method.assert_called_once()

    def test_installing_latest_spine_model(self):
        with patch.object(self.widget, "_goto_installing_latest_spine_model") as mock_method:
            self.widget._goto_prompt_to_install_latest_spine_model()
            self.widget.button_right.click()
        mock_method.assert_called_once()

    def test_prompt_to_reconfigure_py_call(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_prompt_to_reconfigure_py_call"
        ) as mock_method:
            self.widget._goto_checking_py_call_program()
            self.widget.exec_mngr.process_output = "otherpython"
            self.widget.exec_mngr.execution_finished.emit(0)
        mock_method.assert_called_once()

    def test_prompt_to_install_py_call(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_prompt_to_install_py_call"
        ) as mock_method:
            self.widget._goto_checking_py_call_program()
            self.widget.exec_mngr.execution_finished.emit(-1)
        mock_method.assert_called_once()

    def test_report_spine_model_installation_failed(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_report_spine_model_installation_failed"
        ) as mock_method:
            self.widget._goto_installing_latest_spine_model()
            self.widget.exec_mngr.execution_finished.emit(-1)
        mock_method.assert_called_once()

    def test_reconfiguring_py_call(self):
        with patch.object(self.widget, "_goto_reconfiguring_py_call") as mock_method:
            self.widget._goto_prompt_to_reconfigure_py_call()
            self.widget.button_right.click()
        mock_method.assert_called_once()

    def test_installing_py_call(self):
        with patch.object(self.widget, "_goto_installing_py_call") as mock_method:
            self.widget._goto_prompt_to_install_py_call()
            self.widget.button_right.click()
        mock_method.assert_called_once()

    def test_report_spine_model_ready1(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_report_spine_model_ready"
        ) as mock_method:
            self.widget._goto_checking_py_call_program()
            self.widget.exec_mngr.process_output = sys.executable
            self.widget.exec_mngr.execution_finished.emit(0)
        mock_method.assert_called_once()

    def test_report_spine_model_ready2(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_report_spine_model_ready"
        ) as mock_method:
            self.widget._goto_reconfiguring_py_call()
            self.widget.exec_mngr.execution_finished.emit(0)
        mock_method.assert_called_once()

    def test_report_py_call_process_failed1(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_report_py_call_process_failed"
        ) as mock_method:
            self.widget._goto_reconfiguring_py_call()
            self.widget.exec_mngr.execution_finished.emit(-1)
        mock_method.assert_called_once()

    def test_report_py_call_process_failed2(self):
        with patch.object(QProcessExecutionManager, "start_execution"), patch.object(
            self.widget, "_goto_report_py_call_process_failed"
        ) as mock_method:
            self.widget._goto_installing_py_call()
            self.widget.exec_mngr.execution_finished.emit(-1)
        mock_method.assert_called_once()


if __name__ == '__main__':
    unittest.main()
