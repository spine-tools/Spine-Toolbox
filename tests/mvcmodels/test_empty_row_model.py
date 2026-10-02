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
from PySide6.QtCore import QModelIndex
from spinetoolbox.mvcmodels.empty_row_model import EmptyRowModel
from tests.mock_helpers import assert_table_model_data_pytest


def test_default_row(parent_object):
    model = EmptyRowModel(parent_object, ["head_1", "head_2"])
    model.set_default_row(head_1=1.1, head_2=2.2)
    assert model.insertRow(0, QModelIndex())
    expected = [[1.1, 2.2]]
    assert_table_model_data_pytest(model, expected)
    assert model.defaulted_rows() == [0]


def test_default_row_without_header(parent_object):
    model = EmptyRowModel(parent_object)
    assert model.insertRow(0, QModelIndex())
    assert model.insertColumns(0, 2, QModelIndex())
    model.set_default_row(head_1=1.1, head_2=2.2)
    model.set_rows_to_default(0)
    expected = [[None, None, None]]
    assert_table_model_data_pytest(model, expected)
    assert model.defaulted_rows() == [0]


def test_defaulted_rows(parent_object):
    model = EmptyRowModel(parent_object, ["head_1", "head_2"])
    model.set_default_row(head_1=1.1)
    assert model.insertRows(0, 3, QModelIndex())
    assert model.defaulted_rows() == [0, 1, 2]
    assert model.setData(model.index(1, 1), 2.2)
    assert model.defaulted_rows() == [0, 2]
    assert model.setData(model.index(2, 0), None)
    assert model.defaulted_rows() == [0, 3]
