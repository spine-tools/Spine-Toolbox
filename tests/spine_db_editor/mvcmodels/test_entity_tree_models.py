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
from PySide6.QtWidgets import QApplication
from spinetoolbox.spine_db_editor.mvcmodels.entity_tree_models import EntityTreeModel


class TestEntityTreeModel:
    def test_superclass_name_displayed_after_subclass_name(self, db_editor, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="Object")
            db_map.add_entity_class(name="Any")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="Object")
        model = EntityTreeModel(db_editor, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 2:
            QApplication.processEvents()
        assert [child.display_data for child in model.root_item.children] == ["Any", "Object (Any)"]

    def test_entity_items_advertise_they_have_children(self, db_editor, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="A")
            db_map.add_entity(entity_class_name="A", name="a")
            db_map.add_entity_class(name="B")
            db_map.add_entity(entity_class_name="B", name="b")
            db_map.add_entity_class(dimension_name_list=["A", "B"])
            db_map.add_entity(entity_class_name="A__B", entity_byname=["a", "b"])
            db_map.add_entity_class(dimension_name_list=["A__B", "A__B"])
            db_map.add_entity(entity_class_name="A__B__A__B", entity_byname=["a", "b", "a", "b"])
        model = EntityTreeModel(db_editor, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 4:
            QApplication.processEvents()
        assert [child.display_data for child in model.root_item.children] == ["A", "B", "A__B", "A__B__A__B"]
        assert all(child.has_children() for child in model.root_item.children)
        class_a = model.root_item.children[0]
        class_a.fetch_more()
        while len(class_a.children) != 1:
            QApplication.processEvents()
        assert [entity_item.display_data for entity_item in class_a.children] == ["a"]
        assert all(entity_item.has_children() for entity_item in class_a.children)
        entity_a = class_a.children[0]
        entity_a.fetch_more()
        while len(entity_a.children) != 1:
            QApplication.processEvents()
        assert [entity_item.display_data for entity_item in entity_a.children] == ["٭ ǀ b"]
        assert all(entity_item.has_children() for entity_item in entity_a.children)
        relationship_a_b = entity_a.children[0]
        relationship_a_b.fetch_more()
        while len(relationship_a_b.children) != 1:
            QApplication.processEvents()
        assert [relationship.display_data for relationship in relationship_a_b.children] == ["٭ ǀ ٭ ǀ ٭ ǀ ٭"]
        assert all(not relationship.has_children() for relationship in relationship_a_b.children)
