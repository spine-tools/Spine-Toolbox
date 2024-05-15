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
from unittest import mock
from PySide6.QtCore import Qt, QItemSelectionModel
from PySide6.QtTest import QTest
from spinetoolbox.spine_db_editor.graphics_items import EntityItem
from spinetoolbox.helpers import DB_ITEM_SEPARATOR
from .spine_db_editor_test_base import DBEditorTestBase


class TestSpineDBEditorStackedFilter(DBEditorTestBase):
    """Tests for filtering in stacked tables."""

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


class TestSpineDBEditorGraphFilter(DBEditorTestBase):
    """Tests for the filtering in the graph view."""

    def setUp(self):
        super().setUp()
        self.visible_items = []
        self._add_test_data()
        self.spine_db_editor._layout_gen_id = 0
        self.spine_db_editor.apply_graph_style()
        self.gv = self.spine_db_editor.ui.graphicsView
        self.gv.set_property("max_entity_dimension_count", 12)

    def tearDown(self):
        self.clear_selection_models()
        super().tearDown()

    def _add_test_data(self):
        data = {
            "entity_classes": [
                ["A", [], None, None, False],
                ["B", [], None, None, True],
                ["C", [], None, None, False],
                ["A__B", ["A", "B"], None, None, True],
            ],
            "entities": [
                ["A", "aa", None],
                ["A", "ab", None],
                ["B", "ba", None],
                ["B", "bb", None],
                ["C", "ca", None],
                ["C", "cb", None],
                ["A__B", ["aa", "ba"], None],
                ["A__B", ["aa", "bb"], None],
                ["A__B", ["ab", "ba"], None],
                ["A__B", ["ab", "bb"], None],
            ],
            "entity_alternatives": [
                ["A", ["aa"], "Alt1", False],
                ["A", ["aa"], "Alt2", True],
                ["A", ["ab"], "Alt1", True],
                ["B", ["bb"], "Alt2", False],
                ["C", ["ca"], "Alt3", True],
                ["C", ["cb"], "Alt3", True],
            ],
            "alternatives": [["Alt1", ""], ["Alt2", ""], ["Alt3", ""]],
            "scenarios": [["scen1", False, ""], ["scen2", False, ""]],
            "scenario_alternatives": [["scen1", "Alt2", "Alt1"], ["scen1", "Alt1", None], ["scen2", "Alt3", None]],
        }
        sanitized_data = {}
        for item_type, items in data.items():
            sanitized_items = tuple(tuple(x if not isinstance(x, list) else tuple(x) for x in item) for item in items)
            sanitized_data[item_type] = sanitized_items
        self.spine_db_editor.import_data(sanitized_data)

    def _refresh_graph(self):
        self.visible_items_before = self.spine_db_editor.scene.items()
        self.spine_db_editor._update_graph_data()
        self.gv.clear_cross_hairs_items()
        coords = list(range(10))  # Based on amount of entities in the data
        self.spine_db_editor._complete_graph(0, coords, coords)
        self.spine_db_editor._graph_fetch_more_later()
        self.visible_items = self.spine_db_editor.scene.items()

    def clear_selection_models(self):
        for model in (
            self.spine_db_editor.ui.treeView_entity.selectionModel(),
            self.spine_db_editor.ui.alternative_tree_view.selectionModel(),
            self.spine_db_editor.ui.scenario_tree_view.selectionModel(),
        ):
            model.clearSelection()
        self._refresh_graph()
        entities = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
        self.assertEqual(set(), entities)

    @staticmethod
    def select_item_with_index(tree_view, index, extend=False):
        """Select an item form a specified tree view. Possible extended selection"""
        modifier = Qt.KeyboardModifier.NoModifier
        if extend:
            modifier = Qt.KeyboardModifier.ControlModifier
        rect = tree_view.visualRect(index)
        pos = rect.center()
        QTest.mouseClick(
            tree_view.viewport(),
            Qt.LeftButton,
            modifier,
            pos,
        )

    def test_filtering_with_entity_selections(self):
        """Tests that the graph view filters the entities correctly based on the Entity Tree selection"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse([item.name for item in self.visible_items if isinstance(item, EntityItem)])
            # Select the root item, every entity should be visible
            root_item = self.spine_db_editor.entity_tree_model.root_item
            root_index = self.spine_db_editor.entity_tree_model.index_from_item(root_item)
            self.select_item_with_index(entity_tree_view, root_index)
            entity_tree_view.fully_expand()
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa__ba", "ab__ba", "ab", "aa", "ba", "ab__bb", "bb", "aa__bb", "ca", "cb"}, visible)
            # Select the entity class A
            A_item = root_item.child(0)
            A_index = self.spine_db_editor.entity_tree_model.index_from_item(A_item)
            self.select_item_with_index(entity_tree_view, A_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ab", "aa"}, visible)
            # Extend selection with entity class B
            B_item = root_item.child(2)
            B_index = self.spine_db_editor.entity_tree_model.index_from_item(B_item)
            self.select_item_with_index(entity_tree_view, B_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa__ba", "ab__ba", "ab", "aa", "ba", "ab__bb", "bb", "aa__bb"}, visible)

    def test_filtering_with_alternative_selections(self):
        """Tests that the graph view filters the entities correctly based on the Alternative and Scenario -tree
        selections"""
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        scenario_tree_view = self.spine_db_editor.ui.scenario_tree_view
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Selecting the root shouldn't do anything
            alt_root_index = self.spine_db_editor.alternative_model.index(0, 0)
            alt_root_item = self.spine_db_editor.alternative_model.item_from_index(alt_root_index)
            self.select_item_with_index(alternative_tree_view, alt_root_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual(set(), visible)
            # Selecting Alt1 and Alt2
            alt1_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[1])
            alt2_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[2])
            alt3_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[3])
            self.select_item_with_index(alternative_tree_view, alt1_index)
            self.select_item_with_index(alternative_tree_view, alt3_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ab", "ca", "cb"}, visible)
            # Selecting Alt2 and scen2
            self.select_item_with_index(alternative_tree_view, alt2_index)
            scen_root_index = self.spine_db_editor.scenario_model.index(0, 0)
            scen_root_item = self.spine_db_editor.scenario_model.item_from_index(scen_root_index)
            scen2_index = self.spine_db_editor.scenario_model.index_from_item(scen_root_item.children[1])
            self.select_item_with_index(scenario_tree_view, scen2_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa", "ca", "cb"}, visible)
            # Clicking on empty area should clear all selections and nothing should show
            empty_index = self.spine_db_editor.scenario_model.index(-1, -1)
            self.select_item_with_index(scenario_tree_view, empty_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual(set(), visible)

    def test_filtering_with_entity_and_alternative_selections(self):
        """Tests that the graph view filters the entities correctly based on the Entity, Alternative and Scenario -tree
        selections"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select entity classes A and B along with alternative Alt1.
            # Since class B active_by_default is True, Alt1 has no entity alternatives
            # for the class, the alternative selection shouldn't filter out anything.
            entity_root_item = self.spine_db_editor.entity_tree_model.root_item
            A_item = entity_root_item.child(0)
            A_index = self.spine_db_editor.entity_tree_model.index_from_item(A_item)
            B_item = entity_root_item.child(2)
            B_index = self.spine_db_editor.entity_tree_model.index_from_item(B_item)
            alt_root_index = self.spine_db_editor.alternative_model.index(0, 0)
            alt_root_item = self.spine_db_editor.alternative_model.item_from_index(alt_root_index)
            alt1_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[1])
            self.select_item_with_index(entity_tree_view, A_index)
            self.select_item_with_index(entity_tree_view, B_index, extend=True)
            self.select_item_with_index(alternative_tree_view, alt1_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa__ba", "ab__ba", "ab", "aa", "ba", "ab__bb", "bb", "aa__bb"}, visible)
            # Selecting class B with Alt2 should filter out one of the entities in B
            alt2_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[2])
            self.select_item_with_index(entity_tree_view, B_index)
            self.select_item_with_index(alternative_tree_view, alt2_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ba"}, visible)

    def test_filtering_with_entity_selections_with_auto_expand(self):
        """Tests that the graph view filters the entities correctly based on the Entity Tree selections when
        auto-expand is enabled"""
        self.gv.set_property("auto_expand_entities", True)
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse([item.name for item in self.visible_items if isinstance(item, EntityItem)])
            # Select the root item, every entity should be visible
            root_item = self.spine_db_editor.entity_tree_model.root_item
            root_index = self.spine_db_editor.entity_tree_model.index_from_item(root_item)
            self.select_item_with_index(entity_tree_view, root_index)
            entity_tree_view.fully_expand()
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa__ba", "ab__ba", "ab", "aa", "ba", "ab__bb", "bb", "aa__bb", "ca", "cb"}, visible)
            # Select the entity class A
            A_item = root_item.child(0)
            A_index = self.spine_db_editor.entity_tree_model.index_from_item(A_item)
            self.select_item_with_index(entity_tree_view, A_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ab", "aa", "ba", "bb", "aa__ba", "ab__ba", "ab__bb", "aa__bb"}, visible)
            # Extend selection with entity class B, should do nothing to the graph
            B_item = root_item.child(2)
            B_index = self.spine_db_editor.entity_tree_model.index_from_item(B_item)
            self.select_item_with_index(entity_tree_view, B_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa__ba", "ab__ba", "ab", "aa", "ba", "ab__bb", "bb", "aa__bb"}, visible)

    def test_filtering_with_alternative_selections_with_auto_expand(self):
        """Tests that the graph view filters the entities correctly based on the Alternative and Scenario -tree
        selections when auto-expand is enabled"""
        self.gv.set_property("auto_expand_entities", True)
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        scenario_tree_view = self.spine_db_editor.ui.scenario_tree_view
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Selecting the root shouldn't do anything
            alt_root_index = self.spine_db_editor.alternative_model.index(0, 0)
            alt_root_item = self.spine_db_editor.alternative_model.item_from_index(alt_root_index)
            self.select_item_with_index(alternative_tree_view, alt_root_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual(set(), visible)
            # Selecting Alt1
            alt1_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[1])
            alt2_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[2])
            self.select_item_with_index(alternative_tree_view, alt1_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ab", "ba", "bb", "ab__ba", "ab__bb"}, visible)
            # Selecting Alt2 and scen2
            self.select_item_with_index(alternative_tree_view, alt2_index)
            scen_root_index = self.spine_db_editor.scenario_model.index(0, 0)
            scen_root_item = self.spine_db_editor.scenario_model.item_from_index(scen_root_index)
            scen2_index = self.spine_db_editor.scenario_model.index_from_item(scen_root_item.children[1])
            self.select_item_with_index(scenario_tree_view, scen2_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa", "ca", "cb", "ba", "bb", "aa__ba", "aa__bb"}, visible)
            # Clicking on empty area should clear all selections and nothing should show
            empty_index = self.spine_db_editor.scenario_model.index(-1, -1)
            self.select_item_with_index(scenario_tree_view, empty_index)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual(set(), visible)

    def test_filtering_with_entity_and_alternative_selections_with_auto_expand(self):
        """Tests that the graph view filters the entities correctly based on the Entity, Alternative and Scenario -tree
        selections when auto-expand is enabled"""
        self.gv.set_property("auto_expand_entities", True)
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with mock.patch.object(
            self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True
        ), mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value:
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select entity classes A along with alternative Alt1.
            entity_root_item = self.spine_db_editor.entity_tree_model.root_item
            A_item = entity_root_item.child(0)
            A_index = self.spine_db_editor.entity_tree_model.index_from_item(A_item)
            alt_root_index = self.spine_db_editor.alternative_model.index(0, 0)
            alt_root_item = self.spine_db_editor.alternative_model.item_from_index(alt_root_index)
            alt1_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[1])
            self.select_item_with_index(entity_tree_view, A_index)
            self.select_item_with_index(alternative_tree_view, alt1_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"ab__ba", "ab", "ba", "ab__bb", "bb"}, visible)
            # Selecting class B with Alt2
            alt2_index = self.spine_db_editor.alternative_model.index_from_item(alt_root_item.children[2])
            B_item = entity_root_item.child(2)
            B_index = self.spine_db_editor.entity_tree_model.index_from_item(B_item)
            self.select_item_with_index(entity_tree_view, B_index)
            self.select_item_with_index(alternative_tree_view, alt2_index, extend=True)
            self._refresh_graph()
            visible = {item.name for item in self.visible_items if isinstance(item, EntityItem)}
            self.assertEqual({"aa", "ba", "ab", "aa__ba", "ab__ba"}, visible)
