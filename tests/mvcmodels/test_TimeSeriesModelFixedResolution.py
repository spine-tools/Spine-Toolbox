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

"""Unit tests for the TimeSeriesModelFixedResolution class."""
import dateutil.parser
from dateutil.relativedelta import relativedelta
import numpy as np
import numpy.testing
from PySide6.QtCore import Qt
from spinedb_api import TimeSeriesFixedResolution
from spinetoolbox.mvcmodels.time_series_model_fixed_resolution import TimeSeriesModelFixedResolution


class TestTimeSeriesModelFixedStep:
    def test_data(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        for role in [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]:
            model_index = model.index(0, 0)
            assert model.data(model_index, role) == "2019-07-05T12:00:00"
            model_index = model.index(0, 1)
            expected = str(-5.0) if role == Qt.ItemDataRole.DisplayRole else -5.0
            assert model.data(model_index, role) == expected

    def test_flags(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        model_index = model.index(0, 0)
        assert model.flags(model_index) == Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        model_index = model.index(0, 1)
        assert (
            model.flags(model_index)
            == Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        )

    def test_indexes(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        assert model.indexes == numpy.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64")

    def test_insertRows_at_the_beginning(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        assert model.insertRows(0, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [0.0, -5.0, 7.0], True, False)
        assert model.indexes == np.array(
            ["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64"
        )

    def test_insertRows_single_row_in_the_middle(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        assert model.insertRows(1, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 0.0, 7.0], True, False)
        assert model.indexes == np.array(
            ["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64"
        )

    def test_insertRows_multiple_rows_in_the_middle(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        assert model.insertRows(1, 3)
        assert model.value == TimeSeriesFixedResolution(
            "2019-07-05T12:00", "2 hours", [-5.0, 0.0, 0.0, 0.0, 7.0], True, False
        )
        assert model.indexes == np.array(
            ["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00", "2019-07-05T18:00", "2019-07-05T20:00"],
            dtype="datetime64",
        )

    def test_insertRows_in_the_end(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False), parent_object
        )
        assert model.insertRows(2, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0, 0.0], True, False)
        assert model.indexes == np.array(
            ["2019-07-05T12:00", "2019-07-05T14:00", "2019-07-05T16:00"], dtype="datetime64"
        )

    def test_removeRows_from_the_beginning(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False), parent_object
        )
        assert model.removeRows(0, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-5.0, 7.0], True, False)
        assert model.indexes == np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64")

    def test_removeRows_from_the_middle(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False), parent_object
        )
        assert model.removeRows(1, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, 7.0], True, False)
        assert model.indexes == np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64")

    def test_removeRows_from_the_end(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False), parent_object
        )
        assert model.removeRows(2, 1)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False)
        assert model.indexes == np.array(["2019-07-05T12:00", "2019-07-05T14:00"], dtype="datetime64")

    def test_cannot_remove_all_rows(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False), parent_object
        )
        assert model.removeRows(0, 3)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3], True, False)
        assert model.indexes == np.array(["2019-07-05T12:00"], dtype="datetime64")

    def test_removing_last_row_fails(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3], True, False), parent_object
        )
        assert not model.removeRows(0, 1)

    def test_including_empty_row_to_removed_rows_does_not_raise(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, 3.2], True, False), parent_object
        )
        assert model.removeRows(0, 3)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3], True, False)

    def test_reset_updates_indexes(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False), parent_object
        )
        model.reset(TimeSeriesFixedResolution("1991-01-01T13:30", "3 months", [7.0, -4.0], False, True))
        assert model.value == TimeSeriesFixedResolution("1991-01-01T13:30", "3 months", [7.0, -4.0], False, True)
        assert model.indexes == np.array(["1991-01-01T13:30", "1991-04-01T13:30"], dtype="datetime64")

    def test_setData(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False), parent_object
        )
        model_index = model.index(0, 1)
        model.setData(model_index, -4.0)
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [-4.0, -5.0], True, False)

    def test_setData_sets_value_to_nan_if_conversion_to_float_fails(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False), parent_object
        )
        model_index = model.index(0, 1)
        model.setData(model_index, "1,1")
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [np.nan, -5.0], True, False)

    def test_set_resolution_updates_indexes(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False), parent_object
        )
        model.set_resolution([relativedelta(minutes=4)])
        assert model.value == TimeSeriesFixedResolution("2019-07-05T12:00", "4 minutes", [2.3, -5.0], True, False)
        assert model.indexes == np.array(["2019-07-05T12:00", "2019-07-05T12:04"], dtype="datetime64")

    def test_set_start_updates_indexes(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0], True, False), parent_object
        )
        model.set_start(dateutil.parser.parse("1975-07-07T06:33"))
        assert model.value == TimeSeriesFixedResolution("1975-07-07T06:33", "2h", [2.3, -5.0], True, False)
        assert model.indexes == np.array(["1975-07-07T06:33", "1975-07-07T08:33"], dtype="datetime64")

    def test_batch_set_data(self, parent_object):
        model = TimeSeriesModelFixedResolution(
            TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, -5.0, 7.0], True, False), parent_object
        )
        indexes = [model.index(0, 0), model.index(1, 1), model.index(2, 1)]
        values = ["1999-01-01T12:00", 55.5, -55.5]
        model.batch_set_data(indexes, values)
        expected = TimeSeriesFixedResolution("2019-07-05T12:00", "2 hours", [2.3, 55.5, -55.5], True, False)
        assert model.value == expected
