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

"""Unit tests for the KernelEditor widget."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QWizard
from spinetoolbox.widgets.install_julia_wizard import InstallJuliaWizard
from spinetoolbox.widgets.settings_widget import SettingsWidget
from tests.mock_helpers import create_toolboxui, clean_up_toolbox, MockInstantQProcess


class TestInstallJuliaWizard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            QApplication()

    def setUp(self):
        """Set up toolbox."""
        self.toolbox = create_toolboxui()
        with mock.patch(
            "spinetoolbox.widgets.settings_widget.SettingsWidget.start_fetching_python_kernels"
        ) as mock_fetch_python_kernels, mock.patch(
            "spinetoolbox.widgets.settings_widget.SettingsWidget.start_fetching_julia_kernels"
        ) as mock_fetch_julia_kernels:
            self._settings_widget = SettingsWidget(self.toolbox)
            mock_fetch_python_kernels.assert_called()
            mock_fetch_julia_kernels.assert_called()

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self.toolbox)

    def test_julia_installation_succeeds(self):
        wizard = InstallJuliaWizard(self._settings_widget)
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select directories", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install Julia", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        wizard.set_julia_exe = mock_set_julia_exe = mock.Mock()
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        mock_set_julia_exe.assert_called_once()
        wizard.julia_exe = "path/to/julia"
        wizard.next()
        self.assertEqual("Installation successful", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())
        wizard.julia_exe_selected = mock.Mock()
        wizard.accept()
        wizard.julia_exe_selected.emit.assert_called_once()
        wizard.julia_exe_selected.emit.assert_called_with("path/to/julia")

    def test_julia_installation_fails(self):
        wizard = InstallJuliaWizard(self._settings_widget)
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select directories", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install Julia", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        wizard.set_julia_exe = mock_set_julia_exe = mock.Mock()
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        mock_set_julia_exe.assert_not_called()
        wizard.next()
        self.assertEqual("Installation failed", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())
        wizard.julia_exe_selected = mock.Mock()
        wizard.accept()
        wizard.julia_exe_selected.emit.assert_not_called()

    def test_julia_installation_crashes(self):
        wizard = InstallJuliaWizard(self._settings_widget)
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select directories", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install Julia", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        wizard.set_julia_exe = mock_set_julia_exe = mock.Mock()
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.CrashExit))
            wizard.next()
        mock_set_julia_exe.assert_not_called()
        wizard.next()
        self.assertEqual("Installation failed", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())
        wizard.julia_exe_selected = mock.Mock()
        wizard.accept()
        wizard.julia_exe_selected.emit.assert_not_called()
