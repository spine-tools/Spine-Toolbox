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
import json
import pathlib
import re
import pytest
from spinetoolbox.config import (
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_FILENAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_LOCAL_DATA_FILENAME,
)
from spinetoolbox.load_project import (
    ProjectLoadingFailed,
    load_local_project_dict,
    load_project_dict,
    merge_local_dict_to_project_dict,
)


class TestLoadProjectDict:
    def test_loads_json_as_is(self, tmp_path):
        project_dir = pathlib.Path(tmp_path, PROJECT_CONFIG_DIR_NAME)
        project_dir.mkdir()
        project_json_file = project_dir / PROJECT_FILENAME
        with project_json_file.open("w") as fp:
            json.dump("don't panic this is a test", fp)
        project_dict = load_project_dict(tmp_path)
        assert project_dict == "don't panic this is a test"

    def test_raises_if_project_file_is_missing(self, tmp_path):
        project_dir = pathlib.Path(tmp_path, PROJECT_CONFIG_DIR_NAME)
        project_dir.mkdir()
        project_json_file = project_dir / PROJECT_FILENAME
        with pytest.raises(
            ProjectLoadingFailed, match=f"Project file <b>{re.escape(str(project_json_file))}</b> missing"
        ):
            load_project_dict(tmp_path)

    def test_raises_if_json_is_unreadable(self, tmp_path):
        project_dir = pathlib.Path(tmp_path, PROJECT_CONFIG_DIR_NAME)
        project_dir.mkdir()
        project_json_file = project_dir / PROJECT_FILENAME
        with project_json_file.open("w") as fp:
            fp.write("xyzzy")
        with pytest.raises(
            ProjectLoadingFailed,
            match=f"Error in project file <b>{re.escape(str(project_json_file))}</b>. Invalid JSON.",
        ):
            load_project_dict(tmp_path)


class TestLoadLocalProjectDict:
    def test_loads_json_as_is(self, tmp_path):
        local_data_path = pathlib.Path(tmp_path, PROJECT_CONFIG_DIR_NAME, PROJECT_LOCAL_DATA_DIR_NAME)
        local_data_path.mkdir(parents=True)
        local_data_file = local_data_path / PROJECT_LOCAL_DATA_FILENAME
        with local_data_file.open("w") as fp:
            json.dump("don't panic this is a test", fp)
        local_data_dict = load_local_project_dict(tmp_path)
        assert local_data_dict == "don't panic this is a test"

    def test_returns_empty_dict_if_file_not_found(self, tmp_path):
        local_data_dict = load_local_project_dict(tmp_path)
        assert local_data_dict == {}

    def test_raises_if_json_is_unreadable(self, tmp_path):
        local_data_path = pathlib.Path(tmp_path, PROJECT_CONFIG_DIR_NAME, PROJECT_LOCAL_DATA_DIR_NAME)
        local_data_path.mkdir(parents=True)
        local_data_file = local_data_path / PROJECT_LOCAL_DATA_FILENAME
        with local_data_file.open("w") as fp:
            fp.write("xyxy")
        with pytest.raises(
            ProjectLoadingFailed,
            match=f"^Error in project's local data file <b>{re.escape(str(local_data_file))}</b>. Invalid JSON.$",
        ):
            load_local_project_dict(tmp_path)


class TestMergeLocalDictToProjectDict:
    def test_merges_item_data(self):
        local_dict = {"items": {"my item": {"x": 2}}}
        project_dict = {"project": {}, "items": {"my item": {"x": 1, "y": 3}, "your item": {"x": 4, "y": 5}}}
        merge_local_dict_to_project_dict(local_dict, project_dict)
        assert project_dict == {"project": {}, "items": {"my item": {"x": 2, "y": 3}, "your item": {"x": 4, "y": 5}}}

    def test_local_data_can_omit_items(self):
        local_dict = {}
        project_dict = {"project": {}, "items": {"my item": {"x": 1}}}
        merge_local_dict_to_project_dict(local_dict, project_dict)
        assert project_dict == {"project": {}, "items": {"my item": {"x": 1}}}

    def test_project_dict_can_omit_items(self):
        local_dict = {"items": {"my item": {"x": 2}}}
        project_dict = {"project": {}}
        merge_local_dict_to_project_dict(local_dict, project_dict)
        assert project_dict == {"project": {}}

    def test_merges_connection_data(self):
        local_dict = {"project": {"connections": {"source_item": {"destination_item": {"b": 3}}}}}
        project_dict = {
            "project": {
                "connections": [{"from": ["source_item", "top"], "to": ["destination_item", "bottom"], "a": 1, "b": 2}]
            }
        }
        merge_local_dict_to_project_dict(local_dict, project_dict)
        assert project_dict == {
            "project": {
                "connections": [{"from": ["source_item", "top"], "to": ["destination_item", "bottom"], "a": 1, "b": 3}]
            }
        }
