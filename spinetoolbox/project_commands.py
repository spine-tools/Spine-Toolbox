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

import copy
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
    def __init__(self, project, category_name, *items, set_selected=False, verbosity=True):
        """Command to add items.

        Args:
            project (SpineToolboxProject): the project
            category_name (str): The items' category
            items (dict): one or more dict of items to add
            set_selected (bool): Whether to set item selected after the item has been added to project
            verbosity (bool): If True, prints message
        """
        super().__init__()
        self.project = project
        self.category_ind, self.project_tree_items = project.make_project_tree_items(category_name, *items)
        self.set_selected = set_selected
        self.verbosity = verbosity
        if len(items) == 1:
            self.setText(f"add {items[0]['name']}")
        else:
            self.setText("add multiple items")

    def redo(self):
        self.project._add_project_tree_items(
            self.category_ind, *self.project_tree_items, set_selected=self.set_selected, verbosity=self.verbosity
        )

    def undo(self):
        for project_tree_item in self.project_tree_items:
            self.project._remove_item(self.category_ind, project_tree_item, delete_data=True)


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
            self.project._add_project_tree_items(category_ind, *project_tree_items)
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
        self.project._add_project_tree_items(self.category_ind, self.project_tree_item)
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
        self.previous_pos = {x: x._previous_pos for x in graphics_item.selected_icons}
        self.current_pos = {x: x._current_pos for x in graphics_item.selected_icons}
        if len(graphics_item.selected_icons) == 1:
            self.setText(f"move {list(graphics_item.selected_icons)[0]._project_item.name}")
        else:
            self.setText("move multiple items")

    def redo(self):
        for item, current_post in self.current_pos.items():
            item.setPos(current_post)
        self.graphics_item.update_links_geometry()
        self.graphics_item.shrink_scene_if_needed()

    def undo(self):
        for item, previous_pos in self.previous_pos.items():
            item.setPos(previous_pos)
        self.graphics_item.update_links_geometry()
        self.graphics_item.shrink_scene_if_needed()


class AddDCReferencesCommand(SpineToolboxCommand):
    def __init__(self, dc, paths):
        """Command to add DC references.

        Args:
            dc (DataConnection): the DC
            paths (set(str)): set of paths to add
        """
        super().__init__()
        self.dc = dc
        self.paths = paths
        self.setText(f"add references to {dc.name}")

    def redo(self):
        self.dc.do_add_files_to_references(self.paths)

    def undo(self):
        self.dc.do_remove_references(self.paths)


class RemoveDCReferencesCommand(SpineToolboxCommand):
    def __init__(self, dc, paths):
        """Command to remove DC references.

        Args:
            dc (DataConnection): the DC
            paths (list(str)): list of paths to remove
        """
        super().__init__()
        self.dc = dc
        self.paths = paths
        self.setText(f"remove references from {dc.name}")

    def redo(self):
        self.dc.do_remove_references(self.paths)

    def undo(self):
        self.dc.do_add_files_to_references(self.paths)


class UpdateDSURLCommand(SpineToolboxCommand):
    def __init__(self, ds, **kwargs):
        """Command to update DS url.

        Args:
            ds (DataStore): the DS
            kwargs: url keys and their values
        """
        super().__init__()
        self.ds = ds
        self.redo_kwargs = kwargs
        self.undo_kwargs = {k: self.ds._url[k] for k in kwargs}
        if len(kwargs) == 1:
            self.setText(f"change {list(kwargs.keys())[0]} of {ds.name}")
        else:
            self.setText(f"change url of {ds.name}")

    def redo(self):
        self.ds.do_update_url(**self.redo_kwargs)

    def undo(self):
        self.ds.do_update_url(**self.undo_kwargs)


class UpdateImporterSettingsCommand(SpineToolboxCommand):
    def __init__(self, importer, settings, importee):
        """Command to update Importer settings.

        Args:
            importer (Importer): the Importer
            settings (dict): the new settings
            importee (str): the filepath
        """
        super().__init__()
        self.importer = importer
        self.redo_settings = settings
        self.importee = importee
        self.undo_settings = copy.deepcopy(importer.settings.get(importee, {}))
        self.setText(f"change mapping settings of {importer.name}")

    def redo(self):
        self.importer.settings.setdefault(self.importee, {}).update(self.redo_settings)

    def undo(self):
        self.importer.settings[self.importee] = self.undo_settings


class UpdateImporterCancelOnErrorCommand(SpineToolboxCommand):
    def __init__(self, importer, cancel_on_error):
        """Command to update Importer cancel on error setting.

        Args:
            importer (Importer): the Importer
            cancel_on_error (bool): the new setting
        """
        super().__init__()
        self.importer = importer
        self.redo_cancel_on_error = cancel_on_error
        self.undo_cancel_on_error = not cancel_on_error
        self.setText(f"change cancel on error setting of {importer.name}")

    def redo(self):
        self.importer.set_cancel_on_error(self.redo_cancel_on_error)

    def undo(self):
        self.importer.set_cancel_on_error(self.undo_cancel_on_error)


class SetToolSpecificationCommand(SpineToolboxCommand):
    def __init__(self, tool, specification):
        """Command to set the specification for a Tool.

        Args:
            tool (Tool): the Tool
            specification (ToolSpecification): the new tool spec
        """
        super().__init__()
        self.tool = tool
        self.redo_specification = specification
        self.undo_specification = tool._tool_specification
        self.undo_execute_in_work = tool.execute_in_work
        self.setText(f"set Tool specification of {tool.name}")

    def redo(self):
        self.tool.do_set_tool_specification(self.redo_specification)

    def undo(self):
        self.tool.do_set_tool_specification(self.undo_specification)
        self.tool.do_update_execution_mode(self.undo_execute_in_work)


class UpdateToolExecuteInWorkCommand(SpineToolboxCommand):
    def __init__(self, tool, execute_in_work):
        """Command to update Tool execute_in_work setting.

        Args:
            tool (Tool): the Tool
            execute_in_work (bool): True or False
        """
        super().__init__()
        self.tool = tool
        self.execute_in_work = execute_in_work
        self.setText(f"change execute in work setting of {tool.name}")

    def redo(self):
        self.tool.do_update_execution_mode(self.execute_in_work)

    def undo(self):
        self.tool.do_update_execution_mode(not self.execute_in_work)


class UpdateToolCmdLineArgsCommand(SpineToolboxCommand):
    def __init__(self, tool, cmd_line_args):
        """Command to update Tool command line args.

        Args:
            tool (Tool): the Tool
            cmd_line_args (list): list of str args
        """
        super().__init__()
        self.tool = tool
        self.redo_cmd_line_args = cmd_line_args
        self.undo_cmd_line_args = self.tool.cmd_line_args
        self.setText(f"change command line arguments of {tool.name}")

    def redo(self):
        self.tool.do_update_tool_cmd_line_args(self.redo_cmd_line_args)

    def undo(self):
        self.tool.do_update_tool_cmd_line_args(self.undo_cmd_line_args)


class UpdateExporterOutFileNameCommand(SpineToolboxCommand):
    def __init__(self, exporter, file_name, database_path):
        """Command to update Exporter output file name.

        Args:
            exporter (Exporter): the Exporter
            export_list_item (ExportListItem): the widget that holds the name
            file_name (str): the output filename
            database_path (str): the associated db path
        """
        super().__init__()
        self.exporter = exporter
        self.redo_file_name = file_name
        self.undo_file_name = self.exporter._settings_packs[database_path].output_file_name
        self.database_path = database_path
        self.setText(f"change output file in {exporter.name}")

    def redo(self):
        self.exporter.undo_redo_out_file_name(self.redo_file_name, self.database_path)

    def undo(self):
        self.exporter.undo_redo_out_file_name(self.undo_file_name, self.database_path)


class UpdateExporterSettingsCommand(SpineToolboxCommand):
    def __init__(
        self, exporter, settings, indexing_settings, indexing_domains, merging_settings, merging_domains, database_path
    ):
        """Command to update Exporter settings.

        Args:
            exporter (Exporter): the Exporter
            database_path (str): the db path to update settings for
        """
        super().__init__()
        self.exporter = exporter
        self.database_path = database_path
        self.redo_settings_tuple = (settings, indexing_settings, indexing_domains, merging_settings, merging_domains)
        p = exporter.settings_pack(database_path)
        self.undo_settings_tuple = (
            p.settings,
            p.indexing_settings,
            p.indexing_domains,
            p.merging_settings,
            p.merging_domains,
        )
        self.setText(f"change settings of {exporter.name}")

    def redo(self):
        self.exporter.undo_or_redo_settings(*self.redo_settings_tuple, self.database_path)

    def undo(self):
        self.exporter.undo_or_redo_settings(*self.undo_settings_tuple, self.database_path)


class AddToolSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, tool_specification):
        """Command to add Tool specs to a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            tool_specification (ToolSpecification): the tool spec
        """
        super().__init__()
        self.toolbox = toolbox
        self.tool_specification = tool_specification
        self.setText(f"add tool speciciation {tool_specification.name}")

    def redo(self):
        self.toolbox.do_add_tool_specification(self.tool_specification)

    def undo(self):
        row = self.toolbox.tool_specification_model.tool_specification_row(self.tool_specification.name)
        self.toolbox.do_remove_tool_specification(row, ask_verification=False)


class RemoveToolSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, row, ask_verification):
        """Command to remove Tool specs from a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            row (int): the row in the ToolSpecificationModel
            ask_verification (bool): if True, shows confirmation message the first time
        """
        super().__init__()
        self.toolbox = toolbox
        self.row = row
        self.tool_specification = self.toolbox.tool_specification_model.tool_specification(row)
        self.setText(f"remove tool speciciation {self.tool_specification.name}")
        self.ask_verification = ask_verification

    def redo(self):
        self.toolbox.do_remove_tool_specification(self.row, ask_verification=self.ask_verification)
        self.ask_verification = False

    def undo(self):
        self.toolbox.do_add_tool_specification(self.tool_specification, row=self.row)


class UpdateToolSpecificationCommand(SpineToolboxCommand):
    def __init__(self, toolbox, row, tool_specification):
        """Command to update Tool specs in a project.

        Args:
            toolbox (ToolboxUI): the toolbox
            row (int): the row in the ToolSpecificationModel of the spec to be replaced
            tool_specification (ToolSpecification): the updated tool spec
        """
        super().__init__()
        self.toolbox = toolbox
        self.row = row
        self.redo_tool_specification = tool_specification
        self.undo_tool_specification = self.toolbox.tool_specification_model.tool_specification(row)
        self.redo_tool_settings = {}
        self.undo_tool_settings = {}
        for item in toolbox.project_item_model.items("Tools"):
            tool = item.project_item
            if tool.tool_specification() != self.undo_tool_specification:
                continue
            self.redo_tool_settings[tool] = (self.redo_tool_specification, self.redo_tool_specification.execute_in_work)
            self.undo_tool_settings[tool] = (self.undo_tool_specification, tool.execute_in_work)
        self.setText(f"update tool speciciation {tool_specification.name}")

    def redo(self):
        if self.toolbox.do_update_tool_specification(self.row, self.redo_tool_specification):
            self.toolbox.update_tool_settings(self.redo_tool_settings)

    def undo(self):
        if self.toolbox.do_update_tool_specification(self.row, self.undo_tool_specification):
            self.toolbox.update_tool_settings(self.undo_tool_settings)
