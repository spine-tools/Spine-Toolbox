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

"""QUndoCommand subclasses for modifying the project."""
from PySide6.QtGui import QUndoCommand
from spine_engine.project_item.connection import Jump


class SpineToolboxCommand(QUndoCommand):
    def __init__(self):
        super().__init__()
        self.successfully_undone = False
        """Flag to register the outcome of undoing a critical command, so toolbox can react afterwards."""

    @property
    def is_critical(self):
        """Returns True if this command needs to be undone before
        closing the project without saving changes.
        """
        return False


class SetItemSpecificationCommand(SpineToolboxCommand):
    """Command to set the specification for a project item."""

    def __init__(self, item_name, spec, old_spec, project):
        """
        Args:
            item_name (str): item's name
            spec (ProjectItemSpecification): the new spec
            old_spec (ProjectItemSpecification): the old spec
            project (SpineToolboxProject): project
        """
        super().__init__()
        self._item_name = item_name
        self._spec = spec
        self._old_spec = old_spec
        self._project = project
        self.setText(f"set specification of {item_name}")

    def redo(self):
        item = self._project.get_item(self._item_name)
        item.do_set_specification(self._spec)

    def undo(self):
        item = self._project.get_item(self._item_name)
        item.do_set_specification(self._old_spec)


class MoveIconCommand(SpineToolboxCommand):
    """Command to move icons in the Design view."""

    def __init__(self, icon, project):
        """
        Args:
            icon (ProjectItemIcon): the icon
            project (SpineToolboxProject): project
        """
        super().__init__()
        self._project = project
        icon_group = icon.scene().icon_group
        self._representative = next(iter(icon_group), None)
        if self._representative is None:
            self.setObsolete(True)
        self._previous_pos = {x.name(): x.previous_pos for x in icon_group}
        self._current_pos = {x.name(): x.scenePos() for x in icon_group}
        if len(icon_group) == 1:
            self.setText(f"move {self._representative.name()}")
        else:
            self.setText("move multiple items")

    def redo(self):
        self._move_to(self._current_pos)

    def undo(self):
        self._move_to(self._previous_pos)

    def _move_to(self, positions):
        for item_name, position in positions.items():
            icon = self._project.get_item(item_name).get_icon()
            icon.set_pos_without_bumping(position)
        self._representative.update_links_geometry()
        self._representative.notify_item_move()


class SetProjectDescriptionCommand(SpineToolboxCommand):
    """Command to set the project description."""

    def __init__(self, project, description):
        """
        Args:
            project (SpineToolboxProject): the project
            description (str): The new description
        """
        super().__init__()
        self.project = project
        self.redo_desc = description
        self.undo_desc = self.project.description
        self.setText("set project description")

    def redo(self):
        self.project.set_description(self.redo_desc)

    def undo(self):
        self.project.set_description(self.undo_desc)


class AddProjectItemsCommand(SpineToolboxCommand):
    """Command to add items."""

    def __init__(self, project, items_dict, item_factories):
        """
        Args:
            project (SpineToolboxProject): the project
            items_dict (dict): a mapping from item name to item dict
            item_factories (dict): a mapping from item type to ProjectItemFactory
            silent (bool): If True, suppress messages
        """
        super().__init__()
        self._project = project
        self._items_dict = items_dict
        self._item_factories = item_factories
        if not items_dict:
            self.setObsolete(True)
        elif len(items_dict) == 1:
            self.setText(f"add {next(iter(items_dict))}")
        else:
            self.setText("add multiple items")

    def redo(self):
        self._project.restore_project_items(self._items_dict, self._item_factories)

    def undo(self):
        for item_name in self._items_dict:
            self._project.remove_item_by_name(item_name, delete_data=True)


class RemoveAllProjectItemsCommand(SpineToolboxCommand):
    """Command to remove all items from project."""

    def __init__(self, project, item_factories, delete_data=False):
        """
        Args:
            project (SpineToolboxProject): the project
            item_factories (dict): a mapping from item type to ProjectItemFactory
            delete_data (bool): If True, deletes the directories and data associated with the items
        """
        super().__init__()
        self._project = project
        self._item_factories = item_factories
        self._items_dict = {i.name: i.item_dict() for i in self._project.get_items()}
        self._connection_dicts = [c.to_dict() for c in self._project.connections]
        self._delete_data = delete_data
        self.setText("remove all items")

    def redo(self):
        for name in self._items_dict:
            self._project.remove_item_by_name(name, self._delete_data)

    def undo(self):
        self._project.restore_project_items(self._items_dict, self._item_factories)
        for connection_dict in self._connection_dicts:
            self._project.add_connection(self._project.connection_from_dict(connection_dict), silent=True)


class RemoveProjectItemsCommand(SpineToolboxCommand):
    """Command to remove items."""

    def __init__(self, project, item_factories, item_names, delete_data=False):
        """
        Args:
            project (SpineToolboxProject): The project
            item_factories (dict): a mapping from item type to ProjectItemFactory
            item_names (list of str): Item names
            delete_data (bool): If True, deletes the directories and data associated with the item
        """
        super().__init__()
        self._project = project
        self._item_factories = item_factories
        items = [self._project.get_item(name) for name in item_names]
        self._items_dict = {i.name: i.item_dict() for i in items}
        self._delete_data = delete_data
        connections = sum((self._project.connections_for_item(name) for name in item_names), [])
        unique_connections = {(c.source, c.destination): c for c in connections}.values()
        self._connection_dicts = [c.to_dict() for c in unique_connections]
        jumps = sum((self._project.jumps_for_item(name) for name in item_names), [])
        unique_jumps = {(c.source, c.destination): c for c in jumps}.values()
        self._jump_dicts = [c.to_dict() for c in unique_jumps]
        if not item_names:
            self.setObsolete(True)
        elif len(item_names) == 1:
            self.setText(f"remove {item_names[0]}")
        else:
            self.setText("remove multiple items")

    def redo(self):
        for name in self._items_dict:
            self._project.remove_item_by_name(name, self._delete_data)

    def undo(self):
        self._project.restore_project_items(self._items_dict, self._item_factories)
        for connection_dict in self._connection_dicts:
            self._project.add_connection(self._project.connection_from_dict(connection_dict), silent=True)
        for jump_dict in self._jump_dicts:
            self._project.add_jump(self._project.jump_from_dict(jump_dict), silent=True)


class RenameProjectItemCommand(SpineToolboxCommand):
    """Command to rename project items."""

    def __init__(self, project, previous_name, new_name):
        """
        Args:
            project (SpineToolboxProject): the project
            previous_name (str): item's previous name
            new_name (str): the new name
        """
        super().__init__()
        self._project = project
        self._previous_name = previous_name
        self._new_name = new_name
        self.setText(f"rename {self._previous_name} to {self._new_name}")

    def redo(self):
        box_title = f"Doing '{self.text()}'"
        if not self._project.rename_item(self._previous_name, self._new_name, box_title):
            self.setObsolete(True)

    def undo(self):
        box_title = f"Undoing '{self.text()}'"
        self.successfully_undone = self._project.rename_item(self._new_name, self._previous_name, box_title)

    @property
    def is_critical(self):
        return True


class AddConnectionCommand(SpineToolboxCommand):
    """Command to add connection between project items."""

    def __init__(self, project, source_name, source_position, destination_name, destination_position):
        """
        Args:
            project (SpineToolboxProject): project
            source_name (str): source item's name
            source_position (str): link's position on source item's icon
            destination_name (str): destination item's name
            destination_position (str): link's position on destination item's icon
        """
        super().__init__()
        self._project = project
        self._source_name = source_name
        self._source_position = source_position
        self._destination_name = destination_name
        self._destination_position = destination_position
        existing = self._project.find_connection(source_name, destination_name)
        if existing is not None:
            self._old_source_position = existing.source_position
            self._old_destination_position = existing.destination_position
            self._action = "update"
        else:
            self._action = "add"
        connection_name = f"link from {source_name} to {destination_name}"
        self.setText(f"{self._action} {connection_name}")

    def redo(self):
        if self._action == "update":
            existing = self._project.find_connection(self._source_name, self._destination_name)
            self._project.update_connection(existing, self._source_position, self._destination_position)
            return
        if not self._project.add_connection(
            self._source_name, self._source_position, self._destination_name, self._destination_position
        ):
            self.setObsolete(True)

    def undo(self):
        existing = self._project.find_connection(self._source_name, self._destination_name)
        if self._action == "update":
            self._project.update_connection(existing, self._old_source_position, self._old_destination_position)
            return
        self._project.remove_connection(existing)


class RemoveConnectionsCommand(SpineToolboxCommand):
    """Command to remove links."""

    def __init__(self, project, connections):
        """
        Args:
            project (SpineToolboxProject): project
            connections (list of LoggingConnection): the connections
        """
        super().__init__()
        self._project = project
        self._connections_dict = {(c.source, c.destination): c.to_dict() for c in connections}
        if not connections:
            self.setObsolete(True)
        elif len(connections) == 1:
            c = connections[0]
            self.setText(f"remove link from {c.source} to {c.destination}")
        else:
            self.setText("remove multiple links")

    def redo(self):
        for source, destination in self._connections_dict:
            connection = self._project.find_connection(source, destination)
            self._project.remove_connection(connection)

    def undo(self):
        for connection_dict in self._connections_dict.values():
            self._project.add_connection(self._project.connection_from_dict(connection_dict), silent=True)


class AddJumpCommand(SpineToolboxCommand):
    """Command to add a jump between project items."""

    def __init__(self, project, source_name, source_position, destination_name, destination_position):
        """
        Args:
            project (SpineToolboxProject): project
            source_name (str): source item's name
            source_position (str): link's position on source item's icon
            destination_name (str): destination item's name
            destination_position (str): link's position on destination item's icon
        """
        super().__init__()
        self._project = project
        self._source_position = source_position
        self._destination_position = destination_position
        self._existing = self._project.find_jump(source_name, destination_name)
        if self._existing is not None:
            self._old_source_position = self._existing.source_position
            self._old_destination_position = self._existing.destination_position
            action = "update"
        else:
            jump_dict = Jump(source_name, source_position, destination_name, destination_position).to_dict()
            self._jump = self._project.jump_from_dict(jump_dict)
            action = "add"
        jump_name = f"jump link from {source_name} to {destination_name}"
        self.setText(f"{action} {jump_name}")

    def redo(self):
        if self._existing:
            self._project.update_jump(self._existing, self._source_position, self._destination_position)
            return
        if not self._project.add_jump(self._jump):
            self.setObsolete(True)

    def undo(self):
        if self._existing:
            self._project.update_jump(self._existing, self._old_source_position, self._old_destination_position)
            return
        self._project.remove_jump(self._jump)


class RemoveJumpsCommand(SpineToolboxCommand):
    """Command to remove jumps."""

    def __init__(self, project, jumps):
        """
        Args:
            project (SpineToolboxProject): project
            jumps (list of LoggingJump): the jumps
        """
        super().__init__()
        self._project = project
        self._jump_dicts = {(j.source, j.destination): j.to_dict() for j in jumps}
        if not jumps:
            self.setObsolete(True)
        elif len(jumps) == 1:
            j = jumps[0]
            self.setText(f"remove loop from {j.source} to {j.destination}")
        else:
            self.setText("remove multiple loops")

    def redo(self):
        for source, destination in self._jump_dicts:
            jump = self._project.find_jump(source, destination)
            self._project.remove_jump(jump)

    def undo(self):
        for jump_dict in self._jump_dicts.values():
            self._project.add_jump(self._project.jump_from_dict(jump_dict), silent=True)


class SetJumpConditionCommand(SpineToolboxCommand):
    """Command to set jump condition."""

    def __init__(self, project, jump, jump_properties, condition):
        """
        Args:
            project (SpineToolboxProject): project
            jump (Jump): target jump
            jump_properties (JumpPropertiesWidget): jump's properties tab
            condition (dict): jump condition
        """
        super().__init__()
        self._project = project
        self._jump_properties = jump_properties
        self._jump_source = jump.source
        self._jump_destination = jump.destination
        self._condition = condition
        self._previous_condition = jump.condition
        self.setText(f"change loop condition for jump {jump.name}")

    def redo(self):
        jump = self._project.find_jump(self._jump_source, self._jump_destination)
        self._jump_properties.set_condition(jump, self._condition)

    def undo(self):
        jump = self._project.find_jump(self._jump_source, self._jump_destination)
        self._jump_properties.set_condition(jump, self._previous_condition)


class UpdateJumpCmdLineArgsCommand(SpineToolboxCommand):
    """Command to update Jump command line args."""

    def __init__(self, project, jump, jump_properties, cmd_line_args):
        """
        Args:
            project (SpineToolboxProject): project
            jump (Jump): jump
            jump_properties (JumpPropertiesWidget): the item
            cmd_line_args (list): list of command line args
        """
        super().__init__()
        self._project = project
        self._jump_properties = jump_properties
        self._jump_source = jump.source
        self._jump_destination = jump.destination
        self._redo_cmd_line_args = cmd_line_args
        self._undo_cmd_line_args = jump.cmd_line_args
        self.setText(f"change command line arguments of jump {jump.name}")

    def redo(self):
        jump = self._project.find_jump(self._jump_source, self._jump_destination)
        self._jump_properties.update_cmd_line_args(jump, self._redo_cmd_line_args)

    def undo(self):
        jump = self._project.find_jump(self._jump_source, self._jump_destination)
        self._jump_properties.update_cmd_line_args(jump, self._undo_cmd_line_args)


class SetFiltersOnlineCommand(SpineToolboxCommand):
    """Command to toggle filter value."""

    def __init__(self, project, connection, resource, filter_type, online):
        """
        Args:
            project (SpineToolboxProject): project
            connection (Connection): connection
            resource (str): resource label
            filter_type (str): filter type identifier
            online (dict): mapping from scenario/tool id to online flag
        """
        super().__init__()
        self._project = project
        self._resource = resource
        self._filter_type = filter_type
        self._online = online
        self._source_name = connection.source
        self._destination_name = connection.destination
        self.setText(
            f"change {filter_type} for {resource} at link from {self._source_name} to {self._destination_name}"
        )

    def redo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.resource_filter_model.set_online(self._resource, self._filter_type, self._online)

    def undo(self):
        negated_online = {id_: not online for id_, online in self._online.items()}
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.resource_filter_model.set_online(self._resource, self._filter_type, negated_online)


class SetConnectionDefaultFilterOnlineStatus(SpineToolboxCommand):
    """Command to set connection's default filter online status."""

    def __init__(self, project, connection, default_status):
        """
        Args:
            project (SpineToolboxProject): project
            connection (LoggingConnection): connection
            default_status (bool): default filter online status
        """
        super().__init__()
        self.setText(f"change options in connection {connection.name}")
        self._project = project
        self._source_name = connection.source
        self._destination_name = connection.destination
        self._checked = default_status

    def redo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_filter_default_online_status(self._checked)

    def undo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_filter_default_online_status(not self._checked)


class SetConnectionFilterTypeEnabled(SpineToolboxCommand):
    """Command to enable and disable connection's filter types."""

    def __init__(self, project, connection, filter_type, enabled):
        """
        Args:
            project (SpineToolboxProject): project
            connection (LoggingConnection): connection
            filter_type (str): filter type
            enabled (bool): whether filter type is enabled
        """
        super().__init__()
        self.setText(f"change  {connection.name}")
        self._project = project
        self._source_name = connection.source
        self._destination_name = connection.destination
        self._filter_type = filter_type
        self._enabled = enabled

    def redo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_filter_type_enabled(self._filter_type, self._enabled)

    def undo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_filter_type_enabled(self._filter_type, not self._enabled)


class SetConnectionOptionsCommand(SpineToolboxCommand):
    """Command to set connection options."""

    def __init__(self, project, connection, options):
        """
        Args:
            project (SpineToolboxProject): project
            connection (LoggingConnection): project
            options (dict): containing options to be set
        """
        super().__init__()
        self._project = project
        self._source_name = connection.source
        self._destination_name = connection.destination
        self._new_options = connection.options.copy()
        self._new_options.update(options)
        self._old_options = connection.options.copy()
        self.setText(f"change options in connection {connection.name}")

    def redo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_connection_options(self._new_options)

    def undo(self):
        connection = self._project.find_connection(self._source_name, self._destination_name)
        connection.set_connection_options(self._old_options)


class AddSpecificationCommand(SpineToolboxCommand):
    """Command to add item specification to a project."""

    def __init__(self, project, specification, save_to_disk):
        """
        Args:
            project (ToolboxUI): the toolbox
            specification (ProjectItemSpecification): the spec
            save_to_disk (bool): If True, save the specification to disk
        """
        super().__init__()
        self._project = project
        self._specification = specification
        self._save_to_disk = save_to_disk
        self._spec_id = None
        self.setText(f"add specification {specification.name}")

    def redo(self):
        self._spec_id = self._project.add_specification(self._specification, save_to_disk=self._save_to_disk)
        if self._spec_id is None:
            self.setObsolete(True)
        else:
            self._save_to_disk = False

    def undo(self):
        self._project.remove_specification(self._spec_id)


class ReplaceSpecificationCommand(SpineToolboxCommand):
    """Command to replace item specification in project."""

    def __init__(self, project, name, specification):
        """
        Args:
            project (ToolboxUI): the toolbox
            name (str): the name of the spec to be replaced
            specification (ProjectItemSpecification): the new spec
        """
        super().__init__()
        self._project = project
        self._name = name
        self._specification = specification
        self._undo_name = specification.name
        self._undo_specification = self._project.get_specification(name)
        self.setText(f"replace specification {name} by {specification.name}")

    def redo(self):
        if not self._project.replace_specification(self._name, self._specification):
            self.setObsolete(True)

    def undo(self):
        self.successfully_undone = self._project.replace_specification(self._undo_name, self._undo_specification)

    @property
    def is_critical(self):
        return True


class RemoveSpecificationCommand(SpineToolboxCommand):
    """Command to remove specs from a project."""

    def __init__(self, project, name):
        """
        Args:
            project (SpineToolboxProject): the project
            name (str): specification's name
        """
        super().__init__()
        self._project = project
        self._specification = self._project.get_specification(name)
        self._spec_id = self._project.specification_name_to_id(name)
        self.setText(f"remove specification {self._specification.name}")

    def redo(self):
        self._project.remove_specification(self._spec_id)

    def undo(self):
        self._spec_id = self._project.add_specification(self._specification, save_to_disk=False)


class SaveSpecificationAsCommand(SpineToolboxCommand):
    """Command to remove item specs from a project."""

    def __init__(self, project, name, path):
        """
        Args:
            project (SpineToolboxProject): the project
            name (str): specification's name
            path (str): new specification file location
        """
        super().__init__()
        self._project = project
        self._path = path
        self._spec_id = self._project.specification_name_to_id(name)
        specification = self._project.get_specification(self._spec_id)
        self._previous_path = specification.definition_file_path
        self.setText(f"save specification {name} as")

    def redo(self):
        specification = self._project.get_specification(self._spec_id)
        specification.definition_file_path = self._path
        self._project.save_specification_file(specification)

    def undo(self):
        specification = self._project.get_specification(self._spec_id)
        specification.definition_file_path = self._previous_path
        self._project.save_specification_file(specification)
