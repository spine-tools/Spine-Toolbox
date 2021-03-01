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
    def __init__(self, graphics_item):
        """Command to move icons in the Design view.

        Args:
            graphics_item (ProjectItemIcon): the icon
        """
        super().__init__()
        self.graphics_item = graphics_item
        self.previous_pos = {x: x._previous_pos for x in graphics_item.icon_group}
        self.current_pos = {x: x._current_pos for x in graphics_item.icon_group}
        if len(graphics_item.icon_group) == 1:
            self.setText(f"move {list(graphics_item.icon_group)[0].name()}")
        else:
            self.setText("move multiple items")

    def redo(self):
        for item, current_post in self.current_pos.items():
            item.setPos(current_post)
        self.graphics_item.update_links_geometry()
        self.graphics_item.notify_item_move()

    def undo(self):
        for item, previous_pos in self.previous_pos.items():
            item.setPos(previous_pos)
        self.graphics_item.update_links_geometry()
        self.graphics_item.notify_item_move()


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
        self.project = project
        self.project_tree_items = project.make_project_tree_items(items_dict)
        self.set_selected = set_selected
        self.verbosity = verbosity
        if not items_dict:
            self.setObsolete(True)
        elif len(items_dict) == 1:
            self.setText(f"add {next(iter(items_dict))}")
        else:
            self.setText("add multiple items")

    def redo(self):
        for category_ind, project_tree_items in self.project_tree_items.items():
            self.project.do_add_project_tree_items(
                category_ind, *project_tree_items, set_selected=self.set_selected, verbosity=self.verbosity
            )

    def undo(self):
        for category_ind, project_tree_items in self.project_tree_items.items():
            self.project.do_remove_project_tree_items(category_ind, *project_tree_items, delete_data=True)


class RemoveAllProjectItemsCommand(SpineToolboxCommand):
    def __init__(self, project, items_per_category, links, delete_data=False):
        """Command to remove all items from project.

        Args:
            project (SpineToolboxProject): the project
            delete_data (bool): If True, deletes the directories and data associated with the items
        """
        super().__init__()
        self.project = project
        self.items_per_category = items_per_category
        self.links = links
        self.delete_data = delete_data
        self.setText("remove all items")

    def redo(self):
        for category_ind, project_tree_items in self.items_per_category.items():
            self.project.do_remove_project_tree_items(category_ind, *project_tree_items, delete_data=self.delete_data)
        self.project._logger.msg.emit("All items removed from project")

    def undo(self):
        self.project.dag_handler.blockSignals(True)
        for category_ind, project_tree_items in self.items_per_category.items():
            self.project.do_add_project_tree_items(category_ind, *project_tree_items)
        for link in self.links:
            self.project._toolbox.ui.graphicsView.do_add_or_replace_link(link)
        self.project.dag_handler.blockSignals(False)
        self.project.notify_changes_in_all_dags()


class RemoveProjectItemsCommand(SpineToolboxCommand):
    def __init__(self, project, *indexes, delete_data=False):
        """Command to remove items.

        Args:
            project (SpineToolboxProject): the project
            *indexes (QModelIndex): Indexes of the items in project item model
            delete_data (bool): If True, deletes the directories and data associated with the item
        """
        super().__init__()
        indexes = list(indexes)
        self.project = project
        self.names = [ind.data() for ind in indexes]
        self.delete_data = delete_data
        self.project_tree_items = {}
        self.links = set()
        for index in indexes:
            category_ind = index.parent()
            project_tree_item = project._project_item_model.item(index)
            self.project_tree_items.setdefault(category_ind, []).append(project_tree_item)
            icon = project_tree_item.project_item.get_icon()
            self.links.update(link for conn in icon.connectors.values() for link in conn.links)
        if not self.names:
            self.setObsolete(True)
        elif len(self.names) == 1:
            self.setText(f"remove {self.names[0]}")
        else:
            self.setText("remove multiple items")

    def redo(self):
        for category_ind, project_tree_items in self.project_tree_items.items():
            self.project.do_remove_project_tree_items(category_ind, *project_tree_items, delete_data=self.delete_data)

    def undo(self):
        self.project.dag_handler.blockSignals(True)
        for category_ind, project_tree_items in self.project_tree_items.items():
            self.project.do_add_project_tree_items(category_ind, *project_tree_items)
        for link in self.links:
            self.project._toolbox.ui.graphicsView.do_add_or_replace_link(link)
        self.project.dag_handler.blockSignals(False)
        for name in self.names:
            self.project.notify_changes_in_containing_dag(name)


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


class AddLinkCommand(SpineToolboxCommand):
    def __init__(self, graphics_view, src_connector, dst_connector):
        """Command to add link.

        Args:
            graphics_view (DesignQGraphicsView): the view
            src_connector (ConnectorButton): the source connector
            dst_connector (ConnectorButton): the destination connector
        """
        super().__init__()
        self.graphics_view = graphics_view
        self.link = graphics_view.make_link(src_connector, dst_connector)
        self.replaced_link = None
        self.link_name = f"link from {src_connector.parent_name()} to {dst_connector.parent_name()}"

    def redo(self):
        self.replaced_link = self.graphics_view.do_add_or_replace_link(self.link)
        action = "add" if self.replaced_link is None else "replace"
        self.setText(f"{action} {self.link_name}")

    def undo(self):
        self.link.wipe_out()
        if self.replaced_link is not None:
            self.graphics_view.do_add_or_replace_link(self.replaced_link)


class RemoveLinksCommand(SpineToolboxCommand):
    def __init__(self, graphics_view, *links):
        """Command to remove links.

        Args:
            graphics_view (DesignQGraphicsView): the view
            *links (Link): the links
        """
        super().__init__()
        self.graphics_view = graphics_view
        self.links = list(links)
        if not self.links:
            self.setObsolete(True)
        elif len(self.links) == 1:
            self.setText(f"remove link {self.links[0].name}")
        else:
            self.setText("remove multiple links")

    def redo(self):
        for link in self.links:
            link.wipe_out()

    def undo(self):
        for link in self.links:
            self.graphics_view.do_add_or_replace_link(link)


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
