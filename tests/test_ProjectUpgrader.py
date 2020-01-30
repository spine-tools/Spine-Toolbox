######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for ProjectUpgrader class.

:authors: P. Savolainen (VTT)
:date:   28.11.2019
"""

import unittest
import logging
import os
import sys
from tempfile import TemporaryDirectory
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_upgrader import ProjectUpgrader
from spinetoolbox.resources_icons_rc import qInitResources
from .mock_helpers import create_toolboxui
from spinetoolbox.helpers import create_dir


class TestProjectUpgrader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        qInitResources()
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
        """Makes an instance of ToolboxUI class without a project."""
        self.toolbox = create_toolboxui()

    def tearDown(self):
        """Runs after each test. Use this to free resources after a test if needed."""
        self.toolbox.deleteLater()
        self.toolbox = None

    def test_is_valid1(self):
        """Tests that the pre-made project information dictionary is valid according to project version 1."""
        project_config_file = os.path.abspath(
            os.path.join(os.curdir, "tests", "test_resources", "Project Directory", ".spinetoolbox", "project.json")
        )
        project_upgrader = ProjectUpgrader(self.toolbox)
        project_dict = project_upgrader.open_proj_json(project_config_file)
        retval = project_upgrader.is_valid(project_dict)
        self.assertTrue(retval)

    def test_is_valid2(self):
        """Tests that an invalid project information dictionary is not accepted."""
        p = dict()
        p["project"] = dict()
        p["objects"] = dict()
        # p is missing lots of required information on purpose
        project_upgrader = ProjectUpgrader(self.toolbox)
        retval = project_upgrader.is_valid(p)
        self.assertFalse(retval)

    def test_upgrade(self):
        """Tests that reading an old project file (.proj) and
        upgrading it produces a valid project information dictionary."""
        old_project_file = os.path.abspath(os.path.join(os.curdir, "tests", "test_resources", "unit_test_project.proj"))
        pu = ProjectUpgrader(self.toolbox)
        old_project_dict = pu.open_proj_json(old_project_file)
        with TemporaryDirectory() as old_project_dir:
            # Old project has four items which should have a data_dir
            a_dir = os.path.join(old_project_dir, "a")
            b_dir = os.path.join(old_project_dir, "b")
            c_dir = os.path.join(old_project_dir, "c")
            d_dir = os.path.join(old_project_dir, "d")
            create_dir(a_dir)
            create_dir(b_dir)
            create_dir(c_dir)
            create_dir(d_dir)
            udgraded_project_dict = pu.upgrade(old_project_dict, old_project_dir, "dummy_project_dir")
        retval = pu.is_valid(udgraded_project_dict)
        self.assertTrue(retval)
