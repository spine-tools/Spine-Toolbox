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

"""Unit tests for database item update functionality in Database editor."""
from spinedb_api import to_database
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


class TestSpineDBEditorUpdate(DBEditorTestBase):
    def test_update_object_classes_in_object_tree_model(self):
        """Test that object classes are updated in the object tree model."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.fetch_entity_tree_model()
        fish_update = {"id": self.fish_class["id"], "name": "octopus"}
        self.db_mngr.update_items("entity_class", {self.mock_db_map: [fish_update]})
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(1)
        self.assertEqual(fish_item.item_type, "entity_class")
        self.assertEqual(fish_item.display_data, "octopus")

    def test_update_objects_in_object_tree_model(self):
        """Test that objects are updated in the object tree model."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.fetch_entity_tree_model()
        nemo_update = {"id": self.nemo_object["id"], "name": "dory"}
        self.db_mngr.update_items("entity", {self.mock_db_map: [nemo_update]})
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = root_item.child(1)
        nemo_item = fish_item.child(0)
        self.assertEqual(nemo_item.item_type, "entity")
        self.assertEqual(nemo_item.display_data, "dory")

    def test_update_relationship_classes_in_object_tree_model(self):
        """Test that relationship classes are updated in the object tree model."""
        self.spine_db_editor.init_models()
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.fetch_entity_tree_model()
        fish_dog_update = {"id": self.fish_dog_class["id"], "name": "octopus__dog"}
        self.db_mngr.update_items("entity_class", {self.mock_db_map: [fish_dog_update]})
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_dog_item = root_item.child(3)
        self.assertEqual(fish_dog_item.item_type, "entity_class")
        self.assertEqual(fish_dog_item.display_data, "octopus__dog")

    def test_update_object_parameter_definitions_in_model(self):
        """Test that object parameter definitions are updated in the model."""
        model = self.spine_db_editor.parameter_definition_model
        model.init_model()
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.fetch_entity_tree_model()
        water_update = {"id": self.water_parameter["id"], "name": "fire"}
        self.db_mngr.update_items("parameter_definition", {self.mock_db_map: [water_update]})
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("entity_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish", "fire") in parameters)

    def test_update_relationship_parameter_definitions_in_model(self):
        """Test that object parameter definitions are updated in the model."""
        model = self.spine_db_editor.parameter_definition_model
        model.init_model()
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_relationship_classes_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.put_mock_relationship_parameter_definitions_in_db_mngr()
        self.fetch_entity_tree_model()
        relative_speed_update = {"id": self.relative_speed_parameter["id"], "name": "each_others_opinion"}
        self.db_mngr.update_items("parameter_definition", {self.mock_db_map: [relative_speed_update]})
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (model.index(row, h("entity_class_name")).data(), model.index(row, h("parameter_name")).data())
            )
        self.assertTrue(("fish__dog", "each_others_opinion") in parameters)

    def test_update_object_parameter_values_in_model(self):
        """Test that object parameter values are updated in the model."""
        model = self.spine_db_editor.parameter_value_model
        model.init_model()
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_object_classes_in_db_mngr()
        self.put_mock_objects_in_db_mngr()
        self.put_mock_object_parameter_definitions_in_db_mngr()
        self.put_mock_object_parameter_values_in_db_mngr()
        self.fetch_entity_tree_model()
        value, type_ = to_database("pepper")
        nemo_water_update = {"id": self.nemo_water["id"], "value": value, "type": type_}
        self.db_mngr.update_items("parameter_value", {self.mock_db_map: [nemo_water_update]})
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    model.index(row, h("entity_byname")).data(),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue(("nemo", "water", "pepper") in parameters)

    def test_update_relationship_parameter_values_in_model(self):
        """Test that relationship parameter values are updated in the model."""
        model = self.spine_db_editor.parameter_value_model
        model.init_model()
        if model.canFetchMore(None):
            model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        self.fetch_entity_tree_model()
        value, type_ = to_database(100)
        nemo_pluto_relative_speed_update = {
            "id": self.nemo_pluto_relative_speed["id"],
            "value": value,
            "type": type_,
        }
        self.db_mngr.update_items("parameter_value", {self.mock_db_map: [nemo_pluto_relative_speed_update]})
        h = model.header.index
        parameters = []
        for row in range(model.rowCount()):
            parameters.append(
                (
                    tuple((model.index(row, h("entity_byname")).data() or "").split(DB_ITEM_SEPARATOR)),
                    model.index(row, h("parameter_name")).data(),
                    model.index(row, h("value")).data(),
                )
            )
        self.assertTrue((("nemo", "pluto"), "relative_speed", "100.0") in parameters)
