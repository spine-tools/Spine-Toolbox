######################################################################################################################
# Copyright (C) 2017-2020 Spine project consortium
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
    @staticmethod
    def is_critical():
        """Returns True if this command needs to be undone before
        closing the project without saving changes.
        """
        return False


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
    def __init__(self, project, item_type, items, set_selected=False, verbosity=True):
        """Command to add items.

        Args:
            project (SpineToolboxProject): the project
            item_type (str): The factory name
            items (Iterable): one or more dict of items to add
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        super().__init__()
        self.project = project
        self.project_tree_items = project.make_project_tree_items(item_type, items)
        self.set_selected = set_selected
        self.verbosity = verbosity
        if len(items) == 1:
            self.setText(f"add {items[0]['name']}")
        else:
            self.setText("add multiple items")

    def redo(self):
        for category_ind, project_tree_items in self.project_tree_items.items():
            self.project.do_add_project_tree_items(
                category_ind, *project_tree_items, set_selected=self.set_selected, verbosity=self.verbosity
            )

    def undo(self):
        for category_ind, project_tree_items in self.project_tree_items.items():
            for project_tree_item in project_tree_items:
                self.project._remove_item(category_ind, project_tree_item, delete_data=True)


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
            for project_tree_item in project_tree_items:
                self.project._remove_item(category_ind, project_tree_item, delete_data=self.delete_data)
        self.project._logger.msg.emit("All items removed from project")

    def undo(self):
        self.project.dag_handler.blockSignals(True)
        for category_ind, project_tree_items in self.items_per_category.items():
            self.project.do_add_project_tree_items(category_ind, *project_tree_items)
        for link in self.links:
            self.project._toolbox.ui.graphicsView._add_link(link)
        self.project.dag_handler.blockSignals(False)
        self.project.notify_changes_in_all_dags()


class RemoveProjectItemCommand(SpineToolboxCommand):
    def __init__(self, project, name, delete_data=False):
        """Command to remove items.

        Args:
            project (SpineToolboxProject): the project
            name (str): Item's name
            delete_data (bool): If True, deletes the directories and data associated with the item
        """
        super().__init__()
        self.project = project
        self.name = name
        self.delete_data = delete_data
        ind = project._project_item_model.find_item(name)
        self.project_tree_item = project._project_item_model.item(ind)
        self.category_ind = ind.parent()
        icon = self.project_tree_item.project_item.get_icon()
        self.links = set(link for conn in icon.connectors.values() for link in conn.links)
        self.setText(f"remove {name}")

    def redo(self):
        self.project._remove_item(self.category_ind, self.project_tree_item, delete_data=self.delete_data)

    def undo(self):
        self.project.dag_handler.blockSignals(True)
        self.project.do_add_project_tree_items(self.category_ind, self.project_tree_item)
        for link in self.links:
            self.project._toolbox.ui.graphicsView._add_link(link)
        self.project.dag_handler.blockSignals(False)
        self.project.notify_changes_in_containing_dag(self.name)


class RenameProjectItemCommand(SpineToolboxCommand):
    def __init__(self, project_item_model, tree_item, new_name):
        """Command to rename items.

        Args:
            project_item_model (ProjectItemModel): the project
            tree_item (LeafProjectTreeItem): the item to rename
            new_name (str): the new name
        """
        super().__init__()
        self.project_item_model = project_item_model
        self.tree_index = project_item_model.find_item(tree_item.name)
        self.old_name = tree_item.name
        self.new_name = new_name
        self.setText(f"rename {self.old_name} to {new_name}")

    def redo(self):
        if not self.project_item_model.setData(self.tree_index, self.new_name):
            self.setObsolete(True)

    def undo(self):
        self.project_item_model.setData(self.tree_index, self.old_name)

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
        self.replaced_link = self.graphics_view._add_link(self.link)
        action = "add" if self.replaced_link is None else "replace"
        self.setText(f"{action} {self.link_name}")

    def undo(self):
        self.graphics_view.do_remove_link(self.link)
        if self.replaced_link is not None:
            self.graphics_view._add_link(self.replaced_link)


class RemoveLinkCommand(SpineToolboxCommand):
    def __init__(self, graphics_view, link):
        """Command to remove link.

        Args:
            graphics_view (DesignQGraphicsView): the view
            link (Link): the link
        """
        super().__init__()
        self.graphics_view = graphics_view
        self.link = link
        self.setText(f"remove link from {link.src_connector.parent_name()} to {link.dst_connector.parent_name()}")

    def redo(self):
        self.graphics_view.do_remove_link(self.link)

    def undo(self):
        self.graphics_view._add_link(self.link)


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
            self.setText(f"move {list(graphics_item.icon_group)[0]._project_item.name}")
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


class UpdateSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, row, specification):
        """Command to update item specs in a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            row (int): the row in the ProjectItemSpecPaletteModel of the spec to be replaced
            specification (ProjectItemSpecification): the updated spec
        """
        super().__init__()
        self.toolbox = toolbox
        self.row = row
        self.redo_specification = specification
        self.setText(f"update specification {specification.name}")

    def redo(self):
        self.toolbox.do_update_specification(self.row, self.redo_specification)

    def undo(self):
        self.toolbox.undo_update_specification(self.row)
