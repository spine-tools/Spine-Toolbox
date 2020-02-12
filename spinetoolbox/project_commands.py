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


class AddProjectItemsCommand(QUndoCommand):
    def __init__(self, project, category_name, *items, set_selected=False, verbosity=True):
        super().__init__()
        self.project = project
        self.category_name = category_name
        self.items = items
        self.set_selected = set_selected
        self.verbosity = verbosity
        self.setText(f"add {', '.join([item['name'] for item in items])}")

    def redo(self):
        self.project.do_add_project_items(
            self.category_name, *self.items, set_selected=self.set_selected, verbosity=self.verbosity
        )

    def undo(self):
        for item in self.items:
            self.project.do_remove_item(item["name"])


class RemoveProjectItemCommand(QUndoCommand):
    def __init__(self, project, name, delete_item=False, check_dialog=False):
        super().__init__()
        self.project = project
        self.name = name
        self.delete_item = delete_item
        self.check_dialog = check_dialog
        item = project._project_item_model.get_item(name)
        self.category = item.project_item.category()
        self.item_dict = item.project_item.item_dict()
        self.item_dict["name"] = name
        del self.item_dict["short name"]
        icon = item.project_item.get_icon()
        links = set(link for conn in icon.connectors.values() for link in conn.links)
        self.connections = project.get_connections(links)
        self.setText(f"remove {name}")

    def redo(self):
        self.project.do_remove_item(self.name, delete_item=self.delete_item, check_dialog=self.check_dialog)
        self.check_dialog = False

    def undo(self):
        self.project.do_add_project_items(self.category, self.item_dict)
        self.project._toolbox.ui.graphicsView.restore_links(self.connections)


class AddLinkCommand(QUndoCommand):
    def __init__(self, graphics_view, src_connector, dst_connector):
        super().__init__()
        self.graphics_view = graphics_view
        self.src_connector = src_connector
        self.dst_connector = dst_connector
        self.link = None
        self.replaced_link = None

    def redo(self):
        self.link, self.replaced_link = self.graphics_view.do_add_link(self.src_connector, self.dst_connector)
        action = "add" if self.replaced_link is None else "replace"
        self.setText(f"{action} link from {self.src_connector.parent_name()} to {self.dst_connector.parent_name()}")

    def undo(self):
        self.graphics_view.do_remove_link(self.link)
        if self.replaced_link is not None:
            self.graphics_view.do_add_link(self.replaced_link.src_connector, self.replaced_link.dst_connector)


class RemoveLinkCommand(QUndoCommand):
    def __init__(self, graphics_view, link):
        super().__init__()
        self.graphics_view = graphics_view
        self.link = link
        self.src_connector = link.src_connector
        self.dst_connector = link.dst_connector
        self.setText(f"remove link from {self.src_connector.parent_name()} to {self.dst_connector.parent_name()}")

    def redo(self):
        self.graphics_view.do_remove_link(self.link)

    def undo(self):
        self.link, _ = self.graphics_view.do_add_link(self.src_connector, self.dst_connector)
