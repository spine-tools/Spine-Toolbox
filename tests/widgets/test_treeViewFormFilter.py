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
Unit tests for the TreeViewFormFilterMixin class.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

from PySide2.QtCore import Qt, QItemSelectionModel


class TestTreeViewFormFilterMixin:
    @property
    def _parameter_models(self):
        return (
            self.tree_view_form.object_parameter_definition_model,
            self.tree_view_form.object_parameter_value_model,
            self.tree_view_form.relationship_parameter_definition_model,
            self.tree_view_form.relationship_parameter_value_model,
        )

    @property
    def _filtered_fields(self):
        return {
            self.tree_view_form.object_parameter_definition_model: ("object_class_name",),
            self.tree_view_form.object_parameter_value_model: ("object_class_name", "object_name"),
            self.tree_view_form.relationship_parameter_definition_model: ("relationship_class_name",),
            self.tree_view_form.relationship_parameter_value_model: ("relationship_class_name", "object_name_list"),
        }

    def _fetch_parameter_models(self):
        for model in self._parameter_models:
            model.init_model()
            for m in model.sub_models:
                m.fetchMore()

    @staticmethod
    def _parameter_data(model, *fields):
        return [
            tuple(model.index(row, model.header.index(field)).data(Qt.EditRole) for field in fields)
            for row in range(model.rowCount())
        ]

    def _assert_filter(self, filtered_values):
        for model in self._parameter_models:
            fields = self._filtered_fields[model]
            data = self._parameter_data(model, *fields)
            values = filtered_values[model]
            self.assertTrue(all(value in data for value in values))
            model.update_main_filter()
            data = self._parameter_data(model, *fields)
            self.assertTrue(all(value not in data for value in values))

    def test_filter_parameter_tables_per_object_class(self):
        """Test that parameter tables are filtered when selecting object classes in the object tree.
        """
        self.put_mock_dataset_in_db_mngr()
        for item in self.tree_view_form.object_tree_model.visit_all():
            try:
                item.fetch_more()
            except NotImplementedError:
                pass
        self._fetch_parameter_models()
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.index_from_item(fish_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        filtered_values = {
            self.tree_view_form.object_parameter_definition_model: [('dog',)],
            self.tree_view_form.object_parameter_value_model: [('dog', 'pluto'), ('dog', 'scooby')],
            self.tree_view_form.relationship_parameter_definition_model: [],
            self.tree_view_form.relationship_parameter_value_model: [],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_object(self):
        """Test that parameter tables are filtered when selecting objects in the object tree.
        """
        self.put_mock_dataset_in_db_mngr()
        for item in self.tree_view_form.object_tree_model.visit_all():
            try:
                item.fetch_more()
            except NotImplementedError:
                pass
        self._fetch_parameter_models()
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.index_from_item(pluto_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(pluto_index, QItemSelectionModel.Select)
        filtered_values = {
            self.tree_view_form.object_parameter_definition_model: [('fish',)],
            self.tree_view_form.object_parameter_value_model: [('fish', 'nemo'), ('dog', 'scooby')],
            self.tree_view_form.relationship_parameter_definition_model: [],
            self.tree_view_form.relationship_parameter_value_model: [('fish__dog', 'nemo,scooby')],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_relationship_class(self):
        """Test that parameter tables are filtered when selecting relationship classes in the object tree.
        """
        self.put_mock_dataset_in_db_mngr()
        for item in self.tree_view_form.object_tree_model.visit_all():
            try:
                item.fetch_more()
            except NotImplementedError:
                pass
        self._fetch_parameter_models()
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        pluto_item = dog_item.child(0)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_fish_dog_index = self.tree_view_form.object_tree_model.index_from_item(pluto_fish_dog_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(pluto_fish_dog_index, QItemSelectionModel.Select)
        filtered_values = {
            self.tree_view_form.object_parameter_definition_model: [],
            self.tree_view_form.object_parameter_value_model: [],
            self.tree_view_form.relationship_parameter_definition_model: [('dog__fish',)],
            self.tree_view_form.relationship_parameter_value_model: [('dog__fish', 'pluto,nemo')],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_relationship(self):
        """Test that parameter tables are filtered when selecting relationships in the object tree.
        """
        self.put_mock_dataset_in_db_mngr()
        for item in self.tree_view_form.object_tree_model.visit_all():
            try:
                item.fetch_more()
            except NotImplementedError:
                pass
        self._fetch_parameter_models()
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        pluto_item = dog_item.child(0)
        pluto_fish_dog_item = pluto_item.child(0)
        fish_dog_nemo_pluto_item = pluto_fish_dog_item.child(0)
        fish_dog_nemo_pluto_index = self.tree_view_form.object_tree_model.index_from_item(fish_dog_nemo_pluto_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(
            fish_dog_nemo_pluto_index, QItemSelectionModel.Select
        )
        filtered_values = {
            self.tree_view_form.object_parameter_definition_model: [],
            self.tree_view_form.object_parameter_value_model: [],
            self.tree_view_form.relationship_parameter_definition_model: [('dog__fish',)],
            self.tree_view_form.relationship_parameter_value_model: [
                ('fish__dog', 'nemo,scooby'),
                ('dog__fish', 'pluto,nemo'),
            ],
        }
        self._assert_filter(filtered_values)
