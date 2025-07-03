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

"""Unit tests for the ``utils`` module."""
import unittest
from PySide6.QtCore import QObject, QSize
from PySide6.QtGui import QStandardItem, QStandardItemModel
from spinedb_api import DatabaseMapping
from spinetoolbox.mvcmodels.minimal_table_model import MinimalTableModel
from spinetoolbox.spine_db_editor.mvcmodels.utils import (
    entity_class_id_for_row,
    make_entity_on_the_fly,
    two_column_as_csv,
)
from tests.mock_helpers import TestCaseWithQApplication, q_object


class TestTwoColumnAsCsv(TestCaseWithQApplication):
    def test_indexes_from_two_columns(self):
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            data = [["11", "12"], ["21", "22"]]
            for y, row in enumerate(data):
                for x, cell in enumerate(row):
                    item = QStandardItem(cell)
                    model.setItem(y, x, item)
            indexes = []
            for y in range(model.rowCount()):
                for x in range(model.columnCount()):
                    indexes.append(model.index(y, x))
            as_csv = two_column_as_csv(indexes)
            self.assertEqual(as_csv, "11\t12\r\n21\t22\r\n")

    def test_indexes_from_single_column(self):
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            data = [["11", "12"], ["21", "22"]]
            for y, row in enumerate(data):
                for x, cell in enumerate(row):
                    item = QStandardItem(cell)
                    model.setItem(y, x, item)
            indexes = []
            for y in range(model.rowCount()):
                indexes.append(model.index(y, 1))
            as_csv = two_column_as_csv(indexes)
            self.assertEqual(as_csv, "12\r\n22\r\n")


class TestEntityClassIdForRow(TestCaseWithQApplication):
    def test_class_id_is_found(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            entity_class = db_map.add_entity_class(name="MyClass")
            with q_object(QObject()) as parent:
                model = MinimalTableModel(parent, ["entity_class_name", "header 2", "header 3"])
                self.assertTrue(model.insertRows(0, 1))
                data = [entity_class["name"], "x", "y"]
                for column in range(model.columnCount()):
                    index = model.index(0, column)
                    self.assertTrue(model.setData(index, data[column]))
                for column in range(model.columnCount()):
                    index = model.index(0, column)
                    self.assertEqual(entity_class_id_for_row(index, db_map), entity_class["id"])

    def test_returns_none_if_class_is_not_in_db_map(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            entity_class = db_map.add_entity_class(name="MyClass")
            with q_object(QObject()) as parent:
                model = MinimalTableModel(parent, ["entity_class_name", "header 2", "header 3"])
                self.assertTrue(model.insertRows(0, 1))
                data = ["NotMyClass", "x", "y"]
                for column in range(model.columnCount()):
                    index = model.index(0, column)
                    self.assertTrue(model.setData(index, data[column]))
                for column in range(model.columnCount()):
                    index = model.index(0, column)
                    self.assertIsNone(entity_class_id_for_row(index, db_map), entity_class["id"])


class TestMakeEntityOnTheFly(unittest.TestCase):
    def test_empty_item(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            entity, errors = make_entity_on_the_fly({}, db_map)
            self.assertEqual(errors, [])
            self.assertIsNone(entity)

    def test_nonexistent_entity_class(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            entity, errors = make_entity_on_the_fly({"entity_class_name": "not-in-db"}, db_map)
            self.assertEqual(errors, ["Unknown entity_class not-in-db"])
            self.assertIsNone(entity)

    def test_entity_byname_missing(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            db_map.add_entity_class(name="Object")
            entity, errors = make_entity_on_the_fly({"entity_class_name": "Object"}, db_map)
            self.assertEqual(errors, [])
            self.assertIsNone(entity)

    def test_normal_operation(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            db_map.add_entity_class(name="Object")
            entity, errors = make_entity_on_the_fly(
                {"entity_class_name": "Object", "entity_byname": ("gadget",)}, db_map
            )
            self.assertEqual(errors, [])
            self.assertEqual(entity, {"entity_class_name": "Object", "entity_byname": ("gadget",)})

    def test_entity_exists_in_db_map(self):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            db_map.add_entity_class(name="Object")
            db_map.add_entity(entity_class_name="Object", name="gadget")
            entity, errors = make_entity_on_the_fly(
                {"entity_class_name": "Object", "entity_byname": ("gadget",)}, db_map
            )
            self.assertEqual(errors, [])
            self.assertIsNone(entity)


if __name__ == "__main__":
    unittest.main()
