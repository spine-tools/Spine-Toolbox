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
from typing import Any
from .config import PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME, PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME
from .helpers import merge_dicts


class ProjectLoadingFailed(Exception):
    pass


def load_project_dict(project_dir: str | pathlib.Path) -> dict:
    """Loads project dictionary from project directory.

    Args:
        project_dir: Path to project directory.

    Returns:
        project dictionary
    """
    load_path = os.path.abspath(os.path.join(project_dir, PROJECT_CONFIG_DIR_NAME, PROJECT_FILENAME))
    try:
        with open(load_path, "r") as fh:
            try:
                project_dict = json.load(fh)
            except json.decoder.JSONDecodeError:
                raise ProjectLoadingFailed(f"Error in project file <b>{load_path}</b>. Invalid JSON.")
    except OSError:
        raise ProjectLoadingFailed(f"Project file <b>{load_path}</b> missing")
    return project_dict


def load_local_project_dict(project_dir: str | pathlib.Path) -> dict:
    """Loads local project data.

    Args:
        project_dir: Path to project directory

    Returns:
        Local project dict.
    """
    load_path = pathlib.Path(
        project_dir, PROJECT_CONFIG_DIR_NAME, PROJECT_LOCAL_DATA_DIR_NAME, PROJECT_LOCAL_DATA_FILENAME
    )
    if not load_path.exists():
        return {}
    with load_path.open() as fh:
        try:
            local_data_dict = json.load(fh)
        except json.decoder.JSONDecodeError:
            raise ProjectLoadingFailed(f"Error in project's local data file <b>{load_path}</b>. Invalid JSON.")
    return local_data_dict


def merge_local_dict_to_project_dict(local_dict: dict[str, Any], project_dict: dict[str, Any]) -> None:
    """Merges local data into project dict.

    Args:
        local_dict: local data dict
        project_dict: project dict
    """
    local_connections = local_dict.get("project", {}).get("connections")
    connections = project_dict["project"].get("connections")
    if local_connections is not None and connections is not None:
        for connection_dict in connections:
            source = connection_dict["from"][0]
            if source in local_connections:
                destination = connection_dict["to"][0]
                destinations = local_connections[source]
                if destination in destinations:
                    merge_dicts(destinations[destination], connection_dict)
    local_items = local_dict.get("items")
    project_items = project_dict.get("items")
    if local_items is not None and project_items is not None:
        for item_name, item_dict in project_items.items():
            local_item_dict = local_items.get(item_name)
            if local_item_dict is not None:
                merge_dicts(local_item_dict, item_dict)
