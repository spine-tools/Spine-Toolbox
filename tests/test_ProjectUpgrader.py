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
import json
from unittest import mock
import logging
import sys
from tempfile import TemporaryDirectory
from PySide2.QtWidgets import QApplication
from spinetoolbox.project_upgrader import ProjectUpgrader
from spinetoolbox.resources_icons_rc import qInitResources
from .mock_helpers import create_toolboxui
from spinetoolbox.config import LATEST_PROJECT_VERSION


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

    def test_is_valid_v1_1(self):
        """Tests is_valid for a version 1 project dictionary."""
        p = make_v1_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(1, p))

    def test_is_valid_v1_2(self):
        """Tests that an invalid project information dictionary (version 1) is not accepted."""
        p = dict()
        p["project"] = dict()
        p["objects"] = dict()
        # p is missing lots of required information on purpose
        project_upgrader = ProjectUpgrader(self.toolbox)
        retval = project_upgrader.is_valid(1, p)
        self.assertFalse(retval)

    def test_is_valid1_v2_1(self):
        """Tests is_valid for a version 2 project dictionary."""
        p = make_v2_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(2, p))

    def test_is_valid_v2_2(self):
        """Tests that an invalid project information dictionary (version 2) is not accepted."""
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        # p is missing lots of required information on purpose
        project_upgrader = ProjectUpgrader(self.toolbox)
        retval = project_upgrader.is_valid(2, p)
        self.assertFalse(retval)

    def test_upgrade_no_version_to_version_2(self):
        pu = ProjectUpgrader(self.toolbox)
        project_dict = make_no_version_project_dict()
        # Upgrade to version 1
        with TemporaryDirectory() as project_dir:
            proj_dict_v1 = pu.upgrade_to_v1(project_dict, project_dir)
            self.assertTrue(pu.is_valid(1, proj_dict_v1))
            # Upgrade to version 2
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 2
            ):
                proj_dict_v2 = pu.upgrade(proj_dict_v1, project_dir)
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                self.assertTrue(pu.is_valid(2, proj_dict_v2))

    def test_upgrade_with_too_recent_project_version(self):
        """Tests that projects with too recent versions are not opened."""
        project_dict = make_v2_project_dict()
        project_dict["project"]["version"] = LATEST_PROJECT_VERSION + 1
        pu = ProjectUpgrader(self.toolbox)
        self.assertFalse(pu.upgrade(project_dict, project_dir=""))

def make_no_version_project_dict():
    """Returns an example project dictionary as it was in legacy .proj files."""
    p = """
    {
        "project": {
            "name": "UnitTest Project",
            "description": "Project for testing open_project() method in ToolboxUI.",
            "work_dir": "C:\\\\data\\\\GIT\\\\SPINETOOLBOX\\\\work",
            "tool_specifications": [],
            "connections": [
                [
                    false,
                    [
                        "right",
                        "left"
                    ],
                    false,
                    false
                ],
                [
                    false,
                    false,
                    [
                        "right",
                        "left"
                    ],
                    false
                ],
                [
                    false,
                    false,
                    false,
                    [
                        "right",
                        "left"
                    ]
                ],
                [
                    false,
                    false,
                    false,
                    false
                ]
            ],
            "scene_x": -14.5,
            "scene_y": -23.0,
            "scene_w": 464.0,
            "scene_h": 324.0
        },
        "objects": {
            "Data Stores": {
                "a": {
                    "short name": "a",
                    "description": "",
                    "x": 38.0,
                    "y": 100.0,
                    "url": {
                        "dialect": null,
                        "username": null,
                        "password": null,
                        "host": null,
                        "port": null,
                        "database": null
                    }
                }
            },
            "Data Connections": {
                "b": {
                    "short name": "b",
                    "description": "",
                    "x": 155.0,
                    "y": 101.0,
                    "references": []
                }
            },
            "Tools": {
                "c": {
                    "short name": "c",
                    "description": "",
                    "x": 277.0,
                    "y": 101.0,
                    "tool": "",
                    "execute_in_work": true
                }
            },
            "Views": {
                "d": {
                    "short name": "d",
                    "description": "",
                    "x": 395.0,
                    "y": 100.0
                }
            },
            "Importers": {},
            "Exporters": {}
        }
    }
    """
    return json.loads(p)


def make_v1_project_dict():
    p = """
    {
        "project": {
            "version": 1,
            "name": "UnitTest Project",
            "description": "Project for testing open_project() method in ToolboxUI.",
            "tool_specifications": [],
            "connections": [
                {
                    "from": [
                        "a",
                        "right"
                    ],
                    "to": [
                        "b",
                        "left"
                    ]
                },
                {
                    "from": [
                        "b",
                        "right"
                    ],
                    "to": [
                        "c",
                        "left"
                    ]
                },
                {
                    "from": [
                        "c",
                        "right"
                    ],
                    "to": [
                        "d",
                        "left"
                    ]
                }
            ],
            "scene_x": -14.5,
            "scene_y": -23.0,
            "scene_w": 464.0,
            "scene_h": 324.0
        },
        "objects": {
            "Data Stores": {
                "a": {
                    "short name": "a",
                    "description": "",
                    "x": 38.0,
                    "y": 100.0,
                    "url": null
                }
            },
            "Data Connections": {
                "b": {
                    "short name": "b",
                    "description": "",
                    "x": 155.0,
                    "y": 101.0,
                    "references": []
                }
            },
            "Tools": {
                "c": {
                    "short name": "c",
                    "description": "",
                    "x": 277.0,
                    "y": 101.0,
                    "tool": "",
                    "execute_in_work": true
                }
            },
            "Views": {
                "d": {
                    "short name": "d",
                    "description": "",
                    "x": 395.0,
                    "y": 100.0
                }
            }
        }
    }
    """
    return json.loads(p)


def make_v2_project_dict():
    p = """
    {
        "project": {
            "version": 2,
            "name": "Empty",
            "description": "",
            "specifications": {
                "Tool": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": "tool_specs/preprocessing_tool.json"
                    }
                ]
            },
            "connections": [
                {
                    "from": [
                        "Preprocessing Tool 1",
                        "right"
                    ],
                    "to": [
                        "Exporter 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Importer 1",
                        "right"
                    ],
                    "to": [
                        "Data Store 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Data Store 1",
                        "right"
                    ],
                    "to": [
                        "Combiner 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Data Store 1",
                        "right"
                    ],
                    "to": [
                        "Exporter 1",
                        "left"
                    ]
                }
            ]
        },
        "items": {
            "Data Store 1": {
                "type": "Data Store",
                "description": "",
                "x": -100.20784779809955,
                "y": -53.86171819147853,
                "url": {
                    "dialect": "sqlite",
                    "username": "",
                    "password": "",
                    "host": "",
                    "port": "",
                    "database": {
                        "type": "path",
                        "relative": true,
                        "path": ".spinetoolbox/items/data_store_1/Data Store 1.sqlite"
                    }
                }
            },
            "Preprocessing Tool 1": {
                "type": "Tool",
                "description": "",
                "x": -95.1974554081946,
                "y": 71.39809155614594,
                "specification": "Preprocessing Tool",
                "execute_in_work": true,
                "cmd_line_args": []
            },
            "Importer 1": {
                "type": "Importer",
                "description": "",
                "x": -226.72025564320035,
                "y": -47.598727704097286,
                "mappings": [],
                "cancel_on_error": true,
                "mapping_selection": []
            },
            "Exporter 1": {
                "type": "Exporter",
                "description": "",
                "x": 105.21824018800457,
                "y": -5.010392389904993,
                "settings_packs": [
                    {
                        "output_file_name": "output.gdx",
                        "state": 1,
                        "settings": {
                            "domains": {},
                            "sets": {},
                            "global_parameters_domain_name": ""
                        },
                        "indexing_settings": {},
                        "merging_settings": {},
                        "none_fallback": 0,
                        "none_export": 0,
                        "scenario": null,
                        "latest_database_commit": "2020-09-11T15:01:25",
                        "database_url": {
                            "type": "file_url",
                            "relative": true,
                            "path": ".spinetoolbox/items/data_store_1/Data Store 1.sqlite",
                            "scheme": "sqlite"
                        }
                    }
                ],
                "cancel_on_error": true
            },
            "Combiner 1": {
                "type": "Combiner",
                "description": "",
                "x": 141.54358501481573,
                "y": -171.60593935424555,
                "cancel_on_error": false
            }
        }
    }
    """
    return json.loads(p)
