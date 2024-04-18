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

"""Unit tests for filtering in Database editor."""
from PySide6.QtCore import Qt, QItemSelectionModel
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from .spine_db_editor_test_base import DBEditorTestBase


class TestSpineDBEditorFilter(DBEditorTestBase):
    @property
    def _parameter_models(self):
        return (self.spine_db_editor.parameter_definition_model, self.spine_db_editor.parameter_value_model)

    @property
    def _filtered_fields(self):
        return {
            self.spine_db_editor.parameter_definition_model: ("entity_class_name",),
            self.spine_db_editor.parameter_value_model: ("entity_class_name", "entity_byname"),
        }

    @staticmethod
    def _parameter_data(model, *fields):
        return [
            tuple(model.index(row, model.header.index(field)).data(Qt.ItemDataRole.EditRole) for field in fields)
            for row in range(model.rowCount())
        ]

    def _assert_filter(self, filtered_values):
        for model in self._parameter_models:
            fields = self._filtered_fields[model]
            data = self._parameter_data(model, *fields)
            values = filtered_values[model]
            unfiltered_count = len(data)
            self.assertTrue(all(value in data for value in values))
            model.refresh()
            data = self._parameter_data(model, *fields)
            filtered_count = len(data)
            self.assertTrue(all(value not in data for value in values))
            # Check that only the items that were supposed to be filtered were actually filtered.
            self.assertEqual(filtered_count, unfiltered_count - len(values))

    def test_filter_parameter_tables_per_zero_dimensional_entity_class(self):
        """Test that parameter tables are filtered when selecting object classes in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(2)
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(fish_index, QItemSelectionModel.NoUpdate)
        selection_model.select(fish_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("dog",)],
            self.spine_db_editor.parameter_value_model: [("dog", "pluto"), ("dog", "scooby")],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_nonzero_dimensional_entity_class(self):
        """Test that parameter tables are filtered when selecting relationship classes in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_dog_item = root_item.child(3)
        fish_dog_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_dog_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(fish_dog_index, QItemSelectionModel.NoUpdate)
        selection_model.select(fish_dog_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("dog",), ("fish",), ("dog__fish",)],
            self.spine_db_editor.parameter_value_model: [
                ("dog__fish", DB_ITEM_SEPARATOR.join(["pluto", "nemo"])),
                ("fish", "nemo"),
                ("dog", "pluto"),
                ("dog", "scooby"),
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_entity_class_and_entity_cross_selection(self):
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(2)
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        dog_item = root_item.child(0)
        scooby_item = dog_item.child(1)
        scooby_index = self.spine_db_editor.entity_tree_model.index_from_item(scooby_item)
        selection_model.setCurrentIndex(fish_index, QItemSelectionModel.NoUpdate)
        selection_model.select(fish_index, QItemSelectionModel.Select)
        selection_model.setCurrentIndex(scooby_index, QItemSelectionModel.NoUpdate)
        selection_model.select(scooby_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [],
            self.spine_db_editor.parameter_value_model: [
                ("dog", "pluto"),
                ("fish__dog", "nemo ǀ pluto"),
                ("dog__fish", "pluto ǀ nemo"),
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_entity(self):
        """Test that parameter tables are filtered when selecting objects in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        dog_item = root_item.child(0)
        pluto_item = dog_item.child(0)
        pluto_index = self.spine_db_editor.entity_tree_model.index_from_item(pluto_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(pluto_index, QItemSelectionModel.NoUpdate)
        selection_model.select(pluto_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("fish",)],
            self.spine_db_editor.parameter_value_model: [
                ("fish__dog", DB_ITEM_SEPARATOR.join(["nemo", "scooby"])),
                ("fish", "nemo"),
                ("dog", "scooby"),
            ],
        }
        self._assert_filter(filtered_values)
