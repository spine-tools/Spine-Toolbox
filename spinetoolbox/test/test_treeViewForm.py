######################################################################################################################
# Copyright (C) 2017 - 2019 Spine project consortium
# This file is part of Spine Toolbox.
# Spine Toolbox is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option)
# any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General
# Public License for more details. You should have received a copy of the GNU Lesser General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
######################################################################################################################

"""
Unit tests for TreeViewForm and GraphViewForm classes.

:author: M. Marin (KTH)
:date:   6.12.2018
"""

from collections import namedtuple
import unittest
from unittest import mock
import logging
import sys
from PySide2.QtWidgets import QApplication, QStyleOptionViewItem
from PySide2.QtCore import Qt, QItemSelectionModel, QItemSelection
from ..widgets.tree_view_widget import TreeViewForm
from ..widgets.custom_editors import SearchBarEditor, MultiSearchBarEditor, CustomLineEditor


class qry(list):
    def count(self, x=None):
        if x is not None:
            return super().count(x)
        return len(self)

    def all(self):
        return self


class TestTreeViewForm(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Overridden method. Runs once before all tests in this class."""
        try:
            cls.app = QApplication().processEvents()
        except RuntimeError:
            pass
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        cls.ObjectClass = namedtuple("ObjectClass", ["id", "name", "description", "display_order", "display_icon"])
        cls.Object = namedtuple("Object", ["id", "class_id", "name", "description"])
        cls.RelationshipClass = namedtuple(
            "RelationshipClass", ["id", "name", "object_class_id_list", "object_class_name_list"]
        )
        cls.Relationship = namedtuple("Relationship", ["id", "class_id", "name", "object_id_list", "object_name_list"])
        cls.ObjectParameter = namedtuple(
            "ObjectParameter",
            [
                'id',
                'object_class_id',
                'object_class_name',
                'parameter_name',
                'value_list_id',
                'value_list_name',
                'parameter_tag_id_list',
                'parameter_tag_list',
                'default_value',
            ],
        )
        cls.RelationshipParameter = namedtuple(
            "RelationshipParameter",
            [
                'id',
                'relationship_class_id',
                'relationship_class_name',
                'object_class_id_list',
                'object_class_name_list',
                'parameter_name',
                'value_list_id',
                'value_list_name',
                'parameter_tag_id_list',
                'parameter_tag_list',
                'default_value',
            ],
        )
        cls.ObjectParameterValue = namedtuple(
            "ObjectParameterValue",
            [
                'id',
                'object_class_id',
                'object_class_name',
                'object_id',
                'object_name',
                'parameter_id',
                'parameter_name',
                'value',
            ],
        )
        cls.RelationshipParameterValue = namedtuple(
            "RelationshipParameterValue",
            [
                'id',
                'relationship_class_id',
                'relationship_class_name',
                'object_class_id_list',
                'object_class_name_list',
                'relationship_id',
                'object_id_list',
                'object_name_list',
                'parameter_id',
                'parameter_name',
                'value',
            ],
        )

    def setUp(self):
        """Overridden method. Runs before each test. Makes instances of TreeViewForm and GraphViewForm classes."""
        with mock.patch("spinetoolbox.project.SpineToolboxProject") as mock_project, mock.patch(
            "spinedb_api.DiffDatabaseMapping"
        ) as mock_db_map, mock.patch(
            "spinetoolbox.widgets.tree_view_widget.TreeViewForm.restore_ui"
        ) as mock_restore_ui:
            mock_db_map.object_parameter_definition_fields.return_value = [
                'id',
                'object_class_id',
                'object_class_name',
                'parameter_name',
                'value_list_id',
                'value_list_name',
                'parameter_tag_id_list',
                'parameter_tag_list',
                'default_value',
            ]
            mock_db_map.relationship_parameter_definition_fields.return_value = [
                'id',
                'relationship_class_id',
                'relationship_class_name',
                'object_class_id_list',
                'object_class_name_list',
                'parameter_name',
                'value_list_id',
                'value_list_name',
                'parameter_tag_id_list',
                'parameter_tag_list',
                'default_value',
            ]
            mock_db_map.object_parameter_value_fields.return_value = [
                'id',
                'object_class_id',
                'object_class_name',
                'object_id',
                'object_name',
                'parameter_id',
                'parameter_name',
                'value',
            ]
            mock_db_map.relationship_parameter_value_fields.return_value = [
                'id',
                'relationship_class_id',
                'relationship_class_name',
                'object_class_id_list',
                'object_class_name_list',
                'relationship_id',
                'object_id_list',
                'object_name_list',
                'parameter_id',
                'parameter_name',
                'value',
            ]
            mock_db_map.add_wide_relationships.return_value = qry(), []
            mock_db_map.add_parameter_definitions.return_value = qry(), []
            mock_db_map.add_parameter_values.return_value = qry(), []
            self.tree_view_form = TreeViewForm(mock_project, {"mock_db": mock_db_map})
            self.fish_class = None
            self.dog_class = None
            self.nemo_object = None
            self.pluto_object = None
            self.scooby_object = None
            self.fish_dog_class = None
            self.dog_fish_class = None
            self.pluto_nemo_rel = None
            self.nemo_pluto_rel = None
            self.nemo_scooby_rel = None
            self.water_parameter = None
            self.breed_parameter = None
            self.relative_speed_parameter = None
            self.combined_mojo_parameter = None
            self.nemo_water = None
            self.pluto_breed = None
            self.scooby_breed = None
            self.nemo_pluto_relative_speed = None
            self.nemo_scooby_relative_speed = None
            self.pluto_nemo_combined_mojo = None

    def tearDown(self):
        """Overridden method. Runs after each test.
        Use this to free resources after a test if needed.
        """
        with mock.patch(
            "spinetoolbox.widgets.data_store_widget.DataStoreForm._prompt_close_and_commit"
        ) as mock_p_c_and_c, mock.patch(
            "spinetoolbox.widgets.tree_view_widget.TreeViewForm.save_window_state"
        ) as mock_save_w_s:
            mock_p_c_and_c.return_value = True
            self.tree_view_form.close()
            mock_p_c_and_c.assert_called_once()
            mock_save_w_s.assert_called_once()
        self.tree_view_form.deleteLater()
        self.tree_view_form = None

    def test_add_object_classes(self):
        """Test that object classes are added to the object tree model in the right positions.
        """
        db_map = self.tree_view_form.db_maps[0]
        object_classes = qry(
            [
                self.ObjectClass(1, "fish", "A fish.", 1, None),
                self.ObjectClass(2, "dog", "A dog.", 3, None),
                self.ObjectClass(3, "cat", "A cat.", 2, None),
            ]
        )
        db_map.add_object_classes.return_value = object_classes, []
        self.tree_view_form.add_object_classes({db_map: object_classes})
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_type = fish_item.data(Qt.UserRole)
        fish_name = fish_item.data(Qt.UserRole + 1)[db_map]['name']
        dog_item = root_item.child(2)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)[db_map]['name']
        cat_item = root_item.child(1)
        cat_type = cat_item.data(Qt.UserRole)
        cat_name = cat_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(fish_type, "object_class")
        self.assertEqual(fish_name, "fish")
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "dog")
        self.assertEqual(cat_type, "object_class")
        self.assertEqual(cat_name, "cat")
        self.assertEqual(root_item.rowCount(), 3)

    def test_add_objects(self):
        """Test that objects are added to the object tree model."""
        self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        objects = qry(
            [
                self.Object(1, self.fish_class.id, "nemo", "The lost one."),
                self.Object(2, self.fish_class.id, "dory", "Nemo's girl."),
                self.Object(3, self.dog_class.id, "pluto", "Mickey's."),
                self.Object(4, self.dog_class.id, "scooby", "Scooby-Dooby-Doo."),
            ]
        )
        # Fetch fish and dog object class id before adding objects, to reach more lines of code
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        db_map = self.tree_view_form.db_maps[0]
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == self.fish_class.id:
                return objects[0:2]
            elif class_id == self.dog_class.id:
                return objects[2:4]
            else:
                return qry()

        db_map.object_list.side_effect = side_effect
        db_map.add_objects.return_value = objects, []
        # Add objects
        self.tree_view_form.add_objects({db_map: objects})
        # Check tree
        nemo_item = fish_item.child(0)
        nemo_type = nemo_item.data(Qt.UserRole)
        nemo_class_id = nemo_item.data(Qt.UserRole + 1)[db_map]['class_id']
        nemo_id = nemo_item.data(Qt.UserRole + 1)[db_map]['id']
        nemo_name = nemo_item.data(Qt.UserRole + 1)[db_map]['name']
        dory_item = fish_item.child(1)
        dory_type = dory_item.data(Qt.UserRole)
        dory_class_id = dory_item.data(Qt.UserRole + 1)[db_map]['class_id']
        dory_id = dory_item.data(Qt.UserRole + 1)[db_map]['id']
        dory_name = dory_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_item = dog_item.child(0)
        pluto_type = pluto_item.data(Qt.UserRole)
        pluto_class_id = pluto_item.data(Qt.UserRole + 1)[db_map]['class_id']
        pluto_id = pluto_item.data(Qt.UserRole + 1)[db_map]['id']
        pluto_name = pluto_item.data(Qt.UserRole + 1)[db_map]['name']
        scooby_item = dog_item.child(1)
        scooby_type = scooby_item.data(Qt.UserRole)
        scooby_class_id = scooby_item.data(Qt.UserRole + 1)[db_map]['class_id']
        scooby_id = scooby_item.data(Qt.UserRole + 1)[db_map]['id']
        scooby_name = scooby_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(nemo_type, "object")
        self.assertEqual(nemo_class_id, self.fish_class.id)
        self.assertEqual(nemo_id, 1)
        self.assertEqual(nemo_name, "nemo")
        self.assertEqual(dory_type, "object")
        self.assertEqual(dory_class_id, self.fish_class.id)
        self.assertEqual(dory_id, 2)
        self.assertEqual(dory_name, "dory")
        self.assertEqual(fish_item.rowCount(), 2)
        self.assertEqual(pluto_type, "object")
        self.assertEqual(pluto_class_id, self.dog_class.id)
        self.assertEqual(pluto_id, 3)
        self.assertEqual(pluto_name, "pluto")
        self.assertEqual(scooby_type, "object")
        self.assertEqual(scooby_class_id, self.dog_class.id)
        self.assertEqual(scooby_id, 4)
        self.assertEqual(scooby_name, "scooby")
        self.assertEqual(fish_item.rowCount(), 2)

    def test_add_relationship_classes(self):
        """Test that relationship classes are added to the object tree model."""
        self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        # Add nemo object before adding the relationships to test fetch more
        nemo = dict(class_id=self.fish_class.id, name='nemo', description='The lost one.')
        nemo_object = self.Object(1, self.fish_class.id, "nemo", "The lost one.")
        db_map = self.tree_view_form.db_maps[0]
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == self.fish_class.id:
                return qry([nemo_object])
            else:
                return qry()

        db_map.object_list.side_effect = side_effect
        db_map.add_objects.return_value = qry([nemo_object]), []
        # Add nemo object
        self.tree_view_form.add_objects({db_map: qry([nemo_object])})
        # Add dog__fish and fish__dog relationship classes
        relationship_classes = qry(
            [
                self.RelationshipClass(
                    1, "dog__fish", str(self.dog_class.id) + "," + str(self.fish_class.id), "dog,fish"
                ),
                self.RelationshipClass(
                    2, "fish__dog", str(self.fish_class.id) + "," + str(self.dog_class.id), "fish,dog"
                ),
            ]
        )
        # Make wide_relationship_class_list return something meaningful
        def side_effect(object_class_id):
            if object_class_id in (self.fish_class.id, self.dog_class.id):
                return relationship_classes
            else:
                return qry()

        db_map.wide_relationship_class_list.side_effect = side_effect
        db_map.add_wide_relationship_classes.return_value = relationship_classes, []
        self.tree_view_form.add_relationship_classes({db_map: relationship_classes})
        # Add pluto object after adding the relationships to test fetch more
        pluto_object = self.Object(2, self.dog_class.id, "pluto", "Mickey's.")
        # Make object_list return something meaningful
        def side_effect(class_id):
            if class_id == self.fish_class.id:
                return qry([nemo_object])
            if class_id == self.dog_class.id:
                return qry([pluto_object])
            else:
                return qry()

        db_map.object_list.side_effect = side_effect
        db_map.object_list.return_value = qry([pluto_object]), []
        self.tree_view_form.add_objects({db_map: qry([pluto_object])})
        root_item = self.tree_view_form.object_tree_model.root_item
        # Fetch fish
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        # Check that nemo can fetch more (even if the relationship class was added)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        can_nemo_fetch_more = self.tree_view_form.object_tree_model.canFetchMore(nemo_index)
        self.assertTrue(can_nemo_fetch_more, "Nemo can't fetch more.")
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        # Fetch dog
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Check that pluto *can* fetch more (since it wasn't there when adding the relationship class)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        can_pluto_fetch_more = self.tree_view_form.object_tree_model.canFetchMore(pluto_index)
        self.assertTrue(can_pluto_fetch_more, "Pluto can't fetch more.")
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        # Check relationship class items are good
        # The first one under nemo
        nemo_dog_fish_item = nemo_item.child(0)
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        nemo_dog_fish_obj_cls_id_list = nemo_dog_fish_item.data(Qt.UserRole + 1)[db_map]['object_class_id_list']
        nemo_dog_fish_obj_cls_name_list = nemo_dog_fish_item.data(Qt.UserRole + 1)[db_map]['object_class_name_list']
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "dog__fish")
        split_nemo_dog_fish_object_class_id_list = [int(x) for x in nemo_dog_fish_obj_cls_id_list.split(",")]
        self.assertEqual(split_nemo_dog_fish_object_class_id_list, [self.dog_class.id, self.fish_class.id])
        self.assertEqual(nemo_dog_fish_obj_cls_name_list, "dog,fish")
        self.assertEqual(nemo_item.rowCount(), 2)
        # The second one under pluto
        pluto_fish_dog_item = pluto_item.child(1)
        pluto_fish_dog_type = pluto_fish_dog_item.data(Qt.UserRole)
        pluto_fish_dog_name = pluto_fish_dog_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_fish_dog_obj_cls_id_list = pluto_fish_dog_item.data(Qt.UserRole + 1)[db_map]['object_class_id_list']
        pluto_fish_dog_obj_cls_name_list = pluto_fish_dog_item.data(Qt.UserRole + 1)[db_map]['object_class_name_list']
        self.assertEqual(pluto_fish_dog_type, "relationship_class")
        self.assertEqual(pluto_fish_dog_name, "fish__dog")
        split_pluto_fish_dog_object_class_id_list = [int(x) for x in pluto_fish_dog_obj_cls_id_list.split(",")]
        self.assertEqual(split_pluto_fish_dog_object_class_id_list, [self.fish_class.id, self.dog_class.id])
        self.assertEqual(pluto_fish_dog_obj_cls_name_list, "fish,dog")
        self.assertEqual(pluto_item.rowCount(), 2)

    def test_add_relationships(self):
        """Test that relationships are added to the object tree model."""
        self.add_mock_object_classes()
        self.tree_view_form.init_object_tree_model()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        # Add pluto_nemo, nemo_pluto and nemo_scooby relationships
        rel1 = self.Relationship(
            1, self.dog_fish_class.id, "rel1", str(self.pluto_object.id) + "," + str(self.nemo_object.id), "pluto,nemo"
        )
        rel2 = self.Relationship(
            2, self.fish_dog_class.id, "rel2", str(self.nemo_object.id) + "," + str(self.pluto_object.id), "nemo,pluto"
        )
        rel3 = self.Relationship(
            3,
            self.fish_dog_class.id,
            "rel3",
            str(self.nemo_object.id) + "," + str(self.scooby_object.id),
            "nemo,scooby",
        )

        db_map = self.tree_view_form.db_maps[0]
        # Make wide_relationship_list return something meaningful
        def side_effect(class_id, object_id):
            if class_id == self.dog_fish_class.id:
                if object_id in (self.nemo_object.id, self.pluto_object.id):
                    return qry([rel1])
                else:
                    return qry()
            elif class_id == self.fish_dog_class.id:
                if object_id == self.nemo_object.id:
                    return qry([rel2, rel3])
                elif object_id == self.pluto_object.id:
                    return qry([rel2])
                elif object_id == self.scooby_object.id:
                    return qry([rel3])
                else:
                    return qry()
            else:
                return qry()

        db_map.wide_relationship_list.side_effect = side_effect
        self.tree_view_form.add_relationships({db_map: qry([rel1, rel2, rel3])})
        # Get items
        root_item = self.tree_view_form.object_tree_model.root_item
        # Object class items
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Object items
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        # Relationship class items
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_fish_dog_item = scooby_item.child(0)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        pluto_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_fish_dog_item)
        scooby_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_dog_fish_item)
        scooby_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_fish_dog_index)
        # Relationship items
        pluto_nemo_item1 = pluto_dog_fish_item.child(0)
        pluto_nemo_item2 = nemo_dog_fish_item.child(0)
        nemo_pluto_item1 = pluto_fish_dog_item.child(0)
        nemo_pluto_item2 = nemo_fish_dog_item.child(0)
        nemo_scooby_item1 = scooby_fish_dog_item.child(0)
        nemo_scooby_item2 = nemo_fish_dog_item.child(1)
        # Check number of items is good
        self.assertEqual(nemo_dog_fish_item.rowCount(), 1)
        self.assertEqual(nemo_fish_dog_item.rowCount(), 2)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 1)
        self.assertEqual(scooby_dog_fish_item.rowCount(), 0)
        self.assertEqual(scooby_fish_dog_item.rowCount(), 1)
        # Check relationship items are good
        # pluto_nemo_item1
        pluto_nemo_item1_type = pluto_nemo_item1.data(Qt.UserRole)
        pluto_nemo_item1_name = pluto_nemo_item1.data(Qt.UserRole + 1)[db_map]['name']
        pluto_nemo_item1_class_id = pluto_nemo_item1.data(Qt.UserRole + 1)[db_map]['class_id']
        pluto_nemo_item1_object_id_list = pluto_nemo_item1.data(Qt.UserRole + 1)[db_map]['object_id_list']
        pluto_nemo_item1_object_name_list = pluto_nemo_item1.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(pluto_nemo_item1_type, "relationship")
        self.assertEqual(pluto_nemo_item1_name, 'rel1')
        self.assertEqual(pluto_nemo_item1_class_id, self.dog_fish_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item1_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [self.pluto_object.id, self.nemo_object.id])
        self.assertEqual(pluto_nemo_item1_object_name_list, "pluto,nemo")
        # pluto_nemo_item2
        pluto_nemo_item2_type = pluto_nemo_item2.data(Qt.UserRole)
        pluto_nemo_item2_name = pluto_nemo_item2.data(Qt.UserRole + 1)[db_map]['name']
        pluto_nemo_item2_class_id = pluto_nemo_item2.data(Qt.UserRole + 1)[db_map]['class_id']
        pluto_nemo_item2_object_id_list = pluto_nemo_item2.data(Qt.UserRole + 1)[db_map]['object_id_list']
        pluto_nemo_item2_object_name_list = pluto_nemo_item2.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(pluto_nemo_item2_type, "relationship")
        self.assertEqual(pluto_nemo_item2_name, 'rel1')
        self.assertEqual(pluto_nemo_item2_class_id, self.dog_fish_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in pluto_nemo_item2_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [self.pluto_object.id, self.nemo_object.id])
        self.assertEqual(pluto_nemo_item2_object_name_list, "pluto,nemo")
        # nemo_pluto_item1
        nemo_pluto_item1_type = nemo_pluto_item1.data(Qt.UserRole)
        nemo_pluto_item1_name = nemo_pluto_item1.data(Qt.UserRole + 1)[db_map]['name']
        nemo_pluto_item1_class_id = nemo_pluto_item1.data(Qt.UserRole + 1)[db_map]['class_id']
        nemo_pluto_item1_object_id_list = nemo_pluto_item1.data(Qt.UserRole + 1)[db_map]['object_id_list']
        nemo_pluto_item1_object_name_list = nemo_pluto_item1.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(nemo_pluto_item1_type, "relationship")
        self.assertEqual(nemo_pluto_item1_name, 'rel2')
        self.assertEqual(nemo_pluto_item1_class_id, self.fish_dog_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item1_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [self.nemo_object.id, self.pluto_object.id])
        self.assertEqual(nemo_pluto_item1_object_name_list, "nemo,pluto")
        # nemo_pluto_item2
        nemo_pluto_item2_type = nemo_pluto_item2.data(Qt.UserRole)
        nemo_pluto_item2_name = nemo_pluto_item2.data(Qt.UserRole + 1)[db_map]['name']
        nemo_pluto_item2_class_id = nemo_pluto_item2.data(Qt.UserRole + 1)[db_map]['class_id']
        nemo_pluto_item2_object_id_list = nemo_pluto_item2.data(Qt.UserRole + 1)[db_map]['object_id_list']
        nemo_pluto_item2_object_name_list = nemo_pluto_item2.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(nemo_pluto_item2_type, "relationship")
        self.assertEqual(nemo_pluto_item2_name, 'rel2')
        self.assertEqual(nemo_pluto_item2_class_id, self.fish_dog_class.id)
        split_pluto_nemo_object_id_list = [int(x) for x in nemo_pluto_item2_object_id_list.split(",")]
        self.assertEqual(split_pluto_nemo_object_id_list, [self.nemo_object.id, self.pluto_object.id])
        self.assertEqual(nemo_pluto_item2_object_name_list, "nemo,pluto")
        # nemo_scooby_item1
        nemo_scooby_item1_type = nemo_scooby_item1.data(Qt.UserRole)
        nemo_scooby_item1_name = nemo_scooby_item1.data(Qt.UserRole + 1)[db_map]['name']
        nemo_scooby_item1_class_id = nemo_scooby_item1.data(Qt.UserRole + 1)[db_map]['class_id']
        nemo_scooby_item1_object_id_list = nemo_scooby_item1.data(Qt.UserRole + 1)[db_map]['object_id_list']
        nemo_scooby_item1_object_name_list = nemo_scooby_item1.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(nemo_scooby_item1_type, "relationship")
        self.assertEqual(nemo_scooby_item1_name, 'rel3')
        self.assertEqual(nemo_scooby_item1_class_id, self.fish_dog_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item1_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [self.nemo_object.id, self.scooby_object.id])
        self.assertEqual(nemo_scooby_item1_object_name_list, "nemo,scooby")
        # nemo_scooby_item2
        nemo_scooby_item2_type = nemo_scooby_item2.data(Qt.UserRole)
        nemo_scooby_item2_name = nemo_scooby_item2.data(Qt.UserRole + 1)[db_map]['name']
        nemo_scooby_item2_class_id = nemo_scooby_item2.data(Qt.UserRole + 1)[db_map]['class_id']
        nemo_scooby_item2_object_id_list = nemo_scooby_item2.data(Qt.UserRole + 1)[db_map]['object_id_list']
        nemo_scooby_item2_object_name_list = nemo_scooby_item2.data(Qt.UserRole + 1)[db_map]['object_name_list']
        self.assertEqual(nemo_scooby_item2_type, "relationship")
        self.assertEqual(nemo_scooby_item2_name, 'rel3')
        self.assertEqual(nemo_scooby_item2_class_id, self.fish_dog_class.id)
        split_scooby_nemo_object_id_list = [int(x) for x in nemo_scooby_item2_object_id_list.split(",")]
        self.assertEqual(split_scooby_nemo_object_id_list, [self.nemo_object.id, self.scooby_object.id])
        self.assertEqual(nemo_scooby_item2_object_name_list, "nemo,scooby")

    @unittest.skip(
        "TODO: Travis gives a ValueError exception on line _, def_tag_error_log = db_map.set_parameter_definition_tags(tag_dict) in treeview_models.py"
    )
    def test_add_object_parameter_definitions(self):
        """Test that object parameter definitions are added to the model."""
        self.tree_view_form.object_parameter_definition_model.reset_model()
        # Add fish and dog object classes
        self.add_mock_object_classes()
        # Add object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter object class name
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertIsNone(obj_cls_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_cls_name_index)
        view.itemDelegate().setEditorData(editor, obj_cls_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'fish')
        self.assertEqual(editor.proxy_model.index(2, 0).data(), 'dog')
        editor.proxy_model.setData(editor.first_index, 'dog')
        view.itemDelegate().setModelData(editor, model, obj_cls_name_index)
        view.itemDelegate().destroyEditor(editor, obj_cls_name_index)
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), self.dog_class.id)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "")
        editor.setText("breed")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')

    @unittest.skip(
        "TODO: Travis gives a ValueError exception on line _, def_tag_error_log = db_map.set_parameter_definition_tags(tag_dict) in treeview_models.py"
    )
    def test_add_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are added to the model."""
        self.tree_view_form.relationship_parameter_definition_model.reset_model()
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        # Add relationship parameter definition
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        # Enter relationship class name
        rel_cls_name_index = model.index(0, header_index("relationship_class_name"))
        self.assertIsNone(rel_cls_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), rel_cls_name_index)
        view.itemDelegate().setEditorData(editor, rel_cls_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'fish__dog')
        self.assertEqual(editor.proxy_model.index(2, 0).data(), 'dog__fish')
        editor.proxy_model.setData(editor.first_index, 'dog__fish')
        view.itemDelegate().setModelData(editor, model, rel_cls_name_index)
        view.itemDelegate().destroyEditor(editor, rel_cls_name_index)
        self.assertEqual(rel_cls_name_index.data(), 'dog__fish')
        rel_cls_id_index = model.index(0, header_index("relationship_class_id"))
        self.assertEqual(rel_cls_id_index.data(), self.dog_fish_class.id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'dog,fish')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [self.dog_class.id, self.fish_class.id])
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor))
        self.assertEqual(editor.text(), "")
        editor.setText("combined_mojo")
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'combined_mojo')

    def test_add_object_parameter_values(self):
        """Test that object parameter values are added to the model."""
        self.tree_view_form.object_parameter_value_model.reset_model()
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_object_parameter_definitions()
        self.tree_view_form.init_models()
        # Add first object parameter value (for scooby), to test autofilling of object class from *object*
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        # Enter object name
        obj_name_index = model.index(0, header_index("object_name"))
        self.assertIsNone(obj_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 4)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'nemo')
        self.assertEqual(editor.proxy_model.index(2, 0).data(), 'pluto')
        self.assertEqual(editor.proxy_model.index(3, 0).data(), 'scooby')
        editor.proxy_model.setData(editor.first_index, 'scooby')
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertEqual(obj_name_index.data(), 'scooby')
        obj_id_index = model.index(0, header_index("object_id"))
        self.assertEqual(obj_id_index.data(), self.scooby_object.id)
        # Check object class
        obj_cls_name_index = model.index(0, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(0, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), self.dog_class.id)
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 2)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'breed')
        editor.proxy_model.setData(editor.first_index, 'breed')
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')
        # Add second object parameter value (for pluto), to test autofilling of object class from *parameter*
        # Enter parameter name
        parameter_name_index = model.index(1, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(2, 0).data(), 'breed')
        editor.proxy_model.setData(editor.first_index, 'breed')
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'breed')
        # Check objet class
        obj_cls_name_index = model.index(1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        obj_cls_id_index = model.index(1, header_index("object_class_id"))
        self.assertEqual(obj_cls_id_index.data(), self.dog_class.id)
        # Enter object name
        obj_name_index = model.index(1, header_index("object_name"))
        self.assertIsNone(obj_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_index)
        view.itemDelegate().setEditorData(editor, obj_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'pluto')
        self.assertEqual(editor.proxy_model.index(2, 0).data(), 'scooby')
        editor.proxy_model.setData(editor.first_index, 'pluto')
        view.itemDelegate().setModelData(editor, model, obj_name_index)
        view.itemDelegate().destroyEditor(editor, obj_name_index)
        self.assertEqual(obj_name_index.data(), 'pluto')
        obj_id_index = model.index(1, header_index("object_id"))
        self.assertEqual(obj_id_index.data(), self.pluto_object.id)

    def test_add_relationship_parameter_values(self):
        """Test that relationship parameter values are added to the model."""
        self.tree_view_form.relationship_parameter_value_model.reset_model()
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        self.add_mock_relationship_parameter_definitions()
        self.tree_view_form.init_models()
        # Fetch nemo's fish__dog
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish__dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish__dog_index)
        # Add nemo_pluto relationship
        # Don't add nemo_scooby since that one we want to be added 'on the fly'
        nemo_pluto_relationship = self.Relationship(
            1,
            self.fish_dog_class.id,
            "fish__dog_nemo__pluto",
            str(self.nemo_object.id) + "," + str(self.pluto_object.id),
            "nemo,pluto",
        )

        def side_effect(class_id=None, object_id=None):
            if class_id == self.fish_dog_class.id:
                if object_id in (self.nemo_object.id, self.pluto_object.id):
                    return [nemo_pluto_relationship]
                else:
                    return []
            elif class_id is None and object_id is None:
                return [nemo_pluto_relationship]
            else:
                return []

        self.tree_view_form.db_maps[0].wide_relationship_list.side_effect = side_effect
        # Add first relationship parameter value (for existing relationship)
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        # Enter parameter name
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'relative_speed')
        editor.proxy_model.setData(editor.first_index, 'relative_speed')
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'relative_speed')
        # Check relationship class
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, self.fish_dog_class.id)
        obj_cls_name_list_index = model.index(0, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(0, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [self.fish_class.id, self.dog_class.id])
        # Enter object name list
        obj_name_list_index = model.index(0, header_index("object_name_list"))
        self.assertIsNone(obj_name_list_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_list_index)
        view.itemDelegate().setEditorData(editor, obj_name_list_index)
        self.assertTrue(isinstance(editor, MultiSearchBarEditor))
        self.assertEqual(editor.horizontalHeader().count(), 2)
        left_index = editor.model.index(0, 0)
        left_editor = editor.itemDelegate().createEditor(editor, QStyleOptionViewItem(), left_index)
        self.assertEqual(left_editor.verticalHeader().count(), 2)
        self.assertEqual(left_editor.proxy_model.index(1, 0).data(), 'nemo')
        left_editor.proxy_model.setData(left_editor.first_index, 'nemo')
        right_index = editor.model.index(0, 1)
        right_editor = editor.itemDelegate().createEditor(editor, QStyleOptionViewItem(), right_index)
        self.assertEqual(right_editor.verticalHeader().count(), 3)
        self.assertEqual(right_editor.proxy_model.index(1, 0).data(), 'pluto')
        self.assertEqual(right_editor.proxy_model.index(2, 0).data(), 'scooby')
        right_editor.proxy_model.setData(right_editor.first_index, 'pluto')
        editor.itemDelegate().setModelData(left_editor, editor.model, left_index)
        editor.itemDelegate().setModelData(right_editor, editor.model, right_index)
        view.itemDelegate().setModelData(editor, model, obj_name_list_index)
        view.itemDelegate().destroyEditor(editor, obj_name_list_index)
        # Check relationship
        relationship_id = model.index(0, header_index("relationship_id")).data()
        self.assertEqual(relationship_id, nemo_pluto_relationship.id)
        obj_id_list_index = model.index(0, header_index("object_id_list"))
        split_obj_id_list = [int(x) for x in obj_id_list_index.data().split(',')]
        self.assertEqual(split_obj_id_list, [self.nemo_object.id, self.pluto_object.id])
        # Add second relationship parameter value (relationship on the fly)
        parameter_name_index = model.index(1, header_index("parameter_name"))
        self.assertIsNone(parameter_name_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, SearchBarEditor))
        self.assertEqual(editor.verticalHeader().count(), 3)
        self.assertEqual(editor.proxy_model.index(1, 0).data(), 'relative_speed')
        editor.proxy_model.setData(editor.first_index, 'relative_speed')
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        self.assertEqual(parameter_name_index.data(), 'relative_speed')
        # Check relationship class
        rel_cls_name = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, self.fish_dog_class.id)
        obj_cls_name_list_index = model.index(1, header_index("object_class_name_list"))
        self.assertEqual(obj_cls_name_list_index.data(), 'fish,dog')
        obj_cls_id_list_index = model.index(1, header_index("object_class_id_list"))
        split_obj_cls_id_list = [int(x) for x in obj_cls_id_list_index.data().split(",")]
        self.assertEqual(split_obj_cls_id_list, [self.fish_class.id, self.dog_class.id])
        # Enter object name list
        obj_name_list_index = model.index(1, header_index("object_name_list"))
        self.assertIsNone(obj_name_list_index.data())
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), obj_name_list_index)
        view.itemDelegate().setEditorData(editor, obj_name_list_index)
        self.assertTrue(isinstance(editor, MultiSearchBarEditor))
        self.assertEqual(editor.horizontalHeader().count(), 2)
        left_index = editor.model.index(0, 0)
        left_editor = editor.itemDelegate().createEditor(editor, QStyleOptionViewItem(), left_index)
        self.assertEqual(left_editor.verticalHeader().count(), 2)
        self.assertEqual(left_editor.proxy_model.index(1, 0).data(), 'nemo')
        left_editor.proxy_model.setData(left_editor.first_index, 'nemo')
        right_index = editor.model.index(0, 1)
        right_editor = editor.itemDelegate().createEditor(editor, QStyleOptionViewItem(), right_index)
        self.assertEqual(right_editor.verticalHeader().count(), 3)
        self.assertEqual(right_editor.proxy_model.index(1, 0).data(), 'pluto')
        self.assertEqual(right_editor.proxy_model.index(2, 0).data(), 'scooby')
        right_editor.proxy_model.setData(right_editor.first_index, 'scooby')
        editor.itemDelegate().setModelData(left_editor, editor.model, left_index)
        editor.itemDelegate().setModelData(right_editor, editor.model, right_index)
        view.itemDelegate().setModelData(editor, model, obj_name_list_index)
        view.itemDelegate().destroyEditor(editor, obj_name_list_index)
        # Check relationship
        obj_id_list_index = model.index(1, header_index("object_id_list"))
        split_obj_id_list = [int(x) for x in obj_id_list_index.data().split(',')]
        self.assertEqual(split_obj_id_list, [self.nemo_object.id, self.scooby_object.id])

    def test_paste_add_object_parameter_definitions(self):
        """Test that data is pasted onto the view and object parameter definitions are added to the model."""
        self.add_mock_object_classes()
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header = model.horizontal_header_labels()
        sorted_header = [
            header[view.horizontalHeader().logicalIndex(i)]
            for i in range(view.horizontalHeader().count())
            if not view.horizontalHeader().isSectionHidden(view.horizontalHeader().logicalIndex(i))
        ]
        d1 = {
            'parameter_name': 'breed',
            'default_value': "",
            'parameter_tag_list': "",
            'value_list_name': "",
            'object_class_name': "dog",
            'database': "mock_db",
        }
        d2 = {
            'parameter_name': 'water',
            'default_value': "",
            'parameter_tag_list': "",
            'value_list_name': "",
            'object_class_name': "fish",
            'database': "mock_db",
        }
        data1 = [d1[h] for h in sorted_header]
        data2 = [d2[h] for h in sorted_header]
        clipboard_text = "\t".join(data1) + "\n" + "\t".join(data2) + "\n"
        header_index = header.index
        QApplication.clipboard().setText(clipboard_text)
        obj_cls_name_index = model.index(0, 0)
        view.setCurrentIndex(obj_cls_name_index)
        self.tree_view_form.db_maps[0].set_parameter_definition_tags.return_value = qry([]), []
        self.tree_view_form.db_maps[0].update_parameters.return_value = qry([]), []
        view.paste()
        # Check model
        # Object class name and id
        obj_cls_name0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name0, 'dog')
        self.assertEqual(obj_cls_name1, 'fish')
        obj_cls_id0 = model.index(0, header_index("object_class_id")).data()
        obj_cls_id1 = model.index(1, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id0, self.dog_class.id)
        self.assertEqual(obj_cls_id1, self.fish_class.id)
        # Parameter name
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'breed')
        self.assertEqual(parameter_name1, 'water')

    @unittest.skip("TODO: Fix this. Does not work on Windows nor on Travis")
    def test_paste_add_object_parameter_values(self):
        """Test that data is pasted onto the view and object parameter values are added to the model."""
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_object_parameter_definitions()
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header = model.horizontal_header_labels()
        sorted_header = [
            header[view.horizontalHeader().logicalIndex(i)]
            for i in range(view.horizontalHeader().count())
            if not view.horizontalHeader().isSectionHidden(view.horizontalHeader().logicalIndex(i))
        ]
        d1 = {
            'parameter_name': "water",
            'object_name': "nemo",
            'value': '"salt"',
            'object_class_name': "",
            'database': "mock_db",
        }
        d2 = {
            'parameter_name': "breed",
            'object_name': "pluto",
            'value': '"bloodhound"',
            'object_class_name': "",
            'database': "mock_db",
        }
        d3 = {
            'parameter_name': "breed",
            'object_name': "scooby",
            'value': '"great dane"',
            'object_class_name': "",
            'database': "mock_db",
        }
        data1 = [d1[h] for h in sorted_header]
        data2 = [d2[h] for h in sorted_header]
        data3 = [d3[h] for h in sorted_header]
        clipboard_text = "\t".join(data1) + "\n" + "\t".join(data2) + "\n" + "\t".join(data3) + "\n"
        header_index = header.index
        QApplication.clipboard().setText(clipboard_text)
        obj_name_index = model.index(0, 0)
        view.setCurrentIndex(obj_name_index)
        view.paste()
        # Check model
        # Object class name and id
        obj_cls_name = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'fish')
        obj_cls_id = model.index(0, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, self.fish_class.id)
        obj_cls_name = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'dog')
        obj_cls_id = model.index(1, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, self.dog_class.id)
        obj_cls_name = model.index(2, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name, 'dog')
        obj_cls_id = model.index(2, header_index("object_class_id")).data()
        self.assertEqual(obj_cls_id, self.dog_class.id)
        # Parameter name and id
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'water')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.water_parameter.id)
        parameter_name = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'breed')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.breed_parameter.id)
        parameter_name = model.index(2, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'breed')
        parameter_id = model.index(2, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.breed_parameter.id)
        # Object name and id
        obj_name = model.index(0, header_index("object_name")).data()
        self.assertEqual(obj_name, 'nemo')
        obj_id = model.index(0, header_index("object_id")).data()
        self.assertEqual(obj_id, self.nemo_object.id)
        obj_name = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name, 'pluto')
        obj_id = model.index(1, header_index("object_id")).data()
        self.assertEqual(obj_id, self.pluto_object.id)
        obj_name = model.index(2, header_index("object_name")).data()
        self.assertEqual(obj_name, 'scooby')
        obj_id = model.index(2, header_index("object_id")).data()
        self.assertEqual(obj_id, self.scooby_object.id)
        # Parameter value and id
        value = model.index(0, header_index("value")).data()
        self.assertEqual(value, 'salt')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.water_parameter.id)
        value = model.index(1, header_index("value")).data()
        self.assertEqual(value, 'bloodhound')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.breed_parameter.id)
        value = model.index(2, header_index("value")).data()
        self.assertEqual(value, 'great dane')
        parameter_id = model.index(2, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.breed_parameter.id)

    def test_paste_add_relationship_parameter_definitions(self):
        """Test that data is pasted onto the view and relationship parameter definitions are added to the model."""
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header = model.horizontal_header_labels()
        sorted_header = [
            header[view.horizontalHeader().logicalIndex(i)]
            for i in range(view.horizontalHeader().count())
            if not view.horizontalHeader().isSectionHidden(view.horizontalHeader().logicalIndex(i))
        ]
        d1 = {
            'parameter_name': 'relative_speed',
            'default_value': "",
            'parameter_tag_list': "",
            'object_class_name_list': "",
            'relationship_class_name': "fish__dog",
            'value_list_name': "",
            'database': "mock_db",
        }
        d2 = {
            'parameter_name': 'combined_mojo',
            'default_value': "",
            'parameter_tag_list': "",
            'object_class_name_list': "",
            'relationship_class_name': "dog__fish",
            'value_list_name': "",
            'database': "mock_db",
        }
        data1 = [d1[h] for h in sorted_header]
        data2 = [d2[h] for h in sorted_header]
        clipboard_text = "\t".join(data1) + "\n" + "\t".join(data2) + "\n"
        header_index = header.index
        QApplication.clipboard().setText(clipboard_text)
        rel_class_name_index = model.index(0, 0)
        view.setCurrentIndex(rel_class_name_index)
        self.tree_view_form.db_maps[0].set_parameter_definition_tags.return_value = qry([]), []
        self.tree_view_form.db_maps[0].update_parameters.return_value = qry([]), []
        view.paste()
        # Check model
        # Relationship class name and id
        rel_cls_name0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name1 = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name0, 'fish__dog')
        self.assertEqual(rel_cls_name1, 'dog__fish')
        rel_cls_id0 = model.index(0, header_index("relationship_class_id")).data()
        rel_cls_id1 = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id0, self.fish_dog_class.id)
        self.assertEqual(rel_cls_id1, self.dog_fish_class.id)
        # Object class name and id list
        obj_cls_name_lst0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst1, 'dog,fish')
        obj_cls_id_lst0 = model.index(0, header_index("object_class_id_list")).data()
        obj_cls_id_lst1 = model.index(1, header_index("object_class_id_list")).data()
        self.assertEqual(obj_cls_id_lst0, str(self.fish_class.id) + "," + str(self.dog_fish_class.id))
        self.assertEqual(obj_cls_id_lst1, str(self.dog_fish_class.id) + "," + str(self.fish_class.id))
        # Parameter name
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'relative_speed')
        self.assertEqual(parameter_name1, 'combined_mojo')

    @unittest.skip("TODO: Fix this. Does not work on Windows nor on Travis")
    def test_paste_add_relationship_parameter_values(self):
        """Test that data is pasted onto the view and relationship parameter values are added to the model."""
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        self.add_mock_relationships()
        self.add_mock_relationship_parameter_definitions()
        self.tree_view_form.init_models()
        # Paste data
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header = model.horizontal_header_labels()
        sorted_header = [
            header[view.horizontalHeader().logicalIndex(i)]
            for i in range(view.horizontalHeader().count())
            if not view.horizontalHeader().isSectionHidden(view.horizontalHeader().logicalIndex(i))
        ]
        d1 = {
            'relationship_class_name': "",
            'object_class_name_list': "",
            'object_name_list': "nemo,pluto",
            'parameter_name': "relative_speed",
            'value': "-1",
            'database': "mock_db",
        }
        d2 = {
            'relationship_class_name': "",
            'object_class_name_list': "",
            'object_name_list': "pluto,nemo",
            'parameter_name': "combined_mojo",
            'value': "100",
            'database': "mock_db",
        }
        data1 = [d1[h] for h in sorted_header]
        data2 = [d2[h] for h in sorted_header]
        clipboard_text = "\t".join(data1) + "\n" + "\t".join(data2) + "\n"
        header_index = header.index
        QApplication.clipboard().setText(clipboard_text)
        obj_cls_name_lst_index = model.index(0, 0)
        view.setCurrentIndex(obj_cls_name_lst_index)
        view.paste()
        # Check model
        # Relationship class name and id
        rel_cls_name = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'fish__dog')
        rel_cls_id = model.index(0, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, self.fish_dog_class.id)
        rel_cls_name = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name, 'dog__fish')
        rel_cls_id = model.index(1, header_index("relationship_class_id")).data()
        self.assertEqual(rel_cls_id, self.dog_fish_class.id)
        # Parameter name and id
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'relative_speed')
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.relative_speed_parameter.id)
        parameter_name = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'combined_mojo')
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.combined_mojo_parameter.id)
        # Object name and id list
        obj_name_lst = model.index(0, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst, 'nemo,pluto')
        obj_id_lst = model.index(0, header_index("object_id_list")).data()
        self.assertEqual(obj_id_lst, str(self.nemo_object.id) + "," + str(self.pluto_object.id))
        obj_name_lst = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst, 'pluto,nemo')
        obj_id_lst = model.index(1, header_index("object_id_list")).data()
        self.assertEqual(obj_id_lst, str(self.pluto_object.id) + "," + str(self.nemo_object.id))
        # Parameter value and id
        value = model.index(0, header_index("value")).data()
        self.assertEqual(value, -1)
        parameter_id = model.index(0, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.relative_speed_parameter.id)
        value = model.index(1, header_index("value")).data()
        self.assertEqual(value, 100)
        parameter_id = model.index(1, header_index("parameter_id")).data()
        self.assertEqual(parameter_id, self.combined_mojo_parameter.id)

    @unittest.skip("TODO: Manuel")
    def test_copy_from_parameter_tables(self):
        """Test that data is copied from each parameter table into the clipboard."""
        self.add_mock_dataset()
        # Object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header = model.horizontal_header_labels()
        sorted_index = [
            view.horizontalHeader().logicalIndex(i)
            for i in range(view.horizontalHeader().count())
            if not view.horizontalHeader().isSectionHidden(view.horizontalHeader().logicalIndex(i))
        ]
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:2], ['fish', 'water'])
        self.assertEqual(data[1][0:2], ['dog', 'breed'])
        # Object parameter value
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:4], ['fish', 'nemo', 'water', '"salt"'])
        self.assertEqual(data[1][0:4], ['dog', 'pluto', 'breed', '"bloodhound"'])
        self.assertEqual(data[2][0:4], ['dog', 'scooby', 'breed', '"great dane"'])
        # Relationship parameter definition
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:3], ['fish__dog', 'fish,dog', 'relative_speed'])
        self.assertEqual(data[1][0:3], ['dog__fish', 'dog,fish', 'combined_mojo'])
        # Relationship parameter value
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        top_left = model.index(0, 0)
        bottom_right = model.index(model.rowCount() - 1, model.columnCount() - 1)
        item_selection = QItemSelection(top_left, bottom_right)
        view.selectionModel().select(item_selection, QItemSelectionModel.Select)
        view.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data[0][0:4], ['fish__dog', 'nemo,pluto', 'relative_speed', '-1'])
        self.assertEqual(data[1][0:4], ['fish__dog', 'nemo,scooby', 'relative_speed', '5'])
        self.assertEqual(data[2][0:4], ['dog__fish', 'pluto,nemo', 'combined_mojo', '100'])

    def test_copy_from_object_tree(self):
        """Test that data is copied from object_tree into the clipboard."""
        self.add_mock_dataset()
        # Fetch entire object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        root_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.selectionModel().select(scooby_index, QItemSelectionModel.Select)
        self.tree_view_form.ui.treeView_object.copy()
        clipboard_text = QApplication.clipboard().text()
        data = [line.split('\t') for line in clipboard_text.split('\n')]
        self.assertEqual(data, [['fish'], ['dog'], ['nemo'], ['scooby']])

    def test_set_object_parameter_definition_defaults(self):
        """Test that defaults are set in object parameter definition models according the object tree selection."""
        self.add_mock_object_classes()
        self.tree_view_form.init_models()
        # Select fish item in object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_tree_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Select)
        # Check default in object parameter definition
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'fish')
        # Deselected fish and select dog item in object tree
        dog_item = root_item.child(1)
        dog_tree_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_tree_index, QItemSelectionModel.Deselect)
        self.tree_view_form.ui.treeView_object.selectionModel().select(dog_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertEqual(obj_cls_name_index.data(), 'dog')
        # Clear object tree selection and select root
        self.tree_view_form.ui.treeView_object.selectionModel().clearSelection()
        root_tree_index = self.tree_view_form.object_tree_model.indexFromItem(root_item)
        self.tree_view_form.ui.treeView_object.selectionModel().select(root_tree_index, QItemSelectionModel.Select)
        obj_cls_name_index = model.index(model.rowCount() - 1, header_index("object_class_name"))
        self.assertIsNone(obj_cls_name_index.data())

    @unittest.skip("TODO")
    def test_set_object_parameter_value_defaults(self):
        """Test that defaults are set in relationship parameter definition
        models according the object tree selection.
        """
        self.fail()

    @unittest.skip("TODO")
    def test_set_relationship_parameter_definition_defaults(self):
        """Test that defaults are set in relationship parameter definition
        models according the object tree selection.
        """
        self.fail()

    @unittest.skip("TODO")
    def test_set_relationship_parameter_value_defaults(self):
        """Test that defaults are set in relationship parameter definition
        models according the object tree selection.
        """
        self.fail()

    def test_update_object_classes(self):
        """Test that object classes are updated on all model/views."""
        self.add_mock_dataset()
        upd_fish_class = self.ObjectClass(self.fish_class.id, "octopus", "A fish.", 1, None)
        upd_dog_class = self.ObjectClass(self.dog_class.id, "god", "A fish.", 3, None)
        db_map = self.tree_view_form.db_maps[0]
        db_map.update_object_classes.return_value = qry([upd_fish_class, upd_dog_class]), []
        obj_cls_d = {db_map: qry([upd_fish_class, upd_dog_class])}
        self.tree_view_form.update_object_classes(obj_cls_d)
        # Check object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_type = fish_item.data(Qt.UserRole)
        fish_name = fish_item.data(Qt.UserRole + 1)[db_map]['name']
        dog_item = root_item.child(1)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(fish_type, "object_class")
        self.assertEqual(fish_name, "octopus")
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "god")
        self.assertEqual(root_item.rowCount(), 2)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'octopus')
        self.assertEqual(obj_cls_name_1, 'god')
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        obj_cls_name_2 = model.index(2, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'octopus')
        self.assertEqual(obj_cls_name_1, 'god')
        self.assertEqual(obj_cls_name_2, 'god')
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_1, 'god,octopus')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        obj_cls_name_lst_2 = model.index(2, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_1, 'octopus,god')
        self.assertEqual(obj_cls_name_lst_2, 'god,octopus')

    def test_update_objects(self):
        """Test that objects are updated on all model/views."""
        self.add_mock_dataset()
        # Fetch object classes
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        # Update objects
        upd_nemo_object = self.Object(self.nemo_object.id, self.fish_class.id, "dory", "")
        upd_pluto_object = self.Object(self.pluto_object.id, self.dog_class.id, "rascal", "")
        db_map = self.tree_view_form.db_maps[0]
        db_map.update_objects.return_value = qry([upd_nemo_object, upd_pluto_object]), []
        object_d = {db_map: qry([upd_nemo_object, upd_pluto_object])}
        self.tree_view_form.update_objects(object_d)
        # Check object tree
        nemo_item = fish_item.child(0)
        nemo_type = nemo_item.data(Qt.UserRole)
        nemo_name = nemo_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_item = dog_item.child(0)
        pluto_type = pluto_item.data(Qt.UserRole)
        pluto_name = pluto_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(nemo_type, "object")
        self.assertEqual(nemo_name, "dory")
        self.assertEqual(pluto_type, "object")
        self.assertEqual(pluto_name, "rascal")
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        obj_name_1 = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'dory')
        self.assertEqual(obj_name_1, 'rascal')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        obj_name_lst_2 = model.index(2, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'dory,rascal')
        self.assertEqual(obj_name_lst_1, 'dory,scooby')
        self.assertEqual(obj_name_lst_2, 'rascal,dory')

    def test_update_relationship_classes(self):
        """Test that relationship classes are updated on all model/views."""
        self.add_mock_dataset()
        # Fetch object classes and objects
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        # Update relationship classes
        upd_fish_dog_class = self.RelationshipClass(
            self.fish_dog_class.id, "octopus__god", str(self.fish_class.id) + "," + str(self.dog_class.id), "fish,dog"
        )
        upd_dog_fish_class = self.RelationshipClass(
            self.dog_fish_class.id, "god__octopus", str(self.dog_class.id) + "," + str(self.fish_class.id), "dog,fish"
        )
        db_map = self.tree_view_form.db_maps[0]
        db_map.update_wide_relationship_classes.return_value = qry([upd_fish_dog_class, upd_dog_fish_class]), []
        rel_cls_d = {db_map: qry([upd_fish_dog_class, upd_dog_fish_class])}
        self.tree_view_form.update_relationship_classes(rel_cls_d)
        # Check object tree
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_fish_dog_item = scooby_item.child(0)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_fish_dog_type = nemo_fish_dog_item.data(Qt.UserRole)
        nemo_fish_dog_name = nemo_fish_dog_item.data(Qt.UserRole + 1)[db_map]['name']
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_fish_dog_type = pluto_fish_dog_item.data(Qt.UserRole)
        pluto_fish_dog_name = pluto_fish_dog_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_dog_fish_type = pluto_dog_fish_item.data(Qt.UserRole)
        pluto_dog_fish_name = pluto_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        scooby_fish_dog_type = scooby_fish_dog_item.data(Qt.UserRole)
        scooby_fish_dog_name = scooby_fish_dog_item.data(Qt.UserRole + 1)[db_map]['name']
        scooby_dog_fish_type = scooby_dog_fish_item.data(Qt.UserRole)
        scooby_dog_fish_name = scooby_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(nemo_fish_dog_type, "relationship_class")
        self.assertEqual(nemo_fish_dog_name, "octopus__god")
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "god__octopus")
        self.assertEqual(pluto_fish_dog_type, "relationship_class")
        self.assertEqual(pluto_fish_dog_name, "octopus__god")
        self.assertEqual(pluto_dog_fish_type, "relationship_class")
        self.assertEqual(pluto_dog_fish_name, "god__octopus")
        self.assertEqual(scooby_fish_dog_type, "relationship_class")
        self.assertEqual(scooby_fish_dog_name, "octopus__god")
        self.assertEqual(scooby_dog_fish_type, "relationship_class")
        self.assertEqual(scooby_dog_fish_name, "god__octopus")
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name_1 = model.index(1, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'octopus__god')
        self.assertEqual(rel_cls_name_1, 'god__octopus')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        rel_cls_name_1 = model.index(1, header_index("relationship_class_name")).data()
        rel_cls_name_2 = model.index(2, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'octopus__god')
        self.assertEqual(rel_cls_name_1, 'octopus__god')
        self.assertEqual(rel_cls_name_2, 'god__octopus')

    def test_update_relationships(self):
        """Test that relationships are updated on all model/views."""
        self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_dog_fish_item = pluto_item.child(1)
        scooby_dog_fish_item = scooby_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        scooby_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_dog_fish_index)
        # Update relationship
        upd_pluto_nemo_rel = self.Relationship(
            self.pluto_nemo_rel.id,
            self.dog_fish_class.id,
            "dog__fish_scooby__nemo",
            str(self.scooby_object.id) + "," + str(self.nemo_object.id),
            "scooby,nemo",
        )
        db_map = self.tree_view_form.db_maps[0]
        db_map.update_wide_relationships.return_value = qry([upd_pluto_nemo_rel]), []
        relationship_d = {db_map: qry([upd_pluto_nemo_rel])}
        self.tree_view_form.update_relationships(relationship_d)
        # Check object tree
        scooby_nemo_item1 = nemo_dog_fish_item.child(0)
        scooby_nemo_item2 = scooby_dog_fish_item.child(0)
        scooby_nemo_item1_type = scooby_nemo_item1.data(Qt.UserRole)
        scooby_nemo_item1_name = scooby_nemo_item1.data(Qt.UserRole + 1)[db_map]['name']
        scooby_nemo_item2_type = scooby_nemo_item2.data(Qt.UserRole)
        scooby_nemo_item2_name = scooby_nemo_item2.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(scooby_nemo_item1_type, "relationship")
        self.assertEqual(scooby_nemo_item1_name, "dog__fish_scooby__nemo")
        self.assertEqual(scooby_nemo_item2_type, "relationship")
        self.assertEqual(scooby_nemo_item2_name, "dog__fish_scooby__nemo")
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)

    def test_remove_object_classes(self):
        """Test that object classes are removed from all model/views."""
        self.add_mock_dataset()
        # Fetch pluto, so we can test that 'child' relationship classes are correctly removed
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.assertEqual(pluto_item.rowCount(), 2)
        # Select fish and call the removal method
        fish_item = root_item.child(0)
        db_map = self.tree_view_form.db_maps[0]
        item_d = {db_map: {'object_class': [fish_item.data(Qt.UserRole + 1)[db_map]]}}
        self.tree_view_form.remove_tree_items(item_d)
        # Check object tree
        dog_item = root_item.child(0)
        dog_type = dog_item.data(Qt.UserRole)
        dog_name = dog_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(dog_type, "object_class")
        self.assertEqual(dog_name, "dog")
        self.assertEqual(root_item.rowCount(), 1)
        self.assertEqual(pluto_item.rowCount(), 0)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        obj_cls_name_1 = model.index(1, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(obj_cls_name_1, 'dog')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        self.assertEqual(model.rowCount(), 1)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        self.assertEqual(model.rowCount(), 1)

    def test_remove_objects(self):
        """Test that objects are removed from all model/views."""
        self.add_mock_dataset()
        # Fetch pluto's fish__dog and dog__fish relationship class items,
        # so we can test that 'child' relationships are correctly removed
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        pluto_fish_dog_item = pluto_item.child(0)
        pluto_dog_fish_item = pluto_item.child(1)
        pluto_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_fish_dog_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(pluto_fish_dog_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 1)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        # Select nemo and call removal method
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        db_map = self.tree_view_form.db_maps[0]
        item_d = {db_map: {'object': [nemo_item.data(Qt.UserRole + 1)[db_map]]}}
        self.tree_view_form.remove_tree_items(item_d)
        # Check object tree
        self.assertEqual(fish_item.rowCount(), 0)
        self.assertEqual(pluto_fish_dog_item.rowCount(), 0)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        obj_name_1 = model.index(1, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'pluto')
        self.assertEqual(obj_name_1, 'scooby')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        self.assertEqual(model.rowCount(), 1)

    def test_remove_relationship_classes(self):
        """Test that relationship classes are removed from all model/views."""
        self.add_mock_dataset()
        # Fetch object classes and objects, so we can test that relationship classes are removed from all objects
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        scooby_item = dog_item.child(1)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        scooby_index = self.tree_view_form.object_tree_model.indexFromItem(scooby_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        self.tree_view_form.object_tree_model.fetchMore(scooby_index)
        self.assertEqual(nemo_item.rowCount(), 2)
        self.assertEqual(nemo_item.rowCount(), 2)
        self.assertEqual(nemo_item.rowCount(), 2)
        # Select nemo's fish__dog relationship class item and call removal method
        nemo_fish_dog_item = nemo_item.child(0)
        db_map = self.tree_view_form.db_maps[0]
        item_d = {db_map: {'relationship_class': [nemo_fish_dog_item.data(Qt.UserRole + 1)[db_map]]}}
        self.tree_view_form.remove_tree_items(item_d)
        # Check object tree
        self.assertEqual(nemo_item.rowCount(), 1)
        self.assertEqual(nemo_item.rowCount(), 1)
        self.assertEqual(nemo_item.rowCount(), 1)
        nemo_dog_fish_item = nemo_item.child(0)
        pluto_dog_fish_item = pluto_item.child(0)
        scooby_dog_fish_item = scooby_item.child(0)
        nemo_dog_fish_type = nemo_dog_fish_item.data(Qt.UserRole)
        nemo_dog_fish_name = nemo_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        pluto_dog_fish_type = pluto_dog_fish_item.data(Qt.UserRole)
        pluto_dog_fish_name = pluto_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        scooby_dog_fish_type = scooby_dog_fish_item.data(Qt.UserRole)
        scooby_dog_fish_name = scooby_dog_fish_item.data(Qt.UserRole + 1)[db_map]['name']
        self.assertEqual(nemo_dog_fish_type, "relationship_class")
        self.assertEqual(nemo_dog_fish_name, "dog__fish")
        self.assertEqual(pluto_dog_fish_type, "relationship_class")
        self.assertEqual(pluto_dog_fish_name, "dog__fish")
        self.assertEqual(scooby_dog_fish_type, "relationship_class")
        self.assertEqual(scooby_dog_fish_name, "dog__fish")
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'dog__fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        rel_cls_name_0 = model.index(0, header_index("relationship_class_name")).data()
        self.assertEqual(rel_cls_name_0, 'dog__fish')
        self.assertEqual(model.rowCount(), 2)

    def test_remove_relationships(self):
        """Test that relationships are removed from all model/views."""
        self.add_mock_dataset()
        # Fetch nemo's and pluto's dog_fish relationship class,
        # to test that both intances of the relationship are removed.
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        dog_item = root_item.child(1)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        nemo_item = fish_item.child(0)
        pluto_item = dog_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_index)
        nemo_dog_fish_item = nemo_item.child(1)
        pluto_dog_fish_item = pluto_item.child(1)
        nemo_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_dog_fish_item)
        pluto_dog_fish_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_dog_fish_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_dog_fish_index)
        self.tree_view_form.object_tree_model.fetchMore(pluto_dog_fish_index)
        self.assertEqual(nemo_dog_fish_item.rowCount(), 1)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 1)
        # Select nemo's pluto__nemo relationship item and call removal method
        pluto_nemo_item = nemo_dog_fish_item.child(0)
        db_map = self.tree_view_form.db_maps[0]
        item_d = {db_map: {'relationship': [pluto_nemo_item.data(Qt.UserRole + 1)[db_map]]}}
        self.tree_view_form.remove_tree_items(item_d)
        # Check object tree
        self.assertEqual(nemo_dog_fish_item.rowCount(), 0)
        self.assertEqual(pluto_dog_fish_item.rowCount(), 0)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'nemo,scooby')
        self.assertEqual(model.rowCount(), 3)

    def test_update_object_parameter_definitions(self):
        """Test that object parameter definitions are updated using the table delegate."""
        # Update parameter name
        self.add_mock_dataset()
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "water")
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "water")
        editor.set_data("fire")
        x = namedtuple("foo", ["id"])(self.water_parameter.id)
        self.tree_view_form.db_maps[0].set_parameter_definition_tags.return_value = qry([]), []
        self.tree_view_form.db_maps[0].update_parameter_definitions.return_value = qry([x]), []
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        # Check object parameter definition table
        self.assertEqual(parameter_name_index.data(), 'fire')
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name_0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name_0, 'fire')

    def test_update_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are updated using the table delegate."""
        # Update parameter name
        self.add_mock_dataset()
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "relative_speed")
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_name_index)
        view.itemDelegate().setEditorData(editor, parameter_name_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.text(), "relative_speed")
        editor.set_data("equivalent_ki")
        x = namedtuple("foo", ["id"])(self.relative_speed_parameter.id)
        self.tree_view_form.db_maps[0].set_parameter_definition_tags.return_value = qry([]), []
        self.tree_view_form.db_maps[0].update_parameter_definitions.return_value = qry([x]), []
        view.itemDelegate().setModelData(editor, model, parameter_name_index)
        view.itemDelegate().destroyEditor(editor, parameter_name_index)
        # Check relationship parameter definition table
        self.assertEqual(parameter_name_index.data(), 'equivalent_ki')
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        parameter_name1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, 'equivalent_ki')
        self.assertEqual(parameter_name1, 'equivalent_ki')

    def test_update_object_parameter_values(self):
        """Test that object parameter values are updated using the table delegate."""
        # Update parameter value
        self.add_mock_dataset()
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_value_index = model.index(0, header_index("value"))
        self.assertEqual(parameter_value_index.data(), "salt")
        form = self.tree_view_form
        form.db_maps[0].parameter_definition_list.return_value.filter_by.return_value.one_or_none.return_value = None
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_value_index)
        view.itemDelegate().setEditorData(editor, parameter_value_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.data(), '"salt"')
        editor.set_data('"pepper"')
        x = namedtuple("foo", ["id"])(self.nemo_water.id)
        form.db_maps[0].update_parameter_values.return_value = qry([x]), []
        view.itemDelegate().setModelData(editor, model, parameter_value_index)
        view.itemDelegate().destroyEditor(editor, parameter_value_index)
        # Check object parameter value table
        self.assertEqual(parameter_value_index.data(), "pepper")

    @unittest.skip("TODO: Manuel")
    def test_update_relationship_parameter_values(self):
        """Test that relationship parameter values are updated using the table delegate."""
        self.add_mock_dataset()
        # Update parameter value
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_value_index = model.index(0, header_index("value"))
        self.assertEqual(parameter_value_index.data(), -1)
        form = self.tree_view_form
        form.db_maps[0].parameter_definition_list.return_value.filter_by.return_value.one_or_none.return_value = None
        editor = view.itemDelegate().createEditor(view, QStyleOptionViewItem(), parameter_value_index)
        view.itemDelegate().setEditorData(editor, parameter_value_index)
        self.assertTrue(isinstance(editor, CustomLineEditor), "Editor is not a 'CustomLineEditor'")
        self.assertEqual(editor.data(), "-1")
        editor.set_data("123")
        x = namedtuple("foo", ["id"])(self.relative_speed_parameter.id)
        form.db_maps[0].update_parameter_values.return_value = qry([x]), []
        view.itemDelegate().setModelData(editor, model, parameter_value_index)
        view.itemDelegate().destroyEditor(editor, parameter_value_index)
        # Check object parameter value table
        self.assertEqual(parameter_value_index.data(), 123)

    def test_remove_object_parameter_definitions(self):
        """Test that object parameter definitions are removed."""
        self.add_mock_dataset()
        # Select parameter definition and call removal method
        model = self.tree_view_form.object_parameter_definition_model
        view = self.tree_view_form.ui.tableView_object_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "water")
        self.tree_view_form.ui.tableView_object_parameter_definition.selectionModel().select(
            parameter_name_index, QItemSelectionModel.Select
        )
        self.tree_view_form.remove_object_parameter_definitions()
        # Check object parameter definition table
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "breed")
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name_0 = model.index(0, header_index("parameter_name")).data()
        parameter_name_1 = model.index(1, header_index("parameter_name")).data()
        self.assertEqual(parameter_name_0, 'breed')
        self.assertEqual(parameter_name_1, 'breed')
        self.assertEqual(model.rowCount(), 3)

    def test_remove_relationship_parameter_definitions(self):
        """Test that relationship parameter definitions are removed."""
        self.add_mock_dataset()
        # Select parameter definition and call removal method
        model = self.tree_view_form.relationship_parameter_definition_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_definition
        header_index = model.horizontal_header_labels().index
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "relative_speed")
        self.tree_view_form.ui.tableView_relationship_parameter_definition.selectionModel().select(
            parameter_name_index, QItemSelectionModel.Select
        )
        self.tree_view_form.remove_relationship_parameter_definitions()
        # Check relationship parameter definition table
        parameter_name_index = model.index(0, header_index("parameter_name"))
        self.assertEqual(parameter_name_index.data(), "combined_mojo")
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        parameter_name = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name, 'combined_mojo')
        self.assertEqual(model.rowCount(), 2)

    def test_remove_object_parameter_values(self):
        """Test that object parameter values are removed."""
        self.add_mock_dataset()
        # Select two parameter values and call removal method
        model = self.tree_view_form.object_parameter_value_model
        view = self.tree_view_form.ui.tableView_object_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_name0_index = model.index(0, header_index("parameter_name"))
        parameter_name2_index = model.index(2, header_index("parameter_name"))
        self.assertEqual(parameter_name0_index.data(), "water")
        self.assertEqual(parameter_name2_index.data(), "breed")
        self.tree_view_form.ui.tableView_object_parameter_value.selectionModel().select(
            parameter_name0_index, QItemSelectionModel.Select
        )
        self.tree_view_form.ui.tableView_object_parameter_value.selectionModel().select(
            parameter_name2_index, QItemSelectionModel.Select
        )
        self.tree_view_form.remove_object_parameter_values()
        # Check object parameter value table
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, "breed")
        self.assertEqual(model.rowCount(), 2)

    def test_remove_relationship_parameter_values(self):
        """Test that relationship parameter values are removed."""
        self.add_mock_dataset()
        # Select two parameter values and call removal method
        model = self.tree_view_form.relationship_parameter_value_model
        view = self.tree_view_form.ui.tableView_relationship_parameter_value
        header_index = model.horizontal_header_labels().index
        parameter_name0_index = model.index(0, header_index("parameter_name"))
        parameter_name2_index = model.index(2, header_index("parameter_name"))
        self.assertEqual(parameter_name0_index.data(), "relative_speed")
        self.assertEqual(parameter_name2_index.data(), "combined_mojo")
        self.tree_view_form.ui.tableView_relationship_parameter_value.selectionModel().select(
            parameter_name0_index, QItemSelectionModel.Select
        )
        self.tree_view_form.ui.tableView_relationship_parameter_value.selectionModel().select(
            parameter_name2_index, QItemSelectionModel.Select
        )
        self.tree_view_form.remove_relationship_parameter_values()
        # Check relationship parameter value table
        parameter_name0 = model.index(0, header_index("parameter_name")).data()
        self.assertEqual(parameter_name0, "relative_speed")
        self.assertEqual(model.rowCount(), 2)

    def test_filter_parameter_tables_per_object_class(self):
        """Test that parameter value and definition tables are filtered
        when selecting object classes in the object tree.
        """
        self.add_mock_dataset()
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        # Select fish object class in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(fish_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'dog,fish')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        obj_cls_name_lst_2 = model.index(2, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_2, 'dog,fish')
        self.assertEqual(model.rowCount(), 4)

    @unittest.skip("not working, need to check")
    def test_filter_parameter_tables_per_object(self):
        """Test that parameter value and definition tables are filtered
        when selecting objects in the object tree.
        """
        self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        dog_item = root_item.child(1)
        dog_index = self.tree_view_form.object_tree_model.indexFromItem(dog_item)
        self.tree_view_form.object_tree_model.fetchMore(dog_index)
        pluto_item = dog_item.child(0)
        pluto_index = self.tree_view_form.object_tree_model.indexFromItem(pluto_item)
        # Select pluto object in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(pluto_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'dog')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_0 = model.index(0, header_index("object_name")).data()
        self.assertEqual(obj_name_0, 'pluto')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        obj_cls_name_lst_1 = model.index(1, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(obj_cls_name_lst_1, 'dog,fish')
        self.assertEqual(model.rowCount(), 3)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'pluto,nemo')
        self.assertEqual(model.rowCount(), 3)

    def test_filter_parameter_tables_per_relationship_class(self):
        """Test that parameter value and definition tables are filtered
        when selecting relationship classes in the object tree.
        """
        self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        # Select nemo's fish__dog relationship class in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_fish_dog_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(obj_name_lst_1, 'nemo,scooby')
        self.assertEqual(model.rowCount(), 3)

    @unittest.skip("not working, need to check")
    def test_filter_parameter_tables_per_relationship(self):
        """Test that parameter value and definition tables are filtered
        when selecting relationships in the object tree.
        """
        self.add_mock_dataset()
        # Fetch object tree
        root_item = self.tree_view_form.object_tree_model.root_item
        fish_item = root_item.child(0)
        fish_index = self.tree_view_form.object_tree_model.indexFromItem(fish_item)
        self.tree_view_form.object_tree_model.fetchMore(fish_index)
        nemo_item = fish_item.child(0)
        nemo_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_index)
        nemo_fish_dog_item = nemo_item.child(0)
        nemo_fish_dog_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_fish_dog_item)
        self.tree_view_form.object_tree_model.fetchMore(nemo_fish_dog_index)
        nemo_pluto_item = nemo_fish_dog_item.child(0)
        nemo_pluto_index = self.tree_view_form.object_tree_model.indexFromItem(nemo_pluto_item)
        # Select nemo__pluto relationship in object tree
        self.tree_view_form.ui.treeView_object.selectionModel().select(nemo_pluto_index, QItemSelectionModel.Select)
        # Check object parameter definition table
        model = self.tree_view_form.object_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check object parameter value table
        model = self.tree_view_form.object_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_0 = model.index(0, header_index("object_class_name")).data()
        self.assertEqual(obj_cls_name_0, 'fish')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter definition table
        model = self.tree_view_form.relationship_parameter_definition_model
        header_index = model.horizontal_header_labels().index
        obj_cls_name_lst_0 = model.index(0, header_index("object_class_name_list")).data()
        self.assertEqual(obj_cls_name_lst_0, 'fish,dog')
        self.assertEqual(model.rowCount(), 2)
        # Check relationship parameter value table
        model = self.tree_view_form.relationship_parameter_value_model
        header_index = model.horizontal_header_labels().index
        obj_name_lst_0 = model.index(0, header_index("object_name_list")).data()
        obj_name_lst_1 = model.index(1, header_index("object_name_list")).data()
        self.assertEqual(obj_name_lst_0, 'nemo,pluto')
        self.assertEqual(model.rowCount(), 2)

    def add_mock_object_classes(self):
        """Add fish and dog object classes."""
        self.fish_class = self.ObjectClass(1, "fish", "A fish.", 1, None)
        self.dog_class = self.ObjectClass(2, "dog", "A dog.", 3, None)
        self.tree_view_form.db_maps[0].object_class_list.return_value = qry([self.fish_class, self.dog_class])

    def add_mock_objects(self):
        """Add nemo, pluto and scooby objects."""
        fish_class_id, dog_class_id = self.fish_class.id, self.dog_class.id
        self.nemo_object = self.Object(1, fish_class_id, 'nemo', 'The lost one.')
        self.pluto_object = self.Object(2, dog_class_id, 'pluto', "Mickey's.")
        self.scooby_object = self.Object(3, dog_class_id, 'scooby', 'Scooby-Dooby-Doo.')

        def side_effect(class_id=None):
            if class_id == fish_class_id:
                return qry([self.nemo_object])
            elif class_id == dog_class_id:
                return qry([self.pluto_object, self.scooby_object])
            elif class_id is None:
                return qry([self.nemo_object, self.pluto_object, self.scooby_object])
            else:
                return qry()

        self.tree_view_form.db_maps[0].object_list.side_effect = side_effect

    def add_mock_relationship_classes(self):
        """Add dog__fish and fish__dog relationship classes."""
        fish_class_id, dog_class_id = self.fish_class.id, self.dog_class.id
        self.fish_dog_class = self.RelationshipClass(
            1, "fish__dog", str(fish_class_id) + "," + str(dog_class_id), "fish,dog"
        )
        self.dog_fish_class = self.RelationshipClass(
            2, "dog__fish", str(dog_class_id) + "," + str(fish_class_id), "dog,fish"
        )

        def side_effect(object_class_id=None):
            if object_class_id in (fish_class_id, dog_class_id):
                return qry([self.fish_dog_class, self.dog_fish_class])
            elif object_class_id is None:
                return qry([self.fish_dog_class, self.dog_fish_class])
            else:
                return qry()

        self.tree_view_form.db_maps[0].wide_relationship_class_list.side_effect = side_effect

    def add_mock_relationships(self):
        """Add pluto_nemo, nemo_pluto and nemo_scooby relationships."""
        fish_dog_class_id = self.fish_dog_class.id
        dog_fish_class_id = self.dog_fish_class.id
        pluto_object_id = self.pluto_object.id
        nemo_object_id = self.nemo_object.id
        scooby_object_id = self.scooby_object.id
        self.pluto_nemo_rel = self.Relationship(
            1,
            dog_fish_class_id,
            "dog__fish_pluto__nemo",
            str(pluto_object_id) + "," + str(nemo_object_id),
            "pluto,nemo",
        )
        self.nemo_pluto_rel = self.Relationship(
            2,
            fish_dog_class_id,
            "fish__dog_nemo__pluto",
            str(nemo_object_id) + "," + str(pluto_object_id),
            "nemo,pluto",
        )
        self.nemo_scooby_rel = self.Relationship(
            3,
            fish_dog_class_id,
            "fish__dog_nemo__scooby",
            str(nemo_object_id) + "," + str(scooby_object_id),
            "nemo,scooby",
        )

        def side_effect(class_id=None, object_id=None):
            if class_id == dog_fish_class_id:
                if object_id in (nemo_object_id, pluto_object_id):
                    return qry([self.pluto_nemo_rel])
                else:
                    return qry()
            elif class_id == fish_dog_class_id:
                if object_id == nemo_object_id:
                    return qry([self.nemo_pluto_rel, self.nemo_scooby_rel])
                elif object_id == pluto_object_id:
                    return qry([self.nemo_pluto_rel])
                elif object_id == scooby_object_id:
                    return qry([self.nemo_scooby_rel])
                else:
                    return qry()
            elif class_id is None and object_id is None:
                return qry([self.pluto_nemo_rel, self.nemo_pluto_rel, self.nemo_scooby_rel])
            else:
                return qry()

        self.tree_view_form.db_maps[0].wide_relationship_list.side_effect = side_effect

    def add_mock_object_parameter_definitions(self):
        """Add water and breed object parameter definitions."""
        fish_class_id = self.fish_class.id
        dog_class_id = self.dog_class.id
        self.water_parameter = self.ObjectParameter(1, fish_class_id, "fish", "water", None, None, None, None, None)
        self.breed_parameter = self.ObjectParameter(2, dog_class_id, "dog", "breed", None, None, None, None, None)

        def side_effect(object_class_id=None):
            if object_class_id == fish_class_id:
                return qry([self.water_parameter])
            elif object_class_id == dog_class_id:
                return qry([self.breed_parameter])
            elif object_class_id is None:
                return qry([self.water_parameter, self.breed_parameter])
            else:
                return qry()

        self.tree_view_form.db_maps[0].object_parameter_definition_list.side_effect = side_effect

    def add_mock_relationship_parameter_definitions(self):
        """Add relative speed and combined mojo relationship parameter definitions."""
        fish_class_id = self.fish_class.id
        dog_class_id = self.dog_class.id
        fish_dog_class_id = self.fish_dog_class.id
        dog_fish_class_id = self.dog_fish_class.id
        self.relative_speed_parameter = self.RelationshipParameter(
            1,
            fish_dog_class_id,
            "fish__dog",
            str(fish_class_id) + "," + str(dog_class_id),
            "fish,dog",
            "relative_speed",
            None,
            None,
            None,
            None,
            None,
        )
        self.combined_mojo_parameter = self.RelationshipParameter(
            2,
            dog_fish_class_id,
            "dog__fish",
            str(dog_class_id) + "," + str(fish_class_id),
            "dog,fish",
            "combined_mojo",
            None,
            None,
            None,
            None,
            None,
        )

        def side_effect(relationship_class_id=None):
            if relationship_class_id == fish_dog_class_id:
                return qry([self.relative_speed_parameter])
            elif relationship_class_id == dog_fish_class_id:
                return qry([self.combined_mojo_parameter])
            elif relationship_class_id is None:
                return qry([self.relative_speed_parameter, self.combined_mojo_parameter])
            else:
                return qry()

        self.tree_view_form.db_maps[0].relationship_parameter_definition_list.side_effect = side_effect

    def add_mock_object_parameter_values(self):
        """Add some object parameter values."""
        fish_class_id = self.fish_class.id
        dog_class_id = self.dog_class.id
        nemo_object_id = self.nemo_object.id
        pluto_object_id = self.pluto_object.id
        scooby_object_id = self.scooby_object.id
        water_parameter_id = self.water_parameter.id
        breed_parameter_id = self.breed_parameter.id
        self.nemo_water = self.ObjectParameterValue(
            1, fish_class_id, "fish", nemo_object_id, "nemo", water_parameter_id, "water", '"salt"'
        )
        self.pluto_breed = self.ObjectParameterValue(
            2, dog_class_id, "dog", pluto_object_id, 'pluto', breed_parameter_id, "breed", '"bloodhound"'
        )
        self.scooby_breed = self.ObjectParameterValue(
            3, dog_class_id, "dog", scooby_object_id, "scooby", breed_parameter_id, "breed", '"great dane"'
        )

        def side_effect():
            return qry([self.nemo_water, self.pluto_breed, self.scooby_breed])

        self.tree_view_form.db_maps[0].object_parameter_value_list.side_effect = side_effect

    def add_mock_relationship_parameter_values(self):
        """Add some relationship parameter values."""
        fish_class_id = self.fish_class.id
        dog_class_id = self.dog_class.id
        nemo_object_id = self.nemo_object.id
        pluto_object_id = self.pluto_object.id
        scooby_object_id = self.scooby_object.id
        fish_dog_class_id = self.fish_dog_class.id
        dog_fish_class_id = self.dog_fish_class.id
        nemo_pluto_rel_id = self.nemo_pluto_rel.id
        nemo_scooby_rel_id = self.nemo_scooby_rel.id
        pluto_nemo_rel_id = self.pluto_nemo_rel.id
        relative_speed_parameter_id = self.relative_speed_parameter.id
        combined_mojo_parameter_id = self.combined_mojo_parameter.id
        self.nemo_pluto_relative_speed = self.RelationshipParameterValue(
            1,
            fish_dog_class_id,
            "fish__dog",
            str(fish_class_id) + "," + str(dog_class_id),
            "fish,dog",
            nemo_pluto_rel_id,
            str(nemo_object_id) + "," + str(pluto_object_id),
            "nemo,pluto",
            relative_speed_parameter_id,
            "relative_speed",
            "-1",
        )
        self.nemo_scooby_relative_speed = self.RelationshipParameterValue(
            2,
            fish_dog_class_id,
            "fish__dog",
            str(fish_class_id) + "," + str(dog_class_id),
            "fish,dog",
            nemo_scooby_rel_id,
            str(nemo_object_id) + "," + str(scooby_object_id),
            "nemo,scooby",
            relative_speed_parameter_id,
            "relative_speed",
            "5",
        )
        self.pluto_nemo_combined_mojo = self.RelationshipParameterValue(
            3,
            dog_fish_class_id,
            "dog__fish",
            str(dog_class_id) + "," + str(fish_class_id),
            "dog,fish",
            pluto_nemo_rel_id,
            str(pluto_object_id) + "," + str(nemo_object_id),
            "pluto,nemo",
            combined_mojo_parameter_id,
            "combined_mojo",
            "100",
        )

        def side_effect():
            return qry([self.nemo_pluto_relative_speed, self.nemo_scooby_relative_speed, self.pluto_nemo_combined_mojo])

        self.tree_view_form.db_maps[0].relationship_parameter_value_list.side_effect = side_effect

    def add_mock_dataset(self):
        """Add mock dataset."""
        self.add_mock_object_classes()
        self.add_mock_objects()
        self.add_mock_relationship_classes()
        self.add_mock_relationships()
        self.add_mock_object_parameter_definitions()
        self.add_mock_relationship_parameter_definitions()
        self.add_mock_object_parameter_values()
        self.add_mock_relationship_parameter_values()
        self.tree_view_form.init_models()


if __name__ == '__main__':
    unittest.main()
