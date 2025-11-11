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
from PySide6.QtCore import QItemSelectionModel, QObject, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from spinedb_api import Asterisk, DatabaseMapping
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.mvcmodels.shared import ITEM_ID_ROLE
from spinetoolbox.spine_db_editor.filter_selection import FilterSelection
from tests.mock_helpers import q_object


class TestFilterSelection:
    def test_deselect_everything(self, application):
        db_map = DatabaseMapping("sqlite://", create=True)
        with db_map:
            db_map.add_entity_class(name="Gadget")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                index = _find_child_item("Gadget", model.item(0)).index()
                selection_model.select(index, QItemSelectionModel.SelectionFlag.Select)
                waiter.wait()
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(index, QItemSelectionModel.SelectionFlag.Deselect)
                waiter.wait()
                assert waiter.args == ({},)

    def test_select_entity_class(self, application):
        db_map = DatabaseMapping("sqlite://", create=True)
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("Gadget", model.item(0)).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == ({db_map: {entity_class["id"]: Asterisk}},)

    def test_select_entity_class_with_multiple_db_maps(self):
        db_map1 = DatabaseMapping("sqlite://", create=True)
        with db_map1:
            entity_class1a = db_map1.add_entity_class(name="Gadget")
            entity_class1b = db_map1.add_entity_class(name="Widget")
        db_map2 = DatabaseMapping("sqlite://", create=True)
        with db_map2:
            entity_class2 = db_map2.add_entity_class(name="Gadget")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map1, db_map2], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("Gadget", model.item(0)).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (
                    {db_map1: {entity_class1a["id"]: Asterisk}, db_map2: {entity_class2["id"]: Asterisk}},
                )
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("Widget", model.item(0)).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (
                    {
                        db_map1: {entity_class1a["id"]: Asterisk, entity_class1b["id"]: Asterisk},
                        db_map2: {entity_class2["id"]: Asterisk},
                    },
                )

    def test_select_single_entity(self):
        db_map = DatabaseMapping("sqlite://", create=True)
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
            entity = db_map.add_entity(entity_class_name=entity_class["name"], name="wall_clock")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("wall_clock", model.item(0).child(0)).index(),
                    QItemSelectionModel.SelectionFlag.Select,
                )
                waiter.wait()
                assert waiter.args == ({db_map: {entity_class["id"]: {entity["id"]}}},)

    def test_select_entity_with_multiple_db_maps(self):
        db_map1 = DatabaseMapping("sqlite://", create=True)
        with db_map1:
            entity_class1 = db_map1.add_entity_class(name="Gadget")
            entity1a = db_map1.add_entity(entity_class_name="Gadget", name="watch")
            entity1b = db_map1.add_entity(entity_class_name="Gadget", name="iron")
        db_map2 = DatabaseMapping("sqlite://", create=True)
        with db_map2:
            entity_class2 = db_map2.add_entity_class(name="Gadget")
            entity2 = db_map2.add_entity(entity_class_name="Gadget", name="watch")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map1, db_map2], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            gadget_item = _find_child_item("Gadget", model.item(0))
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("watch", gadget_item).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (
                    {db_map1: {entity_class1["id"]: {entity1a["id"]}}, db_map2: {entity_class2["id"]: {entity2["id"]}}},
                )
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("iron", gadget_item).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (
                    {
                        db_map1: {entity_class1["id"]: {entity1a["id"], entity1b["id"]}},
                        db_map2: {entity_class2["id"]: {entity2["id"]}},
                    },
                )

    def test_select_entity_in_one_and_class_in_other_db_map(self):
        db_map1 = DatabaseMapping("sqlite://", create=True)
        with db_map1:
            entity_class1 = db_map1.add_entity_class(name="Gadget")
            entity = db_map1.add_entity(entity_class_name="Gadget", name="watch")
        db_map2 = DatabaseMapping("sqlite://", create=True)
        with db_map2:
            entity_class2 = db_map2.add_entity_class(name="Widget")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map1, db_map2], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            gadget_item = _find_child_item("Gadget", model.item(0))
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("watch", gadget_item).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == ({db_map1: {entity_class1["id"]: {entity["id"]}}},)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(
                    _find_child_item("Widget", model.item(0)).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (
                    {db_map1: {entity_class1["id"]: {entity["id"]}}, db_map2: {entity_class2["id"]: Asterisk}},
                )

    def test_root_item_selected_means_all_entities_selected(self):
        db_map = DatabaseMapping("sqlite://", create=True)
        with db_map:
            entity_class = db_map.add_entity_class(name="Gadget")
        with q_object(QObject()) as parent:
            model = QStandardItemModel(parent)
            _build_entity_tree_model([db_map], model)
            selection_model = QItemSelectionModel(model, parent)
            filter_selection = FilterSelection(selection_model, parent)
            with signal_waiter(filter_selection.entity_selection_changed) as waiter:
                selection_model.select(model.item(0).index(), QItemSelectionModel.SelectionFlag.Select)
                selection_model.select(
                    _find_child_item("Gadget", model.item(0)).index(), QItemSelectionModel.SelectionFlag.Select
                )
                waiter.wait()
                assert waiter.args == (Asterisk,)


def _find_child_item(name, item):
    for row in range(item.rowCount()):
        child_item = item.child(row)
        if child_item.data(Qt.ItemDataRole.DisplayRole) == name:
            return child_item
    raise KeyError(name)


def _build_entity_tree_model(db_maps, model):
    root_item = QStandardItem("root")
    root_item.setData({db_map: None for db_map in db_maps}, ITEM_ID_ROLE)
    for db_map in db_maps:
        with db_map:
            for entity_class in db_map.find_entity_classes():
                entity_class_item = _add_or_update_child_item(root_item, db_map, entity_class)
                for entity in db_map.find_entities(class_id=entity_class["id"]):
                    _add_or_update_child_item(entity_class_item, db_map, entity)
    model.appendRow(root_item)


def _add_or_update_child_item(parent_item, db_map, db_item):
    for row in range(parent_item.rowCount()):
        child_item = parent_item.child(row)
        if child_item.data(Qt.ItemDataRole.DisplayRole) == db_item["name"]:
            child_item.data(ITEM_ID_ROLE)[db_map] = db_item["id"]
            break
    else:
        child_item = QStandardItem(db_item["name"])
        child_item.setData({db_map: db_item["id"]}, ITEM_ID_ROLE)
        parent_item.appendRow(child_item)
    return child_item
