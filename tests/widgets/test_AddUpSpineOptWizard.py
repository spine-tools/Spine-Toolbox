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

import pytest
from unittest import mock
from PySide6.QtWidgets import QWizard
from spinetoolbox.widgets.add_up_spine_opt_wizard import AddUpSpineOptWizard, _PageId
from spinetoolbox.execution_models import ExecutionModels
from tests.mock_helpers import MockInstantQProcess


@pytest.fixture
def execution_models():
    """Returns an execution model with the following:
    Julia executables model has two items:
        1. Select Julia Executable...
        2. /some/julia

    Julia projects model has three items
        1. Select Julia Project...
        2. Empty
        3. @.
    """
    models = ExecutionModels(mock.MagicMock())
    with mock.patch("spinetoolbox.execution_models.resolve_default_julia_executable") as mock_default_julia:
        mock_default_julia.return_value = ""
        models.load_julia_executables(["/some/julia"], show_select_item=True)
        mock_default_julia.assert_called()
    models.load_julia_projects([], show_select_item=True)
    return models


@pytest.fixture
def wizard(parent_widget, execution_models):
    with (
        mock.patch("spinetoolbox.widgets.add_up_spine_opt_wizard.ExecutionModels.refresh_julia_executables_model") as mock_refresh_exes,
        mock.patch("spinetoolbox.widgets.add_up_spine_opt_wizard.ExecutionModels.refresh_julia_projects_model") as mock_refresh_projects,
    ):
        wizard = AddUpSpineOptWizard(parent_widget, execution_models)
        mock_refresh_exes.assert_called_once()
        mock_refresh_projects.assert_called_once()
    return wizard


class TestAddUpSpineOptWizard:
    def test_spine_opt_installation_succeeds(self, application, wizard):
        wizard.restart()
        assert wizard.currentId() == _PageId.INTRO
        wizard.next()
        assert wizard.currentId() == _PageId.SELECT_JULIA
        assert wizard.currentPage()._julia_exe_combobox.model().rowCount() == 2
        assert wizard.currentPage()._julia_project_combobox.model().rowCount() == 3
        wizard.currentPage()._julia_exe_combobox.setCurrentIndex(1)  # /some/julia
        wizard.currentPage()._julia_project_combobox.setCurrentIndex(2)  # @.
        with mock.patch("spinetoolbox.widgets.add_up_spine_opt_wizard.QMessageBox.warning") as mock_warning:
            wizard.next()
            mock_warning.assert_called_once()
        assert wizard.currentId() == _PageId.SELECT_JULIA
        # Now fake that /some/julia path exists
        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess
        ):
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.property('julia_exe') == "/some/julia"
        assert wizard.property('julia_project') == "@."
        assert wizard.currentId() == _PageId.CHECK_PREVIOUS_INSTALL
        assert wizard.currentPage().isCommitPage()
        assert wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton) == "Install SpineOpt"
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT
        assert wizard.currentPage().title() == "Installing SpineOpt"
        wizard.next()
        assert wizard.currentId() == _PageId.SUCCESS
        assert wizard.currentPage().title() == "Installation successful"
        assert wizard.currentPage().isFinalPage()

    def test_spine_opt_update_succeeds(self, application, wizard):
        wizard.restart()
        assert wizard.currentId() == _PageId.INTRO
        wizard.next()
        assert wizard.currentId() == _PageId.SELECT_JULIA
        wizard.currentPage()._julia_exe_combobox.setCurrentIndex(1)  # /some/julia
        wizard.currentPage()._julia_project_combobox.setCurrentIndex(2)  # @.
        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess
        ):
            curr_ver = "0.10.2"
            stdout = curr_ver.encode()
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        assert wizard.currentId() == _PageId.CHECK_PREVIOUS_INSTALL
        assert wizard.currentPage().isCommitPage()
        assert wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton) == "Update SpineOpt"
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(
                finished_args=(0, MockQProcess.NormalExit), stdout="0.10.3".encode()
            )
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT
        assert wizard.currentPage().title() == "Updating SpineOpt"
        wizard.next()
        assert wizard.currentId() == _PageId.SUCCESS
        assert wizard.currentPage().title() == "Update successful"
        assert wizard.currentPage().isFinalPage()

    def test_spine_opt_no_update_found(self, application, wizard):
        wizard.restart()
        assert wizard.currentId() == _PageId.INTRO
        wizard.next()
        assert wizard.currentId() == _PageId.SELECT_JULIA
        wizard.currentPage()._julia_exe_combobox.setCurrentIndex(1)  # /some/julia
        wizard.currentPage()._julia_project_combobox.setCurrentIndex(2)  # @.
        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess
        ):
            curr_ver = "0.10.2"
            stdout = curr_ver.encode()
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        assert wizard.currentId() == _PageId.CHECK_PREVIOUS_INSTALL
        assert wizard.currentPage().isCommitPage()
        assert wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton) == "Update SpineOpt"
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(
                finished_args=(0, MockQProcess.NormalExit), stdout="0.10.2".encode()
            )
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT
        assert wizard.currentPage().title() == "Updating SpineOpt"
        wizard.next()
        assert wizard.currentId() == _PageId.SUCCESS
        assert wizard.currentPage().title() == "No update available"
        assert wizard.currentPage().isFinalPage()

    def _make_failed_wizard(self,wizard):
        wizard.restart()
        assert wizard.currentId() == _PageId.INTRO
        wizard.next()
        assert wizard.currentId() == _PageId.SELECT_JULIA
        wizard.currentPage()._julia_exe_combobox.setCurrentIndex(1)  # /some/julia
        wizard.currentPage()._julia_project_combobox.setCurrentIndex(2)  # @.
        with (
            mock.patch("os.path.exists", return_value=True),
            mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess
        ):
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.currentId() == _PageId.CHECK_PREVIOUS_INSTALL
        assert wizard.currentPage().isCommitPage()
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT
        wizard.next()
        assert wizard.currentId() == _PageId.FAILURE
        return wizard

    def test_spine_opt_installation_fails(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.setField("troubleshoot", False)
        assert wizard.currentPage().title() == "Installation failed"
        assert wizard.currentPage().isFinalPage()

    def test_troubleshoot_solution_page1_and_retry_spineopt_install_fails(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_PROBLEMS
        wizard.setField("problem1", True)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_SOLUTION
        assert wizard.currentPage().isCommitPage()
        assert wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton) == "Install SpineOpt"
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(-1, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT_AGAIN
        wizard.next()
        assert wizard.currentId() == _PageId.TOTAL_FAILURE
        assert wizard.currentPage().isFinalPage()

    def test_troubleshoot_solution_page1_and_retry_spineopt_install_succeeds(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_PROBLEMS
        wizard.setField("problem1", True)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_SOLUTION
        assert wizard.currentPage().isCommitPage()
        assert wizard.currentPage().buttonText(QWizard.WizardButton.CommitButton) == "Install SpineOpt"
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        assert wizard.currentId() == _PageId.ADD_UP_SPINE_OPT_AGAIN
        wizard.next()
        assert wizard.currentId() == _PageId.SUCCESS
        assert wizard.currentPage().isFinalPage()

    def test_troubleshoot_solution_page2(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_PROBLEMS
        wizard.setField("problem2", True)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_SOLUTION
        assert wizard.currentPage().title() == "Environment variable JULIA_SSL_CA_ROOTS_PATH missing"
        assert wizard.currentPage().isFinalPage()

    def test_troubleshoot_solution_page3(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_PROBLEMS
        wizard.setField("problem3", True)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_SOLUTION
        assert wizard.currentPage().title() == "Reset Julia General Registry"
        assert wizard.currentPage().isFinalPage()

    def test_troubleshoot_solution_page4(self, application, wizard):
        wizard = self._make_failed_wizard(wizard)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_PROBLEMS
        wizard.setField("problem4", True)
        wizard.next()
        assert wizard.currentId() == _PageId.TROUBLESHOOT_SOLUTION
        assert wizard.currentPage().title() == "Update Windows Management Framework"
        assert wizard.currentPage().isFinalPage()
