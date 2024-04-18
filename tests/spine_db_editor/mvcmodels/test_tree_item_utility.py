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

"""Unit tests for the ``tree_item_utility`` module."""
from operator import attrgetter
import unittest
from spinetoolbox.spine_db_editor.mvcmodels.tree_item_utility import SortChildrenMixin


class TestSortsChildrenMixin(unittest.TestCase):
    class ChildrenSorterBase:
        def __init__(self):
            self.non_empty_children = []

        def insert_children(self, position, children):
            self.non_empty_children = self.non_empty_children[:position] + children + self.non_empty_children[position:]
            return True

        def child_ns(self):
            return list(map(attrgetter("n"), self.non_empty_children))

    class ChildrenSorter(SortChildrenMixin, ChildrenSorterBase):
        pass

    class Child:
        def __init__(self, n):
            self.n = n

        def data(self, i):
            if i != 0:
                raise RuntimeError(f"i must be 0, got {i}")
            return self.n

    def test_insert_children_sorted_to_empty_data(self):
        sorter = self.ChildrenSorter()
        new_children = list(map(self.Child, [4, 2, 6]))
        self.assertTrue(sorter.insert_children_sorted(new_children))
        self.assertEqual(sorter.child_ns(), [2, 4, 6])

    def test_insert_children_sorted_to_existing_list(self):
        sorter = self.ChildrenSorter()
        sorter.non_empty_children = list(map(self.Child, [3, 7, 9]))
        new_children = list(map(self.Child, [4, 2, 6]))
        self.assertTrue(sorter.insert_children_sorted(new_children))
        self.assertEqual(sorter.child_ns(), [2, 3, 4, 6, 7, 9])


if __name__ == "__main__":
    unittest.main()
