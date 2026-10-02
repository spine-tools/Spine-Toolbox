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
from PySide6.QtWidgets import QApplication
import pytest
from spinetoolbox.helpers import signal_waiter
from spinetoolbox.spine_db_editor.mvcmodels.parameter_group_model import ParameterGroupModel
from spinetoolbox.spine_db_editor.mvcmodels.utils import PARAMETER_GROUP_FIELD_MAP
from tests.mock_helpers import assert_table_model_data_pytest


@pytest.fixture
def parameter_group_model(db_mngr, parent_object):
    model = ParameterGroupModel(db_mngr, parent_object)
    yield model
    model.tear_down()


class TestParameterGroupModel:
    def test_column_count(self, parameter_group_model):
        assert parameter_group_model.columnCount() == len(PARAMETER_GROUP_FIELD_MAP)

    def test_horizontal_header(self, parameter_group_model):
        for column, header in enumerate(("name", "color", "priority", "database")):
            assert parameter_group_model.headerData(column, Qt.Orientation.Horizontal) == header

    def test_data(self, parameter_group_model, db_map, db_name):
        with db_map:
            db_map.add_parameter_group(name="My first", color="deadbf", priority=2)
            db_map.add_parameter_group(name="My second", color="beefaf", priority=3)
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        expected = [["My first", "deadbf", 2, db_name], ["My second", "beefaf", 3, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_flags(self, parameter_group_model, db_map):
        with db_map:
            db_map.add_parameter_group(name="My group", color="deadbf", priority=5)
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        assert (
            model.flags(model.index(0, 0))
            == Qt.ItemFlag.ItemNeverHasChildren
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
        )
        assert (
            model.flags(model.index(0, 1))
            == Qt.ItemFlag.ItemNeverHasChildren
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
        )
        assert (
            model.flags(model.index(0, 2))
            == Qt.ItemFlag.ItemNeverHasChildren
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsEditable
            | Qt.ItemFlag.ItemIsSelectable
        )
        assert (
            model.flags(model.index(0, 3))
            == Qt.ItemFlag.ItemNeverHasChildren | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        )

    def test_set_data(self, parameter_group_model, db_map, db_name):
        with db_map:
            db_map.add_parameter_group(name="My group", color="deadbf", priority=5)
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        with signal_waiter(model.dataChanged) as waiter:
            model.setData(model.index(0, 0), "Renamed")
            waiter.wait()
            assert waiter.args == (
                model.index(0, 0),
                model.index(0, 2),
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
            )
        expected = [
            ["Renamed", "deadbf", 5, db_name],
        ]
        assert_table_model_data_pytest(model, expected)

    def test_batch_set_data(self, parameter_group_model, db_map, db_name):
        with db_map:
            db_map.add_parameter_group(name="My first", color="deadbf", priority=3)
            db_map.add_parameter_group(name="My second", color="beefaf", priority=2)
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        with signal_waiter(model.dataChanged) as waiter:
            model.batch_set_data([model.index(0, 1), model.index(1, 0)], ["090807", "Renamed"])
            waiter.wait()
            assert waiter.args == (
                model.index(0, 0),
                model.index(1, 2),
                [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole],
            )
        expected = [["My first", "090807", 3, db_name], ["Renamed", "beefaf", 2, db_name]]
        assert_table_model_data_pytest(model, expected)

    def test_remove_rows(self, parameter_group_model, db_map):
        with db_map:
            db_map.add_parameter_group(name="My first", color="deadbf", priority=2)
            db_map.add_parameter_group(name="My second", color="beefaf", priority=5)
            db_map.add_parameter_group(name="My third", color="baffed", priority=3)
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        with signal_waiter(model.rowsRemoved) as waiter:
            model.removeRows(0, 3)
            waiter.wait()
            assert waiter.args == (QModelIndex(), 0, 2)
        assert model.rowCount() == 0

    def test_add_more_data(self, parameter_group_model, db_mngr, db_map, db_name):
        model = parameter_group_model
        model.reset_db_maps([db_map])
        while model.canFetchMore(QModelIndex()):
            model.fetchMore(QModelIndex())
            QApplication.processEvents()
        with signal_waiter(model.rowsInserted) as waiter:
            db_mngr.add_items("parameter_group", {db_map: [{"name": "My group", "color": "deadbf", "priority": 5}]})
            waiter.wait()
            assert waiter.args == (QModelIndex(), 0, 0)
        expected = [
            ["My group", "deadbf", 5, db_name],
        ]
        assert_table_model_data_pytest(model, expected)
