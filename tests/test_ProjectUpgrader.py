######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
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
import os
from tempfile import TemporaryDirectory
from PySide6.QtWidgets import QApplication
from spinetoolbox.project_upgrader import ProjectUpgrader
from spinetoolbox.resources_icons_rc import qInitResources
from spinetoolbox.config import LATEST_PROJECT_VERSION
from .mock_helpers import create_toolboxui, clean_up_toolbox


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
        clean_up_toolbox(self.toolbox)

    def test_is_valid_v1(self):
        """Tests is_valid for a version 1 project dictionary."""
        p = make_v1_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(1, p))
        # Test that an invalid v1 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["objects"] = dict()
        self.assertFalse(project_upgrader.is_valid(1, p))

    def test_is_valid_v2(self):
        """Tests is_valid for a version 2 project dictionary."""
        p = make_v2_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(2, p))
        # Test that an invalid v2 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(2, p))

    def test_is_valid_v3(self):
        """Tests is_valid for a version 3 project dictionary."""
        p = make_v3_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(3, p))
        # Test that an invalid v3 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(3, p))

    def test_is_valid_v4(self):
        """Tests is_valid for a version 4 project dictionary."""
        p = make_v4_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(4, p))
        # Test that an invalid v4 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(4, p))

    def test_is_valid_v5(self):
        """Tests is_valid for a version 5 project dictionary."""
        p = make_v5_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(5, p))
        # Test that an invalid v5 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(5, p))

    def test_is_valid_v9(self):
        p = make_v9_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(9, p))
        # Test that an invalid v9 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(9, p))

    def test_is_valid_v10(self):
        p = make_v10_project_dict()
        project_upgrader = ProjectUpgrader(self.toolbox)
        self.assertTrue(project_upgrader.is_valid(10, p))
        # Test that an invalid v10 project dict is not valid
        p = dict()
        p["project"] = dict()
        p["items"] = dict()
        self.assertFalse(project_upgrader.is_valid(10, p))

    def test_upgrade_v1_to_v2(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v1 = make_v1_project_dict()
        self.assertTrue(pu.is_valid(1, proj_v1))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 2
            ):
                # Upgrade to version 2
                proj_v2 = pu.upgrade(proj_v1, project_dir)
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                self.assertTrue(pu.is_valid(2, proj_v2))
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict
                v1_items = proj_v1["objects"]
                v2_items = proj_v2["items"]
                # v1 project items categorized under an item_type dict which were inside an 'objects' dict
                for item_category in v1_items.keys():
                    for name in v1_items[item_category]:
                        self.assertTrue(name in v2_items.keys())
                        self.assertIsInstance(v2_items[name], dict)

    def test_upgrade_v2_to_v3(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v2 = make_v2_project_dict()
        self.assertTrue(pu.is_valid(2, proj_v2))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 3
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to version 3
                    proj_v3 = pu.upgrade(proj_v2, project_dir)
                    mock_backup.assert_called_once()
                    mock_force_save.assert_called_once()
                    self.assertTrue(pu.is_valid(3, proj_v3))
                    # Check that items were transferred successfully by checking that item names are found in new
                    # 'items' dict and that they contain a dict
                    v2_items = proj_v2["items"]
                    v3_items = proj_v3["items"]
                    for name in v2_items.keys():
                        self.assertTrue(name in v3_items.keys())
                        self.assertIsInstance(v3_items[name], dict)

    def test_upgrade_v3_to_v4(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v3 = make_v3_project_dict()
        self.assertTrue(pu.is_valid(3, proj_v3))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 4
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to version 4
                    proj_v4 = pu.upgrade(proj_v3, project_dir)
                    mock_backup.assert_called_once()
                    mock_force_save.assert_called_once()
                    self.assertTrue(pu.is_valid(4, proj_v4))
                    # Check that items were transferred successfully by checking that item names are found in new
                    # 'items' dict and that they contain a dict
                    v3_items = proj_v3["items"]
                    v4_items = proj_v4["items"]
                    for name in v3_items.keys():
                        self.assertTrue(name in v4_items.keys())
                        self.assertIsInstance(v4_items[name], dict)

    def test_upgrade_v4_to_v5(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v4 = make_v4_project_dict()
        self.assertTrue(pu.is_valid(4, proj_v4))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 5
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to version 5
                    proj_v5 = pu.upgrade(proj_v4, project_dir)
                    mock_backup.assert_called_once()
                    mock_force_save.assert_called_once()
                    self.assertTrue(pu.is_valid(5, proj_v5))
                    # Check that items were transferred successfully by checking that item names are found in new
                    # 'items' dict and that they contain a dict. Combiners should be gone in v5
                    v4_items = proj_v4["items"]
                    # Make a list of Combiner names
                    combiners = list()
                    for name, d in v4_items.items():
                        if d["type"] == "Combiner":
                            combiners.append(name)
                    v5_items = proj_v5["items"]
                    for name in v4_items.keys():
                        if name in combiners:
                            # v5 should not have Combiners anymore
                            self.assertFalse(name in v5_items.keys())
                        else:
                            self.assertTrue(name in v5_items.keys())
                            self.assertIsInstance(v5_items[name], dict)

    def test_upgrade_v9_to_v10(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v9 = make_v9_project_dict()
        self.assertTrue(pu.is_valid(9, proj_v9))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.force_save"
            ) as mock_force_save, mock.patch(
                'spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION', 10
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to version 10
                    proj_v10 = pu.upgrade(proj_v9, project_dir)
                    mock_backup.assert_called_once()
                    mock_force_save.assert_called_once()
                    self.assertTrue(pu.is_valid(10, proj_v10))
                    v10_items = proj_v10["items"]
                    # Make a list of Gimlet and GdxExporter names in v9
                    names = list()
                    for name, d in proj_v9["items"].items():
                        if d["type"] in ["Gimlet", "GdxExporter"]:
                            names.append(name)
                    self.assertEqual(4, len(names))  # Old should have 3 Gimlets, 1 GdxExporter
                    # Check that connections have been removed
                    for conn in proj_v10["project"]["connections"]:
                        for name in names:
                            self.assertTrue(name not in conn["from"] and name not in conn["to"])
                    # Check that gimlet and GdxExporter dicts are gone from items
                    for item_name in v10_items.keys():
                        self.assertTrue(item_name not in names)
                    # Check number of connections
                    self.assertEqual(8, len(proj_v9["project"]["connections"]))
                    self.assertEqual(1, len(proj_v10["project"]["connections"]))

    def test_upgrade_v1_to_latest(self):
        pu = ProjectUpgrader(self.toolbox)
        proj_v1 = make_v1_project_dict()
        self.assertTrue(pu.is_valid(1, proj_v1))
        with TemporaryDirectory() as project_dir:
            with mock.patch(
                "spinetoolbox.project_upgrader.ProjectUpgrader.backup_project_file"
            ) as mock_backup, mock.patch("spinetoolbox.project_upgrader.ProjectUpgrader.force_save") as mock_force_save:
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to latest version
                    proj_latest = pu.upgrade(proj_v1, project_dir)
                    mock_backup.assert_called_once()
                    mock_force_save.assert_called_once()
                    self.assertTrue(pu.is_valid(LATEST_PROJECT_VERSION, proj_latest))
                    # Check that items were transferred successfully by checking that item names are found in new
                    # 'items' dict and that they contain a dict. Combiners should be gone in v5
                    v1_items = proj_v1["objects"]
                    latest_items = proj_latest["items"]
                    # v1 project items were categorized under a <item_type> dict which were inside an 'objects' dict
                    for item_category in v1_items.keys():
                        for name in v1_items[item_category]:
                            self.assertTrue(name in latest_items.keys())
                            self.assertIsInstance(latest_items[name], dict)
                            self.assertTrue(latest_items[name]["type"] == item_category[:-1])

    def test_upgrade_with_too_recent_project_version(self):
        """Tests that projects with too recent versions are not opened."""
        project_dict = make_v10_project_dict()
        project_dict["project"]["version"] = LATEST_PROJECT_VERSION + 1
        pu = ProjectUpgrader(self.toolbox)
        self.assertFalse(pu.upgrade(project_dict, project_dir=""))


def make_v1_project_dict():
    p = """
    {
        "project": {
            "version": 1,
            "name": "UnitTest Project",
            "description": "Project for testing open_project() method in ToolboxUI.",
                    "tool_specifications": [
            {
                "type": "path",
                "relative": true,
                "path": "Specs/python_tool_spec.json"
            }
        ],
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


def make_v3_project_dict():
    p = """
    {
        "project": {
            "version": 3,
            "name": "Empty",
            "description": "",
            "specifications": {
                "Tool": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": "tool_specs/preprocessing_tool.json"
                    }
                ],
                "Data Transformer": [],
                "Importer": []
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
                "cancel_on_error": true,
                "mapping_selection": [],
                "specification": "",
                "file_selection": []
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


def make_v4_project_dict():
    p = """
    {
        "project": {
            "version": 4,
            "name": "Empty",
            "description": "",
            "specifications": {
                "Tool": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": "tool_specs/preprocessing_tool.json"
                    }
                ],
                "Data Transformer": [],
                "Importer": []
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
                "cancel_on_error": true,
                "mapping_selection": [],
                "specification": "",
                "file_selection": []
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


def make_v5_project_dict():
    p = """
    {
        "project": {
            "version": 5,
            "name": "Very Good Project",
            "description": "",
            "specifications": {
                "Tool": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": "tool_specs/preprocessing_tool.json"
                    }
                ],
                "Data Transformer": [],
                "Importer": []
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
                "cancel_on_error": true,
                "mapping_selection": [],
                "specification": "",
                "file_selection": []
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
            }
        }
    }
    """
    return json.loads(p)


def make_v9_project_dict():
    p = """
    {
        "project": {
            "version": 9,
            "description": "",
            "specifications": {
                "Tool": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": "tool_specs/python_tool.json"
                    },
                    {
                        "type": "path",
                        "relative": true,
                        "path": ".spinetoolbox/specifications/Tool/run_python_script.json"
                    }
                ],
                "Exporter": [
                    {
                        "type": "path",
                        "relative": true,
                        "path": ".spinetoolbox/specifications/Exporter/pekka.json"
                    }
                ]
            },
            "connections": [
                {
                    "from": [
                        "Gimlet 2",
                        "right"
                    ],
                    "to": [
                        "Output Data Store",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Data Store 1",
                        "right"
                    ],
                    "to": [
                        "Gimlet 2",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Gimlet 2",
                        "right"
                    ],
                    "to": [
                        "Input files",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Data Connection 1",
                        "right"
                    ],
                    "to": [
                        "Gimlet 2",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Input files",
                        "right"
                    ],
                    "to": [
                        "Gimlet 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Gimlet 1",
                        "right"
                    ],
                    "to": [
                        "Importer 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Input files",
                        "right"
                    ],
                    "to": [
                        "Tool 1",
                        "left"
                    ]
                },
                {
                    "from": [
                        "Tool 1",
                        "right"
                    ],
                    "to": [
                        "Exporter 1",
                        "left"
                    ]
                }
            ],
            "jumps": []
        },
        "items": {
            "Data Store 1": {
                "type": "Data Store",
                "description": "",
                "x": -263.6394742868821,
                "y": 176.8323524857541,
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
                },
                "cancel_on_error": true
            },
            "Output Data Store": {
                "type": "Data Store",
                "description": "",
                "x": -13.218981361948352,
                "y": -105.53784602361065,
                "url": {
                    "dialect": "sqlite",
                    "username": "",
                    "password": "",
                    "host": "",
                    "port": "",
                    "database": {
                        "type": "path",
                        "relative": true,
                        "path": ".spinetoolbox/items/output_data_store/Data Store 2.sqlite"
                    }
                },
                "cancel_on_error": true
            },
            "Input files": {
                "type": "Data Connection",
                "description": "",
                "x": 10.576156345791162,
                "y": 20.627396591609312,
                "references": []
            },
            "Data Connection 1": {
                "type": "Data Connection",
                "description": "",
                "x": -280.12202511130465,
                "y": -63.47899907065667,
                "references": []
            },
            "Tool 1": {
                "type": "Tool",
                "description": "",
                "x": 291.62202511130465,
                "y": -1.1880399099676993,
                "specification": "Python Tool",
                "execute_in_work": false,
                "cmd_line_args": []
            },
            "Gimlet 1": {
                "type": "Gimlet",
                "description": "",
                "x": 150.10969114880783,
                "y": -82.95482379567305,
                "use_shell": true,
                "shell_index": 0,
                "cmd": "dir",
                "file_selection": [
                    [
                        "a.txt",
                        true
                    ],
                    [
                        "b.txt",
                        true
                    ]
                ],
                "work_dir_mode": false,
                "cmd_line_args": []
            },
            "Gimlet 2": {
                "type": "Gimlet",
                "description": "",
                "x": -144.68627461687544,
                "y": 13.84376228227775,
                "use_shell": true,
                "shell_index": 0,
                "cmd": "type",
                "file_selection": [
                    [
                        "db_url@Data Store 1",
                        true
                    ],
                    [
                        "a.txt",
                        true
                    ],
                    [
                        "b.txt",
                        true
                    ],
                    [
                        "c.txt",
                        true
                    ],
                    [
                        "db_url@Output Data Store",
                        true
                    ]
                ],
                "work_dir_mode": true,
                "cmd_line_args": [
                    {
                        "type": "resource",
                        "arg": "a.txt"
                    }
                ]
            },
            "Gimlet 3": {
                "type": "Gimlet",
                "description": "",
                "x": 28.650658811521936,
                "y": 172.10664471911343,
                "use_shell": false,
                "shell_index": 0,
                "cmd": "C:/Python38/python.exe script.py",
                "file_selection": [],
                "work_dir_mode": true,
                "cmd_line_args": []
            },
            "Importer 1": {
                "type": "Importer",
                "description": "",
                "x": 290.52669175211753,
                "y": -172.3323524857541,
                "specification": "",
                "cancel_on_error": true,
                "file_selection": [
                    [
                        "a.txt",
                        true
                    ],
                    [
                        "b.txt",
                        true
                    ]
                ]
            },
            "Exporter 1": {
                "type": "GdxExporter",
                "description": "",
                "x": 288.4970615986198,
                "y": 170.40712704565672,
                "databases": [],
                "output_time_stamps": false,
                "cancel_on_error": true,
                "settings_pack": {
                    "settings": null,
                    "indexing_settings": null,
                    "merging_settings": {},
                    "none_fallback": 0,
                    "none_export": 0
                }
            },
            "Pekka 1": {
                "type": "Exporter",
                "description": "",
                "x": -260.724401315556,
                "y": -165.58749767665375,
                "databases": [],
                "output_time_stamps": false,
                "cancel_on_error": true,
                "specification": "Pekka"
            },
            "Run Python Script": {
                "type": "Tool",
                "description": "",
                "x": 134.2282701407487,
                "y": 128.90175148436978,
                "specification": "run python script",
                "execute_in_work": false,
                "cmd_line_args": []
            }
        }
    }"""
    return json.loads(p)

def make_v10_project_dict():
    p = """
    {
        "project": {
            "version": 10,
            "description": "",
            "specifications": {},
            "connections": []
        },
        "items": {}
    }
    """
    return json.loads(p)

