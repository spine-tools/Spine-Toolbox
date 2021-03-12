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
QUndoCommand subclasses for modifying the project.

:authors: M. Marin (KTH)
:date:   12.2.2020
"""
from PySide2.QtWidgets import QUndoCommand
from spine_engine.project_item.connection import Connection


class SpineToolboxCommand(QUndoCommand):
    successfully_undone = False
    """Flag to register the outcome of undoing a critical command, so toolbox can react afterwards."""

    @staticmethod
    def is_critical():
        """Returns True if this command needs to be undone before
        closing the project without saving changes.
        """
        return False


class SetItemSpecificationCommand(SpineToolboxCommand):
    def __init__(self, item, specification):
        """Command to set the specification for a Tool.

        Args:
            item (ProjectItem): the Item
            specification (ProjectItemSpecification): the new spec
        """
        super().__init__()
        self.item = item
        self.redo_specification = specification
        self.setText(f"set specification of {item.name}")

    def redo(self):
        self.item.do_set_specification(self.redo_specification)

    def undo(self):
        self.item.undo_set_specification()


class MoveIconCommand(SpineToolboxCommand):
    def __init__(self, icon, project):
        """Command to move icons in the Design view.

        Args:
            icon (ProjectItemIcon): the icon
            project (SpineToolboxProject): project
        """
        super().__init__()
        self._project = project
        self._previous_pos = {x.name(): x.previous_pos for x in icon.icon_group}
        self._current_pos = {x.name(): x.current_pos for x in icon.icon_group}
        if len(icon.icon_group) == 1:
            self.setText(f"move {next(iter(icon.icon_group)).name()}")
        else:
            self.setText("move multiple items")

    def redo(self):
        self._move_to(self._current_pos)

    def undo(self):
        self._move_to(self._previous_pos)

    def _move_to(self, positions):
        icon_group = set()
        for item_name, position in positions.items():
            icon = self._project.get_item(item_name).get_icon()
            icon.setPos(position)
            icon_group.add(icon)
        for icon in icon_group:
            icon.icon_group = icon_group
        representative = next(iter(icon_group))
        representative.update_links_geometry()
        representative.notify_item_move()


class SetProjectNameCommand(SpineToolboxCommand):
    def __init__(self, project, name):
        """Command to set the project name.

        Args:
            project (SpineToolboxProject): the project
            name (str): The new name
        """
        super().__init__()
        self.project = project
        self.redo_name = name
        self.undo_name = self.project.name
        self.setText("rename project")

    def redo(self):
        self.project.set_name(self.redo_name)

    def undo(self):
        self.project.set_name(self.undo_name)


class SetProjectDescriptionCommand(SpineToolboxCommand):
    def __init__(self, project, description):
        """Command to set the project description.

        Args:
            project (SpineToolboxProject): the project
            description (str): The new description
        """
        super().__init__()
        self.project = project
        self.redo_description = description
        self.undo_description = self.project.description
        self.setText("change project description")

    def redo(self):
        self.project.set_description(self.redo_description)

    def undo(self):
        self.project.set_description(self.undo_description)


class AddProjectItemsCommand(SpineToolboxCommand):
    def __init__(self, project, items_dict, set_selected=False, verbosity=True):
        """Command to add items.

        Args:
            project (SpineToolboxProject): the project
            items_dict (dict): a mapping from item name to item dict
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        super().__init__()
        self._project = project
        self._items_dict = items_dict
        self._set_selected = set_selected
        self._verbosity = verbosity
        if not items_dict:
            self.setObsolete(True)
        elif len(items_dict) == 1:
            self.setText(f"add {next(iter(items_dict))}")
        else:
            self.setText("add multiple items")

    def redo(self):
        self._project.make_and_add_project_items(self._items_dict, self._set_selected, self._verbosity)

    def undo(self):
        for item_name in self._items_dict:
            self._project.remove_item_by_name(item_name, delete_data=True)


class RemoveAllProjectItemsCommand(SpineToolboxCommand):
    def __init__(self, project, delete_data=False):
        """Command to remove all items from project.

        Args:
            project (SpineToolboxProject): the project
            delete_data (bool): If True, deletes the directories and data associated with the items
        """
        super().__init__()
        self._project = project
        self._items_dict = {i.name: i.item_dict() for i in self._project.get_items()}
        self._connection_dicts = [c.to_dict() for c in self._project.connections]
        self._delete_data = delete_data
        self.setText("remove all items")

    def redo(self):
        for name in self._items_dict:
            self._project.remove_item_by_name(name, self._delete_data)

    def undo(self):
        self._project.make_and_add_project_items(self._items_dict, verbosity=False)
        for connection_dict in self._connection_dicts:
            self._project.add_connection(Connection.from_dict(connection_dict))


class RemoveProjectItemsCommand(SpineToolboxCommand):
    def __init__(self, project, item_names, delete_data=False):
        """Command to remove items.

        Args:
            project (SpineToolboxProject): The project
            item_names (list of str): Item names
            delete_data (bool): If True, deletes the directories and data associated with the item
        """
        super().__init__()
        self._project = project
        items = [self._project.get_item(name) for name in item_names]
        self._items_dict = {i.name: i.item_dict() for i in items}
        self._delete_data = delete_data
        connections = sum((self._project.connections_for_item(name) for name in item_names), [])
        unique_connections = {(c.source, c.destination): c for c in connections}.values()
        self._connection_dicts = [c.to_dict() for c in unique_connections]
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
        self._project.make_and_add_project_items(self._items_dict, verbosity=False)
        for connection_dict in self._connection_dicts:
            self._project.add_connection(Connection.from_dict(connection_dict))


class RenameProjectItemCommand(SpineToolboxCommand):
    def __init__(self, project, previous_name, new_name):
        """Command to rename project items.

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

    @staticmethod
    def is_critical():
        return True


class AddConnectionCommand(SpineToolboxCommand):
    def __init__(self, project, source_name, source_position, destination_name, destination_position):
        """Command to add connection between project items.

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
        self._destination_name = destination_name
        self._connection_dict = Connection(
            source_name, source_position, destination_name, destination_position
        ).to_dict()
        replaced_connection = self._project.find_connection(source_name, destination_name)
        self._replaced_connection_dict = replaced_connection.to_dict() if replaced_connection is not None else None
        self._connection_name = f"link from {source_name} to {destination_name}"

    def redo(self):
        if self._replaced_connection_dict is None:
            success = self._project.add_connection(Connection.from_dict(self._connection_dict))
            if not success:
                self.setObsolete(True)
        else:
            self._project.replace_connection(
                Connection.from_dict(self._replaced_connection_dict), Connection.from_dict(self._connection_dict)
            )
        action = "add" if self._replaced_connection_dict is None else "replace"
        self.setText(f"{action} {self._connection_name}")

    def undo(self):
        if self._replaced_connection_dict is None:
            connection = self._project.find_connection(self._source_name, self._destination_name)
            self._project.remove_connection(connection)
        else:
            connection = self._project.find_connection(self._source_name, self._destination_name)
            self._project.replace_connection(connection, Connection.from_dict(self._replaced_connection_dict))


class RemoveConnectionsCommand(SpineToolboxCommand):
    def __init__(self, project, connections):
        """Command to remove links.

        Args:
            project (SpineToolboxProject): project
            connections (list of Connection): the connections
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
            self._project.add_connection(Connection.from_dict(connection_dict))


class SetFiltersOnlineCommand(SpineToolboxCommand):
    def __init__(self, resource_filter_model, resource, filter_type, online):
        """Command to toggle filter value.

        Args:
            resource_filter_model (ResourceFilterModel): filter model
            resource (str): resource label
            filter_type (str): filter type identifier
            online (dict): mapping from scenario/tool id to online flag
        """
        super().__init__()
        self._resource_filter_model = resource_filter_model
        self._resource = resource
        self._filter_type = filter_type
        self._online = online
        source_name = self._resource_filter_model.connection.source
        destination_name = self._resource_filter_model.connection.destination
        self.setText(f"change {filter_type} for {resource} at link from {source_name} to {destination_name}")

    def redo(self):
        self._resource_filter_model.set_online(self._resource, self._filter_type, self._online)

    def undo(self):
        negated_online = {id_: not online for id_, online in self._online.items()}
        self._resource_filter_model.set_online(self._resource, self._filter_type, negated_online)


class AddSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, specification):
        """Command to add item specs to a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            specification (ProjectItemSpecification): the spec
        """
        super().__init__()
        self.toolbox = toolbox
        self.specification = specification
        self.setText(f"add specification {specification.name}")

    def redo(self):
        self.toolbox.do_add_specification(self.specification)

    def undo(self):
        row = self.toolbox.specification_model.specification_row(self.specification.name)
        # Store the current spec for eventual `redo()`
        self.specification = self.toolbox.specification_model.specification(row)
        self.toolbox.do_remove_specification(row, ask_verification=False)


class RemoveSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, row, ask_verification):
        """Command to remove item specs from a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            row (int): the row in the ProjectItemSpecPaletteModel
            ask_verification (bool): if True, shows confirmation message the first time
        """
        super().__init__()
        self.toolbox = toolbox
        self.row = row
        self.specification = self.toolbox.specification_model.specification(row)
        self.setText(f"remove specification {self.specification.name}")
        self.ask_verification = ask_verification

    def redo(self):
        self.toolbox.do_remove_specification(self.row, ask_verification=self.ask_verification)
        self.ask_verification = False

    def undo(self):
        self.toolbox.do_add_specification(self.specification, row=self.row)
