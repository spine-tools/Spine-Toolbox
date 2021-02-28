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
Unit tests for the KernelEditor widget.

:authors: P. Savolainen (VTT)
:date:   10.11.2020
"""

import unittest
from unittest import mock
from PySide2.QtWidgets import QApplication
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

    def tearDown(self):
        """Clean up."""
        clean_up_toolbox(self.toolbox)

    def test_spine_opt_installation_succeeds(self):
        settings_widget = SettingsWidget(self.toolbox)
        wizard = AddUpSpineOptWizard(settings_widget, "path/to/julia", "path/to/julia_project")
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
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Installing SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_spine_opt_update_succeeds(self):
        settings_widget = SettingsWidget(self.toolbox)
        wizard = AddUpSpineOptWizard(settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            # We need the process to return a version that's lower than required
            curr_ver_split = [int(x) for x in REQUIRED_SPINE_OPT_VERSION.split(".")]
            curr_ver_split[-1] = curr_ver_split[-1] - 1
            curr_ver = ".".join(str(x) for x in curr_ver_split)
            stdout = str.encode(curr_ver)
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isCommitPage())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit))
            wizard.next()
        self.assertEqual("Updating SpineOpt", wizard.currentPage().title())
        wizard.next()
        self.assertTrue(wizard.currentPage().isFinalPage())

    def test_spine_opt_already_up_to_date(self):
        settings_widget = SettingsWidget(self.toolbox)
        wizard = AddUpSpineOptWizard(settings_widget, "path/to/julia", "path/to/julia_project")
        wizard.restart()
        self.assertEqual("Welcome", wizard.currentPage().title())
        wizard.next()
        self.assertEqual("Select Julia project", wizard.currentPage().title())
        with mock.patch("spinetoolbox.execution_managers.QProcess") as MockQProcess:
            stdout = str.encode(REQUIRED_SPINE_OPT_VERSION)
            MockQProcess.return_value = MockInstantQProcess(finished_args=(0, MockQProcess.NormalExit), stdout=stdout)
            wizard.next()
        self.assertEqual("Checking previous installation", wizard.currentPage().title())
        self.assertTrue(wizard.currentPage().isFinalPage())
