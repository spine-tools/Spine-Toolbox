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

"""Unit tests for `pivot_table_models` module."""
import itertools
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from spinedb_api import Map
from tests.mock_helpers import assert_table_model_data_pytest, fetch_model


class TestParameterValuePivotTableModel:
    @staticmethod
    def _fill_model_with_data(db_map, db_mngr, db_editor):
        data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", 1.0),
                ("class1", "object2", "parameter1", 3.0),
                ("class1", "object1", "parameter2", 5.0),
                ("class1", "object2", "parameter2", 7.0),
            ),
        }
        db_mngr.import_data({db_map: data}, "Import initial test data.")
        while db_editor.entity_tree_model._root_item.row_count() == 0:
            QApplication.processEvents()

    @staticmethod
    def _start(db_mngr, db_editor):
        get_item_exceptions = []

        def guarded_get_item(db_map, item_type, id_):
            try:
                return db_map.get_item(item_type, id=id_)
            except Exception as error:
                get_item_exceptions.append(error)
                return None

        object_class_index = db_editor.entity_tree_model.index(0, 0)
        fetch_model(db_editor.entity_tree_model)
        index = db_editor.entity_tree_model.index(0, 0, object_class_index)
        db_editor._update_class_attributes(index)
        with patch.object(db_editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
            mock_is_visible.return_value = True
            db_editor.do_reload_pivot_table()
        model = db_editor.pivot_table_model
        with patch.object(db_mngr, "get_item") as get_item:
            get_item.side_effect = guarded_get_item
            model.beginResetModel()
            model.endResetModel()
            QApplication.processEvents()
            assert get_item_exceptions == []
        return model

    def test_x_flag(self, db_map, db_mngr, db_editor):
        self._fill_model_with_data(db_map, db_mngr, db_editor)
        model = self._start(db_mngr, db_editor)
        assert model.plot_x_column is None
        model.set_plot_x_column(1, True)
        assert model.plot_x_column == 1
        model.set_plot_x_column(1, False)
        assert model.plot_x_column is None

    def test_header_name(self, db_map, db_mngr, db_editor):
        self._fill_model_with_data(db_map, db_mngr, db_editor)
        model = self._start(db_mngr, db_editor)
        assert model.rowCount() == 5
        assert model.columnCount() == 4
        assert model.header_name(model.index(2, 0)) == "object1"
        assert model.header_name(model.index(0, 1)) == "parameter1"
        assert model.header_name(model.index(3, 0)) == "object2"
        assert model.header_name(model.index(0, 2)) == "parameter2"

    def test_data(self, db_map, db_mngr, db_editor):
        self._fill_model_with_data(db_map, db_mngr, db_editor)
        model = self._start(db_mngr, db_editor)
        expected = [
            ["parameter", "parameter1", "parameter2", None],
            ["class1", None, None, None],
            ["object1", str(1.0), str(5.0), None],
            ["object2", str(3.0), str(7.0), None],
            [None, None, None, None],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_header_row_count(self, db_map, db_mngr, db_editor):
        self._fill_model_with_data(db_map, db_mngr, db_editor)
        model = self._start(db_mngr, db_editor)
        assert model.headerRowCount() == 2

    def test_model_works_even_without_entities(self, db_map, db_mngr, db_editor):
        data = {
            "entity_classes": (("class1",),),
        }
        db_mngr.import_data({db_map: data}, "Import entity class.")
        while db_editor.entity_tree_model._root_item.row_count() == 0:
            QApplication.processEvents()
        model = self._start(db_mngr, db_editor)
        expected = [
            ["parameter", None],
            ["class1", None],
            [None, None],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_single_entity_creates_half_finished_pivot(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("Object",),),
            "entities": (("Object", "spatula"),),
        }
        db_mngr.import_data({db_map: initial_data}, "Import test data")
        while db_editor.entity_tree_model._root_item.row_count() == 0:
            QApplication.processEvents()
        model = self._start(db_mngr, db_editor)
        expected = [["parameter", None], ["Object", None], ["spatula", None], [None, None]]
        assert_table_model_data_pytest(model, expected)

    def test_single_entity_and_parameter_definition_create_empty_value_cell(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("Object",),),
            "parameter_definitions": (("Object", "x"),),
            "entities": (("Object", "spatula"),),
        }
        db_mngr.import_data({db_map: initial_data}, "Import test data.")
        while db_editor.entity_tree_model._root_item.row_count() == 0:
            QApplication.processEvents()
        model = self._start(db_mngr, db_editor)
        expected = [["parameter", "x", None], ["Object", None, None], ["spatula", None, None], [None, None, None]]
        assert_table_model_data_pytest(model, expected)

    def test_removing_value_from_model_sets_value_cell_to_none(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("Object",),),
            "entities": (("Object", "spatula"),),
            "parameter_definitions": (("Object", "x"),),
            "parameter_values": (("Object", "spatula", "x", 2.3),),
        }
        db_mngr.import_data({db_map: initial_data}, "Import test data.")
        while db_editor.entity_tree_model._root_item.row_count() == 0:
            QApplication.processEvents()
        model = self._start(db_mngr, db_editor)
        expected = [["parameter", "x", None], ["Object", None, None], ["spatula", str(2.3), None], [None, None, None]]
        assert_table_model_data_pytest(model, expected)
        with db_map:
            value_item = db_map.get_parameter_value_item(
                entity_class_name="Object",
                entity_byname=("spatula",),
                parameter_definition_name="x",
                alternative_name="Base",
            )
            value_item.remove()
        expected = [["parameter", "x", None], ["Object", None, None], ["spatula", None, None], [None, None, None]]
        assert_table_model_data_pytest(model, expected)

    def test_drag_and_drop_database_from_frozen_table(self, db_map, db_name, db_mngr, db_editor):
        self._fill_model_with_data(db_map, db_mngr, db_editor)
        model = self._start(db_mngr, db_editor)
        for frozen_column in range(db_editor.frozen_table_model.columnCount()):
            frozen_index = db_editor.frozen_table_model.index(0, frozen_column)
            if frozen_index.data() == "database":
                break
        else:
            raise RuntimeError("No 'database' column found in frozen table")
        frozen_table_header_widget = db_editor.ui.frozen_table.indexWidget(frozen_index)
        for row, column in itertools.product(
            range(db_editor.pivot_table_proxy.rowCount()), range(db_editor.pivot_table_proxy.columnCount())
        ):
            index_widget = db_editor.ui.pivot_table.indexWidget(db_editor.pivot_table_proxy.index(row, column))
            if index_widget.identifier == "parameter":
                break
        else:
            raise RuntimeError("No 'parameter' header found")
        db_editor.handle_header_dropped(frozen_table_header_widget, index_widget)
        QApplication.processEvents()
        expected = [
            ["database", db_name, db_name, db_name],
            ["parameter", "parameter1", "parameter2", None],
            ["class1", None, None, None],
            ["object1", "1.0", "5.0", None],
            ["object2", "3.0", "7.0", None],
            [None, None, None, None],
        ]
        assert_table_model_data_pytest(model, expected)


class TestIndexExpansionPivotTableModel:
    @staticmethod
    def _start(initial_data, db_map, db_mngr, db_editor):
        db_mngr.import_data({db_map: initial_data}, "Import initial test data.")
        object_class_index = db_editor.entity_tree_model.index(0, 0)
        fetch_model(db_editor.entity_tree_model)
        index = db_editor.entity_tree_model.index(0, 0, object_class_index)
        for action in db_editor.pivot_action_group.actions():
            if action.text() == db_editor._INDEX_EXPANSION:
                action.trigger()
                break
        db_editor._update_class_attributes(index)
        with patch.object(db_editor.ui.dockWidget_pivot_table, "isVisible") as mock_is_visible:
            mock_is_visible.return_value = True
            db_editor.do_reload_pivot_table()
        model = db_editor.pivot_table_model
        model.beginResetModel()
        model.endResetModel()
        QApplication.processEvents()
        return model

    def test_data(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("class1",),),
            "parameter_definitions": (("class1", "parameter1"), ("class1", "parameter2")),
            "entities": (("class1", "object1"), ("class1", "object2")),
            "parameter_values": (
                ("class1", "object1", "parameter1", Map(["A", "B"], [1.1, 2.1])),
                ("class1", "object2", "parameter1", Map(["C", "D"], [1.2, 2.2])),
                ("class1", "object1", "parameter2", Map(["C", "D"], [-1.1, -2.1])),
                ("class1", "object2", "parameter2", Map(["A", "B"], [-1.2, -2.2])),
            ),
        }
        model = self._start(initial_data, db_map, db_mngr, db_editor)
        expected = [
            [None, "parameter", "parameter1", "parameter2"],
            ["class1", "index", None, None],
            ["object1", "A", str(1.1), None],
            ["object1", "B", str(2.1), None],
            ["object1", "C", None, str(-1.1)],
            ["object1", "D", None, str(-2.1)],
            ["object2", "A", None, str(-1.2)],
            ["object2", "B", None, str(-2.2)],
            ["object2", "C", str(1.2), None],
            ["object2", "D", str(2.2), None],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_entity_without_parameter_values_does_not_show(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("Object",),),
            "parameter_definitions": (("Object", "x"),),
            "entities": (("Object", "spatula"),),
        }
        model = self._start(initial_data, db_map, db_mngr, db_editor)
        expected = [
            [None, "parameter"],
            ["Object", "index"],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_removing_value_from_model_removes_it_from_model(self, db_map, db_mngr, db_editor):
        initial_data = {
            "entity_classes": (("Object",),),
            "entities": (("Object", "spatula"),),
            "parameter_definitions": (("Object", "x"),),
            "parameter_values": (("Object", "spatula", "x", 2.3),),
        }
        model = self._start(initial_data, db_map, db_mngr, db_editor)
        expected = [
            [None, "parameter", "x"],
            ["Object", "index", None],
            ["spatula", "", str(2.3)],
        ]
        assert_table_model_data_pytest(model, expected)
        with db_map:
            value_item = db_map.get_parameter_value_item(
                entity_class_name="Object",
                entity_byname=("spatula",),
                parameter_definition_name="x",
                alternative_name="Base",
            )
            value_item.remove()
        expected = [[None, "parameter"], ["Object", "index"]]
        assert_table_model_data_pytest(model, expected)
