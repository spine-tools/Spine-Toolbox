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
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QApplication
from tests.spine_db_editor.widgets.helpers import select_item_with_index
from tests.spine_db_editor.widgets.spine_db_editor_test_base import DBEditorTestBase


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
        self.fetch_entity_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = next(x for x in root_item.children if x.display_data == "fish")
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(fish_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        selection_model.select(fish_index, QItemSelectionModel.SelectionFlag.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("dog",)],
            self.spine_db_editor.parameter_value_model: [("dog", ("pluto",)), ("dog", ("scooby",))],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_nonzero_dimensional_entity_class(self):
        """Test that parameter tables are filtered when selecting relationship classes in the object tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        self.fetch_entity_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_dog_item = next(x for x in root_item.children if x.display_data == "fish__dog")
        fish_dog_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_dog_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(fish_dog_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        selection_model.select(fish_dog_index, QItemSelectionModel.SelectionFlag.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("dog",), ("fish",), ("dog__fish",)],
            self.spine_db_editor.parameter_value_model: [
                ("dog__fish", ("pluto", "nemo")),
                ("fish", ("nemo",)),
                ("dog", ("pluto",)),
                ("dog", ("scooby",)),
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_entity_class_and_entity_cross_selection(self):
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        self.fetch_entity_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        fish_item = next(x for x in root_item.children if x.display_data == "fish")
        fish_index = self.spine_db_editor.entity_tree_model.index_from_item(fish_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        dog_item = next(x for x in root_item.children if x.display_data == "dog")
        scooby_item = next(x for x in dog_item.children if x.display_data == "scooby")
        scooby_index = self.spine_db_editor.entity_tree_model.index_from_item(scooby_item)
        selection_model.setCurrentIndex(fish_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        selection_model.select(fish_index, QItemSelectionModel.SelectionFlag.Select)
        selection_model.setCurrentIndex(scooby_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        selection_model.select(scooby_index, QItemSelectionModel.SelectionFlag.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [],
            self.spine_db_editor.parameter_value_model: [
                ("dog", ("pluto",)),
                ("fish__dog", ("nemo", "pluto")),
                ("dog__fish", ("pluto", "nemo")),
            ],
        }
        self._assert_filter(filtered_values)

    def test_filter_parameter_tables_per_entity(self):
        """Test that parameter tables are filtered when selecting entities in the entity tree."""
        for model in self._filtered_fields:
            if model.canFetchMore(None):
                model.fetchMore(None)
        self.put_mock_dataset_in_db_mngr()
        self.fetch_entity_tree_model()
        root_item = self.spine_db_editor.entity_tree_model.root_item
        dog_item = next(x for x in root_item.children if x.display_data == "dog")
        pluto_item = next(x for x in dog_item.children if x.display_data == "pluto")
        pluto_index = self.spine_db_editor.entity_tree_model.index_from_item(pluto_item)
        selection_model = self.spine_db_editor.ui.treeView_entity.selectionModel()
        selection_model.setCurrentIndex(pluto_index, QItemSelectionModel.SelectionFlag.NoUpdate)
        selection_model.select(pluto_index, QItemSelectionModel.SelectionFlag.Select)
        filtered_values = {
            self.spine_db_editor.parameter_definition_model: [("fish",)],
            self.spine_db_editor.parameter_value_model: [
                ("fish__dog", ("nemo", "scooby")),
                ("fish", ("nemo",)),
                ("dog", ("scooby",)),
            ],
        }
        self._assert_filter(filtered_values)


class TestSpineDBEditorGraphFilter(DBEditorTestBase):
    """Tests for the filtering in the graph view."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = {}
        cls._add_test_data()
        cls._create_highlights()

    @classmethod
    def _create_highlights(cls):
        pen = QPen(Qt.PenStyle.SolidLine)
        pen.setColor(QColor.fromRgbF(0, 0, 0, 0))
        cls.ACTIVE = pen
        pen = QPen(Qt.PenStyle.SolidLine)
        pen.setColor(QColor.fromRgbF(0, 0, 0, 1))
        cls.INACTIVE = pen
        pen = QPen(Qt.PenStyle.DashLine)
        pen.setColor(QColor.fromRgbF(0, 0, 0, 1))
        cls.CONFLICTED = pen
        pen = QPen(Qt.PenStyle.DotLine)
        pen.setColor(QColor.fromRgbF(0, 0, 0, 1))
        cls.PARAMETER = pen

    def setUp(self):
        super().setUp()
        self.spine_db_editor.apply_graph_style()
        self._import_data()
        self._create_indexes()
        self.all_entities = {"__".join(x[1]) if isinstance(x[1], list) else x[1] for x in self.data["entities"]}
        self.spine_db_editor._layout_gen_id = 0
        self.gv = self.spine_db_editor.ui.graphicsView
        self.gv.set_property("max_entity_dimension_count", 12)

    def tearDown(self):
        self._clear_selection_models()
        super().tearDown()

    def _create_indexes(self):
        """Gets the indexes for every item in entity, alternative and scenario trees in the database"""
        self.indexes = {
            "empty_space_entity": self.spine_db_editor.entity_tree_model.createIndex(-1, -1),
            "empty_space_alternative": self.spine_db_editor.alternative_model.createIndex(-1, -1),
            "empty_space_scenario": self.spine_db_editor.scenario_model.createIndex(-1, -1),
        }
        model = self.spine_db_editor.entity_tree_model
        root_item = model.root_item
        self.indexes["entity_root"] = model.index_from_item(root_item)
        for entity_class in root_item.children:
            self.indexes[f"entity_class_{entity_class.name}"] = model.index_from_item(entity_class)
            class_index = model.index(2, 0, model.index_from_item(root_item))
            while model.canFetchMore(class_index):
                model.fetchMore(class_index)
                QApplication.processEvents()
            for entity in entity_class.children:
                self.indexes[f"entity_{entity.name}"] = model.index_from_item(entity)
        model = self.spine_db_editor.alternative_model
        self.indexes["alternative_root"] = model.index(0, 0)
        for alternative in model.item_from_index(model.index(0, 0)).children:
            if not alternative.id:
                continue
            self.indexes[f"alternative_{alternative.name}"] = model.index_from_item(alternative)
        model = self.spine_db_editor.scenario_model
        root_index = model.index(0, 0)
        self.indexes["scenario_root"] = root_index
        for scenario in model.item_from_index(root_index).children:
            if not scenario.id:
                continue
            scenario_index = model.index_from_item(scenario)
            self.indexes[f"scenario_{scenario.name}"] = scenario_index
            model.fetchMore(scenario_index)
            while model.canFetchMore(scenario_index):
                model.fetchMore(scenario_index)
                QApplication.processEvents()
            for scenario_alt in scenario.children:
                if not scenario_alt.alternative_id:
                    continue
                self.indexes[f"scen_alt_{scenario_alt.name}"] = model.index_from_item(scenario_alt)

    @classmethod
    def _add_test_data(cls):
        data = {
            "entity_classes": [
                ["A", [], None, None, False],
                ["B", [], None, None, True],
                ["C", [], None, None, False],
                ["D", [], None, None, False],
                ["A__A", ["A", "A"], None, None, True],
                ["A__B", ["A", "B"], None, None, True],
                ["C__C", ["C", "C"], None, None, True],
            ],
            "entities": [
                ["A", "aa", None],
                ["A", "ab", None],
                ["B", "ba", None],
                ["B", "bb", None],
                ["C", "ca", None],
                ["C", "cb", None],
                ["D", "da", None],
                ["D", "db", None],
                ["A__A", ["aa", "ab"], None],
                ["A__B", ["aa", "ba"], None],
                ["A__B", ["ab", "ba"], None],
            ],
            "entity_alternatives": [
                ["A", ["aa"], "Alt1", False],
                ["A", ["aa"], "Alt2", True],
                ["A", ["ab"], "Alt1", True],
                ["A", ["ab"], "Alt3", True],
                ["B", ["bb"], "Alt2", False],
                ["C", ["ca"], "Alt3", True],
                ["C", ["cb"], "Alt3", True],
                ["D", ["da"], "Alt2", True],
            ],
            "alternatives": [["Alt1", ""], ["Alt2", ""], ["Alt3", ""], ["Alt4", ""]],
            "scenarios": [["scen1", False, ""], ["scen2", False, ""]],
            "scenario_alternatives": [["scen1", "Alt1", "Alt2"], ["scen1", "Alt2", None], ["scen2", "Alt3", None]],
            "parameter_definitions": [
                ["A__B", "par_A__B", None, None, None],
                ["D", "par_D", None, None, None],
                ["A", "par_A", None, None, None],
                ["B", "par_B", None, None, None],
            ],
            "parameter_values": [
                ["A__B", ["aa", "ba"], "par_A__B", "some_value", "Alt1"],
                ["A__B", ["aa", "ba"], "par_A__B", 3, "Alt2"],
                ["D", "da", "par_D", 3, "Alt1"],
                ["D", "db", "par_D", 2, "Alt1"],
                ["A", "aa", "par_A", 4, "Alt4"],
                ["B", "ba", "par_B", 5, "Alt4"],
            ],
        }
        cls.data = data
        sanitized_data = {}
        for item_type, items in data.items():
            sanitized_items = tuple(tuple(x if not isinstance(x, list) else tuple(x) for x in item) for item in items)
            sanitized_data[item_type] = sanitized_items
        cls.sanitized_data = sanitized_data

    def _import_data(self):
        self.spine_db_editor.import_data(self.sanitized_data, "Import test data.")
        models = (
            self.spine_db_editor.parameter_value_model,
            self.spine_db_editor.parameter_definition_model,
            self.spine_db_editor.entity_alternative_model,
        )
        for model in models:
            if model.canFetchMore(None):
                model.fetchMore(None)

    def _refresh_graph(self):
        """Rebuilds and refreshes the graph"""
        self.spine_db_editor._update_graph_data()
        self.gv.clear_cross_hairs_items()
        coords = list(range(len(self.data["entities"])))
        self.spine_db_editor._complete_graph(0, coords, coords)
        self.spine_db_editor._graph_fetch_more_later()

    def _clear_selection_models(self):
        for model in (
            self.spine_db_editor.ui.treeView_entity.selectionModel(),
            self.spine_db_editor.ui.alternative_tree_view.selectionModel(),
            self.spine_db_editor.ui.scenario_tree_view.selectionModel(),
        ):
            model.clearSelection()
        self._refresh_graph()
        entities = {item.name for item in self.spine_db_editor.entity_items}
        self.assertEqual(set(), entities)

    def _assert_visible(self, expected):
        """Checks that the correct entities are visible and possibly highlighted with the correct pens"""
        actual = {item.name: item._bg.pen() for item in self.spine_db_editor.entity_items}
        self.assertEqual(expected.keys(), actual.keys())
        for key, expected_pen in expected.items():
            self.assertEqual(expected_pen.style(), actual[key].style())  # Check the linestyle
            for i in ("red", "green", "blue"):  # Check the color
                self.assertEqual(getattr(expected_pen.color(), i)(), getattr(actual[key].color(), i)())

    def test_filtering_with_entity_selections(self):
        """Tests that the graph view filters the entities correctly based on Entity Tree selection"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        entity_tree_view.expandAll()
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse(self.spine_db_editor.entity_items)
            # Select the root item, every entity should be visible
            select_item_with_index(entity_tree_view, self.indexes["entity_root"])
            self._refresh_graph()
            self._assert_visible({name: self.ACTIVE for name in self.all_entities})
            # Select the entity class A
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            self._refresh_graph()
            self._assert_visible({"ab": self.ACTIVE, "aa": self.ACTIVE, "aa__ab": self.ACTIVE})
            # Extend selection with entity class B
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.ACTIVE,
                    "bb": self.ACTIVE,
                    "aa__ab": self.ACTIVE,
                    "aa__ba": self.ACTIVE,
                    "ab__ba": self.ACTIVE,
                }
            )
            # Select one entity
            select_item_with_index(entity_tree_view, self.indexes["entity_ab"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "ab": self.ACTIVE,
                }
            )
            # Selecting other unrelated entity class
            select_item_with_index(entity_tree_view, self.indexes["entity_class_C"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "ab": self.ACTIVE,
                    "ca": self.ACTIVE,
                    "cb": self.ACTIVE,
                }
            )

    def test_filtering_with_alternative_selections(self):
        """Tests that the graph view filters the entities correctly based on Alternative tree selections"""
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.ui.dockWidget_parameter_value, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Selecting the root shouldn't do anything
            select_item_with_index(alternative_tree_view, self.indexes["alternative_root"])
            self._refresh_graph()
            self._assert_visible({})
            # Selecting Alt1
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt1"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.PARAMETER,
                    "ab": self.ACTIVE,
                    "ba": self.PARAMETER,
                    "da": self.PARAMETER,
                    "db": self.PARAMETER,
                    "aa__ba": self.PARAMETER,
                }
            )
            # Selecting Alt1 and Alt2
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt2"], extend=True)
            self._refresh_graph()
            expected = {
                "aa": self.CONFLICTED,
                "ab": self.CONFLICTED,
                "ba": self.PARAMETER,
                "da": self.CONFLICTED,
                "db": self.PARAMETER,
                "aa__ba": self.PARAMETER,
            }
            self._assert_visible(expected)

    def test_filtering_with_entity_and_alternative_selections(self):
        """Tests that the graph view filters the entities correctly based on Entity and Alternative tree selections"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select entity classes A and B along with alternative Alt1.
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"], extend=True)
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt1"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.PARAMETER,
                    "ab": self.ACTIVE,
                    "ba": self.PARAMETER,
                    "aa__ba": self.PARAMETER,
                }
            )
            # This should clear everything
            select_item_with_index(entity_tree_view, self.indexes["empty_space_entity"])
            self._refresh_graph()
            self._assert_visible({})
            # Selecting class B with Alt2 should filter out all the entities in B
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"])
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt2"], extend=True)
            self._refresh_graph()
            self._assert_visible({})

    def test_empty_click_clears(self):
        """Tests that a click on empty space in one of the trees clears all selections"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select the entity class A
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            self._refresh_graph()
            self._assert_visible({"ab": self.ACTIVE, "aa": self.ACTIVE, "aa__ab": self.ACTIVE})
            # This should clear everything
            select_item_with_index(alternative_tree_view, self.indexes["empty_space_alternative"])
            self._refresh_graph()
            self._assert_visible({})

    def test_filtering_with_scenario_selections(self):
        """Tests that the graph view filters the entities correctly based on Scenario tree selections"""
        scenario_tree_view = self.spine_db_editor.ui.scenario_tree_view
        scenario_tree_view.expandAll()
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse(self.spine_db_editor.entity_items)
            # Select scen1
            select_item_with_index(scenario_tree_view, self.indexes["scenario_scen1"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.INACTIVE,
                    "da": self.ACTIVE,
                    "db": self.PARAMETER,
                    "aa__ab": self.INACTIVE,
                    "aa__ba": self.INACTIVE,
                    "ab__ba": self.INACTIVE,
                }
            )
            # Select Alt3 under scen2
            select_item_with_index(scenario_tree_view, self.indexes["scen_alt_Alt3"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "ab": self.ACTIVE,
                    "ca": self.ACTIVE,
                    "cb": self.ACTIVE,
                }
            )
            # Select scen1 again
            select_item_with_index(scenario_tree_view, self.indexes["scenario_scen1"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.INACTIVE,
                    "da": self.ACTIVE,
                    "db": self.PARAMETER,
                    "aa__ab": self.INACTIVE,
                    "aa__ba": self.INACTIVE,
                    "ab__ba": self.INACTIVE,
                }
            )

    def test_scenario_deselection_with_ctrl_is_consistent(self):
        """Tests that deselection with ctrl pressed is consistent"""
        scenario_tree_view = self.spine_db_editor.ui.scenario_tree_view
        scenario_tree_view.expandAll()
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse(self.spine_db_editor.entity_items)
            # Select scen1
            select_item_with_index(scenario_tree_view, self.indexes["scenario_scen1"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.INACTIVE,
                    "da": self.ACTIVE,
                    "db": self.PARAMETER,
                    "aa__ab": self.INACTIVE,
                    "aa__ba": self.INACTIVE,
                    "ab__ba": self.INACTIVE,
                }
            )
            # Select Alt3 under scen2
            select_item_with_index(scenario_tree_view, self.indexes["scen_alt_Alt3"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.PARAMETER,
                    "ab": self.ACTIVE,
                    "ba": self.INACTIVE,
                    "da": self.PARAMETER,
                    "db": self.PARAMETER,
                    "aa__ba": self.PARAMETER,
                }
            )
            # Deselect Alt3 under scen2
            select_item_with_index(scenario_tree_view, self.indexes["scen_alt_Alt3"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.INACTIVE,
                    "da": self.ACTIVE,
                    "db": self.PARAMETER,
                    "aa__ab": self.ACTIVE,
                    "aa__ba": self.ACTIVE,
                    "ab__ba": self.ACTIVE,
                }
            )

    def test_filtering_with_entity_selections_with_auto_expand(self):
        """Tests that the graph view filters the entities correctly based on the Entity Tree selections when
        auto-expand is enabled"""
        self.gv.set_property("auto_expand_entities", True)
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # When nothing selected, no entities should be visible
            self.assertFalse(self.spine_db_editor.entity_items)
            # Select entity class A
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.ACTIVE,
                    "aa__ab": self.ACTIVE,
                    "aa__ba": self.ACTIVE,
                    "ab__ba": self.ACTIVE,
                }
            )
            # Extend selection with entity class B
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.ACTIVE,
                    "bb": self.ACTIVE,
                    "aa__ab": self.ACTIVE,
                    "aa__ba": self.ACTIVE,
                    "ab__ba": self.ACTIVE,
                }
            )

    def test_filtering_with_entity_and_alternative_selections_with_auto_expand(self):
        """Tests that the graph view filters the entities correctly based on the Entity, Alternative and Scenario -tree
        selections when auto-expand is enabled"""
        self.gv.set_property("auto_expand_entities", True)
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        entity_tree_view.expandAll()
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select entity ba
            select_item_with_index(entity_tree_view, self.indexes["entity_ba"])
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ab": self.ACTIVE,
                    "ba": self.ACTIVE,
                    "aa__ba": self.ACTIVE,
                    "ab__ba": self.ACTIVE,
                }
            )
            # Select alternative Alt2
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt2"], extend=True)
            self._refresh_graph()
            self._assert_visible(
                {
                    "aa": self.ACTIVE,
                    "ba": self.PARAMETER,
                    "aa__ba": self.PARAMETER,
                }
            )

    def test_start_connecting_entities(self):
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            select_item_with_index(entity_tree_view, self.indexes["entity_root"])
            entity_tree_view.fully_expand()
            self._refresh_graph()
            entity_class = self.mock_db_map.get_entity_class_item(name="C__C")
            ent_item = [i for i in self.gv.entity_items if i.name == "ca"].pop()
            dimension_id_list = list(entity_class["dimension_id_list"])
            id_ = entity_class["id"]
            entity_class = {
                "name": "C__C",
                "description": None,
                "display_order": 99,
                "display_icon": None,
                "hidden": 0,
                "active_by_default": True,
                "dimension_id_list": dimension_id_list,
                "dimension_name_list": ("C", "C"),
                "dimension_count": 2,
                "id": id_,
                "entity_ids": set(),
            }
            self.spine_db_editor.start_connecting_entities(self.mock_db_map, entity_class, ent_item)

    def test_consistent_across_different_selection_order(self):
        """Tests that the graph view filter is consistent despite the selection order"""
        entity_tree_view = self.spine_db_editor.ui.treeView_entity
        alternative_tree_view = self.spine_db_editor.ui.alternative_tree_view
        entity_tree_view.expandAll()
        with (
            mock.patch.object(self.spine_db_editor.ui.dockWidget_entity_graph, "isVisible", return_value=True),
            mock.patch.object(self.spine_db_editor.qsettings, "value") as mock_value,
        ):
            mock_value.side_effect = lambda key, defaultValue: ("false" if key == "appSettings/stickySelection" else 0)
            # Select entity classes A then B then Alt1.
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"], extend=True)
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt4"], extend=True)
            self._refresh_graph()
            visible_first = {item.name: item._bg.pen() for item in self.spine_db_editor.entity_items}
            # Select entity classes A then Alt1 then class B.
            select_item_with_index(entity_tree_view, self.indexes["entity_class_A"])
            select_item_with_index(alternative_tree_view, self.indexes["alternative_Alt4"], extend=True)
            select_item_with_index(entity_tree_view, self.indexes["entity_class_B"], extend=True)
            self._refresh_graph()
            visible_second = {item.name: item._bg.pen() for item in self.spine_db_editor.entity_items}
            self.assertEqual(visible_first, visible_second)
