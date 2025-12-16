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

"""Unit tests for ProjectUpgrader class."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import pytest
from spinetoolbox.config import LATEST_PROJECT_VERSION
from spinetoolbox.load_project_items import load_project_items
from spinetoolbox.project_settings import ProjectSettings
from spinetoolbox.project_upgrader import (
    InvalidProjectDict,
    VersionCheck,
    check_project_dict_valid,
    check_project_version,
    upgrade_project,
)

item_factories = load_project_items("spine_items")


class TestCheckProjectDictValid:
    def test_is_valid_v1(self):
        """Tests is_valid for a version 1 project dictionary."""
        p = make_v1_project_dict()
        check_project_dict_valid(1, p)
        p = {
            "project": {},
            "objects": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            assert not check_project_dict_valid(1, p)

    def test_is_valid_v2(self):
        """Tests is_valid for a version 2 project dictionary."""
        p = make_v2_project_dict()
        check_project_dict_valid(2, p)
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(2, p)

    def test_is_valid_v3(self):
        """Tests is_valid for a version 3 project dictionary."""
        p = make_v3_project_dict()
        check_project_dict_valid(3, p)
        # Test that an invalid v3 project dict is not valid
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(3, p)

    def test_is_valid_v4(self):
        """Tests is_valid for a version 4 project dictionary."""
        p = make_v4_project_dict()
        check_project_dict_valid(4, p)
        # Test that an invalid v4 project dict is not valid
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(4, p)

    def test_is_valid_v5(self):
        """Tests is_valid for a version 5 project dictionary."""
        p = make_v5_project_dict()
        check_project_dict_valid(5, p)
        # Test that an invalid v5 project dict is not valid
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(5, p)

    def test_is_valid_v9(self):
        p = make_v9_project_dict()
        check_project_dict_valid(9, p)
        # Test that an invalid v9 project dict is not valid
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(9, p)

    def test_is_valid_v10(self):
        p = make_v10_project_dict()
        check_project_dict_valid(10, p)
        # Test that an invalid v10 project dict is not valid
        p = {
            "project": {},
            "items": {},
        }
        with pytest.raises(InvalidProjectDict, match="^Invalid project.json file. Key version not found.$"):
            check_project_dict_valid(10, p)


class TestUpgradeProject:
    def test_upgrade_v1_to_v2(self):
        proj_v1 = make_v1_project_dict()
        check_project_dict_valid(1, proj_v1)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 2),
            ):
                # Upgrade to version 2
                issue_warning = mock.MagicMock()
                proj_v2 = upgrade_project(proj_v1, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(2, proj_v2)
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict
                v1_items = proj_v1["objects"]
                v2_items = proj_v2["items"]
                # v1 project items categorized under an item_type dict which were inside an 'objects' dict
                for item_category in v1_items.keys():
                    for name in v1_items[item_category]:
                        assert name in v2_items.keys()
                        assert isinstance(v2_items[name], dict)

    def test_upgrade_v2_to_v3(self):
        proj_v2 = make_v2_project_dict()
        check_project_dict_valid(2, proj_v2)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 3),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                    # Upgrade to version 3
                issue_warning = mock.MagicMock()
                proj_v3 = upgrade_project(proj_v2, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(3, proj_v3)
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict
                v2_items = proj_v2["items"]
                v3_items = proj_v3["items"]
                for name in v2_items.keys():
                    assert name in v3_items.keys()
                    assert isinstance(v3_items[name], dict)

    def test_upgrade_v3_to_v4(self):
        proj_v3 = make_v3_project_dict()
        check_project_dict_valid(3, proj_v3)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 4),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                # Upgrade to version 4
                issue_warning = mock.MagicMock()
                proj_v4 = upgrade_project(proj_v3, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(4, proj_v4)
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict
                v3_items = proj_v3["items"]
                v4_items = proj_v4["items"]
                for name in v3_items.keys():
                    assert name in v4_items.keys()
                    assert isinstance(v4_items[name], dict)

    def test_upgrade_v4_to_v5(self):
        proj_v4 = make_v4_project_dict()
        check_project_dict_valid(4, proj_v4)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 5),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                # Upgrade to version 5
                issue_warning = mock.MagicMock()
                proj_v5 = upgrade_project(proj_v4, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(5, proj_v5)
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict. Combiners should be gone in v5
                v4_items = proj_v4["items"]
                # Make a list of Combiner names
                combiners = []
                for name, d in v4_items.items():
                    if d["type"] == "Combiner":
                        combiners.append(name)
                v5_items = proj_v5["items"]
                for name in v4_items.keys():
                    if name in combiners:
                        # v5 should not have Combiners anymore
                        assert name not in v5_items.keys()
                    else:
                        assert name in v5_items.keys()
                        assert isinstance(v5_items[name], dict)

    def test_upgrade_v9_to_v10(self):
        proj_v9 = make_v9_project_dict()
        check_project_dict_valid(9, proj_v9)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 10),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                # Make temp preprocessing_tool.json tool spec file
                spec_file_path = os.path.join(project_dir, "tool_specs", "preprocessing_tool.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                # Upgrade to version 10
                issue_warning = mock.MagicMock()
                proj_v10 = upgrade_project(proj_v9, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(10, proj_v10)
                v10_items = proj_v10["items"]
                # Make a list of Gimlet and GdxExporter names in v9
                names = []
                for name, d in proj_v9["items"].items():
                    if d["type"] in ["Gimlet", "GdxExporter"]:
                        names.append(name)
                assert len(names) == 4  # Old should have 3 Gimlets, 1 GdxExporter
                # Check that connections have been removed
                for conn in proj_v10["project"]["connections"]:
                    for name in names:
                        assert name not in conn["from"]
                        assert name not in conn["to"]
                # Check that gimlet and GdxExporter dicts are gone from items
                for item_name in v10_items.keys():
                    assert item_name not in names
                # Check number of connections
                assert len(proj_v9["project"]["connections"]) == 8
                assert len(proj_v10["project"]["connections"]) == 1

    def test_upgrade_v10_to_v11(self):
        proj_v10 = make_v10_project_dict()
        check_project_dict_valid(10, proj_v10)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 11),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                issue_warning = mock.MagicMock()
                proj_v11 = upgrade_project(proj_v10, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(11, proj_v11)
                assert proj_v11["project"]["version"] == 11
                assert "settings" in proj_v11["project"]
                ProjectSettings.from_dict(proj_v11["project"]["settings"])

    def test_upgrade_v11_to_v12(self):
        proj_v11 = make_v11_project_dict()
        check_project_dict_valid(11, proj_v11)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
                mock.patch("spinetoolbox.project_upgrader.LATEST_PROJECT_VERSION", 12),
            ):
                os.mkdir(os.path.join(project_dir, "tool_specs"))  # Make /tool_specs dir
                issue_warning = mock.MagicMock()
                proj_v12 = upgrade_project(proj_v11, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(12, proj_v12)
                assert proj_v12["project"]["version"] == 12
                assert "settings" in proj_v12["project"]

    def test_upgrade_v1_to_latest(self):
        proj_v1 = make_v1_project_dict()
        check_project_dict_valid(1, proj_v1)
        with TemporaryDirectory() as project_dir:
            with (
                mock.patch("spinetoolbox.project_upgrader.backup_project_file") as mock_backup,
                mock.patch("spinetoolbox.project_upgrader.force_save") as mock_force_save,
            ):
                os.mkdir(os.path.join(project_dir, "Specs"))
                spec_file_path = os.path.join(project_dir, "Specs", "python_tool_spec.json")
                with open(spec_file_path, "w", encoding="utf-8") as tmp_spec_file:
                    tmp_spec_file.write("hello")
                # Upgrade to latest version
                issue_warning = mock.MagicMock()
                proj_latest = upgrade_project(proj_v1, project_dir, item_factories, issue_warning)
                issue_warning.assert_not_called()
                mock_backup.assert_called_once()
                mock_force_save.assert_called_once()
                check_project_dict_valid(LATEST_PROJECT_VERSION, proj_latest)
                assert proj_latest["project"]["version"] == LATEST_PROJECT_VERSION
                # Check that items were transferred successfully by checking that item names are found in new
                # 'items' dict and that they contain a dict. Combiners should be gone in v5
                v1_items = proj_v1["objects"]
                latest_items = proj_latest["items"]
                # v1 project items were categorized under a <item_type> dict which were inside an 'objects' dict
                for item_category in v1_items.keys():
                    for name in v1_items[item_category]:
                        assert name in latest_items.keys()
                        assert isinstance(latest_items[name], dict)
                        assert latest_items[name]["type"] == item_category[:-1]

    def test_version_check_with_too_recent_project_version(self):
        project_dict = make_v12_project_dict()
        project_dict["project"]["version"] = LATEST_PROJECT_VERSION + 1
        assert check_project_version(project_dict) == VersionCheck.TOO_RECENT


def make_v1_project_dict():
    return _get_project_dict(1)


def make_v2_project_dict():
    return _get_project_dict(2)


def make_v3_project_dict():
    return _get_project_dict(3)


def make_v4_project_dict():
    return _get_project_dict(4)


def make_v5_project_dict():
    return _get_project_dict(5)


def make_v9_project_dict():
    return _get_project_dict(9)


def make_v10_project_dict():
    return _get_project_dict(10)


def make_v11_project_dict():
    return _get_project_dict(11)


def make_v12_project_dict():
    v12_proj_dict = make_v11_project_dict()
    v12_proj_dict["project"]["version"] = 12
    return v12_proj_dict


def _get_project_dict(v):
    """Returns a project dict read from a file according to given version."""
    project_json_versions_dir = os.path.join(str(Path(__file__).parent), "test_resources", "project_json_versions")
    f_name = "proj_v" + str(v) + ".json"  # e.g. proj_v1.json
    with open(os.path.join(project_json_versions_dir, f_name), "r") as fh:
        project_dict = json.load(fh)
    return project_dict
