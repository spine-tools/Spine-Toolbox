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
import re
from unittest import mock
from PySide6.QtCore import QSettings
import pytest
from spine_engine.logger_interface import LoggerInterface
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from spine_engine.project_item.project_item_specification_factory import ProjectItemSpecificationFactory
from spine_engine.utils.serialization import serialize_path
from spinetoolbox.config import PROJECT_CONFIG_DIR_NAME, PROJECT_LOCAL_DATA_DIR_NAME, SPECIFICATION_LOCAL_DATA_FILENAME
from spinetoolbox.load_specification import (
    SpecificationLoadingFailed,
    load_plugin_dict,
    load_specification_dict,
    load_specification_local_data,
    merge_local_dict_to_specification_dict,
    plugin_specifications_from_dict,
    plugins_dirs,
    specification_from_dict,
)


class TestLoadSpecificationDict:
    def test_adds_definition_file_path_to_loaded_json(self, tmp_path):
        specification_path = tmp_path / "specification.json"
        with open(specification_path, "w") as fp:
            json.dump({"name": "My specification"}, fp)
        specification_dict = load_specification_dict(specification_path)
        assert specification_dict == {"name": "My specification", "definition_file_path": str(specification_path)}

    def test_raises_if_name_not_in_dict(self, tmp_path):
        specification_path = tmp_path / "specification.json"
        with open(specification_path, "w") as fp:
            json.dump({}, fp)
        with pytest.raises(
            SpecificationLoadingFailed,
            match=f"^specification file {re.escape(str(specification_path))} is missing name$",
        ):
            load_specification_dict(specification_path)

    def test_raises_if_cannot_parse_json(self, tmp_path):
        specification_path = tmp_path / "specification.json"
        with open(specification_path, "w") as fp:
            fp.write("yzzyx")
        with pytest.raises(SpecificationLoadingFailed, match="^Item specification file not valid$"):
            load_specification_dict(specification_path)

    def test_raises_if_file_not_found(self, tmp_path):
        specification_path = tmp_path / "specification.json"
        with pytest.raises(
            SpecificationLoadingFailed,
            match=f"^Specification file <b>{re.escape(str(specification_path))}</b> not found$",
        ):
            load_specification_dict(specification_path)


class TestMergeLocalDictToSpecificationDict:
    def test_normal_merge(self):
        specification_dict = {"name": "My specification", "item_type": "SwissArmyKnife", "a": 1, "b": 2}
        local_dict = {"SwissArmyKnife": {"My specification": {"b": 3}}}
        merge_local_dict_to_specification_dict(local_dict, specification_dict)
        assert specification_dict == {"name": "My specification", "item_type": "SwissArmyKnife", "a": 1, "b": 3}

    def test_empty_local_dict_has_no_effect(self):
        specification_dict = {"name": "My specification", "item_type": "SwissArmyKnife", "a": 1, "b": 2}
        local_dict = {}
        merge_local_dict_to_specification_dict(local_dict, specification_dict)
        assert specification_dict == {"name": "My specification", "item_type": "SwissArmyKnife", "a": 1, "b": 2}


class FakeSpecification(ProjectItemSpecification):
    def __init__(self, definition, app_settings, logger):
        super().__init__("Test specification", "", "SwissArmyKnife")
        self.definition = definition
        self.app_settings = app_settings
        self.logger = logger
        self.definition_file_path = None

    def __eq__(self, other):
        if not isinstance(other, FakeSpecification):
            return NotImplemented
        return (
            self.definition == other.definition
            and self.app_settings is other.app_settings
            and self.logger is other.logger
            and self.definition_file_path == other.definition_file_path
        )


class FakeSpecificationFactory(ProjectItemSpecificationFactory):

    @staticmethod
    def item_type() -> str:
        return "SwissArmyKnife"

    @staticmethod
    def make_specification(
        definition: dict, app_settings: QSettings, logger: LoggerInterface
    ) -> ProjectItemSpecification:
        if "required_key" not in definition:
            raise KeyError("required_key")
        return FakeSpecification(definition, app_settings, logger)


class TestSpecificationFromDict:
    def test_sets_definition_file_path_for_specification(self, parent_object, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        app_settings = QSettings("SpineProject", "Spine Toolbox", parent_object)
        spec_dict = {
            "item_type": "SwissArmyKnife",
            "required_key": True,
            "definition_file_path": "path/to/specification.json",
        }
        specification = specification_from_dict(spec_dict, specification_factories, app_settings, logger)
        assert specification.definition == spec_dict
        assert specification.app_settings is app_settings
        assert specification.logger is logger
        assert specification.definition_file_path == "path/to/specification.json"

    def test_item_type_default_to_tool(self, parent_object, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        app_settings = QSettings("SpineProject", "Spine Toolbox", parent_object)
        spec_dict = {
            "definition_file_path": "path/to/specification.json",
        }
        with pytest.raises(SpecificationLoadingFailed, match=f"^no such specification type: Tool$"):
            specification_from_dict(spec_dict, specification_factories, app_settings, logger)

    def test_raises_if_specification_dict_is_missing_a_key(self, parent_object, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        app_settings = QSettings("SpineProject", "Spine Toolbox", parent_object)
        spec_dict = {
            "item_type": "SwissArmyKnife",
            "definition_file_path": "path/to/specification.json",
        }
        with pytest.raises(
            SpecificationLoadingFailed,
            match="^specification in path/to/specification.json is missing a key: 'required_key'$",
        ):
            specification_from_dict(spec_dict, specification_factories, app_settings, logger)


class TestPluginsDirs:
    def test_returns_all_sub_directories(self, tmp_path, app_settings):
        default_plugins_dir = tmp_path / "default_plugins_dir"
        dir_1 = default_plugins_dir / "dir_1"
        dir_1.mkdir(parents=True)
        dir_2 = default_plugins_dir / "dir_2"
        dir_2.mkdir()
        extra_plugins_dir_1 = tmp_path / "extra_plugins_dir_1"
        dir_3 = extra_plugins_dir_1 / "dir_3"
        dir_3.mkdir(parents=True)
        extra_plugins_dir_2 = tmp_path / "extra_plugins_dir_2"
        dir_4 = extra_plugins_dir_2 / "dir_4"
        dir_4.mkdir(parents=True)

        def plugin_search_paths(key, defaultValue):
            assert key == "appSettings/pluginSearchPaths"
            assert defaultValue == ""
            return ";".join(map(str, [extra_plugins_dir_1, extra_plugins_dir_2]))

        app_settings.value = plugin_search_paths
        with mock.patch("spinetoolbox.load_specification.PLUGINS_PATH", default_plugins_dir):
            dirs = plugins_dirs(app_settings)
        assert len(dirs) == 4
        assert set(dirs) == set(map(str, [dir_1, dir_2, dir_3, dir_4]))

    def test_ignores_missing_directory(self, tmp_path, app_settings):
        default_plugins_dir = tmp_path / "default_plugins_dir"
        dir_1 = default_plugins_dir / "dir_1"
        dir_1.mkdir(parents=True)
        extra_plugins_dir_1 = tmp_path / "extra_plugins_dir_1"

        def plugin_search_paths(key, defaultValue):
            assert key == "appSettings/pluginSearchPaths"
            assert defaultValue == ""
            return str(extra_plugins_dir_1)

        app_settings.value = plugin_search_paths
        with mock.patch("spinetoolbox.load_specification.PLUGINS_PATH", default_plugins_dir):
            assert plugins_dirs(app_settings) == [str(dir_1)]


class TestLoadPluginDict:
    def test_adds_plugin_dir_to_loaded_json(self, tmp_path):
        plugin_file_path = tmp_path / "plugin.json"
        with open(plugin_file_path, "w") as fp:
            json.dump({}, fp)
        plugin_dict = load_plugin_dict(tmp_path)
        assert plugin_dict == {"plugin_dir": str(tmp_path)}

    def test_returns_none_if_file_is_not_found(self, tmp_path):
        assert load_plugin_dict(tmp_path) is None

    def test_raises_when_json_is_invalid(self, tmp_path):
        plugin_file_path = tmp_path / "plugin.json"
        with open(plugin_file_path, "w") as fp:
            fp.write("xyzyz")
        with pytest.raises(
            SpecificationLoadingFailed,
            match=f"^Error in plugin file <b>{re.escape(str(plugin_file_path))}</b>. Invalid JSON.$",
        ):
            load_plugin_dict(tmp_path)


class TestPluginSpecificationsFromDict:
    def test_load_plugin_specifications(self, tmp_path, app_settings, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        spec_dict = {
            "name": "My specification",
            "item_type": "SwissArmyKnife",
            "required_key": True,
        }
        specification_file_path = tmp_path / "specification.json"
        with open(specification_file_path, "w") as fp:
            json.dump(spec_dict, fp)
        serialized_specification_path = serialize_path(specification_file_path, tmp_path)
        plugin_dict = {
            "name": "My plugin",
            "plugin_dir": str(tmp_path),
            "specifications": {"My specification": [serialized_specification_path]},
        }
        specifications = plugin_specifications_from_dict(plugin_dict, {}, specification_factories, app_settings, logger)
        loaded_spec_dict = dict(**spec_dict, definition_file_path=str(specification_file_path))
        expected_specification = FakeSpecification(loaded_spec_dict, app_settings, logger)
        expected_specification.definition_file_path = str(specification_file_path)
        expected_specification.plugin = "My plugin"
        assert specifications == {"My plugin": [expected_specification]}

    def test_merges_local_specification_data(self, tmp_path, app_settings, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        spec_dict = {
            "name": "My specification",
            "item_type": "SwissArmyKnife",
            "required_key": True,
        }
        specification_file_path = tmp_path / "specification.json"
        with open(specification_file_path, "w") as fp:
            json.dump(spec_dict, fp)
        serialized_specification_path = serialize_path(specification_file_path, tmp_path)
        plugin_dict = {
            "name": "My plugin",
            "plugin_dir": str(tmp_path),
            "specifications": {"My specification": [serialized_specification_path]},
        }
        local_specification_dict = {"SwissArmyKnife": {"My specification": {"required_key": False}}}
        specifications = plugin_specifications_from_dict(
            plugin_dict, local_specification_dict, specification_factories, app_settings, logger
        )
        loaded_spec_dict = {
            "name": "My specification",
            "item_type": "SwissArmyKnife",
            "required_key": False,
            "definition_file_path": str(specification_file_path),
        }
        expected_specification = FakeSpecification(loaded_spec_dict, app_settings, logger)
        expected_specification.definition_file_path = str(specification_file_path)
        expected_specification.plugin = "My plugin"
        assert specifications == {"My plugin": [expected_specification]}

    def test_raises_if_plugin_dict_is_missing_keys(self, tmp_path, app_settings, logger):
        specification_factories = {"SwissArmyKnife": FakeSpecificationFactory()}
        spec_dict = {
            "name": "My specification",
            "item_type": "SwissArmyKnife",
        }
        specification_file_path = tmp_path / "specification.json"
        with open(specification_file_path, "w") as fp:
            json.dump(spec_dict, fp)
        serialized_specification_path = serialize_path(specification_file_path, tmp_path)
        plugin_dict = {
            "plugin_dir": str(tmp_path),
            "specifications": {"My specification": [serialized_specification_path]},
        }
        with pytest.raises(
            SpecificationLoadingFailed,
            match=f"^Error in plugin file <b>{re.escape(str(tmp_path / 'plugin.json'))}</b>. Key 'name' not found.$",
        ):
            plugin_specifications_from_dict(plugin_dict, {}, specification_factories, app_settings, logger)
        plugin_dict = {
            "name": "My plugin",
            "plugin_dir": str(tmp_path),
        }
        with pytest.raises(
            SpecificationLoadingFailed,
            match=f"^Error in plugin file <b>{re.escape(str(tmp_path / 'plugin.json'))}</b>. Key 'specifications' not found.$",
        ):
            plugin_specifications_from_dict(plugin_dict, {}, specification_factories, app_settings, logger)


class TestLoadSpecificationLocalData:
    def test_loads_json_as_is(self, tmp_path):
        local_data_file = (
            tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_LOCAL_DATA_DIR_NAME / SPECIFICATION_LOCAL_DATA_FILENAME
        )
        local_data_file.parent.mkdir(parents=True)
        with open(local_data_file, "w") as fp:
            json.dump("Don't panic, this is just a test.", fp)
        data_dict = load_specification_local_data(tmp_path)
        assert data_dict == "Don't panic, this is just a test."

    def test_returns_empty_dict_if_file_doesnt_exist(self, tmp_path):
        local_dir = tmp_path / PROJECT_CONFIG_DIR_NAME / PROJECT_LOCAL_DATA_DIR_NAME
        local_dir.mkdir(parents=True)
        data_dict = load_specification_local_data(tmp_path)
        assert data_dict == {}
