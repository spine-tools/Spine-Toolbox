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
from PySide6.QtCore import QItemSelection, QItemSelectionModel, QModelIndex, Qt
import pytest
from spinedb_api import Asterisk, DatabaseMapping
from spinetoolbox.mvcmodels.shared import DB_MAP_ROLE
from spinetoolbox.spine_db_editor.default_row_generator import DefaultRowData, DefaultRowGenerator

uncalled = object()


class Receiver:
    def __init__(self):
        self.definition_default_row = uncalled
        self.value_default_row = uncalled
        self.entity_alternative_default_row = uncalled

    def connect(self, generator: DefaultRowGenerator):
        generator.parameter_definition_default_row_updated.connect(self.update_definition_row)
        generator.parameter_value_default_row_updated.connect(self.update_value_row)
        generator.entity_alternative_default_row_updated.connect(self.update_entity_alternative_row)

    def update_definition_row(self, row_data):
        if self.definition_default_row is not uncalled:
            raise RuntimeError("double call; reset first")
        self.definition_default_row = row_data

    def update_value_row(self, row_data):
        if self.value_default_row is not uncalled:
            raise RuntimeError("double call; reset first")
        self.value_default_row = row_data

    def update_entity_alternative_row(self, row_data):
        if self.entity_alternative_default_row is not uncalled:
            raise RuntimeError("double call; reset first")
        self.entity_alternative_default_row = row_data

    def reset(self):
        self.definition_default_row = uncalled
        self.value_default_row = uncalled
        self.entity_alternative_default_row = uncalled

    def called(self):
        return (
            self.definition_default_row is not uncalled
            and self.value_default_row is not uncalled
            and self.entity_alternative_default_row is not uncalled
        )


class DBMapGenerator:
    def __init__(self, db_mngr, tmp_path, name_prefix, logger):
        self._db_mngr = db_mngr
        self._tmp_path = tmp_path
        self._name_prefix = name_prefix
        self._logger = logger
        self._next_id = 1

    def __call__(self):
        name = f"{self._name_prefix}_{self._next_id}"
        self._next_id += 1
        url = "sqlite:///" + str(self._tmp_path / f"{name}.sqlite")
        db_map = self._db_mngr.get_db_map(url, self._logger, create=True)
        self._db_mngr.name_registry.register(db_map.sa_url, name)
        return db_map


@pytest.fixture()
def db_map_generator(db_mngr, tmp_path, db_name, logger):
    return DBMapGenerator(db_mngr, tmp_path, db_name, logger)


def add_db_maps(db_maps, entity_view, alternative_view):
    for view in (entity_view, alternative_view):
        model = view.model()
        model.db_maps = db_maps
        model.build_tree()


def _find_index(display_data, parent_index, model):
    for row in range(model.rowCount(parent_index)):
        index = model.index(row, 0, parent_index)
        if index.data() == display_data:
            return index
    raise RuntimeError(f"no such display data: {display_data}")


class TestDefaultRowGenerator:
    @staticmethod
    def _add_classes_to_model(db_map_data, model):
        root_index = model.index(0, 0)
        root_item = model.item_from_index(root_index)
        root_item.handle_items_added(db_map_data)

    @staticmethod
    def _add_entities_to_model(db_map_data, class_name, model):
        root_index = model.index(0, 0)
        class_index = _find_index(class_name, root_index, model)
        model.item_from_index(class_index).handle_items_added(db_map_data)

    @staticmethod
    def _select_class_row(row, entity_tree_view, selection_flag=QItemSelectionModel.SelectionFlag.Select):
        model = entity_tree_view.model()
        root_index = model.index(0, 0)
        class_index = model.index(row, 0, root_index)
        db_index = model.index(row, 1, root_index)
        selection = QItemSelection(class_index, db_index)
        entity_tree_view.selectionModel().select(selection, selection_flag)

    @staticmethod
    def _select_entity_row(row, class_name, entity_tree_view, selection_flag=QItemSelectionModel.SelectionFlag.Select):
        model = entity_tree_view.model()
        root_index = model.index(0, 0)
        class_index = _find_index(class_name, root_index, model)
        entity_index = model.index(row, 0, class_index)
        db_index = model.index(row, 1, class_index)
        selection = QItemSelection(entity_index, db_index)
        entity_tree_view.selectionModel().select(selection, selection_flag)

    @staticmethod
    def _add_alternatives_to_model(db_map_data, model):
        for root_row in range(model.rowCount()):
            root_index = model.index(root_row, 0)
            model.item_from_index(root_index).handle_items_added(db_map_data)

    @staticmethod
    def _select_alternative_row(
        row, db_map, alternative_tree_view, selection_flag=QItemSelectionModel.SelectionFlag.Select
    ):
        model = alternative_tree_view.model()
        for db_row in range(model.rowCount()):
            db_index = model.index(db_row, 0)
            if db_index.data(DB_MAP_ROLE) is db_map:
                break
        else:
            raise RuntimeError("no such database mapping")
        alternative_index = model.index(row, 0, db_index)
        description_index = model.index(row, 1, db_index)
        selection = QItemSelection(alternative_index, description_index)
        alternative_tree_view.selectionModel().select(selection, selection_flag)

    def test_selecting_entity_root_first_doesnt_trigger_updates(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        entity_selection_model = entity_tree_view.selectionModel()
        generator = DefaultRowGenerator(entity_selection_model, alternative_tree_view.selectionModel(), parent_object)
        receiver = Receiver()
        receiver.connect(generator)
        entity_model = entity_tree_view.model()
        root_index = entity_model.index(0, 0)
        assert root_index.data() == "root"
        entity_selection_model.select(root_index, QItemSelectionModel.SelectionFlag.Select)
        assert not receiver.called()

    def test_single_entity_class_selected(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        entity_selection_model = entity_tree_view.selectionModel()
        generator = DefaultRowGenerator(entity_selection_model, alternative_tree_view.selectionModel(), parent_object)
        receiver = Receiver()
        receiver.connect(generator)
        entity_model = entity_tree_view.model()
        self._add_classes_to_model({db_map: [gadget]}, entity_model)
        self._select_class_row(0, entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_clear_single_class_selection(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        entity_selection_model = entity_tree_view.selectionModel()
        generator = DefaultRowGenerator(entity_selection_model, alternative_tree_view.selectionModel(), parent_object)
        entity_model = entity_tree_view.model()
        self._add_classes_to_model({db_map: [gadget]}, entity_model)
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_class_row(0, entity_tree_view, QItemSelectionModel.SelectionFlag.Deselect)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": None}, None)
        row_data = DefaultRowData({"entity_class_name": None, "entity_byname": None, "alternative_name": None}, None)
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_first_one_then_two_entity_classes_selected(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            widget = db_map.add_entity_class(name="Widget")
        entity_selection_model = entity_tree_view.selectionModel()
        generator = DefaultRowGenerator(entity_selection_model, alternative_tree_view.selectionModel(), parent_object)
        entity_model = entity_tree_view.model()
        self._add_classes_to_model({db_map: [gadget, widget]}, entity_model)
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_class_row(1, entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": None}, None)
        row_data = DefaultRowData({"entity_class_name": None, "entity_byname": None, "alternative_name": None}, None)
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_two_entity_classes_from_different_databases(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
        db_map2 = db_map_generator()
        with db_map2:
            gadget2 = db_map2.add_entity_class(name="Gadget")
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget1], db_map2: [gadget2]}, empty_entity_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_class_row(0, empty_entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_entity_class_that_exists_in_a_single_database(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
        db_map2 = db_map_generator()
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget1]}, empty_entity_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_class_row(0, empty_entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_single_entity(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_entities_to_model({db_map: [wall_clock]}, "Gadget", entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_entity_row(0, "Gadget", entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData(
            {
                "entity_class_name": "Gadget",
            },
            db_map,
        )
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": ("wall_clock",), "alternative_name": None}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_single_entity_and_entity_root(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_entities_to_model({db_map: [wall_clock]}, "Gadget", entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_entity_row(0, "Gadget", entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        root_index = entity_tree_view.model().index(0, 0)
        entity_tree_view.selectionModel().select(root_index, QItemSelectionModel.SelectionFlag.Select)
        assert not receiver.called()

    def test_first_one_then_two_entities(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
            wrist_watch = db_map.add_entity(name="wrist_watch", entity_class_name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_entities_to_model({db_map: [wall_clock, wrist_watch]}, "Gadget", entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_entity_row(0, "Gadget", entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_entity_row(1, "Gadget", entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_two_entities_in_different_databases(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            wall_clock1 = db_map1.add_entity(name="wall_clock", entity_class_name="Gadget")
        db_map2 = db_map_generator()
        with db_map2:
            gadget2 = db_map2.add_entity_class(name="Gadget")
            wall_clock2 = db_map2.add_entity(name="wall_clock", entity_class_name="Gadget")
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget1], db_map2: [gadget2]}, empty_entity_tree_view.model())
        self._add_entities_to_model(
            {db_map1: [wall_clock1], db_map2: [wall_clock2]}, "Gadget", empty_entity_tree_view.model()
        )
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_entity_row(0, "Gadget", empty_entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": ("wall_clock",), "alternative_name": None}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_entity_that_exists_in_single_database(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            wall_clock1 = db_map1.add_entity(name="wall_clock", entity_class_name="Gadget")
        db_map2 = db_map_generator()
        with db_map2:
            gadget2 = db_map2.add_entity_class(name="Gadget")
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget1], db_map2: [gadget2]}, empty_entity_tree_view.model())
        self._add_entities_to_model({db_map1: [wall_clock1]}, "Gadget", empty_entity_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_entity_row(0, "Gadget", empty_entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": ("wall_clock",), "alternative_name": None}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_single_alternative_selected(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(0, db_map, alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": None, "entity_byname": None, "alternative_name": "Base"}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_empty_alternative_row_selected(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(1, db_map, alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_single_alternative_selection_after_entity_class_selection(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            base = db_map.alternative(name="Base")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(0, db_map, alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Base"}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_select_alternative_that_doesnt_exist_in_entity_class_database(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
        db_map2 = db_map_generator()
        with db_map2:
            base = db_map2.alternative(name="Base")
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget]}, empty_entity_tree_view.model())
        self._add_alternatives_to_model({db_map2: [base]}, empty_alternative_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, empty_entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(0, db_map2, empty_alternative_tree_view)
        assert not receiver.called()

    def test_select_two_alternatives_in_different_databases(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
            base1 = db_map1.alternative(name="Base")
        db_map2 = db_map_generator()
        with db_map2:
            base2 = db_map2.alternative(name="Base")
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget]}, empty_entity_tree_view.model())
        self._add_alternatives_to_model({db_map1: [base1], db_map2: [base2]}, empty_alternative_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, empty_entity_tree_view)
        self._select_alternative_row(0, db_map1, empty_alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(0, db_map2, empty_alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Base"}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_alternative_that_exists_in_single_database(
        self, parent_object, empty_entity_tree_view, empty_alternative_tree_view, db_map_generator
    ):
        db_map1 = db_map_generator()
        with db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
            alternative = db_map1.add_alternative(name="Alternative")
        db_map2 = db_map_generator()
        add_db_maps([db_map1, db_map2], empty_entity_tree_view, empty_alternative_tree_view)
        self._add_classes_to_model({db_map1: [gadget]}, empty_entity_tree_view.model())
        self._add_alternatives_to_model({db_map1: [alternative]}, empty_alternative_tree_view.model())
        generator = DefaultRowGenerator(
            empty_entity_tree_view.selectionModel(), empty_alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, empty_entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(0, db_map1, empty_alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Alternative"}, db_map1
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_select_two_different_alternatives(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            base = db_map.alternative(name="Base")
            top = db_map.add_alternative(name="Top")
        self._add_alternatives_to_model({db_map: [base, top]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_alternative_row(0, db_map, alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_alternative_row(1, db_map, alternative_tree_view)
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData({"entity_class_name": None, "entity_byname": None, "alternative_name": None}, db_map)
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_select_alternatives_then_entity_class(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            base = db_map.alternative(name="Base")
            widget = db_map.add_entity_class(name="Widget")
        self._add_classes_to_model({db_map: [widget]}, entity_tree_view.model())
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_alternative_row(0, db_map, alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        self._select_class_row(0, entity_tree_view)
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Widget"}, db_map)
        assert receiver.value_default_row == DefaultRowData(
            {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": "Base"}, db_map
        )
        assert receiver.entity_alternative_default_row == DefaultRowData(
            {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": "Base"}, db_map
        )

    def test_entity_class_updated(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        gadget.update(name="Widget")
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [])
        assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Widget"}, db_map)
        assert receiver.value_default_row == DefaultRowData(
            {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": None}, db_map
        )
        assert receiver.entity_alternative_default_row == DefaultRowData(
            {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": None}, db_map
        )

    def test_entity_class_update_is_ignored_when_roles_dont_match(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        gadget.update(name="Widget")
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.EditRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_entity_class_update_is_ignored_when_name_doesnt_change(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        gadget.update(description="Gadget is not a widget.")
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_entity_class_update_is_ignored_when_no_class_is_selected(
        self, parent_object, entity_tree_view, alternative_tree_view
    ):
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_entity_updated(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_entities_to_model({db_map: [wall_clock]}, "Gadget", entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_entity_row(0, "Gadget", entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        wall_clock.update(name="microwave_oven")
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": "Gadget", "entity_byname": ("microwave_oven",), "alternative_name": None}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_entity_updated_ignored_if_byname_doesnt_change(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        self._add_entities_to_model({db_map: [wall_clock]}, "Gadget", entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_entity_row(0, "Gadget", entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        wall_clock.update(description="Just another clock on the wall.")
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_entity_updated_ignored_if_no_entity_selected(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            gadget = db_map.add_entity_class(name="Gadget")
        self._add_classes_to_model({db_map: [gadget]}, entity_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_class_row(0, entity_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_alternative_updated(self, parent_object, entity_tree_view, alternative_tree_view, db_map):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_alternative_row(0, db_map, alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        base.update(name="Another")
        generator.alternative_updated(QModelIndex(), QModelIndex(), [])
        assert receiver.definition_default_row is uncalled
        row_data = DefaultRowData(
            {"entity_class_name": None, "entity_byname": None, "alternative_name": "Another"}, db_map
        )
        assert receiver.value_default_row == row_data
        assert receiver.entity_alternative_default_row == row_data

    def test_alternative_updated_ignored_when_roles_mismatch(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_alternative_row(0, db_map, alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        base.update(name="Another")
        generator.alternative_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.BackgroundRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_alternative_updated_ignored_when_alternative_name_hasnt_changed(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        self._select_alternative_row(0, db_map, alternative_tree_view)
        receiver = Receiver()
        receiver.connect(generator)
        base.update(description="The basis of all.")
        generator.alternative_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled

    def test_alternative_update_ignored_when_no_alternative_is_selected(
        self, parent_object, entity_tree_view, alternative_tree_view, db_map
    ):
        with db_map:
            base = db_map.alternative(name="Base")
        self._add_alternatives_to_model({db_map: [base]}, alternative_tree_view.model())
        generator = DefaultRowGenerator(
            entity_tree_view.selectionModel(), alternative_tree_view.selectionModel(), parent_object
        )
        receiver = Receiver()
        receiver.connect(generator)
        base.update(name="Another")
        generator.alternative_updated(QModelIndex(), QModelIndex(), [])
        assert receiver.definition_default_row is uncalled
        assert receiver.value_default_row is uncalled
        assert receiver.entity_alternative_default_row is uncalled
