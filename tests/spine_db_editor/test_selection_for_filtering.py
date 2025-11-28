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
from unittest import mock
from PySide6.QtCore import QItemSelection, QItemSelectionModel
from PySide6.QtWidgets import QApplication
from spinedb_api import Asterisk, DatabaseMapping
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.selection_for_filtering import EntitySelectionForFiltering
from tests.conftest import parent_object
from tests.spine_db_editor.helpers import fetch_entity_tree_model


class TestEntitySelectionForFiltering:
    def test_deselect_everything(self, db_editor, db_map):
        with db_map:
            db_map.add_entity_class(name="Gadget")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            assert root_index.data() == "root"
            selection_model.select(root_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(Asterisk)
            mock_signal.emit.reset_mock()
            selection_model.select(root_index, QItemSelectionModel.SelectionFlag.Deselect)
            mock_signal.emit.assert_called_once_with({})

    def test_select_entity_class(self, db_editor, db_map):
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            assert root_index.data() == "root"
            gadget_index = model.index(0, 0, root_index)
            assert gadget_index.data() == "Gadget"
            database_index = model.index(0, 1, root_index)
            selection = QItemSelection(gadget_index, database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {db_map: {entity_class["id"]: Asterisk}},
            )

    def test_selecting_database_column_doesnt_count(self, db_editor, db_map):
        with db_map:
            db_map.add_entity_class(name="Gadget")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            database_index = model.index(0, 1, root_index)
            assert database_index.data() == "TestEntitySelectionForFiltering_db"
            selection_model.select(database_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()

    def test_select_entity_class_with_multiple_db_maps(self, db_editor, tmp_path, logger):
        url1 = "sqlite:///" + str(tmp_path / "db1.sqlite")
        with DatabaseMapping(url1, create=True) as db_map:
            db_map.add_entity_class(name="Gadget")
            db_map.add_entity_class(name="Widget")
            db_map.commit_session("Add test data.")
        url2 = "sqlite:///" + str(tmp_path / "db2.sqlite")
        with DatabaseMapping(url2, create=True) as db_map:
            entity_class2 = db_map.add_entity_class(name="Gadget")
            db_map.commit_session("Add test data.")
        with mock.patch.object(db_editor, "save_window_state"), mock.patch.object(db_editor, "restore_ui"):
            db_editor.load_db_urls([url1, url2])
        db_map1 = db_editor.db_mngr.get_db_map(url1, logger)
        with db_map1:
            entity_class1a = db_map1.entity_class(name="Gadget")
            entity_class1b = db_map1.entity_class(name="Widget")
        db_map2 = db_editor.db_mngr.get_db_map(url2, logger)
        with db_map2:
            entity_class2 = db_map2.entity_class(name="Gadget")
        view = db_editor.ui.treeView_entity
        model = view.model()
        fetch_entity_tree_model(db_editor)
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            gadget_index = model.index(0, 0, root_index)
            assert gadget_index.data() == "Gadget"
            gadget_database_index = model.index(0, 1, root_index)
            assert gadget_database_index.data() == "db1, db2"
            selection = QItemSelection(gadget_index, gadget_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {db_map1: {entity_class1a["id"]: Asterisk}, db_map2: {entity_class2["id"]: Asterisk}}
            )
            mock_signal.emit.reset_mock()
            widget_index = model.index(1, 0, root_index)
            assert widget_index.data() == "Widget"
            widget_database_index = model.index(1, 1, root_index)
            assert widget_database_index.data() == "db1"
            selection = QItemSelection(widget_index, widget_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {
                    db_map1: {entity_class1a["id"]: Asterisk, entity_class1b["id"]: Asterisk},
                    db_map2: {entity_class2["id"]: Asterisk},
                }
            )

    def test_select_single_entity(self, db_editor, db_map):
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
            entity = db_map.add_entity(entity_class_name=entity_class["name"], name="wall_clock")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            assert root_index.data() == "root"
            gadget_index = model.index(0, 0, root_index)
            assert gadget_index.data() == "Gadget"
            wall_clock_index = model.index(0, 0, gadget_index)
            wall_clock_database_index = model.index(0, 1, gadget_index)
            selection = QItemSelection(wall_clock_index, wall_clock_database_index)
            selection_model.select(
                selection,
                QItemSelectionModel.SelectionFlag.Select,
            )
            mock_signal.emit.assert_called_once_with({db_map: {entity_class["id"]: {entity["id"]}}})

    def test_select_entity_with_multiple_db_maps(self, db_editor, tmp_path, logger):
        url1 = "sqlite:///" + str(tmp_path / "db1.sqlite")
        with DatabaseMapping(url1, create=True) as db_map:
            db_map.add_entity_class(name="Gadget")
            db_map.add_entity(entity_class_name="Gadget", name="watch")
            db_map.add_entity(entity_class_name="Gadget", name="iron")
            db_map.commit_session("Add test data.")
        url2 = "sqlite:///" + str(tmp_path / "db2.sqlite")
        with DatabaseMapping(url2, create=True) as db_map:
            db_map.add_entity_class(name="Gadget")
            db_map.add_entity(entity_class_name="Gadget", name="watch")
            db_map.commit_session("Add test data.")
        with mock.patch.object(db_editor, "save_window_state"), mock.patch.object(db_editor, "restore_ui"):
            db_editor.load_db_urls([url1, url2])
        db_map1 = db_editor.db_mngr.get_db_map(url1, logger)
        with db_map1:
            entity_class1 = db_map1.entity_class(name="Gadget")
            entity1a = db_map1.entity(entity_class_name="Gadget", name="watch")
            entity1b = db_map1.entity(entity_class_name="Gadget", name="iron")
        db_map2 = db_editor.db_mngr.get_db_map(url2, logger)
        with db_map2:
            entity_class2 = db_map2.entity_class(name="Gadget")
            entity2 = db_map2.entity(entity_class_name="Gadget", name="watch")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            gadget_index = model.index(0, 0, root_index)
            iron_index = model.index(0, 0, gadget_index)
            assert iron_index.data() == "iron"
            iron_database_index = model.index(0, 1, gadget_index)
            assert iron_database_index.data() == "db1"
            watch_index = model.index(1, 0, gadget_index)
            assert watch_index.data() == "watch"
            watch_database_index = model.index(1, 1, gadget_index)
            assert watch_database_index.data() == "db1, db2"
            selection = QItemSelection(iron_index, iron_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {db_map1: {entity_class1["id"]: {entity1b["id"]}}, db_map2: {entity_class2["id"]: set()}}
            )
            mock_signal.emit.reset_mock()
            selection = QItemSelection(watch_index, watch_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {
                    db_map1: {entity_class1["id"]: {entity1a["id"], entity1b["id"]}},
                    db_map2: {entity_class2["id"]: {entity2["id"]}},
                }
            )

    def test_select_entity_in_one_and_class_in_other_db_map(self, db_editor, tmp_path, logger):
        url1 = "sqlite:///" + str(tmp_path / "db1.sqlite")
        with DatabaseMapping(url1, create=True) as db_map:
            db_map.add_entity_class(name="Gadget")
            db_map.add_entity(entity_class_name="Gadget", name="watch")
            db_map.commit_session("Add test data.")
        url2 = "sqlite:///" + str(tmp_path / "db2.sqlite")
        with DatabaseMapping(url2, create=True) as db_map:
            db_map.add_entity_class(name="Widget")
            db_map.commit_session("Add test data.")
        with mock.patch.object(db_editor, "save_window_state"), mock.patch.object(db_editor, "restore_ui"):
            db_editor.load_db_urls([url1, url2])
        db_map1 = db_editor.db_mngr.get_db_map(url1, logger)
        with db_map1:
            entity_class1 = db_map1.entity_class(name="Gadget")
            entity = db_map1.entity(entity_class_name="Gadget", name="watch")
        db_map2 = db_editor.db_mngr.get_db_map(url2, logger)
        with db_map2:
            entity_class2 = db_map2.entity_class(name="Widget")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            gadget_index = model.index(0, 0, root_index)
            assert gadget_index.data() == "Gadget"
            watch_index = model.index(0, 0, gadget_index)
            assert watch_index.data() == "watch"
            watch_database_index = model.index(0, 1, gadget_index)
            assert watch_database_index.data() == "db1"
            selection = QItemSelection(watch_index, watch_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with({db_map1: {entity_class1["id"]: {entity["id"]}}})
            mock_signal.emit.reset_mock()
            widget_index = model.index(1, 0, root_index)
            assert widget_index.data() == "Widget"
            widget_database_index = model.index(1, 1, root_index)
            assert widget_database_index.data() == "db2"
            selection = QItemSelection(widget_index, widget_database_index)
            selection_model.select(selection, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(
                {db_map1: {entity_class1["id"]: {entity["id"]}}, db_map2: {entity_class2["id"]: Asterisk}}
            )

    def test_root_item_selected_means_all_entities_selected(self, db_editor, db_map):
        with db_map:
            db_map.add_entity_class(name="Gadget")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            selection_model.select(root_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with(Asterisk)
            mock_signal.emit.reset_mock()
            gadget_index = model.index(0, 0, root_index)
            selection_model.select(gadget_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()

    def test_simplest_secondary_selection_case(self, parent_object):
        mock_selection_model = mock.MagicMock()
        filter_selection = EntitySelectionForFiltering(mock_selection_model, parent_object)
        with signal_waiter(filter_selection.secondary_entity_selection_changed) as waiter:
            filter_selection.update_secondary_entity_selection({})
            waiter.wait()
            assert waiter.args == ({},)

    def test_empty_secondary_entity_selection_results_in_primary_selection(self, db_editor, db_map):
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
            entity = db_map.add_entity(entity_class_name=entity_class["name"], name="wall_clock")
        fetch_entity_tree_model(db_editor)
        view = db_editor.ui.treeView_entity
        model = view.model()
        filter_selection = db_editor._entity_selection_for_filtering
        selection_model = view.selectionModel()
        expected_selection = {db_map: {entity_class["id"]: {entity["id"]}}}
        with mock.patch.object(filter_selection, "entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            root_index = model.index(0, 0)
            gadget_index = model.index(0, 0, root_index)
            wall_clock_index = model.index(0, 0, gadget_index)
            wall_clock_database_index = model.index(0, 1, gadget_index)
            selection = QItemSelection(wall_clock_index, wall_clock_database_index)
            selection_model.select(
                selection,
                QItemSelectionModel.SelectionFlag.Select,
            )
            mock_signal.emit.assert_called_once_with(expected_selection)
        with mock.patch.object(filter_selection, "secondary_entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            filter_selection.update_secondary_entity_selection({})
            mock_signal.emit.assert_called_once_with(expected_selection)

    def test_update_secondary_entity_selection(self, db_editor, tmp_path, logger):
        url1 = "sqlite:///" + str(tmp_path / "db1.sqlite")
        with DatabaseMapping(url1, create=True) as db_map:
            db_map.add_entity_class(name="Class1")
            db_map.add_entity(name="e1", entity_class_name="Class1")
            db_map.add_entity(name="e2", entity_class_name="Class1")
            db_map.commit_session("Add test data.")
        url2 = "sqlite:///" + str(tmp_path / "db2.sqlite")
        with DatabaseMapping(url2, create=True) as db_map:
            db_map.add_entity_class(name="Class1")
            db_map.add_entity(name="e1", entity_class_name="Class1")
            db_map.add_entity_class(name="Class2")
            db_map.add_entity(name="e2", entity_class_name="Class2")
            db_map.commit_session("Add test data.")
        with mock.patch.object(db_editor, "save_window_state"), mock.patch.object(db_editor, "restore_ui"):
            db_editor.load_db_urls([url1, url2])
        db_map1 = db_editor.db_mngr.get_db_map(url1, logger)
        with db_map1:
            entity_class1 = db_map1.entity_class(name="Class1")
            selected_entity1 = db_map1.entity(entity_class_name="Class1", name="e1")
        db_map2 = db_editor.db_mngr.get_db_map(url2, logger)
        with db_map2:
            entity_class2 = db_map2.entity_class(name="Class1")
            selected_entity2 = db_map2.entity(entity_class_name="Class1", name="e1")
        fetch_entity_tree_model(db_editor)
        filter_selection = db_editor._entity_selection_for_filtering
        entity_ids = {db_map1: [selected_entity1["id"]], db_map2: [selected_entity2["id"]]}
        with mock.patch.object(filter_selection, "secondary_entity_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            filter_selection.update_secondary_entity_selection(entity_ids)
            mock_signal.emit.assert_called_once_with(
                {
                    db_map1: {entity_class1["id"]: {selected_entity1["id"]}},
                    db_map2: {entity_class2["id"]: {selected_entity2["id"]}},
                }
            )


class TestAlternativeSelectionForFiltering:
    def test_select_and_deselect_single_alternative(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        base_alternative = db_map.alternative(name="Base")
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            database_index = model.index(0, 0)
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            base_alternative_index = model.index(0, 0, database_index)
            assert base_alternative_index.data() == base_alternative["name"]
            view.selectionModel().select(base_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with({db_map: {base_alternative["id"]}})
            mock_signal.emit.reset_mock()
            view.selectionModel().select(base_alternative_index, QItemSelectionModel.SelectionFlag.Clear)
            mock_signal.emit.assert_called_once_with(Asterisk)

    def test_selecting_alternative_descriptions_doesnt_trigger_signals(self, db_editor, logger):
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            database_index = model.index(0, 0)
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            description_index = model.index(0, 1, database_index)
            assert description_index.data() == "Base alternative"
            view.selectionModel().select(description_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_not_called()

    def test_selecting_empty_alternative_row_doesnt_trigger_signals(self, db_editor, logger):
        view = db_editor.ui.alternative_tree_view
        model = view.model()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            database_index = model.index(0, 0)
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            description_index = model.index(1, 0, database_index)
            assert description_index.data() == "Type new alternative name here..."
            view.selectionModel().select(description_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_not_called()

    def test_selecting_scenario_doesnt_select_its_alternatives(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            db_map.alternative(name="Base")
            db_map.add_alternative(name="Other", description="Another alternative")
            db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Other", rank=0)
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=1)
        view = db_editor.ui.scenario_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        while model.rowCount(database_index) == 1:
            model.fetchMore(database_index)
            QApplication.processEvents()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            scenario_index = model.index(0, 0, database_index)
            assert scenario_index.data() == "Scenario 1"
            view.selectionModel().select(scenario_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_not_called()

    def test_select_scenario_alternatives(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            base_alternative = db_map.alternative(name="Base")
            other_alternative = db_map.add_alternative(name="Other", description="Another alternative")
            db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=0)
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Other", rank=1)
        view = db_editor.ui.scenario_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        while model.rowCount(database_index) == 1:
            model.fetchMore(database_index)
            QApplication.processEvents()
        scenario_index = model.index(0, 0, database_index)
        assert scenario_index.data() == "Scenario 1"
        while model.rowCount(scenario_index) == 1:
            model.fetchMore(scenario_index)
            QApplication.processEvents()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            scenario_alternative_index = model.index(1, 0, scenario_index)
            assert scenario_alternative_index.data() == "Other"
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with({db_map: {other_alternative["id"]}})
            mock_signal.emit.reset_mock()
            scenario_alternative_index = model.index(0, 0, scenario_index)
            assert scenario_alternative_index.data() == base_alternative["name"]
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_called_once_with({db_map: {base_alternative["id"], other_alternative["id"]}})

    def test_selecting_empty_row_doesnt_count(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            base_alternative = db_map.alternative(name="Base")
            db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=0)
        view = db_editor.ui.scenario_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        while model.rowCount(database_index) == 1:
            model.fetchMore(database_index)
            QApplication.processEvents()
        scenario_index = model.index(0, 0, database_index)
        assert scenario_index.data() == "Scenario 1"
        while model.rowCount(scenario_index) == 1:
            model.fetchMore(scenario_index)
            QApplication.processEvents()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            scenario_alternative_index = model.index(0, 0, scenario_index)
            assert scenario_alternative_index.data() == base_alternative["name"]
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with({db_map: {base_alternative["id"]}})
            mock_signal.emit.reset_mock()
            scenario_alternative_index = model.index(1, 0, scenario_index)
            assert scenario_alternative_index.data() == "Type scenario alternative name here..."
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()

    def test_selecting_description_column_doesnt_count(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            base_alternative = db_map.alternative(name="Base")
            db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=0)
        view = db_editor.ui.scenario_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        while model.rowCount(database_index) == 1:
            model.fetchMore(database_index)
            QApplication.processEvents()
        scenario_index = model.index(0, 0, database_index)
        assert scenario_index.data() == "Scenario 1"
        while model.rowCount(scenario_index) == 1:
            model.fetchMore(scenario_index)
            QApplication.processEvents()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            assert database_index.data() == "TestAlternativeSelectionForFiltering_db"
            scenario_alternative_index = model.index(0, 0, scenario_index)
            assert scenario_alternative_index.data() == base_alternative["name"]
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with({db_map: {base_alternative["id"]}})
            mock_signal.emit.reset_mock()
            scenario_alternative_index = model.index(0, 1, scenario_index)
            assert scenario_alternative_index.data() == base_alternative["description"]
            view.selectionModel().select(scenario_alternative_index, QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()

    def test_selections_from_alternative_and_scenario_trees_are_combined(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            base_alternative = db_map.alternative(name="Base")
            other_alternative = db_map.add_alternative(name="Other", description="Another alternative")
            db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=0)
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Other", rank=1)
        alternative_view = db_editor.ui.alternative_tree_view
        alternative_model = alternative_view.model()
        alternative_database_index = alternative_model.index(0, 0)
        while alternative_model.rowCount(alternative_database_index) == 1:
            alternative_model.fetchMore()
            QApplication.processEvents()
        scenario_view = db_editor.ui.scenario_tree_view
        scenario_model = scenario_view.model()
        scenario_database_index = scenario_model.index(0, 0)
        while scenario_model.rowCount(scenario_database_index) == 1:
            scenario_model.fetchMore(scenario_database_index)
            QApplication.processEvents()
        scenario_index = scenario_model.index(0, 0, scenario_database_index)
        assert scenario_index.data() == "Scenario 1"
        while scenario_model.rowCount(scenario_index) == 1:
            scenario_model.fetchMore(scenario_index)
            QApplication.processEvents()
        filter_selection = db_editor._alternative_selection_for_filtering
        with mock.patch.object(filter_selection, "alternative_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            assert scenario_database_index.data() == "TestAlternativeSelectionForFiltering_db"
            scenario_alternative_index = scenario_model.index(1, 0, scenario_index)
            assert scenario_alternative_index.data() == "Other"
            scenario_view.selectionModel().select(
                scenario_alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )
            mock_signal.emit.assert_called_once_with({db_map: {other_alternative["id"]}})
            mock_signal.emit.reset_mock()
            alternative_index = alternative_model.index(0, 0, alternative_database_index)
            assert alternative_index.data() == base_alternative["name"]
            alternative_view.selectionModel().select(
                alternative_index, QItemSelectionModel.SelectionFlag.ClearAndSelect
            )
            mock_signal.emit.assert_called_once_with({db_map: {base_alternative["id"], other_alternative["id"]}})


class TestScenarioSelectionForFiltering:
    def test_select_scenario(self, db_editor, logger):
        db_mngr = db_editor.db_mngr
        db_map = db_mngr.get_db_map("sqlite://", logger, create=True)
        with db_map:
            db_map.alternative(name="Base")
            db_map.add_alternative(name="Other", description="Another alternative")
            scenario = db_map.add_scenario(name="Scenario 1")
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Base", rank=0)
            db_map.add_scenario_alternative(scenario_name="Scenario 1", alternative_name="Other", rank=1)
        view = db_editor.ui.scenario_tree_view
        model = view.model()
        database_index = model.index(0, 0)
        assert database_index.data() == "TestScenarioSelectionForFiltering_db"
        while model.rowCount(database_index) == 1:
            model.fetchMore(database_index)
            QApplication.processEvents()
        scenario_index = model.index(0, 0, database_index)
        assert scenario_index.data() == "Scenario 1"
        while model.rowCount(scenario_index) == 1:
            model.fetchMore(scenario_index)
            QApplication.processEvents()
        filter_selection = db_editor._scenario_selection_for_filtering
        with mock.patch.object(filter_selection, "scenario_selection_changed") as mock_signal:
            mock_signal.emit = mock.MagicMock()
            view.selectionModel().select(scenario_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with({db_map: {scenario["id"]}})
            mock_signal.emit.reset_mock()
            view.selectionModel().select(database_index, QItemSelectionModel.SelectionFlag.ClearAndSelect)
            mock_signal.emit.assert_called_once_with(Asterisk)
            mock_signal.emit.reset_mock()
            view.selectionModel().select(model.index(0, 0, scenario_index), QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()
            view.selectionModel().select(model.index(0, 1, scenario_index), QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()
            view.selectionModel().select(model.index(1, 0, scenario_index), QItemSelectionModel.SelectionFlag.Select)
            mock_signal.emit.assert_not_called()
