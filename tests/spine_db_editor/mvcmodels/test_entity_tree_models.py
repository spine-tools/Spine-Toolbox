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
from spinedb_api import DatabaseMapping
from spinetoolbox.spine_db_editor.mvcmodels.entity_tree_models import EntityTreeModel


class TestEntityTreeModel:
    def test_superclass_name_displayed_after_subclass_name(self, parent_object, app_settings, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="Object")
            db_map.add_entity_class(name="Any")
            db_map.add_superclass_subclass(superclass_name="Any", subclass_name="Object")
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 2:
            QApplication.processEvents()
        assert [child.display_data for child in model.root_item.children] == ["Any", "Object (Any)"]

    def test_entity_items_advertise_they_have_children(self, parent_object, app_settings, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="A")
            db_map.add_entity(entity_class_name="A", name="a")
            db_map.add_entity_class(name="B")
            db_map.add_entity(entity_class_name="B", name="b")
            db_map.add_entity_class(dimension_name_list=["A", "B"])
            db_map.add_entity(entity_class_name="A__B", entity_byname=["a", "b"])
            db_map.add_entity_class(dimension_name_list=["A__B", "A__B"])
            db_map.add_entity(entity_class_name="A__B__A__B", entity_byname=["a", "b", "a", "b"])
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
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

    def test_same_class_in_two_databases_but_one_has_superclass(
        self, parent_object, app_settings, db_mngr, logger, tmp_path
    ):
        url = "sqlite:///" + str(tmp_path / "db.sqlite")
        with DatabaseMapping(url, create=True) as db_map:
            db_map.add_entity_class(name="A")
            db_map.commit_session("Add entity class.")
        url_with_superclass = "sqlite:///" + str(tmp_path / "db_with_superclass.sqlite")
        with DatabaseMapping(url_with_superclass, create=True) as db_map:
            db_map.add_entity_class(name="A")
            db_map.add_entity_class(name="Superclass")
            db_map.add_superclass_subclass(superclass_name="Superclass", subclass_name="A")
            db_map.commit_session("Add entity class and superclass.")
        model = EntityTreeModel(
            parent_object,
            app_settings,
            db_mngr,
            db_mngr.get_db_map(url, logger),
            db_mngr.get_db_map(url_with_superclass, logger),
        )
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 3:
            QApplication.processEvents()
        assert [child.display_data for child in model.root_item.children] == ["A", "A (Superclass)", "Superclass"]

    @staticmethod
    def _built_model_with_entities(parent_object, app_settings, db_mngr, db_map):
        """Builds a fully fetched entity tree with three classes each holding one entity.

        Each class is fetched until ``can_fetch_more()`` is False so it counts as fully loaded (a class with
        no matching entity is only hidden once nothing is left to fetch).

        Returns:
            EntityTreeModel: a model whose classes and entities are fully fetched
        """
        with db_map:
            db_map.add_entity_class(name="Apple")
            db_map.add_entity(entity_class_name="Apple", name="golden")
            db_map.add_entity_class(name="Apricot")
            db_map.add_entity(entity_class_name="Apricot", name="blenheim")
            db_map.add_entity_class(name="Banana")
            db_map.add_entity(entity_class_name="Banana", name="cavendish")
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 3:
            QApplication.processEvents()
        for class_item in model.root_item.children:
            while class_item.can_fetch_more():
                class_item.fetch_more()
                QApplication.processEvents()
        return model

    def test_class_level_filter_hides_non_matching_classes(self, parent_object, app_settings, db_mngr, db_map):
        model = self._built_model_with_entities(parent_object, app_settings, db_mngr, db_map)
        assert model.root_item.row_count() == 3
        model.set_level_filter("entity_class", "^Ap")
        model._apply_level_filters()
        visible = [c.name for c in model.root_item.visible_children]
        assert visible == ["Apple", "Apricot"]

    def test_entity_level_filter_hides_entities_and_fully_loaded_empty_classes(
        self, parent_object, app_settings, db_mngr, db_map
    ):
        model = self._built_model_with_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity", "golden")
        model._apply_level_filters()
        visible_classes = [c.name for c in model.root_item.visible_children]
        # Every class is fully fetched, so only Apple (its lone entity matches) survives.
        assert visible_classes == ["Apple"]
        apple = next(c for c in model.root_item.children if c.name == "Apple")
        assert [e.name for e in apple.visible_children] == ["golden"]

    def test_entity_level_filter_keeps_unfetched_class_visible_then_refines(
        self, parent_object, app_settings, db_mngr, db_map
    ):
        with db_map:
            db_map.add_entity_class(name="Apple")
            db_map.add_entity(entity_class_name="Apple", name="golden")
            db_map.add_entity_class(name="Banana")
            db_map.add_entity(entity_class_name="Banana", name="cavendish")
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 2:
            QApplication.processEvents()
        # Entities are not fetched yet; both classes can still fetch more.
        assert all(c.can_fetch_more() for c in model.root_item.children)
        model.set_level_filter("entity", "golden")
        model._apply_level_filters()
        # Optimistic: an unfetched class stays visible even though no matching entity is loaded yet.
        assert [c.name for c in model.root_item.visible_children] == ["Apple", "Banana"]
        # Fully fetch every class's entities, then re-apply so the tree refines.
        for class_item in model.root_item.children:
            while class_item.can_fetch_more():
                class_item.fetch_more()
                QApplication.processEvents()
        model._apply_level_filters()
        # Now fully loaded: Banana has no matching entity and nothing left to fetch, so it is hidden.
        assert [c.name for c in model.root_item.visible_children] == ["Apple"]

    def test_level_filter_is_case_insensitive(self, parent_object, app_settings, db_mngr, db_map):
        model = self._built_model_with_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity_class", "APPLE")
        model._apply_level_filters()
        assert [c.name for c in model.root_item.visible_children] == ["Apple"]

    def test_invalid_regex_falls_back_to_substring(self, parent_object, app_settings, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="plain")
            db_map.add_entity_class(name="a(b")
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 2:
            QApplication.processEvents()
        # "a(b" is an invalid regex; it must fall back to a case-insensitive substring match rather than error.
        model.set_level_filter("entity_class", "a(b")
        model._apply_level_filters()
        assert [c.name for c in model.root_item.visible_children] == ["a(b"]

    def test_clear_level_filters_restores_tree(self, parent_object, app_settings, db_mngr, db_map):
        model = self._built_model_with_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity_class", "Apple")
        model._apply_level_filters()
        assert model.root_item.row_count() == 1
        model.clear_level_filters()
        model._apply_level_filters()
        assert [c.name for c in model.root_item.visible_children] == ["Apple", "Apricot", "Banana"]


class TestEntityLowerLevelAutoFetch:
    """A lower-level (entity) filter must force-fetch across collapsed/unfetched classes on its own."""

    @staticmethod
    def _model_without_fetched_entities(parent_object, app_settings, db_mngr, db_map):
        """Builds a tree whose classes are loaded but whose entities are deliberately NOT fetched.

        Returns:
            EntityTreeModel: a model with three classes, each with one still-unfetched entity
        """
        with db_map:
            db_map.add_entity_class(name="Apple")
            db_map.add_entity(entity_class_name="Apple", name="golden")
            db_map.add_entity_class(name="Apricot")
            db_map.add_entity(entity_class_name="Apricot", name="blenheim")
            db_map.add_entity_class(name="Banana")
            db_map.add_entity(entity_class_name="Banana", name="cavendish")
        model = EntityTreeModel(parent_object, app_settings, db_mngr, db_map)
        model.build_tree()
        model.root_item.fetch_more()
        while len(model.root_item.children) != 3:
            QApplication.processEvents()
        # Entities are deliberately not fetched: every class can still fetch more.
        assert all(c.can_fetch_more() for c in model.root_item.children)
        return model

    @staticmethod
    def _drive_force_fetch(model):
        """Runs the force-fetch cascade to completion, pumping the event loop between batches."""
        for _ in range(500):
            model._run_force_fetch()
            if not model._force_fetching:
                break
            QApplication.processEvents()
        model._apply_level_filters()

    def test_entity_filter_reveals_matches_without_manual_expansion(self, parent_object, app_settings, db_mngr, db_map):
        model = self._model_without_fetched_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity", "golden")
        # No class was expanded or fetched by hand; the force-fetch alone must resolve the filter.
        self._drive_force_fetch(model)
        assert [c.name for c in model.root_item.visible_children] == ["Apple"]
        apple = next(c for c in model.root_item.children if c.name == "Apple")
        assert [e.name for e in apple.visible_children] == ["golden"]

    def test_class_regex_narrows_which_classes_get_force_fetched(self, parent_object, app_settings, db_mngr, db_map):
        model = self._model_without_fetched_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity_class", "^Ap")
        model.set_level_filter("entity", "n")
        self._drive_force_fetch(model)
        banana = next(c for c in model.root_item.children if c.name == "Banana")
        # Banana fails the class regex, so the force-fetch never touched its entities.
        assert banana.can_fetch_more()
        apple = next(c for c in model.root_item.children if c.name == "Apple")
        assert not apple.can_fetch_more()
        assert [c.name for c in model.root_item.visible_children] == ["Apple", "Apricot"]

    def test_no_match_hides_every_class_after_force_fetch(self, parent_object, app_settings, db_mngr, db_map):
        model = self._model_without_fetched_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity", "does-not-exist")
        self._drive_force_fetch(model)
        assert model.root_item.visible_children == []
        assert model.has_visible_match() is False

    def test_clearing_lower_filter_restores_full_tree(self, parent_object, app_settings, db_mngr, db_map):
        model = self._model_without_fetched_entities(parent_object, app_settings, db_mngr, db_map)
        model.set_level_filter("entity", "golden")
        self._drive_force_fetch(model)
        assert [c.name for c in model.root_item.visible_children] == ["Apple"]
        model.clear_level_filters()
        model._apply_level_filters()
        assert [c.name for c in model.root_item.visible_children] == ["Apple", "Apricot", "Banana"]
