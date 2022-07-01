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
Spine Toolbox project class.

:authors: P. Savolainen (VTT), E. Rinne (VTT)
:date:   10.1.2018
"""
from enum import auto, Enum, unique
from itertools import chain
import os
from pathlib import Path
import json
import random
from PySide2.QtCore import Signal
from PySide2.QtGui import QColor
import networkx as nx
from spine_engine.exception import EngineInitFailed, RemoteEngineFailed
from spine_engine.utils.helpers import create_timestamp
from .project_item.logging_connection import LoggingConnection, LoggingJump
from spine_engine.spine_engine import ExecutionDirection, validate_single_jump
from spine_engine.utils.helpers import shorten
from spine_engine.utils.serialization import deserialize_path, serialize_path
from .server.util.file_packager import FilePackager
from .server.zmq_client import ZMQClient, ClientSecurityModel
from .metaobject import MetaObject
from .helpers import (
    create_dir,
    erase_dir,
    load_specification_from_file,
    make_settings_dict_for_engine,
    load_project_dict,
    load_local_project_data,
    merge_dicts,
)
from .project_upgrader import ProjectUpgrader
from .config import (
    LATEST_PROJECT_VERSION,
    PROJECT_FILENAME,
    INVALID_CHARS,
    PROJECT_LOCAL_DATA_DIR_NAME,
    PROJECT_LOCAL_DATA_FILENAME,
    FG_COLOR,
    PROJECT_ZIP_FILENAME,
)
from .project_commands import SetProjectNameAndDescriptionCommand
from .spine_engine_worker import SpineEngineWorker


@unique
class ItemNameStatus(Enum):
    OK = auto()
    INVALID = auto()
    EXISTS = auto()
    SHORT_NAME_EXISTS = auto()


class SpineToolboxProject(MetaObject):
    """Class for Spine Toolbox projects."""

    renamed = Signal(str)
    """Emitted after project has been renamed."""
    project_about_to_be_torn_down = Signal()
    """Emitted before project is being torn down."""
    project_execution_about_to_start = Signal()
    """Emitted just before the entire project is executed."""
    project_execution_finished = Signal()
    """Emitted after the entire project execution finishes."""
    connection_established = Signal(object)
    """Emitted after new connection has been added to project."""
    connection_about_to_be_removed = Signal(object)
    """Emitted before connection removal."""
    connection_updated = Signal(object)
    """Emitted after a connection has been updated."""
    jump_added = Signal(object)
    """Emitted after a jump has been added."""
    jump_about_to_be_removed = Signal(object)
    """Emitted before a jump is removed."""
    jump_updated = Signal(object)
    """Emitted after a jump has been replaced by another."""
    item_added = Signal(str)
    """Emitted after a project item has been added."""
    item_about_to_be_removed = Signal(str)
    """Emitted before project item removal."""
    item_renamed = Signal(str, str)
    """Emitted after project item has been renamed."""
    specification_added = Signal(str)
    """Emitted after a specification has been added."""
    specification_about_to_be_removed = Signal(str)
    """Emitted before a specification will be removed."""
    specification_replaced = Signal(str, str)
    """Emitted after a specification has been replaced."""
    specification_saved = Signal(str, str)
    """Emitted after a specification has been saved."""

    def __init__(self, toolbox, name, description, p_dir, plugin_specs, settings, logger):
        """
        Args:
            toolbox (ToolboxUI): toolbox of this project
            name (str): Project name
            description (str): Project description
            p_dir (str): Project directory
            plugin_specs (Iterable of ProjectItemSpecification): specifications available as plugins
            settings (QSettings): Toolbox settings
            logger (LoggerInterface): a logger instance
        """
        super().__init__(name, description)
        self._toolbox = toolbox
        self._project_items = dict()
        self._specifications = dict(enumerate(plugin_specs))
        self._connections = list()
        self._jumps = list()
        self._logger = logger
        self._settings = settings
        self._engine_workers = []
        self._execution_in_progress = False
        self.project_dir = None  # Full path to project directory
        self.config_dir = None  # Full path to .spinetoolbox directory
        self.items_dir = None  # Full path to items directory
        self.specs_dir = None  # Full path to specs directory
        self.config_file = None  # Full path to .spinetoolbox/project.json file
        p_dir = os.path.abspath(p_dir)
        if not self._create_project_structure(p_dir):
            self._logger.msg_error.emit(f"Creating project directory structure in <b>{p_dir}</b> failed")

    def toolbox(self):
        """Returns Toolbox main window.

        Returns:
            ToolboxUI: main window
        """
        return self._toolbox

    def _create_project_structure(self, directory):
        """Makes the given directory a Spine Toolbox project directory.
        Creates directories and files that are common to all projects.

        Args:
            directory (str): Abs. path to a directory that should be made into a project directory

        Returns:
            bool: True if project structure was created successfully, False otherwise
        """
        self.project_dir = directory
        self.config_dir = os.path.abspath(os.path.join(self.project_dir, ".spinetoolbox"))
        self.items_dir = os.path.abspath(os.path.join(self.config_dir, "items"))
        self.specs_dir = os.path.abspath(os.path.join(self.config_dir, "specifications"))
        self.config_file = os.path.abspath(os.path.join(self.config_dir, PROJECT_FILENAME))
        for dir_ in (self.project_dir, self.config_dir, self.items_dir, self.specs_dir):
            try:
                create_dir(dir_)
            except OSError:
                self._logger.msg_error.emit(f"Creating directory {dir_} failed")
                return False
        return True

    def call_set_name_and_description(self, name, description):
        self._toolbox.undo_stack.push(SetProjectNameAndDescriptionCommand(self, name, description))

    def set_name(self, name):
        """Changes project name.

        Args:
            name (str): New project name
        """
        if name == self.name:
            return
        super().set_name(name)
        self._logger.msg.emit(f"Project name changed to <b>{self.name}</b>")
        self.renamed.emit(name)

    def set_description(self, description):
        if description == self.description:
            return
        super().set_description(description)
        msg = "Project description "
        if description:
            msg += f"changed to <b>{description}</b>"
        else:
            msg += "cleared"
        self._logger.msg.emit(msg)

    def save(self):
        """Collects project information and objects into a dictionary and writes it to a JSON file.

        Returns:
            bool: True or False depending on success
        """
        serialized_spec_paths = dict()
        for spec in self._specifications.values():
            if spec.plugin is not None:
                continue
            if not spec.save():
                self._logger.msg_error.emit(f"Failed to save specification <b>{spec.name}</b>.")
                return False
            serialized_path = serialize_path(spec.definition_file_path, self.project_dir)
            serialized_spec_paths.setdefault(spec.item_type, []).append(serialized_path)
        project_dict = {
            "version": LATEST_PROJECT_VERSION,
            "name": self.name,
            "description": self.description,
            "specifications": serialized_spec_paths,
            "connections": [connection.to_dict() for connection in self._connections],
            "jumps": [jump.to_dict() for jump in self._jumps],
        }
        items_dict = {name: item.item_dict() for name, item in self._project_items.items()}
        local_items_data = self._pop_local_data_from_items_dict(items_dict)
        saved_dict = dict(project=project_dict, items=items_dict)
        with open(self.config_file, "w") as fp:
            self._dump(saved_dict, fp)
        local_path = Path(self.config_dir, PROJECT_LOCAL_DATA_DIR_NAME)
        local_path.mkdir(parents=True, exist_ok=True)
        with (local_path / PROJECT_LOCAL_DATA_FILENAME).open("w") as fp:
            self._dump(dict(items=local_items_data), fp)
        return True

    def _pop_local_data_from_items_dict(self, items_dict):
        """Pops local data from project items dict.

        Args:
            items_dict (dict): items dict

        Returns:
            dict: local project item data
        """
        local_data_dict = dict()
        for name, item_dict in items_dict.items():
            local_entries = self._project_items[name].item_dict_local_entries()
            if not local_entries:
                continue
            for prefix in local_entries:
                # Pop value from item_dict
                d = item_dict
                for part in prefix[:-1]:
                    d = d.get(part, {})
                value = d.pop(prefix[-1], None)
                if value is None:
                    continue
                # Put value in local_data_dict
                d = local_data_dict.setdefault(name, {})
                for part in prefix[:-1]:
                    d = d.setdefault(part, {})
                d[prefix[-1]] = value
        return local_data_dict

    @staticmethod
    def _dump(project_dict, out_stream):
        """Dumps project dict into output stream.

        Args:
            project_dict (dict): project dictionary
            out_stream (IOBase): output stream
        """
        json.dump(project_dict, out_stream, indent=4)

    def load(self, spec_factories, item_factories):
        """Loads project from its project directory.

        Args:
            spec_factories (dict): Dictionary mapping specification name to ProjectItemSpecificationFactory
            item_factories (dict): mapping from item type to ProjectItemFactory

        Returns:
            bool: True if the operation was successful, False otherwise
        """
        project_dict = load_project_dict(self.config_dir, self._logger)
        if project_dict is None:
            return False
        project_info = ProjectUpgrader(self._toolbox).upgrade(project_dict, self.project_dir)
        if not project_info:
            return False
        # Check project info validity
        if not ProjectUpgrader(self._toolbox).is_valid(LATEST_PROJECT_VERSION, project_info):
            self._logger.msg_error.emit(f"Opening project in directory {self.project_dir} failed")
            return False
        local_data_dict = load_local_project_data(self.config_dir, self._logger)
        self._merge_local_data_to_project_info(local_data_dict, project_info)
        # Parse project info
        self.set_name(project_info["project"]["name"])
        self.set_description(project_info["project"]["description"])
        spec_paths_per_type = project_info["project"]["specifications"]
        deserialized_paths = [
            deserialize_path(path, self.project_dir) for paths in spec_paths_per_type.values() for path in paths
        ]
        self._logger.msg.emit("Loading specifications...")
        for path in deserialized_paths:
            spec = load_specification_from_file(path, spec_factories, self._settings, self._logger)
            if spec is not None:
                self.add_specification(spec, save_to_disk=False)
        items_dict = project_info["items"]
        self._logger.msg.emit("Loading project items...")
        if not items_dict:
            self._logger.msg_warning.emit("Project has no items")
        self.restore_project_items(items_dict, item_factories, silent=True)
        self._logger.msg.emit("Restoring connections...")
        connection_dicts = project_info["project"]["connections"]
        for connection in map(self.connection_from_dict, connection_dicts):
            self.add_connection(connection, silent=True)
        self._logger.msg.emit("Restoring jumps...")
        jump_dicts = project_info["project"].get("jumps", [])
        for jump in map(self.jump_from_dict, jump_dicts):
            self.add_jump(jump, silent=True)
        return True

    @staticmethod
    def _merge_local_data_to_project_info(local_data_dict, project_info):
        """Merges local data into project info.

        Args:
            local_data_dict (dict): local data
            project_info (dict): project dict
        """
        local_items = local_data_dict.get("items")
        project_items = project_info.get("items")
        if local_items is not None and project_items is not None:
            for item_name, item_dict in project_items.items():
                local_item_dict = local_items.get(item_name)
                if local_item_dict is not None:
                    merge_dicts(local_item_dict, item_dict)

    def connection_from_dict(self, connection_dict):
        return LoggingConnection.from_dict(connection_dict, toolbox=self._toolbox)

    def jump_from_dict(self, jump_dict):
        return LoggingJump.from_dict(jump_dict, toolbox=self._toolbox)

    def add_specification(self, specification, save_to_disk=True):
        """Adds a specification to the project.

        Args:
            specification (ProjectItemSpecification): specification to add
            save_to_disk (bool): if True, save the specification to disk

        Returns:
            int: A unique identifier for the specification or None if the operation was unsuccessful
        """
        if self.is_specification_name_reserved(specification.name):
            self._logger.msg_warning.emit(
                f"Specification '{specification.name}' already available to project and will not be added."
            )
            return None
        if save_to_disk and not self.save_specification_file(specification):
            return None
        id_ = self._specification_id()
        self._specifications[id_] = specification
        self.specification_added.emit(specification.name)
        return id_

    def is_specification_name_reserved(self, name):
        """Checks if specification exists.

        Args:
            name (str): specification's name

        Returns:
            bool: True if project has given specification, False otherwise
        """
        return name in (spec.name for spec in self._specifications.values())

    def specifications(self):
        """Yields project's specifications.

        Yield:
            ProjectItemSpecification: specification
        """
        yield from self._specifications.values()

    def _specification_id(self):
        """Creates an id for specification.

        Returns:
            int: new id
        """
        return max(self._specifications) + 1 if self._specifications else 0

    def get_specification(self, name_or_id):
        """Returns project item specification.

        Args:
            name_or_id (str or int): specification's name or id

        Returns:
            ProjectItemSpecification: specification or None if specification was not found
        """
        if isinstance(name_or_id, str):
            name_or_id = self.specification_name_to_id(name_or_id)
        return self._specifications.get(name_or_id, None)

    def specification_name_to_id(self, name):
        """Returns identifier for named specification.

        Args:
            name (str): specification's name

        Returns:
            int: specification's id or None if no such specification exists
        """
        for id_, spec in self._specifications.items():
            if name == spec.name:
                return id_
        return None

    def remove_specification(self, id_or_name):
        """Removes a specification from project.

        Args:
            id_or_name (int or str): specification's id or name
        """
        if isinstance(id_or_name, str):
            id_or_name = self.specification_name_to_id(id_or_name)
        spec = self._specifications[id_or_name]
        self.specification_about_to_be_removed.emit(spec.name)
        del self._specifications[id_or_name]
        for item in self._project_items.values():
            item_spec = item.specification()
            if item_spec is None or item_spec.name != spec.name:
                continue
            self._logger.msg_warning.emit(
                f"Specification <b>{spec.name}</b> is no longer valid for Item <b>{item.name}</b> "
            )
            item.do_set_specification(None)

    def replace_specification(self, name, specification):
        """Replaces an existing specification.

        Saves the given spec to disk and refreshes the spec in all items that use it.

        Args:
            name (str): name of the specification to replace
            specification (ProjectItemSpecification): a specification

        Returns:
            bool: True if operation was successful, False otherwise
        """
        if name != specification.name and self.is_specification_name_reserved(specification.name):
            self._logger.msg_error.emit(f"Specification name {specification.name} already in use.")
            return False
        if not self.save_specification_file(specification):
            return False
        id_ = self.specification_name_to_id(name)
        self._specifications[id_] = specification
        for item in self._project_items.values():
            project_item_spec = item.specification()
            if project_item_spec is None or project_item_spec.name != name:
                continue
            if item.do_set_specification(specification):
                self._logger.msg_success.emit(
                    f"Specification <b>{specification.name}</b> successfully updated in Item <b>{item.name}</b>"
                )
            else:
                self._logger.msg_warning.emit(
                    f"Specification <b>{specification.name}</b> "
                    f"of type <b>{specification.item_type}</b> "
                    f"is no longer valid for Item <b>{item.name}</b> "
                    f"of type <b>{item.item_type()}</b>"
                )
                item.do_set_specification(None)
        self.specification_replaced.emit(name, specification.name)
        return True

    def save_specification_file(self, specification):
        """Saves the given project item specification.

        Save path is determined by specification directory and specification's name.

        Args:
            specification (ProjectItemSpecification): specification to save

        Returns:
            bool: True if operation was successful, False otherwise
        """
        if not specification.definition_file_path:
            # Determine a candidate definition file path *inside* the project folder, for relocatability...
            specs_dir = self.specs_dir
            specs_type_dir = os.path.join(specs_dir, specification.item_type)
            try:
                create_dir(specs_type_dir)
            except OSError:
                self._logger.msg_error.emit(f"Creating directory {specs_type_dir} failed")
                specs_type_dir = specs_dir
            candidate_path = os.path.join(specs_type_dir, shorten(specification.name) + ".json")
            if os.path.exists(candidate_path):
                # Confirm overwriting existing file.
                candidate_path = self._toolbox.prompt_save_location(
                    f"Save {specification.item_type} specification", candidate_path, "JSON (*.json)"
                )
                if candidate_path is None:
                    return False
            specification.definition_file_path = candidate_path
        if not specification.save():
            return False
        self.specification_saved.emit(specification.name, specification.definition_file_path)
        return True

    def add_item(self, item, silent=True):
        """Adds a project to item project.

        Args:
            item (ProjectItem): item to add
            silent (bool): if True, don't log messages
        """
        if item.name in self._project_items:
            raise RuntimeError("Item already in project.")
        self._project_items[item.name] = item
        name = item.name
        self.item_added.emit(name)
        item.set_up()
        if not silent:
            self._logger.msg.emit(f"{item.item_type()} <b>{name}</b> added to project")

    def has_items(self):
        """Returns True if project has project items.

        Returns:
            bool: True if project has items, False otherwise
        """
        return bool(self._project_items)

    def get_item(self, name):
        """Returns project item.

        Args:
            name (str): item's name

        Returns:
            ProjectItem: project item
        """
        return self._project_items[name]

    def get_items(self):
        """Returns all project items.

        Returns:
            list of ProjectItem: all project items
        """
        return list(self._project_items.values())

    def rename_item(self, previous_name, new_name, rename_data_dir_message):
        """Renames a project item

        Args:
            previous_name (str): item's current name
            new_name (str): item's new name
            rename_data_dir_message (str): message to show when renaming item's data directory

        Returns:
            bool: True if item was renamed successfully, False otherwise
        """
        if not new_name.strip() or new_name == previous_name:
            return False
        name_status = self.validate_project_item_name(new_name)
        if name_status == ItemNameStatus.INVALID:
            msg = f"<b>{new_name}</b> contains invalid characters."
            self._logger.error_box.emit("Invalid characters", msg)
            return False
        if name_status == ItemNameStatus.EXISTS:
            msg = f"Project item <b>{new_name}</b> already exists"
            self._logger.error_box.emit("Invalid name", msg)
            return False
        if name_status == ItemNameStatus.SHORT_NAME_EXISTS:
            msg = f"Project item using directory <b>{shorten(new_name)}</b> already exists"
            self._logger.error_box.emit("Invalid name", msg)
            return False
        item = self._project_items.pop(previous_name, None)
        if item is None:
            # Happens when renaming an item, removing, and then closing the project.
            # We try to undo the renaming because it's critical, but the item doesn't exist anymore so it's fine.
            return True
        resources_to_predecessors = item.resources_for_direct_predecessors()
        resources_to_successors = item.resources_for_direct_successors()
        if not item.rename(new_name, rename_data_dir_message):
            self._project_items[previous_name] = item
            return False
        self._project_items[new_name] = item
        for connection in self._connections:
            if connection.source == previous_name:
                connection.source = new_name
            if connection.destination == previous_name:
                connection.destination = new_name
        for jump in self._jumps:
            if jump.source == previous_name:
                jump.source = new_name
            if jump.destination == previous_name:
                jump.destination = new_name
        new_resources_to_predecessors = item.resources_for_direct_predecessors()
        self.notify_resource_replacement_to_predecessors(item, resources_to_predecessors, new_resources_to_predecessors)
        new_resources_to_successors = item.resources_for_direct_successors()
        self.notify_resource_replacement_to_successors(item, resources_to_successors, new_resources_to_successors)
        self.item_renamed.emit(previous_name, new_name)
        self._logger.msg_success.emit(f"Project item <b>{previous_name}</b> renamed to <b>{new_name}</b>.")
        return True

    def validate_project_item_name(self, name):
        """Validates item name.

        Args:
            name (str): proposed project item's name

        Returns:
            ItemNameStatus: validation result
        """
        if any(x in INVALID_CHARS for x in name):
            return ItemNameStatus.INVALID
        if name in self._project_items:
            return ItemNameStatus.EXISTS
        short_name = shorten(name)
        if any(i.short_name == short_name for i in self._project_items.values()):
            return ItemNameStatus.SHORT_NAME_EXISTS
        return ItemNameStatus.OK

    @property
    def connections(self):
        return self._connections

    def find_connection(self, source_name, destination_name):
        """Searches for a connection between given items.

        Args:
            source_name (str): source item's name
            destination_name (str): destination item's name

        Returns:
            Connection: connection instance or None if there is no connection
        """
        return next(
            (c for c in self._connections if c.source == source_name and c.destination == destination_name), None
        )

    def connections_for_item(self, item_name):
        """Returns connections that have given item as source or destination.

        Args:
            item_name (str): item's name

        Returns:
            list of Connection: connections connected to item
        """
        return [c for c in self._connections if item_name in (c.source, c.destination)]

    def add_connection(self, connection, silent=False):
        """Adds a connection to the project.

        Args:
            connection (Connection): connection to add
            silent (bool): If False, prints 'Link establ...' msg to Event Log

        Returns:
            bool: True if connection was added successfully, False otherwise
        """
        if connection in self._connections:
            return False
        if None in (self.dag_with_node(connection.source), self.dag_with_node(connection.destination)):
            return False
        self._connections.append(connection)
        dag = self.dag_with_node(connection.source)
        self.connection_established.emit(connection)
        self._update_jump_icons()
        if not self._is_dag_valid(dag):
            return True  # Connection was added successfully even though DAG is not valid.
        destination = self._project_items[connection.destination]
        self.notify_resource_changes_to_predecessors(destination)
        source = self._project_items[connection.source]
        self.notify_resource_changes_to_successors(source)
        if not silent:
            destination.notify_destination(source)
        self._update_ranks(dag)
        return True

    def remove_connection(self, connection):
        """Removes a connection from the project.

        Args:
            connection (Connection): connection to remove
        """
        self.connection_about_to_be_removed.emit(connection)
        self._connections.remove(connection)
        dags = [self.dag_with_node(connection.source), self.dag_with_node(connection.destination)]
        valid_dags = [dag for dag in dags if self._is_dag_valid(dag)]
        updateable_nodes = set(chain(*(dag.nodes for dag in valid_dags)))
        destination = self._project_items[connection.destination]
        if destination.name in updateable_nodes:
            self._update_item_resources(destination, ExecutionDirection.FORWARD)
        source = self._project_items[connection.source]
        if source.name in updateable_nodes:
            self._update_item_resources(source, ExecutionDirection.BACKWARD)
        for dag in valid_dags:
            self._update_ranks(dag)
        self._update_jump_icons()

    def update_connection(self, connection, source_position, destination_position):
        """Updates existing connection between items.

        Updating does not trigger any updates to the DAG or project items.

        Args:
            connection (LoggingConnection): connection to update
            source_position (str): link's position on source item's icon
            destination_position (str): link's position on destination item's icon
        """
        connection.source_position = source_position
        connection.destination_position = destination_position
        self.connection_updated.emit(connection)

    def jumps_for_item(self, item_name):
        """Returns jumps that have given item as source or destination.

        Args:
            item_name (str): item's name

        Returns:
            list of Jump: jumps connected to item
        """
        return [c for c in self._jumps if item_name in (c.source, c.destination)]

    def add_jump(self, jump, silent=False):
        """Adds a jump to project.

        Args:
            jump (Jump): jump to add
            silent (bool): if True, don't log messages
        """
        self._jumps.append(jump)
        self.jump_added.emit(jump)
        destination = self._project_items[jump.destination]
        source = self._project_items[jump.source]
        self._update_incoming_connection_and_jump_resources(
            destination.name, destination.resources_for_direct_predecessors()
        )
        self._update_outgoing_connection_and_jump_resources(source.name, source.resources_for_direct_successors())
        self._update_jump_icons()
        return True

    def find_jump(self, source_name, destination_name):
        """Searches for a jump between given items.

        Args:
            source_name (str): source item's name
            destination_name (str): destination item's name

        Returns:
            Jump: connection instance or None if there is no jump
        """
        return next((j for j in self._jumps if j.source == source_name and j.destination == destination_name), None)

    def remove_jump(self, jump):
        """Removes a jump from the project.

        Args:
            jump (Jump): jump to remove
        """
        self.jump_about_to_be_removed.emit(jump)
        self._jumps.remove(jump)
        self._update_jump_icons()

    def update_jump(self, jump, source_position, destination_position):
        """Updates an existing jump between items.

        Args:
            jump (LoggingJump): jump to update
            source_position (str): link's position on source item's icon
            destination_position (str): link's position on destination item's icon
        """
        jump.source_position = source_position
        jump.destination_position = destination_position
        self.jump_updated.emit(jump)

    def _update_jump_icons(self):
        """Updates icons for all jumps in the project."""
        for jump in self._jumps:
            jump.jump_link.update_icons()

    def jump_issues(self, jump):
        """Checks if jump is OK.

        Args:
            jump (Jump): jump to check

        Returns:
            list of str: list of issues, if any
        """
        issues = list()
        dag = self.dag_with_node(jump.source)
        if not dag.has_node(jump.destination):
            issues.append("Loop cannot span over separate DAGs.")
        try:
            validate_single_jump(jump, self._jumps, dag)
        except EngineInitFailed as issue:
            issues.append(str(issue))
        return issues

    def _dag_iterator(self):
        """Iterates directed graphs in the project.

        Yields:
            nx.DiGraph
        """
        graph = nx.DiGraph()
        graph.add_nodes_from(self._project_items)
        graph.add_edges_from(((x.source, x.destination) for x in self._connections))
        for nodes in nx.weakly_connected_components(graph):
            yield graph.subgraph(nodes)

    def dags(self):
        """Used in tests. Returns a list of dags in the project.

        Returns:
            list
        """
        return list(self._dag_iterator())

    def node_is_isolated(self, node):
        """Used in tests. Checks if the project item with the given name has any connections.

        Args:
            node (str): Project item name

        Returns:
            bool
        """
        g = self.dag_with_node(node)
        return nx.is_isolate(g, node)

    def dag_with_node(self, node):
        return next((x for x in self._dag_iterator() if x.has_node(node)), None)

    def restore_project_items(self, items_dict, item_factories, silent):
        """Restores project items from dictionary.

        Args:
            items_dict (dict): a mapping from item name to item dict
            item_factories (dict): a mapping from item type to ProjectItemFactory
            silent (bool): if True, suppress a log messages
        """
        for item_name, item_dict in items_dict.items():
            try:
                item_type = item_dict["type"]
            except KeyError as missing:
                raise missing
            factory = item_factories.get(item_type)
            if factory is None:
                self._logger.msg_error.emit(f"Unknown item type <b>{item_type}</b>")
                self._logger.msg_error.emit(f"Loading project item <b>{item_name}</b> failed")
                return
            try:
                project_item = factory.make_item(item_name, item_dict, self._toolbox, self)
            except TypeError:
                self._logger.msg_error.emit(
                    f"Creating <b>{item_type}</b> project item <b>{item_name}</b> failed. "
                    "This is most likely caused by an outdated project file."
                )
                continue
            except KeyError as error:
                self._logger.msg_error.emit(
                    f"Creating <b>{item_type}</b> project item <b>{item_name}</b> failed. "
                    "This is most likely caused by an outdated or corrupted project file "
                    f"(missing JSON key: {str(error)})."
                )
                continue
            project_item.copy_local_data(item_dict)
            self.add_item(project_item, silent)

    def remove_item_by_name(self, item_name, delete_data=False):
        """Removes project item by its name.

        Args:
            item_name (str): Item's name
            delete_data (bool): If set to True, deletes the directories and data associated with the item
        """
        self.item_about_to_be_removed.emit(item_name)
        for c in self.connections_for_item(item_name):
            self.remove_connection(c)
        for j in self.jumps_for_item(item_name):
            self.remove_jump(j)
        item = self._project_items.pop(item_name)
        item.tear_down()
        if delete_data:
            try:
                data_dir = item.data_dir
            except AttributeError:
                data_dir = None
            if data_dir:
                # Remove data directory and all its contents
                self._logger.msg.emit(f"Removing directory <b>{data_dir}</b>")
                try:
                    if not erase_dir(data_dir):
                        self._logger.msg_error.emit("Directory does not exist")
                except OSError:
                    self._logger.msg_error.emit("[OSError] Removing directory failed. Check directory permissions.")
        if not self._project_items:
            self._logger.msg.emit("All items removed from project.")

    def execute_dags(self, dags, execution_permits_list, msg):
        """Executes given dags.

        Args:
            dags (Sequence(DiGraph))
            execution_permits_list (Sequence(dict))
            msg (str): Message depending on execution mode (project or selected)
        """
        self.project_execution_about_to_start.emit()
        self._logger.msg.emit("")
        self._logger.msg.emit("-------------------------------------------------")
        self._logger.msg.emit(f"<b>{msg}</b>")
        self._logger.msg.emit("-------------------------------------------------")
        self._execution_in_progress = True
        self._execute_dags(dags, execution_permits_list)

    def _execute_dags(self, dags, execution_permits_list):
        if self._engine_workers:
            self._logger.msg_error.emit("Execution already in progress.")
            return
        if not self.prepare_remote_execution():
            self.project_execution_finished.emit()
            return
        settings = make_settings_dict_for_engine(self._settings)
        darker_fg_color = QColor(FG_COLOR).darker().name()
        darker = lambda x: f'<span style="color: {darker_fg_color}">{x}</span>'
        for k, (dag, execution_permits) in enumerate(zip(dags, execution_permits_list)):
            dag_identifier = f"{k + 1}/{len(dags)}"
            worker = self.create_engine_worker(dag, execution_permits, dag_identifier, settings)
            if worker is None:
                continue
            self._logger.msg.emit("<b>Starting DAG {0}</b>".format(dag_identifier))
            item_names = (darker(name) if not execution_permits[name] else name for name in nx.topological_sort(dag))
            self._logger.msg.emit(darker(" -> ").join(item_names))
            worker.finished.connect(lambda worker=worker: self._handle_engine_worker_finished(worker))
            self._engine_workers.append(worker)
        timestamp = create_timestamp()
        self._toolbox.start_execution(timestamp)
        # NOTE: Don't start the workers as they are created. They may finish too quickly, before the others
        # are added to ``_engine_workers``, and thus ``_handle_engine_worker_finished()`` will believe
        # that the project is done executing before it's fully loaded.
        for worker in self._engine_workers:
            worker.start()

    def create_engine_worker(self, dag, execution_permits, dag_identifier, settings):
        """Creates and returns a SpineEngineWorker to execute given *validated* dag.

        Args:
            dag (nx.DiGraph): The dag
            execution_permits (dict): mapping item names to a boolean indicating whether to execute it or skip it
            dag_identifier (str): A string identifying the dag, for logging
            settings (dict): project and app settings to send to the spine engine.

        Returns:
            SpineEngineWorker
        """
        item_dicts = {}
        specification_dicts = {}
        items = {name: item for name, item in self._project_items.items() if name in dag.nodes}
        for name, project_item in items.items():
            item_dicts[name] = project_item.item_dict()
            spec = project_item.specification()
            if spec is not None:
                spec_dict = spec.to_dict().copy()
                spec_dict["definition_file_path"] = spec.definition_file_path
                specification_dicts.setdefault(project_item.item_type(), list()).append(spec_dict)
        connections = {c.name: c for c in self._connections if {c.source, c.destination}.intersection(items)}
        connection_dicts = [c.to_dict() for c in connections.values()]
        jumps = {c.name: c for c in self._jumps if execution_permits.get(c.source, False)}
        jump_dicts = [c.to_dict() for c in jumps.values()]
        connections.update(jumps)
        data = {
            "items": item_dicts,
            "specifications": specification_dicts,
            "connections": connection_dicts,
            "jumps": jump_dicts,
            "execution_permits": execution_permits,
            "items_module_name": "spine_items",
            "settings": settings,
            "project_dir": self.project_dir.replace(os.sep, "/"),
        }
        server_address = self._settings.value("appSettings/engineServerAddress", defaultValue="")
        worker = SpineEngineWorker(server_address, data, dag, dag_identifier, items, connections, self._logger)
        return worker

    def _handle_engine_worker_finished(self, worker):
        finished_outcomes = {
            "USER_STOPPED": [self._logger.msg_warning, "stopped by the user"],
            "FAILED": [self._logger.msg_error, "failed"],
            "COMPLETED": [self._logger.msg_success, "completed successfully"],
        }
        outcome = finished_outcomes.get(worker.engine_final_state())
        # print("project._handle_engine_worker_finished() worker state: %s"%outcome)
        if outcome is not None:
            outcome[0].emit(f"<b>DAG {worker.dag_identifier} {outcome[1]}</b>")
        if any(worker.engine_final_state() not in finished_outcomes for worker in self._engine_workers):
            return
        # Only after all workers have finished, notify changes and handle successful executions.
        # Doing it *while* executing leads to deadlocks at acquiring sqlalchemy's infamous _CONFIGURE_MUTEX
        # (needed to create DatabaseMapping instances). It seems that the lock gets confused when
        # being acquired by threads from different processes or maybe even different QThreads.
        # Can't say I really understand the whole extent of it.
        for finished_worker in self._engine_workers:
            for item, direction, state in finished_worker.successful_executions:
                item.handle_execution_successful(direction, state)
            finished_worker.clean_up()
        self._engine_workers.clear()
        # We could remove the transmitted project zip-file here if we want
        # FilePackager.remove_file(
        #     os.path.abspath(os.path.join(self._project_dir, os.pardir, PROJECT_ZIP_FILENAME + ".zip"))
        # )
        self.project_execution_finished.emit()

    def execute_selected(self, names):
        """Executes DAGs corresponding to given project items.

        Args:
            names (Iterable of str): item names to execute
        """
        if not self._project_items:
            self._logger.msg_warning.emit("Project has no items to execute")
            return
        if not names:
            self._logger.msg_warning.emit("Please select a project item and try again.")
            return
        dags = [dag for dag in self._dag_iterator() if set(names) & dag.nodes]
        dags = self._validate_dags(dags)
        execution_permit_list = list()
        for dag in dags:
            execution_permits = {name: name in names for name in dag.nodes}
            execution_permit_list.append(execution_permits)
        self.execute_dags(dags, execution_permit_list, "Executing Selected Directed Acyclic Graphs")

    def execute_project(self):
        """Executes all dags in the project."""
        if not self._project_items:
            self._logger.msg_warning.emit("Project has no items to execute")
            return
        dags = self._validate_dags(self._dag_iterator())
        execution_permit_list = list()
        for dag in dags:
            execution_permit_list.append({item_name: True for item_name in dag.nodes})
        self.execute_dags(dags, execution_permit_list, "Executing All Directed Acyclic Graphs")

    def _validate_dags(self, dags):
        """Validates dags and logs error messages.

        Args:
            dags (list): dags to validate

        Returns:
            list: validated dag
        """
        valid = []
        for dag in dags:
            if not dag.nodes:
                # Should never happen
                continue
            if not nx.is_directed_acyclic_graph(dag):
                items = ", ".join(dag.nodes)
                self._logger.msg_error.emit(f"<b>Skipping execution of items as they are in a cycle: {items}</b>")
                continue
            valid.append(dag)
        return valid

    def stop(self):
        """Stops execution."""
        if not self._execution_in_progress:
            self._logger.msg.emit("No execution in progress")
            return
        self._logger.msg.emit("Stopping...")
        self._execution_in_progress = False
        # Stop engines
        for worker in self._engine_workers:
            worker.stop_engine()

    def notify_resource_changes_to_predecessors(self, item):
        """Updates resources for direct predecessors of given item.

        Args:
            item (ProjectItem): item whose resources have changed
        """
        item_name = item.name
        predecessor_names = {c.source for c in self._incoming_connections(item_name)}
        successor_connections = self._outgoing_connections
        update_resources = self._update_predecessor
        trigger_resources = item.resources_for_direct_predecessors()
        self._notify_resource_changes(
            item_name, predecessor_names, successor_connections, update_resources, trigger_resources
        )
        self._update_incoming_connection_and_jump_resources(item_name, trigger_resources)

    def _update_incoming_connection_and_jump_resources(self, item_name, trigger_resources):
        for connection in self._incoming_connections_and_jumps(item_name):
            connection.receive_resources_from_destination(trigger_resources)

    def notify_resource_changes_to_successors(self, item):
        """Updates resources for direct successors and outgoing connections of given item.

        Args:
            item (ProjectItem): item whose resources have changed
        """
        item_name = item.name
        successor_names = {c.destination for c in self._outgoing_connections(item_name)}
        predecessor_connections = self._incoming_connections
        update_resources = self._update_successor
        trigger_resources = item.resources_for_direct_successors()
        self._notify_resource_changes(
            item_name, successor_names, predecessor_connections, update_resources, trigger_resources
        )
        self._update_outgoing_connection_and_jump_resources(item_name, trigger_resources)

    def _update_outgoing_connection_and_jump_resources(self, item_name, trigger_resources):
        for connection in self._outgoing_connections_and_jumps(item_name):
            connection.receive_resources_from_source(trigger_resources)

    def _notify_resource_changes(
        self, trigger_name, target_names, provider_connections, update_resources, trigger_resources
    ):
        """Updates resources in given direction for immediate neighbours of an item.

        Args:
            trigger_name (str): item whose resources have changed
            target_names (Iterable of str): items to be notified
            provider_connections (Callable): function that receives a target item name and returns a list of
                Connections from resource providers
            update_resources (Callable): function that takes an item name, a list of provider names, and a dictionary
                of resources, and does the updating
            trigger_resources (list of ProjectItemResource): resources from the trigger item
        """
        resource_cache = {trigger_name: trigger_resources}
        for target_name in target_names:
            target_item = self._project_items[target_name]
            connections = provider_connections(target_name)
            update_resources(target_item, connections, resource_cache)

    def notify_resource_replacement_to_successors(self, item, old, new):
        """Replaces resources for direct successors and outgoing connections of given item.

        Args:
            item (ProjectItem): item whose resources have changed
            old (list of ProjectItemResource): old resource
            new (list of ProjectItemResource): new resource
        """
        if not old:
            return
        for connection in self._connections:
            if connection.source != item.name:
                continue
            connection.replace_resources_from_source(old, new)
            old_converted = connection.convert_forward_resources(old)
            new_converted = connection.convert_forward_resources(new)
            self.get_item(connection.destination).replace_resources_from_upstream(old_converted, new_converted)

    def notify_resource_replacement_to_predecessors(self, item, old, new):
        """Replaces resources for direct predecessors.

        Args:
            item (ProjectItem): item whose resources have changed
            old (list of ProjectItemResource): old resources
            new (list of ProjectItemResource): new resources
        """
        for connection in self._connections:
            if connection.destination != item.name:
                continue
            self.get_item(connection.source).replace_resources_from_downstream(old, new)

    def _update_item_resources(self, target_item, direction):
        """Updates up or downstream resources for a single project item.
        Called in both directions after removing a Connection.

        Args:
            target_item (ProjectItem): item whose resource need update
            direction (ExecutionDirection): FORWARD updates resources from upstream, BACKWARD from downstream
        """
        target_name = target_item.name
        if direction == ExecutionDirection.FORWARD:
            connections = self._incoming_connections(target_name)
            self._update_successor(target_item, connections, resource_cache={})
        else:
            connections = self._outgoing_connections(target_name)
            self._update_predecessor(target_item, connections, resource_cache={})

    def predecessor_names(self, name):
        """Collects direct predecessor item names.

        Args:
            name (str): name of the project item whose predecessors to collect

        Returns:
            set of str: direct predecessor names
        """
        return {c.source for c in self._incoming_connections(name)}

    def successor_names(self, name):
        """Collects direct successor item names.

        Args:
            name (str): name of the project item whose successors to collect

        Returns:
            set of str: direct successor names
        """
        return {c.destination for c in self._outgoing_connections(name)}

    def _outgoing_connections(self, name):
        """Collects outgoing connections.

        Args:
            name (str): name of the project item whose connections to collect

        Returns:
            set of Connection: outgoing connections
        """
        return [c for c in self._connections if c.source == name]

    def _outgoing_jumps(self, name):
        """Collects outgoing jumps.

        Args:
            name (str): name of the project item whose jumps to collect

        Returns:
            set of Jump: outgoing jumps
        """
        return [c for c in self._jumps if c.source == name]

    def _outgoing_connections_and_jumps(self, name):
        """Collects outgoing connections and jumps.

        Args:
            name (str): name of the project item whose connections and jumps to collect

        Returns:
            set of Connection/Jump: outgoing connections and jumps
        """
        return self._outgoing_connections(name) + self._outgoing_jumps(name)

    def _incoming_connections(self, name):
        """Collects incoming connections.

        Args:
            name (str): name of the project item whose connections to collect

        Returns:
            set of Connection: incoming connections
        """
        return [c for c in self._connections if c.destination == name]

    def _incoming_jumps(self, name):
        """Collects incoming jumps.

        Args:
            name (str): name of the project item whose jumps to collect

        Returns:
            set of Jump: incoming jumps
        """
        return [c for c in self._jumps if c.destination == name]

    def _incoming_connections_and_jumps(self, name):
        """Collects incoming connections and jumps.

        Args:
            name (str): name of the project item whose connections and jumps to collect

        Returns:
            set of Connection/Jump: incoming connections
        """
        return self._incoming_connections(name) + self._incoming_jumps(name)

    def _update_successor(self, successor, incoming_connections, resource_cache):
        combined_resources = list()
        for conn in incoming_connections:
            item_name = conn.source
            predecessor = self._project_items[item_name]
            resources = resource_cache.get(item_name)
            if resources is None:
                resources = predecessor.resources_for_direct_successors()
                resource_cache[item_name] = resources
            resources = conn.convert_forward_resources(resources)
            combined_resources += resources
        successor.upstream_resources_updated(combined_resources)

    def _update_predecessor(self, predecessor, outgoing_connections, resource_cache):
        combined_resources = list()
        for conn in outgoing_connections:
            item_name = conn.destination
            successor = self._project_items[item_name]
            resources = resource_cache.get(item_name)
            if resources is None:
                resources = successor.resources_for_direct_predecessors()
                resource_cache[item_name] = resources
            combined_resources += resources
        predecessor.downstream_resources_updated(combined_resources)

    def _is_dag_valid(self, dag):
        if not nx.is_directed_acyclic_graph(dag):
            edges = _edges_causing_loops(dag)
            for node in dag.nodes:
                self._project_items[node].invalidate_workflow(edges)
            return False
        for node in dag.nodes:
            self._project_items[node].revalidate_workflow()
        return True

    def _update_ranks(self, dag):
        node_successors_ = node_successors(dag)
        ranks = _ranks(node_successors_)
        for item_name in node_successors_:
            item = self._project_items[item_name]
            item.set_rank(ranks[item_name])

    @property
    def settings(self):
        return self._settings

    def prepare_remote_execution(self):
        if self._settings.value("engineSettings/remoteExecutionEnabled", defaultValue="false") == "true":
            # Check remote execution settings
            host = self._settings.value("engineSettings/remoteHost", "")  # Host name
            port = self._settings.value("engineSettings/remotePort", "")  # Host port
            sec_model = self._settings.value("engineSettings/remoteSecurityModel", "")  # ZQM security model
            security = ClientSecurityModel.NONE if not sec_model else ClientSecurityModel.STONEHOUSE
            sec_folder = (
                ""
                if security == ClientSecurityModel.NONE
                else self._settings.value("engineSettings/remoteSecurityFolder", "")
            )
            if not host:
                self._logger.msg_error.emit("Spine Engine Server <b>host address</b> missing. "
                                            "Please enter host in <b>Settings->Engine</b>.")
                return False
            elif not port:
                self._logger.msg_error.emit("Spine Engine Server <b>port</b> missing. "
                                            "Please select port in <b>Settings->Engine</b>.")
                return False
            self._logger.msg.emit(f"Establishing connection to Spine Engine Server in <b>{host}:{port}</b>")
            try:
                ZMQClient("tcp", host, port, sec_model, sec_folder, ping=True)  # Ping server
            except RemoteEngineFailed as e:
                self._logger.msg_error.emit(f"Server is not responding. {e}. "
                                            f"Check settings in <b>Settings->Engine</b>.")
                return False
            # When preparing for remote execution, archive the project into a zip-file
            dest_dir = os.path.join(self.project_dir, os.pardir)  # Parent dir of project_dir TODO: Find a better dst
            try:
                FilePackager.package(src_folder=self.project_dir, dst_folder=dest_dir, fname=PROJECT_ZIP_FILENAME)
            except Exception as e:
                self._logger.msg_error.emit(f"{e}")
                return False
            project_zip_file = os.path.abspath(os.path.join(self.project_dir, os.pardir, PROJECT_ZIP_FILENAME + '.zip'))
            if not os.path.isfile(project_zip_file):
                self._logger.msg_error.emit(f"Project zip-file {project_zip_file} does not exist")
                return False
            file_size = os.path.getsize(project_zip_file)
            self._logger.msg.emit(f"Connection established. Transmitting <b>{PROJECT_ZIP_FILENAME + '.zip'} "
                                  f"[size:{file_size} B]</b> to server.")
        return True

    def tear_down(self):
        """Cleans up project."""
        if self._execution_in_progress:
            self.stop()
        self.project_about_to_be_torn_down.emit()
        for item in self._project_items.values():
            item.tear_down()
        self.deleteLater()


def node_successors(g):
    """Returns a dict mapping nodes in topological order to a list of successors.

    Args:
        g (nx.DiGraph)

    Returns:
        dict
    """
    return {n: list(g.successors(n)) for n in nx.topological_sort(g)}


def _edges_causing_loops(g):
    """Returns a list of edges whose removal from g results in it becoming acyclic.

    Args:
        g (nx.DiGraph)

    Returns:
        list
    """
    result = list()
    h = g.copy()  # Let's work on a copy of the graph
    while True:
        try:
            cycle = list(nx.find_cycle(h))
        except nx.NetworkXNoCycle:
            break
        edge = random.choice(cycle)
        h.remove_edge(*edge)
        result.append(edge)
    return result


def _ranks(node_successors):
    """
    Calculates node ranks.

    Args:
        node_successors (dict): a mapping from successor name to a list of predecessor names

    Returns:
        dict: a mapping from node name to rank
    """
    node_predecessors = dict()
    for predecessor, successors in node_successors.items():
        node_predecessors.setdefault(predecessor, list())
        for successor in successors:
            node_predecessors.setdefault(successor, list()).append(predecessor)
    ranking = []
    while node_predecessors:
        same_ranks = [node for node, predecessor in node_predecessors.items() if not predecessor]
        for ranked_node in same_ranks:
            del node_predecessors[ranked_node]
            for node, successors in node_predecessors.items():
                node_predecessors[node] = [s for s in successors if s != ranked_node]
        ranking.append(same_ranks)
    return {node: rank for rank, nodes in enumerate(ranking) for node in nodes}
