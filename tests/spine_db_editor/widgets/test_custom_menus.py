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

"""Unit tests for ``custom_menus`` module."""
from unittest import mock
from PySide6.QtWidgets import QApplication, QWidget
from spinetoolbox.database_display_names import NameRegistry
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.mvcmodels.compound_models import (
    CompoundEntityAlternativeModel,
    CompoundEntityModel,
    CompoundParameterDefinitionModel,
)
from spinetoolbox.spine_db_editor.widgets.custom_menus import AutoFilterMenu, TabularViewDatabaseNameFilterMenu
from tests.mock_helpers import TestCaseWithQApplication, assert_table_model_data_pytest, fetch_model


class TestAutoFilterMenu:
    def test_select_all_items_for_filtering(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_entity(entity_class_name="bird", name="cassowary")
            db_map.add_entity(entity_class_name="bird", name="emu")
            db_map.add_entity_alternative(
                entity_class_name="bird", entity_byname=("cassowary",), alternative_name="Base", active=False
            )
            db_map.add_entity_alternative(
                entity_class_name="bird", entity_byname=("emu",), alternative_name="Base", active=True
            )
        source_model = CompoundEntityAlternativeModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "alternative_name")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"Base"}
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("alternative_name", None)

    def test_parameter_definition_names(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_parameter_definition(entity_class_name="bird", name="wing")
            db_map.add_parameter_definition(entity_class_name="bird", name="weight")
            db_map.add_entity_class(name="fish")
            db_map.add_parameter_definition(entity_class_name="fish", name="fin")
            db_map.add_parameter_definition(entity_class_name="fish", name="weight")
        source_model = CompoundParameterDefinitionModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "name")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"wing", "weight", "fin"}
        menu.filter.model().filter_by_condition(lambda active: active == "fin")
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("name", {"fin", "", None})
        menu.filter.model().filter_by_condition(lambda active: active == "weight")
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("name", {"weight", "", None})

    def test_select_entity_activities(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_entity(entity_class_name="bird", name="cassowary")
            db_map.add_entity(entity_class_name="bird", name="emu")
            db_map.add_entity_alternative(
                entity_class_name="bird", entity_byname=("cassowary",), alternative_name="Base", active=False
            )
            db_map.add_entity_alternative(
                entity_class_name="bird", entity_byname=("emu",), alternative_name="Base", active=True
            )
        source_model = CompoundEntityAlternativeModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "active")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"true", "false"}
        menu.filter.model().filter_by_condition(lambda active: active == "false")
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("active", {False})

    def test_select_entity_byname(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_entity(entity_class_name="bird", name="cassowary")
            db_map.add_entity(entity_class_name="bird", name="emu")
            db_map.add_entity_class(name="fish")
            db_map.add_entity(entity_class_name="fish", name="barracuda")
            db_map.add_entity(entity_class_name="fish", name="eel")
            db_map.add_entity_class(dimension_name_list=("fish", "bird"))
            db_map.add_entity(entity_class_name="fish__bird", element_name_list=("eel", "emu"))
            db_map.add_entity(entity_class_name="fish__bird", element_name_list=("barracuda", "emu"))
            db_map.add_entity(entity_class_name="fish__bird", element_name_list=("barracuda", "cassowary"))
            db_map.add_entity(entity_class_name="fish__bird", element_name_list=("eel", "cassowary"))
            db_map.add_entity_alternative(
                entity_class_name="fish__bird",
                entity_byname=("barracuda", "cassowary"),
                alternative_name="Base",
                active=False,
            )
            db_map.add_entity_alternative(
                entity_class_name="fish__bird", entity_byname=("barracuda", "emu"), alternative_name="Base", active=True
            )
            db_map.add_entity_alternative(
                entity_class_name="fish__bird", entity_byname=("eel", "cassowary"), alternative_name="Base", active=True
            )
            db_map.add_entity_alternative(
                entity_class_name="fish__bird", entity_byname=("eel", "emu"), alternative_name="Base", active=False
            )
        source_model = CompoundEntityAlternativeModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "entity_byname")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {
            "barracuda ǀ cassowary",
            "barracuda ǀ emu",
            "eel ǀ cassowary",
            "eel ǀ emu",
        }
        menu.filter.model().filter_by_condition(lambda active: active == "eel ǀ cassowary")
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("entity_byname", {("eel", "cassowary")})

    def test_menu_remembers_selected_data(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_parameter_definition(entity_class_name="bird", name="wing")
            db_map.add_entity_class(name="fish")
            db_map.add_parameter_definition(entity_class_name="fish", name="fin")
        source_model = CompoundParameterDefinitionModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "name")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"wing", "fin"}
        menu.filter.model().filter_by_condition(lambda active: active == "wing")
        menu.filter.model().empty_selected = False
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("name", {"wing"})
            source_model.set_auto_filter(*waiter.args)
        with signal_waiter(source_model.non_committed_items_added) as waiter:
            db_mngr.add_items(
                "parameter_definition",
                {
                    db_map: [
                        {"entity_class_name": "bird", "name": "weight"},
                        {"entity_class_name": "fish", "name": "weight"},
                    ]
                },
            )
            waiter.wait()
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"wing", "fin", "weight"}
        assert not menu.filter.model().all_selected
        assert not menu.filter.model().empty_selected
        assert menu.filter.model().get_selected() == {"wing"}

    def test_empty_selected(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_entity(entity_class_name="bird", name="cassowary", lat=2.3, lon=3.2)
            db_map.add_entity(entity_class_name="bird", name="emu", description="Another grounded bird.")
            db_map.add_entity(entity_class_name="bird", name="ostrich", description="")
        source_model = CompoundEntityModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "lon")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"3.2"}
        menu.filter.model().filter_by_condition(lambda active: False)
        assert menu.filter.model().empty_selected
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("lon", {None})
        menu = AutoFilterMenu(parent_widget, source_model, "description")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"Another grounded bird."}
        menu.filter.model().filter_by_condition(lambda active: False)
        assert menu.filter.model().empty_selected
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("description", {None, ""})

    def test_empty_selection_remembered(self, parent_widget, db_mngr, db_map):
        with db_map:
            db_map.add_entity_class(name="bird")
            db_map.add_entity(entity_class_name="bird", name="cassowary", lat=2.3, lon=3.2)
            db_map.add_entity(entity_class_name="bird", name="emu")
            db_map.add_entity(entity_class_name="bird", name="ostrich")
        source_model = CompoundEntityModel(db_mngr, db_mngr, db_map)
        fetch_model(source_model)
        menu = AutoFilterMenu(parent_widget, source_model, "lon")
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"3.2"}
        menu.filter.model().filter_by_condition(lambda active: False)
        assert menu.filter.model().empty_selected
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.filter.apply_filter()
            waiter.wait()
            assert waiter.args == ("lon", {None})
            source_model.set_auto_filter(*waiter.args)
        while source_model.rowCount() != 2:
            QApplication.processEvents()
        expected = [
            ["bird", "emu", "emu", None, None, None, None, None, None, "TestAutoFilterMenu_db"],
            ["bird", "ostrich", "ostrich", None, None, None, None, None, None, "TestAutoFilterMenu_db"],
        ]
        assert_table_model_data_pytest(source_model, expected)
        menu.aboutToShow.emit()
        assert menu.filter.model().data_set == {"3.2"}
        assert menu.filter.model().empty_selected


class TestTabularViewCodenameFilterMenu(TestCaseWithQApplication):
    def setUp(self):
        self._parent = QWidget()

    def tearDown(self):
        self._parent.deleteLater()

    def test_init_fills_filter_list_with_database_codenames(self):
        db_map1 = mock.MagicMock()
        db_map1.sa_url = "sqlite:///a"
        db_map2 = mock.MagicMock()
        db_map2.sa_url = "sqlite:///b"
        db_maps = [db_map1, db_map2]
        name_registry = NameRegistry()
        name_registry.register(db_map1.sa_url, "db map 1")
        name_registry.register(db_map2.sa_url, "db map 2")
        menu = TabularViewDatabaseNameFilterMenu(self._parent, db_maps, "database", name_registry)
        self.assertIsNone(menu.anchor)
        filter_list_model = menu.filter.model()
        filter_rows = []
        for row in range(filter_list_model.rowCount()):
            filter_rows.append(filter_list_model.index(row, 0).data())
        self.assertEqual(filter_rows, ["(Select all)", "(Empty)", "db map 1", "db map 2"])

    def test_filter_changed_signal_is_emitted_correctly(self):
        db_map1 = mock.MagicMock()
        db_map1.sa_url = "sqlite:///a"
        db_map2 = mock.MagicMock()
        db_map2.sa_url = "sqlite:///b"
        db_maps = [db_map1, db_map2]
        name_registry = NameRegistry()
        name_registry.register(db_map1.sa_url, "db map 1")
        name_registry.register(db_map2.sa_url, "db map 2")
        menu = TabularViewDatabaseNameFilterMenu(self._parent, db_maps, "database", name_registry)
        with signal_waiter(menu.filter_changed, timeout=0.1) as waiter:
            menu.clear_filter()
            waiter.wait()
            self.assertEqual(waiter.args, ("database", {None, "db map 1", "db map 2"}, False))
