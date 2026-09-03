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

"""Unit tests for the per-level regex filters of the scenario, alternative and value-list trees."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from spinedb_api import to_database
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.mvcmodels.alternative_model import AlternativeModel
from spinetoolbox.spine_db_editor.mvcmodels.parameter_value_list_model import ParameterValueListModel
from spinetoolbox.spine_db_editor.mvcmodels.scenario_model import ScenarioModel


def _fetch_recursively(model):
    for item in model.visit_all():
        while item.can_fetch_more():
            item.fetch_more()
            QApplication.processEvents()


def _fetch_db_children_only(model):
    """Fetches the db item's direct children (top level) but leaves the level below unfetched.

    Returns:
        the db tree item whose children (scenarios / value lists) are now loaded
    """
    db_item = _db_item(model)
    while db_item.can_fetch_more():
        db_item.fetch_more()
        QApplication.processEvents()
    return db_item


def _drive_force_fetch(model):
    """Runs the force-fetch cascade to completion, pumping the event loop between batches."""
    for _ in range(500):
        model._run_force_fetch()
        if not model._force_fetching:
            break
        QApplication.processEvents()
    model._apply_level_filters()


def _names(item):
    return [str(child.data(0, Qt.ItemDataRole.DisplayRole)) for child in item.visible_children]


def _db_item(model):
    return model.item_from_index(model.index(0, 0))


class TestAlternativeLevelFilter:
    """The alternative tree has a single filterable level, so it never hides empty parents."""

    def _model(self, db_editor, db_mngr, db_map):
        db_mngr.add_items("alternative", {db_map: [{"name": "apple"}, {"name": "apricot"}, {"name": "banana"}]})
        model = AlternativeModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_recursively(model)
        return model

    def test_filter_hides_non_matching_alternatives_but_keeps_add_row(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        db_item = _db_item(model)
        assert _names(db_item) == ["Base", "apple", "apricot", "banana", "Type new alternative name here..."]
        model.set_level_filter("alternative", "^ap")
        model._apply_level_filters()
        # The two matches survive and the phantom add-row is always kept visible.
        assert _names(db_item) == ["apple", "apricot", "Type new alternative name here..."]

    def test_filter_is_case_insensitive(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("alternative", "APPLE")
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["apple", "Type new alternative name here..."]

    def test_invalid_regex_falls_back_to_substring(self, db_editor, db_mngr, db_map):
        db_mngr.add_items("alternative", {db_map: [{"name": "a(b"}]})
        model = AlternativeModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_recursively(model)
        model.set_level_filter("alternative", "a(b")
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["a(b", "Type new alternative name here..."]

    def test_clear_restores_tree(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("alternative", "banana")
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["banana", "Type new alternative name here..."]
        model.clear_level_filters()
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["Base", "apple", "apricot", "banana", "Type new alternative name here..."]


class TestScenarioLevelFilter:
    def _model(self, db_editor, db_mngr, db_map):
        """Builds a scenario tree with scenario_a -> (Base, alt1, alt2) and scenario_b -> (Base)."""
        db_mngr.add_items("alternative", {db_map: [{"name": "alt1"}, {"name": "alt2"}]})
        db_mngr.add_items("scenario", {db_map: [{"name": "scenario_a"}, {"name": "scenario_b"}]})
        base_id = db_map.alternative(name="Base")["id"]
        alt1_id = db_map.alternative(name="alt1")["id"]
        alt2_id = db_map.alternative(name="alt2")["id"]
        scen_a_id = db_map.scenario(name="scenario_a")["id"]
        scen_b_id = db_map.scenario(name="scenario_b")["id"]
        db_mngr.set_scenario_alternatives(
            {
                db_map: [
                    {"id": scen_a_id, "alternative_id_list": [base_id, alt1_id, alt2_id]},
                    {"id": scen_b_id, "alternative_id_list": [base_id]},
                ]
            }
        )
        model = ScenarioModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_recursively(model)
        return model, {"Base": base_id, "alt1": alt1_id, "alt2": alt2_id}

    def _scenario(self, model, name):
        return next(c for c in _db_item(model).children if str(c.data(0, Qt.ItemDataRole.DisplayRole)) == name)

    def test_scenario_level_filter_hides_non_matching_scenarios(self, db_editor, db_mngr, db_map):
        model, _ = self._model(db_editor, db_mngr, db_map)
        db_item = _db_item(model)
        assert _names(db_item) == ["scenario_a", "scenario_b", "Type new scenario name here..."]
        model.set_level_filter("scenario", "scenario_a")
        model._apply_level_filters()
        assert _names(db_item) == ["scenario_a", "Type new scenario name here..."]

    def test_scenario_alternative_filter_hides_empty_scenarios(self, db_editor, db_mngr, db_map):
        model, _ = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("scenario_alternative", "alt2")
        model._apply_level_filters()
        # scenario_b has no alt2 and is fully loaded, so hide-empty drops it; scenario_a stays.
        assert _names(_db_item(model)) == ["scenario_a", "Type new scenario name here..."]
        scenario_a = self._scenario(model, "scenario_a")
        assert _names(scenario_a) == ["alt2", "Type scenario alternative name here..."]

    def test_add_rows_stay_visible_under_filters(self, db_editor, db_mngr, db_map):
        model, _ = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("scenario", "nomatch")
        model.set_level_filter("scenario_alternative", "nomatch")
        model._apply_level_filters()
        # Nothing matches, but the scenario add-row must remain.
        assert _names(_db_item(model)) == ["Type new scenario name here..."]

    def test_clear_restores_tree(self, db_editor, db_mngr, db_map):
        model, _ = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("scenario", "scenario_a")
        model._apply_level_filters()
        model.clear_level_filters()
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["scenario_a", "scenario_b", "Type new scenario name here..."]

    def _partially_built_model(self, db_editor, db_mngr, db_map):
        """Same tree as :meth:`_model` but with only the scenarios fetched - their alternatives are not."""
        db_mngr.add_items("alternative", {db_map: [{"name": "alt1"}, {"name": "alt2"}]})
        db_mngr.add_items("scenario", {db_map: [{"name": "scenario_a"}, {"name": "scenario_b"}]})
        base_id = db_map.alternative(name="Base")["id"]
        alt1_id = db_map.alternative(name="alt1")["id"]
        alt2_id = db_map.alternative(name="alt2")["id"]
        scen_a_id = db_map.scenario(name="scenario_a")["id"]
        scen_b_id = db_map.scenario(name="scenario_b")["id"]
        db_mngr.set_scenario_alternatives(
            {
                db_map: [
                    {"id": scen_a_id, "alternative_id_list": [base_id, alt1_id, alt2_id]},
                    {"id": scen_b_id, "alternative_id_list": [base_id]},
                ]
            }
        )
        model = ScenarioModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_db_children_only(model)
        return model

    def test_scenario_alternative_filter_force_fetches_across_scenarios(self, db_editor, db_mngr, db_map):
        model = self._partially_built_model(db_editor, db_mngr, db_map)
        real_scenarios = [c for c in _db_item(model).children if c.item_type == "scenario" and c.id is not None]
        # The scenario alternatives are not fetched yet.
        assert all(s.can_fetch_more() for s in real_scenarios)
        model.set_level_filter("scenario_alternative", "alt2")
        _drive_force_fetch(model)
        # Only scenario_a has alt2; scenario_b is force-fetched, found empty and hidden - no manual expansion.
        assert _names(_db_item(model)) == ["scenario_a", "Type new scenario name here..."]
        scenario_a = self._scenario(model, "scenario_a")
        assert _names(scenario_a) == ["alt2", "Type scenario alternative name here..."]

    def test_scenario_regex_narrows_which_scenarios_get_force_fetched(self, db_editor, db_mngr, db_map):
        model = self._partially_built_model(db_editor, db_mngr, db_map)
        model.set_level_filter("scenario", "scenario_a")
        model.set_level_filter("scenario_alternative", "Base")
        _drive_force_fetch(model)
        scenario_b = self._scenario(model, "scenario_b")
        # scenario_b fails the scenario regex, so its alternatives were never force-fetched.
        assert scenario_b.can_fetch_more()
        assert _names(_db_item(model)) == ["scenario_a", "Type new scenario name here..."]

    def test_b1_alternative_id_correct_under_scenario_alternative_filter(self, db_editor, db_mngr, db_map):
        """Regression: a hidden sibling must not shift the raw alternative_id lookup (raw_row, not child_number)."""
        model, ids = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("scenario_alternative", "alt2")
        model._apply_level_filters()
        scenario_a = self._scenario(model, "scenario_a")
        visible = scenario_a.visible_children
        real_items = [c for c in visible if c.alternative_id is not None]
        assert len(real_items) == 1
        # alt2 is raw row 2 in [Base, alt1, alt2]; a visible-index lookup would wrongly return Base's id.
        assert real_items[0].alternative_id == ids["alt2"]


class TestValueListLevelFilter:
    def _model(self, db_editor, db_mngr, db_map):
        """Builds list_a -> (apple, banana, cherry) and list_b -> (date)."""
        with signal_waiter(db_mngr.items_added, condition=lambda item_type, _: item_type == "list_value") as waiter:
            db_mngr.import_data(
                {
                    db_map: {
                        "parameter_value_lists": [
                            ("list_a", "apple"),
                            ("list_a", "banana"),
                            ("list_a", "cherry"),
                            ("list_b", "date"),
                        ]
                    }
                },
                "import value lists",
            )
            waiter.wait()
        model = ParameterValueListModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_recursively(model)
        return model

    def _partially_built_model(self, db_editor, db_mngr, db_map):
        """Same tree as :meth:`_model` but with only the value lists fetched - their values are not."""
        with signal_waiter(db_mngr.items_added, condition=lambda item_type, _: item_type == "list_value") as waiter:
            db_mngr.import_data(
                {
                    db_map: {
                        "parameter_value_lists": [
                            ("list_a", "apple"),
                            ("list_a", "banana"),
                            ("list_a", "cherry"),
                            ("list_b", "date"),
                        ]
                    }
                },
                "import value lists",
            )
            waiter.wait()
        model = ParameterValueListModel(db_editor, db_mngr, db_map)
        model.build_tree()
        _fetch_db_children_only(model)
        return model

    def _list(self, model, name):
        return next(c for c in _db_item(model).children if str(c.data(0, Qt.ItemDataRole.DisplayRole)) == name)

    def test_list_value_filter_force_fetches_across_lists(self, db_editor, db_mngr, db_map):
        model = self._partially_built_model(db_editor, db_mngr, db_map)
        real_lists = [c for c in _db_item(model).children if c.item_type == "parameter_value_list" and c.id is not None]
        # The list values are not fetched yet.
        assert all(list_item.can_fetch_more() for list_item in real_lists)
        model.set_level_filter("list_value", "banana")
        _drive_force_fetch(model)
        # Only list_a has banana; list_b is force-fetched, found empty and hidden - no manual expansion.
        assert _names(_db_item(model)) == ["list_a", "Type new list name here..."]
        list_a = self._list(model, "list_a")
        assert _names(list_a) == ["banana", "Enter new list value here..."]

    def test_list_regex_narrows_which_lists_get_force_fetched(self, db_editor, db_mngr, db_map):
        model = self._partially_built_model(db_editor, db_mngr, db_map)
        model.set_level_filter("parameter_value_list", "list_a")
        model.set_level_filter("list_value", "apple")
        _drive_force_fetch(model)
        list_b = self._list(model, "list_b")
        # list_b fails the list regex, so its values were never force-fetched.
        assert list_b.can_fetch_more()
        assert _names(_db_item(model)) == ["list_a", "Type new list name here..."]

    def test_list_level_filter_hides_non_matching_lists(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        assert _names(_db_item(model)) == ["list_a", "list_b", "Type new list name here..."]
        model.set_level_filter("parameter_value_list", "list_a")
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["list_a", "Type new list name here..."]

    def test_list_value_filter_hides_empty_lists(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("list_value", "banana")
        model._apply_level_filters()
        # list_b has no banana and is fully loaded -> hidden; list_a survives with only banana + add-row.
        assert _names(_db_item(model)) == ["list_a", "Type new list name here..."]
        list_a = self._list(model, "list_a")
        assert _names(list_a) == ["banana", "Enter new list value here..."]

    def test_clear_restores_tree(self, db_editor, db_mngr, db_map):
        model = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("parameter_value_list", "list_a")
        model._apply_level_filters()
        model.clear_level_filters()
        model._apply_level_filters()
        assert _names(_db_item(model)) == ["list_a", "list_b", "Type new list name here..."]

    def test_b1_add_value_index_correct_under_list_value_filter(self, db_editor, db_mngr, db_map):
        """Regression: hiding leading values must not corrupt the computed DB index (raw_row, not child_number)."""
        model = self._model(db_editor, db_mngr, db_map)
        model.set_level_filter("list_value", "apple")
        model._apply_level_filters()
        list_a = self._list(model, "list_a")
        # apple(0), banana(1), cherry(2) are the real rows; the phantom add-row follows at raw row 3.
        add_row = list_a.children[-1]
        assert add_row.is_empty_row()
        item_to_add = add_row._make_item_to_add(to_database("durian"))
        # Correct next index is 3 (cherry's index 2 + 1); a visible-index lookup would compute 1.
        assert item_to_add["index"] == 3
