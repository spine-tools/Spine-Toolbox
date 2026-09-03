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
import os
import pathlib
from PySide6.QtCore import QSettings
from spine_engine.logger_interface import LoggerInterface
from spine_engine.project_item.project_item_specification import ProjectItemSpecification
from spine_engine.project_item.project_item_specification_factory import ProjectItemSpecificationFactory
from spine_engine.utils.serialization import deserialize_path
from spinetoolbox.config import (
    PLUGINS_PATH,
    PROJECT_CONFIG_DIR_NAME,
    PROJECT_LOCAL_DATA_DIR_NAME,
    SPECIFICATION_LOCAL_DATA_FILENAME,
)
from spinetoolbox.helpers import merge_dicts


class SpecificationLoadingFailed(Exception):
    pass


def load_specification_dict(spec_path: pathlib.Path | str) -> dict:
    """Loads specification dict from a file.

    Args:
        spec_path: path to specification file

    Returns:
        specification dict
    """
    try:
        with open(spec_path, "r") as fp:
            try:
                specification_dict = json.load(fp)
            except ValueError:
                raise SpecificationLoadingFailed("Item specification file not valid")
    except OSError:
        raise SpecificationLoadingFailed(f"Specification file <b>{spec_path}</b> not found")
    if "name" not in specification_dict:
        raise SpecificationLoadingFailed(f"specification file {spec_path} is missing name")
    specification_dict["definition_file_path"] = str(spec_path)
    return specification_dict


def merge_local_dict_to_specification_dict(local_dict: dict, specification_dict: dict) -> None:
    """Returns an Item specification dict from a definition file.

    Args:
        local_dict: specification's local data dict
        specification_dict: specification dict
    """
    # NOTE: If the spec doesn't have the "item_type" key, we can assume it's a tool spec
    item_type = specification_dict.get("item_type", "Tool")
    local_data = local_dict.get(item_type, {}).get(specification_dict["name"])
    if local_data is not None:
        merge_dicts(local_data, specification_dict)


def specification_from_dict(
    spec_dict: dict,
    spec_factories: dict[str, ProjectItemSpecificationFactory],
    app_settings: QSettings,
    logger: LoggerInterface,
) -> ProjectItemSpecification:
    """Returns item specification from a dictionary.

    Args:
        spec_dict: Dictionary with the specification
        spec_factories: Dictionary mapping specification name to ProjectItemSpecificationFactory
        app_settings: Toolbox settings
        logger: A logger instance.

    Returns:
        Item specification.
    """
    # NOTE: If the spec doesn't have the "item_type" key, we can assume it's a tool spec
    item_type = spec_dict.get("item_type", "Tool")
    try:
        spec_factory = spec_factories[item_type]
    except KeyError:
        raise SpecificationLoadingFailed(f"no such specification type: {item_type}")
    try:
        specification = spec_factory.make_specification(spec_dict, app_settings, logger)
    except KeyError as missing_key:
        spec_path = spec_dict["definition_file_path"]
        raise SpecificationLoadingFailed(f"specification in {spec_path} is missing a key: {missing_key}")
    specification.definition_file_path = spec_dict["definition_file_path"]
    return specification


def plugins_dirs(app_settings: QSettings) -> list[str]:
    """Loads plugins.

    Args:
        app_settings: Toolbox settings

    Returns:
        plugin directories
    """
    search_paths = {PLUGINS_PATH}
    search_paths |= set(app_settings.value("appSettings/pluginSearchPaths", defaultValue="").split(";"))
    # Plugin dirs are top-level dirs in all search paths
    plugin_dirs = []
    for path in search_paths:
        try:
            top_level_items = [os.path.join(path, item) for item in os.listdir(path)]
        except OSError:
            continue
        plugin_dirs += [item for item in top_level_items if os.path.isdir(item)]
    return plugin_dirs


def load_plugin_dict(plugin_dir: pathlib.Path | str) -> dict | None:
    """Loads plugin dict from plugin directory.

    Args:
        plugin_dir: path of plugin dir with "plugin.json" in it

    Returns:
        Plugin dict or None if plugin.json was not found in plugin dir.
    """
    plugin_file = os.path.join(plugin_dir, "plugin.json")
    if not os.path.isfile(plugin_file):
        return None
    with open(plugin_file, "r") as fh:
        try:
            plugin_dict = json.load(fh)
        except json.decoder.JSONDecodeError:
            raise SpecificationLoadingFailed(f"Error in plugin file <b>{plugin_file}</b>. Invalid JSON.")
    plugin_dict["plugin_dir"] = str(plugin_dir)
    return plugin_dict


def plugin_specifications_from_dict(
    plugin_dict: dict,
    local_data_dict: dict,
    spec_factories: dict[str, ProjectItemSpecificationFactory],
    app_settings: QSettings,
    logger: LoggerInterface,
) -> dict[str, list[ProjectItemSpecification]]:
    """Loads plugin's specifications.

    Args:
        plugin_dict: plugin dict
        local_data_dict: specifications local data dictionary
        spec_factories: Dictionary mapping specification name to ProjectItemSpecificationFactory
        app_settings: Toolbox settings
        logger: A logger instance.

    Returns:
        mapping from plugin name to list of specifications
    """
    plugin_dir = plugin_dict["plugin_dir"]
    try:
        name = plugin_dict["name"]
        specifications = plugin_dict["specifications"]
    except KeyError as key:
        plugin_file = os.path.join(plugin_dir, "plugin.json")
        raise SpecificationLoadingFailed(f"Error in plugin file <b>{plugin_file}</b>. Key {key} not found.")
    deserialized_paths = [deserialize_path(path, plugin_dir) for paths in specifications.values() for path in paths]
    plugin_specs = []
    for path in deserialized_paths:
        specification_dict = load_specification_dict(path)
        merge_local_dict_to_specification_dict(local_data_dict, specification_dict)
        specification = specification_from_dict(specification_dict, spec_factories, app_settings, logger)
        specification.plugin = name
        plugin_specs.append(specification)
    return {name: plugin_specs}


def load_specification_local_data(project_dir: pathlib.Path | str) -> dict:
    """Loads specifications' project-specific data.

    Args:
        project_dir: Path to project directory.

    Returns:
        specifications local data
    """
    local_data_path = pathlib.Path(
        project_dir, PROJECT_CONFIG_DIR_NAME, PROJECT_LOCAL_DATA_DIR_NAME, SPECIFICATION_LOCAL_DATA_FILENAME
    )
    if not local_data_path.exists():
        return {}
    with open(local_data_path) as data_file:
        return json.load(data_file)
