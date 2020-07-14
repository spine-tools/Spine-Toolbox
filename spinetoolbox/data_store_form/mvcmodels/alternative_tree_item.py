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
Classes to represent alternative and scenario items in a tree.

:authors: P. Vennström (VTT)
:date:    17.6.2020
"""
from PySide2.QtCore import Qt
from .multi_db_tree_item import MultiDBTreeItem


class ThreeColumnItemBase(MultiDBTreeItem):
    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.DisplayRole:
            return (self.display_data, None, None)[column]
        return None

    def _get_children_ids(self, db_map):
        """Returns a list of children ids.
        Must be reimplemented in subclasses."""
        raise NotImplementedError()


class AlternativeRootItem(ThreeColumnItemBase):
    item_type = "alternative root"

    @property
    def display_id(self):
        """"See super class."""
        return "alternative"

    @property
    def display_data(self):
        """"See super class."""
        return "Alternative"

    def _get_children_ids(self, db_map):
        """Returns a list of object ids in this class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "alternative")]

    @property
    def child_item_type(self):
        """Returns an ObjectItem."""
        return AlternativeItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(alternative_name=self.display_name, database=self.first_db_map.codename)


class ScenarioRootItem(ThreeColumnItemBase):
    item_type = "scenario root"

    @property
    def display_id(self):
        """"See super class."""
        return "scenario"

    @property
    def display_data(self):
        """"See super class."""
        return "Scenario"

    def _get_children_ids(self, db_map):
        """Returns a list of object ids in this class."""
        return [x["id"] for x in self.db_mngr.get_items(db_map, "scenario")]

    @property
    def child_item_type(self):
        """Returns an ObjectItem."""
        return ScenarioItem

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(scenario_name=self.display_name, database=self.first_db_map.codename)


class AlternativeItem(ThreeColumnItemBase):
    item_type = "alternative"

    def __init__(self, *args, **kwargs):
        """Overridden method to parse some data for convenience later.
        Also make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)
        self._fetched = True

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.DisplayRole:
            return (self.display_data, None, self.display_database)[column]
        return None

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(alternative_name=self.display_data, database=self.first_db_map.codename)

    def _get_children_ids(self, db_map):
        """See base class."""
        raise NotImplementedError()


class ScenarioItem(ThreeColumnItemBase):
    item_type = "scenario"

    def __init__(self, *args, **kwargs):
        """Overridden method to parse some data for convenience later.
        Also make sure we never try to fetch this item."""
        super().__init__(*args, **kwargs)

    def data(self, column, role=Qt.DisplayRole):
        """Returns data for given column and role."""
        if role == Qt.CheckStateRole and column == 1:
            is_active = self.db_map_data_field(self.first_db_map, "active")
            return Qt.Checked if is_active else Qt.Unchecked
        if role == Qt.DisplayRole:
            return (self.display_data, None, self.display_database)[column]
        return None

    @property
    def child_item_type(self):
        """Returns a RelationshipItem."""
        return ScenarioAlternativeItem

    def _sort_children(self):
        sorted_children = sorted(self.children, key=lambda c: c.display_id)
        self.children = sorted_children
        self._refresh_child_map()
        self.model.layoutChanged.emit()

    def append_children_by_id(self, db_map_ids):
        super().append_children_by_id(db_map_ids)
        self._sort_children()

    def update_children_by_id(self, db_map_ids):
        super().update_children_by_id(db_map_ids)
        self._sort_children()

    def flags(self, column):
        flags = super().flags(column) | Qt.ItemIsDropEnabled
        if column == 1:
            flags = flags | Qt.ItemIsUserCheckable
        return flags

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(scenario_name=self.display_data, database=self.first_db_map.codename)

    def _get_children_ids(self, db_map):
        """See base class."""
        scenario_id = self.db_map_id(db_map)
        scenario_alt = self.db_mngr.get_items_by_field(db_map, "scenario_alternative", "scenario_id", scenario_id)
        return [x["id"] for x in scenario_alt]

    @staticmethod
    def _new_scenario_alt(db_map_scenario_id, db_map_alt_id, db_map_rank):
        return {
            db_map: [
                {
                    "scenario_id": db_map_scenario_id[db_map],
                    "alternative_id": id_,
                    "rank": db_map_rank.get(db_map, 1) + i,
                }
                for i, id_ in enumerate(ids)
            ]
            for db_map, ids in db_map_alt_id.items()
        }

    def move_scenario_alternative(self, source_row, count, target_row):
        if target_row in range(source_row, source_row + count + 1):
            return False
        if target_row < 0 or target_row > len(self.children):
            return False
        # create new ordered child list
        new_children = list(self.children)
        move_children = new_children[source_row : source_row + count]
        for i, child in enumerate(move_children):
            new_children.insert(target_row + i, child)
        if target_row < source_row:
            delete_from = source_row + count
            del new_children[delete_from : delete_from + count]
        else:
            del new_children[source_row : source_row + count]

        # find new rank/order of items.
        update_items = {}
        curr_rank = {db_map: 1 for db_map in self.db_maps}
        for child in new_children:
            for db_map in child.db_maps:
                current_rank = child.db_map_data_field(db_map, "rank")
                new_rank = curr_rank.get(db_map)
                if current_rank != new_rank:
                    update_items.setdefault(db_map, []).append(
                        {"id": child.db_map_id(db_map), "rank": curr_rank.get(db_map), "old_rank": current_rank}
                    )
                curr_rank[db_map] += 1
        ordered_update = {}
        # change order of items to update. First update highest old rank to an higher rank than existing so that rank
        # is availble for other items, which are update in rank descending order. Last update highest old rank to actual rank
        for db_map, items in update_items.items():
            last_item = sorted(items, key=lambda x: x["old_rank"], reverse=True)[0]
            last_item.pop("old_rank")
            last_item_final = {"id": last_item["id"], "rank": last_item["rank"]}
            last_item["rank"] = curr_rank[db_map]
            ordered_items = [
                {"id": i["id"], "rank": i["rank"]}
                for i in sorted(items, key=lambda x: x["rank"], reverse=True)
                if i["id"] != last_item["id"]
            ]
            ordered_items.insert(0, last_item)
            ordered_items.append(last_item_final)
            ordered_update[db_map] = ordered_items

        self.db_mngr.update_scenario_alternatives(ordered_update)

    def insert_alternative(self, row, db_map_alt_id):
        new_items_per_db = {db_map: len(ids) for db_map, ids in db_map_alt_id.items()}
        new_items = {}
        update_items = {}
        curr_rank = {}
        scenario_ids = {db_map: self.db_map_id(db_map) for db_map in self.db_maps}
        children = sorted(self.children, key=lambda c: c.db_map_data_field(c.first_db_map, "rank"))
        if row == -1:
            # item dropped on parent, append
            row = len(children)
        for child_row, child in enumerate(children):
            curr_rank.update({db_map: child.db_map_data_field(db_map, "rank") for db_map in child.db_maps})
            if child_row == row:
                new_items = self._new_scenario_alt(scenario_ids, db_map_alt_id, curr_rank)
            if child_row >= row:
                for db_map in child.db_maps:
                    if db_map not in new_items_per_db:
                        continue
                    update_items.setdefault(db_map, []).append(
                        {
                            "id": child.db_map_id(db_map),
                            "rank": child.db_map_data_field(db_map, "rank") + new_items_per_db[db_map],
                        }
                    )
        if row >= len(self.children):
            for db_map in curr_rank:
                curr_rank[db_map] += 1
            new_items = self._new_scenario_alt(scenario_ids, db_map_alt_id, curr_rank)
        if update_items:
            self.db_mngr.update_scenario_alternatives(update_items)
        self.db_mngr.add_scenario_alternatives(new_items)

    def set_data(self, column, value, role):
        if role != Qt.CheckStateRole or column != 1:
            return False
        update_data = {"name": self.display_data, "active": True if value == Qt.Checked else False}
        self.db_mngr.update_scenario({self.first_db_map: update_data})
        return True


class ScenarioAlternativeItem(ThreeColumnItemBase):
    item_type = "scenario_alternative"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._fetched = True

    @property
    def display_id(self):
        ids = []
        for db_map in self.db_maps:
            data = self.db_map_data(db_map)
            alt_id = data.get("alternative_id")
            alt_rank = data.get("rank")
            alt_name = self.db_mngr.get_item(self.first_db_map, "alternative", alt_id).get("name")
            ids.append((alt_rank, alt_name))

        if len(set(ids)) != 1:
            return None
        return ids[0]

    @property
    def display_data(self):
        data = self.db_map_data(self.first_db_map)
        alt_id = data.get("alternative_id")
        alt_rank = data.get("rank")
        alt_name = self.db_mngr.get_item(self.first_db_map, "alternative", alt_id).get("name")
        return f"{alt_rank}: {alt_name}"

    def has_children(self):
        """Returns false, this item never has children."""
        return False

    def flags(self, column):
        return super().flags(column) | Qt.ItemIsDragEnabled

    def default_parameter_data(self):
        """Return data to put as default in a parameter table when this item is selected."""
        return dict(scenario_name=self.display_data, database=self.first_db_map.codename)

    def _get_children_ids(self, db_map):
        """See base class."""
        raise NotImplementedError()
