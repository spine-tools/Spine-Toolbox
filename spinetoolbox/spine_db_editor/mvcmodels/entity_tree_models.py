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

"""Models to represent entities in a tree."""
from .entity_tree_item import EntityTreeRootItem
from .multi_db_tree_model import MultiDBTreeModel


class EntityTreeModel(MultiDBTreeModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._hide_empty_classes = (
            self.db_editor.qsettings.value("appSettings/hideEmptyClasses", defaultValue="false") == "true"
        )

    @property
    def root_item_type(self):
        return EntityTreeRootItem

    def find_next_entity_index(self, index):
        """Find and return next occurrence of relationship item."""
        if not index.isValid():
            return None
        ent_item = self.item_from_index(index)
        if not (ent_item.item_type == "entity" and ent_item.element_name_list):
            return None
        # Get all ancestors
        el_item = ent_item.parent_item
        if el_item.item_type != "entity":
            return
        for db_map in ent_item.db_maps:
            # Get data from ancestors
            ent_data = ent_item.db_map_data(db_map)
            el_data = el_item.db_map_data(db_map)
            # Get specific data for our searches
            el_id = el_data["id"]
            element_ids = list(reversed(ent_data["element_id_list"]))
            dimension_ids = list(reversed(ent_data["dimension_id_list"]))
            # Find position in the entity of the (grand parent) element,
            # then use it to determine dimension and element id to look for
            pos = element_ids.index(el_id) - 1
            element_id = element_ids[pos]
            dimension_id = dimension_ids[pos]
            # Return first node that passes all cascade filters
            for parent_item in self.find_items(db_map, (dimension_id, element_id), fetch=True):
                for item in parent_item.find_children(lambda child: child.display_id == ent_item.display_id):
                    return self.index_from_item(item)

    def save_hide_empty_classes(self):
        hide_empty_classes = "true" if self.hide_empty_classes else "false"
        self.db_editor.qsettings.setValue("appSettings/hideEmptyClasses", hide_empty_classes)

    @property
    def hide_empty_classes(self):
        return self._hide_empty_classes

    @hide_empty_classes.setter
    def hide_empty_classes(self, hide_empty_classes):
        if self._hide_empty_classes is hide_empty_classes:
            return
        self._hide_empty_classes = hide_empty_classes
        self.root_item.refresh_child_map()
