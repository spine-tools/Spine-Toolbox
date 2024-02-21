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

"""Unit tests for the Add/Update SpineOpt Wizard."""
import unittest
from unittest import mock
from PySide6.QtWidgets import QApplication, QWizard
from spinetoolbox.widgets.add_up_spine_opt_wizard import AddUpSpineOptWizard, REQUIRED_SPINE_OPT_VERSION
from spinetoolbox.widgets.settings_widget import SettingsWidget
from tests.mock_helpers import create_toolboxui, clean_up_toolbox, MockInstantQProcess


class TestAddUpSpineOptWizard(unittest.TestCase):
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
            self.settings_widget = SettingsWidget(self.toolbox)
            mock_fetch_python_kernels.assert_called()
            mock_fetch_julia_kernels.assert_called()

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self.toolbox)
        self.settings_widget.deleteLater()

    def test_spine_opt_installation_succeeds(self):
        wizard = AddUpSpineOptWizard(self.settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_spine_opt_update_succeeds(self):
        wizard = AddUpSpineOptWizard(self.settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            # We need the process to return a version that's lower than required
            curr_ver_split = [int(x) for x in REQUIRED_SPINE_OPT_VERSION.split(".")]
            curr_ver_split[-1] = curr_ver_split[-1] - 1
            curr_ver = ".".join(str(x) for x in curr_ver_split)
            stdout = curr_ver.encode()
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Update SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Updating SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_spine_opt_already_up_to_date(self):
        wizard = AddUpSpineOptWizard(self.settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            stdout = REQUIRED_SPINE_OPT_VERSION.encode()
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())

    def _make_failed_wizard(self):
        wizard = AddUpSpineOptWizard(self.settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Installation failed", wizard.currentPage().title())
        return wizard

    def test_spine_opt_installation_fails(self):
        wizard = self._make_failed_wizard()
        wizard.setField("troubleshoot", False)
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_registry_reset_succeeds(self):
        wizard = self._make_failed_wizard()
        wizard.next()
        self.assertEqual("Troubleshooting", wizard.currentPage().title())
        wizard.setField("problem1", True)
        wizard.next()
        self.assertEqual("Reset Julia General Registry", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Reset registry", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Resetting Julia General Registry", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Installation successful", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_registry_reset_fails(self):
        wizard = self._make_failed_wizard()
        wizard.next()
        self.assertEqual("Troubleshooting", wizard.currentPage().title())
        wizard.setField("problem1", True)
        wizard.next()
        self.assertEqual("Reset Julia General Registry", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Reset registry", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Resetting Julia General Registry", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Troubleshooting failed", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_registry_reset_succeeds_but_installing_spine_opt_fails_again_afterwards(self):
        wizard = self._make_failed_wizard()
        wizard.next()
        self.assertEqual("Troubleshooting", wizard.currentPage().title())
        wizard.setField("problem1", True)
        wizard.next()
        self.assertEqual("Reset Julia General Registry", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Reset registry", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Resetting Julia General Registry", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Troubleshooting failed", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_updating_wmf_succeeds(self):
        wizard = self._make_failed_wizard()
        wizard.next()
        self.assertEqual("Troubleshooting", wizard.currentPage().title())
        wizard.setField("problem2", True)
        wizard.next()
        self.assertEqual("Update Windows Managemet Framework", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Installation successful", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_updating_wmf_fails(self):
        wizard = self._make_failed_wizard()
        wizard.next()
        self.assertEqual("Troubleshooting", wizard.currentPage().title())
        wizard.setField("problem2", True)
        wizard.next()
        self.assertEqual("Update Windows Managemet Framework", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        self.assertEqual("Install SpineOpt", wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton))
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Troubleshooting failed", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())
