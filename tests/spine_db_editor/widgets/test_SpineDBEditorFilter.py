######################################################################################################################
# Copyright (C) 2017-2022 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for the TreeViewFormFilterMixin class.
"""

from PySide6.QtCore import Qt, QItemSelectionModel
from spinetoolbox.helpers import DB_ITEM_SEPARATOR


class TestSpineDBEditorFilterMixin:
    @property
    def _parameter_models(self):
        return (
            self.spine_db_editor.object_parameter_definition_model,
            self.spine_db_editor.object_parameter_value_model,
            self.spine_db_editor.relationship_parameter_definition_model,
            self.spine_db_editor.relationship_parameter_value_model,
        )

    @property
    def _filtered_fields(self):
        return {
            self.spine_db_editor.object_parameter_definition_model: ("object_class_name",),
            self.spine_db_editor.object_parameter_value_model: ("object_class_name", "object_name"),
            self.spine_db_editor.relationship_parameter_definition_model: ("relationship_class_name",),
            self.spine_db_editor.relationship_parameter_value_model: ("relationship_class_name", "object_name_list"),
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
            self.assertTrue(all(value in data for value in values))
            model.refresh()
            data = self._parameter_data(model, *fields)
            self.assertTrue(all(value not in data for value in values))

    def test_filter_parameter_tables_per_object_class(self):
        """Test that parameter tables are filtered when selecting object classes in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.object_tree_model.root_item
        fish_item = root_item.child(1)
        fish_index = self.spine_db_editor.object_tree_model.index_from_item(fish_item)
        selection_model = self.spine_db_editor.ui.treeView_object.selectionModel()
        selection_model.setCurrentIndex(fish_index, QItemSelectionModel.NoUpdate)
        selection_model.select(fish_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.object_parameter_definition_model: [('dog',)],
            self.spine_db_editor.object_parameter_value_model: [('dog', 'pluto'), ('dog', 'scooby')],
            self.spine_db_editor.relationship_parameter_definition_model: [],
            self.spine_db_editor.relationship_parameter_value_model: [],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_object(self):
        """Test that parameter tables are filtered when selecting objects in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.object_tree_model.root_item
        dog_item = root_item.child(0)
        pluto_item = dog_item.child(0)
        pluto_index = self.spine_db_editor.object_tree_model.index_from_item(pluto_item)
        selection_model = self.spine_db_editor.ui.treeView_object.selectionModel()
        selection_model.setCurrentIndex(pluto_index, QItemSelectionModel.NoUpdate)
        selection_model.select(pluto_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.object_parameter_definition_model: [('fish',)],
            self.spine_db_editor.object_parameter_value_model: [('fish', 'nemo'), ('dog', 'scooby')],
            self.spine_db_editor.relationship_parameter_definition_model: [],
            self.spine_db_editor.relationship_parameter_value_model: [
                ('fish__dog', DB_ITEM_SEPARATOR.join(['nemo', 'scooby']))
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_relationship_class(self):
        """Test that parameter tables are filtered when selecting relationship classes in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.object_tree_model.root_item
        dog_item = root_item.child(0)
        pluto_item = dog_item.child(0)
        pluto_fish_dog_item = pluto_item.child(1)
        pluto_fish_dog_index = self.spine_db_editor.object_tree_model.index_from_item(pluto_fish_dog_item)
        selection_model = self.spine_db_editor.ui.treeView_object.selectionModel()
        selection_model.setCurrentIndex(pluto_fish_dog_index, QItemSelectionModel.NoUpdate)
        selection_model.select(pluto_fish_dog_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.object_parameter_definition_model: [],
            self.spine_db_editor.object_parameter_value_model: [],
            self.spine_db_editor.relationship_parameter_definition_model: [('dog__fish',)],
            self.spine_db_editor.relationship_parameter_value_model: [
                ('dog__fish', DB_ITEM_SEPARATOR.join(['pluto', 'nemo']))
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_relationship(self):
        """Test that parameter tables are filtered when selecting relationships in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        root_item = self.spine_db_editor.object_tree_model.root_item
        dog_item = root_item.child(0)
        pluto_item = dog_item.child(0)
        pluto_fish_dog_item = pluto_item.child(1)
        fish_dog_nemo_pluto_item = pluto_fish_dog_item.child(0)
        fish_dog_nemo_pluto_index = self.spine_db_editor.object_tree_model.index_from_item(fish_dog_nemo_pluto_item)
        selection_model = self.spine_db_editor.ui.treeView_object.selectionModel()
        selection_model.setCurrentIndex(fish_dog_nemo_pluto_index, QItemSelectionModel.NoUpdate)
        selection_model.select(fish_dog_nemo_pluto_index, QItemSelectionModel.Select)
        filtered_values = {
            self.spine_db_editor.object_parameter_definition_model: [],
            self.spine_db_editor.object_parameter_value_model: [],
            self.spine_db_editor.relationship_parameter_definition_model: [('dog__fish',)],
            self.spine_db_editor.relationship_parameter_value_model: [
                ('fish__dog', DB_ITEM_SEPARATOR.join(['nemo', 'scooby'])),
                ('dog__fish', DB_ITEM_SEPARATOR.join(['pluto', 'nemo'])),
            ],
        }
        self._assert_filter(filtered_values)
