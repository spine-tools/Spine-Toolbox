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
from PySide6.QtCore import QModelIndex, Qt
from spinedb_api import Asterisk, DatabaseMapping
from spinetoolbox.spine_db_editor.default_row_generator import DefaultRowData, DefaultRowGenerator


class Receiver:
    def __init__(self):
        self.definition_default_row = None
        self.value_default_row = None
        self.entity_alternative_default_row = None

    def connect(self, generator: DefaultRowGenerator):
        generator.parameter_definition_default_row_updated.connect(self.update_definition_row)
        generator.parameter_value_default_row_updated.connect(self.update_value_row)
        generator.entity_alternative_default_row_updated.connect(self.update_entity_alternative_row)

    def update_definition_row(self, row_data):
        if self.definition_default_row is not None:
            raise RuntimeError("double call; reset first")
        self.definition_default_row = row_data

    def update_value_row(self, row_data):
        if self.value_default_row is not None:
            raise RuntimeError("double call; reset first")
        self.value_default_row = row_data

    def update_entity_alternative_row(self, row_data):
        if self.entity_alternative_default_row is not None:
            raise RuntimeError("double call; reset first")
        self.entity_alternative_default_row = row_data

    def reset(self):
        self.definition_default_row = None
        self.value_default_row = None
        self.entity_alternative_default_row = None


class TestDefaultRowGenerator:
    def test_empty_entity_selection(self, parent_object):
        generator = DefaultRowGenerator(parent_object)
        receiver = Receiver()
        receiver.connect(generator)
        generator.update_defaults_from_entity_selection({})
        assert receiver.definition_default_row is None
        assert receiver.value_default_row is None
        assert receiver.entity_alternative_default_row is None

    def test_asterisk_entity_selection(self, parent_object):
        generator = DefaultRowGenerator(parent_object)
        receiver = Receiver()
        receiver.connect(generator)
        generator.update_defaults_from_entity_selection(Asterisk)
        assert receiver.definition_default_row is None
        assert receiver.value_default_row is None
        assert receiver.entity_alternative_default_row is None

    def test_single_entity_class_selected(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map)
            row_data = DefaultRowData(
                {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_first_one_then_two_entity_classes_selected(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            widget = db_map.add_entity_class(name="Widget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk, widget["id"]: Asterisk}})
            assert receiver.definition_default_row == DefaultRowData({"entity_class_name": None}, None)
            row_data = DefaultRowData(
                {"entity_class_name": None, "entity_byname": None, "alternative_name": None}, None
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_two_entity_classes_from_different_databases(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                gadget2 = db_map2.add_entity_class(name="Gadget")
                generator = DefaultRowGenerator(parent_object)
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_entity_selection(
                    {db_map1: {gadget1["id"]: Asterisk}, db_map2: {gadget2["id"]: Asterisk}}
                )
                assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_entity_class_that_exists_in_a_single_database(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                generator = DefaultRowGenerator(parent_object)
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_entity_selection({db_map1: {gadget1["id"]: Asterisk}, db_map2: {}})
                assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_single_entity(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: {wall_clock["id"]}}})
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

    def test_first_one_then_two_entities(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
            wrist_watch = db_map.add_entity(name="wrist_watch", entity_class_name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: {wall_clock["id"]}}})
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection(
                {db_map: {gadget["id"]: {wall_clock["id"], wrist_watch["id"]}}}
            )
            assert receiver.definition_default_row is None
            row_data = DefaultRowData(
                {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": None}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_two_entities_in_different_databases(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            wall_clock1 = db_map1.add_entity(name="wall_clock", entity_class_name="Gadget")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                gadget2 = db_map2.add_entity_class(name="Gadget")
                wall_clock2 = db_map2.add_entity(name="wall_clock", entity_class_name="Gadget")
                generator = DefaultRowGenerator(parent_object)
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_entity_selection(
                    {db_map1: {gadget1["id"]: {wall_clock1["id"]}}, db_map2: {gadget2["id"]: {wall_clock2["id"]}}}
                )
                assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": ("wall_clock",), "alternative_name": None}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_entity_that_exists_in_single_database(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget1 = db_map1.add_entity_class(name="Gadget")
            wall_clock1 = db_map1.add_entity(name="wall_clock", entity_class_name="Gadget")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                gadget2 = db_map2.add_entity_class(name="Gadget")
                generator = DefaultRowGenerator(parent_object)
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_entity_selection(
                    {db_map1: {gadget1["id"]: {wall_clock1["id"]}}, db_map2: {gadget2["id"]: set()}}
                )
                assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Gadget"}, db_map1)
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": ("wall_clock",), "alternative_name": None}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_single_alternative_selected(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            assert receiver.definition_default_row is None
            row_data = DefaultRowData(
                {"entity_class_name": None, "entity_byname": None, "alternative_name": "Base"}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_single_alternative_selection_after_entity_class_selection(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            assert receiver.definition_default_row is None
            row_data = DefaultRowData(
                {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Base"}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_select_alternative_that_doesnt_exist_in_entity_class_database(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                base = db_map2.alternative(name="Base")
                generator = DefaultRowGenerator(parent_object)
                generator.update_defaults_from_entity_selection({db_map1: {gadget["id"]: Asterisk}})
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_alternative_selection({db_map2: {base["id"]}})
                assert receiver.definition_default_row is None
                assert receiver.value_default_row is None
                assert receiver.entity_alternative_default_row is None

    def test_select_two_alternatives_in_different_databases(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
            base1 = db_map1.alternative(name="Base")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                base2 = db_map2.alternative(name="Base")
                generator = DefaultRowGenerator(parent_object)
                generator.update_defaults_from_entity_selection({db_map1: {gadget["id"]: Asterisk}})
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_alternative_selection({db_map2: {base2["id"]}, db_map1: {base1["id"]}})
                assert receiver.definition_default_row is None
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Base"}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_alternative_that_exists_in_single_database(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map1:
            gadget = db_map1.add_entity_class(name="Gadget")
            alternative = db_map1.add_alternative(name="Alternative")
            with DatabaseMapping("sqlite://", create=True) as db_map2:
                generator = DefaultRowGenerator(parent_object)
                generator.update_defaults_from_entity_selection({db_map1: {gadget["id"]: Asterisk}})
                receiver = Receiver()
                receiver.connect(generator)
                generator.update_defaults_from_alternative_selection({db_map2: set(), db_map1: {alternative["id"]}})
                assert receiver.definition_default_row is None
                row_data = DefaultRowData(
                    {"entity_class_name": "Gadget", "entity_byname": None, "alternative_name": "Alternative"}, db_map1
                )
                assert receiver.value_default_row == row_data
                assert receiver.entity_alternative_default_row == row_data

    def test_select_two_different_alternatives(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            top = db_map.add_alternative(name="Top")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_alternative_selection({db_map: {top["id"], base["id"]}})
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_select_alternatives_then_entity_class(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            widget = db_map.add_entity_class(name="Widget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            receiver = Receiver()
            receiver.connect(generator)
            generator.update_defaults_from_entity_selection({db_map: {widget["id"]: Asterisk}})
            assert receiver.definition_default_row == DefaultRowData({"entity_class_name": "Widget"}, db_map)
            assert receiver.value_default_row == DefaultRowData(
                {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": "Base"}, db_map
            )
            assert receiver.entity_alternative_default_row == DefaultRowData(
                {"entity_class_name": "Widget", "entity_byname": None, "alternative_name": "Base"}, db_map
            )

    def test_entity_class_updated(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
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

    def test_entity_class_update_is_ignored_when_roles_dont_match(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            receiver = Receiver()
            receiver.connect(generator)
            gadget.update(name="Widget")
            generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.EditRole])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_entity_class_update_is_ignored_when_name_doesnt_change(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            receiver = Receiver()
            receiver.connect(generator)
            gadget.update(description="Gadget is not a widget.")
            generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_entity_class_update_is_ignored_when_no_class_is_selected(self, parent_object):
        generator = DefaultRowGenerator(parent_object)
        receiver = Receiver()
        receiver.connect(generator)
        generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
        assert receiver.definition_default_row is None
        assert receiver.value_default_row is None
        assert receiver.entity_alternative_default_row is None

    def test_entity_updated(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: {wall_clock["id"]}}})
            receiver = Receiver()
            receiver.connect(generator)
            wall_clock.update(name="microwave_oven")
            generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
            assert receiver.definition_default_row is None
            row_data = DefaultRowData(
                {"entity_class_name": "Gadget", "entity_byname": ("microwave_oven",), "alternative_name": None}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_entity_updated_ignored_if_byname_doesnt_change(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            wall_clock = db_map.add_entity(name="wall_clock", entity_class_name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: {wall_clock["id"]}}})
            receiver = Receiver()
            receiver.connect(generator)
            wall_clock.update(description="Just another clock on the wall.")
            generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_entity_updated_ignored_if_no_entity_selected(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            gadget = db_map.add_entity_class(name="Gadget")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_entity_selection({db_map: {gadget["id"]: Asterisk}})
            receiver = Receiver()
            receiver.connect(generator)
            generator.entity_or_class_updated(QModelIndex(), QModelIndex(), [])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_alternative_updated(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            receiver = Receiver()
            receiver.connect(generator)
            base.update(name="Another")
            generator.alternative_updated(QModelIndex(), QModelIndex(), [])
            assert receiver.definition_default_row is None
            row_data = DefaultRowData(
                {"entity_class_name": None, "entity_byname": None, "alternative_name": "Another"}, db_map
            )
            assert receiver.value_default_row == row_data
            assert receiver.entity_alternative_default_row == row_data

    def test_alternative_updated_ignored_when_roles_mismatch(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            receiver = Receiver()
            receiver.connect(generator)
            base.update(name="Another")
            generator.alternative_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.BackgroundRole])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_alternative_updated_ignored_when_alternative_name_hasnt_changed(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            generator.update_defaults_from_alternative_selection({db_map: {base["id"]}})
            receiver = Receiver()
            receiver.connect(generator)
            base.update(description="The basis of all.")
            generator.alternative_updated(QModelIndex(), QModelIndex(), [Qt.ItemDataRole.DisplayRole])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None

    def test_alternative_update_ignored_when_no_alternative_is_selected(self, parent_object):
        with DatabaseMapping("sqlite://", create=True) as db_map:
            base = db_map.alternative(name="Base")
            generator = DefaultRowGenerator(parent_object)
            receiver = Receiver()
            receiver.connect(generator)
            base.update(name="Another")
            generator.alternative_updated(QModelIndex(), QModelIndex(), [])
            assert receiver.definition_default_row is None
            assert receiver.value_default_row is None
            assert receiver.entity_alternative_default_row is None
